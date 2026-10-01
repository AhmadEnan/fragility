"""Recompute the Figure 1 control fields and selected action from licensed tracking."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from obso.state import state_from_cache_row
from .research_operator import StructuralOperator

ROOT = Path(__file__).resolve().parents[2]


def verify(cache_root):
    cache = pd.read_parquet(Path(cache_root) / "match_10507_stride8.parquet")
    row = cache.loc[cache.frame_num.eq(53427) & cache.focal_is_home].iloc[0]
    state = state_from_cache_row(row)
    op = StructuralOperator(state)
    player = state.jerseys.index("9")
    assert op.base.carrier_index is not None and state.jerseys[op.base.carrier_index] == "4"
    cf = state.positions[player] + np.array([1.5/np.sqrt(2), 1.5/np.sqrt(2)])
    c0 = np.clip(np.asarray(op.base.control, float), 0.0, 1.0)
    control, after = op.op._single_control(player, cf)
    assert bool(after[player]) == bool(state.offside[player])
    c1 = np.clip(control, 0.0, 1.0)
    gain = (1.0-c0) * np.maximum(c1-c0, 0.0)
    original = np.load(ROOT / "data/derived/figure1_plot.npz")
    expected = json.loads((ROOT / "data/derived/figure1_plot.json").read_text())["selected_score"]
    np.testing.assert_allclose(c0, original["C0"], atol=1e-12, rtol=0)
    np.testing.assert_allclose(gain, original["gain"], atol=1e-12, rtol=0)
    score = float(gain.sum()/1.5)
    np.testing.assert_allclose(score, expected, atol=1e-12, rtol=0)
    return {"match_id": 10507, "frame": 53427, "release_frame": 53454, "jersey": "9",
        "radius_m": 1.5, "direction_deg": 45, "score": score,
        "C0_max_abs_error": float(np.abs(c0-original["C0"]).max()),
        "gain_max_abs_error": float(np.abs(gain-original["gain"]).max()),
        "interpretation": "Spent illustrative example, centered velocities; route artwork represents static geometry."}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cache_root", type=Path)
    print(json.dumps(verify(ap.parse_args().cache_root), indent=2))
