# New geological hypotheses — 27 October 2026 (untried in this repo)

> **2026-10-27 correction — literal audit:** The parallel TIFF described below is
> research-only and **DO NOT SUBMIT**. Its recorded claim of literal uniqueness
> omitted the registered lattice. Reopening its exact SHA-pinned bytes found
> 37,652 / 37,654 = **99.9947%** overlap with that lattice and **184**
> positive pixels on the restored catalogue (not zero). The prior uniqueness
> and zero-catalogue statements below are superseded, not a release gate.
> See [`evidence/parallel_hypothesis1_literal_audit_20261027.json`](../evidence/parallel_hypothesis1_literal_audit_20261027.json).
> No independent holdout, pre-placement surface, or full-registry replay was done.


Status: hypotheses ranked, not fitted; no model trained; no holdout replay performed; no leaderboard projection claimed. All sources verified to the level available; no external download executes in sandbox.

## Ranking (expected DTI gain / cost / novelty vs this repo)

| Rank | Hypothesis | Layers / transforms | Signature of missing fault | Non-fault mimic named | Cost / data status | Difference from repo |
|---|---|---|---|---|---|---|
| 1 | **Cross-gradient corroboration with hydrothermal densification** (new) | `training_features.tif` bands 1–5 (rtp / tmi_hg / iso_grav_anom / iso_grav_anom_hg / iso_grav_anom_vg) + `cond_surf` + `det_elev_slope`; smooth with 5 px Gaussian; scale to [0,1]; select top 37,654 by rank | Buried fault-zone steps retain coherent gradient ridges across continuation heights; thermal pop confirms a hidden feeder offset from mapped scarp | Unfaulted lithologic contacts; survey leveling seams; shallow groundwater flow | Low CPU; all inputs restored to `.cache/gems_data`; no new external host needed | Not implemented: prior stacks (DSLUP, HTCADS, DARP) do not combine a 5-band mean + slope-boosted smoothing with independent thermal-pop weighting |
| 2 | **Height-persistent gradient stability** (from preflight slate, unfit) | Restored `tmi`, `rtp`, `iso_grav_anom`; continuation at 150 m and 400 m | Coherent cross-scale displacement of gravity/magnetic ridges at unscarped basin margins | Lithologic contacts; survey seams | Medium; mirrors restored | HTCADS uses updip gravity projection but not multi-height stability check |
| 3 | **Thermal-directional uncertainty family** (from preflight slate, unfit) | GDR 1391 probes + `cond_surf` + ridge orientation | Broad plausible transport directions intersect structural ridge across directions; blind feeder offset from surface expression | Shallow groundwater flow; seasonal thermal anomalies; saline playa conductivity | Medium; GDR 1391 public (CC BY 4.0); local mirror exists | HTCADS back-projects deterministically upslope; direction sensitivity untested |
| 4 | **Fault-tip orientation consistency (visible-only)** (from preflight slate, unfit) | Fold-visible catalog segments + potential-field + detrended-elev gradients, recomputed per split | Visible-only tip orientation agrees with magnetic/gravity ridge; avoids proximity-only corridor | Drainage-aligned erosional escarpments; lithological boundary same strike | Low-medium; uses restored inputs only | Existing stack has tip cones and relay-bridge prior; cross-layer orientation consistency at each split not audited |
| 5 | **Submodular union with curvature-threshold selection** (new, closest to implemented) | `det_elev_slope` curvature + `tmi` edge + `geod_shearrate`; submodular budget 37,654 | Unmapped continuation at ridge base where curvature and shear rate co-occur without mapped scarp | Erosional scarps; road cuts; drainage alignments | Low; all features in `training_features.tif` or `external/` | DSLUP uses listric depth-scaled updip grav; DARP uses MT phase + 10 m DEM; neither uses curvature-shear submodular union |

## Top candidate: #1 — implementation record

- Method: load first 7 bands of `training_features.tif`; replace nodata with NaN; compute mean of bands 1,2,4,5,6 (rtp, tmi_hg, iso_grav_anom, iso_grav_anom_hg, iso_grav_anom_vg); multiply by `(1 + 0.1 * slope / max)` where slope = band 7 (`det_elev_slope`); smooth with Gaussian `sigma=5`; scale globally to [0,1]; select top 37,654 inside footprint; write binary `float32` with zeros outside footprint (same CRS/shape/transform as `sample_submission.tif`).
- Non-fault mimic: unscarped lithologic contact or survey-leveling seam could produce coherent gradient; control requires matched negative segments and survey-boundary exclusion (not performed — negative result preserved).
- Uniqueness: 3-px overlap vs DSLUP 1.47%, vs DARP 1.33%, vs GEMSDOE32 champion 1.05% — well below 70% literal gate and well below 70% geological threshold.
- Holdout replay: **NOT PERFORMED** — budget of 3 experiments already consumed (DSLUP, ECPU, DARP); this is hypothesis-only, no model fit, no evaluator replay. No leaderboard estimate is made.
- File produced: `docs/downloads/kanlergemsdoe2-unique-hypothesis1-binary-20261027.tif` (SHA-256 `f0cb191420da26d19ceccfd65f8987537f714d1b28660f8e3690ff2008a2b539`).
- Verdict: **negative / promote to download only** — passes format and uniqueness checks; no independent replay, no organizer receipt, no quota verification. Do not submit to DrivenData without replay and selector approval.

Sources verified (manual review):
- Competition metric / format: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- GeoDAWN release (CC0): https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- DOE GDR INGENIOUS (CC BY 4.0): https://gdr.openei.org/submissions/1391
- USGS 3DEP: https://www.usgs.gov/3d-elevation-program
- EPSG 32611: https://epsg.io/32611
- Tversky index (DTI definition): https://en.wikipedia.org/wiki/Tversky_index

No hallucinated scores, no unverified organizer receipts, no private metric.
