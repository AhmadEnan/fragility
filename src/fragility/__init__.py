"""Fragility: Counterfactual Defensive Fragility and SOG Engine for SSAC 2027."""

from __future__ import annotations

from fragility.config import SOGConfig, CANONICAL_CONFIG
from fragility.pitch_control import (
    PitchGrid,
    make_grid,
    compute_pitch_control,
    time_to_intercept,
    ball_travel_time,
    control_from_E,
)
from fragility.pff import (
    TrackingState,
    load_pff_state,
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
from fragility.validation import (
    evaluate_tactical_recovery,
    evaluate_gold20,
    evaluate_ablation,
    evaluate_grid_stability,
    evaluate_state_fragility,
    exact_permutation_auc,
    wilson_ci,
)
from fragility.figures import (
    plot_action_recovery,
    plot_gold20_recovery,
    plot_grid_stability,
)

__version__ = "1.0.0"

__all__ = [
    "SOGConfig",
    "CANONICAL_CONFIG",
    "PitchGrid",
    "make_grid",
    "compute_pitch_control",
    "time_to_intercept",
    "ball_travel_time",
    "control_from_E",
    "TrackingState",
    "load_pff_state",
    "load_synthetic_state",
    "offside_line",
    "carrier_index",
    "eligible_attackers",
    "compute_offside",
    "enumerate_actions",
    "score_action",
    "score_state",
    "state_fragility",
    "aggregate_cells",
    "evaluate_tactical_recovery",
    "evaluate_gold20",
    "evaluate_ablation",
    "evaluate_grid_stability",
    "evaluate_state_fragility",
    "exact_permutation_auc",
    "wilson_ci",
    "plot_action_recovery",
    "plot_gold20_recovery",
    "plot_grid_stability",
    "__version__",
]
