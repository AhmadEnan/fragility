"""Pitch control field (PPCF) model based on Spearman (2018).

Corrected db10578 production engine:
- Full unclipped directional velocity projection along intercept ray (remediation 009)
- Mass-conserving exponential integration step
- Factorized logistic interception term for fast single-player counterfactuals
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from fragility.config import SOGConfig, CANONICAL_CONFIG


@dataclass(frozen=True)
class PitchGrid:
    """Cell centres of the evaluation grid."""

    x: np.ndarray  # (nx,)
    y: np.ndarray  # (ny,)
    targets: np.ndarray  # (ny, nx, 2)
    goal: np.ndarray  # (2,) target goal position (+52.5, 0.0)

    @property
    def shape(self) -> tuple[int, int]:
        return (self.y.size, self.x.size)

    @property
    def n_cells(self) -> int:
        return self.y.size * self.x.size


def make_grid(
    nx: int = 50,
    ny: int = 32,
    length: float = 105.0,
    width: float = 68.0,
) -> PitchGrid:
    """Create cell-centre grid spanning the full playing surface."""
    x = np.linspace(-length / 2 + length / (2 * nx), length / 2 - length / (2 * nx), nx)
    y = np.linspace(-width / 2 + width / (2 * ny), width / 2 - width / (2 * ny), ny)
    gx, gy = np.meshgrid(x, y)  # shape: (ny, nx)
    targets = np.stack([gx, gy], axis=-1)
    goal = np.array([length / 2.0, 0.0], dtype=np.float64)
    return PitchGrid(x=x, y=y, targets=targets, goal=goal)


def time_to_intercept(
    positions: np.ndarray,
    velocities: np.ndarray,
    targets: np.ndarray,
    max_speed: float = 5.0,
    max_acceleration: float = 7.0,
) -> np.ndarray:
    """Compute time-to-intercept (TTI) under constant acceleration kinematics.

    Parameters
    ----------
    positions : np.ndarray, shape (N, 2)
    velocities : np.ndarray, shape (N, 2)
    targets : np.ndarray, shape (ny, nx, 2)
    max_speed : float, default 5.0 m/s
    max_acceleration : float, default 7.0 m/s^2

    Returns
    -------
    tau : np.ndarray, shape (N, ny, nx)
        Time in seconds for each player to reach each grid cell.
    """
    a = float(max_acceleration)
    v = float(max_speed)

    # Vector to target: shape (N, ny, nx, 2)
    delta = targets[None, :, :, :] - positions[:, None, None, :]
    distance = np.linalg.norm(delta, axis=-1)
    safe_dist = np.maximum(distance, 1e-9)
    unit = delta / safe_dist[..., None]

    # Initial directional velocity component along ray to target
    # NOTE (EXP_FSTRUCT_ENGINE_REMEDIATION_009): u is NOT clipped to [-v, v].
    u = np.einsum("nijc,nc->nij", unit, velocities)

    t_accel = np.maximum(v - u, 0.0) / a
    s_accel = u * t_accel + 0.5 * a * (t_accel**2)

    tau_accel = (-u + np.sqrt(np.maximum(u**2 + 2.0 * a * distance, 0.0))) / a
    tau_cruise = t_accel + np.maximum(distance - s_accel, 0.0) / v

    tau = np.where(distance <= s_accel, tau_accel, tau_cruise)
    return np.where(distance <= 1e-9, 0.0, tau)


def ball_travel_time(
    targets: np.ndarray,
    ball_pos: np.ndarray,
    ball_speed: float = 15.0,
) -> np.ndarray:
    """Ball flight time to every cell at constant speed (15 m/s)."""
    distance = np.linalg.norm(targets - ball_pos[None, None, :], axis=-1)
    return distance / float(ball_speed)


def control_from_E(
    E: np.ndarray,
    rates: np.ndarray,
    is_att: np.ndarray,
    travel: np.ndarray,
    int_dt: float = 0.04,
    max_int_time: float = 10.0,
    coef: float | None = None,
    tti_sigma: float = 0.54,
) -> np.ndarray:
    """Vectorized exponential integration of pitch control from factorized E matrix.

    E = exp(coef * TTI), where coef = pi / (sqrt(3) * tti_sigma).
    This allows updating control after moving a single player by replacing only
    that player's row in E.
    """
    if coef is None:
        coef = np.pi / (np.sqrt(3.0) * float(tti_sigma))

    dt = float(int_dt)
    n_steps = int(np.ceil((float(max_int_time) + dt) / dt))

    n_players, ny, nx = E.shape
    accumulated = np.zeros((n_players, ny, nx), dtype=np.float64)
    hazard = np.empty((n_players, ny, nx), dtype=np.float64)
    available = np.ones((ny, nx), dtype=np.float64)
    released = np.empty((ny, nx), dtype=np.float64)
    rates_col = rates[:, None, None]

    for step in range(n_steps):
        time_term = coef * (travel + step * dt)
        exp_a = np.exp(-time_term)

        np.multiply(E, exp_a, out=hazard)
        hazard += 1.0
        np.divide(1.0, hazard, out=hazard)
        hazard *= rates_col

        total_hazard = hazard.sum(axis=0)
        np.exp(-np.clip(total_hazard * dt, 0.0, 700.0), out=released)
        released -= 1.0
        released *= -available
        np.divide(released, total_hazard, out=released, where=total_hazard > 0)
        released[total_hazard <= 0.0] = 0.0

        accumulated += released[None, :, :] * hazard
        available = np.clip(1.0 - accumulated.sum(axis=0), 0.0, 1.0)

    return accumulated[is_att].sum(axis=0)


def compute_pitch_control(
    positions: np.ndarray,
    velocities: np.ndarray,
    is_att: np.ndarray,
    is_gk: np.ndarray,
    offside: np.ndarray,
    ball: np.ndarray,
    grid: PitchGrid,
    config: SOGConfig = CANONICAL_CONFIG,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Compute baseline pitch control and return (C0, E, travel, coef)."""
    coef = np.pi / (np.sqrt(3.0) * float(config.tti_sigma))
    travel = ball_travel_time(grid.targets, ball, config.ball_speed)
    tti = time_to_intercept(
        positions,
        velocities,
        grid.targets,
        max_speed=config.max_player_speed,
        max_acceleration=config.max_acceleration,
    )
    E = np.exp(np.clip(coef * tti, 0.0, 700.0))

    # Control rates: 0 for offside attackers
    rates = np.where(is_att, config.lambda_att, config.lambda_def)
    rates = np.where(is_gk, config.lambda_gk, rates)
    rates = np.where(offside, 0.0, rates)

    raw_control = control_from_E(
        E,
        rates,
        is_att,
        travel,
        int_dt=config.int_dt,
        max_int_time=config.max_int_time,
        coef=coef,
    )
    C0 = np.clip(raw_control, 0.0, 1.0)
    return C0, E, travel, coef
