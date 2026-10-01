# Code provenance

`results/source_manifest.json` records original file hashes and function AST hashes, excluding docstrings and formatting. Tests check the extracted functions against these fingerprints.

| Module | Research source or adaptation |
|---|---|
| `preprocessing.py` | Original frame-cache notebook, cell 2; CLI fixes stride at 8 |
| `models.py` | EXP022 classifier and metrics; EXP029 review selection |
| `benchmark.py` | EXP032 transforms and tied-score statistics |
| `features.py` | EXP029 context features; EXP022 landscape reducer and alignment |
| `extract_features.py` | EXP029 solve-loop adapter using the original feature functions and SOG engine adaptation |
| `reference/exp032_comparators.py` | Original EXP032 comparator extraction functions, provided for inspection |
| `outcomes.py` | EXP022 future-release window linkage |
| `scoring.py` | Saved model inference and refitting on normalized features |
| `submission_figures.py` | Submission renderer adapted to included fields and annotation artwork |
| `reproduce.py` | Input checks, statistics and event retrieval |

The SOG engine is adapted from the research implementation. The tracking extractor computes 14 context features, six SOG features and two alignment features in original units, using possession age from the cohort definition. Its adapter replaces research-repository imports and checkpoint handling. Comparisons with original feature rows are recorded in `results/feature_extraction_parity.json`; see [reproducibility checks](RELEASE_AUDIT.md) for numerical agreement.

The comparator reference preserves the original functions. Running it requires the original experiment driver and research modules. The notebook uses the supplied derived comparator values.

The complete raw-event cohort and CAP outcome qualification pipeline is not included. Reproduction uses the original derived outcome labels and event links.
