"""Structural Opening Gain (SOG) counterfactual engine.

Implements the frozen formulation:
    dC_a(r) = Ca(r) - C0(r)
    SOG(a)  = sum_r (1 - C0(r)) * max(dC_a(r), 0) / (rho / 1m)
    F_SOG(s) = arithmetic mean of the top 10% valid action scores

Filters:
1. Playing surface boundary check: |x| <= 52.5 m, |y| <= 34.0 m
2. Outfield collision check: distance to nearest outfield player >= 0.5 m
3. Offside-switch exclusion: candidates that flip baseline offside status are rejected
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from fragility.config import SOGConfig, CANONICAL_CONFIG
from fragility.pitch_control import PitchGrid, make_grid, compute_pitch_control, time_to_intercept, control_from_E
from fragility.pff import TrackingState, carrier_index, eligible_attackers, compute_offside


def enumerate_actions(
    state: TrackingState,
    config: SOGConfig = CANONICAL_CONFIG,
) -> list[dict[str, Any]]:
    """Enumerate candidate perturbations for all eligible attackers."""
    carrier = carrier_index(state, config.carrier_max_distance_m)
    eligible = eligible_attackers(state, carrier)
    offsets = config.action_offsets()

    actions = []
    for att_idx in eligible:
        base_pos = state.positions[att_idx]
        jersey = state.jerseys[att_idx] if att_idx < len(state.jerseys) else str(att_idx)
        for dx, dy, radius in offsets:
            new_pos = base_pos + np.array([dx, dy], dtype=np.float64)
            deg = round(float(np.rad2deg(np.arctan2(dy, dx)) % 360.0), config.direction_decimals)
            actions.append({
                "attacker_index": att_idx,
                "jersey": str(jersey),
                "base_x": float(base_pos[0]),
                "base_y": float(base_pos[1]),
                "cf_x": float(new_pos[0]),
                "cf_y": float(new_pos[1]),
                "dx": float(dx),
                "dy": float(dy),
                "radius": float(radius),
                "direction_deg": deg,
                "cost": float(radius / 1.0),
                "baseline_offside": bool(state.offside[att_idx]),
            })
    return actions


def score_action(
    state: TrackingState,
    action: dict[str, Any],
    C0: np.ndarray,
    base_E: np.ndarray,
    travel: np.ndarray,
    coef: float,
    grid: PitchGrid,
    config: SOGConfig = CANONICAL_CONFIG,
) -> dict[str, Any]:
    """Evaluate a single counterfactual action candidate.

    Returns the action dictionary updated with validity flags and scores.
    """
    row = dict(action)
    new_xy = np.array([row["cf_x"], row["cf_y"]], dtype=np.float64)
    att_idx = row["attacker_index"]
    half_l = config.pitch_length / 2.0
    half_w = config.pitch_width / 2.0

    # Filter 1: Boundary check
    if abs(new_xy[0]) > half_l or abs(new_xy[1]) > half_w:
        row.update({
            "rejected": "out_of_pitch",
            "valid_primary": False,
            "offside_switch": False,
            "sog": np.nan,
            "pcg": np.nan,
        })
        return row

    # Filter 2: Collision check with other outfield players
    outfield = np.flatnonzero(~state.is_gk)
    others = outfield[outfield != att_idx]
    dists = np.linalg.norm(state.positions[others] - new_xy[None, :], axis=1)
    min_dist = float(np.min(dists)) if len(dists) > 0 else 999.0
    row["min_dist_other_outfield_m"] = min_dist

    if min_dist < config.collision_radius_m:
        row.update({
            "rejected": "collision",
            "valid_primary": False,
            "offside_switch": False,
            "sog": np.nan,
            "pcg": np.nan,
        })
        return row

    # Filter 3: Offside-switch check
    positions_cf = state.positions.copy()
    positions_cf[att_idx] = new_xy
    offside_cf = compute_offside(positions_cf, state.is_att, state.ball, config.offside_tol_m)
    new_offside = bool(offside_cf[att_idx])
    offside_switch = bool(new_offside != row["baseline_offside"])

    row["perturbed_offside"] = new_offside
    row["offside_switch"] = offside_switch
    row["valid_primary"] = not offside_switch

    if offside_switch:
        row.update({
            "rejected": "offside_switch",
            "sog": np.nan,
            "pcg": np.nan,
        })
        return row

    # Counterfactual solve: recompute TTI only for the moved player
    tti_j = time_to_intercept(
        positions_cf[[att_idx]],
        state.velocities[[att_idx]],
        grid.targets,
        max_speed=config.max_player_speed,
        max_acceleration=config.max_acceleration,
    )
    E_cf = base_E.copy()
    E_cf[att_idx] = np.exp(np.clip(coef * tti_j[0], 0.0, 700.0))

    # Control rates (0 for offside players)
    rates = np.where(state.is_att, config.lambda_att, config.lambda_def)
    rates = np.where(state.is_gk, config.lambda_gk, rates)
    rates = np.where(state.offside, 0.0, rates)
    rates[att_idx] = 0.0 if new_offside else config.lambda_att

    raw_control_cf = control_from_E(
        E_cf, rates, state.is_att, travel,
        int_dt=config.int_dt,
        max_int_time=config.max_int_time,
        coef=coef,
    )
    C1 = np.clip(raw_control_cf, 0.0, 1.0)
    dC = C1 - C0
    dC_pos = np.maximum(dC, 0.0)
    residual = 1.0 - C0
    cost = row["cost"]

    # SOG (residual weighted) and PCG (unweighted baseline)
    gain_sog = float(np.sum(residual * dC_pos))
    gain_pcg = float(np.sum(dC_pos))

    row["sog"] = float(gain_sog / cost) if cost > 0 else np.nan
    row["pcg"] = float(gain_pcg / cost) if cost > 0 else np.nan
    row["rejected"] = None
    return row


def state_fragility(
    action_scores: np.ndarray | list[float],
    tail_fraction: float = 0.10,
) -> float:
    """Compute state-level fragility F_SOG as mean of top 10% valid action scores."""
    v = np.asarray(action_scores, dtype=np.float64)
    v = v[np.isfinite(v)]
    if len(v) == 0:
        return float("nan")
    k = max(1, int(math.ceil(tail_fraction * len(v))))
    top_k = np.sort(v)[::-1][:k]
    return float(np.mean(top_k))


def score_state(
    state: TrackingState,
    config: SOGConfig = CANONICAL_CONFIG,
    grid: PitchGrid | None = None,
) -> tuple[pd.DataFrame, float]:
    """Score all actions in a state and return (action_dataframe, F_SOG)."""
    if grid is None:
        grid = make_grid(config.grid_nx, config.grid_ny, config.pitch_length, config.pitch_width)

    C0, base_E, travel, coef = compute_pitch_control(
        state.positions, state.velocities, state.is_att, state.is_gk,
        state.offside, state.ball, grid, config,
    )

    actions = enumerate_actions(state, config)
    scored_rows = [
        score_action(state, a, C0, base_E, travel, coef, grid, config)
        for a in actions
    ]
    df = pd.DataFrame(scored_rows)

    valid_sog = df[df["valid_primary"]]["sog"].dropna().values
    F = state_fragility(valid_sog, config.tail_fraction)
    return df, F


def aggregate_cells(
    actions_df: pd.DataFrame,
    score_col: str = "sog",
    direction_decimals: int = 6,
) -> pd.DataFrame:
    """Group actions into player x direction cells with Q = max_r score.

    Direction is quantized to `direction_decimals` places to prevent floating-point
    splitting of 45° sectors.
    """
    valid = actions_df[actions_df["valid_primary"] & actions_df[score_col].notna()].copy()
    if valid.empty:
        return pd.DataFrame(columns=["jersey", "direction_deg", "Q", "rank", "percentile"])

    valid["dir_round"] = valid["direction_deg"].round(direction_decimals)

    # Q per (jersey, dir_round) is maximum over feasible radii
    cells = (
        valid.groupby(["jersey", "dir_round"], as_index=False)
        .agg(
            Q=(score_col, "max"),
            best_radius=("radius", lambda s: valid.loc[s.index[valid.loc[s.index, score_col].argmax()], "radius"]),
            n_radii=(score_col, "count"),
        )
        .rename(columns={"dir_round": "direction_deg"})
    )

    # Min-rank: 1 + #{v > target}
    M = len(cells)
    scores = cells["Q"].values
    ranks = [int(1 + np.sum(scores > q)) for q in scores]
    cells["rank"] = ranks
    cells["percentile"] = [float(1.0 - (r - 1) / (M - 1)) if M > 1 else 1.0 for r in ranks]
    return cells.sort_values("rank").reset_index(drop=True)
