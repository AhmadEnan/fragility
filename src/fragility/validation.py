"""Validation statistics and statistical testing for SOG abstract claims.

Includes:
1. Tactical benchmark action recovery
2. Residual-weight incremental ablation SOG vs PCG (EXP024)
3. Grid resolution convergence G0 vs G1 (EXP026A)
4. State-level fragility and path accessibility on CAP pairs (EXP027)
5. Exact small-sample permutation AUC validation (EXP028)
"""

from __future__ import annotations

import itertools
import math
from typing import Any

import numpy as np
import pandas as pd


def wilson_ci(k: int | float, n: int, z: float = 1.96) -> tuple[float, float]:
    """Compute Wilson score 95% confidence interval for a proportion."""
    if n <= 0:
        return (float("nan"), float("nan"))
    p = float(k) / float(n)
    denom = 1.0 + (z ** 2) / n
    centre = p + (z ** 2) / (2.0 * n)
    spread = z * math.sqrt(p * (1.0 - p) / n + (z ** 2) / (4.0 * (n ** 2)))
    lo = max(0.0, (centre - spread) / denom)
    hi = min(1.0, (centre + spread) / denom)
    return (float(lo), float(hi))


def evaluate_tactical_recovery(
    player_actions_df: pd.DataFrame,
    cases_df: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Evaluate tactical benchmark recovery performance."""
    df = player_actions_df.copy()
    evaluable_mask = df["evaluability"].isin(["DIRECTLY_EVALUABLE", "OFFSIDE_CONFOUNDED_BUT_SCOREABLE"])
    eval_df = df[evaluable_mask].copy()

    # Bank A (Primary: 13 cases)
    ev_a = eval_df[eval_df["evidence_strength"] == "A"].copy()
    nA = len(ev_a)
    hitsA = int(ev_a["TOP10_SUPPORTED"].sum())
    rateA = hitsA / nA if nA > 0 else 0.0
    ciA = wilson_ci(hitsA, nA)

    pe_a = ev_a[ev_a["role_in_mechanism"] == "PRIMARY_EXPLOITER"]
    n_pe = len(pe_a)
    hits_pe = int(pe_a["TOP10_SUPPORTED"].sum())
    rate_pe = hits_pe / n_pe if n_pe > 0 else 0.0

    sc_a = ev_a[ev_a["role_in_mechanism"].isin(["SPACE_CREATOR", "DECOY", "DECOY_RUNNER"])]
    n_sc = len(sc_a)
    hits_sc = int(sc_a["TOP10_SUPPORTED"].sum())
    rate_sc = hits_sc / n_sc if n_sc > 0 else 0.0

    # Bank B (Secondary: 7 cases)
    ev_b = eval_df[eval_df["evidence_strength"] == "B"].copy()
    nB = len(ev_b)
    hitsB = int(ev_b["TOP10_SUPPORTED"].sum())
    rateB = hitsB / nB if nB > 0 else 0.0
    ciB = wilson_ci(hitsB, nB)

    out = {
        "A": {
            "cases": 13,
            "evaluable_actions": nA,
            "top10_supported": hitsA,
            "action_rate": rateA,
            "wilson95": ciA,
            "median_peak": float(ev_a["peak_cell_percentile"].median()),
            "median_window": float(ev_a["median_cell_percentile"].median()),
            "primary_exploiter_n": n_pe,
            "primary_exploiter_hits": hits_pe,
            "primary_exploiter_rate": rate_pe,
            "space_creator_n": n_sc,
            "space_creator_hits": hits_sc,
            "space_creator_rate": rate_sc,
        },
        "B": {
            "cases": 7,
            "evaluable_actions": nB,
            "top10_supported": hitsB,
            "action_rate": rateB,
            "wilson95": ciB,
        },
    }

    if cases_df is not None:
        c_a = cases_df[cases_df["evidence_strength"] == "A"]
        out["A"]["case_support_rate"] = float((c_a["n_top10_supported"] > 0).mean())
        if "NULL_WINDOW_HIT_RATE" in c_a.columns:
            out["A"]["null_window_background_rate"] = float(c_a["NULL_WINDOW_HIT_RATE"].median())

    return out


# Compatibility alias
evaluate_gold20 = evaluate_tactical_recovery


def evaluate_ablation(ablation_df: pd.DataFrame) -> dict[str, Any]:
    """Evaluate residual-weight ablation: SOG vs PCG (EXP024)."""
    df = ablation_df[ablation_df["evidence_strength"] == "A"].copy()
    nA = len(df)
    df["SOG_TOP10"] = df["SOG_TOP10"].astype(int)
    df["PCG_TOP10"] = df["PCG_TOP10"].astype(int)
    sog_hits = int(df["SOG_TOP10"].sum())
    pcg_hits = int(df["PCG_TOP10"].sum())
    sog_rate = sog_hits / nA
    pcg_rate = pcg_hits / nA
    delta = sog_rate - pcg_rate

    # Paired case bootstrap (1,000 resamples)
    rng = np.random.default_rng(20260928)
    cases = df["case_id"].unique()
    case_diffs = {c: float((df[df["case_id"] == c]["SOG_TOP10"] - df[df["case_id"] == c]["PCG_TOP10"]).sum()) for c in cases}
    case_counts = {c: int(len(df[df["case_id"] == c])) for c in cases}
    diffs = []
    for _ in range(1000):
        boot_cases = rng.choice(cases, size=len(cases), replace=True)
        tot_diff = sum(case_diffs[c] for c in boot_cases)
        tot_n = sum(case_counts[c] for c in boot_cases)
        diffs.append(tot_diff / tot_n)
    ci_delta = (float(np.quantile(diffs, 0.025)), float(np.quantile(diffs, 0.975)))

    return {
        "n_evaluable": nA,
        "sog_hits": sog_hits,
        "sog_rate": sog_rate,
        "pcg_hits": pcg_hits,
        "pcg_rate": pcg_rate,
        "delta_pp": float(delta),
        "bootstrap_95_ci": ci_delta,
        "median_peak_sog": float(df["SOG_peak"].median()),
        "median_peak_pcg": float(df["PCG_peak"].median()),
    }


def evaluate_grid_stability(stability_df: pd.DataFrame) -> dict[str, Any]:
    """Evaluate G0 (50x32) vs G1 (100x64) grid rank convergence (EXP026A)."""
    df = stability_df.copy()
    return {
        "n_states": len(df),
        "median_spearman": float(df["spearman"].median()),
        "min_spearman": float(df["spearman"].min()),
        "median_top10_jaccard": float(df["top10_jaccard"].median()),
        "min_top10_jaccard": float(df["top10_jaccard"].min()),
        "best_player_agreement": float(df["best_player_agree"].mean()),
        "top1_agreement": float(df["top1_agree"].mean()),
    }


def evaluate_state_fragility(cap_pairs_df: pd.DataFrame) -> dict[str, Any]:
    """Evaluate state-level fragility and path accessibility on CAP pairs (EXP027)."""
    df = cap_pairs_df.copy()
    n = len(df)

    # Win-share: case > ctrl -> 1.0, case == ctrl -> 0.5, case < ctrl -> 0.0
    def win_share(col_case, col_ctrl):
        c = df[col_case].values
        k = df[col_ctrl].values
        return float(np.mean(np.where(c > k, 1.0, np.where(c == k, 0.5, 0.0))))

    ws_sog = win_share("F_SOG_case", "F_SOG_ctrl")
    ws_pa = win_share("F_PA_case", "F_PA_ctrl")
    ws_rad = win_share("F_RAD_case", "F_RAD_ctrl")

    # Identical ordering between PA and RADIAL
    pa_correct = df["correct_PA"].values
    rad_correct = df["correct_RAD"].values
    agree_pa_rad = int(np.sum(pa_correct == rad_correct))

    return {
        "n_pairs": n,
        "win_share_F_SOG": ws_sog,
        "win_share_F_PA": ws_pa,
        "win_share_F_RADIAL": ws_rad,
        "delta_PA_RADIAL": float(ws_pa - ws_rad),
        "delta_PA_SOG": float(ws_pa - ws_sog),
        "agree_pa_rad_count": agree_pa_rad,
        "verdict": "DISTANCE_EFFECT_ONLY" if abs(ws_pa - ws_rad) < 1e-6 else "UNKNOWN",
    }


def exact_permutation_auc(
    scores: list[float] | np.ndarray,
    is_vulnerable: list[bool] | np.ndarray,
) -> dict[str, Any]:
    """Exact small-sample label-permutation test for AUC (Mann-Whitney U)."""
    y = np.asarray(is_vulnerable, dtype=bool)
    x = np.asarray(scores, dtype=np.float64)
    n_v = int(np.sum(y))
    n_r = int(np.sum(~y))
    N = len(y)

    if n_v == 0 or n_r == 0:
        return {"auc": float("nan"), "exact_p": float("nan")}

    v_scores = x[y]
    r_scores = x[~y]

    # Observed AUC: P(v > r) + 0.5 * P(v == r)
    comparisons = [
        1.0 if v > r else (0.5 if v == r else 0.0)
        for v in v_scores
        for r in r_scores
    ]
    obs_auc = float(np.mean(comparisons))

    # Exact permutation over all C(N, n_r) allocations
    all_indices = list(range(N))
    null_aucs = []
    for r_comb in itertools.combinations(all_indices, n_r):
        r_set = set(r_comb)
        v_idx = [i for i in all_indices if i not in r_set]
        null_v = x[v_idx]
        null_r = x[list(r_comb)]
        comps = [
            1.0 if v > r else (0.5 if v == r else 0.0)
            for v in null_v
            for r in null_r
        ]
        null_aucs.append(float(np.mean(comps)))

    # One-sided exact p-value: P(null >= obs)
    exact_p = float(np.mean(np.array(null_aucs) >= obs_auc))

    return {
        "n_states": N,
        "n_vulnerable": n_v,
        "n_robust": n_r,
        "observed_auc": obs_auc,
        "exact_one_sided_p": exact_p,
        "n_permutations": len(null_aucs),
        "vulnerable_median": float(np.median(v_scores)),
        "robust_median": float(np.median(r_scores)),
    }
