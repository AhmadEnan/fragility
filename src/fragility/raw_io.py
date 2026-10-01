"""Read-only adapters for authorized provider files and locally built caches."""
from pathlib import Path
import numpy as np
import pandas as pd
from . import raw_events

RAW_ROOT = CACHE_ROOT = INDEX_ROOT = None


def configure(raw_root, cache_root, index_root):
    global RAW_ROOT, CACHE_ROOT, INDEX_ROOT
    RAW_ROOT, CACHE_ROOT, INDEX_ROOT = map(lambda p: Path(p).resolve(), (raw_root, cache_root, index_root))


def load_cache(match_id):
    if CACHE_ROOT is None:
        raise RuntimeError("Configure the authorized input paths first")
    return pd.read_parquet(CACHE_ROOT / f"match_{match_id}_stride8.parquet")


def load_index(match_id):
    if INDEX_ROOT is None:
        raise RuntimeError("Configure the authorized input paths first")
    return pd.read_parquet(INDEX_ROOT / f"event_frame_index_{match_id}.parquet")


def event_table(match_id):
    events = raw_events.load_events(RAW_ROOT / "Event Data" / f"{match_id}.json")
    index = load_index(match_id)
    poss_map = index.dropna(subset=["possession_event_id"]).drop_duplicates("possession_event_id").set_index("possession_event_id")["frame_num"]
    game_map = index.dropna(subset=["game_event_id"]).drop_duplicates("game_event_id").set_index("game_event_id")["frame_num"]
    by_poss = events["possession_event_id"].map(poss_map)
    by_game = events["game_event_id"].map(game_map)
    events["frame_num"] = by_poss.fillna(by_game)
    events["frame_source"] = np.where(by_poss.notna(), "possession", np.where(by_game.notna(), "game", "none"))
    events["attacking_team_is_home"] = events["home_team"].astype(bool)
    return events


def safe_output(output, *inputs):
    """Reject writing into inputs or into a parent containing any input."""
    out = Path(output).resolve()
    for value in inputs:
        path = Path(value).resolve()
        if out == path or out.is_relative_to(path) or path.is_relative_to(out):
            raise ValueError(f"Output must be separate from input: {out} / {path}")
    out.mkdir(parents=True, exist_ok=True)
    return out
