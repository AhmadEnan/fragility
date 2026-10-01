# Fragility Score

Mapping counterfactual openings in soccer defenses.

[![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/AhmadEnan/fragility/blob/main/notebooks/reproduce_ssac27.ipynb)
[![Tests](https://github.com/AhmadEnan/fragility/actions/workflows/tests.yml/badge.svg)](https://github.com/AhmadEnan/fragility/actions/workflows/tests.yml)
[![Code license: MIT](https://img.shields.io/badge/Code%20license-MIT-blue.svg)](LICENSE)

Reproduction package for the SSAC 2027 soccer abstract using PFF FC's 2022 World Cup data. Structural Opening Gain (SOG) scores and ranks hypothetical player movements by the openings they create in a fixed defensive configuration.

## Reproduce the figures

Open the Colab notebook above and select **Runtime > Run all**. It recomputes classifier scores, checks the abstract statistics and displays both submission figures. No raw-data download, credentials or GPU are required.

For local execution, use Python 3.12 or newer:

```bash
python -m pip install -r requirements-reproduce.txt -e ".[test]"
python tests/verify_notebook.py
python -m pytest
```

## Reported results

The comparison adds SOG landscape features to an observed-context baseline classifier.

| Evaluation | Matches | States | Baseline | With SOG landscape features |
|---|---:|---:|---:|---:|
| Held-out test: average precision | 16 | 38,751 | 0.0482 | 0.0598 |
| Held-out test: events retrieved | 16 | 38,751 | 170 / 694 | 220 / 694 |
| Figure 2 development comparison: events retrieved | 16 | 38,035 | 195 / 752 | 245 / 752 |

Event retrieval uses the same top 10% review budget. The Figure 2 comparison uses development matches. Across 20 documented tactical actions, SOG recovers 13 versus 11 for plain control gain; pre-release recovery ties at 10 each. Centered velocities include subsequent positions, so evaluation is retrospective.

## Data and reference code

The notebook uses derived features, outcome labels, event links and computed control fields. Raw PFF files are excluded. The [data-access guide](DATA_ACCESS.md) explains how to request the underlying dataset from Gradient Sports.

The repo includes the original preprocessing and feature functions, a [runnable tracking feature extractor](src/fragility/extract_features.py), and the original [comparator extraction functions](reference/exp032_comparators.py) for reference. The complete raw-event qualification pipeline is outside this compact package.

- [Reproduction details](REPRODUCIBILITY.md)
- [Code provenance](CODE_PROVENANCE.md)
- [Abstract claims](ABSTRACT_CLAIMS.md)
- [Verification record](RELEASE_AUDIT.md)

The MIT license covers code only. See the data-access guide for the status of derived-data sharing terms.
