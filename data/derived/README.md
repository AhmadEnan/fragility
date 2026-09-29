# Derived data

Precomputed tables used by `notebooks/reproduce_ssac27.ipynb` in public mode. These contain aggregate model outputs and percentiles, with no raw coordinates or tracking trajectories.

| File | Description |
| :--- | :--- |
| `gold20_player_actions.csv` | SOG recovery percentiles for the 46 tactical actions. |
| `gold20_cases_summary.csv` | Case-level recovery summaries for the 20 benchmark cases. |
| `gold20_ablation_comparison.csv` | Paired comparison between SOG and unweighted PCG. |
| `grid_stability_summary.csv` | Resolution convergence metrics ($50 \times 32$ vs $100 \times 64$). |
| `cap_pair_scores.csv` | Fragility scores on 32 counter-attack matched pairs. |
| `manifest.json` | SHA-256 checksums for each file. |
