"""Portable checks for the exported source and frozen cohort identities."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def verify_sources():
    manifest = json.loads((ROOT / "results/source_export_manifest.json").read_text())
    for entry in manifest:
        path = ROOT / entry["target"]
        if "symbol" in entry:
            nodes = {n.name: n for n in ast.parse(path.read_text(encoding="utf-8-sig")).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
            digest = hashlib.sha256(ast.dump(nodes[entry["symbol"]], include_attributes=False).encode()).hexdigest()
            assert digest == entry["ast_sha256"], entry["target"] + ":" + entry["symbol"]
        else:
            assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["source_sha256"], entry["target"]
    ids = pd.read_parquet(ROOT / "data/identity/row_identity.parquet")
    assert ids.state_key.is_unique
    assert set(ids.loc[ids.split.eq("dev"), "match_id"]).isdisjoint(ids.loc[ids.split.eq("test"), "match_id"])
    for split, count in [("dev", 38035), ("test", 38751)]:
        part = ids.loc[ids.split.eq(split)].sort_values("row")
        assert len(part) == count and part.row.tolist() == list(range(count))
        features = pd.read_parquet(ROOT / f"data/derived/{split}_features.parquet")
        np.testing.assert_array_equal(part.public_match_id, features.match)
        np.testing.assert_array_equal(part.Y_CAP_2S, features.Y_CAP_2S)
        if split == "dev":
            np.testing.assert_array_equal(part.fold, features.fold)
            assert part.groupby("match_id").fold.nunique().eq(1).all()
    return {"source_entries": len(manifest), "cohort_rows": len(ids), "disjoint_matches": True}


def verify_cohort(directory):
    """Compare freshly qualified raw events with released labels and link structure."""
    directory = Path(directory)
    states = pd.read_parquet(directory / "cohort.parquet").set_index("state_key")
    links = pd.read_parquet(directory / "event_links.parquet")
    ids = pd.read_parquet(ROOT / "data/identity/row_identity.parquet")
    result = {}
    for split in ["dev", "test"]:
        expected = ids.loc[ids.split.eq(split)].sort_values("row")
        observed = states.loc[expected.state_key]
        np.testing.assert_array_equal(observed.Y_CAP_2S.to_numpy(bool), expected.Y_CAP_2S.to_numpy(bool))
        lookup = dict(zip(expected.state_key, expected.row))
        actual = links.loc[links.state_key.isin(lookup)].copy()
        actual["row"] = actual.state_key.map(lookup)
        released = pd.read_parquet(ROOT / f"data/derived/{split}_event_links.parquet")
        # Each event is identified by its complete set of predecessor rows. Multisets
        # preserve two distinct releases even when they share the same predecessors.
        signatures = lambda d: Counter(tuple(sorted(g.row.tolist())) for _, g in d.groupby("event_key"))
        assert signatures(actual) == signatures(released), f"{split}: event-link structure differs"
        extras = set(states.loc[states.match_id.astype(str).isin(expected.match_id.astype(str))].index) - set(expected.state_key)
        result[split] = {"states": len(observed), "positives": int(observed.Y_CAP_2S.sum()),
            "events": actual.event_key.nunique(), "links": len(actual), "labels_exact": True,
            "event_link_structure_exact": True, "additional_sampled_states": len(extras)}
    return result


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cohort-root", type=Path)
    args = ap.parse_args()
    print(json.dumps(verify_cohort(args.cohort_root) if args.cohort_root else verify_sources(), indent=2))
