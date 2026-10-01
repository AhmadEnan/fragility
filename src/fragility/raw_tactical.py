"""Regenerate the frozen tactical candidate scores from an authorized stride-8 cache."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from obso.state import state_from_cache_row
from .raw_io import safe_output
from .tactical_solver import solve_state_sog_pcg
from .tactical import ROOT, evaluate


def solve_case(case, cache):
    focal = str(case.attacking_team) == str(case.home_team)
    # Original stage-B lookup kept the final exact duplicate; duplicates are equal.
    cache = cache.loc[cache.focal_is_home.eq(focal)].drop_duplicates("frame_num", keep="last")
    cache = cache.loc[cache.frame_num.between(int(case.safety_window_start_frame), int(case.safety_window_end_frame))].sort_values("frame_num")
    if cache.empty:
        raise ValueError(f"No analysis frames for {case.case_id}")
    records = []
    for r in cache.to_dict("records"):
        try:
            state = state_from_cache_row(r)
        except (ValueError, KeyError, TypeError):
            continue  # Original stage-B omitted unbuildable states, before target evaluation.
        scores = solve_state_sog_pcg(state)
        n = len(scores["R_RES0"])
        d = pd.DataFrame({"case_id": [case.case_id] * n,
            "state_id": [f"{case.case_id}|{case.pff_match_id}|{state.frame_num}"] * n,
            "frame": state.frame_num, "vendor_t": float(state.frame_num) / 29.9697,
            "jersey": scores["jersey"], "direction_deg": scores["direction_deg"],
            "radius": scores["radius"], "cost": scores["cost"],
            "valid_primary": scores["valid_primary"], "rejected": scores["rejected"],
            "offside_switch": scores["offside_switch"], "SOG": scores["R_RES0"], "PCG": scores["PCG"]})
        records.append(d)
    if not records:
        raise ValueError(f"No buildable states for {case.case_id}")
    return pd.concat(records, ignore_index=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cache_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--raw-root", type=Path, help="Build missing caches from privately held provider data")
    ap.add_argument("--cases", nargs="+", help="Bounded case verification only")
    args = ap.parse_args()
    out = safe_output(args.output, args.cache_root, *([args.raw_root] if args.raw_root else []))
    cases = pd.read_csv(ROOT / "data/validation/case_alignment_freeze.csv", dtype={"pff_match_id": str})
    if args.cases:
        if not set(args.cases) <= set(cases.case_id):
            ap.error("Unknown case ID")
        cases = cases.loc[cases.case_id.isin(args.cases)]
    frames = []
    for c in cases.itertuples(index=False):
        path = args.cache_root / f"match_{c.pff_match_id}_stride8.parquet"
        if not path.exists():
            if not args.raw_root:
                raise FileNotFoundError(path)
            from .preprocessing import build_frame_cache
            built = build_frame_cache(str(args.raw_root), str(out / "private_cache"), [c.pff_match_id], stride=8)
            path = Path(built[c.pff_match_id])
        frame = solve_case(c, pd.read_parquet(path))
        frame.to_parquet(out / f"candidates_{c.case_id}.parquet", index=False)
        frames.append(frame)
        print(f"{c.case_id}: {frame.state_id.nunique()} states, {len(frame)} candidates", flush=True)
    actions = pd.concat(frames, ignore_index=True)
    actions.to_parquet(out / "tactical_candidate_scores.parquet", index=False)
    targets = pd.read_csv(ROOT / "data/validation/player_action_freeze.csv", dtype={"shirt_number": str})
    targets = targets.loc[targets.case_id.isin(cases.case_id)]
    summary, evidence = evaluate(actions, targets, cases)
    summary.to_csv(out / "tactical_action_recovery.csv", index=False)
    evidence.to_parquet(out / "tactical_frame_evidence.parquet", index=False)
    (out / "run.json").write_text(json.dumps({"cases": cases.case_id.tolist(), "bounded": args.cases is not None,
        "states": int(actions.state_id.nunique()), "candidates": len(actions)}, indent=2))


if __name__ == "__main__":
    main()
