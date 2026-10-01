"""One-call evaluation of a pitch state into PPCF, transition, score and danger."""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

from obso.danger import DangerConfig, obso_surfaces
from obso.grid import PitchGrid
from obso.ppcf import PPFCParams, ball_travel_time, integrate_ppcf, time_to_intercept
from obso.state import PitchState


@dataclass
class Evaluation:
    """All component surfaces for one state, plus the numbers needed to audit them."""

    surfaces: dict
    ppcf_att: np.ndarray
    ppcf_def: np.ndarray
    ppcf_diagnostics: dict
    runtime_s: float
    offside: np.ndarray
    is_att: np.ndarray

    @property
    def D(self) -> float:
        return self.surfaces["D"]


def evaluate_state(
    state: PitchState,
    params: PPFCParams,
    config: DangerConfig,
    grid: PitchGrid,
    *,
    force_offside_off: bool = False,
    positions_override: np.ndarray | None = None,
    velocities_override: np.ndarray | None = None,
    ball_override: np.ndarray | None = None,
    integrator: str = "exponential",
) -> Evaluation:
    """Evaluate one state.

    ``force_offside_off`` is the counterfactual diagnostic required by validation E:
    it restores full control rates to offside attackers. The ``*_override`` arguments
    are the perturbation hooks used by the invariant and smoothness diagnostics.
    """
    started = time.perf_counter()
    positions = state.positions if positions_override is None else positions_override
    velocities = state.velocities if velocities_override is None else velocities_override
    ball = state.ball if ball_override is None else ball_override

    offside = np.zeros_like(state.offside) if force_offside_off else state.offside
    rates = np.where(state.is_att, params.lambda_att, params.lambda_def)
    rates = np.where(state.is_gk, params.lambda_gk, rates)
    rates = np.where(offside, 0.0, rates)

    tti = time_to_intercept(positions, velocities, grid.targets, params)
    travel = ball_travel_time(grid.targets, ball, params.ball_speed)
    att, deff, diagnostics = integrate_ppcf(
        tti, state.is_att, rates, travel, params, integrator=integrator
    )
    surfaces = obso_surfaces(grid, ball, att, config)
    runtime = time.perf_counter() - started
    return Evaluation(
        surfaces=surfaces,
        ppcf_att=att,
        ppcf_def=deff,
        ppcf_diagnostics=diagnostics,
        runtime_s=runtime,
        offside=offside,
        is_att=state.is_att,
    )
