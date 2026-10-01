# Data access and sharing

Research uses PFF FC's 2022 World Cup tracking and events. The [Gradient Sports release page](https://www.gradientsports.com/blog/enhanced-2022-world-cup-dataset) describes provider access.

1. Use the release page's access form where available.
2. Alternatively, contact [support@gradientsports.com](mailto:support@gradientsports.com), listed on the [official contact page](https://www.gradientsports.com/contact).
3. Request the **2022 FIFA World Cup dataset originally released by PFF FC**, including tracking, events, metadata, rosters and specifications. State that you are reproducing an SSAC submission and request applicable usage terms.

Links and the contact address were checked on 2026-10-01. The lightweight notebook needs no provider access.

## Included derived inputs

The owner confirmed on 2026-10-01 that derived inputs may be shared and raw tracking JSONL files may not be shared. This package follows that instruction. Included inputs are computed features, normalization parameters, coefficients and scores, qualified labels and event links, derived cohort identities, scalar tactical candidate scores, authored annotations and computed control fields.

Raw tracking JSONL/BZ2 files, tracking-cache coordinate/velocity tables, provider event JSON and the original HDF5 field bank are excluded. Reconstruction reads authorized data and places private caches in an explicitly chosen local output directory. `.gitignore` excludes raw tracking and documented private-output directories.

The owner's confirmation records the sharing basis supplied for this submission. The repo does not assert an organizer-approved exception or publish correspondence that was not supplied. Reviewers obtain raw data through the provider for full reconstruction.

MIT covers project source code, without granting independent redistribution rights to provider data or relicensing derived inputs. The EPV grid has its own included MIT notice; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
