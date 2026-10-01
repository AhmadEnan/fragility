"""Continuous Off-Ball Scoring Opportunity (OBSO) as a candidate Danger function.

Pilot implementation for the Defensive Fragility feasibility study. The pipeline is
the three-factor decomposition of Spearman (2018, MIT SSAC, "Beyond Expected Goals")
as re-specified by Rios-Neto, Meira Jr. and Vaz-de-Melo (2020, "A new look into
Off-ball Scoring Opportunity: taking into account the continuous nature of the game"):

    O_t(r) = T_t(r) * C_t(r) * S(r)
    D_t    = sum_r O_t(r)

with C the Potential Pitch Control Field, T the transition density and S the scoring
probability at r. The frozen parameter choices and the reasons for them live in
``outputs/obso_pilot/preregistered_validation.json``.
"""

from obso.danger import DangerConfig, obso_surfaces, score_surface, transition_surface
from obso.evaluate import Evaluation, evaluate_state
from obso.grid import PitchGrid, make_grid
from obso.ppcf import (
    PPFCParams,
    canonical_params,
    fot_params,
    integrate_ppcf,
    spearman_kappa_params,
    time_to_intercept,
)
from obso.state import PitchState, offside_line, state_from_cache_row

__all__ = [
    "DangerConfig",
    "Evaluation",
    "PPFCParams",
    "PitchGrid",
    "PitchState",
    "canonical_params",
    "evaluate_state",
    "fot_params",
    "integrate_ppcf",
    "make_grid",
    "obso_surfaces",
    "offside_line",
    "score_surface",
    "spearman_kappa_params",
    "state_from_cache_row",
    "time_to_intercept",
    "transition_surface",
]
