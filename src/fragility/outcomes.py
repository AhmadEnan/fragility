"""Frozen two-second state outcome linkage."""

import numpy as np
import pandas as pd


def label_states(
    states: pd.DataFrame,
    events: pd.DataFrame,
    horizon_s: float,
    *,
    anchor: str = "release",
) -> np.ndarray:
    """Y(t) = 1 iff an event begins in (t, t + horizon]."""
    if states.empty:
        return np.zeros(0, dtype=bool)
    fps = float(states["fps"].iloc[0])
    span = horizon_s * fps
    t = states["frame_num"].to_numpy(dtype=float)
    poss = states["poss_index"].to_numpy(dtype=float)
    team = states["focal_is_home"].to_numpy(dtype=bool)
    y = np.zeros(len(states), dtype=bool)
    if events.empty or anchor not in events.columns:
        return y
    e_f = events[anchor].to_numpy(dtype=float)
    e_poss = events["possession_index"].to_numpy(dtype=float)
    e_team = events["attacking_team_is_home"].to_numpy(dtype=bool)
    ok = np.isfinite(e_f)
    e_f, e_poss, e_team = (e_f[ok], e_poss[ok], e_team[ok])
    for i in range(len(states)):
        same = (e_team == team[i]) & (e_poss == poss[i])
        y[i] = bool(np.any(same & (e_f > t[i]) & (e_f <= t[i] + span)))
    return y
