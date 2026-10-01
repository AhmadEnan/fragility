"""Original PFF frame-cache preprocessing, with centered velocities."""

import os
import glob
import json
import bz2
import numpy as np
import pandas as pd

N_OUTFIELD = 10
MAX_SPEED = 12.0
VELOCITY_WINDOW = 3


def _match_ids(raw_dir):
    files = sorted(glob.glob(os.path.join(raw_dir, "Tracking Data", "*.jsonl.bz2")))
    return [os.path.basename(f).split(".")[0] for f in files]


def _load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _read_metadata(raw_dir, match_id):
    meta = _load_json(os.path.join(raw_dir, "Metadata", f"{match_id}.json"))
    meta = meta[0] if isinstance(meta, list) else meta
    return {
        "home_team_id": str(meta["homeTeam"]["id"]),
        "away_team_id": str(meta["awayTeam"]["id"]),
        "home_name": meta["homeTeam"]["shortName"],
        "away_name": meta["awayTeam"]["shortName"],
        "home_start_left": bool(meta["homeTeamStartLeft"]),
        "fps": float(meta.get("fps") or 29.97),
    }


def _read_gk_jerseys(raw_dir, match_id, meta):
    """Shirt numbers that belong to a goalkeeper, per team."""
    roster = _load_json(os.path.join(raw_dir, "Rosters", f"{match_id}.json"))
    gk = {meta["home_team_id"]: set(), meta["away_team_id"]: set()}
    for entry in roster:
        if entry.get("positionGroupType") != "GK":
            continue
        tid = str(entry["team"]["id"])
        if tid in gk:
            gk[tid].add(str(entry["shirtNumber"]))
    return (gk[meta["home_team_id"]], gk[meta["away_team_id"]])


def _pick_players(raw_list, gk_jerseys):
    """Split one frame's player list into (outfield, goalkeeper)."""
    if not raw_list:
        return None
    seen, players = (set(), [])
    for p in raw_list:
        j = str(p.get("jerseyNum"))
        if j in seen:
            continue
        x, y = (p.get("x"), p.get("y"))
        if x is None or y is None:
            return None
        seen.add(j)
        players.append((j, float(x), float(y)))
    keepers = [p for p in players if p[0] in gk_jerseys]
    outfield = [p for p in players if p[0] not in gk_jerseys]
    if len(keepers) != 1 or len(outfield) != N_OUTFIELD:
        return None
    return (outfield, keepers[0])


def _ball_xy(frame):
    b = frame.get("ballsSmoothed")
    if isinstance(b, dict) and b.get("x") is not None:
        return (float(b["x"]), float(b["y"]))
    b = frame.get("balls")
    if isinstance(b, list) and b and (b[0].get("x") is not None):
        return (float(b[0]["x"]), float(b[0]["y"]))
    return None


def _velocities(pos, fps, window=VELOCITY_WINDOW, max_speed=MAX_SPEED):
    """Central-difference velocity for an (T, P, 2) position array sampled at `fps`."""
    T = pos.shape[0]
    if T == 1:
        return np.zeros_like(pos)
    idx = np.arange(T)
    lo = np.clip(idx - window, 0, T - 1)
    hi = np.clip(idx + window, 0, T - 1)
    dt = (hi - lo).astype(np.float32) / fps
    dt[dt == 0] = 1.0 / fps
    vel = (pos[hi] - pos[lo]) / dt[:, None, None]
    speed = np.linalg.norm(vel, axis=-1, keepdims=True)
    scale = np.where(speed > max_speed, max_speed / np.maximum(speed, 1e-09), 1.0)
    return (vel * scale).astype(np.float32)


def _possession_series(events):
    """Forward-fill possession from PFF game events."""
    home_ball, in_play = ({}, {})
    cur_home, cur_in_play = (None, False)
    for i, ev in enumerate(events):
        if ev is not None:
            etype = ev.get("game_event_type")
            if etype == "OUT":
                cur_in_play = False
            elif etype in ("END",):
                cur_in_play = False
            else:
                hb = ev.get("home_ball")
                if hb is not None:
                    cur_home = bool(hb)
                    cur_in_play = True
        home_ball[i] = cur_home
        in_play[i] = cur_in_play and cur_home is not None
    return (home_ball, in_play)


def preprocess_match(raw_dir, match_id, out_path, stride=6, verbose=True):
    """Convert one raw match into a compact frame table and write it to `out_path`."""
    meta = _read_metadata(raw_dir, match_id)
    home_gk_j, away_gk_j = _read_gk_jerseys(raw_dir, match_id, meta)
    frames, events = ([], [])
    src = os.path.join(raw_dir, "Tracking Data", f"{match_id}.jsonl.bz2")
    with bz2.open(src, "rt") as fh:
        for k, line in enumerate(fh):
            if k % stride:
                continue
            d = json.loads(line)
            period = d.get("period")
            if period not in (1, 2, 3, 4):
                continue
            home = _pick_players(
                d.get("homePlayersSmoothed") or d.get("homePlayers"), home_gk_j
            )
            away = _pick_players(
                d.get("awayPlayersSmoothed") or d.get("awayPlayers"), away_gk_j
            )
            ball = _ball_xy(d)
            if home is None or away is None or ball is None:
                continue
            frames.append((int(d["frameNum"]), int(period), home, away, ball))
            events.append(d.get("game_event"))
    if not frames:
        if verbose:
            print(f"  match {match_id}: no usable frames")
        return None
    home_ball, in_play = _possession_series(events)
    T = len(frames)
    home_out = np.zeros((T, N_OUTFIELD, 2), np.float32)
    away_out = np.zeros((T, N_OUTFIELD, 2), np.float32)
    home_gk = np.zeros((T, 1, 2), np.float32)
    away_gk = np.zeros((T, 1, 2), np.float32)
    ball_xy = np.zeros((T, 1, 2), np.float32)
    home_j = np.empty((T, N_OUTFIELD), object)
    away_j = np.empty((T, N_OUTFIELD), object)
    periods = np.zeros(T, np.int8)
    frame_nums = np.zeros(T, np.int64)
    for t, (fnum, period, home, away, ball) in enumerate(frames):
        (h_out, h_gk), (a_out, a_gk) = (home, away)
        h_out = sorted(h_out, key=lambda p: int(p[0]) if p[0].isdigit() else 999)
        a_out = sorted(a_out, key=lambda p: int(p[0]) if p[0].isdigit() else 999)
        home_out[t] = [[p[1], p[2]] for p in h_out]
        away_out[t] = [[p[1], p[2]] for p in a_out]
        home_j[t] = [p[0] for p in h_out]
        away_j[t] = [p[0] for p in a_out]
        home_gk[t, 0] = [h_gk[1], h_gk[2]]
        away_gk[t, 0] = [a_gk[1], a_gk[2]]
        ball_xy[t, 0] = ball
        periods[t] = period
        frame_nums[t] = fnum
    eff_fps = meta["fps"] / stride
    lineup_key = np.array(
        [hash((tuple(home_j[t]), tuple(away_j[t]), int(periods[t]))) for t in range(T)]
    )
    seg_start = np.flatnonzero(np.r_[True, lineup_key[1:] != lineup_key[:-1]])
    seg_bounds = np.r_[seg_start, T]

    def _seg_vel(arr):
        out = np.zeros_like(arr)
        for a, b in zip(seg_bounds[:-1], seg_bounds[1:]):
            out[a:b] = _velocities(arr[a:b], eff_fps)
        return out

    home_out_v, away_out_v = (_seg_vel(home_out), _seg_vel(away_out))
    home_gk_v, away_gk_v = (_seg_vel(home_gk), _seg_vel(away_gk))
    ball_v = _seg_vel(ball_xy)
    home_attacks_plus = np.where(
        np.isin(periods, [1, 3]),
        1.0 if meta["home_start_left"] else -1.0,
        -1.0 if meta["home_start_left"] else 1.0,
    ).astype(np.float32)
    rows = []
    for focal_is_home in (True, False):
        flip = home_attacks_plus if focal_is_home else -home_attacks_plus
        f = flip[:, None, None]
        if focal_is_home:
            fo, fo_v, fgk, fgk_v = (home_out, home_out_v, home_gk, home_gk_v)
            op, op_v, ogk, ogk_v = (away_out, away_out_v, away_gk, away_gk_v)
            jerseys = home_j
            has_ball = np.array([home_ball[i] is True for i in range(T)])
        else:
            fo, fo_v, fgk, fgk_v = (away_out, away_out_v, away_gk, away_gk_v)
            op, op_v, ogk, ogk_v = (home_out, home_out_v, home_gk, home_gk_v)
            jerseys = away_j
            has_ball = np.array([home_ball[i] is False for i in range(T)])
        data = {
            "match_id": np.full(T, int(match_id), np.int64),
            "frame_num": frame_nums,
            "period": periods,
            "focal_is_home": np.full(T, focal_is_home),
            "flip": flip,
            "in_possession": has_ball,
            "ball_in_play": np.array([in_play[i] for i in range(T)]),
            "ball_x": ball_xy[:, 0, 0] * flip,
            "ball_y": ball_xy[:, 0, 1] * flip,
            "ball_vx": ball_v[:, 0, 0] * flip,
            "ball_vy": ball_v[:, 0, 1] * flip,
            "fgk_x": fgk[:, 0, 0] * flip,
            "fgk_y": fgk[:, 0, 1] * flip,
            "fgk_vx": fgk_v[:, 0, 0] * flip,
            "fgk_vy": fgk_v[:, 0, 1] * flip,
            "ogk_x": ogk[:, 0, 0] * flip,
            "ogk_y": ogk[:, 0, 1] * flip,
            "ogk_vx": ogk_v[:, 0, 0] * flip,
            "ogk_vy": ogk_v[:, 0, 1] * flip,
        }
        fo_r, fo_vr = (fo * f, fo_v * f)
        op_r, op_vr = (op * f, op_v * f)
        for i in range(N_OUTFIELD):
            data[f"fo_x_{i}"], data[f"fo_y_{i}"] = (fo_r[:, i, 0], fo_r[:, i, 1])
            data[f"fo_vx_{i}"], data[f"fo_vy_{i}"] = (fo_vr[:, i, 0], fo_vr[:, i, 1])
            data[f"op_x_{i}"], data[f"op_y_{i}"] = (op_r[:, i, 0], op_r[:, i, 1])
            data[f"op_vx_{i}"], data[f"op_vy_{i}"] = (op_vr[:, i, 0], op_vr[:, i, 1])
            data[f"fo_jersey_{i}"] = jerseys[:, i].astype(str)
        rows.append(pd.DataFrame(data))
    df = pd.concat(rows, ignore_index=True)
    df = df[df["ball_in_play"]].reset_index(drop=True)
    for c in df.columns:
        if df[c].dtype == np.float64:
            df[c] = df[c].astype(np.float32)
    df.to_parquet(out_path, index=False)
    if verbose:
        print(
            f"  match {match_id} ({meta['home_name']} v {meta['away_name']}): {T} frames -> {len(df)} rows"
        )
    return out_path


def build_frame_cache(
    raw_dir, cache_dir, match_ids=None, stride=6, force=False, verbose=True
):
    """Preprocess every requested match into `cache_dir`, skipping work already done."""
    if raw_dir is None:
        raise FileNotFoundError(
            'Raw PFF dataset not found. Set RAW_DIR to a directory containing "Tracking Data", "Metadata" and "Rosters".'
        )
    os.makedirs(cache_dir, exist_ok=True)
    ids = [
        str(m) for m in (match_ids if match_ids is not None else _match_ids(raw_dir))
    ]
    built = {}
    for mid in ids:
        out_path = os.path.join(cache_dir, f"match_{mid}_stride{stride}.parquet")
        if os.path.exists(out_path) and (not force):
            if verbose:
                print(f"  match {mid}: cached")
            built[mid] = out_path
            continue
        try:
            res = preprocess_match(
                raw_dir, mid, out_path, stride=stride, verbose=verbose
            )
            if res:
                built[mid] = res
        except FileNotFoundError as e:
            if verbose:
                print(f"  match {mid}: skipped ({e})")
    return built


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("raw_root")
    parser.add_argument("cache_root")
    parser.add_argument("--match", nargs="+", required=True)
    args = parser.parse_args()
    build_frame_cache(args.raw_root, args.cache_root, args.match, stride=8)
