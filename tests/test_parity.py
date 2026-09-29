"""Numerical parity tests against frozen canonical experiment outputs.

Asserts exact equality or tight numerical tolerances for all reported claims.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from fragility.config import CANONICAL_CONFIG
from fragility.pff import load_synthetic_state, load_pff_state
from fragility.sog import score_state, aggregate_cells
from fragility.validation import (
    evaluate_tactical_recovery,
    evaluate_gold20,
    evaluate_ablation,
    evaluate_grid_stability,
    evaluate_state_fragility,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DERIVED_DIR = REPO_ROOT / "data" / "derived"
RESULTS_PATH = REPO_ROOT / "results" / "expected_results.json"


@pytest.fixture
def expected() -> dict:
    assert RESULTS_PATH.exists(), f"Missing {RESULTS_PATH}"
    with open(RESULTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_gold20_claim_c01_and_c02_parity(expected):
    pa_path = DERIVED_DIR / "action_recovery.csv"
    cs_path = DERIVED_DIR / "case_summary.csv"
    assert pa_path.exists()
    assert cs_path.exists()

    pa = pd.read_csv(pa_path)
    cs = pd.read_csv(cs_path)

    res = evaluate_tactical_recovery(pa, cs)
    exp = expected["claims"]["C01_gold20_action_recovery"]

    # Bank A primary claims
    assert res["A"]["evaluable_actions"] == exp["a_bank"]["evaluable_actions"]
    assert res["A"]["top10_supported"] == exp["a_bank"]["top10_supported"]
    assert np.isclose(res["A"]["action_rate"], exp["a_bank"]["action_rate"], atol=1e-6)
    assert np.isclose(res["A"]["wilson95"][0], exp["a_bank"]["wilson95_ci"][0], atol=1e-5)
    assert np.isclose(res["A"]["wilson95"][1], exp["a_bank"]["wilson95_ci"][1], atol=1e-5)
    assert np.isclose(res["A"]["median_peak"], exp["a_bank"]["median_peak_percentile"], atol=1e-5)
    assert np.isclose(res["A"]["primary_exploiter_rate"], exp["a_bank"]["primary_exploiter_rate"], atol=1e-5)

    # Space creators vs primary exploiters (Claim C02)
    exp_c02 = expected["claims"]["C02_gold20_space_creators"]
    assert res["A"]["space_creator_hits"] == exp_c02["space_creator_hits"]
    assert res["A"]["space_creator_rate"] == exp_c02["space_creator_rate"]

    # Bank B secondary claims
    assert res["B"]["evaluable_actions"] == exp["b_bank"]["evaluable_actions"]
    assert res["B"]["top10_supported"] == exp["b_bank"]["top10_supported"]
    assert np.isclose(res["B"]["action_rate"], exp["b_bank"]["action_rate"], atol=1e-5)


def test_ablation_claim_c03_parity(expected):
    abl_path = DERIVED_DIR / "residual_ablation.csv"
    assert abl_path.exists()

    abl = pd.read_csv(abl_path)
    res = evaluate_ablation(abl)
    exp = expected["claims"]["C03_residual_weight_ablation"]

    assert res["sog_hits"] == exp["sog_hits"]
    assert res["pcg_hits"] == exp["pcg_hits"]
    assert np.isclose(res["sog_rate"], exp["sog_rate"], atol=1e-6)
    assert np.isclose(res["pcg_rate"], exp["pcg_rate"], atol=1e-6)
    assert np.isclose(res["delta_pp"], exp["delta_rate_pp"], atol=1e-6)
    assert np.isclose(res["median_peak_sog"], exp["median_peak_sog"], atol=1e-5)
    assert np.isclose(res["median_peak_pcg"], exp["median_peak_pcg"], atol=1e-5)


def test_grid_convergence_claim_c04_parity(expected):
    gs_path = DERIVED_DIR / "grid_stability.csv"
    assert gs_path.exists()

    gs = pd.read_csv(gs_path)
    res = evaluate_grid_stability(gs)
    exp = expected["claims"]["C04_grid_convergence"]

    assert res["n_states"] == exp["n_states"]
    assert np.isclose(res["median_spearman"], exp["median_action_spearman"], atol=1e-4)
    assert np.isclose(res["min_spearman"], exp["min_action_spearman"], atol=1e-4)
    assert np.isclose(res["median_top10_jaccard"], exp["median_top10_jaccard"], atol=1e-4)
    assert np.isclose(res["best_player_agreement"], exp["best_player_agreement"], atol=1e-6)


def test_state_fragility_claim_c05_parity(expected):
    cp_path = DERIVED_DIR / "counterattack_pairs.csv"
    assert cp_path.exists()

    cp = pd.read_csv(cp_path)
    res = evaluate_state_fragility(cp)
    exp = expected["claims"]["C05_state_fragility_path_accessibility"]

    assert res["n_pairs"] == exp["n_pairs"]
    assert np.isclose(res["win_share_F_SOG"], exp["win_share_F_SOG"], atol=1e-5)
    assert np.isclose(res["win_share_F_PA"], exp["win_share_F_PA"], atol=1e-5)
    assert np.isclose(res["win_share_F_RADIAL"], exp["win_share_F_RADIAL"], atol=1e-5)
    assert res["delta_PA_RADIAL"] == exp["delta_PA_RADIAL"]
    assert res["verdict"] == exp["verdict"]


def test_synthetic_state_sog_engine_parity():
    """Verify end-to-end numerical parity of SOG solver on synthetic fixture."""
    fixture_path = REPO_ROOT / "tests" / "fixtures" / "synthetic_state.json"
    state = load_synthetic_state(fixture_path)
    df, F = score_state(state, CANONICAL_CONFIG)

    # Invariants
    assert len(df) == 216
    assert df["valid_primary"].sum() == 216
    # Exact frozen arithmetic mean of top-10% (k=22 actions)
    assert np.isclose(F, 3.375321759226284, atol=1e-5)

    cells = aggregate_cells(df)
    assert len(cells) == 72  # 9 players * 8 directions
    assert cells["rank"].min() == 1
    assert cells["percentile"].max() == 1.0


def test_canonical_real_state_sog_parity():
    """Verify numerical parity of SOG calculation on canonical World Cup match state.

    Tests GOLD001 best documented frame (Match 10505, Frame 70930) against canonical
    experiment records from EXP_SOG_GOLD20_CONFIRMATION_023 (cases/GOLD001.md):
      - State F_SOG == 3.5180
      - Top cell: #9 Harry Kane @ 0 deg, Q == 6.1950, rank 1/80, pct 1.000
      - Rank 2 cell: #9 Harry Kane @ 45 deg, Q == 5.2533, rank 2/80, pct 0.987
      - Rank 3 cell: #9 Harry Kane @ 315 deg, Q == 4.0727, rank 3/80, pct 0.975
    """
    pff_root = os.environ.get("PFF_DATA_ROOT")
    candidate_roots = [
        pff_root,
        Path("C:/dev/MIT/frame_cache"),
        Path("C:/dev/MIT/FIFA World Cup 2022"),
    ]
    valid_root = next((r for r in candidate_roots if r and Path(r).exists()), None)
    if not valid_root:
        pytest.skip("PFF tracking data or frame cache not configured (set PFF_DATA_ROOT)")

    try:
        state = load_pff_state(valid_root, 10505, 70930, focal_is_home=True)
    except FileNotFoundError:
        pytest.skip(f"Match 10505 not found under {valid_root}")

    df, F = score_state(state, CANONICAL_CONFIG)
    assert np.isclose(F, 3.5180, atol=1e-3)

    cells = aggregate_cells(df)
    top_cell = cells.iloc[0]
    assert top_cell["jersey"] == "9"
    assert np.isclose(top_cell["direction_deg"], 0.0)
    assert np.isclose(top_cell["Q"], 6.1950, atol=1e-3)
    assert top_cell["rank"] == 1
    assert np.isclose(top_cell["percentile"], 1.0)

    second_cell = cells.iloc[1]
    assert second_cell["jersey"] == "9"
    assert np.isclose(second_cell["direction_deg"], 45.0)
    assert np.isclose(second_cell["Q"], 5.2533, atol=1e-3)

    third_cell = cells.iloc[2]
    assert third_cell["jersey"] == "9"
    assert np.isclose(third_cell["direction_deg"], 315.0)
    assert np.isclose(third_cell["Q"], 4.0727, atol=1e-3)

