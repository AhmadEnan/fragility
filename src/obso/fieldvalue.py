"""Field-value surface w_field(r) — Ogawa, Umemoto & Fujii (2025), arXiv:2505.14711.

This surface is used ONLY as the controlled value-surface ablation called
**OBSO-FV**: the same transition ``T`` and the same control ``C`` as OBSO, with
the score surface ``S`` replaced by the published field-value surface::

    weight(x)     = 1 / (1 + exp(-(x + 15) / 30))          [paper Eq. 13]
    sigma(x)      = 34 * (1 + weight(x))                   [paper Eq. 14]
    w_field(x, y) = exp(-y^2 / (2 sigma(x)^2)) * weight(x)  [paper Eq. 15]

This is **NOT** full OBPV.  Full OBPV (paper Eq. 4) is
``OBPV_r = w_field * P(C_r|D) * P(TK_r|D)`` and additionally replaces the OBSO
transition ``T`` with a learned transition kernel ``TK`` built by KDE over pass
start/end positions in 18 pitch regions.  The 18-region geometry is shown only
in the paper's Fig. 2 and is never enumerated in the text, so per brief section
18 it is not reproduced and full OBPV is skipped.  OBSO-FV changes exactly one
thing — the value surface — which is what the pilot is designed to test.

Nothing here is fitted to World Cup data and no constant is tuned.
"""

from __future__ import annotations

import numpy as np

from obso.grid import PitchGrid

# Paper constants, used exactly as published.
WEIGHT_SHIFT_M = 15.0
WEIGHT_SCALE_M = 30.0
LATERAL_CONSTANT_M = 34.0


def weight_x(x: np.ndarray | float) -> np.ndarray:
    """Longitudinal logistic weight, paper Eq. 13."""
    x = np.asarray(x, dtype=float)
    return 1.0 / (1.0 + np.exp(-(x + WEIGHT_SHIFT_M) / WEIGHT_SCALE_M))


def sigma_x(x: np.ndarray | float) -> np.ndarray:
    """Lateral Gaussian standard deviation, paper Eq. 14."""
    return LATERAL_CONSTANT_M * (1.0 + weight_x(x))


def field_value_surface(grid: PitchGrid) -> np.ndarray:
    """w_field on the grid's cell centres, shape (ny, nx)."""
    x = grid.targets[..., 0]
    y = grid.targets[..., 1]
    sigma = sigma_x(x)
    return np.exp(-(y**2) / (2.0 * sigma**2)) * weight_x(x)


def field_value_checks(grid: PitchGrid) -> dict:
    """The invariants the brief requires before the surface is used."""
    w = field_value_surface(grid)
    x = grid.targets[..., 0]
    y = grid.targets[..., 1]

    def wf(xx: float, yy: float) -> float:
        s = float(sigma_x(xx))
        return float(np.exp(-(yy**2) / (2.0 * s**2)) * float(weight_x(xx)))

    checks = {
        "weight_bounds_ok": bool(np.all((weight_x(x) > 0.0) & (weight_x(x) < 1.0))),
        "weight_min": float(weight_x(x).min()),
        "weight_max": float(weight_x(x).max()),
        "w_field_positive_ok": bool(np.all(w > 0.0)),
        "w_field_leq_one_ok": bool(np.all(w <= 1.0)),
        "w_field_min": float(w.min()),
        "w_field_max": float(w.max()),
        "weight_plus40": float(weight_x(40.0)),
        "weight_zero": float(weight_x(0.0)),
        "weight_minus40": float(weight_x(-40.0)),
        "weight_ordering_ok": bool(weight_x(40.0) > weight_x(0.0) > weight_x(-40.0)),
        "central_gt_wide_ok": bool(wf(0.0, 0.0) > wf(0.0, 30.0)),
        "central_gt_wide_example": {"w_field(0,0)": wf(0.0, 0.0), "w_field(0,30)": wf(0.0, 30.0)},
        "weight_midpoint_at_minus15": float(weight_x(-15.0)),
        "sigma_at_plus40": float(sigma_x(40.0)),
        "sigma_at_minus40": float(sigma_x(-40.0)),
        "grid_cell_y_extent_m": [float(y.min()), float(y.max())],
    }
    checks["all_ok"] = bool(
        checks["weight_bounds_ok"]
        and checks["w_field_positive_ok"]
        and checks["w_field_leq_one_ok"]
        and checks["weight_ordering_ok"]
        and checks["central_gt_wide_ok"]
    )
    return checks
