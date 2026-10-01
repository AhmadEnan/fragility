"""Extract the EXP029 context and SOG features from a licensed tracking state."""

from types import SimpleNamespace
import json

import numpy as np
import pandas as pd

from .config import CANONICAL_CONFIG
from .features import alignment_features, m0_features, state_scores_res0
from .pff import carrier_index, load_pff_state
from .pitch_control import compute_pitch_control, make_grid
from .sog import enumerate_actions, score_action


def extract_state_features(state, possession_age_s):
    """Return features in research units, before public-data normalization."""
    if not np.isfinite(possession_age_s) or possession_age_s < 0:
        raise ValueError("possession_age_s must be finite and nonnegative")
    config = CANONICAL_CONFIG
    grid = make_grid(
        config.grid_nx, config.grid_ny, config.pitch_length, config.pitch_width
    )
    C0, base_E, travel, coef = compute_pitch_control(
        state.positions,
        state.velocities,
        state.is_att,
        state.is_gk,
        state.offside,
        state.ball,
        grid,
        config,
    )
    base = SimpleNamespace(
        carrier_index=carrier_index(state, config.carrier_max_distance_m)
    )
    features = m0_features(state, base, C0, grid, float(possession_age_s))
    actions = pd.DataFrame(
        [
            score_action(state, action, C0, base_E, travel, coef, grid, config)
            for action in enumerate_actions(state, config)
        ]
    )
    reduced = state_scores_res0(
        {
            "R_RES0": actions.sog.to_numpy(),
            "valid_primary": actions.valid_primary.to_numpy(),
            "attacker_index": actions.attacker_index.to_numpy(),
            "jersey": actions.jersey.to_numpy(),
        },
        fraction=config.tail_fraction,
    )
    features.update(
        {"F_SOG" if key == "F_RES0" else key: value for key, value in reduced.items()}
    )
    valid = actions[actions.valid_primary & np.isfinite(actions.sog)]
    players = np.unique(valid.attacker_index)
    best = [
        valid[valid.attacker_index.eq(player)].iloc[
            int(np.argmax(valid.loc[valid.attacker_index.eq(player), "sog"]))
        ]
        for player in players
    ]
    q = np.array([row.sog for row in best])
    directions = np.array([row.direction_deg for row in best])
    alignment, top = alignment_features(state.velocities[players], directions, q)
    features.update(BEST_ALIGNMENT=alignment, TOP_PLAYER_ALIGNMENT=top)
    return features


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache_root")
    parser.add_argument("--match", required=True)
    parser.add_argument("--frame", required=True, type=int)
    parser.add_argument("--perspective", choices=["home", "away"], required=True)
    parser.add_argument("--possession-age-s", required=True, type=float)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    state = load_pff_state(
        args.cache_root,
        args.match,
        args.frame,
        focal_is_home=args.perspective == "home",
    )
    features = extract_state_features(state, args.possession_age_s)
    features = {
        key: None if isinstance(value, float) and not np.isfinite(value) else value
        for key, value in features.items()
    }
    args.output.write_text(
        json.dumps(features, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
