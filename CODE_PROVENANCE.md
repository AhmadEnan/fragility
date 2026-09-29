# Code & Data Provenance

This document records the exact lineage, source commits, and experiment provenance for all code and derived data in this repository.

---

## 1. Engine & Library Lineage

The canonical research implementation was developed and frozen in the primary research repository across experiments `EXP020` through `EXP028`. The canonical engine configuration is anchored at commit **`db10578`**.

| Public Path (`src/fragility/`) | Original Internal Path | Canonical Commit | Why Required | Copied or Refactored | Parity Test Used |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `config.py` | `src/sog/config.py` | `db10578` | Encodes frozen canonical parameters (50x32 grid, 8 directions, 3 radii, 0.5 m collision, Law 11 offside, top 10% reducer). | Refactored into standalone frozen dataclass | `tests/test_sog_unit.py::test_grid_geometry` |
| `pitch_control.py` | `src/obso/ppcf.py` | `db10578` | Analytical continuous acceleration-cruise kinematics ($v_{\max}=5.0, a_{\max}=7.0$), exponential PPCF integration. | Refactored for clean NumPy vectorization | `tests/test_sog_unit.py::test_tti_kinematics`, `test_score_state_execution` |
| `pff.py` | `src/fragility/pff.py` & `sfa_common.py` | `db10578` | Coordinate normalization (+x attack), Law 11 offside line, carrier exclusion ($d \le 2.0\text{ m}$), tracking state loader. | Refactored for minimal dependencies | `tests/test_sog_unit.py::test_offside_line_and_status`, `test_carrier_exclusion` |
| `sog.py` | `scripts/exp020_.../rc_common.py` | `db10578` | Counterfactual perturbation generator (24 actions/player), boundary/collision/offside-switch filters, SOG scoring, cell aggregation. | Refactored for clean modular API | `tests/test_parity.py::test_sog_state_numerical_parity`, `tests/test_sog_unit.py` |
| `validation.py` | `scripts/exp023_.../` & `scripts/exp027_.../` | `db10578` | Statistical metrics: Wilson 95% CI, case bootstrap, Spearman $\rho$, Jaccard overlap, CAP win-shares, permutation AUC. | Refactored into unified validation library | `tests/test_parity.py::test_gold20_claim_c01_and_c02_parity`, `test_ablation_claim_c03_parity`, etc. |
| `figures.py` | `scripts/res0_case_visuals/` | `db10578` | Automated regeneration of publication-ready Figures 1 and 2 directly from data tables. | Refactored for clean matplotlib styling | `notebooks/reproduce_ssac27.ipynb` Cell 9 visual generation |
| `__init__.py` | Clean public export | `db10578` | Exposes unified public API (`SOGConfig`, `TrackingState`, `score_state`, `evaluate_*`). | New | All package imports across test suite |

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
