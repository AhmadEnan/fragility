"""Original EXP032 feature functions for reference.

These require the original experiment driver globals and research modules.
They are separate from the portable reproduction notebook.
"""


def _surfaces():
    import numpy as np
    from pct_common import GRID, CONFIG, CANONICAL, FIELD_VALUE
    from obso.danger import score_surface

    epv = np.loadtxt(ROOT / "assets" / "EPV_grid.csv", delimiter=",", dtype=float)
    assert epv.shape == tuple(CFG["grid"]["epv_grid_shape"]), f"EPV grid {epv.shape}"
    assert (
        GRID.targets.shape[:2] == epv.shape
    ), f"grid/EPV mismatch {GRID.targets.shape} {epv.shape}"
    return (
        GRID,
        CONFIG,
        CANONICAL,
        np.asarray(FIELD_VALUE, float),
        score_surface(GRID, CONFIG),
        epv,
    )


def _frozen_cell_area(GRID):
    import numpy as np

    targets = np.asarray(GRID.targets, dtype=float)
    return float(
        (targets[0, 1, 0] - targets[0, 0, 0]) * (targets[1, 0, 1] - targets[0, 0, 1])
    )


def _das_batch(ann_rec, akey, sub, period_of):
    import warnings
    import numpy as np, pandas as pd
    import accessible_space as accs
    from obso.state import state_from_cache_row
    from obso.operator import carrier_index

    FOCAL, OPP = ("Focal", "Opponent")
    BATCH = 200

    def _one(frames_wanted):
        rows = []
        for fn, st, car, per in frames_wanted:
            pos = np.asarray(st.positions, float)
            vel = np.asarray(st.velocities, float)
            is_att = np.asarray(st.is_att, bool)
            is_gk = np.asarray(st.is_gk, bool)
            assert len(pos) == 22 and int(is_gk.sum()) == 2 and (car != "ball")
            ball = np.asarray(st.ball, float)
            rows.append(
                (fn, "ball", "Ball", ball[0], ball[1], 0.0, 0.0, FOCAL, car, per)
            )
            for k in range(pos.shape[0]):
                tag = ("fo" if is_att[k] else "op") + str(k)
                team = FOCAL if is_att[k] else OPP
                rows.append(
                    (
                        fn,
                        tag,
                        team,
                        pos[k, 0],
                        pos[k, 1],
                        vel[k, 0],
                        vel[k, 1],
                        FOCAL,
                        car,
                        per,
                    )
                )
        if not rows:
            return {}
        tr = pd.DataFrame(
            rows,
            columns=[
                "frame_id",
                "player_id",
                "team_id",
                "x",
                "y",
                "vx",
                "vy",
                "team_in_possession",
                "player_in_possession",
                "period_id",
            ],
        )
        for c in ("team_id", "team_in_possession", "player_in_possession"):
            tr[c] = tr[c].astype(object)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = accs.get_dangerous_accessible_space(
                tr,
                period_col="period_id",
                attacking_direction_col=None,
                infer_attacking_direction=False,
                respect_offside=True,
                player_in_possession_col="player_in_possession",
                use_progress_bar=False,
                chunk_size=int(CFG["das_frozen_params"]["chunk_size"]),
            )
        aligned = pd.DataFrame(
            {
                "frame": tr.frame_id.to_numpy(),
                "library_frame": np.asarray(res.frame_index),
                "DAS": np.asarray(res.das, float),
                "AS": np.asarray(res.acc_space, float),
            }
        )
        assert (
            (aligned.groupby("frame")[["library_frame", "DAS", "AS"]].nunique() == 1)
            .all()
            .all()
        )
        per_frame = aligned.groupby("frame", sort=False).first()
        assert per_frame.library_frame.is_unique
        assert np.isfinite(per_frame[["DAS", "AS"]].to_numpy()).all()
        out = {int(fn): (float(r.DAS), float(r.AS)) for fn, r in per_frame.iterrows()}
        del res
        return out

    pending = []
    for r in sub.itertuples(index=False):
        fn = int(r.frame_num)
        i = akey.get((fn, bool(r.focal_is_home)))
        if i is None:
            continue
        st = state_from_cache_row(ann_rec[i])
        j = carrier_index(st, 12.0)
        pending.append(
            (fn, st, f"fo{j}" if j is not None else None, int(period_of(fn)))
        )
    out = {}
    for s in range(0, len(pending), BATCH):
        out.update(_one(pending[s : s + BATCH]))
    return out


def solve_match(match_id: str):
    e22 = _init()
    import numpy as np, pandas as pd
    import cap_common as cc
    from obso.state import state_from_cache_row
    from obso.ppcf import time_to_intercept
    from sfa_common import StructuralOperator
    from scipy.spatial import ConvexHull, Delaunay

    mid = str(match_id)
    assert mid in DEV, f"non-DEV match {mid} REFUSED"
    assert mid not in FORBIDDEN, f"TEST match {mid} REFUSED"
    GRID, CONFIG, CANONICAL, S_FIELD, S_SCORE, EPV = _surfaces()
    CELL_AREA = _frozen_cell_area(GRID)
    import dataclasses
    from obso.danger import DangerConfig

    CFG_SIGMA14 = dataclasses.replace(
        DangerConfig(), sigma=float(CFG["das_frozen_params"]["obso_transition_sigma_m"])
    )
    from obso.danger import obso_surfaces

    tgt = np.asarray(GRID.targets, float)
    gx, gy = (tgt[:, :, 0], tgt[:, :, 1])
    gxy = tgt.reshape(-1, 2)
    gridx = np.asarray(GRID.x, float)
    gridy = np.asarray(GRID.y, float)
    out_path = OUT / f"comparators_{mid}.parquet"
    part_path = OUT / f"comparators_{mid}.partial.parquet"
    meta_path = out_path.with_suffix(".metadata.json")
    fingerprint = _fingerprint()
    if (
        out_path.exists()
        and meta_path.exists()
        and (json.loads(meta_path.read_text()).get("fingerprint") == fingerprint)
    ):
        return {
            "match_id": mid,
            "status": "cached",
            "n": int(len(pd.read_parquet(out_path))),
        }
    dev = pd.read_parquet(
        ROOT
        / "experiments"
        / "EXP_SOG_PREDICTIVE_CONFIRM_029"
        / "data"
        / "DEV_FEATURES.parquet"
    )
    dev["match_id"] = dev["match_id"].astype(str)
    sub = dev[dev["match_id"] == mid][
        ["state_key", "frame_num", "focal_is_home", "C0_ATTACK_AREA_m2"]
    ].copy()
    if sub.empty:
        return {"match_id": mid, "status": "empty", "n": 0}
    tv = cc.view(mid)
    ann = tv.ann
    akey = {
        (int(r.frame_num), bool(r.focal_is_home)): i
        for i, r in enumerate(ann.itertuples(index=False))
    }
    ann_rec = ann.to_dict("records")
    rows, done = ([], set())
    partial_meta = part_path.with_suffix(".metadata.json")
    if (
        part_path.exists()
        and partial_meta.exists()
        and (json.loads(partial_meta.read_text()).get("fingerprint") == fingerprint)
        and (not CFG.get("am03_refresh_source"))
    ):
        try:
            prev = pd.read_parquet(part_path)
            if {"C0_ATTACK_AREA_recomputed", "C0_ATTACK_AREA_frozen"} <= set(
                prev.columns
            ):
                rows = prev.to_dict("records")
                done = {str(k) for k in prev["state_key"]}
            else:
                part_path.unlink()
        except Exception:
            rows, done = ([], set())
    period_by_frame = {int(a["frame_num"]): int(a["period"]) for a in ann_rec}
    das_map, das_err = ({}, "")
    try:
        das_map = _das_batch(ann_rec, akey, sub, period_by_frame.get)
    except Exception as exc:
        das_err = f"{type(exc).__name__}:{str(exc)[:90]}"
        das_map = {}
    print(
        f"  match {mid}: DAS/AS for {len(das_map)}/{len(sub)} states"
        + (f"  DAS_ERROR {das_err}" if das_err else ""),
        flush=True,
    )
    if CFG.get("am03_refresh_source"):
        source = ROOT / CFG["am03_refresh_source"] / f"comparators_{mid}.parquet"
        manifest = ROOT / "archive/exp032_pre_am03/SHA256SUMS.txt"
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        assert any(
            (
                source_hash in line and f"comparators_{mid}.parquet" in line
                for line in manifest.read_text(encoding="utf-8-sig").splitlines()
            )
        ), "preserved source hash mismatch"
        original = pd.read_parquet(source)
        assert (
            set(original.state_key) == set(sub.state_key)
            and original.state_key.is_unique
        )
        assert len(das_map) == len(sub) and (not das_err), f"DAS incomplete: {das_err}"
        refreshed = original.copy()
        refreshed["DAS"] = [das_map[int(fn)][0] for fn in refreshed.frame_num]
        refreshed["AS_ACC"] = [das_map[int(fn)][1] for fn in refreshed.frame_num]
        inherited = [c for c in original.columns if c not in ("DAS", "AS_ACC")]
        pd.testing.assert_frame_equal(
            original[inherited], refreshed[inherited], check_exact=True
        )
        assert np.isfinite(refreshed[["DAS", "AS_ACC"]].to_numpy()).all()
        assert float(refreshed.C0_equiv_abs_diff.max()) <= float(
            CFG["stop_rules"]["c0_equivalence_tol"]
        )
        _write_atomic(out_path, refreshed)
        meta_path.write_text(
            json.dumps(
                {
                    "fingerprint": fingerprint,
                    "unchanged_columns_exact": inherited,
                    "preserved_source_sha256": hashlib.sha256(
                        source.read_bytes()
                    ).hexdigest(),
                    "n": len(refreshed),
                },
                indent=2,
            )
        )
        return {
            "match_id": mid,
            "status": "AM03_DAS_REFRESH",
            "n": len(refreshed),
            "n_failed": int(refreshed.build_failed.sum()),
            "das_finite": len(das_map),
            "unchanged_columns_bit_identical": True,
        }
    t0 = time.time()
    n_since = 0
    for r in sub.itertuples(index=False):
        sk = str(r.state_key)
        if sk in done:
            continue
        rec = {
            "state_key": sk,
            "match_id": mid,
            "frame_num": int(r.frame_num),
            "focal_is_home": bool(r.focal_is_home),
            "build_failed": False,
            "fail_reason": "",
            "C0_ATTACK_AREA_frozen": float(r.C0_ATTACK_AREA_m2),
            "C0_ATTACK_AREA_recomputed": float("nan"),
            "DAS": float("nan"),
            "AS_ACC": float("nan"),
            "D_OBSO_SIGMA14": float("nan"),
        }
        try:
            i = akey.get((int(r.frame_num), bool(r.focal_is_home)))
            if i is None:
                raise RuntimeError("no_ann_row")
            st = state_from_cache_row(ann_rec[i])
            pos = np.asarray(st.positions, float)
            vel = np.asarray(st.velocities, float)
            is_att = np.asarray(st.is_att, bool)
            is_gk = np.asarray(st.is_gk, bool)
            ball = np.asarray(st.ball, float)
            dmask = ~is_att & ~is_gk
            dpos = pos[dmask]
            op = StructuralOperator(st)
            C0 = np.clip(np.asarray(op.base.control, float), 0.0, 1.0)
            rec["C0_ATTACK_AREA_recomputed"] = float(CELL_AREA * C0.ravel().sum())
            surf = obso_surfaces(GRID, ball, C0, CONFIG)
            rec["D_OBSO"] = float(surf["D"])
            rec["D_OBSO_SIGMA14"] = float(
                obso_surfaces(GRID, ball, C0, CFG_SIGMA14)["D"]
            )
            rec["EPV_WEIGHTED_CONTROL"] = float((C0 * EPV).sum())
            rec["SSCORE_WEIGHTED_CONTROL"] = float((C0 * S_SCORE).sum())
            rec["FIELD_WEIGHTED_CONTROL"] = float((C0 * S_FIELD).sum())
            ix = int(np.argmin(np.abs(gridx - ball[0])))
            iy = int(np.argmin(np.abs(gridy - ball[1])))
            rec["EPV_AT_BALL"] = float(EPV[iy, ix])
            _d = das_map.get(int(r.frame_num))
            if _d is not None:
                rec["DAS"], rec["AS_ACC"] = (float(_d[0]), float(_d[1]))
            tti = np.asarray(time_to_intercept(pos, vel, tgt, CANONICAL), float)
            att_t = tti[is_att].min(axis=0)
            def_t = tti[~is_att].min(axis=0)
            rec["DOMINANT_REGION_SHARE"] = float((att_t < def_t).mean())
            rec["OFFSIDE_LINE_X"] = float(st.offside_line_x)
            ys = np.sort(dpos[:, 1])
            rec["G_LAT_MAX"] = (
                float(np.max(np.diff(ys))) if ys.size >= 2 else float("nan")
            )
            d2 = np.linalg.norm(dpos[:, None, :] - dpos[None, :, :], axis=-1)
            np.fill_diagonal(d2, np.inf)
            nnd = d2.min(axis=1)
            rec["CV_NND"] = (
                float(nnd.std() / nnd.mean()) if nnd.mean() > 0 else float("nan")
            )
            rec["PACKING_BYPASSED"] = float((dpos[:, 0] < ball[0]).sum())
            uniq = np.unique(np.round(dpos, 6), axis=0)
            if uniq.shape[0] >= 3:
                try:
                    hull = ConvexHull(dpos)
                    A = float(hull.volume)
                    P = float(hull.area)
                    bw = float(dpos[:, 0].max() - dpos[:, 0].min())
                    bh = float(dpos[:, 1].max() - dpos[:, 1].min())
                    rec["SOLIDITY_BBOX"] = (
                        A / (bw * bh) if bw > 0 and bh > 0 else float("nan")
                    )
                    rec["IPQ"] = 4.0 * np.pi * A / (P * P) if P > 0 else float("nan")
                    tri = Delaunay(dpos[hull.vertices])
                    inside = tri.find_simplex(gxy) >= 0
                    if inside.any():
                        dd = np.linalg.norm(
                            gxy[inside][:, None, :] - dpos[None, :, :], axis=-1
                        ).min(axis=1)
                        rec["R_EMPTY_GRID"] = float(dd.max())
                    else:
                        rec["R_EMPTY_GRID"] = float("nan")
                except Exception:
                    rec["SOLIDITY_BBOX"] = rec["IPQ"] = rec["R_EMPTY_GRID"] = float(
                        "nan"
                    )
            else:
                rec["SOLIDITY_BBOX"] = rec["IPQ"] = rec["R_EMPTY_GRID"] = float("nan")
        except Exception as exc:
            rec["build_failed"] = True
            rec["fail_reason"] = type(exc).__name__ + ":" + str(exc)[:80]
        rows.append(rec)
        n_since += 1
        if n_since >= CHECKPOINT_EVERY:
            _write_atomic(part_path, pd.DataFrame(rows))
            n_since = 0
            partial_meta.write_text(json.dumps({"fingerprint": fingerprint}))
    df = pd.DataFrame(rows)
    ok = np.isfinite(df["C0_ATTACK_AREA_recomputed"].to_numpy(float))
    d = np.abs(
        df.loc[ok, "C0_ATTACK_AREA_recomputed"].to_numpy(float)
        - df.loc[ok, "C0_ATTACK_AREA_frozen"].to_numpy(float)
    )
    max_diff = float(d.max()) if d.size else float("nan")
    n_cmp = int(d.size)
    tol = float(CFG["stop_rules"]["c0_equivalence_tol"])
    df["C0_equiv_abs_diff"] = np.where(
        ok,
        np.abs(
            df["C0_ATTACK_AREA_recomputed"].to_numpy(float)
            - df["C0_ATTACK_AREA_frozen"].to_numpy(float)
        ),
        np.nan,
    )
    if not np.isfinite(max_diff):
        raise SystemExit(
            f"C0 PRODUCTION-EQUIVALENCE GATE FAILED on match {mid}: 0 of {len(df)} states produced a finite recomputed area (operator/grid cell area unavailable). STOP per prereg §15."
        )
    if max_diff > tol:
        raise SystemExit(
            f"C0 PRODUCTION-EQUIVALENCE GATE FAILED on match {mid}: max_abs_diff {max_diff:.3e} > tol {tol:.1e} over {n_cmp} states. STOP."
        )
    _write_atomic(out_path, df)
    meta_path.write_text(
        json.dumps({"fingerprint": fingerprint, "n": len(df)}, indent=2)
    )
    if part_path.exists():
        part_path.unlink()
    return {
        "match_id": mid,
        "status": "built",
        "n": int(len(df)),
        "n_failed": int(df["build_failed"].sum()),
        "c0_equiv_max_abs_diff": max_diff,
        "c0_equiv_n": n_cmp,
        "das_finite": int(np.isfinite(df["DAS"].to_numpy(float)).sum()),
        "as_finite": int(np.isfinite(df["AS_ACC"].to_numpy(float)).sum()),
        "das_error": das_err,
        "seconds": round(time.time() - t0, 1),
    }
