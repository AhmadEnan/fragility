# Data

This directory contains benchmark data used to evaluate defensive fragility:

- `validation/`: Independent tactical annotations and citations (`tactical_cases.csv`, `tactical_actions.csv`, `tactical_sources.csv`).
- `derived/`: Precomputed metric tables (`action_recovery.csv`, `case_summary.csv`, `residual_ablation.csv`, `grid_stability.csv`, `counterattack_pairs.csv`) used to run the reproduction notebook without access to commercial tracking data.

Raw optical tracking data from PFF FC are not distributed here under the dataset terms. See [DATA_ACCESS.md](../DATA_ACCESS.md) for instructions on using licensed tracking files.
