"""The local positional stress operator ("Fragility-Lite") on top of OBSO.

Definitions frozen in ``outputs/fragility_operator_pilot/preregistered_operator_pilot.json``::

    D_OBSO(s) = sum_r T_s(r) C_s(r) S(r)
    D_FV(s)   = sum_r T_s(r) C_s(r) w_field(r)      # OBSO-FV, the value ablation
    Delta_X(a, s) = D_X(s^a) - D_X(s)               # X in {OBSO, FV}

The operator perturbs ONLY non-ball attackers.  The ball, the ball carrier, the
defenders and both goalkeepers are held fixed, so ``T``'s centre, the offside
line and every defender's control contribution are invariant by construction.

Numerics.  ``obso.ppcf.integrate_ppcf`` evaluates, for every step and every
player, ``f_j = 1 / (1 + exp(-(time_term - coef * tti_j)))``.  Since
``exp(-(time_term - coef*tti_j)) == exp(coef*tti_j) * exp(-time_term)`` and the
``exp(-time_term)`` factor is shared by all players, the player-specific
exponential ``E_j = exp(coef*tti_j)`` is precomputed once per state.  A
perturbation changes one player's position, hence exactly one row of ``E``.
That turns the per-step transcendental from 22 x 1600 into 1 x 1600.  The
recurrence itself is untouched and the result is verified against
``integrate_ppcf`` to ~1e-13 (``scripts/fragility_operator_pilot/01a_verify_fast_integrator.py``).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from obso.danger import DangerConfig, score_surface, transition_surface
from obso.grid import PITCH_LENGTH_M, PITCH_WIDTH_M, PitchGrid
from obso.ppcf import PPFCParams, ball_travel_time, time_to_intercept
from obso.state import PitchState, offside_line

HALF_LENGTH_M = PITCH_LENGTH_M / 2.0
HALF_WIDTH_M = PITCH_WIDTH_M / 2.0


# --------------------------------------------------------------------- spec


@dataclass(frozen=True)
class OperatorSpec:
    """Every knob of the operator, frozen before any Fragility value is computed."""

    radii_m: tuple[float, ...] = (0.50, 1.00, 1.50)
    directions_deg: tuple[float, ...] = (0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0)
    collision_radius_m: float = 0.50
    offside_tol_m: float = 0.0
    carrier_max_m: float = 2.0
    min_valid_actions: int = 20
    tail_fraction: float = 0.10
    reversal_angle_deg: float = 135.0
    reversal_speed_ms: float = 3.0

    def offsets(self) -> np.ndarray:
        """(n, 3) array of (dx, dy, radius) for every radius x direction pair."""
        rows = []
        for r in self.radii_m:
            for d in self.directions_deg:
                th = np.deg2rad(d)
                rows.append((r * np.cos(th), r * np.sin(th), r))
        return np.asarray(rows, dtype=float)

    def as_dict(self) -> dict:
        return {
            "radii_m": list(self.radii_m),
            "directions_deg": list(self.directions_deg),
            "n_candidates_per_attacker": len(self.radii_m) * len(self.directions_deg),
            "collision_radius_m": self.collision_radius_m,
            "offside_tolerance_m": self.offside_tol_m,
            "carrier_max_m": self.carrier_max_m,
            "min_valid_actions": self.min_valid_actions,
            "tail_fraction": self.tail_fraction,
            "reversal_flag_angle_deg": self.reversal_angle_deg,
            "reversal_flag_speed_ms": self.reversal_speed_ms,
        }


# --------------------------------------------------------------------- helpers


def control_rates(state: PitchState, params: PPFCParams, offside: np.ndarray) -> np.ndarray:
    """lambda_j with exactly zero for offside attackers (the frozen rule)."""
    rates = np.where(state.is_att, params.lambda_att, params.lambda_def)
    rates = np.where(state.is_gk, params.lambda_gk, rates)
    return np.where(offside, 0.0, rates)


def control_from_E(
    E: np.ndarray,
    rates: np.ndarray,
    is_att: np.ndarray,
    travel: np.ndarray,
    params: PPFCParams,
    *,
    coef: float | None = None,
) -> np.ndarray:
    """Summed attacking control, using the factorised logistic term.

    Algebraically identical to ``obso.ppcf.integrate_ppcf`` with the canonical
    exponential integrator; see the module docstring.
    """
    if coef is None:
        coef = np.pi / (np.sqrt(3.0) * float(params.tti_sigma))
    dt = float(params.int_dt)
    n_steps = int(np.ceil((float(params.max_int_time) + dt) / dt))

    n_players, ny, nx = E.shape
    accumulated = np.zeros((n_players, ny, nx), dtype=float)
    hazard = np.empty((n_players, ny, nx), dtype=float)
    available = np.ones((ny, nx), dtype=float)
    released = np.empty((ny, nx), dtype=float)
    rates_col = rates[:, None, None]

    for step in range(n_steps):
        exp_a = np.exp(-coef * (travel + step * dt))  # (ny, nx), shared by all players
        # f_j = 1 / (1 + exp(coef*tti_j) * exp(-time_term)); fully in place.
        np.multiply(E, exp_a, out=hazard)
        hazard += 1.0
        np.divide(1.0, hazard, out=hazard)
        hazard *= rates_col

        total = hazard.sum(axis=0)
        np.exp(-np.clip(total * dt, 0.0, 700.0), out=released)
        released -= 1.0
        released *= -available  # available * (1 - decay)
        np.divide(released, total, out=released, where=total > 0)
        released[total <= 0.0] = 0.0
        accumulated += released[None, :, :] * hazard
        available = np.clip(1.0 - accumulated.sum(axis=0), 0.0, 1.0)

    return accumulated[is_att].sum(axis=0)


def carrier_index(state: PitchState, max_m: float) -> int | None:
    """Nearest attacking player to the ball, if within ``max_m`` (else None)."""
    att = np.flatnonzero(state.is_att)
    d = np.linalg.norm(state.positions[att] - state.ball[None, :], axis=1)
    j = int(np.argmin(d))
    return int(att[j]) if d[j] <= max_m else None


# --------------------------------------------------------------------- operator


@dataclass
class Baseline:
    D_OBSO: float
    D_FV: float
    control: np.ndarray
    transition: np.ndarray
    score: np.ndarray
    field_value: np.ndarray
    opportunity_obso: np.ndarray
    opportunity_fv: np.ndarray
    n_offside_att: int
    carrier_index: int | None
    carrier_distance_m: float

    def as_dict(self) -> dict:
        return {
            "D_OBSO": self.D_OBSO,
            "D_FV": self.D_FV,
            "n_offside_att": self.n_offside_att,
            "carrier_index": self.carrier_index,
            "carrier_distance_m": self.carrier_distance_m,
        }


class StateOperator:
    """Counterfactual evaluation of one state under the frozen operator spec."""

    def __init__(
        self,
        state: PitchState,
        params: PPFCParams,
        config: DangerConfig,
        grid: PitchGrid,
        field_value: np.ndarray,
        spec: OperatorSpec,
    ) -> None:
        self.state = state
        self.params = params
        self.config = config
        self.grid = grid
        self.field_value = field_value
        self.spec = spec

        self.coef = np.pi / (np.sqrt(3.0) * float(params.tti_sigma))
        self.travel = ball_travel_time(grid.targets, state.ball, params.ball_speed)
        self.tti = time_to_intercept(state.positions, state.velocities, grid.targets, params)
        self.E = np.exp(np.clip(self.coef * self.tti, 0.0, 700.0))
        self.rates = control_rates(state, params, state.offside)
        self.score = score_surface(grid, config)
        self._baseline: Baseline | None = None

    # -- baseline ---------------------------------------------------------

    def baseline(self) -> Baseline:
        if self._baseline is not None:
            return self._baseline
        control = control_from_E(self.E, self.rates, self.state.is_att, self.travel,
                                 self.params, coef=self.coef)
        transition, _ = transition_surface(self.grid, self.state.ball, control, self.config)
        clipped = np.clip(control, 0.0, 1.0)
        opp_obso = transition * clipped * self.score
        opp_fv = transition * clipped * self.field_value
        att = np.flatnonzero(self.state.is_att)
        carrier = carrier_index(self.state, self.spec.carrier_max_m)
        carrier_d = float(np.min(np.linalg.norm(self.state.positions[att] - self.state.ball[None, :], axis=1)))
        self._baseline = Baseline(
            D_OBSO=float(opp_obso.sum()),
            D_FV=float(opp_fv.sum()),
            control=control,
            transition=transition,
            score=self.score,
            field_value=self.field_value,
            opportunity_obso=opp_obso,
            opportunity_fv=opp_fv,
            n_offside_att=int(self.state.offside[self.state.is_att].sum()),
            carrier_index=carrier,
            carrier_distance_m=carrier_d,
        )
        return self._baseline

    # -- counterfactuals --------------------------------------------------

    def _single_control(self, moved: int, new_pos: np.ndarray) -> tuple[float, np.ndarray]:
        """Attacking control surface after moving player ``moved`` to ``new_pos``."""
        positions = self.state.positions.copy()
        positions[moved] = new_pos
        line = offside_line(positions, self.state.is_att, self.state.ball)
        x_att = positions[:, 0]
        offside = self.state.is_att & (x_att > line + self.spec.offside_tol_m)
        is_offside = bool(offside[moved])

        rates = self.rates.copy()
        rates[moved] = 0.0 if is_offside else float(self.params.lambda_att)

        tti_j = time_to_intercept(
            positions[[moved]], self.state.velocities[[moved]], self.grid.targets, self.params
        )
        E = self.E.copy()
        E[moved] = np.exp(np.clip(self.coef * tti_j[0], 0.0, 700.0))
        control = control_from_E(E, rates, self.state.is_att, self.travel, self.params, coef=self.coef)
        return control, offside

    def candidates(self, *, with_surfaces: bool = False) -> list[dict]:
        """Every perturbation of every eligible non-ball attacker."""
        state = self.state
        spec = self.spec
        base = self.baseline()

        offside_out = np.flatnonzero(state.is_att & ~state.is_gk)
        if base.carrier_index is not None and base.carrier_index in set(offside_out.tolist()):
            offside_out = offside_out[offside_out != base.carrier_index]

        # other outfield players, for the collision test (both teams, keepers excluded
        # exactly as the brief's wording specifies)
        outfield = np.flatnonzero(~state.is_gk)

        rows: list[dict] = []
        for j in offside_out:
            j = int(j)
            base_xy = state.positions[j].copy()
            base_offside = bool(state.offside[j])
            vel = state.velocities[j]
            speed = float(np.linalg.norm(vel))
            for dx, dy, radius in spec.offsets():
                new_xy = base_xy + np.array([dx, dy])
                row = {
                    "match_id": state.match_id,
                    "frame": int(state.frame_num),
                    "period": int(state.period),
                    "focal_is_home": bool(state.focal_is_home),
                    "attacker_index": j,
                    "attacker_jersey": state.jerseys[j] if j < len(state.jerseys) else None,
                    "base_x": float(base_xy[0]),
                    "base_y": float(base_xy[1]),
                    "cf_x": float(new_xy[0]),
                    "cf_y": float(new_xy[1]),
                    "dx": float(dx),
                    "dy": float(dy),
                    "radius": float(radius),
                    "direction_deg": float(np.rad2deg(np.arctan2(dy, dx)) % 360.0),
                    "baseline_offside": base_offside,
                    "attacker_speed_ms": speed,
                    "rejected": None,
                }

                # A. out of pitch
                if abs(new_xy[0]) > HALF_LENGTH_M or abs(new_xy[1]) > HALF_WIDTH_M:
                    row.update({"perturbed_offside": None, "offside_switch": False,
                                "valid_primary": False, "rejected": "out_of_pitch",
                                "delta_OBSO": None, "delta_FV": None})
                    rows.append(row)
                    continue

                # B. collision / implausible overlap with another outfield player
                others = outfield[outfield != j]
                dmin = float(np.min(np.linalg.norm(state.positions[others] - new_xy[None, :], axis=1)))
                row["min_dist_other_outfield_m"] = dmin
                if dmin < spec.collision_radius_m:
                    row.update({"perturbed_offside": None, "offside_switch": False,
                                "valid_primary": False, "rejected": "collision",
                                "delta_OBSO": None, "delta_FV": None})
                    rows.append(row)
                    continue

                # D. offside-status change (primary rule)
                control, offside_after = self._single_control(j, new_xy)
                new_offside = bool(offside_after[j])
                switch = new_offside != base_offside
                row["perturbed_offside"] = new_offside
                row["offside_switch"] = switch
                row["valid_primary"] = not switch

                clipped = np.clip(control, 0.0, 1.0)
                transition, _ = transition_surface(self.grid, state.ball, control, self.config)
                opp_obso = transition * clipped * self.score
                opp_fv = transition * clipped * self.field_value
                row["D_OBSO_cf"] = float(opp_obso.sum())
                row["D_FV_cf"] = float(opp_fv.sum())
                row["delta_OBSO"] = row["D_OBSO_cf"] - base.D_OBSO
                row["delta_FV"] = row["D_FV_cf"] - base.D_FV
                row["D_OBSO_base"] = base.D_OBSO
                row["D_FV_base"] = base.D_FV

                # kinematic diagnostic (section 8) — recorded, never used to filter
                if speed > 1e-6:
                    cosang = float(np.dot(np.array([dx, dy]), vel) / (radius * speed))
                    ang = float(np.rad2deg(np.arccos(np.clip(cosang, -1.0, 1.0))))
                else:
                    ang = float("nan")
                row["displacement_angle_vs_velocity_deg"] = ang
                row["reversal_flag"] = bool(
                    np.isfinite(ang) and ang > spec.reversal_angle_deg and speed > spec.reversal_speed_ms
                )
                rows.append(row)
        return rows


# --------------------------------------------------------------------- scoring


def tail_mean(values: np.ndarray, fraction: float) -> float:
    """Mean of the largest ``ceil(fraction * n)`` entries (CVaR-style upper tail)."""
    values = np.asarray([v for v in values if v is not None and np.isfinite(v)], dtype=float)
    if values.size == 0:
        return float("nan")
    k = max(1, int(np.ceil(fraction * values.size)))
    return float(np.sort(values)[::-1][:k].mean())


def state_fragility(rows: list[dict], spec: OperatorSpec, *, exclude_reversals: bool = False) -> dict:
    """Fragility of one state from its candidate rows.

    ``U_X(s) = {max(0, Delta_X(a,s))}`` over valid primary actions; ``F_X(s)`` is
    the mean of the largest ``ceil(0.10 * |U_X|)`` entries.  The absolute maximum
    is never the primary score.
    """
    primary = [r for r in rows if r.get("valid_primary") and r.get("delta_OBSO") is not None]
    if exclude_reversals:
        primary = [r for r in primary if not r.get("reversal_flag")]

    offside_switch = [r for r in rows if r.get("offside_switch") and r.get("delta_OBSO") is not None]

    def _pack(sel: list[dict], key: str) -> dict:
        pos = [max(0.0, r[key]) for r in sel if r.get(key) is not None and np.isfinite(r[key])]
        allv = [r[key] for r in sel if r.get(key) is not None and np.isfinite(r[key])]
        arr = np.asarray(pos, dtype=float) if pos else np.array([])
        allarr = np.asarray(allv, dtype=float) if allv else np.array([])
        return {
            "F": tail_mean(arr, spec.tail_fraction),
            "max_delta": float(allarr.max()) if allarr.size else float("nan"),
            "median_positive_delta": float(np.median(arr)) if arr.size else float("nan"),
            "p90_delta": float(np.percentile(allarr, 90)) if allarr.size else float("nan"),
            "n_valid": len(sel),
            "n_positive": int((allarr > 0).sum()) if allarr.size else 0,
            "n_zero": int((allarr == 0).sum()) if allarr.size else 0,
            "n_negative": int((allarr < 0).sum()) if allarr.size else 0,
        }

    obso = _pack(primary, "delta_OBSO")
    fv = _pack(primary, "delta_FV")
    off = _pack(offside_switch, "delta_OBSO")
    off_fv = _pack(offside_switch, "delta_FV")

    def _top(sel: list[dict], key: str, n: int = 5) -> list[dict]:
        ranked = sorted(
            [r for r in sel if r.get(key) is not None and np.isfinite(r[key])],
            key=lambda r: r[key],
            reverse=True,
        )[:n]
        return [
            {
                "attacker_index": r["attacker_index"],
                "attacker_jersey": r.get("attacker_jersey"),
                "dx": r["dx"],
                "dy": r["dy"],
                "radius": r["radius"],
                "direction_deg": r["direction_deg"],
                "cf_x": r["cf_x"],
                "cf_y": r["cf_y"],
                "delta": r[key],
            }
            for r in ranked
        ]

    return {
        "F_OBSO": obso["F"],
        "F_FV": fv["F"],
        "F_offside_switch_OBSO": off["F"],
        "F_offside_switch_FV": off_fv["F"],
        "n_candidates": len(rows),
        "n_offside_switch": len(offside_switch),
        "n_rejected_out_of_pitch": sum(1 for r in rows if r.get("rejected") == "out_of_pitch"),
        "n_rejected_collision": sum(1 for r in rows if r.get("rejected") == "collision"),
        "n_reversal_flagged": sum(1 for r in primary if r.get("reversal_flag")),
        "insufficient_neighborhood": bool(obso["n_valid"] < spec.min_valid_actions),
        "obso": obso,
        "fv": fv,
        "offside_switch_obso": off,
        "top5_OBSO": _top(primary, "delta_OBSO"),
        "top5_FV": _top(primary, "delta_FV"),
        "top5_offside_switch": _top(offside_switch, "delta_OBSO"),
    }
