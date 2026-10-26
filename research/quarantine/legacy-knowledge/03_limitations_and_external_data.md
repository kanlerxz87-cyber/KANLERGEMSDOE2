# Limitations & Free External Data

## Blocker to training
No DrivenData auth in sandbox → cannot auto-download `training_features.tif`, `labels.tif`, `sample_submission.tif`, `1m_DEM_links.csv` from https://www.drivendata.org/competitions/306/competition-doe-gems/data/ (verified redirect to login). Mirrors exist (GDR + Dropbox) — see `scripts/download_competition_data.sh`. Run on unrestricted host into `data/`, then `python scripts/prepare_data.py` — after that train→infer→validate is ready (GPU needed for training; metric/losses/validation verified on CPU).

## Free, official external sources vetted

| Source | URL | License | Shareable with DOE/NLR? | Used for |
|---|---|---|---|---|
| GeoDAWN airborne mag/rad (USGS) | https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and | Public domain (USGS) | Yes | Baseline features (already in training_features.tif) |
| INGENIOUS fault compilation (GBCGE) | https://gbcge.org/current-projects/ingenious/ | Open (contact GBCGE) | Yes | Training labels context |
| 3DEP 1m lidar DEM (USGS) | https://apps.nationalmap.gov/lidar-explorer/ | Public domain | Yes | H2 PJC lane (needs bulk) |
| GDR #1391 Great Basin wells/springs/vents | https://gdr.openei.org/submissions/1391 | CC-BY 4.0 | Yes — attribution | Vent seeds for HVG lane (this submission uses it) |
| GNSS strain rate (UNAVCO/MAGNET) | https://www.unavco.org/data/gps-gnss/derived-products/strain/ | Open | Yes | Strain corridor (already in training_features b5-7) |
| OpenTopography | https://opentopography.org/ | Mixed, per-dataset CC | Check per tile | Alt DEM source |
| Example submission template | https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8 | Competition MIT-ish | Yes | CRS/shape/transform |

All external use complies with Official Rules §3.6/A.4 (must be shareable for verification).

## Known irregularities
- Band b10 vs page “Density of earthquakes” label mismatch — flagged, not blocking.
- R13 lattice pigeonhole — disclosed, rescope applied.
- No ORGANIZER-CONFIRMED score in this repo — all live scores are OWNER-REPORTED.

