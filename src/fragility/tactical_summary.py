"""Frozen tactical temporal recovery summaries (EXP023/024 convention)."""
import numpy as np
import pandas as pd
VENDOR_FPS = 29.9697
DT_STATE = 8.0 / VENDOR_FPS

def dir6(x: float) -> float:
    return round(float(x) % 360.0, 6)

def run_stats(frames: np.ndarray, flags: np.ndarray) -> tuple[int, float]:
    """Longest consecutive-True run (frames, seconds=(n-1)*DT_STATE)."""
    best = cur = 0
    for f in flags:
        cur = cur + 1 if f else 0
        best = max(best, cur)
    n = int(best)
    s = float((n - 1) * DT_STATE) if n >= 2 else 0.0
    return n, s

def summarize(g: pd.DataFrame, pre: np.ndarray) -> dict:
    """Per-action summaries over window frames (g, ordered by frame) + pre-release mask.

    Convention (EXP023/024): peak/median/mean/frac over VALID frames only
    (finite percentiles); runs break at invalid frames.
    """
    p = g["percentile"].to_numpy(dtype=float)
    v = p[np.isfinite(p)]
    out = {"peak": float(np.nanmax(v)), "median": float(np.nanmedian(v)),
           "mean": float(np.nanmean(v)), "frac": float((v >= 0.90).mean()),
           "n_valid": int(v.size)}
    run, run_s = run_stats(g["frame"].to_numpy(), np.where(np.isfinite(p), p >= 0.90, False))
    out.update({"run": run, "run_s": run_s,
                "top10": bool(run >= 2)})
    pmask = pre & np.isfinite(p)
    pp = p[pmask]
    if pp.size:
        out.update({"pre_peak": float(np.nanmax(pp)), "pre_median": float(np.nanmedian(pp)),
                    "pre_mean": float(np.nanmean(pp)), "pre_frac": float((pp >= 0.90).mean()),
                    "n_pre_valid": int(pp.size)})
        # pre-release runs: consecutive in WINDOW order, both pre-release and top10.
        # pre frames form a window prefix, so adjacency in window order is exact.
        # Runs break at invalid frames (NaN percentiles).
        idx = np.flatnonzero(pmask)
        prun = cur = 0
        prev = None
        for k in range(len(pp)):
            top = bool(pp[k] >= 0.90)
            if top and prev is not None and prev[0] == idx[k] - 1 and prev[1]:
                cur += 1
            elif top:
                cur = 1
            else:
                cur = 0
            prev = (int(idx[k]), top)
            prun = max(prun, cur)
        out.update({"pre_run": int(prun),
                    "pre_run_s": float((prun - 1) * DT_STATE) if prun >= 2 else 0.0,
                    "pre_sup": bool(prun >= 2)})
    else:
        out.update({"pre_peak": np.nan, "pre_median": np.nan, "pre_mean": np.nan,
                    "pre_frac": np.nan, "pre_run": 0, "pre_run_s": 0.0, "pre_sup": False})
    j = int(np.nanargmax(p))
    out.update({"tpeak": float(g["vendor_t"].to_numpy()[j]),
                "rpeak": float(g["rank"].to_numpy()[j])})
    return out
