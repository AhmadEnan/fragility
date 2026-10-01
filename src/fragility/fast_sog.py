"""Original frozen-equivalent SOG solver; arithmetic hoisting only, no formula changes."""
import numpy as np
from .research_operator import SPEC, StructuralOperator
from obso.state import offside_line
from obso.ppcf import time_to_intercept
COLLISION_RADIUS_M = 0.5
INTEGRATION_CHUNK = 4
HALF_LEN, HALF_WID = 52.5, 34.0

def _step_table(op, moved_set: np.ndarray) -> dict:
    """Per-step baseline hazard sums, hoisted out of the candidate loop.

    Returns
    -------
    exp_a      : (n_steps, n_cells)  exp(-coef * (travel + step*dt)), the frozen term
    total_base : (n_steps, n_cells)  sum over ALL 22 players of hazard_j(step)
    satt_base  : (n_steps, n_cells)  sum over the ATTACKING players of hazard_j(step)
    hbase      : {player_index: (n_steps, n_cells)}  hazard of that player alone

    ``hbase`` is built only for the players that can be moved (the frozen moved set),
    which is what keeps the table at tens of megabytes rather than hundreds.
    """
    params = op.op.params
    coef = float(op.op.coef)
    dt = float(params.int_dt)
    n_steps = int(np.ceil((float(params.max_int_time) + dt) / dt))

    travel = np.asarray(op.op.travel, dtype=float).ravel()
    E = np.asarray(op.op.E, dtype=float)
    rates = np.asarray(op.op.rates, dtype=float)
    is_att = np.asarray(op.state.is_att, dtype=bool)
    n_players = E.shape[0]
    n_cells = travel.size

    exp_a = np.empty((n_steps, n_cells), dtype=float)
    total_base = np.empty((n_steps, n_cells), dtype=float)
    satt_base = np.empty((n_steps, n_cells), dtype=float)
    hbase = {int(j): np.empty((n_steps, n_cells), dtype=float) for j in moved_set}

    Eflat = E.reshape(n_players, n_cells)
    rates_col = rates[:, None]
    for t in range(n_steps):
        ea = np.exp(-coef * (travel + t * dt))
        exp_a[t] = ea
        haz = rates_col / (1.0 + Eflat * ea[None, :])
        for j in hbase:
            hbase[j][t] = haz[j]
        total_base[t] = haz.sum(axis=0)
        satt_base[t] = haz[is_att].sum(axis=0)

    return {"exp_a": exp_a, "total_base": total_base, "satt_base": satt_base,
            "hbase": hbase, "n_steps": n_steps, "dt": dt}

def _integrate_from_player(tab: dict, moved: int, is_att_moved: bool,
                           E_new: np.ndarray, rate_new: np.ndarray,
                           *, chunk: int = INTEGRATION_CHUNK) -> np.ndarray:
    """Integrate the frozen recurrence with only `moved` changed.

    E_new  : (K, n_cells)  the moved player's E under each of the K offsets
    rate_new : (K,)        the moved player's rate under each of the K offsets
    returns : (K, n_cells) sum over ATTACKING players of accumulated_j

    THE REORDERING THIS RELIES ON (pure reordering, no change of formula)
    --------------------------------------------------------------------
    The frozen integrator accumulates per player j:

        accumulated_j(t) = released_t * hazard_j(t)
        released_t       = available_t * (1 - decay_t) / total_t      (0 if total_t <= 0)
        decay_t          = exp(-clip(total_t * dt, 0, 700))
        available_{t+1}  = clip(1 - sum_j accumulated_j(t), 0, 1)

    Summing the first line over j and using `sum_j hazard_j(t) == total_t` gives
    `sum_j accumulated_j(t) = available_t * (1 - decay_t)`, so the per-player
    accumulation can be replaced by its sum over the two player classes:

        A_att = sum_t released_t * s_att_t ,   s_att_t = sum_{j in att} hazard_j(t)

    That is valid **only because `_single_control` moves exactly one player**: every
    other player's hazard is constant across the whole candidate neighbourhood of a
    state, so `total_t` and `s_att_t` are the frozen sums with the moved player's
    contribution swapped, and are hoisted out of the candidate loop by `_step_table`.

    TWO VARIANTS WERE TRIED AND MEASURED (see `d01_ab_integrator.py`)
    -----------------------------------------------------------------
    *This* variant — the per-step loop over time — is the adopted one.  A second
    variant replaced the time loop with an exclusive cumulative sum, using the exact
    telescoping identity

        available_t = exp(-sum_{s<t} clip(total_s*dt, 0, 700))

    which follows from `sum_{s<=t} available_s (1-decay_s) = 1 - prod_{s<=t} decay_s`
    (and whose `clip(.,0,1)` is provably inactive because `exp(-x) in (0,1]`).  It was
    **correct** (agreed to 2.8e-15) but **2-3x slower**, because it materialises
    `(chunk, n_steps, n_cells)` float64 temporaries instead of streaming `(K, n_cells)`
    slices, and this kernel is memory-bandwidth bound.  It was therefore not adopted;
    it is recorded here so that the same idea is not re-derived and re-tried.

    The frozen `released /= total` is *not* a no-op: the `* total` that cancels it lives
    inside the per-player accumulation being hoisted away, so the division is kept
    explicitly, together with the frozen `total <= 0 -> 0` guard.

    `01_verify_solver.py` *measures* the difference against the frozen path; it is
    never assumed.
    """
    dt = tab["dt"]
    n_steps = tab["n_steps"]
    exp_a = tab["exp_a"]
    total_base = tab["total_base"]
    satt_base = tab["satt_base"]
    hbase_m = tab["hbase"][moved]                     # (n_steps, n_cells)

    E_new = np.asarray(E_new, dtype=float)
    rate_new = np.asarray(rate_new, dtype=float)
    K, n_cells = E_new.shape
    rate_col = rate_new[:, None]

    # preallocated scratches: the frozen integrator is fully in-place for exactly this
    # reason, and the same discipline is what keeps this kernel off the allocator
    A_att = np.zeros((K, n_cells), dtype=float)
    available = np.ones((K, n_cells), dtype=float)
    hnew = np.empty((K, n_cells), dtype=float)
    total = np.empty((K, n_cells), dtype=float)
    s_att = np.empty((K, n_cells), dtype=float)
    decay = np.empty((K, n_cells), dtype=float)
    released = np.empty((K, n_cells), dtype=float)

    for t in range(n_steps):
        ea = exp_a[t]
        # hnew = rates_moved / (1 + E_moved * exp_a)
        np.multiply(E_new, ea[None, :], out=hnew)
        hnew += 1.0
        np.divide(1.0, hnew, out=hnew)
        hnew *= rate_col
        # total hazard = (sum over the other 21) + hnew
        np.subtract(total_base[t][None, :], hbase_m[t][None, :], out=total)
        total += hnew
        if is_att_moved:
            np.subtract(satt_base[t][None, :], hbase_m[t][None, :], out=s_att)
            s_att += hnew
        else:
            np.copyto(s_att, satt_base[t][None, :])

        # decay = exp(-clip(total*dt, 0, 700))
        np.multiply(total, dt, out=decay)
        np.clip(decay, 0.0, 700.0, out=decay)
        np.negative(decay, out=decay)
        np.exp(decay, out=decay)

        # released = available * (1 - decay) / total, 0 where total <= 0
        np.subtract(1.0, decay, out=released)
        np.multiply(released, available, out=released)
        np.divide(released, total, out=released, where=total > 0.0)
        released[total <= 0.0] = 0.0

        np.multiply(released, s_att, out=released)     # released := this step's increment
        A_att += released

        # frozen: available_{t+1} = clip(1 - sum_j accumulated_j, 0, 1).
        # Summing `accumulated_j = released * hazard_j` over j gives available*(1-decay),
        # so the recurrence telescopes to available *= decay — which is why no explicit
        # `A_all` accumulator is carried here.  The frozen clip to [0, 1] is inactive:
        # decay = exp(-x) with x >= 0 lies in (0, 1], so available stays in (0, 1].
        np.multiply(available, decay, out=available)

    return A_att

def solve_state_res0(state, *, spec=SPEC) -> dict:
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
                  "offside_switch", "valid_primary", "R_RES0",
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
        out["min_dist_other_outfield_m"].append(dmin)

    res = {k: (np.concatenate(v) if len(v) else np.array([])) for k, v in out.items()}
    res["n_steps"] = n_steps
    res["dt"] = dt
    res["n_eligible_attackers"] = int(moved_set.size)
    return res

def state_scores_res0(res: dict, *, fraction: float = 0.10) -> dict:
    """The frozen state reducer F_RES0 and the Model B landscape features.

    All quantities are read off the SAME valid-action vector
    (`valid_primary` and finite `R_RES0`), exactly as `x20_common.state_scores`
    defines N and k.
    """
    v = np.asarray(res["R_RES0"], dtype=float)
    ok = np.asarray(res["valid_primary"], dtype=bool) & np.isfinite(v)
    vv = v[ok]
    n = int(vv.size)
    if n == 0:
        return {"N_actions": 0, "k": 0, "F_RES0": float("nan"), "R_MAX": float("nan"),
                "R_MEDIAN": float("nan"), "TOP_CONCENTRATION": float("nan"),
                "TOP_GAP": float("nan"), "PLAYER_CONCENTRATION": float("nan"),
                "N_players": 0}

    k = max(1, int(np.ceil(fraction * n)))
    srt = np.sort(vv)[::-1]
    f_res0 = float(srt[:k].mean())
    r_max = float(srt[0])
    r_median = float(np.median(vv))
    top_gap = float((srt[0] - srt[1]) / (abs(srt[0]) + 1e-12)) if n >= 2 else float("nan")

    # PLAYER_CONCENTRATION: Q_i = max over that player's valid directions/radii
    att = np.asarray(res["attacker_index"], dtype=int)[ok]
    q = {}
    for p in np.unique(att):
        q[int(p)] = float(vv[att == p].max())
    qv = np.array(list(q.values()), dtype=float)
    denom = float(np.maximum(qv, 0.0).sum())
    player_conc = float(qv.max() / (denom + 1e-12)) if qv.size else float("nan")

    return {
        "N_actions": n, "k": k,
        "F_RES0": f_res0,
        "R_MAX": r_max,
        "R_MEDIAN": r_median,
        "TOP_CONCENTRATION": float(r_max / (f_res0 + 1e-12)),
        "TOP_GAP": top_gap,
        "PLAYER_CONCENTRATION": player_conc,
        "N_players": int(qv.size),
        "top1_attacker_index": int(att[int(np.argmax(vv))]),
        "top1_jersey": str(res["jersey"][ok][int(np.argmax(vv))]),
    }
