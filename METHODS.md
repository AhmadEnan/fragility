# Scoring and feature dictionary

SOG evaluates off-ball attacking outfield movements of 0.5, 1.0 and 1.5 metres in eight directions. The ball, carrier, defenders, goalkeepers and other attackers stay fixed. Coordinates are oriented with the focal attack toward +x.

For baseline control `C0`, counterfactual control `Ca` and displacement cost `c = radius / 1 metre`:

```text
SOG(a) = sum over cells [(1 - C0) * max(Ca - C0, 0)] / c
PCG(a) = sum over cells [max(Ca - C0, 0)] / c
```

SOG discounts gains in already-controlled space. Scores are sums on the frozen 50×32 grid, not calibrated action-success probabilities. Candidates leaving the pitch, colliding within 0.5 m of another outfielder or changing the moved player's offside status are excluded from primary rankings. The carrier is the nearest attacker within 2 m. Both keepers contribute to control and offside calculations. SOG has no learned scoring weights.

## Situations and outcomes

Development and test contain 16 disjoint matches each. Eligibility requires regular time, possession age ≥5 s, attacking possession, ball in play, stable jersey slots and a known possession run. Sampling anchors each possession at its first eligible state and takes the next eligible state at least `round(fps × 1 second)` raw frames later. Test exclusions are frozen in `data/identity/test_window_exclusions.csv`.

CAP means **controlled advantageous penetration**. Ordinarily completed passes, crosses and carries must cross a release-time defensive-unit boundary. Three contiguous longitudinal units, each with at least two outfield defenders, minimize within-unit squared error. Crossings within 0.5 m of the boundary are ambiguous and excluded.

The endpoint must be received by the same team, with tracking possession retained for one second or until an earlier attacking shot. Within the following two seconds there must be ≥5 m forward progression, an attacking shot or entry into the frozen box proxy (`x ≥36`, `|y| ≤10.08` metres). These proxy dimensions are preserved exactly. Qualified events must be settled at release and aligned within 32 raw frames. A sampled state is positive when a qualified event is released in `(frame, frame + 2 × fps]` in the same possession and perspective. Many-to-many event links are retained.

## Classifier features

Released values are DEV-normalized and dimensionless; original-unit suffixes remain in names. Exact affine parameters are in `data/identity/normalization.json`. `features.py` supplies the formulas.

| Block | Features and meaning | Original units |
|---|---|---|
| Ball context | `ball_x_norm`: focal x; `abs_ball_y_m`: absolute lateral position; `ball_dist_to_goal_m`: Euclidean goal distance | m |
| Possession | `possession_age_s`: raw-frame age / metadata fps | s |
| Pressure | `carrier_nearest_def_dist_m`; `nearest_def_closing_speed_ms`: relative velocity toward carrier | m; m/s |
| Movement | `carrier_speed_ms`; `offball_att_speed_mean_ms`, `offball_att_speed_max_ms`; `def_outfield_speed_mean_ms` | m/s |
| Shape | `def_width_m`, `def_depth_m`, `def_hull_area_m2` | m; m² |
| Control | `C0_ATTACK_AREA_m2`: clipped control sum × original grid-cell area | m² |
| Landscape | `F_SOG`: mean top 10% valid scores; `R_MAX`; `R_MEDIAN` | Fixed-grid score |
| Concentration | `TOP_CONCENTRATION`: maximum / tail mean; `TOP_GAP`: normalized top-two gap; `PLAYER_CONCENTRATION`: largest player maximum / sum of player maxima | Ratios |
| Alignment | `BEST_ALIGNMENT`: largest eligible player's velocity/direction cosine; `TOP_PLAYER_ALIGNMENT`: cosine for the highest-scoring player | Cosines |

When no carrier outfielder is identified, context uses the nearest attacking outfielder and records the fallback. The three ball variables also enter as squared terms after training-partition standardization. Classifier design median-imputes and standardizes separately on each training partition. The classifier is L2 logistic IRLS with `C=1`, separate from the SOG algorithm. All feature roles, ordering and transform statistics are recorded in `data/derived/models.json`.

## Figure 2 comparators

`EPV_AT_BALL` is nearest-cell lookup. `EPV_WEIGHTED_CONTROL` sums `C0 × EPV`. `D_OBSO` is the frozen continuous OBSO adaptation using transition and scoring surfaces, with fitted transition width 23.9 m. `DAS` uses unmodified accessible-space 2.1.0 with frozen published defaults, all 22 players, the actual carrier and exact frame mapping. The pandas compatibility adapter changes input string dtypes only.

Each comparator augments the same context baseline on the same development rows and folds. DAS was added through a disclosed post-hoc literature-completeness amendment; the full configuration preserves that disclosure and the AM03 defect repair. Figure 2 is a development comparison, separate from held-out evidence.

## Documented-action recovery

Frozen annotations identify players, source IDs, movement intervals and direction sectors. Primary recovery uses 20 A-strength evaluable actions from 13 sequences, retaining one offside-confounded but scoreable action. Nine B-strength actions provide supporting evidence. Other roles remain annotated and are excluded by the frozen evaluability rule.

For each state, directions are rounded to six decimals, scores are maximized over radii within player–direction cells, and cells receive minimum ranks. Percentile is `1 - (rank - 1)/(number of cells - 1)`. Recovery requires the documented cell to reach ≥0.90 percentile for two consecutive analysis states within the frozen movement interval expanded by eight raw frames on each side. Missing/invalid cells break the run. Pre-release support uses the original `frame ≤ release frame` convention. Bootstrap resampling is by case, retaining clustered actions.

## Interpretation

Centered tracking velocities can use roughly 0.801 s of subsequent positions. Tactical windows also include post-release states. Evaluation is retrospective: the evidence supports landscape-based retrieval and documented-action correspondence, without establishing live prediction, causal movement benefits or a universally valid scalar defensive-quality measure.
