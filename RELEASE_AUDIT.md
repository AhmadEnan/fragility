# Verification record: source completion

Checked locally on 2026-10-01, starting from submission commit `d8e5176550684955f73cdeb63a668faab339ad4a`.

The source export preserves the frozen study and adds the missing reconstruction paths. The GitHub Actions workflow file has been removed, and the existing remote workflow was disabled and verified as `disabled_manually` at the owner's request. The checks below ran locally.

| Check | Independently verified result |
|---|---|
| Original research checkout protection | 647 file hashes, HEAD and working-tree status unchanged |
| Source and split integrity | 52 copied/extracted source entries checked; all 32 match identities disjoint across splits |
| Fresh raw-event qualification and cohort construction | All 76,786 situations and every label match the release |
| Development event linkage | 38,035 states; 1,314 positives; 752 events; 1,336 links; complete predecessor structure exact |
| Held-out event linkage | 38,751 states; 1,216 positives; 694 events; 1,231 links; complete predecessor structure exact |
| Fresh SOG/context feature extraction | Four held-out states; maximum absolute feature error 1.78e-15 |
| Fresh Figure 2 comparator extraction | Four development states; EPV-at-ball, EPV-weighted control, OBSO and DAS all numerically identical |
| Fresh tactical tracking extraction | GOLD001: 39 states and 8,736 candidates; validity and recovery exact; max SOG error 6.45e-14, PCG error 3.53e-13 |
| Full tactical ranking/recovery from permitted derived scores | All 158,304 candidates; all 29 A/B action recovery and pre-release flags match; primary SOG 13/20, PCG 11/20, pre-release 10/20 each |
| Release-normalization bridge | Full DEV and TEST feature tables match exactly using DEV-only transforms |
| Independent fitting on freshly qualified labels | All ten arms reproduce every event-retrieval count; largest evaluation-probability difference 4.32e-8 |
| Figure 1 engine reconstruction | Selected score 1.0723332626605457; C0 error 2.23e-16; gain error 8.84e-17 |
| Full notebook execution | Completed both in this checkout and from an extracted source archive in a separate virtual environment/kernel |
| Local checks with licensed cache | 12 passed; 116.71 seconds |
| Submission figure PNGs | Both remain byte-for-byte identical to the starting submission |

Machine-readable evidence is in `results/raw_*_completion_parity.json`, `results/export_bridge_completion_parity.json`, `results/refit_verification.json` and `results/original_checkout_protection.json`. The source manifest records original function/file fingerprints. The original four-state extractor and preprocessing checks remain available in their earlier evidence files.

## Scope of computation

Full raw-event/cohort/outcome reconstruction used authorized provider event/metadata files and existing original stride-8 caches and event indices, read-only. No raw tracking files were redistributed. The earlier preprocessing audit reproduced all 30,284 rows and 109 columns for match 10507.

The full normalization/fitting bridge used freshly reconstructed cohorts, labels and links with the original frozen research-unit feature/comparator tables. Fresh pitch-control/SOG and comparator extraction were verified on the bounded samples above; every feature for all 76,786 states was not recalculated in this completion run. Tactical extraction from tracking covered one complete case; full recovery covered the entire supplied candidate bank. The exported commands support those longer complete reconstructions without the private checkout.

The revised notebook was executed locally on Windows/Python 3.13.14 and from the extracted source archive in an isolated environment. `results/source_archive_verification.json` confirms all final code and input files match that executed snapshot. A new browser-based Google Colab run and cross-platform run were not performed for this version. Earlier Colab/CI results apply to earlier commits only.

## Frozen submission artifact

`python tools/build_submission.py` creates `dist/ssac27-source-v1.1.0.zip`, a deterministic source archive with an embedded file manifest and a companion SHA-256 checksum. The archive excludes raw tracking, private caches, the historical local audit and GitHub workflow files. Install from the extracted checkout using `pip -e .`.

Version 1.1.0 uses the publication reference `ssac27-abstract-v1.1.0`. The old `ssac27-abstract-v1.0.0` tag is preserved. The README and remote notebook bootstrap target the new reference. The [versioned release](https://github.com/AhmadEnan/fragility/releases/tag/ssac27-abstract-v1.1.0) provides the source archive and its SHA-256 checksum as frozen reviewer artifacts.
