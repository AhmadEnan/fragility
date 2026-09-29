# Derived Data Directory & Redistribution Audit

This directory contains frozen, shareable derived research tables that allow reviewers to immediately reproduce all empirical findings and publication figures presented in the SSAC 2027 paper without access to commercial tracking feeds.

---

## 1. PFF-Derived Data Classification Audit

Every table in this directory was subjected to a rigorous data protection audit prior to release. Files containing raw optical tracking, player trajectories, or reversible state reconstructions are strictly excluded from the public repository.

| Filename | Source Experiment | Contains Raw Coordinates? | Contains Player Velocities? | Contains Event Payloads? | Reconstructs Raw State? | Aggregation Level | Redistribution Rationale | Decision |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `gold20_player_actions.csv` | `EXP023` | **NO** | **NO** | **NO** | **NO** | Action scalar percentiles | 1 row per action (46 rows). Contains only scalar SOG percentiles and boolean recovery flags. Mathematically irreversible. | **PUBLIC** |
| `gold20_cases_summary.csv` | `EXP023` | **NO** | **NO** | **NO** | **NO** | Case-level classification | 1 row per case (20 rows). Categorical support levels (`STRONG_CASE_SUPPORT`, `NULL_WINDOW_HIT_RATE`). Irreversible. | **PUBLIC** |
| `gold20_ablation_comparison.csv` | `EXP024` | **NO** | **NO** | **NO** | **NO** | Action ablation pairs | 1 row per evaluable action (29 rows). Contains paired scalar percentiles for SOG vs unweighted PCG. Irreversible. | **PUBLIC** |
| `grid_stability_summary.csv` | `EXP026A` | **NO** | **NO** | **NO** | **NO** | State-level stability summary | 1 row per audit state (36 rows). Contains Spearman $\rho$, Jaccard overlap, and rank agreement metrics. Irreversible. | **PUBLIC** |
| `cap_pair_scores.csv` | `EXP027` | **NO** | **NO** | **NO** | **NO** | Matched pair scores | 1 row per matched pair (32 rows). Scalar state scores ($F_{\text{SOG}}$, $F_{\text{PA}}$, $F_{\text{RAD}}$) and pair win indicators. Irreversible. | **PUBLIC** |
| `manifest.json` | Release Eng | **NO** | **NO** | **NO** | **NO** | Cryptographic metadata | SHA-256 hashes, row counts, and provenance metadata. Zero data content. | **PUBLIC** |

*Policy Rule: Any candidate artifact with uncertain redistributability is excluded by default (`UNCERTAIN => EXCLUDE`). Only high-level scalar summaries are included.*

---

## 2. Dataset Descriptions & Schemas

### 1. `gold20_player_actions.csv` (EXP023)
Contains SOG recovery percentiles for all 46 actions across the 20 Gold benchmark cases.
- `case_id`: Tactical case ID (`GOLD001`–`GOLD020`)
- `player_name`: Name of the documented actor
- `shirt_number`: Shirt number of the player
- `team`: Team name
- `role_in_mechanism`: Tactical role (`PRIMARY_EXPLOITER`, `SPACE_CREATOR`, `SUPPORT_RUNNER`, etc.)
- `evidence_strength`: Evidence grade (`A` = Primary Bank, `B` = Secondary Bank)
- `evaluability`: Evaluability classification
- `frozen_direction_deg`: Documented movement direction sector (0°, 45°, ..., 315°)
- `peak_percentile`: Maximum SOG percentile achieved by the documented player in the documented direction across the candidate window
- `top10_supported`: Boolean flag (`True` if `peak_percentile >= 0.90`)
- `case_rank`: Rank of the action within the candidate window

### 2. `gold20_cases_summary.csv` (EXP023)
Summarizes recovery performance at the case level.
- `case_id`: Tactical case ID
- `evidence_strength`: Case evidence bank (`A` or `B`)
- `evaluable_actions`: Count of directly evaluable actions in the case
- `supported_actions`: Count of actions achieving top-10% recovery (`peak_percentile >= 0.90`)
- `case_classification`: Overall case support status (`STRONG_SUPPORT`, `SUPPORT`, `PARTIAL`, `MISS`)
- `primary_exploiter_top10`: Boolean flag indicating if the primary exploiter was recovered
- `null_window_rate`: Mean top-10% hit rate during baseline/background control periods

### 3. `gold20_ablation_comparison.csv` (EXP024)
Direct paired comparison evaluating the incremental contribution of the $(1 - C_0)$ residual weighting.
- `case_id`: Tactical case ID
- `player_name`: Mover name
- `role_in_mechanism`: Tactical role
- `sog_peak_percentile`: Peak percentile under full residual-weighted SOG
- `pcg_peak_percentile`: Peak percentile under unweighted Positive Control Gain (PCG)
- `sog_top10`: Boolean flag indicating top-10% hit for SOG
- `pcg_top10`: Boolean flag indicating top-10% hit for PCG
- `delta_percentile`: `sog_peak_percentile - pcg_peak_percentile`

### 4. `grid_stability_summary.csv` (EXP026A)
Cell-by-cell and action-by-action convergence metrics comparing G0 ($50 \times 32$, 1,600 cells) against G1 ($100 \times 64$, 6,400 cells) across 36 defensive states.
- `state_id`: Discrete state identifier
- `n_actions`: Total valid counterfactual actions scored in the state
- `spearman_rho`: Spearman rank correlation between G0 and G1 action scores
- `top10_jaccard`: Jaccard similarity coefficient of the top-10% action sets between G0 and G1
- `best_player_agrees`: Boolean flag indicating whether G0 and G1 identify the same top player
- `top1_action_agrees`: Boolean flag indicating whether G0 and G1 identify the exact same top-1 action (player + direction + radius)

### 5. `cap_pair_scores.csv` (EXP027)
Pairwise evaluation across 32 matched Counter-Attack Phase pairs comparing SOG, Path Accessibility ($F_{\text{PA}}$), and Radial Distance ($F_{\text{RAD}}$).
- `pair_id`: Unique identifier for the matched pair
- `case_state_id`: State identifier for the vulnerable/case counter-attack state
- `ctrl_state_id`: State identifier for the matched control/non-vulnerable state
- `F_SOG_case`: $F_{\text{SOG}}$ score for the case state
- `F_SOG_ctrl`: $F_{\text{SOG}}$ score for the control state
- `F_PA_case`: Path accessibility score for the case state
- `F_PA_ctrl`: Path accessibility score for the control state
- `F_RAD_case`: Radial distance score for the case state
- `F_RAD_ctrl`: Radial distance score for the control state
- `win_F_SOG`: Boolean indicator (`F_SOG_case > F_SOG_ctrl`)
- `win_F_PA`: Boolean indicator (`F_PA_case > F_PA_ctrl`)
- `win_F_RAD`: Boolean indicator (`F_RAD_case > F_RAD_ctrl`)
- `agree_PA_RAD`: Boolean indicator (`win_F_PA == win_F_RAD`)

---

## 3. Cryptographic Verification

All files in this directory are verified against `manifest.json`. You can verify dataset integrity using:

```bash
python -c "import hashlib, json; m = json.load(open('data/derived/manifest.json')); [print(k, hashlib.sha256(open('data/derived/' + k, 'rb').read()).hexdigest() == m[k]['sha256']) for k in m]"
```
