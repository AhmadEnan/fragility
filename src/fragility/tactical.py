"""Recompute documented-action recovery from candidate scores, never from hit flags."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from .tactical_summary import dir6, summarize

ROOT = Path(__file__).resolve().parents[2]
EVALUABLE = {"DIRECTLY_EVALUABLE", "OFFSIDE_CONFOUNDED_BUT_SCOREABLE"}


def cell_landscapes(actions, metric):
    v = actions.loc[actions.valid_primary.astype(bool) & np.isfinite(actions[metric])].copy()
    v["dir6"] = v.direction_deg.map(dir6)
    v["jersey_s"] = v.jersey.astype(str)
    # Sort is stable; ties over radii choose the smallest radius.
    keys = ["case_id", "state_id", "jersey_s", "dir6"]
    best = v.sort_values([metric, "radius"], ascending=[False, True], kind="stable").drop_duplicates(keys)
    cell = best[keys + ["frame", "vendor_t", metric, "radius"]].rename(columns={metric: "Q", "radius": "best_radius"})
    parts = []
    for _, g in cell.groupby(["case_id", "state_id"], sort=True):
        g = g.copy()
        q = g.Q.to_numpy(float)
        g["rank"] = 1 + (q[None, :] > q[:, None]).sum(axis=1)
        g["M"] = len(g)
        g["percentile"] = 1.0 - (g["rank"] - 1) / max(len(g) - 1, 1)
        parts.append(g)
    return pd.concat(parts, ignore_index=True)


def evaluate(actions, targets=None, alignments=None):
    targets = pd.read_csv(ROOT / "data/validation/player_action_freeze.csv", dtype={"shirt_number": str}) if targets is None else targets
    alignments = pd.read_csv(ROOT / "data/validation/case_alignment_freeze.csv") if alignments is None else alignments
    releases = dict(zip(alignments.case_id, alignments.key_release_frame))
    states = actions[["case_id", "state_id", "frame", "vendor_t"]].drop_duplicates().sort_values("frame")
    summaries, evidence = [], []
    for metric in ["SOG", "PCG"]:
        cells = cell_landscapes(actions, metric)
        for p in targets.itertuples(index=False):
            if p.evaluability not in EVALUABLE:
                continue
            aid = f"{p.case_id}|{p.shirt_number}|{dir6(p.frozen_direction_deg):.6f}"
            win = states.loc[states.case_id.eq(p.case_id) & states.frame.between(p.movement_eval_start_frame - 8, p.movement_eval_end_frame + 8)].copy()
            selected = cells.loc[cells.case_id.eq(p.case_id) & cells.jersey_s.eq(str(p.shirt_number)) & cells.dir6.eq(dir6(p.frozen_direction_deg))]
            g = win.merge(selected[["state_id", "Q", "rank", "M", "percentile", "best_radius"]], on="state_id", how="left", validate="one_to_one").sort_values("frame")
            g["pre_release"] = g.frame.le(releases[p.case_id])
            g["action_key"], g["metric"] = aid, metric
            evidence.append(g)
            # No valid-frame smoothing: missing candidates break the consecutive run.
            if np.isfinite(g.percentile).any():
                summary = summarize(g, g.pre_release.to_numpy(bool))
            else:
                summary = {"top10": False, "pre_sup": False, "n_valid": 0, "run": 0, "pre_run": 0}
            summaries.append({"action_key": aid, "case_id": p.case_id, "player_name": p.player_name,
                "shirt_number": str(p.shirt_number), "direction_deg": dir6(p.frozen_direction_deg),
                "source_id": p.source_id, "evidence_strength": p.evidence_strength,
                "evaluability": p.evaluability, "metric": metric, **summary})
    return pd.DataFrame(summaries), pd.concat(evidence, ignore_index=True)


def verify():
    actions = pd.read_parquet(ROOT / "data/derived/tactical_candidate_scores.parquet")
    summary, evidence = evaluate(actions)
    ref = pd.read_csv(ROOT / "data/validation/action_recovery_reference.csv", dtype={"shirt_number": str})
    for metric in ["SOG", "PCG"]:
        actual = summary.loc[summary.metric.eq(metric)]
        joined = actual.merge(ref, on=["case_id", "player_name", "shirt_number"], validate="one_to_one")
        assert len(joined) == 29
        np.testing.assert_array_equal(joined.top10, joined[f"{metric}_TOP10"])
        np.testing.assert_array_equal(joined.pre_sup, joined[f"{metric}_pre_sup"])
        np.testing.assert_allclose(joined.peak, joined[f"{metric}_peak"], atol=1e-12, rtol=0)
        assert int(actual.loc[actual.evidence_strength.eq("A"), "top10"].sum()) == {"SOG": 13, "PCG": 11}[metric]
        assert int(actual.loc[actual.evidence_strength.eq("A"), "pre_sup"].sum()) == 10
    return summary, evidence


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=ROOT / "results/reproduced")
    ap.add_argument("--candidates", type=Path, help="Fresh licensed-data candidate table instead of the included table")
    args = ap.parse_args()
    summary, evidence = evaluate(pd.read_parquet(args.candidates)) if args.candidates else verify()
    args.output.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output / "tactical_action_recovery.csv", index=False)
    evidence.to_parquet(args.output / "tactical_frame_evidence.parquet", index=False)
    a = summary.loc[summary.evidence_strength.eq("A")]
    print(a.groupby("metric")[["top10", "pre_sup"]].sum().to_string())


if __name__ == "__main__":
    main()
