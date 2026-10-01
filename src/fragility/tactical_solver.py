"""Fast frozen SOG solver with the EXP024 pure-control-gain companion.
Only additional PCG bookkeeping differs from fast_sog.solve_state_res0.
"""
import numpy as np
from .fast_sog import _step_table, _integrate_from_player, COLLISION_RADIUS_M, HALF_LEN, HALF_WID
from .research_operator import SPEC, StructuralOperator
from obso.state import offside_line
from obso.ppcf import time_to_intercept

def solve_state_sog_pcg(state, *, spec=SPEC) -> dict:
    """Per-candidate R_RES0 for one state, using the frozen RES0_V1 formulation.

    Returns a dict with parallel arrays over every candidate in the frozen
    neighbourhood (attacker x 24 offsets), in the same order the frozen
    `spec.offsets()` enumerates them for each attacker of the frozen moved set:

        attacker_index, jersey, direction_deg, radius, cost,
        base_x, base_y, cf_x, cf_y,
        rejected (object array, None when the candidate survived the filters),
        offside_switch (bool), valid_primary (bool), R_RES0 (float, NaN if rejected)

    A rejected candidate (`out_of_pitch`, `collision`) is reported with `rejected`
    set and `R_RES0 = NaN`, exactly as `rc.candidate_row` does.
    """
    op = StructuralOperator(state)

    state_obj = op.state
    positions = np.asarray(state_obj.positions, dtype=float)
    velocities = np.asarray(state_obj.velocities, dtype=float)
    is_att = np.asarray(state_obj.is_att, dtype=bool)
    is_gk = np.asarray(state_obj.is_gk, dtype=bool)
    base_offside = np.asarray(state_obj.offside, dtype=bool)
    jerseys = list(getattr(state_obj, "jerseys", []))

    # frozen moved set: attacking, non-keeper, carrier excluded
    moved_set = np.flatnonzero(is_att & ~is_gk)
    carrier = op.base.carrier_index
    if carrier is not None and carrier in set(moved_set.tolist()):
        moved_set = moved_set[moved_set != carrier]

    tab = _step_table(op, moved_set)
    n_steps = tab["n_steps"]
    dt = tab["dt"]

    C0 = np.clip(np.asarray(op.base.control, dtype=float), 0.0, 1.0).ravel()
    residual = 1.0 - C0
    coef = float(op.op.coef)
    lam_att = float(op.op.params.lambda_att)
    targets = op.op.grid.targets
    params = op.op.params

    outfield = np.flatnonzero(~is_gk)

    offsets = np.asarray(spec.offsets(), dtype=float)          # (24, 3)
    K = offsets.shape[0]
    dir_deg = np.rad2deg(np.arctan2(offsets[:, 1], offsets[:, 0])) % 360.0

    out: dict = {k: [] for k in
                 ("attacker_index", "jersey", "direction_deg", "radius", "cost",
                  "base_x", "base_y", "cf_x", "cf_y", "rejected",
                  "offside_switch", "valid_primary", "R_RES0", "PCG",
                  "min_dist_other_outfield_m", "perturbed_offside")}

    for j in moved_set:
        j = int(j)
        base_xy = positions[j]
        cf = base_xy[None, :] + offsets[:, :2]                 # (K, 2)
        dx_abs = np.abs(cf[:, 0])
        dy_abs = np.abs(cf[:, 1])

        # --- frozen filter A: leaves the playing surface
        bad_a = (dx_abs > HALF_LEN) | (dy_abs > HALF_WID)
        # --- frozen filter B: implausible overlap with another outfield player
        others = outfield[outfield != j]
        d = np.linalg.norm(positions[others][None, :, :] - cf[:, None, :], axis=2)
        dmin = d.min(axis=1)                                   # (K,)
        bad_b = dmin < COLLISION_RADIUS_M
        keep = ~(bad_a | bad_b)

        R = np.full(K, np.nan)
        PCG = np.full(K, np.nan)
        sw = np.zeros(K, dtype=bool)
        poff = np.zeros(K, dtype=bool)

        if keep.any():
            idx = np.flatnonzero(keep)
            cf_k = cf[idx]
            # --- frozen offside rule, one line per candidate
            pos_k = np.repeat(positions[None, :, :], idx.size, axis=0)
            pos_k[:, j, :] = cf_k
            for q, p in enumerate(pos_k):
                line = offside_line(p, is_att, state_obj.ball)
                off = is_att & (p[:, 0] > line + spec.offside_tol_m)
                poff[idx[q]] = bool(off[j])
            sw[idx] = poff[idx] != bool(base_offside[j])

            # --- frozen E for the moved player only
            tti = time_to_intercept(cf_k, velocities[j][None, :], targets, params)
            E_new = np.exp(np.clip(coef * tti, 0.0, 700.0)).reshape(idx.size, -1)
            rate_new = np.where(poff[idx], 0.0, lam_att).astype(float)

            A_att = _integrate_from_player(tab, j, bool(is_att[j]), E_new, rate_new)
            C1 = np.clip(A_att, 0.0, 1.0)
            dC = C1 - C0[None, :]
            d_pos = np.maximum(dC, 0.0)
            R[idx] = (residual[None, :] * d_pos).sum(axis=1) / offsets[idx, 2]
            # EXP024 accumulated the stored float32 dC fields. Preserve that convention.
            PCG[idx] = np.maximum(dC.astype(np.float32), 0).sum(axis=1) / offsets[idx, 2]

        rejected = np.where(bad_a, "out_of_pitch",
                            np.where(bad_b, "collision", None)).astype(object)
        # a rejected candidate is never valid_primary (frozen `candidate_row` returns
        # early with valid_primary = False); `keep` is exactly ~(bad_a | bad_b)
        valid_primary = (~sw) & keep

        out["attacker_index"].append(np.full(K, j, dtype=int))
        out["jersey"].append(np.full(K, str(jerseys[j]) if j < len(jerseys) else None,
                                     dtype=object))
        out["direction_deg"].append(dir_deg.copy())
        out["radius"].append(offsets[:, 2].copy())
        out["cost"].append(offsets[:, 2].copy())
        out["base_x"].append(np.full(K, base_xy[0]))
        out["base_y"].append(np.full(K, base_xy[1]))
        out["cf_x"].append(cf[:, 0].copy())
        out["cf_y"].append(cf[:, 1].copy())
        out["rejected"].append(rejected)
        out["offside_switch"].append(sw)
        out["perturbed_offside"].append(poff)
        out["valid_primary"].append(valid_primary)
        out["R_RES0"].append(R)
        out["PCG"].append(np.where(valid_primary, PCG, np.nan))
        out["min_dist_other_outfield_m"].append(dmin)

    res = {k: (np.concatenate(v) if len(v) else np.array([])) for k, v in out.items()}
    res["n_steps"] = n_steps
    res["dt"] = dt
    res["n_eligible_attackers"] = int(moved_set.size)
    return res
