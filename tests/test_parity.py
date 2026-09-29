"""Numerical parity tests against frozen canonical experiment outputs.

Asserts exact equality or tight numerical tolerances for all reported claims.
"""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from fragility.validation import (
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
    pa_path = DERIVED_DIR / "gold20_player_actions.csv"
    cs_path = DERIVED_DIR / "gold20_cases_summary.csv"
    assert pa_path.exists()
    assert cs_path.exists()

    pa = pd.read_csv(pa_path)
    cs = pd.read_csv(cs_path)

    res = evaluate_gold20(pa, cs)
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
    abl_path = DERIVED_DIR / "gold20_ablation_comparison.csv"
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
    gs_path = DERIVED_DIR / "grid_stability_summary.csv"
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
    cp_path = DERIVED_DIR / "cap_pair_scores.csv"
    assert cp_path.exists()

    cp = pd.read_csv(cp_path)
    res = evaluate_state_fragility(cp)
    exp = expected["claims"]["C05_state_fragility_path_accessibility"]

    assert res["n_pairs"] == exp["n_pairs"]
    assert np.isclose(res["win_share_F_SOG"], exp["win_share_F_SOG"], atol=1e-5)
    assert np.isclose(res["win_share_F_PA"], exp["win_share_F_PA"], atol=1e-5)
    assert np.isclose(res["win_share_F_RADIAL"], exp["win_share_F_RADIAL"], atol=1e-5)
    assert np.isclose(res["delta_PA_RADIAL"], exp["delta_PA_RADIAL"], atol=1e-6)
    assert res["verdict"] == exp["verdict"]
