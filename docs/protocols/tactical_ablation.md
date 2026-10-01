# EXP024_SOG_INCREMENTAL_ABLATION — PREREGISTRATION

**Experiment:** `EXP024_SOG_INCREMENTAL_ABLATION`
**Directory:** `experiments/EXP_SOG_INCREMENTAL_ABLATION_024/`
**Status:** PREREGISTERED — written and committed **before any PCG score, ranking, or comparison outcome is computed**
**Date (UTC):** 2026-09-28

> ## REGISTRATION STATUS — READ FIRST
>
> **EXP024 was designed after observing EXP023 SOG outcomes. It is therefore NOT an
> independent confirmatory experiment. Its purpose is mechanistic ablation: testing
> whether the residual weighting in frozen SOG adds value over a simpler
> pitch-control gain score on the same frozen bank.**
>
> No PCG value, PCG ranking, PCG percentile, SOG-vs-PCG difference, bootstrap
> interval, or sign-flip result exists as of this commit. The SOG side of the
> comparison is the already-published frozen EXP023 record (imported, never
> recomputed differently). Only input-schema audits (§3) were performed pre-reg;
> they expose no ablation outcome.

---

## 1. Scientific question (one ablation only)

SOG's defining idea is the residual factor `(1 − C0)`: it discounts gains in space
the attacking team already controls. The reviewer question:

> Does that residual weighting actually improve recovery of externally documented
> tactical openings, or would a much simpler positive pitch-control gain metric
> work just as well?

## 2. Frozen SOG formulation (imported from EXP023, unchanged)

```
dC_a(r) = Ca(r) − C0(r)
SOG(a)  = Σ_r (1 − C0(r)) · max(dC_a(r), 0) / c(a)
c(a)    = rho / 1 m
```

Engine `db10578` (unmodified). Grid 50×32=1600. 8 directions × 3 radii
(0.5/1.0/1.5 m). Frozen offside (`offside_tol_m=0.0`, status-switch excluded from
primary via `valid_primary`), carrier, and collision rules. SOG values are
**imported from frozen EXP023 outputs, never recomputed differently**.

## 3. The single comparison metric: PCG (PURE CONTROL GAIN)

```
PCG(a)  = Σ_r max(dC_a(r), 0) / c(a)
```

The ONLY difference from SOG is removal of `(1 − C0)`. Everything else is
identical: same cost `c(a)=rho/1m`, same valid action masks, same windows, same
radii/directions, same cell grouping, same percentile convention, same TOP10
rule. No normalization, no exponent, no value/xT, no C0 threshold, no parameter.

## 4. Frozen inputs (hashes in INPUT_HASHES.json; key pins)

- Gold bank `Validation Set/`: sequences `e2347c6e…08feaa`, players `c223ed5a…25ff1`,
  sources `c4cb6ec0…32c1` — all MATCH prereg (verified pre-reg, 5/5).
- Alignment freeze: `01…f5469271…1923d`, `02…7360c787…ee2d9` — MATCH (2/2).
- Downloaded Stage-B outputs: **32/32 match** `KAGGLE_RUN_PROVENANCE.json`
  (incl. `ALL_ACTION_ROWS d9fab46c…`, `ALL_CELL_LANDSCAPES ed9bd5a3…`,
  `DOCUMENTED… 35951c10…`, 20 H5 files).
- EXP023 closeout QA: **24/24 PASS** (commit `1f34b40` verified).
- Table sizes: ALL_ACTION_ROWS 158304×18; CELL_LANDSCAPES 52489×12; STATE_ROWS 699;
  DOCUMENTED 778 rows; PLAYER_ACTION_SUMMARY 46 rows; H5 totals 154949 actions / 699 states.
- H5 attrs: `engine_commit=db10578`, formula `SOG(a)=sum_r (1-C0(r))*max(dC_a(r),0)/(rho/1m)`.

## 5. Pre-registered structural facts (schema-level input audit, no outcomes)

Verified pre-reg from frozen artifacts (implementation facts the pipeline reuses):

1. `cost == radius` exactly (max |diff| = 0) — cost column reused as-is.
2. `valid_primary ⟺ ~(rejected ∨ offside_switch)` exactly; H5 `action_id` sets
   **equal** valid_primary sets 20/20 cases and globally (154949 rows).
   Rejected rows (1806) carry NaN SOG and have no stored dC; offside-switch rows
   (1549) carry finite SOG but no stored dC and are excluded from ranking.
   **PCG is therefore defined on exactly the valid_primary universe; all other
   rows carry PCG=NaN, mirroring their exclusion from cell ranking.**
3. Action-row `direction_deg` contains float-split values (e.g. `44.99999999999999`
   ×6596 rows alongside `45.0`); cell landscapes are clean 8-grid. Pipeline MUST
   round directions to 6 dp before player×direction grouping (225°-class guard).
4. Cell key is `(jersey, direction)` — `player_name` is NaN for 40194/52489
   landscape rows (names populated only for documented-relevant players).
   Documented cells map via `shirt_number → jersey` (string) + frozen direction.
5. Documented evaluation window per case = scored states with
   `frame ∈ [aligned_seq_start_frame − 8, aligned_seq_end_frame + 8]`; reproduces
   stored `n_window_states` **20/20** and DOCUMENTED state sets 19/19 (GOLD019: 19,
   rule-derived, zero documented rows).
6. Window background (reproduced 20/20 to ≤1e-16): pool `(jersey, dir6)` cells over
   window states; exclude documented `(shirt_number, frozen dir)` cells
   (GOLD019: exclude none); hit = ≥2 **positionally-consecutive** window states
   with percentile ≥ 0.90; rate = hits / non-documented cells. Stored A-bank
   median ≈ 0.20.
7. `DOCUMENTED.direction_deg` equals frozen `frozen_direction_deg` for all 46
   targets (pre-verified); D rows (778) are reused verbatim as the evaluation
   lattice for PCG (same frames, same directions, same pre_release flags).

## 6. PCG computation (from stored raw dC only — zero new Kaggle compute)

- For every stored valid action: `pcg_num = Σ max(dC,0)` over the 1600 float32
  cells; `PCG = pcg_num / cost` (stored cost column).
- New Kaggle run required: **NO** (declared a priori; all dC/C0 already downloaded).
- Kaggle hours consumed: **0**.
- Deterministic verification gate (§9.8): recompute SOG from stored dC+C0 and
  require agreement with stored SOG; hand-check 1 action each from
  GOLD001/GOLD010/GOLD015/GOLD020. (Implementation verification, not outcome
  inspection — SOG outcomes are already public.)

## 7. PCG cell ranking (must match EXP023 convention exactly)

- `Q_PCG(player,direction) = max over frozen radii PCG(player,direction,rho)`.
- 6-dp direction grouping; rank = `1 + #{Q_j > Q_documented}` (min-rank);
  `percentile = 1 − (rank−1)/(M−1)`; identical validity universe and denominator M.
- Never rank radius rows.
- Verification gate (§9): rerun the same code on stored SOG and require exact
  reproduction of ALL_CELL_LANDSCAPES (Q/rank/M/percentile) before trusting PCG.

## 8. Documented-action test (identical to EXP023)

- For each of the 29 evaluable documented player-actions (20 A + 9 B), PCG cell
  percentile at every frame of the SAME pre-frozen window (the 778 D rows).
- Per-action: peak/median/mean percentile, fraction_frames_top10, longest
  consecutive run (frames + seconds), time_of_peak, rank_at_peak.
- `PCG_TOP10_SUPPORTED` ⟺ percentile ≥ 0.90 for ≥2 CONSECUTIVE analysis frames.
- Verification gate: rerun endpoint code on stored SOG D rows and require exact
  reproduction of PLAYER_ACTION_SUMMARY TOP10 flags before trusting PCG.

## 9. Estimands

PRIMARY (A-grade bank only; 13 cases / 20 evaluable actions / 13 primary exploiters):
action-level TOP10 counts/rates + Wilson 95% CI for SOG and PCG; medians of peak,
window-level, and fraction_top10 percentiles; per-metric same-window background;
`Delta_hit = SOG_rate − PCG_rate`; paired `Delta` peak/window percentiles.
SECONDARY: B-grade (7 cases / 9 actions); primary-exploiter hits (SOG x/13 vs PCG
x/13); pre-release diagnostic (supported with ≥2 consec PRE-RELEASE top-10 frames
vs post-release-only) for both metrics; case-level STRONG/SUPPORT/PARTIAL/MISS
under EXP023 rules + transition matrix; mechanism diagnostics per documented
action (`raw_positive_mass`, `residual_weighted_mass`,
`weighted_mean_baseline_control_on_gain = Σ(C0·[dC]+)/Σ[dC]+`) at peak frames to
explain ranking changes (explanatory only).

## 10. Clustering / inference (pre-registered)

- Actions within a case are NOT independent → CASE-CLUSTERED bootstrap: 13 A cases,
  10,000 replicates, seed `20260928`, resample case IDs with replacement, include
  ALL evaluable actions of sampled cases. 95% percentile CIs for Delta_hit, Delta
  mean-peak, Delta mean-window.
- Exact paired case-level diagnostic: per-case
  `d_case = support_fraction_SOG − support_fraction_PCG` (support_fraction =
  supported evaluable actions / evaluable actions); exact two-sided sign-flip test
  over 2^13 = 8192 assignments; report observed mean d_case + p. Diagnostic only.
- No other tests. No p-value thresholds decide the story (see §12).

## 11. GOAL_PROX secondary baseline — NOT COMPUTED

Pre-registered conditional (§15 of the ablation brief): compute GOAL_PROX only if
moved-player baseline/endpoint x/y already exist in downloaded EXP023 outputs.
Schema audit (pre-reg) finds NO per-action coordinates in ALL_ACTION_ROWS (18
cols), H5 files (C0/dC/ids/grid only), or any stage_b_raw table.
**Verdict: GOAL_PROX_NOT_COMPUTED_EXISTING_OUTPUTS_INSUFFICIENT.** No new tracking
solve will be launched for it. Primary ablation is SOG vs PCG.

## 12. Interpretation rule (communication aid; exact numbers always reported)

- A. CLEAR INCREMENTAL EVIDENCE: SOG hit rate > PCG by ≥ ~10 pp AND paired
  percentile deltas agree AND not driven by one case. (Positive cluster CI /
  sign-flip strengthens; no p-threshold required.)
- B. SUGGESTIVE: SOG > PCG on rate + percentiles but wide uncertainty / CI overlaps 0.
- C. NO CLEAR INCREMENTAL EVIDENCE: essentially similar.
- D. ABLATION FAILURE: PCG meaningfully better than SOG → report immediately.

## 13. No-rescue rule (binding after outcomes)

No change to PCG, thresholds (0.90 / 2-frame), windows, case grades, directions,
cost, radii, validity, formulas, exponents, xT/EPV, classifiers, or endpoints
after outcomes are exposed. If SOG loses → ABLATION FAILURE, reported as-is.

## 14. Outputs & figures

`PCG_ACTION_ROWS.parquet`, `PCG_CELL_LANDSCAPES.parquet`,
`DOCUMENTED_ACTION_COMPARISON.csv`, `CASE_COMPARISON.csv`, `BOOTSTRAP_RESULTS.csv`,
`SIGN_FLIP_RESULTS.json`, `MECHANISM_DIAGNOSTICS.csv`, `INPUT_HASHES.json`,
`QA_CHECKS.csv`, `EXP024_REPORT.md`, `EXP024_ABSTRACT_EVIDENCE.md`,
`EXP024_SUBMISSION_DECISION.md`, `checksums.sha256`,
`figures/FIG_EXP024_ABLATION_HIT_RATE.{png,pdf}`,
`figures/FIG_EXP024_PAIRED_PERCENTILES.{png,pdf}`,
optional `figures/FIG_EXP024_WHY_RESIDUAL_MATTERS.{png,pdf}` (one illustrative
case only, labelled as such, only if the fields compellingly explain a change).
Abstract figures: simple, readable at abstract scale, with CIs, exact n, and
same-metric background references.

## 15. QA gates (all must pass before interpreting outcomes)

1. Gold hashes unchanged (5/5). 2. Alignment freeze unchanged (2/2).
3. Documented directions unchanged. 4. Windows unchanged (20/20 rule + D sets).
5. Valid masks reused exactly. 6. Same analysis frames. 7. Same cell denominator.
8. PCG differs from SOG ONLY by removal of (1−C0) (SOG-identity recomputation gate).
9. Same cost. 10. Q = max over frozen radii (SOG-landscape reproduction gate).
11. Min-rank percentiles (same gate). 12. 6-dp direction grouping (split values absorbed).
13. All 20 A actions represented. 14. All 9 B actions represented.
15. No NaN/Inf silently zeroed. 16. 4-action direct recomputation matches table.
17. SOG imported from frozen outputs. 18. Bootstrap samples cases, not actions.
19. No result-dependent exclusion. 20. No formula change after this prereg commit
(engine/formulation metadata consistent: db10578, 50×32).

Any outcome-changing QA failure → STOP, document failure/root cause/exposure/
prereg impact; smallest legitimate bug-fix only if clearly an implementation bug.
