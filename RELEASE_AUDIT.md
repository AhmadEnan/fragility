# Verification status

The submission package is verified locally, in GitHub Actions and in Google Colab.

- Fresh Windows and clean Linux kernels execute all notebook cells using only the released inputs.
- Held-out and development scores match frozen predictions within 1e-12. Abstract statistics match within 1e-12; event counts match exactly.
- Both 10,000-draw bootstrap intervals reproduce their original seeds.
- Independent classifier refits differ by at most 3.4e-8 in predicted probability.
- Figure 1 pixels match the submitted PNG on Windows and Linux. Figure 2 pixels match on Windows; Linux uses a font fallback.
- The original cache converter reproduces match 10507 exactly: 30,284 rows and 109 columns.
- The compact engine agrees with two tactical examples and four held-out states. Errors in the four held-out comparisons are at most 5.4e-15.
- The reference extractor matches 23 original feature values and flags in each of four held-out states, with maximum absolute error 1.3e-14.
- Tests check input hashes, extracted function fingerprints, score behavior, outcome boundaries and abstract results.
- Latest Windows suite: 11 passed, one optional licensed-data test skipped. The earlier licensed-data run passed all 12 tests. The clean Linux notebook and four submission checks also passed.
- [All six GitHub jobs passed](https://github.com/AhmadEnan/fragility/actions/runs/36893753470): Windows and Linux, Python 3.12, 3.13 and 3.14. Each job runs the tests and executes the notebook.
- Google Colab CPU `Run all` passed on 2026-10-01 at commit `98b1e5cc89a998135cc7f2da566f9da68a6328b5`. All three cells completed and both figures displayed, without raw PFF files or a manual kernel restart.

The public reproduction starts from frozen derived features and labels. It does not rebuild the complete raw-event cohort or CAP qualification pipeline. See [code provenance](CODE_PROVENANCE.md).

Provider permission for downloadable derived inputs has not been independently established. Historical commits retain earlier documentation and local paths; history has not been rewritten.

Provider access and contact links were verified on 2026-10-01. The provider's official contact page lists `support@gradientsports.com`; delivery and access approval have not been tested.
