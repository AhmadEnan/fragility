# Code provenance

`results/source_manifest.json` records original file hashes and function AST hashes, excluding docstrings and formatting. Tests check the extracted functions against these fingerprints.

| Public module | Research source |
|---|---|
| `preprocessing.py` | Original frame-cache notebook, cell 2; CLI fixes stride at 8 |
| `models.py` | EXP022 classifier and metrics; EXP029 review selection |
| `benchmark.py` | EXP032 transforms and tied-score statistics |
| `features.py` | EXP029 context features; EXP022 landscape reducer and alignment |
| `extract_features.py` | Portable EXP029 solve-loop adapter using the extracted feature functions and public SOG engine |
| `reference/exp032_comparators.py` | Original EXP032 comparator extraction functions, provided for inspection |
| `outcomes.py` | EXP022 future-release window linkage |
| `scoring.py` | Portable replay of frozen models on normalized features |
| `submission_figures.py` | Submission renderer adapted to computed fields, annotation artwork and portable paths |
| `reproduce.py` | Public input checks, statistics and anonymous event retrieval |

The compact SOG engine is a public adaptation. Local checks reproduce two tactical examples and four held-out states. The raw-cache converter reproduces all 30,284 rows and 109 columns of match 10507 exactly.

The tracking feature extractor computes the 14 context features, six SOG features and two alignment features in research units. It accepts possession age from the original cohort definition. `results/feature_extraction_parity.json` records comparisons with original held-out feature rows. The extracted functions are unchanged; the portable adapter replaces private repository imports and checkpoint handling.

The comparator reference preserves the original functions, with docstrings and formatting removed from fingerprint comparisons. It requires the original experiment driver and research modules; it is not a standalone extractor. The notebook uses the frozen derived comparator values.

The complete raw-event cohort and CAP qualification pipeline is outside this compact package. Frozen outcome labels and event links define the public reproduction boundary.
