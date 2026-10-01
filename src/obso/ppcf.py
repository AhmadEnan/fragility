"""Potential Pitch Control Field (PPCF).

The recurrence is Spearman (2018) Eq. 3 with the logistic interception term of Eq. 4:

    dPPCF_j/dT = [1 - sum_k PPCF_k(T, r)] * f_j(T, r) * lambda_j
    f_j(T, r)  = 1 / (1 + exp(-pi * (T - tau_j(r)) / (sqrt(3) * sigma)))

integrated over T from the ball's flight time to the target (before which control is
zero by construction) up to a fixed horizon. Offside attackers are handled exactly as
both primary sources prescribe: their control rate lambda_j is set to zero for that
state, so they neither accumulate control nor consume the available probability.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np


@dataclass(frozen=True)
class PPFCParams:
    """Everything needed to build a PPCF surface for one state."""

    label: str
    tti_model: str  # "constant_acceleration" | "reaction_then_max_speed"
    max_player_speed: float
    tti_sigma: float
    lambda_att: float
    lambda_def: float
    lambda_gk: float
    ball_speed: float
    int_dt: float
    max_int_time: float
    converge_tol: float
    max_acceleration: float | None = None
    reaction_time: float | None = None
    kappa_def: float | None = None

    def as_dict(self) -> dict:
        return {
            "label": self.label,
            "tti_model": self.tti_model,
            "max_player_speed": self.max_player_speed,
            "max_acceleration": self.max_acceleration,
            "reaction_time": self.reaction_time,
            "tti_sigma": self.tti_sigma,
            "lambda_att": self.lambda_att,
            "lambda_def": self.lambda_def,
            "lambda_gk": self.lambda_gk,
            "kappa_def": self.kappa_def,
            "ball_speed": self.ball_speed,
            "int_dt": self.int_dt,
            "max_int_time": self.max_int_time,
            "converge_tol": self.converge_tol,
        }


def canonical_params(**overrides) -> PPFCParams:
    """Variant A: the 2020 continuous-OBSO / Spearman primary-source specification.

    a = 7 m/s^2 and v = 5 m/s (Spearman 2018 sec 3.1.1, restated by OBSO 2020 sec
    3.1.1); sigma = s = 0.54 s (Spearman 2018 Table 1 MAP, the value the 2020 paper
    cites for its own logistic width); lambda = 3.99 Hz (both papers); ball speed
    15 m/s (OBSO 2020 sec 3.1.1). The 2020 paper never mentions Spearman's defensive
    multiplier kappa, so the canonical rates are symmetric; keepers are ordinary
    defenders, since the 2020 paper gives no keeper-specific rate.
    """
    base = PPFCParams(
        label="A_2020_continuous_obso_spearman",
        tti_model="constant_acceleration",
        max_player_speed=5.0,
        tti_sigma=0.54,
        lambda_att=3.99,
        lambda_def=3.99,
        lambda_gk=3.99,
        ball_speed=15.0,
        int_dt=0.04,
        max_int_time=10.0,
        converge_tol=0.01,
        max_acceleration=7.0,
        reaction_time=None,
        kappa_def=1.0,
    )
    return replace(base, **overrides)


def fot_params(**overrides) -> PPFCParams:
    """Variant B: the Friends-of-Tracking / LaurieOnTracking reference implementation.

    Reaction time 0.7 s then constant maximum speed (no acceleration phase), logistic
    width 0.45 s, symmetric control rate 4.3 Hz, and a keeper control rate three times
    the outfield rate. Used only as a declared sensitivity, never as canonical.
    """
    base = PPFCParams(
        label="B_friends_of_tracking_reference",
        tti_model="reaction_then_max_speed",
        max_player_speed=5.0,
        tti_sigma=0.45,
        lambda_att=4.3,
        lambda_def=4.3,
        lambda_gk=12.9,
        ball_speed=15.0,
        int_dt=0.04,
        max_int_time=10.0,
        converge_tol=0.01,
        max_acceleration=None,
        reaction_time=0.7,
        kappa_def=1.0,
    )
    return replace(base, **overrides)


def spearman_kappa_params(**overrides) -> PPFCParams:
    """Declared sensitivity: canonical geometry with Spearman's defensive advantage.

    Spearman 2018 Table 1 reports kappa = 1.72, scaling the defending team's control
    rate. The 2020 paper does not restate it, so it is not canonical here; it is
    computed only to show that the D ranking is not an artefact of that choice.
    """
    return canonical_params(lambda_def=3.99 * 1.72, kappa_def=1.72, **overrides)


def time_to_intercept(
    positions: np.ndarray,
    velocities: np.ndarray,
    targets: np.ndarray,
    params: PPFCParams,
) -> np.ndarray:
    """Expected interception time tau_j(r) for every player at every target cell.

    positions : (N, 2)  metres, focal-attacking frame
    velocities: (N, 2)  metres/second
    targets   : (ny, nx, 2)
    returns   : (N, ny, nx)
    """
    if params.tti_model == "constant_acceleration":
        return _tti_constant_acceleration(positions, velocities, targets, params)
    if params.tti_model == "reaction_then_max_speed":
        return _tti_reaction_then_max_speed(positions, velocities, targets, params)
    raise ValueError(f"unknown tti_model {params.tti_model!r}")


def _tti_constant_acceleration(
    positions: np.ndarray,
    velocities: np.ndarray,
    targets: np.ndarray,
    params: PPFCParams,
) -> np.ndarray:
    """Straight-line travel time with constant acceleration a up to a speed cap v.

    Both primary sources define tau_exp as "the time it would take player j to reach
    location r from their start location with a starting velocity, constant
    acceleration a and maximum velocity v", but neither publishes the numerical solve.
    The closed form below is the exact one-dimensional optimum along the straight line
    to the target, using the component of the player's supplied velocity in that
    direction (u). A player moving away (u < 0) must first decelerate and reverse,
    which the same quadratic already prices in, matching Spearman's remark that a
    player running away from a region no longer controls it because of the time it
    takes them to turn around.
    """
    a = float(params.max_acceleration)
    v = float(params.max_player_speed)
    delta = targets[None, :, :, :] - positions[:, None, None, :]  # (N, ny, nx, 2)
    distance = np.linalg.norm(delta, axis=-1)
    safe = np.maximum(distance, 1e-9)
    unit = delta / safe[..., None]
    u = np.einsum("nijc,nc->nij", unit, velocities)
    # NOTE (EXP_FSTRUCT_ENGINE_REMEDIATION_009): Do NOT clip u to [-v, v].
    # Initial directional velocity along the line to target is an initial condition:
    # - For u < -v, unclipped constant-acceleration kinematics accounts for the full
    #   turnaround deceleration time and outward drift distance.
    # - For u >= v, t_accel collapses to 0.0 and tau evaluates to distance / v.

    t_accel = np.maximum(v - u, 0.0) / a
    s_accel = u * t_accel + 0.5 * a * t_accel**2

    tau_accel_phase = (-u + np.sqrt(np.maximum(u**2 + 2.0 * a * distance, 0.0))) / a
    tau_cruise = t_accel + np.maximum(distance - s_accel, 0.0) / v
    tau = np.where(distance <= s_accel, tau_accel_phase, tau_cruise)
    return np.where(distance <= 1e-9, 0.0, tau)


def _tti_reaction_then_max_speed(
    positions: np.ndarray,
    velocities: np.ndarray,
    targets: np.ndarray,
    params: PPFCParams,
) -> np.ndarray:
    """LaurieOnTracking's approximation: drift for the reaction time, then run at v."""
    reaction = positions + velocities * float(params.reaction_time)
    delta = targets[None, :, :, :] - reaction[:, None, None, :]
    distance = np.linalg.norm(delta, axis=-1)
    return float(params.reaction_time) + distance / float(params.max_player_speed)


def ball_travel_time(targets: np.ndarray, ball_pos: np.ndarray, ball_speed: float) -> np.ndarray:
    """Ball flight time to every cell, at a constant average speed.

    The 2020 paper explicitly drops Spearman's aerodynamic-drag treatment in favour of
    distance divided by a fixed average ball speed (15 m/s, citing Shaw 2020).
    """
    distance = np.linalg.norm(targets - ball_pos[None, None, :], axis=-1)
    return distance / float(ball_speed)


def integrate_ppcf(
    tti: np.ndarray,
    is_att: np.ndarray,
    control_rate: np.ndarray,
    travel: np.ndarray,
    params: PPFCParams,
    integrator: str = "exponential",
    stop_on_convergence: bool = False,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Integrate the PPCF recurrence to the control horizon.

    tti          : (N, ny, nx) interception times
    is_att       : (N,)        True for the team in possession
    control_rate : (N,)        lambda_j, already zero for offside attackers
    travel       : (ny, nx)    ball flight time to each cell
    integrator   : "exponential" (canonical) or "euler_explicit" (reference
                   reproduction, kept only as a documented numerical diagnostic)
    returns      : (att, def, diagnostics) where att/def are (ny, nx) summed control
                   per team, and diagnostics carries the numerical-accuracy report.

    An offside attacker keeps is_att True but carries control_rate 0, so they
    contribute nothing and do not consume available probability -- which is exactly
    the rule both primary sources state.

    NUMERICAL NOTE (implementation fix, logged in implementation_notes.md): the
    Friends-of-Tracking reference integrates this ODE with explicit Euler at
    dt = 0.04 s, which is not mass-conserving when the summed hazard is large (22
    players at lambda = 3.99 Hz gives a summed hazard up to ~88 Hz, so a single step
    can in principle add more than the 1.0 of available probability). The canonical
    scheme here is instead exact for a piecewise-constant hazard over each step: it
    removes exactly ``available * (1 - exp(-sum_j f_j lambda_j dt))`` of the remaining
    probability and shares it in proportion to each player's hazard. The ODE is
    unchanged; only the discretisation is made mass-conserving, so gate 1 (control in
    [0, 1]) holds by construction rather than by luck. Both schemes are computed and
    compared in the validation-A numerical report.

    A second implementation fix: the early exit on the convergence tolerance is OFF by
    default. Stopping when the remaining available probability falls below 0.01 makes
    the number of integration steps depend on floating-point noise at the threshold,
    which injects a ~0.01 discontinuity into the control field between two states that
    differ by a single ulp. That is exactly the kind of numerical cliff the smoothness
    diagnostic is meant to detect, so it must not be manufactured by the solver.
    Running the full 10 s horizon is equivalent to tolerance zero and is strictly
    closer to the paper's integral to infinity.
    """
    coef = np.pi / (np.sqrt(3.0) * float(params.tti_sigma))
    dt = float(params.int_dt)
    n_steps = int(np.ceil((float(params.max_int_time) + dt) / dt))

    is_att = np.asarray(is_att, dtype=bool)
    control_rate = np.asarray(control_rate, dtype=float)
    accumulated = np.zeros_like(tti)
    available = np.ones(tti.shape[1:], dtype=float)
    converged_step = n_steps
    max_step_excess = 0.0
    min_available = 1.0

    for step in range(n_steps):
        time_term = coef * (travel + step * dt)  # T starts at the ball flight time
        f = 1.0 / (1.0 + np.exp(-(time_term[None, :, :] - coef * tti)))
        hazard = f * control_rate[:, None, None]
        total_hazard = hazard.sum(axis=0)

        if integrator == "euler_explicit":
            increment = available[None, :, :] * hazard * dt
            excess = float(np.max(increment.sum(axis=0) - available))
            max_step_excess = max(max_step_excess, excess)
            accumulated += increment
        elif integrator == "exponential":
            decay = np.exp(-np.clip(total_hazard * dt, 0.0, 700.0))
            released = available * (1.0 - decay)
            share = np.divide(
                hazard,
                total_hazard[None, :, :],
                out=np.zeros_like(hazard),
                where=total_hazard[None, :, :] > 0,
            )
            accumulated += released[None, :, :] * share
        else:
            raise ValueError(f"unknown integrator {integrator!r}")

        available = np.clip(1.0 - accumulated.sum(axis=0), 0.0, 1.0)
        min_available = min(min_available, float(available.min()))
        if stop_on_convergence and available.max() < float(params.converge_tol):
            converged_step = step + 1
            break

    att = accumulated[is_att].sum(axis=0)
    deff = accumulated[~is_att].sum(axis=0)
    diagnostics = {
        "integrator": integrator,
        "stop_on_convergence": bool(stop_on_convergence),
        "n_steps_run": converged_step,
        "max_remaining_available": float(available.max()),
        "min_remaining_available": float(available.min()),
        "median_remaining_available": float(np.median(available)),
        "max_step_excess_over_available": max_step_excess,
        "n_players": int(tti.shape[0]),
        "n_players_with_control_rate": int((control_rate > 0).sum()),
        "n_attacking_players_active": int((is_att & (control_rate > 0)).sum()),
    }
    return att, deff, diagnostics
