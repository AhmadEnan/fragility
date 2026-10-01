# Reproducibility checks

Checks completed on 2026-10-01 cover numerical results, source provenance and notebook execution.

| Check | Agreement with the research outputs |
|---|---|
| Held-out and development predictions | Absolute error within 1e-12 |
| Abstract statistics and event retrieval | Statistics within 1e-12; event counts exact |
| Bootstrap intervals | Both original 10,000-draw intervals reproduced using the original seeds |
| Independent classifier refits | Maximum probability difference 3.4e-8 |
| Figure 1 | Submitted PNG pixels reproduced on Windows and Linux |
| Figure 2 | Submitted PNG pixels reproduced on Windows; font fallback on Linux |
| Raw-cache preprocessing | All 30,284 rows and 109 columns of match 10507 reproduced exactly |
| SOG engine | Two tactical examples and four held-out states reproduced; maximum held-out error 5.4e-15 |
| Tracking feature extraction | 23 feature values and flags checked in each of four held-out states; maximum absolute error 1.3e-14 |

The test suite also checks input hashes, source-function fingerprints, score behavior and outcome-window boundaries. All 12 tests passed with a licensed tracking cache. Without that cache, 11 tests pass and the optional raw-data comparison is skipped.

[GitHub Actions](https://github.com/AhmadEnan/fragility/actions/runs/36894997265) passed tests and full notebook execution on Windows and Linux with Python 3.12, 3.13 and 3.14. Google Colab CPU **Run all** completed at commit `98b1e5cc89a998135cc7f2da566f9da68a6328b5`: all three cells ran and both figures displayed without raw PFF files or a manual runtime restart.

See [reproduction details](REPRODUCIBILITY.md) for model recovery, figure rendering and the scope of raw-data reproduction.
