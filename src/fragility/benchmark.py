"""Development benchmark transforms and tied-score statistics."""

import numpy as np
import pandas as pd


def average_precision(y, p):
    y = np.asarray(y, float)
    p = np.asarray(p, float)
    ok = np.isfinite(p)
    y, p = (y[ok], p[ok])
    groups = (
        pd.DataFrame({"p": p, "y": y})
        .groupby("p")
        .y.agg(["sum", "count"])
        .sort_index(ascending=False)
    )
    return float(
        (
            groups["sum"]
            / max(y.sum(), 1e-12)
            * (groups["sum"].cumsum() / groups["count"].cumsum())
        ).sum()
    )


def prep_arm(p, y):
    """One-time per-arm setup for the weighted bootstrap accumulator."""
    p = np.asarray(p, float)
    assert np.isfinite(
        p
    ).all(), "non-finite OOF prediction; weighted AUC assumes finite"
    order = np.argsort(p, kind="stable")
    ps = p[order]
    newgrp = np.empty(ps.size, bool)
    newgrp[0] = True
    np.not_equal(ps[1:], ps[:-1], out=newgrp[1:])
    grp = np.cumsum(newgrp) - 1
    return {
        "order": order,
        "grp": grp.astype(np.int64),
        "G": int(grp[-1]) + 1,
        "ys": y[order].astype(float),
    }


def wauc(pre, w):
    """Weighted mid-rank AUC of the multiset w against the precomputed order/grp."""
    order, grp, G, ys = (pre["order"], pre["grp"], pre["G"], pre["ys"])
    wg = w[order]
    gsum = np.bincount(grp, weights=wg, minlength=G)
    gstart = np.zeros(G, float)
    if G > 1:
        np.cumsum(gsum[:-1], out=gstart[1:])
    rank = gstart[grp] + (gsum[grp] + 1.0) * 0.5
    wp = wg * ys
    npos = float(wp.sum())
    nneg = float(wg.sum()) - npos
    if npos <= 0.0 or nneg <= 0.0:
        return float("nan")
    num = float((wp * rank).sum()) - npos * (npos + 1.0) / 2.0
    return num / (npos * nneg)


def design(df, cols, stats=None):
    """Median-impute + standardize; '<name>_sq' derived as z^2 (EXP029 convention)."""
    fit = stats is None
    stats = {} if fit else stats
    X = np.empty((len(df), len(cols)), float)
    for j, c in enumerate(cols):
        if c.endswith("_sq"):
            X[:, j] = X[:, cols.index(c[:-3])] ** 2
            continue
        v = df[c].to_numpy(float)
        if fit:
            med = float(np.nanmedian(v)) if np.isfinite(v).any() else 0.0
            vi = np.where(np.isfinite(v), v, med)
            mu, sd = (float(vi.mean()), float(vi.std(ddof=0)))
            stats[c] = {"median": med, "mean": mu, "std": sd if sd > 0 else 1.0}
        s = stats[c]
        vi = np.where(np.isfinite(v), v, s["median"])
        X[:, j] = (vi - s["mean"]) / s["std"]
    return (X, stats)
