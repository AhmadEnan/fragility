# Data access

Raw optical tracking data from the 2022 FIFA World Cup used in this paper is proprietary to **PFF FC** and cannot be redistributed.

This repository provides two ways to run the analysis:

1. **Public mode (`MODE = "public"`):** Reproduces all paper claims and figures in seconds using shareable summary tables in `data/derived/`. No commercial data needed.
2. **Full mode (`MODE = "full"`):** Recomputes everything from raw tracking frames if you have a licensed copy of the PFF dataset.

---

## Obtaining PFF data

Commercial tracking data must be requested directly from [PFF FC](https://www.pff.com/):
- **Dataset:** *FIFA World Cup Qatar 2022 Full Match Tracking Data*
- **Contact:** `academic-access@pff.com` or `data-inquiries@pff.com`

---

## Running in full mode

Set `PFF_DATA_ROOT` to your dataset folder:

```bash
export PFF_DATA_ROOT="/path/to/FIFA World Cup 2022"
```

The loader expects either the standard PFF folder structure (`Tracking Data/`, `Event Data/`, `Metadata/`, `Rosters/`) or preprocessed frame caches in `frame_cache/match_<id>_stride8.parquet`.

The code normalizes pitch coordinates to attack toward $+x$, determines the Law 11 offside line from the second-last defender, and excludes the ball carrier within 2.0 m.

---

## Evaluated matches

Full reproduction processes only the candidate windows for the benchmark cases:

| Match ID | Date | Match | Benchmark cases |
| :--- | :--- | :--- | :--- |
| `3813` | 2022-11-21 | England vs Iran | `GOLD010`, `GOLD014` |
| `3821` | 2022-11-23 | Germany vs Japan | `GOLD006` |
| `3823` | 2022-11-23 | Belgium vs Canada | `GOLD009` |
| `3834` | 2022-11-26 | France vs Denmark | `GOLD005` |
| `3840` | 2022-11-28 | Cameroon vs Serbia | `GOLD008` |
| `3858` | 2022-12-02 | Serbia vs Switzerland | `GOLD002`, `GOLD003` |
| `10502` | 2022-12-03 | Netherlands vs USA | `GOLD016`, `GOLD017`, `GOLD018` |
| `10505` | 2022-12-04 | England vs Senegal | `GOLD001`, `GOLD013`, `GOLD020` |
| `10511` | 2022-12-09 | Netherlands vs Argentina | `GOLD007` |
| `10513` | 2022-12-10 | England vs France | `GOLD012` |
| `10514` | 2022-12-13 | Argentina vs Croatia | `GOLD004`, `GOLD019` |
| `10515` | 2022-12-14 | France vs Morocco | `GOLD015` |
| `10517` | 2022-12-18 | Argentina vs France | `GOLD011` |
