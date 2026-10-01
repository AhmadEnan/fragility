"""Bridge freshly reconstructed research-unit features to the released classifier inputs."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .raw_io import safe_output
from .raw_cohort import assign_folds
from .raw_pipeline import DEV, TEST, ROOT


def fit_normalization(dev, columns):
    """Outcome-blind, DEV-only affine export; model imputation is a separate step."""
    return {c: {"mean": float(np.nanmean(dev[c].to_numpy(float))),
                "std": float(np.nanstd(dev[c].to_numpy(float), ddof=0)) or 1.0} for c in columns}


def normalize(frame, stats):
    return pd.DataFrame({c: (frame[c].to_numpy(float) - s["mean"]) / s["std"] for c, s in stats.items() if c in frame}, index=frame.index)


def export(cohort_root, feature_root, comparator_root, output):
    out = safe_output(output, cohort_root, feature_root, comparator_root)
    all_states = pd.read_parquet(Path(cohort_root) / "cohort.parquet")
    all_links = pd.read_parquet(Path(cohort_root) / "event_links.parquet")
    frames = {}
    schema = json.loads((ROOT / "data/identity/normalization.json").read_text())["features"]
    core = [c for c in schema if c not in {"EPV_AT_BALL", "EPV_WEIGHTED_CONTROL", "D_OBSO", "DAS"}]
    for split, mids in [("dev", DEV), ("test", TEST)]:
        if not set(mids) <= set(all_states.match_id.astype(str)):
            raise ValueError(f"Incomplete {split} cohort; bounded runs cannot become study inputs")
        features = pd.concat([pd.read_parquet(Path(feature_root) / f"features_{m}.parquet") for m in mids], ignore_index=True)
        good = features.loc[~features.solve_failed.astype(bool)].copy()
        states = all_states.loc[all_states.match_id.astype(str).isin(mids)].copy()
        # Only recorded solver failures may remove cohort rows. Retain their audit log.
        features.loc[features.solve_failed.astype(bool)].to_parquet(out / f"{split}_solve_failures.parquet", index=False)
        assert set(states.state_key) == set(features.state_key)
        frames[split] = states.merge(good.drop(columns=["solve_failed"]), on="state_key", validate="one_to_one")
        order = {mid: i for i, mid in enumerate(mids)}
        frames[split]["order"] = frames[split].match_id.astype(str).map(order)
        frames[split] = frames[split].sort_values(["order", "frame_num"], kind="stable").reset_index(drop=True)
    comparator = pd.concat([pd.read_parquet(Path(comparator_root) / f"comparators_{m}.parquet") for m in DEV], ignore_index=True)
    frames["dev"] = frames["dev"].merge(comparator, on="state_key", validate="one_to_one")
    stats = fit_normalization(frames["dev"], list(schema))
    models = json.loads((ROOT / "data/derived/models.json").read_text())
    fitted_models = {"dev": {}, "test": {}}
    from .benchmark import design
    from .models import fit_logistic, predict_logistic
    for split in ["dev", "test"]:
        frame = frames[split]
        table = normalize(frame, stats)
        mids = DEV if split == "dev" else TEST
        mapping = {mid: f"M{i:02d}" for i, mid in enumerate(mids)}
        table.insert(0, "Y_CAP_2S", frame.Y_CAP_2S.to_numpy(bool))
        table.insert(0, "match", frame.match_id.astype(str).map(mapping))
        if split == "dev":
            folds = assign_folds(DEV)
            table["fold"] = frame.match_id.astype(str).map(folds)
            train = table[["match", "Y_CAP_2S"] + core].copy()
            train.to_parquet(out / "train_features.parquet", index=False)
        table.to_parquet(out / f"{split}_features.parquet", index=False)
        rows = dict(zip(frame.state_key, np.arange(len(frame))))
        links = all_links.loc[all_links.state_key.isin(rows)].copy()
        links["row"] = links.state_key.map(rows)
        # Globally stable opaque event identity, preserving multi-release links.
        events = sorted(links.event_key.unique())
        event_mapping = {key: f"{split.upper()}-E{i:04d}" for i, key in enumerate(events)}
        links["event_key"] = links.event_key.map(event_mapping)
        links[["row", "event_key"]].to_parquet(out / f"{split}_event_links.parquet", index=False)
        predictions = table[["match", "Y_CAP_2S"]].copy()
        predictions.insert(0, "order", np.arange(len(table)))
        for name, specifications in models[split].items():
            specs = specifications if split == "dev" else [specifications]
            probability = np.full(len(table), np.nan)
            results = []
            for spec in specs:
                training = table.loc[table.fold.ne(spec["fold"])] if split == "dev" else pd.read_parquet(out / "train_features.parquet")
                selected = table.fold.eq(spec["fold"]).to_numpy() if split == "dev" else np.ones(len(table), bool)
                matrix, transform = design(training, spec["features"])
                fit = fit_logistic(matrix, training.Y_CAP_2S.to_numpy(float))
                evaluation, _ = design(table.loc[selected], spec["features"], transform)
                probability[selected] = predict_logistic(fit, evaluation)
                results.append({"features": spec["features"], "stats": transform,
                    "coef": np.asarray(fit["coef"]).tolist(), "intercept": float(fit["intercept"]),
                    **({"fold": spec["fold"]} if split == "dev" else {})})
            predictions["p_" + name] = probability
            fitted_models[split][name] = results if split == "dev" else results[0]
        predictions["tie_order"] = np.arange(len(table))
        predictions.to_parquet(out / f"{split}_predictions.parquet", index=False)
    (out / "models.json").write_text(json.dumps(fitted_models, indent=2))
    (out / "normalization.json").write_text(json.dumps({"features": stats}, indent=2))
    import hashlib
    manifest = {p.name: {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size}
                for p in sorted(out.iterdir()) if p.is_file() and p.name != "manifest.json"}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ["cohort_root", "feature_root", "comparator_root", "output"]:
        ap.add_argument(name, type=Path)
    args = ap.parse_args()
    print(export(args.cohort_root, args.feature_root, args.comparator_root, args.output))
