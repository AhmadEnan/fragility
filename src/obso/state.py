"""Extract a model-ready pitch state from a frame-cache row.

The frame cache already stores every frame rotated so the FOCAL team attacks +x, with
both teams' ten outfielders plus keeper, the ball, and velocities. This module turns
one row into the arrays the PPCF needs, applies the offside rule geometrically, and
assembles the control-rate vector.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from obso.grid import PITCH_LENGTH_M, PITCH_WIDTH_M
from obso.ppcf import PPFCParams

N_OUTFIELD = 10


@dataclass
class PitchState:
    """One instantaneous game state in the focal team's attacking frame."""

    match_id: int
    frame_num: int
    period: int
    focal_is_home: bool
    positions: np.ndarray  # (22, 2)
    velocities: np.ndarray  # (22, 2)
    is_att: np.ndarray  # (22,) True for the focal (in-possession) team
    is_gk: np.ndarray  # (22,)
    ball: np.ndarray  # (2,)
    jerseys: list[str]
    offside: np.ndarray  # (22,) True where an attacking player is in an offside position
    offside_line_x: float
    offside_margin_m: float  # signed distance of the most-marginal attacker from the line
    in_possession: bool
    ball_to_nearest_player_m: float

    @property
    def attacking_positions(self) -> np.ndarray:
        return self.positions[self.is_att]

    def control_rates(self, params: PPFCParams) -> np.ndarray:
        """Per-player lambda_j, with exactly zero for offside attackers.

        Both primary sources state this rule directly (Spearman 2018 sec 3.1.3;
        OBSO 2020 sec 3.1.1). Keepers take the defending keeper rate because the
        focal keeper is by construction on the defending side of the state.
        """
        rates = np.where(self.is_att, params.lambda_att, params.lambda_def)
        rates = np.where(self.is_gk, params.lambda_gk, rates)
        return np.where(self.offside, 0.0, rates)

    def as_row(self) -> dict:
        return {
            "match_id": self.match_id,
            "frame_num": self.frame_num,
            "period": self.period,
            "focal_is_home": bool(self.focal_is_home),
            "ball_x": float(self.ball[0]),
            "ball_y": float(self.ball[1]),
            "n_offside_att": int(self.offside[self.is_att].sum()),
            "offside_line_x": self.offside_line_x,
            "offside_margin_m": self.offside_margin_m,
            "ball_to_nearest_player_m": self.ball_to_nearest_player_m,
        }


def offside_line(positions: np.ndarray, is_att: np.ndarray, ball: np.ndarray) -> float:
    """x of the offside line for the attacking team, in the focal-attacking frame.

    The line is the maximum of the second-last opponent, the ball, and the halfway
    line. Level with the line is onside (Law 11), so the test downstream is strict.
    """
    defender_x = np.where(~is_att, positions[:, 0], -np.inf)
    second_last = float(np.sort(defender_x)[-2])
    return max(second_last, float(ball[0]), 0.0)


def state_from_cache_row(row: pd.Series | dict, offside_tol: float = 0.0) -> PitchState:
    """Build a PitchState from one frame_cache row (one frame, one perspective)."""
    get = row.__getitem__

    att_pos = np.array(
        [[get(f"fo_x_{i}"), get(f"fo_y_{i}")] for i in range(N_OUTFIELD)]
        + [[get("fgk_x"), get("fgk_y")]],
        dtype=float,
    )
    att_vel = np.array(
        [[get(f"fo_vx_{i}"), get(f"fo_vy_{i}")] for i in range(N_OUTFIELD)]
        + [[get("fgk_vx"), get("fgk_vy")]],
        dtype=float,
    )
    def_pos = np.array(
        [[get(f"op_x_{i}"), get(f"op_y_{i}")] for i in range(N_OUTFIELD)]
        + [[get("ogk_x"), get("ogk_y")]],
        dtype=float,
    )
    def_vel = np.array(
        [[get(f"op_vx_{i}"), get(f"op_vy_{i}")] for i in range(N_OUTFIELD)]
        + [[get("ogk_vx"), get("ogk_vy")]],
        dtype=float,
    )
    positions = np.vstack([att_pos, def_pos])
    velocities = np.vstack([att_vel, def_vel])
    is_att = np.array([True] * (N_OUTFIELD + 1) + [False] * (N_OUTFIELD + 1))
    is_gk = np.array([False] * N_OUTFIELD + [True] + [False] * N_OUTFIELD + [True])
    ball = np.array([get("ball_x"), get("ball_y")], dtype=float)

    if not (np.isfinite(positions).all() and np.isfinite(velocities).all() and np.isfinite(ball).all()):
        raise ValueError("non-finite coordinates in cache row")

    line = offside_line(positions, is_att, ball)
    x_att = positions[:, 0]
    offside = is_att & (x_att > line + offside_tol)
    # Signed margin of the attacker closest to the line (negative = safely onside).
    att_x = x_att[is_att]
    margin = float(np.min(line - att_x))

    player_dist = np.linalg.norm(positions - ball[None, :], axis=1)

    return PitchState(
        match_id=int(get("match_id")),
        frame_num=int(get("frame_num")),
        period=int(get("period")),
        focal_is_home=bool(get("focal_is_home")),
        positions=positions,
        velocities=velocities,
        is_att=is_att,
        is_gk=is_gk,
        ball=ball,
        jerseys=[str(get(f"fo_jersey_{i}")) for i in range(N_OUTFIELD)],
        offside=offside,
        offside_line_x=line,
        offside_margin_m=margin,
        in_possession=bool(get("in_possession")),
        ball_to_nearest_player_m=float(player_dist.min()),
    )


def on_pitch_fraction(state: PitchState) -> float:
    """Fraction of players inside the playing surface (diagnostic for tracking noise)."""
    inside = (
        (np.abs(state.positions[:, 0]) <= PITCH_LENGTH_M / 2)
        & (np.abs(state.positions[:, 1]) <= PITCH_WIDTH_M / 2)
    )
    return float(inside.mean())
