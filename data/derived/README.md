# Derived inputs

| Files | Contents |
|---|---|
| `train_features.parquet` | Normalized development inputs for refitting held-out models |
| `dev_features.parquet` | Common Figure 2 cohort, normalized inputs and original fold assignments |
| `test_features.parquet` | Normalized held-out inputs |
| `models.json` | Saved model parameters in normalized units and recovered development fold parameters |
| `*_predictions.parquet` | Original scores for verification, labels, anonymous matches and tie order |
| `*_event_links.parquet` | Row-to-event links with anonymous event IDs |
| `tactical_comparison.csv` | Paired recovery and pre-release support flags |
| `figure1_plot.npz` | Computed control fields, raster annotation artwork and compositing corrections |
| `figure1_plot.json` | Illustration provenance and original pixel hash |
| `manifest.json` | SHA-256 hashes for all inputs |

Feature values are dimensionless. Row order, anonymous match groups and tie ordering preserve the original bootstrap sampling and review selection. See [data access](../../DATA_ACCESS.md) for sharing terms.
