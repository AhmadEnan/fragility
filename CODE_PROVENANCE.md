# Code & Data Provenance

This document records the exact lineage, source commits, and experiment provenance for all code and derived data in this repository.

---

## 1. Engine & Library Lineage

The canonical research implementation was developed and frozen in the primary research repository across experiments `EXP020` through `EXP028`. The canonical engine configuration is anchored at commit **`db10578`**.

| Public Module (`src/fragility/`) | Internal Origin (`research-repo`) | Canonical Commit | Purpose / Scientific Responsibilities |
| :--- | :--- | :--- | :--- |
| `config.py` | `src/sog/config.py` | `db10578` | Frozen numerical constants ($50 \times 32$ grid, 8 directions, 3 radii, 0.5 m collision, Law 11 offside, top 10% reducer). |
| `pitch_control.py` | `src/pitch_control/` | `db10578` | Vectorized analytical PPCF integrator. TTI kinematics with verified continuous acceleration-cruise mechanics ($v_{\max} = 5.0\text{ m/s}, a_{\max} = 7.0\text{ m/s}^2$). |
| `pff.py` | `src/data/pff.py` | `db10578` | Coordinate normalization, Law 11 second-last defender offside plane calculation, carrier exclusion ($d \le 2.0\text{ m}$), and tracking state parsing. |
| `sog.py` | `src/sog/engine.py` | `db10578` | Counterfactual perturbation generator (24 candidate actions/attacker), boundary/collision/offside filtering, cell aggregation, and state fragility reduction $F_{\text{SOG}}$. |
| `validation.py` | `src/sog/analysis/` | `db10578` | Wilson score 95% CI, 1,000-resample paired case bootstrap, Spearman rank correlation, Jaccard overlap, CAP pair win-shares, and exact permutation AUC. |
| `figures.py` | `scripts/` | `db10578` | Publication-ready figure generation for Figure 1 (tactical recovery) and Figure 2 (grid convergence). |
| `__init__.py` | New clean export | `db10578` | Exposes public API: `SOGConfig`, `TrackingState`, `evaluate_*`, `plot_*`. |

---

## 2. Experimental Data Lineage

All data artifacts in `data/derived/` are verbatim extractions from completed canonical experiment runs. None of these files contain raw tracking coordinates or proprietary PFF tracking tables.

| Derived Dataset (`data/derived/`) | Originating Experiment | Canonical Commit | Method / Description |
| :--- | :--- | :--- | :--- |
| `gold20_player_actions.csv` | `EXP_SOG_GOLD20_CONFIRMATION_023` | `db10578` | 46 tactical actions evaluated across 20 tactical cases, with peak cell percentiles and `TOP10_SUPPORTED` flags. |
| `gold20_cases_summary.csv` | `EXP_SOG_GOLD20_CONFIRMATION_023` | `db10578` | Per-case support classifications (strong, support, partial, miss) and background null window rates. |
| `gold20_ablation_comparison.csv` | `EXP_SOG_INCREMENTAL_ABLATION_024` | `c5afd6f` | Paired comparison between SOG (residual weighted $(1 - C_0) \Delta C$) and PCG (pure pitch control gain $\Delta C$) across 46 actions. |
| `grid_stability_summary.csv` | `EXP_SOG_GRID_STEERING_026A` | `ea6a9df` | Numerical convergence metrics across 36 defensive states comparing G0 ($50 \times 32$) to G1 ($100 \times 64$). |
| `cap_pair_scores.csv` | `EXP_SOG_STATE_FRAGILITY_027` | `0524d91` | Pairwise scores for 32 matched Counter-Attack Phase pairs comparing SOG, Path Accessibility ($F_{\text{PA}}$), and Radial Distance ($F_{\text{RAD}}$). |
| `manifest.json` | Public Pipeline Integrity | `current` | Cryptographic SHA-256 checksums, byte counts, and raw PFF isolation flags. |

---

## 3. Qualitative Ground-Truth Data Lineage

All files in `data/validation/` are compiled from independent public tactical sources, external football analyses, and video timestamps:

| Validation File (`data/validation/`) | Originating Protocol | Canonical Commit | Description |
| :--- | :--- | :--- | :--- |
| `gold20_cases.csv` | Gold-20 Ground Truth Registry | `db10578` | 20 tactical benchmark cases from 2022 World Cup matches (13 Primary Bank A, 7 Secondary Bank B). |
| `gold20_actions.csv` | Gold-20 Action Registry | `db10578` | 46 tactical movements categorized by role (`PRIMARY_EXPLOITER` vs `SPACE_CREATOR` / `DECOY`). |
| `gold20_sources.csv` | External Bibliography | `db10578` | 47 published citations (The Athletic, Coaches' Voice, Spielverlagerung, FIFA Training Centre). |
| `fragility_validation.csv` | `EXP_SOG_INDEPENDENT_FRAGILITY_028` | `db10578` | 11 unpaired World Cup states (9 vulnerable, 2 robust) with tactical explanations. |
| `fragility_sources.csv` | `EXP_SOG_INDEPENDENT_FRAGILITY_028` | `db10578` | Tactical literature sources and match timestamps for independent construct validation. |
