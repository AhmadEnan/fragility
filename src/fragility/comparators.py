"""Executable extraction of the four established comparators in Figure 2."""
import importlib.metadata
from pathlib import Path
import numpy as np
import pandas as pd
from obso.danger import obso_surfaces
from obso.state import state_from_cache_row
from .das_adapter import CFG, _das_batch
from .research_operator import GRID, CONFIG, StructuralOperator

EPV = np.loadtxt(Path(__file__).resolve().parents[2] / "assets/EPV_grid.csv", delimiter=",")
assert EPV.shape == GRID.targets.shape[:2] == (32, 50)


def scalar_features(state, op=None):
    op = StructuralOperator(state) if op is None else op
    c0 = np.clip(np.asarray(op.base.control, float), 0.0, 1.0)
    ix = int(np.argmin(np.abs(np.asarray(GRID.x) - state.ball[0])))
    iy = int(np.argmin(np.abs(np.asarray(GRID.y) - state.ball[1])))
    return {"EPV_AT_BALL": float(EPV[iy, ix]),
            "EPV_WEIGHTED_CONTROL": float((c0 * EPV).sum()),
            "D_OBSO": float(obso_surfaces(GRID, state.ball, c0, CONFIG)["D"])}


def extract_match(match_id, cohort, annotation):
    mid = str(match_id)
    if mid not in CFG["dev_matches"] or mid in CFG["forbidden_matches"]:
        raise ValueError(f"Figure 2 comparators are DEV-only; match {mid} refused")
    version = importlib.metadata.version("accessible-space")
    if version != "2.1.0":
        raise RuntimeError(f"Frozen DAS requires accessible-space==2.1.0; found {version}")
    sub = cohort.loc[cohort.match_id.astype(str).eq(mid)].copy()
    records = annotation.to_dict("records")
    keys = {(int(r["frame_num"]), bool(r["focal_is_home"])): i for i, r in enumerate(records)}
    periods = {int(r["frame_num"]): int(r["period"]) for r in records}
    das = _das_batch(records, keys, sub, periods.get)
    if len(das) != len(sub):
        raise RuntimeError("Incomplete DAS extraction; no silent cohort deletion")
    rows = []
    for r in sub.itertuples(index=False):
        state = state_from_cache_row(records[keys[(int(r.frame_num), bool(r.focal_is_home))]])
        rows.append({"state_key": r.state_key, **scalar_features(state), "DAS": das[int(r.frame_num)][0]})
    return pd.DataFrame(rows)
