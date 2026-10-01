"""Observed-context features from one tracking state."""

import numpy as np

EPS = 1e-12


def m0_features(state, op_base, C0: np.ndarray, grid, possession_age_s: float) -> dict:
    """The 14 frozen M0 baseline features for one built state."""
    pos = np.asarray(state.positions, dtype=float)
    vel = np.asarray(state.velocities, dtype=float)
    is_att = np.asarray(state.is_att, dtype=bool)
    is_gk = np.asarray(state.is_gk, dtype=bool)
    ball = np.asarray(state.ball, dtype=float)
    goal = np.asarray(grid.goal, dtype=float)
    carrier = op_base.carrier_index
    fallback = False
    att_out = np.flatnonzero(is_att & ~is_gk)
    if carrier is None or carrier not in set(att_out.tolist()):
        d = np.linalg.norm(pos[att_out] - ball[None, :], axis=1)
        carrier = int(att_out[int(np.argmin(d))])
        fallback = True
    def_out = np.flatnonzero(~is_att & ~is_gk)
    offball = att_out[att_out != carrier]
    dc = pos[carrier]
    dd = np.linalg.norm(pos[def_out] - dc[None, :], axis=1)
    j = int(np.argmin(dd))
    nearest_dist = float(dd[j])
    dp = pos[def_out[j]]
    u = (dc - dp) / (nearest_dist if nearest_dist > 1e-09 else 1.0)
    closing = float(np.dot(vel[def_out[j]] - vel[carrier], u))
    spd = np.linalg.norm(vel, axis=1)
    off_spd = spd[offball] if offball.size else np.array([np.nan])
    def_spd = spd[def_out] if def_out.size else np.array([np.nan])
    dy = pos[def_out][:, 1]
    dx = pos[def_out][:, 0]
    width = float(dy.max() - dy.min()) if def_out.size else float("nan")
    depth = float(dx.max() - dx.min()) if def_out.size else float("nan")
    try:
        from scipy.spatial import ConvexHull, QhullError

        hull = float(ConvexHull(pos[def_out]).volume) if def_out.size >= 3 else 0.0
    except Exception:
        hull = 0.0
    targets = np.asarray(grid.targets, dtype=float)
    cell_area = float(
        (targets[0, 1, 0] - targets[0, 0, 0]) * (targets[1, 0, 1] - targets[0, 0, 1])
    )
    c0a = float(
        cell_area * np.clip(np.asarray(C0, dtype=float).ravel(), 0.0, 1.0).sum()
    )
    return {
        "ball_x_norm": float(ball[0]),
        "abs_ball_y_m": float(abs(ball[1])),
        "ball_dist_to_goal_m": float(np.linalg.norm(ball - goal)),
        "possession_age_s": float(possession_age_s),
        "carrier_nearest_def_dist_m": nearest_dist,
        "nearest_def_closing_speed_ms": closing,
        "carrier_speed_ms": float(spd[carrier]),
        "offball_att_speed_mean_ms": float(np.nanmean(off_spd)),
        "offball_att_speed_max_ms": float(np.nanmax(off_spd)),
        "def_outfield_speed_mean_ms": float(np.nanmean(def_spd)),
        "def_width_m": width,
        "def_depth_m": depth,
        "def_hull_area_m2": hull,
        "C0_ATTACK_AREA_m2": c0a,
        "carrier_fallback": bool(fallback),
    }


def alignment_features(
    vel: np.ndarray, dirs: np.ndarray, q: np.ndarray
) -> tuple[float, float]:
    """Movement-alignment features for one state."""
    if vel.size == 0 or q.size == 0:
        return (float("nan"), float("nan"))
    speed = np.linalg.norm(vel, axis=1)
    theta_v = np.rad2deg(np.arctan2(vel[:, 1], vel[:, 0]))
    dtheta = np.deg2rad(theta_v - dirs)
    cos_ok = np.maximum(np.cos(dtheta), 0.0)
    qmax = float(np.max(q)) if q.size else 0.0
    qn = q / (qmax + EPS)
    terms = qn * cos_ok
    best = float(np.nanmax(terms)) if np.isfinite(terms).any() else float("nan")
    i_top = int(np.argmax(q))
    return (best, float(terms[i_top]))


def state_scores_res0(res: dict, *, fraction: float = 0.1) -> dict:
    """The frozen state reducer F_RES0 and the Model B landscape features."""
    v = np.asarray(res["R_RES0"], dtype=float)
    ok = np.asarray(res["valid_primary"], dtype=bool) & np.isfinite(v)
    vv = v[ok]
    n = int(vv.size)
    if n == 0:
        return {
            "N_actions": 0,
            "k": 0,
            "F_RES0": float("nan"),
            "R_MAX": float("nan"),
            "R_MEDIAN": float("nan"),
            "TOP_CONCENTRATION": float("nan"),
            "TOP_GAP": float("nan"),
            "PLAYER_CONCENTRATION": float("nan"),
            "N_players": 0,
        }
    k = max(1, int(np.ceil(fraction * n)))
    srt = np.sort(vv)[::-1]
    f_res0 = float(srt[:k].mean())
    r_max = float(srt[0])
    r_median = float(np.median(vv))
    top_gap = (
        float((srt[0] - srt[1]) / (abs(srt[0]) + 1e-12)) if n >= 2 else float("nan")
    )
    att = np.asarray(res["attacker_index"], dtype=int)[ok]
    q = {}
    for p in np.unique(att):
        q[int(p)] = float(vv[att == p].max())
    qv = np.array(list(q.values()), dtype=float)
    denom = float(np.maximum(qv, 0.0).sum())
    player_conc = float(qv.max() / (denom + 1e-12)) if qv.size else float("nan")
    return {
        "N_actions": n,
        "k": k,
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
