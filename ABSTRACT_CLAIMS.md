# SSAC 2027 Abstract Claims & Verification Matrix

This document maps every empirical and scientific claim in the conference abstract to its canonical experiment, originating commit, derived artifact, and exact numerical reproduction value.

---

## Claims Summary Table

| Claim ID | Claim Summary | Experiment / Commit | Primary Metric | Canonical Value | Reproduction Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **C01** | Gold-20 Tactical Action Recovery | `EXP023` / `db10578` | Bank A Action Recovery Rate | **65.0%** (13/20 actions) | Verified Exact |
| **C02** | Space-Creator vs Exploiter Recovery | `EXP023` / `db10578` | Space-Creator Recovery Rate | **100.0%** (5/5 actions) | Verified Exact |
| **C03** | Residual Weighting Ablation ($\Delta C$) | `EXP024` / `c5afd6f` | Incremental Hit Rate Delta | **+10.0 pp** (65.0% vs 55.0%) | Verified Exact |
| **C04** | Discretization Invariance ($50\times 32$) | `EXP026A` / `ea6a9df` | Median Spearman $\rho$ | **0.9998** (Min: 0.9938) | Verified Exact |
| **C05** | Path Accessibility vs Radial Distance | `EXP027` / `0524d91` | Pairwise Difference $\Delta(\text{PA} - \text{RAD})$ | **0.0000** (Win-share 53.12%) | Verified Exact |
| **C06** | Independent Construct Validation | `EXP028` / `db10578` | Full 203-State Solve | *In Progress* (11-state pilot) | Pilot Documented |

---

## Detailed Claim Specifications

### Claim C01: Ground-Truth Tactical Recovery (EXP023)
- **Statement:** Structural Opening Gain (SOG) ranks externally documented tactical movements in its top 10% in 13 out of 20 evaluable actions in Primary Bank A (65.0%).
- **Primary Bank A Metrics:**
  - Evaluated Actions: 20 across 13 tactical benchmark cases.
  - Top-10% Supported: 13 / 20 ($65.0\%$).
  - 95% Wilson Score Confidence Interval: $[43.3\%, 81.9\%]$.
  - Median Peak SOG Percentile: $97.3\%$ (action peak within candidate set).
  - Median Window SOG Percentile: $76.1\%$.
- **Secondary Bank B Metrics:**
  - Evaluated Actions: 9 across 7 secondary cases.
  - Top-10% Supported: 4 / 9 ($44.4\%$).
  - 95% Wilson Score Confidence Interval: $[18.9\%, 73.3\%]$.
- **Reproduction:** `fragility.evaluate_gold20(actions_df, cases_df)` -> Exact match.

---

### Claim C02: Space-Creator / Decoy Differential Recovery (EXP023)
- **Statement:** Space-creator and decoy runs that open channels for teammates without receiving the ball are identified with 100% sensitivity (5/5), whereas primary ball exploiters achieve 53.8% (7/13).
- **Key Metrics:**
  - Space Creators / Decoys: 5 evaluable actions, 5 top-10 supported ($100.0\%$).
  - Primary Exploiters: 13 evaluable actions, 7 top-10 supported ($53.8\%$).
- **Tactical Interpretation:** SOG directly rewards counterfactual opening of space for the attacking unit, capturing off-ball decoy value that traditional on-ball receiving metrics miss.
- **Reproduction:** `fragility.evaluate_gold20(actions_df)` -> Exact match.

---

### Claim C03: Incremental Residual Weighting Ablation (EXP024)
- **Statement:** The residual space term $(1 - C_0) \max(\Delta C, 0)$, which discounts already-controlled pitch regions and prioritizes contested or defensive space, provides an incremental +10.0 percentage points of recovery over plain Pitch Control Gain (PCG).
- **Key Metrics:**
  - SOG Top-10% Hit Rate: 13 / 20 ($65.0\%$).
  - PCG Top-10% Hit Rate: 11 / 20 ($55.0\%$).
  - Incremental Gain ($\Delta_{\text{pp}}$): $+10.0\text{ percentage points}$.
  - Paired Case Bootstrap 95% CI (1,000 resamples): $[0.0\%, 23.5\%]$.
  - Median Peak Percentile: SOG $97.3\%$ vs PCG $93.7\%$.
- **Reproduction:** `fragility.evaluate_ablation(ablation_df)` -> Exact match.

---

### Claim C04: Grid Discretization Invariance & Numerical Convergence (EXP026A)
- **Statement:** SOG action rankings are numerically converged at the canonical $50 \times 32$ grid ($G_0$, 1,600 cells) relative to a $4\times$ finer $100 \times 64$ grid ($G_1$, 6,400 cells), demonstrating that findings are not artifacts of pitch discretization.
- **Key Metrics across 36 Defensive States (7,968 total evaluated actions):**
  - Median Action Spearman Rank Correlation: $\rho = 0.9998$ (Minimum $\rho = 0.9938$).
  - Median Top-10% Action Jaccard Similarity: $1.0000$ (Minimum Jaccard: $0.9130$).
  - Best-Player Identification Agreement: $100.0\%$ (36 / 36 states agree on the most dangerous attacker).
  - Top-1 Action Direction Match: $97.2\%$ (35 / 36 states agree on the exact optimal perturbation vector).
  - Documented Top-10% Status Changes: $0$ (zero actions switch from supported to unsupported).
- **Reproduction:** `fragility.evaluate_grid_stability(stability_df)` -> Exact match.

---

### Claim C05: State-Level Fragility & Path Accessibility on CAP Matched Pairs (EXP027)
- **Statement:** On 32 matched pairs from the Counter-Attack Phase (CAP) dataset, angular Path Accessibility (PA) offers zero incremental discrimination over isotropic Radial Distance (RADIAL), establishing that macro defensive fragility is governed by basic spatial separation rather than complex angular corridors.
- **Key Metrics across 32 Matched Pairs:**
  - Win-Share $F_{\text{SOG}}$: $43.75\%$ (14 / 32 pairs).
  - Win-Share $F_{\text{PA}}$: $53.12\%$ (17 / 32 pairs).
  - Win-Share $F_{\text{RADIAL}}$: $53.12\%$ (17 / 32 pairs).
  - Pairwise Difference $\Delta(F_{\text{PA}} - F_{\text{RADIAL}})$: $0.0000$ (30 / 32 pairs produce identical rank ordering).
  - Scientific Verdict: `DISTANCE_EFFECT_ONLY`.
- **Reproduction:** `fragility.evaluate_state_fragility(cap_pairs_df)` -> Exact match.

---

### Claim C06: Independent Construct Validation (EXP028)
- **Statement:** Independent construct validation of defensive state fragility ($F_{\text{SOG}}$) across World Cup knockout states, distinguishing structurally vulnerable defensive formations from robust ones.
- **Validation Dataset:**
  - 11 qualitative benchmark states (9 vulnerable, 2 robust) with published tactical citations.
  - 192 background reference states from knockout rounds (total 203 states).
  - Statistical Protocol: Preregistered exact label-permutation test over $\binom{11}{2} = 55$ allocations.
- **Status:** Preregistration and pilot dataset included. Full 203-state solve is computationally intensive and in progress in the internal research pipeline.
