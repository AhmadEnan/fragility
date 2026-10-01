# Abstract claim ledger

Status: SUPPORTING. This ledger reports existing frozen evidence and reproduction QA. It does not amend any experiment verdict.

| Claim | Primary artifact | Scope |
|---|---|---|
| 38,751 states; 1,216 positive windows; prevalence3.14% | EXP029/results/MODEL_PERFORMANCE.csv |16 held-out regular-time matches; not all64 source matches |
| AUC0.6449802 to0.6784619 | EXP029/results/MODEL_PERFORMANCE.csv |Offline frozen-model comparison; abstract rounds to0.645 and0.678 |
| Paired AUC interval[0.0236367,0.0454728] | EXP029/results/MODEL_COMPARISONS.csv |10,000 match draws; reported mean0.0334468 is bootstrap mean, direct point difference0.0334817 |
| AP0.0482229 to0.0598361 | EXP029/results/MODEL_PERFORMANCE.csv |Rare outcome; AP is not accuracy |
|170 to220 events out of694 | EXP029/results/EVENT_CAPTURE.csv |Top ceil(0.1*38,751)=3,876 ranked states; each linked event once; net count difference, not necessarily50 exclusive new events |
| +29.4% event retrieval | Arithmetic: (220-170)/170 |Relative increase; +7.2046 percentage points in event capture |
| Scalar adds essentially nothing | M1 AUC0.6448875; same table |No promotion of universal scalar fragility |
|13/20 A-grade documented actions, tolerant | EXP023/HEADLINE_METRICS.json; EXP023_SUBMISSION_RESULT.md |13 independently documented high-evidence cases; successful-attack selection; descriptive action correspondence |
|10/20 pre-release action support | experiments/EXP_SOG_PATH_ACCESSIBILITY_DEVELOPMENT_025/PAIRED_PRE_RELEASE.csv |20 rows,10 SOG_pre_sup hits; frame-restricted action correspondence, not causal/predictive accuracy |
| SOG 13/20 versus PCG 11/20; difference +10 percentage points, 95% CI [0,24] percentage points | experiments/EXP_SOG_INCREMENTAL_ABLATION_024/EXP024_ABSTRACT_EVIDENCE.md and DOCUMENTED_ACTION_COMPARISON.csv |20 A-grade actions across 13 sequences; case-bootstrap exact upper bound 0.235 rounded to 0.24; suggestive incremental evidence, not established superiority. Both extra SOG hits are post-release-only; pre-release hits tie 10/20. |
| Median rank correlation0.9998; best-player36/36 | EXP026/026A_GRID_CONVERGENCE/SUMMARY.csv and PLAYER_STABILITY.csv |50x32 versus100x64;36 frozen audit states |
| Fixed1.5m Richarlison candidate | outputs/res0_case_visuals/metadata/case_facts.json; current frame cache |GF003,10507,53427,jersey9,45degrees; score1.072333262660546; reproduced exactly. Spent development illustration, not validation. |
| Centered velocity future support | EXP030/VELOCITY_PROVENANCE_AUDIT.csv; PREREGISTRATION_AMENDMENT_01.md |Formal temporal limitation affects prospective interpretation; magnitude of bias unresolved |
| Central attacking zone branch | outputs/cap_validation_pilot/cap_label_spec.json; cap_common.py |Actual frozen branch x>=36,abs(y)<=10.08; not the full standard penalty area |

Paths abbreviated above: EXP029=`experiments/EXP_SOG_PREDICTIVE_CONFIRM_029`; EXP023=`experiments/EXP_SOG_GOLD20_CONFIRMATION_023`; EXP026=`experiments/EXP_SOG_GRID_STEERING_026`; EXP030=`experiments/EXP_SOG_NONLINEAR_FOLLOWUP_030`.

The revised illustration uses GF003's fixed documented45degree,1.5m candidate at its original precursor frame. The algorithm's overall maximum is a different player's action; this is an illustrative candidate, not the global optimum. GF003 was chosen from a two-case editorial comparison with GF004 because its carrier is unambiguous and its near-goal geometry is clearer. No post-release score is attributed to the pre-release state. Positions remain continuous and calculations retain the frozen32x50 grid. Display shading is interpolated, using an explicit nonlinear green color scale for contrast; the colorbar reports actual values.

The displayed receiving option is (36.75,-5.3125)m. Modeled attacking control increases from0.53344 to0.63679 at that grid cell. Candidate ball paths from the carrier to this point and onwards to the far side of goal have minimum static point-to-segment defender clearances of2.74289m and2.81545m. The goal keeper is included for the shot check. These distances do not establish dynamic interception, a guaranteed reception, causal effects or successful finishing. The exact selection rule and all coordinates are recorded in the figure provenance JSON. The inset enlarges scale while preserving the actual1.5m displacement; dotted guides show its location on the pitch.

No EXP030 boosted result appears in the abstract. No hypotheses, thresholds, labels, estimator parameters, model fits, active jobs, authoritative specifications, or pre-existing owner changes were altered.

The 2026-09-30 wording review is documented in `EXP024_STAGE1_EDITORIAL_ASSESSMENT.md`. The external Stage 1 report reinforces EXP022's pilot-only status. Its missing-3820 limitation does not apply to the local source inventory: raw tracking and event indices exist here. The published pilot's OOF keys are exact first-N cohort prefixes in all 16 matches, including 3812 despite its subsequently complete feature store. No external rebuild metrics replace EXP029's held-out numbers.

The follow-up abstract revision adds the local EXP024 SOG-versus-PCG player-direction comparison requested by the owner. It replaces the grid-resolution sentence to preserve the word limit. The captioned figures remain unchanged; the tactical-action graph is represented by its results in the text, not added as a third figure. The original grid-stability evidence remains in this ledger.

## Editorial clarification of algorithm, evaluation and Gold20 sources

SOG is a deterministic action-scoring algorithm with no learned scoring weights: `S(a) = sum_r ((1-C0(r)) * max(Ca(r)-C0(r),0)) / (rho_a/1m)`. It ranks eligible hypothetical player-displacement actions by decreasing score. The underlying pitch-control calculation is a modeled quantity; other player states remain fixed. Separate logistic classifiers evaluate summaries of these action scores. Figure 2 compares M0 (context baseline), M1 (M0 plus scalar top-tail summary), M2-L (M0 plus six landscape features), and M2 (M0 plus those six features and two movement-alignment features) on identical held-out states. AUC concerns classifier state discrimination, not recovery of a documented action or the SOG score itself. Values, fits, labels, frozen results and uncertainty intervals are unchanged.

The owner's explicitly identified bank is `Validation Set/README_GOLD_VALIDATION_DATASET.md` with `Validation Set/gold_validation_sources.csv`, not `Validation Set/Fragility/`. It contains **20 accepted sequences**, split into **13 A-grade primary** and **7 B-grade secondary** sequences. The abstract's **13/20** result is **13 supported player-direction actions out of 20 evaluable actions in the 13 primary sequences**, not 13 recovered sequences out of 20 sequences. These reference actions come from published third-party tactical accounts; they are not invented examples. This external case correspondence is separate from the EXP029 held-out classifier evaluation.

The source ledger's primary `TACTICAL` publisher assignments are:

| Publisher | Sequences | Case IDs |
|---|---:|---|
| FIFA Training Centre | 5 | GOLD005, GOLD008, GOLD009, GOLD013, GOLD019 |
| Total Football Analysis | 8 | GOLD001, GOLD002, GOLD003, GOLD004, GOLD006, GOLD007, GOLD010, GOLD012 |
| Coaches' Voice | 4 | GOLD011, GOLD014, GOLD015, GOLD020 |
| Opta Analyst | 3 | GOLD016, GOLD017, GOLD018 |

Within the 13 primary sequences, FIFA supplies 4 sequences / 6 of the 20 actions, Total Football Analysis supplies 6 sequences / 10 actions, and Coaches' Voice supplies 3 sequences / 4 actions. GOLD019 is secondary. Article titles beginning "FIFA World Cup 2022" do not establish FIFA authorship. Accurate abstract wording is therefore "external tactical analyses, including FIFA Training Centre reports", rather than attributing the entire bank to FIFA. A FIFA example was verified directly at [Harry Kane: Movement to evade defenders](https://www.fifatrainingcentre.com/en/game/individual-qualities/world-class-skills/harry-kane-movement-to-evade-defenders.php), Example 2 (England-Senegal).

Provenance limit: the current source CSV SHA-256 is `81af1f306733ae7d9787556bdf57a13e9328887abea72eca24038a0c96ffceec`, different from the EXP023 historical input hash `c4cb6ec06441f229b123e080548b8920ef85152cd893ce1b32455ffd6aa232c1`. This editorial attribution uses the current owner-identified ledger; it does not assert byte-identical reproduction of the old source freeze or alter that freeze. Case membership and all reported recovery counts are verified against the existing EXP023/024 outputs. No new validation or rescoring is performed.

### Rebuild commands

Figure fields and vector/raster figures use the existing WSL environment:

```powershell
wsl.exe -e /mnt/c/dev/MIT/.venv/bin/python /mnt/c/dev/MIT/scripts/ssac27_submission/prepare_revision.py
wsl.exe -e /mnt/c/dev/MIT/.venv/bin/python /mnt/c/dev/MIT/scripts/ssac27_submission/render_figures.py
```

The review PDF uses the bundled Windows Python runtime and ReportLab:

```powershell
& 'C:/Users/Ahmed/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' 'C:/dev/MIT/scripts/ssac27_submission/build_review_pdf.py'
```

For text-only revisions, run `scripts/ssac27_submission/export_texts.py` with that Python interpreter before rebuilding the review PDF. It refreshes upload text and word counts while retaining the existing figures. Run `validate_artifacts.py` under WSL to verify frozen prediction arithmetic and hashes, then visually inspect the new PDF before finalizing its validation record and checksum manifest.

The generated input/output SHA-256 manifest and validation log live in `outputs/ssac27_submission/`. Rebuilding field pairs uses licensed local tracking; this packet is not an open-source release.

## Figure 2 single-cohort update, 2026-10-01

Figure 2 exclusively reproduces corrected EXP032 AM03 development-match out-of-fold results for M0 and its SOG/EPV/OBSO/DAS additions. All rows share 38,035 states and 752 events. The separately reported held-out abstract results (29.4% additional retrieval, AP 0.048 to 0.060) still come from EXP029 and are not the values plotted in this revised figure. No new fit or inference.
