"""Original frozen eligibility, cadence, release labels and match-grouped folds."""
import numpy as np
import pandas as pd
from . import raw_cap as cc
CAP_PHASE_REQUIRED = "settled"
CAP_SYNC_MAX_RAW_FRAMES = 32
CADENCE_S = 1.0
N_FOLDS = 5

def eligible_frames(match_id: str) -> pd.DataFrame:
    """The frozen cohort-eligibility convention, recovered from the CAP pilot.

    A prediction state must be:
      * regular time (period in (1, 2)),
      * a settled structure (corrected possession age >= 5.0 s),
      * in possession, ball in play, jersey-slot stable,
      * attached to a defined possession run,
      * on the attacking team's perspective (guaranteed by `phase` being defined).
    """
    a = cc.corrected_annotation(match_id)
    m = (a["period"].isin([1, 2])
         & a["phase"].eq(CAP_PHASE_REQUIRED)
         & a["in_possession"].astype(bool)
         & a["ball_in_play"].astype(bool)
         & a["slot_stable"].astype(bool)
         & a["poss_index"].notna())
    return a.loc[m].copy()

def cadence_states(match_id: str) -> pd.DataFrame:
    """Deterministic ~1.0 s cadence: anchor at each possession's first eligible frame,
    then step to the next eligible frame at least ``CADENCE_S`` of RAW frames later."""
    el = eligible_frames(match_id)
    if el.empty:
        return el
    fps = cc.match_fps(match_id)
    min_raw_gap = int(round(CADENCE_S * fps))          # 29.97 -> 30 raw frames
    keep_parts = []
    for _pi, g in el.groupby("poss_index", sort=True):
        g = g.sort_values("frame_num")
        fr = g["frame_num"].to_numpy(dtype=np.int64)
        keep = np.zeros(len(g), dtype=bool)
        if len(fr):
            keep[0] = True
            last = fr[0]
            for k in range(1, len(fr)):
                if fr[k] - last >= min_raw_gap:
                    keep[k] = True
                    last = fr[k]
        keep_parts.append(g.loc[keep])
    out = pd.concat(keep_parts, ignore_index=True)
    out["match_id"] = str(match_id)
    out["fps"] = fps
    return out.reset_index(drop=True)

def cap_events(match_id: str) -> pd.DataFrame:
    """The frozen CAP **positives**, restricted to the frozen CAP cohort.

    Identical cohort filters to `08_fresh_cohort.eligible_action_rows` (not
    excluded, settled phase, not boundary-ambiguous, within the sync tolerance)
    **and** the frozen `cap` flag itself.

    The `cap` filter is not optional.  `label_cap` returns every action family in
    the match (1,074 rows for match 10510) of which only 74 carry `cap == True`,
    and only 46 of those survive the cohort filters — the count the CAP pilot
    stored.  Returning the eligible rows *without* the `cap` filter would treat
    every eligible action as an event, which inflated the CAP positive rate from
    ~3% to 41% and would have made the label mean "the attack continues" rather
    than "a penetration is realized".
    """
    lab = cc.label_cap(match_id)
    ok = lab[lab["excluded"].isna()]
    ok = ok[ok["phase"] == CAP_PHASE_REQUIRED]
    ok = ok[~ok["boundary_ambiguous"].astype(bool)]
    ok = ok[ok["sync_offset_raw_frames"] <= CAP_SYNC_MAX_RAW_FRAMES]
    ok = ok[ok["cap"].fillna(False).astype(bool)]
    return ok.reset_index(drop=True)

def label_states(states: pd.DataFrame, events: pd.DataFrame, horizon_s: float,
                 *, anchor: str = "release") -> np.ndarray:
    """Y(t) = 1 iff an event begins in (t, t + horizon].

    ``anchor='release'`` uses the event's release frame (the action begins);
    ``anchor='endpoint'`` uses the event's endpoint frame (the action completes),
    available only for the CAP label.
    """
    if states.empty:
        return np.zeros(0, dtype=bool)
    fps = float(states["fps"].iloc[0])
    span = horizon_s * fps
    t = states["frame_num"].to_numpy(dtype=float)
    poss = states["poss_index"].to_numpy(dtype=float)
    team = states["focal_is_home"].to_numpy(dtype=bool)
    y = np.zeros(len(states), dtype=bool)
    if events.empty or anchor not in events.columns:
        return y
    e_f = events[anchor].to_numpy(dtype=float)
    e_poss = events["possession_index"].to_numpy(dtype=float)
    e_team = events["attacking_team_is_home"].to_numpy(dtype=bool)
    ok = np.isfinite(e_f)
    e_f, e_poss, e_team = e_f[ok], e_poss[ok], e_team[ok]
    for i in range(len(states)):
        same = (e_team == team[i]) & (e_poss == poss[i])
        y[i] = bool(np.any(same & (e_f > t[i]) & (e_f <= t[i] + span)))
    return y

def assign_folds(match_ids, n_folds: int = N_FOLDS) -> dict[str, int]:
    """Deterministic match -> fold assignment.

    Unique match ids are sorted numerically and dealt round-robin into folds 0..k-1,
    so no match appears in two folds and the assignment depends on nothing but the
    sorted id list.
    """
    ids = sorted({str(m) for m in match_ids}, key=int)
    return {m: i % n_folds for i, m in enumerate(ids)}
