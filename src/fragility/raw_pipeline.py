"""Reconstruct the frozen cohorts and features from authorized tracking and events."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from obso.state import state_from_cache_row
from . import raw_cap as cap, raw_cohort as cohort
from .raw_io import safe_output

ROOT = Path(__file__).resolve().parents[2]
DEV = [str(m) for m in range(3812, 3843, 2)]
TEST = [str(m) for m in range(3844, 3860, 2)] + [str(m) for m in range(10502, 10518, 2)]


def build_match(mid):
    states = cohort.cadence_states(mid)
    if mid in TEST:
        exc = pd.read_csv(ROOT / "data/identity/test_window_exclusions.csv", dtype={"match_id": str})
        drop = np.zeros(len(states), bool)
        for r in exc.loc[exc.match_id.eq(mid)].itertuples(index=False):
            drop |= states.frame_num.between(int(r.frame_lo), int(r.frame_hi)).to_numpy()
        states = states.loc[~drop].copy()
    states["match_id"] = mid
    states["state_key"] = mid + "|" + states.frame_num.astype(int).astype(str) + "|" + states.focal_is_home.astype(bool).astype(str)
    events = cohort.cap_events(mid)
    states["Y_CAP_2S"] = cohort.label_states(states, events, 2.0, anchor="release_frame")
    events["event_key"] = [f"{mid}|{r.game_event_id}|{r.possession_event_id}|{int(r.release_frame)}" for r in events.itertuples(index=False)]
    # Preserve all qualified releases, including many-to-many predecessor links.
    links = []
    for r in states.itertuples(index=False):
        e = events.loc[events.attacking_team_is_home.eq(bool(r.focal_is_home))
                       & events.possession_index.eq(r.poss_index)
                       & events.release_frame.gt(r.frame_num)
                       & events.release_frame.le(r.frame_num + 2.0 * r.fps)]
        links.extend({"state_key": r.state_key, "event_key": k} for k in e.event_key)
    keep = ["state_key", "match_id", "frame_num", "focal_is_home", "period", "poss_index", "age_s", "fps", "Y_CAP_2S"]
    return states[keep].reset_index(drop=True), pd.DataFrame(links, columns=["state_key", "event_key"])


def solve_features(states, annotation):
    from .fast_sog import solve_state_res0, state_scores_res0
    from .features import m0_features, alignment_features
    from .research_operator import GRID, StructuralOperator
    lookup = {(int(r["frame_num"]), bool(r["focal_is_home"])): r for r in annotation.to_dict("records")}
    rows = []
    for r in states.itertuples(index=False):
        rec = {"state_key": r.state_key, "solve_failed": False}
        try:
            state = state_from_cache_row(lookup[(int(r.frame_num), bool(r.focal_is_home))])
            op = StructuralOperator(state)
            rec.update(m0_features(state, op.base, op.base.control, GRID, float(r.age_s)))
            res = solve_state_res0(state)
            summary = state_scores_res0(res)
            rec.update({"F_SOG" if k == "F_RES0" else k: summary[k] for k in
                        ["F_RES0", "R_MAX", "R_MEDIAN", "TOP_CONCENTRATION", "TOP_GAP", "PLAYER_CONCENTRATION"]})
            ok = np.asarray(res["valid_primary"], bool) & np.isfinite(res["R_RES0"])
            values, players, dirs = res["R_RES0"][ok], res["attacker_index"][ok], res["direction_deg"][ok]
            unique = np.unique(players)
            q = np.array([values[players == p].max() for p in unique])
            best = np.array([dirs[players == p][np.argmax(values[players == p])] for p in unique])
            rec["BEST_ALIGNMENT"], rec["TOP_PLAYER_ALIGNMENT"] = alignment_features(state.velocities[unique], best, q) if len(unique) else (np.nan, np.nan)
        except (ValueError, KeyError, TypeError, RuntimeError, FloatingPointError) as exc:
            rec.update(solve_failed=True, solve_error=f"{type(exc).__name__}: {exc}")
        rows.append(rec)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("raw_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--cache-root", type=Path)
    ap.add_argument("--index-root", type=Path)
    ap.add_argument("--stage", choices=["cohort", "features", "comparators"], default="cohort")
    ap.add_argument("--matches", nargs="+")
    ap.add_argument("--limit", type=int, help="Bounded verification only; never a full-study output")
    args = ap.parse_args()
    inputs = [args.raw_root] + [v for v in (args.cache_root, args.index_root) if v]
    out = safe_output(args.output, *inputs)
    cache_root = args.cache_root or out / "private_cache"
    index_root = args.index_root or out / "private_index"
    mids = args.matches or (DEV if args.stage == "comparators" else DEV + TEST)
    if not set(mids) <= set(DEV + TEST):
        ap.error("Only the frozen match split is accepted")
    all_states, all_links = [], []
    for mid in mids:
        if not (cache_root / f"match_{mid}_stride8.parquet").exists():
            if args.cache_root:
                raise FileNotFoundError(f"Missing cache for {mid} in explicit read-only cache root")
            from .preprocessing import build_frame_cache
            built = build_frame_cache(str(args.raw_root), str(cache_root), [mid], stride=8)
            if mid not in built:
                raise RuntimeError(f"Tracking preprocessing failed: {mid}")
        if not (index_root / f"event_frame_index_{mid}.parquet").exists():
            if args.index_root:
                raise FileNotFoundError(f"Missing index for {mid} in explicit read-only index root")
            from .raw_index import build
            build(mid, args.raw_root, index_root)
        cap.configure(args.raw_root, cache_root, index_root)
        states, links = build_match(mid)
        if args.limit:
            states = states.iloc[:args.limit].copy()
            links = links.loc[links.state_key.isin(states.state_key)]
        if args.stage == "features":
            features = solve_features(states, cap.corrected_annotation(mid))
            features.to_parquet(out / f"features_{mid}.parquet", index=False)
        elif args.stage == "comparators":
            from .comparators import extract_match
            retained = pd.read_parquet(ROOT / "data/identity/row_identity.parquet")
            states = states.loc[states.state_key.isin(retained.state_key)].copy()
            extract_match(mid, states, cap.corrected_annotation(mid)).to_parquet(out / f"comparators_{mid}.parquet", index=False)
        states.to_parquet(out / f"cohort_{mid}.parquet", index=False)
        links.to_parquet(out / f"event_links_{mid}.parquet", index=False)
        all_states.append(states)
        all_links.append(links)
        print(f"{mid}: {len(states)} sampled states, {int(states.Y_CAP_2S.sum())} positives, {links.event_key.nunique()} reachable events", flush=True)
    pd.concat(all_states, ignore_index=True).to_parquet(out / "cohort.parquet", index=False)
    pd.concat(all_links, ignore_index=True).to_parquet(out / "event_links.parquet", index=False)
    (out / "run.json").write_text(json.dumps({"matches": mids, "stage": args.stage,
        "bounded": args.limit is not None, "raw_root": str(args.raw_root.resolve())}, indent=2))


if __name__ == "__main__":
    main()
