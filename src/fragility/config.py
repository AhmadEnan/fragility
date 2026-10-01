"""Configuration for Structural Opening Gain (SOG) and defensive fragility.

Encodes the frozen canonical parameters from db10578 and EXP020:
- Pitch: 105 x 68 m
- Grid: 50 x 32 evaluation cells
- Perturbation: 8 directions (45°), 3 radii (0.5, 1.0, 1.5 m) -> 24 candidates per attacker
- Cost: rho / 1.0 m (cost equals radius in metres)
- Residual weighting: (1 - C0) * max(dC, 0)
- State reducer: F_SOG = arithmetic mean of the top 10% valid action scores
- Collision radius: 0.5 m
- Offside tolerance: 0.0 m with offside-switch exclusion rule
- Carrier exclusion: nearest attacker within 2.0 m of the ball
- Direction quantization: 6 decimal places
"""

from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np


@dataclass(frozen=True)
class SOGConfig:
    """Frozen configuration for SOG counterfactual computation."""

    # Pitch geometry
    pitch_length: float = 105.0
    pitch_width: float = 68.0

    # Grid dimensions
    grid_nx: int = 50
    grid_ny: int = 32

    # Action space
    radii: tuple[float, ...] = (0.5, 1.0, 1.5)
    directions: tuple[float, ...] = (0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0)

    # Physical / rule constraints
    collision_radius_m: float = 0.5
    offside_tol_m: float = 0.0
    carrier_max_distance_m: float = 2.0
    tail_fraction: float = 0.10
    direction_decimals: int = 6

    # Pitch control kinematics (db10578 canonical specification)
    max_player_speed: float = 5.0  # m/s
    max_acceleration: float = 7.0  # m/s^2
    ball_speed: float = 15.0  # m/s
    tti_sigma: float = 0.54  # logistic scale parameter (s)
    lambda_att: float = 3.99  # control rate (Hz)
    lambda_def: float = 3.99  # control rate (Hz)
    lambda_gk: float = 3.99  # goalkeeper control rate (Hz)
    int_dt: float = 0.04  # integration timestep (s)
    max_int_time: float = 10.0  # integration horizon (s)

    def action_offsets(self) -> np.ndarray:
        """Return (24, 3) array of (dx, dy, radius) for each action."""
        rows = []
        for r in self.radii:
            for d in self.directions:
                rad = np.deg2rad(d)
                rows.append((float(r * np.cos(rad)), float(r * np.sin(rad)), float(r)))
        return np.asarray(rows, dtype=np.float64)


CANONICAL_CONFIG = SOGConfig()
