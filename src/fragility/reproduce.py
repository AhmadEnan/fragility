"""Recalculate submission results from derived scores and event links."""

from pathlib import Path
import json
import hashlib

import numpy as np
import pandas as pd

from .benchmark import average_precision, prep_arm, wauc
from .models import metrics_bundle
from .scoring import score

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/derived"
REFERENCE = ROOT / "results/reference"


def cohort_results(cohort):
    df = pd.read_parquet(DATA / f"{cohort}_predictions.parquet")
    features, predictions = score(cohort, DATA)
    assert features.match.equals(df.match)
    np.testing.assert_array_equal(
        features.Y_CAP_2S.to_numpy(bool), df.Y_CAP_2S.to_numpy(bool)
    )
    for column, values in predictions.items():
        np.testing.assert_allclose(values, df[column], rtol=0, atol=1e-12)
        df[column] = values
    links = pd.read_parquet(DATA / f"{cohort}_event_links.parquet")
    assert df.order.tolist() == list(range(len(df)))
    assert links.row.between(0, len(df) - 1).all()
    assert df.loc[links.row, "Y_CAP_2S"].all()
    assert set(links.row) == set(np.flatnonzero(df.Y_CAP_2S))
    y = df.Y_CAP_2S.to_numpy(float)
    rows = []
    for column in df.filter(regex="^p_"):
        p = df[column].to_numpy(float)
        assert np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all()
        order = np.lexsort((df.tie_order.to_numpy(), -p))
        k = int(np.ceil(0.1 * len(df)))
        selected = np.zeros(len(df), bool)
        selected[order[:k]] = True
        count = links.loc[selected[links.row], "event_key"].nunique()
        result = metrics_bundle(y, p)
        if cohort == "dev":
            result["pr_auc"] = average_precision(y, p)
        result.update(
            model=column[2:],
            events_captured=count,
            events_total=links.event_key.nunique(),
            review_states=k,
        )
        rows.append(result)
    result = pd.DataFrame(rows).set_index("model")
    expected = pd.read_csv(
        REFERENCE
        / ("MODEL_PERFORMANCE.csv" if cohort == "test" else "arm_performance.csv")
    )
    expected = expected.set_index("model" if cohort == "test" else "arm")
    for model in result.index:
        for metric, original in [
            ("roc_auc", "roc_auc" if cohort == "test" else "auc"),
            ("pr_auc", "pr_auc" if cohort == "test" else "ap"),
        ]:
            np.testing.assert_allclose(
                result.loc[model, metric],
                expected.loc[model, original],
                rtol=0,
                atol=1e-12,
            )
        if cohort == "dev":
            assert (
                result.loc[model, "events_captured"]
                == expected.loc[model, "events_captured"]
            )
    if cohort == "test":
        events = pd.read_csv(REFERENCE / "EVENT_CAPTURE.csv").set_index("model")
        assert result.events_captured.to_dict() == events.n_unique_captured.to_dict()
        assert result.events_total.eq(694).all()
    return result


def tactical_results(tactical_candidates=None):
    from .tactical import verify as verify_tactical
    if tactical_candidates:
        from .tactical import evaluate
        actions, evidence = evaluate(pd.read_parquet(tactical_candidates))
    else:
        actions, evidence = verify_tactical()
    actions = actions.loc[actions.evidence_strength.eq("A")]
    df = actions.loc[actions.metric.eq("SOG"), ["action_key", "case_id", "top10", "pre_sup"]].rename(columns={"top10": "SOG_TOP10", "pre_sup": "SOG_pre_sup"})
    pcg = actions.loc[actions.metric.eq("PCG"), ["action_key", "top10", "pre_sup"]].rename(columns={"top10": "PCG_TOP10", "pre_sup": "PCG_pre_sup"})
    df = df.merge(pcg, on="action_key", validate="one_to_one")
    output = OUTPUT
    output.mkdir(parents=True, exist_ok=True)
    actions.to_csv(output / "tactical_action_recovery.csv", index=False)
    evidence.to_parquet(output / "tactical_frame_evidence.parquet", index=False)
    assert len(df) == 20 and df.case_id.nunique() == 13
    assert df.SOG_TOP10.sum() == 13 and df.PCG_TOP10.sum() == 11
    assert df.SOG_pre_sup.sum() == df.PCG_pre_sup.sum() == 10
    extra = df[df.SOG_TOP10 & ~df.PCG_TOP10]
    assert len(extra) == 2 and not extra.SOG_pre_sup.any()
    groups = df.groupby("case_id", sort=True)
    counts = groups.size().to_numpy()
    deltas = (
        df.assign(delta=df.SOG_TOP10.astype(int) - df.PCG_TOP10.astype(int))
        .groupby("case_id", sort=True)
        .delta.sum()
        .to_numpy()
    )
    rng = np.random.default_rng(20260928)
    draws = rng.choice(len(counts), size=(10000, len(counts)), replace=True)
    bootstrap = deltas[draws].sum(axis=1) / counts[draws].sum(axis=1)
    ci = np.quantile(bootstrap, [0.025, 0.975])
    np.testing.assert_allclose(ci, [0, 0.23529411764705882], atol=1e-12, rtol=0)
    return {
        "sog_hits": 13,
        "pcg_hits": 11,
        "actions": 20,
        "pre_release_hits_each": 10,
        "bootstrap95": ci.tolist(),
    }


def development_interval():
    df = pd.read_parquet(DATA / "dev_predictions.parquet")
    for column, values in score("dev", DATA)[1].items():
        df[column] = values
    y = df.Y_CAP_2S.to_numpy(float)
    matches = sorted(df.match.unique())
    groups = [np.flatnonzero(df.match.eq(m)) for m in matches]
    prepared = [
        prep_arm(df[c].to_numpy(float), y) for c in ["p_M0", "p_M0+SOG(incumbent)"]
    ]
    rng = np.random.default_rng(20261001)
    differences = np.empty(10000)
    for i in range(len(differences)):
        draws = rng.choice(len(matches), size=len(matches), replace=True)
        indices = np.concatenate([groups[j] for j in draws])
        weights = np.bincount(indices, minlength=len(df)).astype(float)
        differences[i] = wauc(prepared[1], weights) - wauc(prepared[0], weights)
    ci = np.quantile(differences, [0.025, 0.975])
    expected = pd.read_csv(REFERENCE / "increments_m0.csv").set_index("arm")
    np.testing.assert_allclose(
        ci,
        expected.loc["M0+SOG(incumbent)", ["ci_lo", "ci_hi"]].to_numpy(float),
        rtol=0,
        atol=1e-12,
    )
    return ci.tolist()


OUTPUT = ROOT / "results/reproduced"


def verify(tactical_candidates=None):
    manifest = json.loads((DATA / "manifest.json").read_text())
    for name, entry in manifest.items():
        assert (
            hashlib.sha256((DATA / name).read_bytes()).hexdigest() == entry["sha256"]
        ), name
    fields = np.load(ROOT / "data/derived/figure1_plot.npz")
    illustration = json.loads((ROOT / "data/derived/figure1_plot.json").read_text())
    assert fields["C0"].shape == fields["gain"].shape == (32, 50)
    assert np.isfinite(fields["C0"]).all() and np.isfinite(fields["gain"]).all()
    np.testing.assert_allclose(
        fields["gain"].sum() / 1.5, illustration["selected_score"], rtol=0, atol=1e-12
    )
    test = cohort_results("test")
    dev = cohort_results("dev")
    assert test.n.eq(38751).all() and dev.n.eq(38035).all()
    gain = test.loc["M2", "events_captured"] / test.loc["M0", "events_captured"] - 1
    np.testing.assert_allclose(gain, 50 / 170, rtol=0, atol=1e-12)
    interval = development_interval()
    output = OUTPUT
    output.mkdir(parents=True, exist_ok=True)
    table = dev.reset_index().rename(
        columns={"model": "arm", "roc_auc": "auc", "pr_auc": "ap"}
    )
    table["event_capture_at_10"] = table.events_captured / table.events_total
    table.to_csv(output / "arm_performance.csv", index=False)
    pd.DataFrame(
        [
            {
                "arm": "M0+SOG(incumbent)",
                "d_auc": dev.loc["M0+SOG(incumbent)", "roc_auc"]
                - dev.loc["M0", "roc_auc"],
                "ci_lo": interval[0],
                "ci_hi": interval[1],
            }
        ]
    ).to_csv(output / "increments_m0.csv", index=False)
    report = {
        "held_out": test.reset_index().to_dict("records"),
        "development": dev.reset_index().to_dict("records"),
        "relative_event_gain": gain,
        "tactical": tactical_results(tactical_candidates),
        "development_auc_interval": interval,
    }
    report_path = ROOT / "results/verification.json" if OUTPUT == ROOT / "results/reproduced" else OUTPUT / "verification.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DATA)
    parser.add_argument("--output-root", type=Path, default=OUTPUT)
    parser.add_argument("--tactical-candidates", type=Path)
    args = parser.parse_args()
    DATA, OUTPUT = args.data_root, args.output_root
    verify(args.tactical_candidates)
    print("Submission results verified.")
