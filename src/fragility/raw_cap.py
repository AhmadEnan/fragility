"""Frozen CAP labels and tracking annotation with portable, explicit input paths.

Call configure before reading. Inputs are read-only; no work occurs on import.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .raw_io import load_cache, load_index, event_table
from . import raw_events
RAW_FPS_DEFAULT = 29.97
CACHE_STRIDE = 8
PHASE_TRANSITION_MAX_S = 5.0
SLOT_CHANGE_GUARD_FRAMES = 3
CONTROL_RETENTION_S = 1.0
ADVANTAGE_WINDOW_S = 2.0
PROGRESS_PRIMARY_M = 5.0
PROGRESS_SENSITIVITY_M = (3.0, 8.0)
BOUNDARY_AMBIGUOUS_M = 0.50
BOX_X = 52.5 - 16.5
BOX_Y = 20.16 / 2.0
SYNC_MAX_RAW_FRAMES = 32
FAMILY_PASS, FAMILY_CROSS, FAMILY_CARRY = "pass", "cross", "carry"
PASS_LIKE = (FAMILY_PASS, FAMILY_CROSS)
THIRD_EDGES = [(-52.5, -17.5, "defensive"), (-17.5, 17.5, "middle"), (17.5, 52.5, "attacking")]
META_DIR = EVENT_DIR = None
_FPS_CACHE, _EXTRA_CACHE, _EV_CACHE, _ANNOT_CACHE = {}, {}, {}, {}
_UNIQUE_CACHE, _DUP_COUNTS, _VIEW_CACHE = {}, {}, {}

def configure(raw_root, cache_root, index_root):
    from . import raw_io
    global META_DIR, EVENT_DIR
    raw_io.configure(raw_root, cache_root, index_root)
    META_DIR, EVENT_DIR = Path(raw_root) / "Metadata", Path(raw_root) / "Event Data"
    for cache in (_FPS_CACHE, _EXTRA_CACHE, _EV_CACHE, _ANNOT_CACHE, _UNIQUE_CACHE, _DUP_COUNTS, _VIEW_CACHE):
        cache.clear()

def passes_module():
    return raw_events
from .raw_third import third_of

def match_fps(match_id: str) -> float:
    """Vendor frame rate from the match metadata (never assumed)."""
    match_id = str(match_id)
    if match_id not in _FPS_CACHE:
        raw = json.loads((META_DIR / f"{match_id}.json").read_text(encoding="utf-8"))
        entry = raw[0] if isinstance(raw, list) else raw
        fps = entry.get("fps")
        if fps is None:
            fps = RAW_FPS_DEFAULT
        _FPS_CACHE[match_id] = float(fps)
    return _FPS_CACHE[match_id]

def _extra_outcome_fields(match_id: str) -> pd.DataFrame:
    """``crossOutcomeType`` / ``ballCarryOutcome``, which the repo loader omits.

    Kept in a separate table rather than modifying ``src/fragility/passes.py`` so
    that no frozen upstream file is touched.
    """
    match_id = str(match_id)
    if match_id not in _EXTRA_CACHE:
        raw = json.loads((EVENT_DIR / f"{match_id}.json").read_text(encoding="utf-8"))
        rows = []
        for entry in raw:
            poss = entry["possessionEvents"]
            rows.append({
                "game_event_id": entry["gameEventId"],
                "possession_event_id": entry["possessionEventId"],
                "cross_outcome_type": poss.get("crossOutcomeType"),
                "ball_carry_outcome": poss.get("ballCarryOutcome"),
                "carry_type": poss.get("carryType"),
            })
        _EXTRA_CACHE[match_id] = pd.DataFrame(rows)
    return _EXTRA_CACHE[match_id]

def events_with_possessions(match_id: str) -> pd.DataFrame:
    """Events with frames, possession runs and the corrected possession age.

    Pipeline: repo event loader -> tracking-frame linkage -> ``assign_possessions``
    -> ``add_frame_timing``.  ``add_frame_timing`` already divides raw frame
    differences by the vendor frame rate, which is exactly the D1 fix; it is used
    rather than re-implemented.
    """
    match_id = str(match_id)
    if match_id in _EV_CACHE:
        return _EV_CACHE[match_id]

    pm = passes_module()
    ev = event_table(match_id)
    ev = pm.assign_possessions(ev)
    ev = pm.add_frame_timing(ev)

    extra = _extra_outcome_fields(match_id)
    if len(extra) == len(ev):
        for col in ("cross_outcome_type", "ball_carry_outcome", "carry_type"):
            ev[col] = extra[col].to_numpy()
    else:  # pragma: no cover - defensive
        ev = ev.merge(
            extra.drop_duplicates("game_event_id"), on="game_event_id", how="left"
        )
    _EV_CACHE[match_id] = ev
    return ev

def possession_table(match_id: str) -> pd.DataFrame:
    """One row per possession run: team, frame span, duration, set piece."""
    ev = events_with_possessions(match_id)
    live = ev[ev["possession_index"] >= 0]
    meta = live.groupby("possession_index").agg(
        n_events=("game_event_id", "size"),
        first_frame=("poss_first_frame", "first"),
        last_frame=("poss_last_frame", "first"),
        team_id=("team_id", "first"),
        team_name=("team_name", "first"),
        home_team=("home_team", "first"),
        setpiece=("setpiece_type", "first"),
        start_time=("start_time", "min"),
        end_time=("end_time", "max"),
    )
    meta["attacking_team_is_home"] = meta["home_team"].astype(bool)
    meta["duration_s"] = (meta["last_frame"] - meta["first_frame"]) / match_fps(match_id)
    meta["period"] = live.groupby("possession_index")["period"].first()
    return meta.reset_index()

def frame_possession(match_id: str) -> pd.DataFrame:
    """Per raw tracking frame: the possession run it belongs to (uncapped ffill).

    This is the D3 fix.  The previous code attached to every cache frame the frame
    of the *nearest preceding event*, capped at 120 raw frames.  Here the frame's
    own possession identity is read from the tracking stream and mapped onto the
    possession run, so the age is measured from the true start of the possession
    and no cutoff exists.
    """
    idx = load_index(match_id).copy()
    idx = idx.sort_values("frame_num", kind="mergesort")
    ev = events_with_possessions(match_id)

    pe = idx["possession_event_id"].ffill()
    keyed = ev.dropna(subset=["possession_event_id"]).drop_duplicates("possession_event_id")
    pe_to_pi = dict(zip(keyed["possession_event_id"].to_numpy(), keyed["possession_index"].to_numpy()))
    pi = pe.map(pe_to_pi)

    out = pd.DataFrame({
        "frame_num": idx["frame_num"].to_numpy(dtype=np.int64),
        "period": idx["period"].to_numpy(),
        "possession_event_id": pe.to_numpy(),
        "possession_index": pi.to_numpy(dtype=float),
    })
    return out.reset_index(drop=True)

def load_cache_unique(match_id: str) -> pd.DataFrame:
    """Frame cache with duplicate ``(frame_num, focal_is_home)`` rows removed.

    The stride-8 cache carries a small number of *exact* duplicate rows (about 0.7 %
    of rows; verified identical across every column).  They are harmless in
    substance but silently inflate every join on the frame key, so they are dropped
    once here, keeping the first occurrence.
    """
    match_id = str(match_id)
    if match_id not in _UNIQUE_CACHE:
        cache = load_cache(match_id)
        n0 = len(cache)
        cache = cache.drop_duplicates(subset=["frame_num", "focal_is_home"], keep="first")
        _UNIQUE_CACHE[match_id] = cache.reset_index(drop=True)
        if n0 != len(cache):
            _DUP_COUNTS[match_id] = n0 - len(cache)
    return _UNIQUE_CACHE[match_id]

def corrected_annotation(match_id: str) -> pd.DataFrame:
    """Cache rows with the corrected possession age and phase.

    Adds ``poss_index``, ``poss_first_frame``, ``age_s`` and ``phase``.  ``phase``
    is ``None`` when the possession start cannot be established, and such a state
    is not eligible for the primary experiment (brief section 3).
    """
    match_id = str(match_id)
    if match_id in _ANNOT_CACHE:
        return _ANNOT_CACHE[match_id]

    fps = match_fps(match_id)
    cache = load_cache_unique(match_id).copy()
    cache = cache.sort_values(["focal_is_home", "frame_num"]).reset_index(drop=True)

    fp = frame_possession(match_id)
    poss = possession_table(match_id).set_index("possession_index")

    frames = fp["frame_num"].to_numpy()
    pi = fp["possession_index"].to_numpy(dtype=float)

    slot = np.searchsorted(frames, cache["frame_num"].to_numpy(), side="right") - 1
    good = slot >= 0
    pi_at = np.full(len(cache), np.nan)
    pi_at[good] = pi[slot[good]]

    first = np.full(len(cache), np.nan)
    team_is_home = np.full(len(cache), np.nan)
    known = np.isfinite(pi_at)
    idx = pi_at[known].astype(int)
    if idx.size:
        first[known] = poss["first_frame"].reindex(idx).to_numpy(dtype=float)
        team_is_home[known] = poss["attacking_team_is_home"].reindex(idx).to_numpy(dtype=float)

    age_s = (cache["frame_num"].to_numpy() - first) / fps

    # the possession must belong to the team whose perspective the row is in
    same_team = team_is_home == cache["focal_is_home"].to_numpy(dtype=float)
    defined = np.isfinite(age_s) & same_team

    phase = np.where(defined, np.where(age_s < PHASE_TRANSITION_MAX_S, "transition", "settled"), None)

    out = cache.assign(
        poss_index=np.where(defined, pi_at, np.nan),
        poss_first_frame=np.where(defined, first, np.nan),
        age_s=np.where(defined, age_s, np.nan),
        phase=phase,
    )
    out["third"] = out["ball_x"].map(third_of)

    # Frozen slot-stability rule (op_common.annotate_cache): a jersey-slot change and
    # the guard band either side of it are treated as unstable tracking.
    jersey_cols = [f"fo_jersey_{i}" for i in range(10)]
    stable = np.ones(len(out), dtype=bool)
    for _persp, idx in out.groupby("focal_is_home").groups.items():
        block = out.loc[idx, jersey_cols].to_numpy()
        changed = np.zeros(len(block), dtype=bool)
        if len(block) > 1:
            changed[1:] = (block[1:] != block[:-1]).any(axis=1)
        bad = changed.copy()
        for shift in range(1, SLOT_CHANGE_GUARD_FRAMES + 1):
            bad |= np.roll(changed, shift) | np.roll(changed, -shift)
        stable[idx] = ~bad
    out["slot_stable"] = stable

    _ANNOT_CACHE[match_id] = out
    return out

def state_phase(match_id: str, frame: int, focal_is_home: bool) -> dict:
    """Corrected phase / possession age for one cache state."""
    a = corrected_annotation(match_id)
    row = a[(a["frame_num"] == int(frame)) & (a["focal_is_home"] == bool(focal_is_home))]
    if len(row) == 0:
        return {"phase": None, "age_s": None, "poss_index": None, "third": None, "found": False}
    r = row.iloc[0]
    return {
        "phase": r["phase"] if isinstance(r["phase"], str) else None,
        "age_s": float(r["age_s"]) if np.isfinite(r["age_s"]) else None,
        "poss_index": float(r["poss_index"]) if np.isfinite(r["poss_index"]) else None,
        "third": r["third"] if isinstance(r["third"], str) else None,
        "found": True,
    }

class TrackingView:
    """Per-perspective tracking arrays for one match, aligned to cache frames."""

    def __init__(self, match_id: str) -> None:
        self.match_id = str(match_id)
        self.fps = match_fps(self.match_id)
        ann = corrected_annotation(self.match_id)
        self.ann = ann
        self.axis: dict[bool, np.ndarray] = {}
        self.ball: dict[bool, np.ndarray] = {}
        self.in_poss: dict[bool, np.ndarray] = {}
        self.ball_in_play: dict[bool, np.ndarray] = {}
        self.poss_index: dict[bool, np.ndarray] = {}
        self.row_index: dict[bool, np.ndarray] = {}
        for persp, group in ann.groupby("focal_is_home"):
            order = np.argsort(group["frame_num"].to_numpy())
            persp = bool(persp)
            self.axis[persp] = group["frame_num"].to_numpy()[order]
            self.ball[persp] = group[["ball_x", "ball_y"]].to_numpy()[order]
            self.in_poss[persp] = group["in_possession"].to_numpy(dtype=bool)[order]
            self.ball_in_play[persp] = group["ball_in_play"].to_numpy(dtype=bool)[order]
            self.poss_index[persp] = group["poss_index"].to_numpy(dtype=float)[order]
            self.row_index[persp] = group.index.to_numpy()[order]

    def snap(self, raw_frame: float, persp: bool) -> tuple[int | None, int]:
        """Nearest cache frame and its raw-frame offset."""
        axis = self.axis[bool(persp)]
        if axis.size == 0 or not np.isfinite(raw_frame):
            return None, 10 ** 6
        slot = int(np.clip(np.searchsorted(axis, raw_frame), 0, axis.size - 1))
        left = max(slot - 1, 0)
        pick = left if abs(axis[left] - raw_frame) <= abs(axis[slot] - raw_frame) else slot
        return int(axis[pick]), int(abs(axis[pick] - raw_frame))

    def at(self, raw_frame: float, persp: bool) -> dict | None:
        cf, off = self.snap(raw_frame, persp)
        if cf is None:
            return None
        persp = bool(persp)
        pos = int(np.searchsorted(self.axis[persp], cf))
        return {
            "cache_frame": cf,
            "offset_raw_frames": off,
            "ball": self.ball[persp][pos].copy(),
            "in_possession": bool(self.in_poss[persp][pos]),
            "ball_in_play": bool(self.ball_in_play[persp][pos]),
            "poss_index": float(self.poss_index[persp][pos]) if np.isfinite(self.poss_index[persp][pos]) else None,
        }

    def slice(self, raw_frame_lo: float, raw_frame_hi: float, persp: bool) -> dict:
        """Cache frames in ``(lo, hi]`` for one perspective."""
        axis = self.axis[bool(persp)]
        lo = int(np.searchsorted(axis, raw_frame_lo, side="right"))
        hi = int(np.searchsorted(axis, raw_frame_hi, side="right"))
        persp = bool(persp)
        return {
            "frames": axis[lo:hi],
            "ball": self.ball[persp][lo:hi],
            "in_possession": self.in_poss[persp][lo:hi],
            "ball_in_play": self.ball_in_play[persp][lo:hi],
            "poss_index": self.poss_index[persp][lo:hi],
        }

    def state(self, raw_frame: float, persp: bool):
        cf, off = self.snap(raw_frame, persp)
        if cf is None:
            return None, None, off
        from obso.state import state_from_cache_row

        persp = bool(persp)
        pos = int(np.searchsorted(self.axis[persp], cf))
        row = self.ann.loc[self.row_index[persp][pos]]
        try:
            return state_from_cache_row(row.to_dict()), cf, off
        except (ValueError, KeyError, TypeError):
            return None, cf, off

def view(match_id: str) -> TrackingView:
    match_id = str(match_id)
    if match_id not in _VIEW_CACHE:
        _VIEW_CACHE[match_id] = TrackingView(match_id)
    return _VIEW_CACHE[match_id]

def detect_units(xs: np.ndarray, min_unit: int = 2) -> dict:
    """Partition the 10 outfield defenders into three contiguous 1-D groups.

    Exact rule of brief section 9: choose split indices ``(i, j)`` with
    ``i >= 2``, ``j - i >= 2``, ``10 - j >= 2`` minimising the summed within-group
    SSE, ties broken lexicographically.  Groups are labelled by mean x, and the
    rear (goal-side) boundary of a unit is its maximum x.
    """
    xs = np.asarray(xs, dtype=float)
    order = np.argsort(xs, kind="mergesort")
    s = xs[order]
    n = len(s)
    if n != 10:
        raise ValueError(f"unit detection needs exactly 10 outfield defenders, got {n}")

    def sse(seg: np.ndarray) -> float:
        if seg.size == 0:
            return 0.0
        return float(((seg - seg.mean()) ** 2).sum())

    best = None
    for i in range(2, n - 3):
        for j in range(i + 2, n - 1):
            if n - j < 2:
                continue
            total = sse(s[:i]) + sse(s[i:j]) + sse(s[j:])
            if best is None or total < best[0] - 1e-12:
                best = (total, i, j)
            elif abs(total - best[0]) <= 1e-12 and (i, j) < (best[1], best[2]):
                best = (total, i, j)
    if best is None:  # pragma: no cover - guarded by n == 10
        raise ValueError("no feasible 3-way split")

    total, i, j = best
    segs = [s[:i], s[i:j], s[j:]]
    labels = ["front", "midfield", "back"]
    units = {}
    for label, seg in zip(labels, segs):
        members = order[:i] if label == "front" else (order[i:j] if label == "midfield" else order[j:])
        units[label] = {
            "size": int(seg.size),
            "mean_x": float(seg.mean()),
            "sse": float(sse(seg)),
            "boundary_x": float(seg.max()),
            "near_x": float(seg.min()),
            "player_indices": [int(k) for k in members],
        }
    gaps = {
        "front_to_midfield_m": float(units["midfield"]["near_x"] - units["front"]["boundary_x"]),
        "midfield_to_back_m": float(units["back"]["near_x"] - units["midfield"]["boundary_x"]),
    }
    return {"splits": [int(i), int(j)], "total_sse": float(total), "units": units, "gaps": gaps}

def _family_and_completion(row: pd.Series) -> tuple[str | None, bool | None]:
    """Action family and whether the ordinary outcome field marks completion."""
    kind = row.get("poss_event_type")
    if kind == "PA":
        outcome = row.get("pass_outcome_type")
        return FAMILY_PASS, (outcome == "C")
    if kind == "CR":
        return FAMILY_CROSS, (row.get("cross_outcome_type") == "C")
    if kind == "BC":
        return FAMILY_CARRY, (row.get("ball_carry_outcome") == "R")
    return None, None

def candidate_actions(match_id: str) -> pd.DataFrame:
    """Every realized action eligible to be tested for CAP (brief section 8).

    Excludes set pieces, non-event passages, clearances and events without a
    reliable release or end frame.  Does **not** consult ``linesBrokenType``.
    """
    ev = events_with_possessions(match_id).reset_index(drop=True)
    fps = match_fps(match_id)

    fam = []
    complete = []
    for _, row in ev.iterrows():
        f, c = _family_and_completion(row)
        fam.append(f)
        complete.append(c)
    ev = ev.assign(family=fam, family_complete=complete)

    # endpoint = the next event row in the flattened stream
    nxt = ev.shift(-1)
    ev = ev.assign(
        end_event_type=nxt["poss_event_type"],
        end_team_id=nxt["team_id"],
        end_frame=nxt["frame_num"],
        end_possession_index=nxt["possession_index"],
        end_event_ball_x=nxt["event_ball_x"],
        end_event_ball_y=nxt["event_ball_y"],
        end_game_event_id=nxt["game_event_id"],
    )

    keep = (
        ev["family"].notna()
        & ev["period"].isin((1, 2))
        & ev["possession_index"].notna()
        & ev["frame_num"].notna()
        & ev["end_frame"].notna()
        & ~ev["non_event"].fillna(False).astype(bool)
        & ev["setpiece_type"].astype(str).eq("O")
        & ev["team_id"].notna()
    )
    out = ev.loc[keep].copy()
    out["release_frame"] = out["frame_num"].astype(float)
    out["endpoint_frame"] = out["end_frame"].astype(float)
    out["release_to_endpoint_s"] = (out["endpoint_frame"] - out["release_frame"]) / fps
    out["match_id"] = str(match_id)
    return out.reset_index(drop=True)

def label_cap(match_id: str) -> pd.DataFrame:
    """Compute the CAP family of labels for every candidate action.

    Returns one row per candidate with the geometry, the controlled-endpoint test,
    the advantageous-continuation test and the four nested labels.  No Fragility
    quantity is touched.
    """
    match_id = str(match_id)
    tv = view(match_id)
    fps = tv.fps
    cand = candidate_actions(match_id)

    # shots by the attacking team, hoisted: needed both for the retention window
    # (a shot ends it early) and for the advantageous-continuation test.
    ev_all = events_with_possessions(match_id)
    shot_ev = ev_all[ev_all["poss_event_type"] == "SH"]
    shots_by_team: dict = {}
    for team_id, group in shot_ev.groupby("team_id"):
        shots_by_team[team_id] = np.sort(group["frame_num"].dropna().to_numpy(dtype=float))

    rows: list[dict] = []
    for _, a in cand.iterrows():
        persp = bool(a["home_team"])
        rec: dict = {
            "match_id": match_id,
            "game_event_id": a["game_event_id"],
            "possession_event_id": a["possession_event_id"],
            "possession_index": float(a["possession_index"]),
            "period": int(a["period"]),
            "team_id": a["team_id"],
            "team_name": a["team_name"],
            "attacking_team_is_home": persp,
            "player_name": a.get("player_name"),
            "family": a["family"],
            "family_complete": bool(a["family_complete"]),
            "release_frame": float(a["release_frame"]),
            "endpoint_frame": float(a["endpoint_frame"]),
            "release_to_endpoint_s": float(a["release_to_endpoint_s"]),
        }

        start = tv.at(a["release_frame"], persp)
        end = tv.at(a["endpoint_frame"], persp)
        if start is None or end is None:
            rec["excluded"] = "no_tracking_frame"
            rows.append(rec)
            continue
        rec["cache_frame"] = start["cache_frame"]
        rec["sync_offset_raw_frames"] = int(start["offset_raw_frames"])
        rec["sync_offset_s"] = float(start["offset_raw_frames"]) / fps
        rec["endpoint_cache_frame"] = end["cache_frame"]
        rec["endpoint_sync_offset_raw_frames"] = int(end["offset_raw_frames"])
        rec["x_start"] = float(start["ball"][0])
        rec["y_start"] = float(start["ball"][1])
        rec["x_end"] = float(end["ball"][0])
        rec["y_end"] = float(end["ball"][1])
        rec["release_in_possession"] = bool(start["in_possession"])
        rec["endpoint_in_possession"] = bool(end["in_possession"])
        rec["release_poss_index"] = start["poss_index"]
        rec["endpoint_poss_index"] = end["poss_index"]

        ph = state_phase(match_id, start["cache_frame"], persp)
        rec["phase"] = ph["phase"]
        rec["age_s"] = ph["age_s"]
        rec["third"] = ph["third"]

        # --- defensive units at t0
        st, _cf, _off = tv.state(a["release_frame"], persp)
        if st is None:
            rec["excluded"] = "no_state_at_release"
            rows.append(rec)
            continue
        def_x = np.asarray(st.positions[11:21, 0], dtype=float)
        try:
            units = detect_units(def_x)
        except ValueError:
            rec["excluded"] = "unit_detection_failed"
            rows.append(rec)
            continue
        rec["units"] = units["units"]
        rec["unit_gaps"] = units["gaps"]
        rec["unit_splits"] = units["splits"]
        rec["unit_sse"] = units["total_sse"]

        # --- geometric penetration
        x0, x1 = rec["x_start"], rec["x_end"]
        penetrated, ambiguous = [], []
        for label in ("front", "midfield", "back"):
            b = units["units"][label]["boundary_x"]
            if x0 <= b and x1 > b:
                penetrated.append(label)
                if abs(x1 - b) < BOUNDARY_AMBIGUOUS_M:
                    ambiguous.append(label)
        rec["penetrated_units"] = penetrated
        rec["boundary_ambiguous_units"] = ambiguous
        rec["boundary_ambiguous"] = bool(ambiguous)
        rec["penetration"] = bool(penetrated)
        rec["progress_m"] = float(x1 - x0)

        # --- controlled endpoint
        # The retention window is 1.0 s after reception, shortened if the attacking
        # team shoots sooner (brief section 11: "or until an attacking shot occurs
        # sooner").
        team_shots = shots_by_team.get(a["team_id"], np.array([], dtype=float))
        soon = team_shots[(team_shots > a["endpoint_frame"])
                          & (team_shots <= a["endpoint_frame"] + CONTROL_RETENTION_S * fps)]
        retention_end = float(soon.min()) if soon.size else a["endpoint_frame"] + CONTROL_RETENTION_S * fps
        seg = tv.slice(a["endpoint_frame"], retention_end, persp)
        end_pi = rec["endpoint_poss_index"]
        cont = (seg["poss_index"] == end_pi) & seg["in_possession"] & seg["ball_in_play"]
        rec["retention_frames"] = int(len(seg["frames"]))
        rec["retention_continued_frames"] = int(cont.sum())
        retention_ok = bool(len(seg["frames"]) > 0 and cont.all())
        rec["retention_s"] = (
            float((retention_end - a["endpoint_frame"]) / fps) if retention_ok else 0.0
        )
        rec["shot_ends_retention"] = bool(soon.size > 0)

        # The action must be *successfully received*: the very next event row must be
        # by the attacking team.  Without this, a pass the vendor marks completed but
        # whose successor row is the opponent's clearance can still pass the tracking
        # retention test when the attacking team recovers the loose ball, which
        # contradicts "the action is recorded as completed / successfully received"
        # (brief section 11) and "if possession immediately changes to the defender:
        # not controlled".
        end_team = a["end_team_id"]
        rec["endpoint_team_id"] = None if pd.isna(end_team) else end_team
        rec["endpoint_same_team"] = bool(
            not pd.isna(end_team) and end_team == a["team_id"]
        )
        rec["controlled"] = bool(a["family_complete"]) and rec["endpoint_same_team"] and retention_ok

        # --- advantageous continuation
        w_lo, w_hi = a["endpoint_frame"], a["endpoint_frame"] + ADVANTAGE_WINDOW_S * fps
        wseg = tv.slice(w_lo, w_hi, persp)
        same = (wseg["poss_index"] == end_pi) & wseg["in_possession"] & wseg["ball_in_play"]
        ball = wseg["ball"][same]
        rec["window_frames"] = int(len(wseg["frames"]))
        rec["window_continued_frames"] = int(same.sum())
        if ball.size:
            max_x = float(ball[:, 0].max())
            rec["max_future_x"] = max_x
            rec["future_progress_m"] = float(max_x - x1)
            in_box = (ball[:, 0] >= BOX_X) & (np.abs(ball[:, 1]) <= BOX_Y)
            rec["box_entry"] = bool(in_box.any())
        else:
            rec["max_future_x"] = None
            rec["future_progress_m"] = None
            rec["box_entry"] = False

        # shot by the attacking team inside the advantage window
        w_hi = a["endpoint_frame"] + ADVANTAGE_WINDOW_S * fps
        sf = team_shots[(team_shots > a["endpoint_frame"]) & (team_shots <= w_hi)]
        rec["shot"] = bool(sf.size > 0)
        rec["shot_frames"] = [float(x) for x in sf]

        progress = rec["future_progress_m"] if rec["future_progress_m"] is not None else -np.inf
        rec["adv_A_progress"] = bool(progress >= PROGRESS_PRIMARY_M)
        rec["adv_B_box"] = bool(rec["box_entry"])
        rec["adv_C_shot"] = bool(rec["shot"])
        rec["advantageous"] = bool(rec["adv_A_progress"] or rec["adv_B_box"] or rec["adv_C_shot"])

        rec["cap_core"] = bool(rec["penetration"] and rec["controlled"])
        rec["cap"] = bool(rec["cap_core"] and rec["advantageous"])
        rec["cap_strict_3m"] = bool(rec["cap_core"] and (
            progress >= PROGRESS_SENSITIVITY_M[0] or rec["adv_B_box"] or rec["adv_C_shot"]))
        rec["cap_strict_8m"] = bool(rec["cap_core"] and (
            progress >= PROGRESS_SENSITIVITY_M[1] or rec["adv_B_box"] or rec["adv_C_shot"]))
        rec["excluded"] = None
        rows.append(rec)

    out = pd.DataFrame(rows)
    if "excluded" not in out.columns:
        out["excluded"] = None
    out["match_id"] = match_id
    return out
