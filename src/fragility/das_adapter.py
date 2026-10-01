"""Frozen EXP032 AM03 DAS call and exact grid-area expression."""
import json
from pathlib import Path
CFG = json.loads((Path(__file__).resolve().parents[2] / "configs/literature_benchmark.json").read_text())

def _das_batch(ann_rec, akey, sub, period_of):
    """DAS and accessible space for every state of one match, in one library call.

    Bischofberger & Baca (2026), `accessible-space` 2.1.0, unmodified, published
    defaults only (AM02 §3). Returns {frame_num: (DAS, AS_ACC)}.

    ENVIRONMENT DEFECT, WORKED AROUND AT THE CALL SITE ONLY (AM02 §3): the library
    predates pandas 3. `accessible_space/interface.py:216` evaluates `.values` on a
    string-dtype Series, which under pandas 3.0.5 returns an Arrow-backed array rather
    than a numpy array, and the next line's `passer_teams[:, np.newaxis]` then raises
    `IndexError: too many indices for array`. Passing team_id / team_in_possession as
    numpy `object` dtype restores the numpy array the library expects. The installed
    package is NOT patched.
    """
    import warnings
    import numpy as np, pandas as pd
    import accessible_space as accs
    from obso.state import state_from_cache_row
    from obso.operator import carrier_index

    FOCAL, OPP = "Focal", "Opponent"
    BATCH = 200   # frames per library call; bounds peak RSS (see below)

    def _one(frames_wanted):
        rows = []
        for (fn, st, car, per) in frames_wanted:
            pos = np.asarray(st.positions, float); vel = np.asarray(st.velocities, float)
            is_att = np.asarray(st.is_att, bool); is_gk = np.asarray(st.is_gk, bool)
            assert len(pos)==22 and int(is_gk.sum())==2 and car!='ball'
            ball = np.asarray(st.ball, float)
            rows.append((fn, "ball", "Ball", ball[0], ball[1], 0.0, 0.0, FOCAL, car, per))
            for k in range(pos.shape[0]):
                # Keep both goalkeepers: they affect interception and the offside line.
                tag = ("fo" if is_att[k] else "op") + str(k)
                team = FOCAL if is_att[k] else OPP
                rows.append((fn, tag, team, pos[k, 0], pos[k, 1], vel[k, 0], vel[k, 1],
                             FOCAL, car, per))
        if not rows:
            return {}
        tr = pd.DataFrame(rows, columns=["frame_id", "player_id", "team_id", "x", "y",
                                         "vx", "vy", "team_in_possession",
                                         "player_in_possession", "period_id"])
        for c in ("team_id", "team_in_possession", "player_in_possession"):
            tr[c] = tr[c].astype(object)
        with warnings.catch_warnings():
            # The focal frame is already normalised so the focal team attacks +x, which is
            # exactly the library's left-to-right assumption; no direction is inferred.
            warnings.simplefilter("ignore")
            res = accs.get_dangerous_accessible_space(
                tr, period_col="period_id",
                attacking_direction_col=None, infer_attacking_direction=False,
                respect_offside=True, player_in_possession_col="player_in_possession",
                use_progress_bar=False,
                chunk_size=int(CFG["das_frozen_params"]["chunk_size"]))
        aligned=pd.DataFrame({'frame':tr.frame_id.to_numpy(),
            'library_frame':np.asarray(res.frame_index), 'DAS':np.asarray(res.das,float),
            'AS':np.asarray(res.acc_space,float)})
        assert (aligned.groupby('frame')[['library_frame','DAS','AS']].nunique()==1).all().all()
        per_frame=aligned.groupby('frame',sort=False).first()
        assert per_frame.library_frame.is_unique
        assert np.isfinite(per_frame[['DAS','AS']].to_numpy()).all()
        out={int(fn):(float(r.DAS),float(r.AS)) for fn,r in per_frame.iterrows()}
        # The library retains the whole per-frame simulation tensor on the result object
        # (~1.2 GB for a 2340-frame match). Only the two scalars per frame are wanted, so
        # drop everything else before the next batch or 8 workers exhaust the 8 GB host.
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
        # Preserve the frozen 12 m identification rule. Airborne/no-nearby-player
        # states have no identified carrier, so no player gets the exemption.
        pending.append((fn, st, f"fo{j}" if j is not None else None,
                        int(period_of(fn))))
    out = {}
    for s in range(0, len(pending), BATCH):
        out.update(_one(pending[s:s + BATCH]))
    return out

def _frozen_cell_area(GRID):
    """Grid cell area, expression-identical to the frozen EXP029 lineage.

    e29_common.py:113-115 derives it from the grid targets' first-cell spacing.
    Do not substitute PitchGrid.cell_area_m2 (mean spacing) or a nominal 105/50*68/32:
    the point of the prereg production-equivalence gate is to reproduce the frozen
    pipeline exactly, and its tolerance is 1e-9 absolute on values of order 1e3 m^2.
    """
    import numpy as np
    targets = np.asarray(GRID.targets, dtype=float)
    return float((targets[0, 1, 0] - targets[0, 0, 0]) * (targets[1, 0, 1] - targets[0, 0, 1]))
