# Data access and sharing

Research uses PFF FC's 2022 World Cup tracking and events. The [Gradient Sports release page](https://www.gradientsports.com/blog/enhanced-2022-world-cup-dataset) describes provider access.

1. Use the release page's access form where available.
2. Alternatively, contact [support@gradientsports.com](mailto:support@gradientsports.com), listed on the [official contact page](https://www.gradientsports.com/contact).
3. Request the **2022 FIFA World Cup dataset originally released by PFF FC**, including tracking, events, metadata, rosters and specifications. Describe your intended research use and ask for the applicable usage terms.

Links and the contact address were checked on 2026-10-01. The notebook uses the included derived data and needs no provider access.

## Included derived inputs

The derived inputs shared here include computed features, normalization parameters, coefficients and scores, qualified labels and event links, cohort identities, scalar tactical candidate scores, annotations and computed control fields. These are sufficient to run the reproduction notebook without downloading the provider's dataset.

Raw tracking JSONL/BZ2 files, tracking-cache coordinate/velocity tables, provider event JSON and the original HDF5 field bank are excluded. Reconstruction reads authorized data and places private caches in an explicitly chosen local output directory. `.gitignore` excludes raw tracking and documented private-output directories.

To reconstruct these inputs from raw data, obtain access through the provider and follow [the reconstruction instructions](REPRODUCIBILITY.md#reconstruction-from-authorized-provider-data).

MIT covers project source code, without granting independent redistribution rights to provider data or relicensing derived inputs. The EPV grid has its own included MIT notice; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
