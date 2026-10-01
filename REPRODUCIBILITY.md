# Reproducing the results

## Using the included data

The notebook checks source fingerprints and input hashes, refits all ten classifiers from labels, checks saved coefficients, recomputes event retrieval and both 10,000-draw bootstrap intervals, and regenerates both figures. Tactical recovery is calculated by ranking candidate scores against the documented player actions.

```bash
python -m pip install -r requirements-reproduce.txt -e ".[test]"
python tests/verify_notebook.py
```

Separate Python processes avoid Colab's preloaded-package state. Frozen probabilities agree within 1e-12. Independent fitting checks training and evaluation rows at a fixed 1e-7 probability tolerance. Figure 2 typography may differ when Arial is unavailable.

## Reconstruction from authorized provider data

Use a source checkout and editable installation. Obtain the PFF FC 2022 World Cup dataset through [DATA_ACCESS.md](DATA_ACCESS.md). `RAW_ROOT` contains `Tracking Data`, `Event Data`, `Metadata` and `Rosters`; tracking filenames are `<match>.jsonl.bz2`. `WORK` is a separate local output directory outside raw inputs and existing cache/index directories.

```bash
python -m pip install -r requirements-reproduce.txt -e ".[raw,test]"

# Build caches/indices, select situations, qualify CAP events and link releases.
python -m fragility.raw_pipeline RAW_ROOT WORK/cohort --stage cohort

# Calculate all context, SOG landscape and movement-alignment features.
python -m fragility.raw_pipeline RAW_ROOT WORK/features --stage features --cache-root WORK/cohort/private_cache --index-root WORK/cohort/private_index

# Calculate Figure 2 comparators on development matches only.
python -m fragility.raw_pipeline RAW_ROOT WORK/comparators --stage comparators --cache-root WORK/cohort/private_cache --index-root WORK/cohort/private_index

# DEV-only normalization, independent fitting, scores and event-link export.
python -m fragility.export_inputs WORK/cohort WORK/features WORK/comparators WORK/derived

# Check freshly qualified labels and the entire event-link structure.
python -m fragility.integrity --cohort-root WORK/cohort

# Rebuild the tactical action bank; build any missing caches privately.
python -m fragility.raw_tactical WORK/cohort/private_cache WORK/tactical --raw-root RAW_ROOT
python -m fragility.tactical --candidates WORK/tactical/tactical_candidate_scores.parquet --output WORK/tactical_results

# Recalculate the results from the freshly fitted classifier inputs.
python -m fragility.reproduce --data-root WORK/derived --output-root WORK/results --tactical-candidates WORK/tactical/tactical_candidate_scores.parquet
```

Keep the raw dataset, caches and event indices separate from each command's output directory. Existing caches and indices can be reused; the commands read them without modifying them. All reconstruction code is included here.

Full feature reconstruction is CPU-intensive: up to 240 movements per state over 1,600 pitch cells. Allow hours, depending on hardware. Serial match processing bounds memory. A quick wiring check adds `--matches 3844 --limit 4` to the feature stage, or `--matches 3812 --limit 4` to the comparator stage. Bounded runs are recorded as such and cannot replace full-study inputs. Tactical extraction accepts `--cases GOLD001`. No GPU is required.

The row manifest records 38,035 development states and 38,751 held-out states with match/frame/perspective keys and globally distinct match identities. Fresh extraction records solver failures; only those recorded failures may remove sampled states. Event linkage preserves multiple qualified releases reachable from one situation.

## Normalization and fitting

`data/identity/normalization.json` supplies the release transforms. `export_inputs.py` reconstructs them from DEV alone: `(x - DEV mean) / DEV population standard deviation`. Nonfinite values remain until classifier design. Feature names retain original-unit suffixes; released values are dimensionless.

Classifier design median-imputes and standardizes on each training partition. Squared ball terms square the already-standardized linear term. Five folds deal numerically sorted development match IDs round-robin. Held-out models fit all development rows; test rows never fit normalization, imputation or coefficients.

The original development run did not retain fold coefficients. Frozen replay coefficients were recovered from its out-of-fold logits without outcomes; independent IRLS fitting checks evaluation probabilities. Fresh raw-data export fits directly from fresh labels and does not rely on recovered coefficients.

## Illustration and optional local checks

Figure 1 combines saved control fields with labels, player symbols and raster corrections to reproduce the original image. To recalculate the illustrated action and control fields from tracking data:

```bash
python -m fragility.preprocessing RAW_ROOT CACHE_ROOT --match 10507 10505
python -m fragility.verify_illustration CACHE_ROOT
```

Set `PFF_DATA_ROOT` to `CACHE_ROOT` for the optional local engine-parity check, `python -m pytest`. It uses match **10505**. `load_pff_state` requires a cache and does not decode raw JSONL.

The frozen [held-out](docs/protocols/heldout.md) and [tactical ablation](docs/protocols/tactical_ablation.md) protocols preserve historical registration. Their predictive language is qualified by the centered-velocity disclosure in the submitted abstract and [METHODS.md](METHODS.md). Reconstruction preserves the existing method without new thresholds or sampling.
