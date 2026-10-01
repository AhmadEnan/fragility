"""Transition, score and the combined OBSO / Danger surfaces.

    O_t(r) = T_t(r) * C_t(r) * S(r)
    D_t    = sum_r O_t(r)

T is normalised to unity over the valid grid, so with C and S bounded in [0, 1] the
integrated danger D_t lies in [0, 1].
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from obso.grid import PitchGrid


@dataclass(frozen=True)
class DangerConfig:
    """Frozen transition and score parameters (see preregistered_validation.json)."""

    sigma: float = 23.9
    alpha: float = 1.04
    c0: float = 0.7895
    c1: float = -1.2594
    c2: float = 0.1155
    score_sign: int = -1  # -1 selects the complement (pilot interpretation)
    transition_normalisation_tol: float = 1e-6

    def as_dict(self) -> dict:
        return {
            "sigma_m": self.sigma,
            "alpha": self.alpha,
            "score_c0": self.c0,
            "score_c1": self.c1,
            "score_c2": self.c2,
            "score_linear_predictor_sign": self.score_sign,
        }


def score_surface(grid: PitchGrid, config: DangerConfig) -> np.ndarray:
    """Scoring probability S(r) from goal angle and distance.

    The 2020 paper prints sigmoid(c0 + c1*theta + c2*d) with c0 = 0.7895,
    c1 = -1.2594, c2 = 0.1155 and states that scoring probability rises with the goal
    angle and falls with distance. Those printed signs do the opposite on both counts.
    ``score_sign = -1`` evaluates the complement, sigmoid(-(c0 + c1*theta + c2*d)),
    which is the algebraic form implied if the regression was fitted on the
    complementary response; it is the only interpretation satisfying the paper's own
    stated semantics and the four canonical-location invariants. This choice is frozen
    in the pre-registration and is not re-fitted here.
    """
    targets = grid.targets
    goal = grid.goal
    post_high, post_low = grid.posts[0], grid.posts[1]
    v_high = post_high[None, None, :] - targets
    v_low = post_low[None, None, :] - targets
    cosang = (v_high * v_low).sum(axis=-1) / (
        np.linalg.norm(v_high, axis=-1) * np.linalg.norm(v_low, axis=-1)
    )
    theta = np.arccos(np.clip(cosang, -1.0, 1.0))
    distance = np.linalg.norm(targets - goal[None, None, :], axis=-1)
    linear = config.c0 + config.c1 * theta + config.c2 * distance
    return 1.0 / (1.0 + np.exp(-config.score_sign * linear))


def transition_surface(
    grid: PitchGrid, ball_pos: np.ndarray, control: np.ndarray, config: DangerConfig
) -> tuple[np.ndarray, np.ndarray]:
    """Decision-weighted next-touch density T(r), normalised to unity over the grid.

    Returns (T, T_raw). The isotropic 2-D normal is centred on the current ball
    location and multiplied by the attacking control field raised to alpha, exactly as
    in Spearman 2018 Eq. 6 and the 2020 paper Eq. 5.
    """
    targets = grid.targets
    sq = ((targets - ball_pos[None, None, :]) ** 2).sum(axis=-1)
    normal = np.exp(-sq / (2.0 * config.sigma**2)) / (2.0 * np.pi * config.sigma**2)
    raw = normal * np.power(np.clip(control, 0.0, 1.0), config.alpha)
    total = raw.sum()
    if total <= 0:
        raise ValueError("transition field integrates to zero; check the control surface")
    return raw / total, raw


def obso_surfaces(
    grid: PitchGrid,
    ball_pos: np.ndarray,
    control_att: np.ndarray,
    config: DangerConfig,
) -> dict:
    """Build every component surface and the integrated danger D.

    Returns a dict with C (attacking control), T, S, O, D and the raw transition field,
    so that a failure can always be attributed to the transition, control or score
    component rather than to the composite.
    """
    score = score_surface(grid, config)
    transition, transition_raw = transition_surface(grid, ball_pos, control_att, config)
    opportunity = transition * np.clip(control_att, 0.0, 1.0) * score
    return {
        "C": control_att,
        "T": transition,
        "T_raw": transition_raw,
        "S": score,
        "O": opportunity,
        "D": float(opportunity.sum()),
        "transition_mass": float(transition.sum()),
    }


@dataclass
class ComponentReport:
    """Component magnitudes at one chosen location, for the failure-attribution tables."""

    label: str
    x: float
    y: float
    C: float
    T: float
    S: float
    O: float
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "label": self.label,
            "x_m": self.x,
            "y_m": self.y,
            "C_control": self.C,
            "T_transition": self.T,
            "S_score": self.S,
            "O_obso": self.O,
            "notes": self.notes,
        }


def component_at(surfaces: dict, grid: PitchGrid, x: float, y: float, label: str) -> ComponentReport:
    """Read the four component surfaces at the nearest grid cell to (x, y)."""
    ix = int(np.argmin(np.abs(grid.x - x)))
    iy = int(np.argmin(np.abs(grid.y - y)))
    return ComponentReport(
        label=label,
        x=float(grid.x[ix]),
        y=float(grid.y[iy]),
        C=float(surfaces["C"][iy, ix]),
        T=float(surfaces["T"][iy, ix]),
        S=float(surfaces["S"][iy, ix]),
        O=float(surfaces["O"][iy, ix]),
    )
