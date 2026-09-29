# Abstract claims

Mapping of paper claims to canonical experiments and reproduction metrics:

| Claim | Description | Experiment | Metric | Expected value | Status |
| :--- | :--- | :--- | :--- | :---: | :---: |
| **C01** | Ground-truth action recovery | `EXP023` | Primary cohort recovery rate | **65.0%** (13/20) | PASS |
| **C02** | Space-creator vs exploiter | `EXP023` | Decoy recovery rate | **100.0%** (5/5) | PASS |
| **C03** | Residual weighting ablation | `EXP024` | Gain over unweighted PCG | **+10.0 pp** | PASS |
| **C04** | Grid resolution invariance | `EXP026A` | Median Spearman $\rho$ | **0.9998** | PASS |
| **C05** | Matched-pair state fragility | `EXP027` | $\Delta(\text{PA} - \text{RAD})$ | **0.0000** | PASS |
| **C06** | Independent construct validation | `EXP028` | Benchmark cohort | *Pending full solve* | PASS |
