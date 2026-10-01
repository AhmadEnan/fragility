# Fragility Score: Mapping Counterfactual Openings in Soccer Defenses

Code and derived inputs for the SSAC 2027 abstract.

[Run in Colab](https://colab.research.google.com/github/AhmadEnan/fragility/blob/main/notebooks/reproduce_ssac27.ipynb)

Choose **Runtime > Run all**. The notebook recomputes classifier scores, verifies the abstract results and creates both submission figures. No PFF download, credentials or GPU are needed.

For local runs, use Python 3.12 or newer:

```bash
python -m pip install -r requirements-reproduce.txt -e ".[test]"
python tests/verify_notebook.py
python -m pytest
```

| Evaluation | Matches | States | Result |
|---|---:|---:|---|
| Held-out test | 16 | 38,751 | AP 0.0482 to 0.0598; 170 to 220 retrieved events |
| Figure 2, development comparison | 16 | 38,035 | 195 to 245 retrieved events |

SOG recovers 13/20 documented tactical actions versus 11/20 for plain control gain. Pre-release recovery ties at 10/20. Centered velocities include subsequent positions, so evaluation is retrospective.

Public reproduction starts from derived features and computed control fields. Raw PFF files are excluded. The [tracking feature extractor](src/fragility/extract_features.py) is included for reference and licensed-data checks. See [data access](DATA_ACCESS.md), [reproduction](REPRODUCIBILITY.md) and [verification](RELEASE_AUDIT.md). The MIT license covers code only.

The package is verified in fresh Windows and Linux kernels. See [data access](DATA_ACCESS.md) for provider terms and [verification](RELEASE_AUDIT.md) for the scope of the checks.
