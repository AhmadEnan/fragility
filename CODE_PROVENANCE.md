# Source provenance

The public source exports frozen research methods with portable input/output adapters. The original checkout was read without importing or executing its drivers. Frozen scores, outcomes, selection rules and figures were preserved.

`results/source_export_manifest.json` records source-file hashes and copied-file/function/class fingerprints. `python -m fragility.integrity` checks these and split identities. `results/source_manifest.json` retains the original 33 extracted-function fingerprints.

| Public source | Original method |
|---|---|
| `src/obso/` | Eight engine modules copied byte-for-byte; corrected constant-acceleration lineage `db10578` |
| `raw_events.py`, `raw_index.py`, `raw_io.py` | Event parsing, possession segmentation and tracking/event linkage with explicit read-only paths |
| `raw_cap.py`, `raw_cohort.py` | CAP qualification, possession age, frozen eligibility, cadence and release labels |
| `fast_sog.py`, `research_operator.py` | EXP022 fast solver and minimal expression-identical operator initialization |
| `raw_pipeline.py`, `export_inputs.py` | Portable EXP029 adapters and DEV-only release normalization |
| `das_adapter.py`, `comparators.py` | EXP032 AM03 DAS call and original EPV/OBSO reductions |
| `tactical_summary.py`, `tactical.py` | Original temporal summaries and frozen EXP023/024 player-direction evaluation adapter |
| `tactical_solver.py`, `raw_tactical.py` | Frozen fast arithmetic plus PCG accumulation and case extraction |
| `models.py`, `benchmark.py`, `scoring.py` | Original IRLS, design and metrics; frozen replay and independent fitting |
| `submission_figures.py`, `verify_illustration.py` | Presentation reproduction and independent scientific-field check |

The fast solver hoists unchanged-player contributions, preserving the frozen score and action universe. Tactical PCG removes only residual weighting and preserves original float32 stored-field accumulation. Bounded parity checks compare outputs against research references.

The four Figure 2 comparators run with the included engine and optional `accessible-space==2.1.0`. `reference/exp032_comparators.py` remains a historical inspection copy; runtime uses `fragility.comparators` without private imports.

Maintainer export scripts in `tools/` read the original checkout without modifying it. Reviewers do not need those scripts or that checkout. See [verification evidence](RELEASE_AUDIT.md) for what was actually rerun.
