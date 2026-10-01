# EXP029 — HELD-OUT PREDICTIVE VALIDATION OF THE SOG OPENING LANDSCAPE — PREREGISTRATION

**Experiment:** `EXP_SOG_PREDICTIVE_CONFIRM_029`
**Title:** Held-out predictive validation of the SOG opening landscape (+ movement alignment) vs a strong contemporaneous football baseline
**Status:** PREREGISTERED — written and committed **before DEV completion, before model fitting, and before any TEST outcome, prediction, or performance metric exists**
**Date (UTC):** 2026-09-29
**Terminology:** SOG = STRUCTURAL OPENING GAIN, the metric historically called RES0/RES0_V1/R_RES0, frozen by EXP020 (`FRAGILITY_RES0_FREEZE_v1.json`, prereg `38a55c1`, result `e57b751`, engine `db10578`). Stored-row names (`F_RES0`, `R_RES0`, …) keep their historical spelling in code; the report uses SOG names (`F_SOG`, …) for the identical quantities.

> ## REGISTRATION STATUS — READ FIRST
>
> No EXP029 SOG score, C0 field, CAP label, prediction, coefficient, AUC, AP, capture fraction,
> calibration number, bootstrap replicate, permutation result, or figure exists as of this commit.
> The DEV feature store is incomplete (15/16 DEV matches truncated; see `qa/DEV_COVERAGE_AUDIT.csv`) and the
> TEST feature store does not exist. The only numbers cited here are the already-published frozen EXP022
> pilot record (replication panel, §21) and the cohort-construction counts measured during the forensic audit.
> No TEST prediction-state label prevalence was inspected during the audit (only state counts and frame ranges).

---

## 1. Scientific question (one estimand family)

Do the FROZEN SOG opening-landscape features plus the EXISTING movement-alignment features improve prediction
of imminent Controlled Advantageous Penetration (CAP) beyond a strong contemporaneous football baseline on
COMPLETELY HELD-OUT matches?

Conceptual chain under test: defensive state → counterfactual opening landscape → attacker movement toward
available openings → imminent realized exploitation.

NOT under test: whether F_SOG alone is "true fragility"; goals; shots; match outcomes; team quality; future
player trajectories; any new SOG variant.

## 2. Frozen science (do-not-change list)

SOG formula, corrected PPCF implementation, engine commit `db10578`, 50×32 grid (1600 cells,
runtime-extracted), 8 directions, radii 0.5/1.0/1.5 m, residual weighting (exponent 1), movement cost
(rho/1 m), carrier exclusion (nearest attacker within 2.0 m of ball), collision rule, offside logic
(`offside_tol_m = 0.0`; status-switch actions excluded from primary via `valid_primary`), action universe,
direction grouping (6-dp rounding), CAP definition (`cap_common.label_cap` + `cap_label_spec.json`), 2.0 s
release-anchored horizon, 1.0 s cadence + eligibility from EXP022 (`e22_common.cadence_states`,
`eligible_frames`), six SOG landscape features + two alignment features with EXACT EXP022 definitions (§6),
logistic-regression family with EXP022's exact solver settings (§9).

FORBIDDEN: horizon change; CAP redefinition; new outcome; new SOG feature; alignment modification; PA;
RADIAL; steering; SOG tuning; future tracking as predictor; receiver prediction; multiple feature sets with
winner-keeping; any rescue model (exactly three models + one frozen diagnostic, §5).

## 3. Cohort (frozen; Branch A+B hybrid — see `00_EXP022_PROVENANCE_AUDIT.md` §§3–5)

- DEV (development; reported in EXP022; to be completed to 100% under original EXP022 rules): 16 matches
  3812–3842 (even IDs). `cohorts/DEV_MATCHES.csv`. Expected states: 38,450 (sum of cohort counts).
- TEST (held-out; never SOG-solved, never in any OOF/prediction file): 16 matches
  3844, 3846, 3848, 3850, 3852, 3854, 3856, 3858, 10502, 10504, 10506, 10508, 10510, 10512, 10514, 10516.
  `cohorts/TEST_COHORT_FREEZE.csv`. Expected states: ~38,446 minus < 0.1% frozen window exclusions.
- No SHA256 redraw was performed (Branch C not triggered) and none is permitted after this freeze.
- Window exclusions: `cohorts/TEST_WINDOW_EXCLUSIONS.csv` (17 EXP027/028 frames pinned; Gold20 frames in
  3858/10502/10514 pinned from frozen EXP023 STATE_ROWS before TEST generation; rule: exclude states whose
  identity matches or whose (t, t+2.0 s] window contains a development release frame in the same possession).
- Extra time (periods 3/4) excluded everywhere (quarantined sensitivity population; AGENTS.md Rule 4).
- The 48 non-stride tournament matches are listed in `cohorts/EXCLUDED_MATCHES.csv` (never eligible).

## 4. Target (exactly EXP022)

`Y_CAP_2S` = 1 iff a cohort-eligible frozen CAP action's release frame lies in (t, t+2.0 s] for the same
possession and attacking team. CAP completion need NOT occur within two seconds; the two-second requirement
applies to ACTION RELEASE. Future information enters ONLY the label (via frozen `cap_common` event tables).
No predictor uses any tracking/event information after t (provenance table `qa/FEATURE_PROVENANCE.csv`;
leakage audit programmatic: assert max predictor-input timestamp ≤ t per state before scoring, else FAIL
before scoring). Secondary label `Y_LB_2S` (provider line break) is NOT carried forward (EXP022 secondary;
out of scope for confirmation).

## 5. State sampling (exactly EXP022; no balance tuning)

`e22_common.eligible_frames` + `e22_common.cadence_states`: regular time, settled phase (corrected age ≥ 5 s),
in_possession, ball_in_play, slot-stable, defined possession run; deterministic ~1.0 s stepping (30 raw frames).
No oversampling of positives, no undersampling of negatives. TEST prevalence reflects the frozen process.
If computational subsampling becomes necessary: STOP and report before changing protocol (no silent change).

## 6. Features (exact; canonical EXP022 implementation reused, not rederived)

### 6.1 SOG landscape (six) + alignment (two) — EXP022 `feature_dictionary.csv` rows 7–14 verbatim

Over valid_primary actions with finite SOG only. `Q_i` = player i's best valid action score.
- `F_SOG` = mean of top k = max(1, ceil(0.10·N)) valid action scores (the frozen top-10%-mean reducer).
- `R_MAX` = max valid action score. `R_MEDIAN` = median valid action score.
- `TOP_CONCENTRATION` = R_MAX / (F_SOG + 1e-12).
- `TOP_GAP` = (R_rank1 − R_rank2) / (|R_rank1| + 1e-12).
- `PLAYER_CONCENTRATION` = max_i Q_i / (Σ_i max(Q_i,0) + 1e-12).
- `BEST_ALIGNMENT` = max over eligible attackers of (Q_i / max_j Q_j) · max(cos(θ_vel,i − θ_best,i), 0).
- `TOP_PLAYER_ALIGNMENT` = same term for the argmax-Q player.
Velocities are current at-t velocities (that is why M0 carries movement variables: §7).

### 6.2 M0 — strong contemporaneous football baseline (14 conceptual features, §9 of the commission)

Location/possession: (1) normalized ball x (attack +x); (2) |ball y|; (3) Euclidean ball distance to
attacking-goal centre; (4) possession age (corrected `age_s`).
Pressure: (5) carrier→nearest-defender distance; (6) nearest-defender closing speed toward carrier
(positive = closing; radial projection of relative velocity at t).
Movement: (7) carrier speed; (8) mean eligible off-ball attacker speed; (9) max eligible off-ball attacker
speed; (10) mean defending-outfield speed.
Defensive geometry: (11) defending-outfield width; (12) depth; (13) convex-hull area (Qhull; 0.0 degenerate).
Existing control: (14) `C0_ATTACK_AREA` = cell_area × Σ_r C0(r) on the same runtime-extracted 50×32 field
(nominal cell 2.1 × 2.125 = 4.4625 m²; runtime value governs).
Eligibility: carrier = nearest attacking outfielder within 2.0 m of ball (frozen SOG carrier rule; fallback
nearest attacking outfielder, frozen); off-ball attackers = attacking outfielders minus carrier (GK excluded);
defending outfield = 10 outfield defenders (GK excluded from 5,6,10,11,12,13 per the GK protocol; GK enters
only the offside calc, which is not a feature). All positions/velocities at t from the cache row.

### 6.3 Models (exactly three + one frozen diagnostic; no fourth rescue model)

- M0 = 14 baseline features (§6.2).
- M1 = M0 + F_SOG (scalar SOG test).
- M2 = M0 + six landscape + two alignment (primary test).
- M2_LANDSCAPE_ONLY = M0 + six landscape (diagnostic, SECONDARY; preregistered here, fitted on DEV with all
  others; never promoted to primary).

### 6.4 Nonlinearity freeze (simple, predeclared)

Standardized linear + squared terms for ball_x_norm, |ball y|, ball-goal distance (z and z², z² not
re-standardized). All other predictors standardized linear only. (EXP022 had no polynomial convention, so the
commission's default applies; documented here rather than silently underfitting location.)

## 7. Movement baseline fairness (mandatory)

M0 contains carrier speed, off-ball attacker mean/max speed, defender mean speed, and defender closing speed
so alignment cannot win merely because the baseline is blind to motion. These variables stay regardless of
their effect on M2's gain.

## 8. Missing values (freeze before TEST; DEV audit first)

Preferred: deterministic computability (expected: zero missingness). If genuine missingness survives on DEV:
DEV medians + one missingness indicator per affected feature; indicator set frozen before TEST transform; TEST
never supplies imputation values. (To be recorded in DEV_MODEL_FREEZE.json; currently no indicator frozen.)

## 9. Model family + regularization + CV (EXP022 continuity branches)

- Logistic regression, L2, **fixed C = 1.0** (EXP022 used a fixed C → reuse branch; no grid, no tuning),
  no class weighting, intercept YES, Newton-Raphson IRLS (`e22_common.fit_logistic`, byte-identical path),
  max_iter 200, tol 1e-10, deterministic w = 0 start. No forests/GBM/nets/interactions/selection/stepwise.
- CV: EXP022's exact 5-fold grouped-by-match splitter (sorted IDs round-robin; `e22_common.assign_folds`)
  applied to the 16 DEV matches (CV branch "prefer it exactly"; the 8×2 alternative NOT used). All
  preprocessing fitted inside training folds only.
- DEV may be inspected (implementation checks, bug detection, preprocessing fits, coefficient transparency).
  DEV may NOT change features, outcome, horizon, cohort, or success criteria. A disappointing DEV changes nothing.

## 10. Freeze-before-test (commit 5 precedes ANY TEST scoring)

`PREREGISTRATION.md` (this file) + `preregistration.json` + `freeze/FEATURE_SCHEMA.json` +
`qa/FEATURE_PROVENANCE.csv` + `cohorts/TEST_COHORT_FREEZE.csv` + `cohorts/TEST_WINDOW_EXCLUSIONS.csv` +
`freeze/DEV_MODEL_FREEZE.json` (feature order, DEV means/SDs, medians/indicators, polynomial spec, C,
coefficients, intercept, solver settings, software versions — PENDING DEV solve). After that commit, TEST is
evaluation only: no refitting on TEST, no recalibration on TEST.

## 11. TEST generation (once)

TEST features + TEST outcomes generated exactly once into `data/TEST_FEATURES.parquet` /
`data/TEST_OUTCOMES.parquet`; join verified on (match_id, frame_num, focal_is_home/state_key): exactly one
outcome row per state; audits for duplicates/orphans/coverage/class counts recorded without modeling.
Only predeclared eligibility may exclude rows. Production-equivalence gate (§16) must PASS before modeling.

## 12. Comparisons and metrics (frozen)

- PRIMARY: ΔROC_AUC = AUC(M2) − AUC(M0) on full locked TEST; success direction > 0; confirmatory success
  requires 95% match-bootstrap CI (10,000 replicates, seed 20260929, unit = match, paired inside replicate,
  invalid single-class replicates marked and counted, never silently replaced) to exclude 0 positively.
- M1−M0 secondary (same bootstrap): scalar-alone question. M2−M1 descriptive.
- Rare-event (mandatory): AP / PR-AUC / prevalence-no-skill baseline / top-risk-10% window capture per model;
  primary rare-event comparison ΔAP M2−M0 with same bootstrap.
- Review budget: rank all TEST states per model (ties: risk desc, match_id asc, frame_id asc); top 10% states;
  positive-WINDOW capture reported as such (never "event recall").
- Unique CAP-event capture: per linked CAP action/event id, captured if ≥1 eligible window in top-10% set;
  report unique events / captured / fraction per model.
- Alerts (secondary/descriptive): merge same-match same-possession selected states with gap ≤ 2.0 s; report
  episodes, alerts/match, alerts/90, events captured, events/alert. Rule never tuned post hoc.
- Calibration: unmodified TEST probabilities; Brier, log loss, intercept, slope; fixed-quantile reliability
  diagram if N allows. Diagnostics only.
- LOMO robustness: leave-one-match-out pooled ΔAUC M2−M0 on frozen predictions (no refit) + per-match
  states/positives/unique events; report min/max/median/count > 0.
- Coefficients SECONDARY: standardized, transparency only; no causal reading (esp. correlated SOG block).
- Sanity 1 (mandatory, one shot): within-TEST-match permutation of SOG+alignment rows (seed 29092026),
  frozen M2 coefficients; report AUC/AP; similar-to-real ⇒ flag non-state-specific.
- Sanity 2 (diagnostic, prefrozen): M2_LANDSCAPE_ONLY (§6.3) estimates landscape-vs-alignment contribution.

## 13. Success labels (frozen; one of four; no bespoke wording)

- CONFIRMED_INCREMENTAL_PREDICTIVE_SIGNAL iff: ΔAUC M2−M0 > 0 AND 95% CI excludes 0 AND AP M2 > M0 AND
  unique-event capture@10% M2 > M0 AND LOMO not one-match-driven AND calibration not catastrophically degraded.
- PROMISING_BUT_NOT_CONFIRMED iff directional M2 gains but primary CI overlaps 0.
- NO_INCREMENTAL_SIGNAL iff no material/consistent M2 improvement.
- BASELINE_EXPLAINS_PILOT_SIGNAL iff strong M0 closes the EXP022 advantage and M2 adds nothing meaningful.

## 14. Failure/success discipline (frozen)

If TEST fails: no horizon/label/threshold/match/feature/regularization/cohort/model/outcome/alignment/SOG-summary
changes; no subgroup primary; report the null; TEST cohort spent. If TEST succeeds: no TEST refit, no effect
optimization, no subset figures, no F_SOG validation claim from M1 failure, no causality, no within-2-seconds
penetration claim, no goals claim, no "fragility accuracy". M2-success/M1-failure means: the counterfactual
landscape carries prospective information while the top-tail average alone is an inadequate summary (reconciling
EXP023 action correspondence, EXP027 scalar weakness, EXP028 state-level null, EXP022 landscape pilot).
Both-succeed means: F_SOG contributes AND landscape/alignment adds further iff M2 > M1; never a universal
calibrated fragility scale.

## 15. Compute policy + production equivalence + QA (frozen)

- Kaggle T4 for new tracking/PPCF/SOG solves when available; benchmark ≥ 3 matches first; states/sec logged;
  full DEV+TEST projection must fit < 12 h headroom or STOP-and-report; checkpoint by MATCH (immutable);
  resume missing matches only; versioned rerun only on verified implementation bug. Remaining work ≈ 58k
  states (DEV completion ~20k + TEST ~38k); local projection ~10 h at measured 1.647 states/s — Kaggle path
  preferred; benchmark-first rule governs either way.
- PRODUCTION_EQUIVALENCE.json: C0, per-action SOG, action IDs/counts, F_SOG, six landscape, two alignment
  reproduced vs canonical EXP022/EXP023 states (discrete exact; numeric tight tolerance); STOP on failure.
- Action-ID QA: globally unique state IDs; state-local action IDs; no cross-shard collision; 0 orphans;
  0 duplicated canonical action IDs; every action links to exactly one state (BEFORE modeling).
- Temporal/possession QA: no period reversal; monotonic frames; correct possession/attack direction; no state
  after its CAP release; horizon (t, t+2.0 s] from t; CAP release independently recoverable; 25+/25− human audit.
- Leakage audit: programmatic max-predictor-timestamp ≤ t per state; FAIL before scoring on any violation.

## 16. Results artifacts (frozen paths)

`results/TEST_PREDICTIONS.csv MODEL_PERFORMANCE.csv MODEL_COMPARISONS.csv MATCH_BOOTSTRAP.parquet
EVENT_CAPTURE.csv ALERT_ANALYSIS.csv LEAVE_ONE_MATCH_OUT.csv CALIBRATION.csv PERMUTATION_SANITY.csv`;
`figures/FIG01_ROC_HELDOUT FIG02_PRECISION_RECALL_HELDOUT FIG03_REVIEW_BUDGET_CAPTURE FIG04_MATCH_SENSITIVITY
FIG05_CALIBRATION FIG06_RESULT_SUMMARY` (no truncated-axis bars); `EXP029_REPORT.md`; `EXP029_DECISION.md`;
`checksums.sha256`. Report records all 7 commit hashes and the EXP022 replication panel below (historical,
never pooled with held-out numbers).

## 17. No TEST peeking (binding)

Before model freeze: no TEST AUC/AP/prevalence/coefficients/SOG-by-label/examples/calibration/correlations.
Integrity-only checks (counts/timestamps/missingness/files/uniqueness) without outcome comparison. Post-exposure
bug ⇒ freeze, document, assess prediction/outcome impact, versioned amendment, rerun only if objectively
required — never silent patching.

## 21. EXP022 replication panel (HISTORICAL PILOT — never mixed with held-out numbers)

Context AUC 0.586 / context+landscape 0.629 / +alignment(exploratory) 0.674; AP 0.043/0.049/0.063;
top-10% positive-window capture 13.7%/18.1%/25.2% (16 matches, 18,450 states, temporally truncated to
early-match prefixes — see `qa/DEV_COVERAGE_AUDIT.csv`). Purpose: pilot→confirmatory narrative only.
