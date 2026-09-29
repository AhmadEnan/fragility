# Data Directory Overview

This directory contains qualitative validation registries, external ground-truth tactical benchmarks, and shareable derived metric tables supporting the research submission:

> **One Meter from Trouble: Counterfactual Defensive Fragility from Player Tracking**  
> *MIT Sloan Sports Analytics Conference (SSAC) 2027 — Soccer Track*

---

## Third-Party Data Licensing Notice

- **No Proprietary PFF FC Data:** Commercial optical tracking data from the 2022 FIFA World Cup (Qatar) provided by **PFF FC** are strictly excluded from this repository in accordance with commercial data agreements. No raw frame dumps, player `(x, y)` trajectories, raw velocities, or proprietary JSON/bz2 streams are distributed here or in the commit history.
- **Independent Qualitative Evidence:** All annotations, tactical mechanism descriptions, and video timestamps in `data/validation/` were independently compiled from public broadcast footage, open event feeds (StatsBomb Open Data), and published football analysis literature.
- **Third-Party Terms:** All citations, article titles, quotes, and author credits remain the intellectual property of their respective creators and publishers. See [DATA_ACCESS.md](../DATA_ACCESS.md) for full licensing details and commercial data access instructions.

---

## Directory Layout

```text
data/
├── README.md                      # This file (directory overview & schemas)
├── validation/                    # Independent qualitative & tactical ground-truth
│   ├── gold20_cases.csv           # 20 tactical benchmark cases (Bank A & Bank B)
│   ├── gold20_actions.csv         # 46 documented tactical actions & player roles
│   ├── gold20_sources.csv         # 47 published tactical & timing citations
│   ├── fragility_validation.csv   # 11 independent World Cup validation states
│   └── fragility_sources.csv      # Tactical and video timing sources for validation states
└── derived/                       # Frozen, shareable derived metric tables
    ├── README.md                  # Classification audit & derived dataset documentation
    ├── manifest.json              # Cryptographic SHA-256 hashes & provenance
    ├── gold20_player_actions.csv  # SOG action percentiles & Top-10% recovery indicators
    ├── gold20_cases_summary.csv   # Case-level mechanism support classifications
    ├── gold20_ablation_comparison.csv # Paired SOG vs PCG residual ablation comparisons
    ├── grid_stability_summary.csv # G0 (50x32) vs G1 (100x64) numerical convergence metrics
    └── cap_pair_scores.csv        # 32 matched pairs comparing SOG, PA, and RADIAL
```

---

## Validation Schemas (`data/validation/`)

### 1. `gold20_cases.csv`
Defines the 20 canonical tactical benchmark cases across the 2022 FIFA World Cup.

| Column | Type | Description |
| :--- | :--- | :--- |
| `case_id` | string | Unique identifier (`GOLD001`–`GOLD020`) |
| `pff_match_id` | int | Commercial PFF match identifier |
| `home_team` | string | Home team name |
| `away_team` | string | Away team name |
| `attacking_team` | string | Team executing the attacking tactical mechanism |
| `defending_team` | string | Team whose defensive structure is evaluated |
| `period` | int | Match half (1 or 2) |
| `search_start_clock`| string | Visible match clock start for tactical event search |
| `search_end_clock` | string | Visible match clock end for tactical event search |
| `safety_window_start_frame` | int | Earliest allowable frame in candidate window |
| `safety_window_end_frame` | int | Latest allowable frame in candidate window |
| `key_release_frame` | int | Exact discrete release frame aligned to mechanism |
| `evidence_strength` | string | `A` (Primary Bank: 13 cases) or `B` (Secondary Bank: 7 cases) |
| `compatibility_class` | string | `DIRECT_MULTI`, `DIRECT_SINGLE`, `PARTIAL`, `INDIRECT` |
| `offside_relevance` | string | `NONE`, `POSSIBLE`, `CENTRAL_TO_MECHANISM` |

### 2. `gold20_actions.csv`
Catalogues the 46 individual tactical movements executed across the 20 cases.

| Column | Type | Description |
| :--- | :--- | :--- |
| `case_id` | string | Foreign key referencing `gold20_cases.csv` |
| `player_name` | string | Documented player name |
| `shirt_number` | int | Player jersey number |
| `team` | string | Player's national team |
| `role_in_mechanism` | string | `PRIMARY_EXPLOITER`, `SPACE_CREATOR`, `SUPPORT_RUNNER`, `PINNING_PLAYER`, `DECOY`, `PASSER` |
| `movement_description`| string | Qualitative description of movement from external source |
| `source_id` | string | Foreign key referencing `gold20_sources.csv` |
| `evidence_strength` | string | Evidence tier (`A` or `B`) |
| `evaluability` | string | `DIRECTLY_EVALUABLE`, `STATIC_ROLE_NOT_ACTION_COMPATIBLE`, `PASSER_ONLY_NOT_ACTION_COMPATIBLE`, `OFFSIDE_CONFOUNDED_BUT_SCOREABLE` |
| `frozen_direction_deg`| float | Documented movement vector quantized to nearest 45° sector (0°, 45°, ..., 315°) |

### 3. `gold20_sources.csv`
Full bibliographic references and video timestamps supporting each Gold-20 action.

| Column | Type | Description |
| :--- | :--- | :--- |
| `source_id` | string | Unique source identifier (e.g. `GOLD001-S1`) |
| `case_id` | string | Associated case identifier |
| `source_role` | string | `TACTICAL`, `TIMING`, or `SECONDARY_CORROBORATION` |
| `title` | string | Article or document title |
| `author_or_speaker` | string | Tactical analyst, journalist, or coaching author |
| `publisher` | string | Publishing outlet (e.g. *The Athletic*, *Coaches' Voice*, *Total Football Analysis*) |
| `publication_date` | string | Date of publication |
| `url` | string | Public URL to original source article or open data feed |
| `source_tier` | string | Source reliability classification tier |
| `exact_quote` | string | Verbatim quote establishing the tactical mechanism |
| `quote_location` | string | Paragraph, figure, or section citation |
| `video_timestamp_start` | string | Broadcast video start timestamp |
| `video_timestamp_end` | string | Broadcast video end timestamp |
| `visible_match_clock` | string | On-screen broadcast scoreboard time |
| `accessed_date` | string | Date source URL was retrieved and verified |
| `timing_source_type` | string | Type of timing verification (e.g. open event feed, broadcast) |
| `timing_evidence_text` | string | Supporting timing details and event timestamps |
| `timing_confidence` | string | Timing accuracy confidence rating |
| `video_access_status` | string | Availability of broadcast video footage |
| `source_notes` | string | Methodological notes regarding source alignment |

### 4. `fragility_validation.csv`
Defines 11 unpaired World Cup states (9 vulnerable, 2 robust) for independent construct validation (EXP028 preregistration).

| Column | Type | Description |
| :--- | :--- | :--- |
| `case_id` | string | Unique identifier (`STATE_001`–`STATE_UNP_001`, `NRP001`–`NRP005`) |
| `label` | string | Ground-truth construct label: `VULNERABLE` or `ROBUST` |
| `competition` | string | Competition name (*FIFA World Cup Qatar 2022*) |
| `match_date` | string | Date of match (YYYY-MM-DD) |
| `home_team` | string | Home team |
| `away_team` | string | Away team |
| `attacking_team` | string | Attacking team |
| `defending_team` | string | Defending team |
| `period` | string | Match half (`1H` or `2H`) |
| `assessment_clock` | string | Visible match clock (MM:SS) |
| `structural_mechanism` | string | Qualitative description of defensive weakness or robustness |
| `why_vulnerable_or_robust` | string | Tactical rationale from published literature |
| `phase` | string | Tactical phase (`SETTLED_ATTACK` or `TRANSITION`) |
| `ball_zone` | string | Pitch zone of ball (`DEFENSIVE_THIRD`, `MIDDLE_THIRD`, `FINAL_THIRD`) |
| `downstream_outcome` | string | Immediate sequence result (`GOAL`, `SHOT`, `TURNOVER`, `OTHER`) |

### 5. `fragility_sources.csv`
Bibliographic sources and verification notes for the 11 independent construct validation states.

| Column | Type | Description |
| :--- | :--- | :--- |
| `source_id` | string | Unique source identifier |
| `state_id` | string | Associated state identifier |
| `role` | string | `PRIMARY_TACTICAL` or `TIMING_VERIFICATION` |
| `url` | string | Public URL to source publication or raw event feed |
| `bibliographic_metadata` | string | Citation details (author, publication, date) |
| `short_quote` | string | Verbatim quote establishing tactical status |
| `independence_notes` | string | Confirmation of independence from metric formulation |
| `timing_notes` | string | Event-aligned timing details |
| `verification_status` | string | Verification status and audit date |
