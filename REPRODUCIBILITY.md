# SSAC 2027 Reproducibility Guide

This guide describes how to replicate all findings, tables, and figures from the MIT Sloan Sports Analytics Conference 2027 submission: *"One Meter from Trouble: Counterfactual Defensive Fragility from Player Tracking"*.

---

## 1. System Requirements

- **Operating System:** Linux (Ubuntu 22.04+), macOS (12+), or Windows (10/11).
- **Python Version:** Python 3.10, 3.11, 3.12, or 3.13.
- **Hardware:** Standard consumer CPU (Intel i5/AMD Ryzen 5 or Apple Silicon). No GPU or specialized accelerator is required.
- **Memory:** Minimum 4 GB RAM.
- **Disk Space:** ~50 MB for the repository, environment, and derived tables.

---

## 2. Fast 60-Second Reproduction

To reproduce all published claims from derived tables and regenerate publication figures:

```bash
# 1. Clone repository
git clone https://github.com/AhmadEnan/fragility.git
cd fragility

# 2. Create virtual environment
python -m venv .venv
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# 3. Install in editable mode
pip install -e .

# 4. Run full test suite (unit tests + claim parity assertions)
python -m pytest tests/ -v
```

Execution takes less than 5 seconds for the parity assertions and ~35 seconds for the synthetic state end-to-end simulation.

---

## 3. Interactive Reproduction (Colab & Jupyter)

The repository contains exactly one self-contained, lightweight reproduction notebook:
`notebooks/reproduce_ssac27.ipynb`

### Running Locally
```bash
pip install jupyter
jupyter notebook notebooks/reproduce_ssac27.ipynb
```

### Running on Google Colab
1. Open [Google Colab](https://colab.research.google.com/).
2. Select **File > Open Notebook > GitHub** and enter the repository URL.
3. Select `notebooks/reproduce_ssac27.ipynb`.
4. Run all 10 cells sequentially (`Runtime > Run all`).

The notebook executes within 10 seconds, displays all claim recovery percentages, regenerates the two abstract figures in `results/figures/`, and validates against `results/expected_results.json`.

---

## 4. Execution Modes

The codebase supports two distinct operational modes:

| Mode | Data Prerequisite | Target Artifacts | Expected Runtime |
| :--- | :--- | :--- | :--- |
| **`MODE = "public"`** (Default) | Public repository only | Re-evaluates all 6 claims from vetted tables in `data/derived/` | ~2 seconds |
| **`MODE = "full"`** | Licensed PFF 2022 World Cup optical tracking files (`PFF_DATA_ROOT`) | Recomputes raw continuous PPCF integrals, 24 perturbations per attacker, offside checks, and tail aggregations from raw trajectories | ~4–8 hours across 20 matches |

---

## 5. Numerical Tolerances & Random Seeds

- **Paired Case Bootstrap (EXP024):**
  - Resamples: 1,000 paired case iterations.
  - Seed: `20260928` (`numpy.random.default_rng(20260928)`).
- **Direction Quantization:**
  - Angles rounded to 6 decimal places (`round(deg, 6)`) to eliminate floating-point boundary split near 225° / 315°.
- **Numerical Parity Tolerances (`tests/test_parity.py`):**
  - Action / space-creator hit rates: Exact or `atol=1e-5`.
  - Spearman rank correlation: `atol=1e-4`.
  - Win-shares and delta metrics: `atol=1e-5`.
