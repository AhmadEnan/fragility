# One Meter from Trouble: Counterfactual Defensive Fragility from Player Tracking

[![Tests and Parity Verification](https://github.com/AhmadEnan/fragility/actions/workflows/tests.yml/badge.svg)](https://github.com/AhmadEnan/fragility/actions/workflows/tests.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/AhmadEnan/fragility/blob/main/notebooks/reproduce_ssac27.ipynb)

**Official Public Reproduction Package** for the paper:  
*“One Meter from Trouble: Counterfactual Defensive Fragility from Player Tracking”*  
**MIT Sloan Sports Analytics Conference 2027 (SSAC27) — Soccer Track**

---

## Executive Summary

Modern football analytics evaluates spatial dominance via pitch control models, but these models describe only the *observed* configuration of players. They cannot directly measure how precarious a defensive formation is to minute attacking adjustments.

This repository provides **`fragility`**, an open-source Python library implementing **Structural Opening Gain (SOG)**. By subjecting every off-ball attacker to an exhaustive grid of localized counterfactual perturbations ($\pm 0.5\text{ m}, \pm 1.0\text{ m}, \pm 1.5\text{ m}$ in 8 compass directions), SOG quantifies the defensive space an attacker *could* unlock if they took a single step into an unmonitored lane. Aggregating the tail (top 10%) of these counterfactual gains yields a scalar measure of macro defensive fragility ($F_{\text{SOG}}$).

---

## Published Abstract Claims & Parity Status

All empirical claims from the conference abstract reproduce exactly from the public derived tables:

| Claim ID | Paper Claim | Empirical Benchmark | Metric | Expected Result | Reproduction |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **C01** | Ground-Truth Action Recovery | Gold-20 Bank A (13 cases) | Top-10% Action Recovery | **65.0%** (13/20 actions) | `[PASS] 65.0%` (95% CI: 43.3–81.9%) |
| **C02** | Space-Creator vs Exploiter | Gold-20 Bank A (13 cases) | Decoy / Space-Creator Hit Rate | **100.0%** (5/5 actions) | `[PASS] 100.0%` (Exploiters: 53.8%) |
| **C03** | Residual Weighting Ablation | Gold-20 Bank A (13 cases) | Incremental Gain over PCG | **+10.0 pp** (65.0% vs 55.0%) | `[PASS] +10.0 pp` (95% CI: 0.0–23.5%) |
| **C04** | Discretization Invariance | 36 states ($G_0$ vs $G_1$) | Rank Agreement ($50\times 32$ vs $100\times 64$) | **$\rho = 0.9998$**, Best-Player: **100%** | `[PASS] \rho = 0.9998`, Agree: 100% |
| **C05** | State Fragility on Matched Pairs | 32 CAP Matched Pairs | Angular Path Accessibility vs Radial | **$\Delta(\text{PA} - \text{RAD}) = 0.000$** | `[PASS] \Delta = 0.0000`, Verdict: DISTANCE_ONLY |
| **C06** | Independent Construct Validation | 11 qualitative states (9 vuln, 2 robust) | Pilot Cohort Evaluation | *In Progress* (Full 203-state solve) | `[PASS]` Preregistered pilot documented |

For full experimental provenance and canonical git commits, see [ABSTRACT_CLAIMS.md](ABSTRACT_CLAIMS.md) and [CODE_PROVENANCE.md](CODE_PROVENANCE.md).

---

## 60-Second Quickstart

### 1. Installation

```bash
git clone https://github.com/AhmadEnan/fragility.git
cd fragility
python -m pip install -e .
```

### 2. Verify Everything with Pytest

```bash
# Run unit tests on synthetic 22-player fixture + claim parity tests
python -m pytest tests/ -v
```

All 11 tests execute in under 45 seconds:
- 7 unit tests verifying pitch control integration, time-to-intercept kinematics, Law 11 offside projection, carrier exclusion, and tail reduction on a clean synthetic 22-player frame.
- 4 parity tests asserting exact reproduction of Claims C01, C02, C03, C04, and C05.

### 3. One-Click Colab Reproduction

Run the self-contained reproduction notebook in Google Colab with zero local setup:
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ssac2027/fragility/blob/main/notebooks/reproduce_ssac27.ipynb)

The notebook executes in ~5 seconds, regenerates the two abstract figures in `results/figures/`, and validates against `results/expected_results.json`.

---

## Mathematical Formulation

### 1. Potential Pitch Control Field (PPCF)
For player $i$ with current position $\mathbf{p}_i$ and velocity $\mathbf{v}_i$, arrival time $t_i(\mathbf{r})$ to target location $\mathbf{r}$ follows continuous acceleration-cruise kinematics:
$$t_{\text{cruise}} = \frac{d_i - s_{\text{accel}}}{v_{\max}} \quad \text{if } d_i > s_{\text{accel}}$$
Individual probability of control is integrated over time horizon $T = 10.0\text{ s}$ with reaction time $\tau = 0.54\text{ s}$ and control rate $\lambda = 3.99\text{ s}^{-1}$.

### 2. Structural Opening Gain (SOG)
For an off-ball attacking player $k$, candidate perturbation $\mathbf{u} = (\Delta x, \Delta y)$ with radius $\rho = \|\mathbf{u}\|$ produces counterfactual pitch control field $C_{\mathbf{u}}(\mathbf{r})$. The localized gain is weighted by the *uncontrolled* baseline density $(1 - C_0(\mathbf{r}))$:
$$\text{SOG}_k(\mathbf{u}) = \sum_{\mathbf{r} \in \text{Pitch}} \big(1 - C_0(\mathbf{r})\big) \max\big(C_{\mathbf{u}}(\mathbf{r}) - C_0(\mathbf{r}), 0\big) - \text{cost}(\rho)$$
where $\text{cost}(\rho) = \rho / 1.0\text{ m}$.

### 3. Defensive Fragility Reducer
Macro state fragility $F_{\text{SOG}}$ is the arithmetic mean of the top 10% highest-scoring valid counterfactual actions across all attacking players:
$$F_{\text{SOG}} = \frac{1}{|K_{\text{top10}}|} \sum_{a \in K_{\text{top10}}} \text{SOG}(a)$$

---

## Repository Structure

```text
fragility/
├── .github/workflows/
│   └── tests.yml                 # Cross-platform CI (Ubuntu, Windows / Python 3.10-3.13)
├── data/
│   ├── derived/                  # Vetted non-proprietary derived tables
│   │   ├── gold20_player_actions.csv
│   │   ├── gold20_cases_summary.csv
│   │   ├── gold20_ablation_comparison.csv
│   │   ├── grid_stability_summary.csv
│   │   ├── cap_pair_scores.csv
│   │   └── manifest.json         # SHA-256 integrity checksums
│   └── validation/               # Independent tactical annotations & citations
│       ├── gold20_cases.csv
│       ├── gold20_actions.csv
│       ├── gold20_sources.csv    # 47 published tactical sources
│       ├── fragility_validation.csv
│       └── fragility_sources.csv
├── notebooks/
│   └── reproduce_ssac27.ipynb    # Single Colab notebook (10 cells, <=150 LOC)
├── results/
│   ├── figures/                  # Regenerated publication figures
│   │   ├── figure1_gold20_recovery.png
│   │   └── figure2_grid_stability.png
│   └── expected_results.json     # Canonical claim baseline values
├── src/fragility/                # Standalone Python library
│   ├── __init__.py
│   ├── config.py                 # Frozen SOGConfig parameters
│   ├── pitch_control.py          # Vectorized PPCF & kinematics
│   ├── pff.py                    # Tracking state & Law 11 offside projection
│   ├── sog.py                    # Counterfactual perturbations & tail reducer
│   ├── validation.py             # Statistical tests (Wilson CI, bootstrap, permutation)
│   └── figures.py                # Publication figure generation
├── tests/
│   ├── fixtures/
│   │   └── synthetic_state.json  # 22-player synthetic tracking state
│   ├── test_parity.py            # Exact assertion parity tests for Claims C01-C05
│   └── test_sog_unit.py          # Physics and rule unit tests
├── ABSTRACT_CLAIMS.md            # Detailed claim matrix and literature references
├── CITATION.cff                  # Citation metadata
├── CODE_PROVENANCE.md            # Engine commit and experiment audit
├── DATA_ACCESS.md                # PFF FC tracking data access guide
├── REPRODUCIBILITY.md            # Step-by-step reproduction guide
├── RELEASE_AUDIT.md              # Privacy, security, and licensing audit
└── pyproject.toml                # Packaging & metadata
```

---

## Dual Execution Modes

1. **`MODE = "public"` (Default)**:
   Loads and evaluates all claims from the verified derived tables in `data/derived/`. Fast (~2 seconds), requiring zero proprietary data or external dependencies.

2. **`MODE = "full"`**:
   For researchers with an official license to the PFF 2022 World Cup optical tracking dataset. Set the environment variable:
   ```bash
   export PFF_DATA_ROOT="/path/to/pff/tracking"
   ```
   The engine will load raw coordinates, calculate continuous PPCF integrals, evaluate all 24 counterfactual actions per player, enforce Law 11 offside boundaries, and aggregate defensive fragility end-to-end.

---

## Citation

If you use this library, methodology, or derived tactical benchmarks in your research, please cite:

```bibtex
@inproceedings{ssac2027fragility,
  title={One Meter from Trouble: Counterfactual Defensive Fragility from Player Tracking},
  author={SSAC 2027 Research Team},
  booktitle={Proceedings of the MIT Sloan Sports Analytics Conference},
  year={2027},
  month={March}
}
```

---

## License

This software and derived data are released under the [MIT License](LICENSE).
Raw tracking trajectories are proprietary to [PFF FC](https://www.pff.com/) and are not included in this repository.