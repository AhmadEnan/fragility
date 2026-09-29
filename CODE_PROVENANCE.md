# Code provenance

Source mapping for the public implementation against canonical research commit `db10578`.

| Public module | Canonical source | Purpose |
| :--- | :--- | :--- |
| `src/fragility/config.py` | `src/sog/config.py` | Parameters ($50 \times 32$ grid, 8 directions, 3 radii, top 10% reducer). |
| `src/fragility/pitch_control.py` | `src/obso/ppcf.py` | PPCF integration and acceleration-cruise kinematics ($v_{\max}=5.0, a_{\max}=7.0$). |
| `src/fragility/pff.py` | `src/fragility/pff.py` | Coordinate normalization, Law 11 offside line, carrier exclusion ($d \le 2.0\text{ m}$). |
| `src/fragility/sog.py` | `scripts/exp020_.../rc_common.py` | 24 counterfactual actions per player, SOG scoring, and tail aggregation. |
| `src/fragility/validation.py` | `scripts/exp023_.../`, `exp027_...` | Wilson CIs, case bootstrap, Spearman rank correlation, permutation tests. |
| `src/fragility/figures.py` | `scripts/exp025_.../` | Programmatic generation of Figures 1 and 2 directly from data tables. |
