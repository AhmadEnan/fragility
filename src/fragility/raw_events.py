"""Frozen event parsing and possession segmentation; no historical outcome proxy."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
BREAK_EVENTS = frozenset({"OUT", "SUB", "END", "G", "ON", "OFF"})
KICKOFF_EVENTS = frozenset({"FIRSTKICKOFF", "SECONDKICKOFF", "THIRDKICKOFF", "FOURTHKICKOFF"})
FPS = 29.97

def load_events(path: Path) -> pd.DataFrame:
    """Flatten one match's event JSON into the columns this study uses."""
    with open(path) as handle:
        raw = json.load(handle)
    rows = []
    for entry in raw:
        game = entry["gameEvents"]
        poss = entry["possessionEvents"]
        grades = entry["grades"]
        ball = entry["ball"]
        ball_xy = (ball[0].get("x"), ball[0].get("y")) if ball else (None, None)
        rows.append({
            "match_id": entry["gameId"],
            "game_event_id": entry["gameEventId"],
            "possession_event_id": entry["possessionEventId"],
            "start_time": entry["startTime"],
            "end_time": entry["endTime"],
            "duration": entry["duration"],
            "sequence": entry["sequence"],
            "period": game["period"],
            "game_event_type": game["gameEventType"],
            "team_id": game["teamId"],
            "team_name": game["teamName"],
            "home_team": game["homeTeam"],
            "player_id": game["playerId"],
            "player_name": game["playerName"],
            "setpiece_type": game["setpieceType"],
            "touches": game["touches"],
            "touches_in_box": game["touchesInBox"],
            "initial_non_event": game["initialNonEvent"],
            "poss_event_type": poss["possessionEventType"],
            "non_event": poss["nonEvent"],
            "passer_player_id": poss["passerPlayerId"],
            "passer_player_name": poss["passerPlayerName"],
            "receiver_player_id": poss["receiverPlayerId"],
            "target_player_id": poss["targetPlayerId"],
            "pass_type": poss["passType"],
            "pass_outcome_type": poss["passOutcomeType"],
            "accuracy_type": poss["accuracyType"],
            "lines_broken_type": poss["linesBrokenType"],
            "pressure_type": poss["pressureType"],
            "better_option_type": poss["betterOptionType"],
            "creates_space": poss["createsSpace"],
            "shot_outcome_type": poss["shotOutcomeType"],
            "shot_type": poss["shotType"],
            "ball_height_type": poss["ballHeightType"],
            "passer_grade": grades["passerGrade"],
            "receiver_grade": grades["receiverGrade"],
            "event_ball_x": ball_xy[0],
            "event_ball_y": ball_xy[1],
        })
    frame = pd.DataFrame(rows)
    frame = frame.sort_values(["period", "start_time", "sequence"], kind="mergesort")
    return frame.reset_index(drop=True)

def assign_possessions(events: pd.DataFrame) -> pd.DataFrame:
    """Label maximal runs of consecutive same-team events as possessions.

    gameEventType is ~95% "OTB" so it cannot delimit possessions on its own.
    A run ends when the team on the ball changes, the period changes, or play
    stops. Rows with no team (END, some stoppages) are breaks, not possessions.
    """
    events = events.copy()
    team = events["team_id"].to_numpy(dtype=object)
    period = events["period"].to_numpy()
    kind = events["game_event_type"].to_numpy(dtype=object)
    starts = np.zeros(len(events), dtype=bool)
    starts[0] = True
    for i in range(1, len(events)):
        starts[i] = (
            period[i] != period[i - 1]
            or team[i] != team[i - 1]
            or kind[i - 1] in BREAK_EVENTS
            or kind[i] in KICKOFF_EVENTS
        )
    events["possession_index"] = np.cumsum(starts) - 1
    # Drop possessions that have no team on the ball; they are stoppage markers.
    events.loc[events["team_id"].isna(), "possession_index"] = -1
    grouped = events[events["possession_index"] >= 0].groupby("possession_index")
    meta = pd.DataFrame({
        "poss_start_time": grouped["start_time"].min(),
        "poss_end_time": grouped["end_time"].max(),
        "poss_n_events": grouped.size(),
        "poss_setpiece": grouped["setpiece_type"].first(),
        "poss_first_event": grouped["game_event_type"].first(),
    })
    meta["poss_duration"] = meta["poss_end_time"] - meta["poss_start_time"]
    meta["poss_start_kind"] = meta["poss_setpiece"].fillna("open")
    events = events.merge(meta, left_on="possession_index", right_index=True, how="left")
    events["t_poss"] = events["start_time"] - events["poss_start_time"]
    events["poss_time_after"] = events["poss_end_time"] - events["start_time"]
    order = events[events["possession_index"] >= 0].groupby("possession_index").cumcount()
    events["poss_event_order"] = order
    return events

def add_frame_timing(events: pd.DataFrame) -> pd.DataFrame:
    """Recompute possession timing from tracking frames instead of event times.

    `startTime` is the onset of the *game* event, shared by every possession event
    inside it, so a pass carries the time its passer first touched the ball rather
    than the time of the pass (median difference 0.8 s). The possession-event frame
    is the pass itself, so frame differences give the timing the study needs.
    """
    events = events.copy()
    frame = pd.to_numeric(events["frame_num"], errors="coerce")
    events["event_frame"] = frame
    grouped = events[events["possession_index"] >= 0].groupby("possession_index")["event_frame"]
    first = grouped.min().rename("poss_first_frame")
    last = grouped.max().rename("poss_last_frame")
    events = events.merge(first, left_on="possession_index", right_index=True, how="left")
    events = events.merge(last, left_on="possession_index", right_index=True, how="left")
    events["t_poss_frame"] = (frame - events["poss_first_frame"]) / FPS
    events["poss_after_frame"] = (events["poss_last_frame"] - frame) / FPS
    events["poss_duration_frame"] = (events["poss_last_frame"] - events["poss_first_frame"]) / FPS
    return events
