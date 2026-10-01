"""Frozen classifier fitting and evaluation routines."""

from __future__ import annotations
import numpy as np
import pandas as pd

LOGREG_C = 1.0
LOGREG_MAX_ITER = 200
LOGREG_TOL = 1e-10
N_FOLDS = 5


def fit_logistic(
    X: np.ndarray,
    y: np.ndarray,
    *,
    C: float = LOGREG_C,
    max_iter: int = LOGREG_MAX_ITER,
    tol: float = LOGREG_TOL,
) -> dict:
    """L2-regularised logistic regression by Newton-Raphson (IRLS)."""
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    n, p = X.shape
    y01 = (y > 0.5).astype(float)
    ym = np.where(y01 > 0.5, 1.0, -1.0)
    A = np.hstack([X, np.ones((n, 1))])
    w = np.zeros(p + 1, dtype=float)

    def obj(wv):
        z = ym * (A @ wv)
        return 0.5 * float(wv[:p] @ wv[:p]) + C * float(np.logaddexp(0.0, -z).sum())

    f_old = obj(w)
    for _ in range(max_iter):
        z = A @ w
        s = 1.0 / (1.0 + np.exp(-np.clip(z, -700.0, 700.0)))
        g = np.zeros(p + 1, dtype=float)
        g[:p] = w[:p] + C * (X.T @ (s - y01))
        g[p] = C * float((s - y01).sum())
        W = s * (1.0 - s)
        H = np.zeros((p + 1, p + 1), dtype=float)
        H[:p, :p] = np.eye(p) + C * (X.T @ (X * W[:, None]))
        H[:p, p] = C * (X.T @ W)
        H[p, :p] = H[:p, p]
        H[p, p] = C * float(W.sum())
        H = H + 1e-10 * np.eye(p + 1)
        try:
            step = np.linalg.solve(H, g)
        except np.linalg.LinAlgError:
            break
        t = 1.0
        improved = False
        for _ls in range(30):
            w_new = w - t * step
            f_new = obj(w_new)
            if np.isfinite(f_new) and f_new <= f_old:
                improved = True
                break
            t *= 0.5
        if not improved:
            break
        delta = float(np.max(np.abs(w_new - w)))
        w, f_old = (w_new, f_new)
        if delta < tol:
            break
    return {
        "coef": w[:p].copy(),
        "intercept": float(w[p]),
        "objective": float(f_old),
        "n_train": int(n),
        "n_features": int(p),
    }


def predict_logistic(model: dict, X: np.ndarray) -> np.ndarray:
    X = np.asarray(X, dtype=float)
    z = X @ model["coef"] + model["intercept"]
    return 1.0 / (1.0 + np.exp(-np.clip(z, -700.0, 700.0)))


def _average_ranks(x: np.ndarray) -> np.ndarray:
    """1-based average ranks with ties resolved by their mean rank (vectorised)."""
    order = np.argsort(x, kind="mergesort")
    xs = x[order]
    uniq, inv, counts = np.unique(xs, return_inverse=True, return_counts=True)
    cum = np.cumsum(counts)
    start = cum - counts
    avg = (start + cum + 1) / 2.0
    ranks_sorted = avg[inv]
    out = np.empty_like(ranks_sorted)
    out[order] = ranks_sorted
    return out


def roc_auc(y: np.ndarray, p: np.ndarray) -> float:
    """Rank-based ROC AUC (Mann-Whitney U with mid-ranks).  NaN if one class."""
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    ok = np.isfinite(p)
    y, p = (y[ok], p[ok])
    n_pos = int((y > 0.5).sum())
    n_neg = int(len(y) - n_pos)
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    ranks = _average_ranks(p)
    r_pos = float(ranks[y > 0.5].sum())
    return float((r_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def pr_auc(y: np.ndarray, p: np.ndarray) -> float:
    """Average precision, the scikit-learn step definition (vectorised)."""
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    ok = np.isfinite(p)
    y, p = (y[ok], p[ok])
    n_pos = int((y > 0.5).sum())
    if n_pos == 0 or len(y) == 0:
        return float("nan")
    order = np.argsort(-p, kind="mergesort")
    ys = y[order]
    tp = np.cumsum(ys)
    rank = np.arange(1, len(ys) + 1, dtype=float)
    precision = tp / rank
    recall = tp / n_pos
    sel = ys > 0.5
    if not sel.any():
        return float("nan")
    p_sel = precision[sel]
    r_sel = recall[sel]
    r_prev = np.concatenate([[0.0], r_sel[:-1]])
    return float(np.sum((r_sel - r_prev) * p_sel))


def brier(y: np.ndarray, p: np.ndarray) -> float:
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    ok = np.isfinite(p)
    if ok.sum() == 0:
        return float("nan")
    return float(np.mean((p[ok] - y[ok]) ** 2))


def capture_at(y: np.ndarray, p: np.ndarray, frac: float = 0.1) -> float:
    """Fraction of all positives inside the highest-risk ``frac`` of states."""
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    ok = np.isfinite(p)
    y, p = (y[ok], p[ok])
    n = len(y)
    n_pos = int((y > 0.5).sum())
    if n == 0 or n_pos == 0:
        return float("nan")
    k = max(1, int(np.ceil(frac * n)))
    top = np.argsort(-p, kind="mergesort")[:k]
    return float(y[top].sum() / n_pos)


def metrics_bundle(y: np.ndarray, p: np.ndarray) -> dict:
    return {
        "n": int(len(y)),
        "n_pos": int(np.sum(np.asarray(y) > 0.5)),
        "event_rate": float(np.mean(y)) if len(y) else float("nan"),
        "roc_auc": roc_auc(y, p),
        "pr_auc": pr_auc(y, p),
        "brier": brier(y, p),
        "capture_at_10": capture_at(y, p, 0.1),
    }


def assign_folds(match_ids, n_folds: int = N_FOLDS) -> dict[str, int]:
    """Deterministic match -> fold assignment."""
    ids = sorted({str(m) for m in match_ids}, key=int)
    return {m: i % n_folds for i, m in enumerate(ids)}


def review_capture(y, p, match_ids, frame_ids, frac=0.1):
    """Top-frac state selection with deterministic tie-break; window capture."""
    order = np.lexsort((frame_ids, match_ids, -np.asarray(p, float)))
    n = len(y)
    k = max(1, int(np.ceil(frac * n)))
    sel = np.zeros(n, dtype=bool)
    sel[order[:k]] = True
    y = np.asarray(y, float)
    return (sel, float(y[sel].sum() / y.sum()) if y.sum() else float("nan"))


def event_capture(df, sel_col):
    """Unique-event capture fraction over linked CAP events."""
    ev = {}
    for keys, s in zip(df["cap_event_keys"], df[sel_col].to_numpy(dtype=bool)):
        if not keys:
            continue
        for k in str(keys).split(";"):
            ev.setdefault(k, False)
            ev[k] = ev[k] or bool(s)
    if not ev:
        return (0, 0, float("nan"))
    got = sum((1 for v in ev.values() if v))
    return (len(ev), got, got / len(ev))
