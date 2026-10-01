"""Maintainer export of permitted derived inputs; reads, never imports, research code."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("research_root", type=Path)
    original = ap.parse_args().research_root
    identity, stats = [], {}
    for split in ["dev", "test"]:
        d = pd.read_parquet(original / f"outputs/exp029_sog_predictive_confirm/data/{split.upper()}_FEATURES.parquet")
        public = pd.read_parquet(ROOT / f"data/derived/{'train' if split == 'dev' else 'test'}_features.parquet")
        assert len(d) == len(public)
        key = d[["state_key", "match_id", "frame_num", "focal_is_home", "period", "poss_index"]].copy()
        key["split"], key["row"] = split, np.arange(len(d))
        key["public_match_id"] = public.match.to_numpy()
        key["global_match_id"] = split.upper() + "-" + key.public_match_id
        key["Y_CAP_2S"] = public.Y_CAP_2S.to_numpy(bool)
        key["fold"] = [i % 5 for i in pd.Categorical(d.match_id, categories=sorted(d.match_id.unique(), key=int)).codes] if split == "dev" else -1
        identity.append(key)
        for c in public.columns:
            if c in {"match", "Y_CAP_2S", "fold"}:
                continue
            x = d[c].to_numpy(float)
            if split == "dev":
                stats[c] = {"mean": float(np.nanmean(x)), "std": float(np.nanstd(x, ddof=0)) or 1.0}
            s = stats[c]
            np.testing.assert_allclose((x-s["mean"])/s["std"], public[c], rtol=0, atol=1e-10)
    p = ROOT / "data/identity"
    p.mkdir(exist_ok=True)
    pd.concat(identity, ignore_index=True).to_parquet(p / "row_identity.parquet", index=False)
    dev = pd.read_parquet(ROOT / "data/derived/dev_features.parquet")
    for c in ["EPV_AT_BALL", "EPV_WEIGHTED_CONTROL", "D_OBSO", "DAS"]:
        chunks = [pd.read_parquet(original / f"outputs/exp032_literature_benchmark/comparators_{m}.parquet") for m in sorted(identity[0].match_id.unique(), key=int)]
        raw = pd.concat(chunks, ignore_index=True).set_index("state_key").loc[identity[0].state_key]
        x = raw[c].to_numpy(float)
        stats[c] = {"mean": float(np.nanmean(x)), "std": float(np.nanstd(x, ddof=0)) or 1.0}
        np.testing.assert_allclose((x-stats[c]["mean"])/stats[c]["std"], dev[c], rtol=0, atol=1e-10)
    (p / "normalization.json").write_text(json.dumps({"recipe": "DEV mean and population standard deviation; preserves nonfinite values; no outcomes used", "features": stats}, indent=2))
    # Publish scalar candidate scores, never raw tracking, player coordinates or HDF5 fields.
    import h5py
    base = original / "outputs/EXP_SOG_GOLD20_CONFIRMATION_023/stage_b_raw"
    a = pd.read_parquet(base / "ALL_ACTION_ROWS.parquet")
    pcg = {}
    for file in sorted((base / "raw_fields").glob("*.h5")):
        with h5py.File(file) as h:
            ids = h["actions/action_id"][:]
            for start in range(0, len(ids), 256):
                delta = h["actions/dC"][start:start+256]
                mass = np.maximum(delta, 0).sum(axis=(1, 2))
                pcg.update(zip(ids[start:start+256].tolist(), mass.tolist()))
        print(f"Exported scalar PCG: {file.stem}", flush=True)
    a["PCG"] = [pcg.get(int(r.action_id), np.nan)/float(r.cost) for r in a.itertuples(index=False)]
    keep = ["action_id", "case_id", "state_id", "frame", "vendor_t", "jersey", "direction_deg", "radius", "cost", "valid_primary", "rejected", "offside_switch", "SOG", "PCG"]
    a[keep].to_parquet(ROOT / "data/derived/tactical_candidate_scores.parquet", index=False)
    print(f"Export complete: {len(a)} candidates")


if __name__ == "__main__":
    main()
