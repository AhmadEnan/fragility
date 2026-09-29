# Reproducibility guide

Instructions for replicating the findings, tables, and figures from *"One Meter from Trouble: Counterfactual Defensive Fragility from Player Tracking"* (SSAC 2027).

---

## 1. Quick reproduction

Clone the repository and run the test suite:

```bash
git clone https://github.com/AhmadEnan/fragility.git
cd fragility
pip install -e ".[dev,test]"
python -m pytest tests/ -v
```

All 13 tests execute in under 45 seconds using synthetic fixtures and derived tables. No external dataset or GPU is required.

---

## 2. Interactive notebook

Open the reproduction notebook in Google Colab or locally in Jupyter:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/AhmadEnan/fragility/blob/main/notebooks/reproduce_ssac27.ipynb)

```bash
jupyter notebook notebooks/reproduce_ssac27.ipynb
```

The notebook executes all claims, regenerates Figures 1 and 2, and validates against `results/expected_results.json` in under 6 seconds.

---

## 3. Execution modes

- **`MODE = "public"` (default):** Evaluates all claims from vetted tables in `data/derived/`. Fast (~2 seconds), requiring no external files.
- **`MODE = "full"`:** Recomputes pitch control integrals, action scoring, and tail aggregations from licensed PFF World Cup tracking data. Set `export PFF_DATA_ROOT="/path/to/FIFA World Cup 2022"`. See [DATA_ACCESS.md](DATA_ACCESS.md).
