# Data Access & Licensing

This repository provides two verification pathways to accommodate researchers with and without commercial PFF FC data licenses:

1. **Public Mode (`MODE = "public"`)**: Fully reproducible out-of-the-box in < 5 seconds using shareable, non-restricted derived metric tables and external qualitative tactical annotations. No proprietary files or credentials are required.
2. **Full Mode (`MODE = "full"`)**: End-to-end execution directly from the licensed 2022 FIFA World Cup tracking dataset for reviewers and researchers with legitimate PFF commercial access.

---

## 1. Raw PFF FC Tracking Data

The raw optical tracking dataset evaluated in this paper covers the 2022 FIFA World Cup (Qatar) and is proprietary commercial data licensed from **PFF FC** (Professional Football Focus / FC Python / PFF Soccer).

### Data Restrictions
- Raw player optical coordinates, instantaneous velocities, ball trajectories, event JSON records, and per-frame tracking feeds are strictly governed by commercial data agreements and **cannot be redistributed** in this public repository.
- No raw tracking coordinates, continuous frame dumps, or serialized raw states are hosted in this repository or in its commit history.
- The repository and reproduction notebooks execute entirely locally or in Google Colab memory; they **never upload, transmit, or re-host** any proprietary PFF data.

### Commercial Access Instructions
Researchers affiliated with academic institutions, federations, or professional clubs must obtain the underlying dataset directly from PFF FC:
- **Provider:** PFF FC (Professional Football Focus Soccer)
- **Official Portal:** [https://www.pff.com/](https://www.pff.com/)
- **Contact:** Research & Academic Partnerships (`academic-access@pff.com` / `data-inquiries@pff.com`)
- **Dataset Title:** *FIFA World Cup Qatar 2022 Full Match Tracking Data* (29.97 / 25 Hz optical tracking with synchronized event metadata and roster mappings).
- *[Author Note: Insert any institutional agreement number or verified direct PFF portal URL prior to final archival release.]*

---

## 2. Directory Layout & Configuration for Full Mode

To run in `MODE = "full"`, configure the environment variable `PFF_DATA_ROOT` to point to your local licensed copy of the PFF FIFA World Cup 2022 dataset:

```bash
export PFF_DATA_ROOT="/path/to/FIFA World Cup 2022"
```

### Expected PFF Dataset Layout
The official PFF World Cup 2022 distribution is organized as follows:

```text
${PFF_DATA_ROOT}/
├── Tracking Data/
│   ├── 10502.jsonl.bz2     # Compressed 25/30 Hz optical tracking frames
│   ├── 10503.jsonl.bz2
│   ├── ...
│   └── 3859.jsonl.bz2
├── Event Data/
│   ├── 10502.json          # Synchronized match events
│   └── ...
├── Metadata/
│   ├── 10502.json          # Match metadata (period clocks, homeTeamStartLeft)
│   └── ...
├── Rosters/
│   ├── 10502.json          # Squad rosters with GK position flags & jersey numbers
│   └── ...
├── competitions.csv
└── players.csv
```

Alternatively, if preprocessed frame cache parquets are available:
```text
${PFF_DATA_ROOT}/
└── frame_cache/
    ├── match_10502_stride8.parquet
    ├── match_10505_stride8.parquet
    └── ...
```

The data loader in `src/fragility/pff.py` automatically detects either layout, normalizes coordinates so the attacking team attacks towards $+x$, identifies goalkeeper jerseys, computes the Law 11 offside line from the second-last defender, and excludes the ball carrier within 2.0 m.

---

## 3. Matches Used in Reproduction

Full end-to-end reproduction does not process the entire 64-match tournament. Only the specific matches and discrete candidate time windows associated with the paper's claims are evaluated in memory:

| Match ID | Match Date | Teams | Claim / Evaluation Role |
| :--- | :--- | :--- | :--- |
| `3813` | 2022-11-21 | England vs Iran | Gold20 Cases: `GOLD010`, `GOLD014` |
| `3821` | 2022-11-23 | Germany vs Japan | Gold20 Case: `GOLD006` |
| `3823` | 2022-11-23 | Belgium vs Canada | Gold20 Case: `GOLD009` |
| `3834` | 2022-11-26 | France vs Denmark | Gold20 Case: `GOLD005` |
| `3840` | 2022-11-28 | Cameroon vs Serbia | Gold20 Case: `GOLD008` |
| `3858` | 2022-12-02 | Serbia vs Switzerland | Gold20 Cases: `GOLD002`, `GOLD003` |
| `10502` | 2022-12-03 | Netherlands vs USA | Gold20 Cases: `GOLD016`, `GOLD017`, `GOLD018` |
| `10505` | 2022-12-04 | England vs Senegal | Gold20 Cases: `GOLD001`, `GOLD013`, `GOLD020` |
| `10511` | 2022-12-09 | Netherlands vs Argentina | Gold20 Case: `GOLD007` |
| `10513` | 2022-12-10 | England vs France | Gold20 Case: `GOLD012` |
| `10514` | 2022-12-13 | Argentina vs Croatia | Gold20 Cases: `GOLD004`, `GOLD019` |
| `10515` | 2022-12-14 | France vs Morocco | Gold20 Case: `GOLD015` |
| `10517` | 2022-12-18 | Argentina vs France | Gold20 Case: `GOLD011` |

---

## 4. Included Public Validation & Derived Data

To enable immediate, independent verification of all scientific claims without requiring proprietary PFF access:

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
   - `grid_stability_summary.csv`: Convergence metrics comparing G0 ($50 \times 32$) and G1 ($100 \times 64$).
   - `cap_pair_scores.csv`: 32 clean matched Counter-Attack Phase pairs comparing SOG, Path Accessibility, and Radial Distance.
   - `manifest.json`: Cryptographic SHA-256 checksums and provenance records.

3. **`tests/fixtures/synthetic_state.json`**:
   - A fully synthetic, physically realistic 22-player tracking frame that enables complete unit testing of SOG kinematics, pitch control numerical integration, offside filters, and tail reducers with zero proprietary dependencies.
