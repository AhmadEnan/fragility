# Data Access & Licensing

This repository provides two verification pathways to accommodate researchers with and without commercial data access agreements:

1. **Public Mode (`MODE = "public"`)**: Fully reproducible out-of-the-box using shareable, non-restricted derived metric tables and external qualitative tactical annotations. No proprietary files or credentials are required.
2. **Full Mode (`MODE = "full"`)**: End-to-end execution from raw player trajectories and frame sequences for researchers with legitimate PFF FC data licenses.

---

## 1. Raw PFF FC Tracking Data

The raw optical tracking dataset used in this paper covers the 2022 FIFA World Cup (Qatar) and is proprietary to **PFF FC** (formerly Pro Football Focus / FC Python / PFF Soccer).

### Data Restrictions
- Raw player coordinates, velocities, ball trajectories, and per-frame tracking files are governed by restrictive data agreements and **cannot be redistributed** in this public repository.
- No raw tracking coordinates, continuous frame dumps, or serialized raw states are hosted in this repository or its commit history.

### Obtaining Access
Researchers affiliated with academic institutions or professional clubs can apply for research access to the 2022 FIFA World Cup tracking dataset directly through PFF:
- **Provider:** PFF FC (Professional Football Focus)
- **Website:** [https://www.pff.com/](https://www.pff.com/)
- **Contact:** Research & Data Partnerships (`academic-access@pff.com` / `data-inquiries@pff.com`)
- **Dataset Specification:** FIFA World Cup Qatar 2022 Full Match Tracking (25 Hz optical tracking, event-aligned metadata).

---

## 2. Directory Layout for Full Mode

When running in `MODE = "full"`, configure your environment to point to your local licensed copy of the PFF tracking directory:

```bash
export PFF_DATA_ROOT="/path/to/pff/tracking"
```

Expected internal layout:
```text
${PFF_DATA_ROOT}/
├── tracking/
│   ├── 10503.csv       # Match tracking (Argentina vs Mexico)
│   ├── 10507.csv       # Match tracking (Spain vs Germany)
│   ├── 10525.csv       # Match tracking (Argentina vs France)
│   └── ...
└── events/
    ├── 10503_events.csv
    └── ...
```

The pipeline loader (`src/fragility/pff.py`) parses these CSV tables directly, aligns home/away coordinate conventions, applies Law 11 offside line projections, and excludes the ball carrier within 2.0 m.

---

## 3. Included Public Validation & Derived Data

To enable independent verification of all scientific claims without proprietary access, this repository publishes:

1. **`data/validation/`**:
   - `gold20_cases.csv`: Tactical case metadata (match date, teams, tactical mechanism, video timestamp).
   - `gold20_actions.csv`: 46 tactical actions, player roles (space creator vs primary exploiter), and frozen counterfactual directions.
   - `gold20_sources.csv`: 47 public citations (The Athletic, Spielverlagerung, Coaches' Voice, FIFA Training Centre) documenting each movement.
   - `fragility_validation.csv`: 11 unpaired World Cup defensive states (9 vulnerable, 2 robust) with tactical explanations.
   - `fragility_sources.csv`: External tactical literature and video timestamps for state validation.

2. **`data/derived/`**:
   - `gold20_player_actions.csv`: SOG percentiles and Top-10% recovery indicators.
   - `gold20_cases_summary.csv`: Per-case recovery levels and support classifications.
   - `gold20_ablation_comparison.csv`: Paired SOG vs PCG (Pitch Control Gain) comparisons for residual weighting ablation.
   - `grid_stability_summary.csv`: Cell-by-cell and action-by-action convergence metrics comparing G0 ($50 \times 32$) and G1 ($100 \times 64$).
   - `cap_pair_scores.csv`: 32 clean matched Counter-Attack Phase (CAP) pairs comparing SOG, Path Accessibility (PA), and Radial Distance (RADIAL).
   - `manifest.json`: Cryptographic SHA-256 checksums and provenance records for every public artifact.

3. **`tests/fixtures/synthetic_state.json`**:
   - A fully synthetic, physically realistic 22-player tracking frame that allows complete unit testing of SOG kinematics, pitch control numerical integration, offside filters, and tail reducers without any proprietary data.
