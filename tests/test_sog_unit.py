"""Unit tests for SOG core engine using synthetic tracking state.

Zero proprietary PFF data required.
"""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pytest

from fragility.config import CANONICAL_CONFIG, SOGConfig
from fragility.pitch_control import (
    make_grid,
    time_to_intercept,
    ball_travel_time,
    control_from_E,
    compute_pitch_control,
)
from fragility.pff import (
    TrackingState,
    load_synthetic_state,
    offside_line,
    carrier_index,
    eligible_attackers,
    compute_offside,
)
from fragility.sog import (
    enumerate_actions,
    score_action,
    score_state,
    state_fragility,
    aggregate_cells,
)

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "synthetic_state.json"


@pytest.fixture
def synthetic_state() -> TrackingState:
    assert FIXTURE_PATH.exists(), f"Missing fixture at {FIXTURE_PATH}"
    return load_synthetic_state(FIXTURE_PATH)


def test_grid_geometry():
    grid = make_grid(50, 32, 105.0, 68.0)
    assert grid.shape == (32, 50)
    assert grid.n_cells == 1600
    assert grid.targets.shape == (32, 50, 2)
    assert np.isclose(grid.goal[0], 52.5)
    assert np.isclose(grid.goal[1], 0.0)
    # Check cell centres stay strictly within pitch boundaries
    assert grid.targets[:, :, 0].min() > -52.5
    assert grid.targets[:, :, 0].max() < 52.5
    assert grid.targets[:, :, 1].min() > -34.0
    assert grid.targets[:, :, 1].max() < 34.0


def test_offside_line_and_status(synthetic_state):
    line = offside_line(synthetic_state.positions, synthetic_state.is_att, synthetic_state.ball)
    # In synthetic fixture, second-last defender is at x = 25.0, ball at x = 19.0
    assert np.isclose(line, 25.0)

    offside = compute_offside(synthetic_state.positions, synthetic_state.is_att, synthetic_state.ball)
    assert isinstance(offside, np.ndarray)
    assert offside.shape == (22,)
    # All attackers in synthetic fixture are at x <= 19.5, so none are offside
    assert int(offside[synthetic_state.is_att].sum()) == 0


def test_carrier_exclusion(synthetic_state):
    # Ball is at [19.0, 0.0]. Player 8 is at [19.5, 0.5] (dist ~0.71 m <= 2.0 m)
    carrier = carrier_index(synthetic_state, CANONICAL_CONFIG.carrier_max_distance_m)
    assert carrier == 8

    eligible = eligible_attackers(synthetic_state, carrier)
    # Outfield attackers are 0..9 (10 players). Excluding carrier 8 leaves 9 players.
    assert len(eligible) == 9
    assert carrier not in eligible
    # Goalkeeper (index 10) must not be eligible
    assert 10 not in eligible


def test_action_enumeration(synthetic_state):
    actions = enumerate_actions(synthetic_state, CANONICAL_CONFIG)
    # 9 eligible attackers * 24 actions (3 radii * 8 directions) = 216 candidate actions
    assert len(actions) == 216

    radii_found = {a["radius"] for a in actions}
    assert radii_found == {0.5, 1.0, 1.5}

    directions_found = {a["direction_deg"] for a in actions}
    assert len(directions_found) == 8
    assert 0.0 in directions_found
    assert 180.0 in directions_found


def test_tti_kinematics():
    targets = np.array([[[10.0, 0.0]]], dtype=np.float64)  # (1, 1, 2)
    positions = np.array([[0.0, 0.0]], dtype=np.float64)   # (1, 2)
    velocities = np.array([[0.0, 0.0]], dtype=np.float64)  # (1, 2)

    # From 0 to 10m from rest:
    # a = 7 m/s^2, v_max = 5 m/s.
    # Time to v_max: t1 = 5 / 7 s (~0.714 s), d1 = 0.5 * 7 * (5/7)^2 = 25 / 14 m (~1.786 m).
    # Cruise distance: 10 - 25/14 = 115 / 14 m (~8.214 m).
    # Cruise time: (115/14) / 5 = 23 / 14 s (~1.643 s).
    # Total tau = t_accel + (d - s_accel)/v = 5/7 + (10 - 25/14)/5 = 33 / 14 s (~2.35714 s)
    tau = time_to_intercept(positions, velocities, targets, max_speed=5.0, max_acceleration=7.0)
    assert np.isclose(tau[0, 0, 0], 33.0 / 14.0, atol=1e-5)


def test_score_state_execution(synthetic_state):
    grid = make_grid(CANONICAL_CONFIG.grid_nx, CANONICAL_CONFIG.grid_ny)
    df, F = score_state(synthetic_state, CANONICAL_CONFIG, grid)

    assert len(df) == 216
    assert np.isfinite(F)
    assert F >= 0.0

    valid_mask = df["valid_primary"]
    assert valid_mask.sum() > 0
    # SOG of all valid actions must be non-negative
    valid_sog = df[valid_mask]["sog"].values
    assert (valid_sog >= 0.0).all()

    # Reducer test
    k = max(1, int(np.ceil(CANONICAL_CONFIG.tail_fraction * len(valid_sog))))
    top_k_mean = float(np.sort(valid_sog)[::-1][:k].mean())
    assert np.isclose(F, top_k_mean)


def test_cell_aggregation(synthetic_state):
    grid = make_grid(CANONICAL_CONFIG.grid_nx, CANONICAL_CONFIG.grid_ny)
    df, _ = score_state(synthetic_state, CANONICAL_CONFIG, grid)
    cells = aggregate_cells(df)

    assert not cells.empty
    assert "Q" in cells.columns
    assert "rank" in cells.columns
    assert "percentile" in cells.columns
    # Best rank is 1, corresponding to maximum percentile
    assert cells["rank"].min() == 1
    assert cells.loc[cells["rank"] == 1, "percentile"].max() == 1.0
    # Minimum percentile >= 0.0
    assert cells["percentile"].min() >= 0.0
