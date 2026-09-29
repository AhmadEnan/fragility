# Release Safety, Security & Data Privacy Audit

This audit document verifies that the `fragility` public reproducibility repository satisfies all commercial data licensing terms, conference double-blind submission guidelines, and repository safety standards prior to public release.

Conducted per **SSAC27 Release Engineering Specification (Section 25)**.

---

## 1. Exhaustive Security & Data Privacy Scan Matrix

Every item required by Section 25 was audited across the entire public working tree and fresh Git history using automated regex pattern scanning and manual inspection.

| Category / Artifact Scanned | Target Pattern / Rule | Status | Evidence & Audit Details |
| :--- | :--- | :--- | :--- |
| **1. PFF raw filenames** | Match IDs + tracking extensions | **PASSED** | Zero raw tracking files hosted. Documented only in `DATA_ACCESS.md` as illustrative layout for reviewers with commercial licenses. |
| **2. `.bz2` compressed files** | Binary archives (`*.bz2`) | **PASSED** | Zero `.bz2` binary files exist in repository tree or git history (`git ls-files *.bz2` returns 0). |
| **3. Proprietary JSON dumps** | Raw PFF event / tracking dumps | **PASSED** | Zero raw event or tracking JSON feeds present. Only `expected_results.json` and synthetic unit fixtures exist. |
| **4. x/y tracking dumps** | Frame-by-frame trajectory series | **PASSED** | Zero real tracking coordinates. `data/derived/` stores only scalar percentiles, summary flags, and test statistics. |
| **5. Raw player coordinates** | Proprietary player positions | **PASSED** | No real-match player positions. `synthetic_state.json` contains purely synthetic positions generated for unit tests. |
| **6. Absolute local paths** | Hardcoded filesystem paths | **PASSED** | Zero occurrences of developer drive paths (`C:\...`, `/home/...`). All module references use dynamic `Path.resolve()`. |
| **7. `C:\dev\MIT`** | Internal repository path | **PASSED** | Zero occurrences in working tree or git history (`grep_search` returned 0 matches). |
| **8. `/kaggle/input/`** | Kaggle cloud runtime paths | **PASSED** | Zero occurrences in working tree or git history. |
| **9. Google Drive private paths** | `drive.google.com`, `/content/drive` | **PASSED** | Zero private drive paths present. |
| **10. API keys** | Secret tokens / keys | **PASSED** | Automated entropy and regex scan found zero secret/token signatures. |
| **11. Tokens** | Access tokens (`ghp_`, `bearer`) | **PASSED** | Zero tokens present. |
| **12. Cookies** | Session cookies / authentication | **PASSED** | Zero session cookies or browser caches present. |
| **13. Non-public email addresses**| Conference double-blind check | **PASSED** | All documentation uses generic project contact channels (`SSAC 2027 Research Team`). |
| **14. Private URLs** | Internal staging / private links | **PASSED** | All links point to public documentation or official publisher URLs (Total Football Analysis, Coaches' Voice). |
| **15. Usernames** | Private developer usernames | **PASSED** | Zero developer usernames embedded in source files. |
| **16. Credentials** | Passwords / auth headers | **PASSED** | Zero credentials found. |
| **17. `.env` files** | Environment config files | **PASSED** | Zero `.env` files present; explicitly excluded in `.gitignore`. |
| **18. Notebook hidden outputs** | Stale or private notebook outputs| **PASSED** | `reproduce_ssac27.ipynb` contains clean, deterministic cells without private file paths or environment variables. |
| **19. Binary caches** | `__pycache__`, `.pytest_cache` | **PASSED** | Excluded via `.gitignore` and absent from git index (`git ls-files` shows zero `.pyc` or cache blobs). |
| **20. Model checkpoints** | `*.pt`, `*.pth`, `*.ckpt`, `*.h5` | **PASSED** | Zero model checkpoints; methodology is analytical counterfactual geometry, requiring no neural weights. |
| **21. Raw logs** | Runtime output / debug logs | **PASSED** | Zero `.log` files present in tracked tree. |

---

## 2. Git History & Object Verification

```text
Repository: C:\dev\fragility
Active Branch: main
Total Commits: 2
Tracked Files: 37
Git Objects: All inspected via `git rev-list --objects --all`
Restricted Objects Detected: NONE
```

The Git repository was initialized from a completely fresh directory (`git init`) to guarantee zero historical retention of deleted research files.

---

## 3. Cryptographic Manifest Parity

All 5 shareable derived tables in `data/derived/` cryptographically match the SHA-256 digests in `data/derived/manifest.json`:
- `gold20_player_actions.csv` (`67f0adb1bcbc44edd93d57d62862861d57a6b060f7ba57083446faa3f4bc8fc8`)
- `gold20_cases_summary.csv` (`46394b892f94ac7478023e4dd20765b6effaf3cece4ef27b278e3017b1043b22`)
- `gold20_ablation_comparison.csv` (`e842c7d24efc3121c8e88aa747f90ed4cd1b26be6235603ac884f7cec3b4074a`)
- `grid_stability_summary.csv` (`66e9413b8ff0cbdab63bec343d5255b34443d7a4586538bf6f3867a4451f34ce`)
- `cap_pair_scores.csv` (`6744f1755cec5123d0798784cb1d9bbf472b99a616f988b151074f083186e6ee`)

**Overall Release Audit Verdict: PASSED — Fully cleared for public release.**
