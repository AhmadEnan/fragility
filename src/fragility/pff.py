"""PFF tracking state parser and geometric normalization.

Handles coordinate conventions:
- Focal attacking team attacks towards +x
- Dimensions: pitch 105 x 68 m, origin at pitch centre (0, 0)
- Offside line evaluated from second-last opponent, ball, and halfway line
- Eligible attackers: non-GK outfield attackers, excluding the ball carrier
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass
class TrackingState:
    """Normalized 22-player tracking state at a single discrete frame."""

    match_id: str | int
    frame_num: int
    period: int
    focal_is_home: bool

    positions: np.ndarray  # shape (22, 2), metres, focal attacks +x
    velocities: np.ndarray  # shape (22, 2), m/s
    is_att: np.ndarray  # shape (22,), bool (True for focal attacking team)
    is_gk: np.ndarray  # shape (22,), bool (True for goalkeepers)
    jerseys: list[str]  # length 22
    ball: np.ndarray  # shape (2,), metres

    offside: np.ndarray = None  # shape (22,), bool

    def __post_init__(self) -> None:
        self.positions = np.asarray(self.positions, dtype=np.float64)
        self.velocities = np.asarray(self.velocities, dtype=np.float64)
        self.is_att = np.asarray(self.is_att, dtype=bool)
        self.is_gk = np.asarray(self.is_gk, dtype=bool)
        self.ball = np.asarray(self.ball, dtype=np.float64)
        if self.offside is None:
            self.offside = compute_offside(self.positions, self.is_att, self.ball)
        else:
            self.offside = np.asarray(self.offside, dtype=bool)


def offside_line(positions: np.ndarray, is_att: np.ndarray, ball: np.ndarray) -> float:
    """Compute the x-coordinate of the attacking team's offside line.

    Per Law 11, the offside line is the maximum of:
    1. The second-last defending player's x position
    2. The ball's x position
    3. The halfway line (x = 0.0)
    """
    def_x = np.where(~is_att, positions[:, 0], -np.inf)
    second_last = float(np.sort(def_x)[-2])
    return float(max(second_last, float(ball[0]), 0.0))


def compute_offside(
    positions: np.ndarray,
    is_att: np.ndarray,
    ball: np.ndarray,
    offside_tol_m: float = 0.0,
) -> np.ndarray:
    """Return boolean array of offside status for all players."""
    line = offside_line(positions, is_att, ball)
    x_pos = positions[:, 0]
    return is_att & (x_pos > line + offside_tol_m)


def carrier_index(state: TrackingState, max_distance_m: float = 2.0) -> int | None:
    """Identify the ball carrier (nearest attacker within threshold, if any)."""
    att_indices = np.flatnonzero(state.is_att)
    dists = np.linalg.norm(state.positions[att_indices] - state.ball[None, :], axis=1)
    min_idx = int(np.argmin(dists))
    if float(dists[min_idx]) <= max_distance_m:
        return int(att_indices[min_idx])
    return None


def eligible_attackers(
    state: TrackingState, carrier_idx: int | None = None
) -> list[int]:
    """Return indices of eligible attackers (outfield attackers minus carrier)."""
    outfield_att = np.flatnonzero(state.is_att & ~state.is_gk)
    if carrier_idx is not None:
        outfield_att = outfield_att[outfield_att != carrier_idx]
    return [int(i) for i in outfield_att]


def load_synthetic_state(path: str | Path) -> TrackingState:
    """Load synthetic tracking state fixture from JSON."""
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)

    return TrackingState(
        match_id=d["match_id"],
        frame_num=d["frame_num"],
        period=d["period"],
        focal_is_home=d["focal_is_home"],
        positions=np.array(d["positions"], dtype=np.float64),
        velocities=np.array(d["velocities"], dtype=np.float64),
        is_att=np.array(d["is_att"], dtype=bool),
        is_gk=np.array(d["is_gk"], dtype=bool),
        jerseys=list(d["jerseys"]),
        ball=np.array(d["ball"], dtype=np.float64),
    )


def load_pff_state(
    data_root: str | Path,
    match_id: str | int,
    frame_num: int,
    focal_is_home: bool = True,
    offside_tol_m: float = 0.0,
) -> TrackingState:
    """Load a specific match frame from reviewer-provided PFF dataset directory.

    Reads a stride-8 cache Parquet. Build it first with fragility.preprocessing;
    this function does not decode raw tracking JSONL files.
    """
    root = Path(data_root)

    # Search frame_cache subdirectory, direct root, or parent paths
    cache_candidates = [
        root / f"match_{match_id}_stride8.parquet",
        root / "frame_cache" / f"match_{match_id}_stride8.parquet",
        root
        / "FIFA World Cup 2022"
        / "frame_cache"
        / f"match_{match_id}_stride8.parquet",
        root / "FIFA World Cup 2022" / f"match_{match_id}_stride8.parquet",
        root.parent / "frame_cache" / f"match_{match_id}_stride8.parquet",
    ]
    cache_path = next((p for p in cache_candidates if p.exists()), None)

    if cache_path is not None:
        import pandas as pd

        df = pd.read_parquet(cache_path)
        sub = df[
            (df["frame_num"] == frame_num) & (df["focal_is_home"] == focal_is_home)
        ]
        if sub.empty:
            raise KeyError(
                f"Exact frame {frame_num}, perspective {focal_is_home} not found"
            )
        else:
            row = sub.iloc[0]

        n_outfield = 10
        att_pos = np.array(
            [[row[f"fo_x_{i}"], row[f"fo_y_{i}"]] for i in range(n_outfield)]
            + [[row["fgk_x"], row["fgk_y"]]],
            dtype=np.float64,
        )
        att_vel = np.array(
            [[row[f"fo_vx_{i}"], row[f"fo_vy_{i}"]] for i in range(n_outfield)]
            + [[row["fgk_vx"], row["fgk_vy"]]],
            dtype=np.float64,
        )
        def_pos = np.array(
            [[row[f"op_x_{i}"], row[f"op_y_{i}"]] for i in range(n_outfield)]
            + [[row["ogk_x"], row["ogk_y"]]],
            dtype=np.float64,
        )
        def_vel = np.array(
            [[row[f"op_vx_{i}"], row[f"op_vy_{i}"]] for i in range(n_outfield)]
            + [[row["ogk_vx"], row["ogk_vy"]]],
            dtype=np.float64,
        )

        positions = np.vstack([att_pos, def_pos])
        velocities = np.vstack([att_vel, def_vel])
        is_att = np.array([True] * 11 + [False] * 11, dtype=bool)
        is_gk = np.array([False] * 10 + [True] + [False] * 10 + [True], dtype=bool)
        ball = np.array([row["ball_x"], row["ball_y"]], dtype=np.float64)
        jerseys = (
            [str(row.get(f"fo_jersey_{i}", i + 1)) for i in range(n_outfield)]
            + ["GK"]
            + [str(i + 1) for i in range(n_outfield)]
            + ["GK"]
        )

        return TrackingState(
            match_id=match_id,
            frame_num=int(row["frame_num"]),
            period=int(row["period"]),
            focal_is_home=focal_is_home,
            positions=positions,
            velocities=velocities,
            is_att=is_att,
            is_gk=is_gk,
            jerseys=jerseys,
            ball=ball,
            offside=compute_offside(positions, is_att, ball, offside_tol_m),
        )

    raise FileNotFoundError(
        f"Could not locate stride-8 cache for match {match_id} under {data_root}. "
        "Please verify your PFF dataset layout per DATA_ACCESS.md."
    )
