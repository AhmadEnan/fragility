# Reproduction

The notebook verifies input hashes, recomputes held-out and development classifier scores, checks the abstract statistics and renders both figures. Calculations run in fresh Python processes to avoid conflicts with Colab's preloaded packages. Expected scores are comparison artifacts; they are not substituted for inference.

Inputs are normalized with development-only affine transforms. Absolute ball coordinates and the transforms back to provider units are not included. The original feature names identify their mathematical roles; released values are dimensionless. Squared ball-context terms are computed after fold standardization, as in the research code.

Held-out model coefficients come from the original freeze. EXP032 did not save its fold coefficients; these were recovered from frozen out-of-fold logits and the original design matrices, without outcome labels. Replayed probabilities agree within 1e-12. `python -m fragility.scoring` independently refits all models using the original IRLS routine. Its largest local probability difference is 3.4e-8, reflecting stopping-point sensitivity after affine normalization.

Statistics agree with the original tables within 1e-12; counts match exactly. The development AUC interval and tactical case interval use their original 10,000-draw seeds. Figure 1 reconstructs computed control fields beneath fixed annotation artwork, with saved raster compositing corrections. Its PNG pixels match the submitted illustration exactly. Figure 2 is redrawn from recalculated model metrics; Arial is used when installed, otherwise Liberation Sans or DejaVu Sans. Typography can differ across operating systems.

Figure 2 is a development comparison. The abstract's 29.4% is the relative increase from 170 to 220 held-out events; Figure 2's 25.6% is 195 to 245.

For licensed raw-data checks, the original cache preprocessing is available:

```bash
python -m fragility.preprocessing RAW_ROOT CACHE_ROOT --match 10507
```

It uses stride 8 and centered velocities. Set `PFF_DATA_ROOT` to the generated cache directory to enable the optional engine parity test. The public notebook does not rebuild the complete raw-event cohort or CAP qualification pipeline; it uses frozen derived outcome labels and event links.

The reference extractor reads a licensed cache and computes the context and SOG feature block before public-data normalization:

```bash
python -m fragility.extract_features CACHE_ROOT --match 3844 --frame 19209 --perspective home --possession-age-s 62.2288955622289 --output features.json
```

Possession age must come from the cohort's possession timing. This extractor does not assign outcome labels or compute the external Figure 2 comparators. It is separate from the notebook, which needs only the included derived inputs.

The original Figure 2 comparator extraction functions are in `reference/exp032_comparators.py` for inspection. Their fingerprints are checked against the research source. Running them requires the original experiment driver and research modules.
