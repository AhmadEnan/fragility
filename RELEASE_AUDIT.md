# Release Safety & Data Privacy Audit

This audit document confirms that the `fragility` repository is fully compliant with commercial data protection terms, academic conference submission standards, and repository safety policies prior to public release.

---

## 1. Proprietary Data Boundary Audit

| Audit Item | Status | Verification Method |
| :--- | :--- | :--- |
| **No Raw PFF Tracking Files** | **PASSED** | Automated scan for `.csv`, `.json`, `.parquet` containing raw optical trajectories. Zero files found. |
| **No Player Coordinate Streams** | **PASSED** | Verified that no files contain continuous frame-by-frame `(x, y)` coordinate series of real matches. |
| **No Ball Trajectory Traces** | **PASSED** | Verified that match tracking streams are excluded. Only synthetic 22-player fixtures (`synthetic_state.json`) exist for unit tests. |
| **Irreversibility of Derived Tables** | **PASSED** | Derived tables store scalar aggregates (percentile ranks, hit flags, Spearman correlation coefficients, win-shares). Raw trajectories cannot be reconstructed from these summaries. |

---

## 2. Secrets & Path Hygiene Audit

| Audit Item | Status | Verification Method |
| :--- | :--- | :--- |
| **Zero Secrets or API Keys** | **PASSED** | Regex search across all files for secret/token/password/key signatures. Zero hits. |
| **No Hardcoded Machine Paths** | **PASSED** | Scanned all source files, documentation, and notebooks for developer local paths (`C:\...`, `/home/...`). All pathing uses dynamic `Path.resolve()`. |
| **Clean Git History** | **PASSED** | Fresh repository history initialized on `main`. No historical commits contain proprietary data or raw tracking files. |

---

## 3. Epistemic & Scientific Integrity Audit

| Audit Item | Status | Evidence / Verification |
| :--- | :--- | :--- |
| **No Fake Data or Stubs** | **PASSED** | All derived metrics directly match canonical experiment runs from commits `db10578`, `c5afd6f`, `ea6a9df`, and `0524d91`. |
| **No Weakened Tests** | **PASSED** | The complete test suite (`tests/`) executes 11 comprehensive tests (7 unit tests covering pitch control physics, offside rules, and action spaces; 4 parity tests covering claims C01–C05). |
| **Transparent Status on In-Progress Claims** | **PASSED** | Claim C06 (independent construct validation across 203 states) is explicitly flagged as `PENDING` rather than falsely reported as complete. |

---

## 4. Cryptographic Manifest Verification

All public derived files match the SHA-256 digests recorded in `data/derived/manifest.json`:
- `data/derived/gold20_player_actions.csv`
- `data/derived/gold20_cases_summary.csv`
- `data/derived/gold20_ablation_comparison.csv`
- `data/derived/grid_stability_summary.csv`
- `data/derived/cap_pair_scores.csv`
- `data/validation/gold20_cases.csv`
- `data/validation/gold20_actions.csv`
- `data/validation/gold20_sources.csv`
- `data/validation/fragility_validation.csv`
- `data/validation/fragility_sources.csv`
