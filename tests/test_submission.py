"""Submission data integrity, provenance and result checks."""

import ast
import hashlib
import json
from pathlib import Path

from fragility.reproduce import verify
from fragility.features import alignment_features
from fragility.outcomes import label_states
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_input_hashes():
    directory = ROOT / "data/derived"
    manifest = json.loads((directory / "manifest.json").read_text())
    actual = {
        p.name
        for p in directory.iterdir()
        if p.suffix in {".csv", ".parquet", ".npz", ".json"}
        and p.name != "manifest.json"
    }
    assert actual == set(manifest)
    for name, entry in manifest.items():
        assert (
            hashlib.sha256((directory / name).read_bytes()).hexdigest()
            == entry["sha256"]
        )


def test_original_function_provenance():
    manifest = json.loads((ROOT / "results/source_manifest.json").read_text())
    for entry in manifest:
        tree = ast.parse((ROOT / entry["public_module"]).read_text(encoding="utf-8"))
        node = next(
            n
            for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name == entry["function"]
        )
        if ast.get_docstring(node):
            node.body = node.body[1:]
        digest = hashlib.sha256(
            ast.dump(node, include_attributes=False).encode()
        ).hexdigest()
        assert digest == entry["function_sha256"]


def test_current_abstract_results():
    report = verify()
    assert len(report["held_out"]) == 4
    assert len(report["development"]) == 6


def test_alignment_and_strict_future_release_window():
    alignment, top = alignment_features(
        np.array([[0.0, 1.0], [1.0, 0.0]]), np.array([90.0, 0.0]), np.array([2.0, 1.0])
    )
    assert np.isclose(alignment, 1.0) and np.isclose(top, 1.0)
    states = pd.DataFrame(
        {
            "fps": [30.0] * 3,
            "frame_num": [0, 30, 60],
            "poss_index": [1, 2, 1],
            "focal_is_home": [True] * 3,
        }
    )
    events = pd.DataFrame(
        {
            "release_frame": [60],
            "possession_index": [1],
            "attacking_team_is_home": [True],
        }
    )
    np.testing.assert_array_equal(
        label_states(states, events, 2.0, anchor="release_frame"), [True, False, False]
    )
