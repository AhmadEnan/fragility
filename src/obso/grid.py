"""The 32 x 50 evaluation grid used by the continuous-OBSO paper."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

PITCH_LENGTH_M = 105.0
PITCH_WIDTH_M = 68.0

# The attacked goal, in the focal-attacking frame (focal team always attacks +x).
GOAL_X_M = PITCH_LENGTH_M / 2.0
POST_Y_M = 3.66  # half of the 7.32 m goal


@dataclass(frozen=True)
class PitchGrid:
    """Cell centres of the OBSO evaluation grid, plus the goal geometry."""

    x: np.ndarray  # (nx,)
    y: np.ndarray  # (ny,)
    targets: np.ndarray  # (ny, nx, 2)
    goal: np.ndarray  # (2,) attacked goal centre
    posts: np.ndarray  # (2, 2) the two posts

    @property
    def shape(self) -> tuple[int, int]:
        return (self.y.size, self.x.size)

    @property
    def n_cells(self) -> int:
        return self.y.size * self.x.size

    @property
    def cell_area_m2(self) -> float:
        return float(np.diff(self.x).mean() * np.diff(self.y).mean())


def make_grid(nx: int = 50, ny: int = 32) -> PitchGrid:
    """Cell-centre grid spanning the full playing surface.

    The 2020 paper evaluates a 32 x 50 matrix and reports OBSO as a discrete sum over
    cells, so the grid spans the whole pitch rather than an inset region.
    """
    x = np.linspace(-PITCH_LENGTH_M / 2 + PITCH_LENGTH_M / (2 * nx), PITCH_LENGTH_M / 2 - PITCH_LENGTH_M / (2 * nx), nx)
    y = np.linspace(-PITCH_WIDTH_M / 2 + PITCH_WIDTH_M / (2 * ny), PITCH_WIDTH_M / 2 - PITCH_WIDTH_M / (2 * ny), ny)
    gx, gy = np.meshgrid(x, y)  # (ny, nx)
    targets = np.stack([gx, gy], axis=-1)
    return PitchGrid(
        x=x,
        y=y,
        targets=targets,
        goal=np.array([GOAL_X_M, 0.0]),
        posts=np.array([[GOAL_X_M, POST_Y_M], [GOAL_X_M, -POST_Y_M]]),
    )
