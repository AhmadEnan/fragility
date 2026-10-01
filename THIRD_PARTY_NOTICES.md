# Third-party methods and assets

Project source is released under [MIT](LICENSE). Provider data and derived inputs follow [DATA_ACCESS.md](DATA_ACCESS.md).

## EPV grid

`assets/EPV_grid.csv` is numerically identical to the grid from [Friends of Tracking / LaurieOnTracking](https://github.com/Friends-of-Tracking-Data-FoTD/LaurieOnTracking/blob/master/EPV_grid.csv). Its [MIT license](https://github.com/Friends-of-Tracking-Data-FoTD/LaurieOnTracking/blob/master/LICENSE), copyright 2021 Friends-of-Tracking-Data-FoTD, is included verbatim in `assets/EPV_GRID_LICENSE.txt`. Upstream/local hashes and the identity check are in `assets/EPV_PROVENANCE.json`.

## Pitch control and OBSO

The frozen engine implements a corrected constant-acceleration time-to-intercept adaptation and Spearman-family pitch-control integration. It is the project's implementation; published-model parameter fidelity is qualified in the frozen configuration. Included `obso` modules document equations and alternatives. Source lineage is in [CODE_PROVENANCE.md](CODE_PROVENANCE.md).

Reference: William Spearman, *Beyond Expected Goals*, MIT Sloan Sports Analytics Conference (2018). EPV teaching/reference code is described in [LaurieOnTracking](https://github.com/Friends-of-Tracking-Data-FoTD/LaurieOnTracking).

## Dangerous accessible space

The optional `accessible-space==2.1.0` dependency is used unmodified under its own package license. Reference: Bischofberger and Baca, *Dangerous accessible space*, Journal of Big Data 13:76 (2026). Frozen defaults, late-addition disclosure and the pandas input-dtype workaround are in `configs/literature_benchmark.json`. The runtime checks the version.

## Tactical sources

Authored annotations link FIFA Training Centre, Total Football Analysis and Coaches' Voice sources in `data/validation/tactical_sources.csv`. Frozen action source IDs join those annotations. Source videos and full tactical articles are not redistributed.
