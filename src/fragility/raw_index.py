"""Original raw tracking-to-event index builder."""
import bz2
import json
from pathlib import Path
import numpy as np
import pandas as pd

def build(match_id: str, raw_dir: Path, out_dir: Path) -> Path:
    src = raw_dir / "Tracking Data" / f"{match_id}.jsonl.bz2"
    rows = []
    n_lines = 0
    with bz2.open(src, "rt", encoding="utf-8") as handle:
        for line in handle:
            n_lines += 1
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("frameNum") is None or row.get("period") is None:
                continue
            rows.append(
                {
                    "match_id": int(row["gameRefId"]) if row.get("gameRefId") else int(match_id),
                    "frame_num": int(row["frameNum"]),
                    "period": int(row["period"]),
                    "video_time_s": float(row["videoTimeMs"]) / 1000.0
                    if row.get("videoTimeMs") is not None
                    else np.nan,
                    "period_elapsed_s": float(row["periodElapsedTime"])
                    if row.get("periodElapsedTime") is not None
                    else np.nan,
                    "game_event_id": row.get("game_event_id"),
                    "possession_event_id": row.get("possession_event_id"),
                    "game_event_type": (row.get("game_event") or {}).get("game_event_type"),
                    "possession_event_type": (row.get("possession_event") or {}).get(
                        "possession_event_type"
                    ),
                }
            )
    frame = pd.DataFrame(rows)
    for column in ("game_event_id", "possession_event_id"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"event_frame_index_{match_id}.parquet"
    frame.to_parquet(out, index=False)
    print(
        f"match {match_id}: {n_lines} tracking lines -> {len(frame)} rows; "
        f"{frame['possession_event_id'].notna().sum()} with possession_event_id, "
        f"{frame['game_event_id'].notna().sum()} with game_event_id -> {out}"
    )
    return out
