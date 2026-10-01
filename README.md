# Fragility Score

**Mapping counterfactual openings in soccer defenses.**

[![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/AhmadEnan/fragility/blob/ssac27-abstract-v1.1.0/notebooks/reproduce_ssac27.ipynb)
[![Code license: MIT](https://img.shields.io/badge/Code%20license-MIT-blue.svg)](LICENSE)

An organized defense can still offer an attacker a useful movement nearby. **Structural Opening Gain (SOG)** makes those opportunities visible: it scores small hypothetical movements, holds the other players fixed, and ranks the resulting gains in attacking control. This deterministic scoring algorithm has no learned scoring parameters.

This repository accompanies the **SSAC 2027 abstract** and includes the source behind scoring, cohort construction, event qualification, comparator extraction, classifier analysis and documented-action recovery. The [exact abstract](docs/submission/ABSTRACT.md) and [figure captions](docs/submission/FIGURE_CAPTIONS.md) are included.

## Reproduce the submission

Open the Colab notebook and select **Runtime → Run all**. It verifies source and input integrity, independently refits the classifiers, recomputes results and tactical recovery, and displays both figures. It uses permitted derived inputs; no raw-data download, credentials or GPU are needed.

Locally, with Python 3.12 or newer:

```bash
python -m pip install -r requirements-reproduce.txt -e ".[test]"
python tests/verify_notebook.py
```

For reconstruction from authorized provider data, follow the [raw-data instructions](REPRODUCIBILITY.md#reconstruction-from-authorized-provider-data). That route runs independently of the original research repository. Raw tracking stays on the reviewer's computer.

## What the evidence shows

The opening landscape and its alignment with player movement add information to an observed-context classifier for **retrospective tactical review**.

| Evaluation | Common review budget | Observed-context baseline | Baseline + SOG landscape and alignment |
|---|---|---:|---:|
| Held-out: 16 matches, 38,751 situations | Top 10% of situations | 170 / 694 events | **220 / 694 events** |
| Held-out average precision | Same situations | 0.0482 | **0.0598** |
| Figure 2: 16 development matches, 38,035 situations | Top 10% of situations | 195 / 752 events | **245 / 752 events** |

The held-out increase is **29.4% more distinct qualified penetrations** at the same review budget. Figure 2 compares SOG with EPV at the ball, EPV-weighted control, adapted OBSO and dangerous accessible space on the same development cohort.

Separately, 13 externally documented tactical sequences provide 20 evaluable player–direction actions. SOG recovers **13/20**, compared with **11/20** for plain pitch-control gain. Pre-release recovery is 10/20 each; the two additional SOG recoveries occur after release. The case-bootstrap interval for the difference is 0–24 percentage points.

![Review utility on the common development cohort](results/figures/FIGURE_2_REVIEW_UTILITY.png)

The scalar SOG summary alone adds essentially no held-out discrimination. The contribution is the **action landscape and movement alignment**. Centered velocities include subsequent positions, so these results support retrospective retrieval, without establishing live forecasting, causal movement effects or a universal defensive-quality scale.

## Where to look

| Reviewer question | Source |
|---|---|
| What does SOG compute? | [Method and features](METHODS.md), [frozen solver](src/fragility/fast_sog.py) |
| How are situations and successful penetrations selected? | [Cohort driver](src/fragility/raw_pipeline.py), [CAP qualification](src/fragility/raw_cap.py) |
| How are Figure 2 comparators calculated? | [Comparator extraction](src/fragility/comparators.py), [settings](configs/literature_benchmark.json) |
| How are documented actions recovered? | [Ranking and recovery](src/fragility/tactical.py), [frame evidence](results/reproduced/tactical_frame_evidence.parquet) |
| How do raw features connect to released rows? | [Export bridge](src/fragility/export_inputs.py), [row identities](data/identity/row_identity.parquet) |
| What was independently checked? | [Verification](RELEASE_AUDIT.md), [source provenance](CODE_PROVENANCE.md) |

The [data-access guide](DATA_ACCESS.md) explains provider access and sharing. MIT covers project code; [third-party notices](THIRD_PARTY_NOTICES.md) cover external methods and the EPV asset. No GitHub Actions test workflows are configured.
