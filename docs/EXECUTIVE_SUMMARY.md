# Executive summary — GEMS submission readiness and nine-site review

**Review date:** 2026-10-26 (UTC)  
**Decision:** **NO TIF GENERATED. DO NOT DOWNLOAD OR SUBMIT A FILE FROM THIS REPOSITORY.**  
**Scope:** repo review; focused-site historical raster audit; official source and competition-page checks; candidate slate. This is not a submission selection.

> **The requested unique submission is not safe to create in this checkout.** This repository contains no competition data, feature cache, shared template, holdout evaluator, or submission writer. The official DrivenData data page redirects to login. The required shared workflow cannot be reproduced without those inputs. Inventing a raster, copying a previous TIFF, or reporting a projected leaderboard score would violate the research protocol.

## Decision at a glance

| Question | Answer |
|---|---|
| Which focus-site artifact has the highest historical reported value? | GEMSDOE32 `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` is the highest item in the supplied historical list. Its `0.2778` is an **unverified OWNER-REPORT**, not an organizer receipt or a holdout result. |
| What is the best submission to download from this checkout? | **None.** No candidate TIFF was generated. Historical TIFFs are inspection-only and fail the requested uniqueness gate. |
| Estimated score for a new candidate? | **Not estimable.** No `HOLDOUT-DTI` was run. No numerical projection is reported. |
| Are the nine historical focus-site winners unique from each other? | **No.** Independent raster comparison found every one of the 36 site pairs violates the `>70% within 3 px` overlap rule. Eleven pairs also exceed `0.90` absolute Spearman rank correlation. |
| Is there a validated candidate that beats the current holdout best? | No candidate could be tested: the shared feature cache/evaluator/writer are absent. No slot was used. |
| What is the official public leaderboard baseline now? | At retrieval on 2026-10-26, the official page showed rank 1 at `0.4437`. This is a time-stamped public leaderboard observation, not a score for this project or a submission-page receipt. The prompt's `0.3195` is stale relative to that retrieved page. |

### Submit/download callout

**OK TO DOWNLOAD AND SUBMIT: NO.** There is no new `.tif` file to download from this repo. Do not submit any of the old focus-site rasters as a “unique” candidate. Their names and reported values below are kept only for audit and learning.

## Focus-site executive table

The historical values below are copied from the user-supplied list and cross-referenced against the nine-site artifact audit in GEMSDOE32. That audit labels these values as owner-reported and says it has no organizer receipt that binds the exact TIFF bytes to the portal score. They are therefore **not `ORGANIZER-CONFIRMED`** and must not be used as estimates for a new file. Every new-file estimate is explicitly **not available as `HOLDOUT-DTI`**.

| Site | Highest historical artifact in the supplied list (reference only; do not re-submit) | Historical value (unverified OWNER-REPORT) | New-file estimate (`HOLDOUT-DTI`) | Unique vs the other eight listed winners? | Download / submit status |
|---|---|---:|---|---|---|
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | 0.2477 | Not run; no evaluator/data | **No** — all eight pairings fail the overlap test | No new TIF; historical only |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | 0.2600 | Not run; no evaluator/data | **No** — all eight pairings fail the overlap test | No new TIF; historical only |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | 0.2449 | Not run; no evaluator/data | **No** — all eight pairings fail the overlap test | No new TIF; historical only |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | 0.2710 | Not run; no evaluator/data | **No** — all eight pairings fail the overlap test | No new TIF; historical only |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | 0.2600 | Not run; no evaluator/data | **No** — all eight pairings fail the overlap test | No new TIF; historical only |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | `h27-4-solo-d28-20261004-8acb75e1-nan` | 0.2708 | Not run; no evaluator/data | **No** — all eight pairings fail the overlap test | No new TIF; historical only |
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | 0.2778 | Not run; no evaluator/data | **No** — all eight pairings fail the overlap test | No new TIF; historical only |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | 0.2632 | Not run; no evaluator/data | **No** — all eight pairings fail the overlap test | No new TIF; historical only |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | 0.2750 | Not run; no evaluator/data | **No** — all eight pairings fail the overlap test | No new TIF; historical only |

**Audit details:** I cloned the nine public GitHub source repositories for read-only review; did not copy any TIFF into this repository. I independently checked each audited TIFF's SHA-256 against the site audit, verified single-band shape and EPSG:32611, then recomputed pairwise Spearman correlation and directional positive-pixel overlap within 3 pixels on the valid sample footprint. All 36 pairs had both directional overlap fractions above 70%. GEMSDOE25 and GEMSDOE30 have identical binary positive-pixel sets (Spearman `1.000`, both directional overlaps `1.000`). GEMSDOE24/GEMSDOE27 have correlation `0.9896`; GEMSDOE32/GEMSDOE36 have correlation `0.9843`. These are **uniqueness-audit results**, not score estimates. The full reproducibility metadata and pairwise values are retained in [`docs/data/focus-site-raster-audit.json`](data/focus-site-raster-audit.json). The upstream comparison source is [GEMSDOE32's nine-site best-file audit](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/07806249f4ed3efe70b4fbf866183c32392b7853/evidence/nine_site_best_files_audit.json); the result was re-computed from nine raw GeoTIFFs whose SHA-256 hashes match the audit's recorded values. Mask/encoding differences do not make the positive-dot location sets unique under the requested rule.

## Why the GEMSDOE32 `h33…b2` entry appears to lead this historical set

### What is supported

- The supplied historical list identifies this as the focus-set high entry. The source repo's own forensic note calls the value **OWNER-REPORT** and explicitly says there is no submission-page receipt tying the precise raster hash to that value.
- The GEMSDOE32 analysis describes the raster as part of a sparse, thinned ridge-network family, with an additional pruning step near the provided fault catalogue. Its proposed explanation is consistent with the challenge metric: the official DTI uses a 300 m triangular distance kernel and weights `alpha=0.2`, `beta=0.8`; reducing low-credit prediction mass can reduce false-positive cost while nearby useful predictions retain soft credit.
- The project page says existing catalogue labels are incomplete and are not the hidden test set; the task is to detect additional geological faults, not reproduce the public catalogue.

### What is not supported

The report cannot establish that thinning or catalogue-near pruning caused the claimed result, because the private truth, exact weighted TP/FP/FN contribution, and a receipt bound to the exact TIFF bytes are not available in this checkout. Nor does that reported value demonstrate that a new candidate can score higher. The GEMSDOE32 analysis itself retracts earlier hidden-truth inversions and says they should not be reused as results. A model projection is not a score. The prudent conclusion is a plausible mechanism—not a proven causal explanation or a score promise.

### Stale/irregular claims flagged

- The request mentions both `0.3195` and `0.4413` as current top scores. The official public leaderboard page retrieved for this review showed `0.4437` at rank 1 on 2026-10-26. Leaderboards change; always refresh the linked official page. This is not the project's score.
- The old winner-family candidates are heavily overlapping. A different filename, score label, output nodata convention, or raster byte hash does not establish a different geological prediction.
- One source repo's recent research explicitly considered OPERA Sentinel-1 displacement products (GEMSDOE36 HGV36), so InSAR is **not** genuinely novel across the focused sites. Do not relabel that as an untried idea.
- Local format validation is not proof that DrivenData will accept the file. The earlier portal error “Predicted values must be in range [0, 1]” cannot be causally diagnosed without the rejected bytes and portal diagnostics. For future artifacts validate all finite values globally, in-footprint values, nodata behavior, dtype, CRS, shape, bounds, transform, and then record the portal receipt separately.

## New hypothesis slate (ranked; not score projections)

I searched the active research/evidence records in the nine focus repositories for the candidate identifiers below. The three ideas below were not found as named registered experiments in that targeted review; that is a bounded search, not proof that no team has ever tried them. The order is a qualitative research priority (target relevance versus cost/feasibility), **not an estimated score**. Each candidate still needs preregistration, per-feature leakage canaries, buffered whole-segment holdout, and the uniqueness gate.

| Rank | Hypothesis, specific layers, physical signature | Why it could find a missing fault; difference from reviewed work | Primary mimic / falsification | Official source and availability check | Expected DTI benefit / cost |
|---|---|---|---|---|---|
| 1 | **ECOSTRESS persistent thermal-conduit anomaly.** Use NASA LP DAAC ECOSTRESS L2 tiled land-surface temperature and emissivity (`ECO_L2T_LSTE.002`; 70 m), QA/cloud, water, and view-geometry layers. Test robust, scene-normalized temperature residuals and repeat-observation persistence/lineament edges; resample only to the competition grid without implying finer truth. | A permeable unmapped fault may transport hot fluids to a surface thermal anomaly even when the fault lacks a preserved scarp or a strong magnetic/radiometric edge. This is a spaceborne time-varying thermal signal, unlike the static GeoDAWN stack or point thermal/site data seen in prior work. | Solar/topographic illumination, soil-moisture and vegetation stress, lithologic emissivity, wildfire, mines, and irrigated ground. Require persistence across acquisition dates and a visible-fault-only holdout; report a negative if signal vanishes after conditioning on these covariates. | NASA/JPL says DISP/OPERA is already a prior focus-site test (excluded). For this alternative, NASA Earthdata confirms ECOSTRESS L2 temperature/emissivity products and LP DAAC distribution. A CMR catalog query using the sample grid's approximate geographic envelope returned a matching `ECO_L2T_LSTE.002` granule intersecting it. **Product and at least one intersecting granule confirmed; actual download/authentication and full-scene coverage/QA not verified.** | **Highest priority, unquantified and uncertain**; medium-high cost (time-series discovery, cloud/QA, resampling, confound controls). No DTI estimate. |
| 2 | **ASTER hydrothermal alteration signature.** Use ASTER calibrated radiance/reflectance in VNIR/SWIR/TIR plus QA; compute robust spectral ratios or matched-filter scores for spatially coherent alteration zones and their margins, not arbitrary raw-band brightness. | Surface mineral alteration may identify fluid-rock interaction along previously unmapped conduits where topography is subdued. It is multispectral mineral/thermal evidence, distinct from GeoDAWN radiometrics and the reviewed point-based geochemical/thermal features. | Ordinary lithologic contacts, weathering, desert varnish, mine waste, and cloud/shadow. Require blind spatial holdout and a negative-control mineral/contact set. | NASA Earthdata confirms ASTER's 14 wavelengths and LP DAAC products. A CMR query for `AST_L1B.004` and the approximate sample-grid envelope returned an intersecting granule; the returned record reports VNIR/SWIR/TIR acquired. **Catalog intersection confirmed; download, scene-quality screening, and spectral index suitability not verified.** | **Second, unquantified**; high cost (radiometric/atmospheric calibration, scene mosaicking, feature design, geology controls). No DTI estimate. |
| 3 | **Landsat Collection 2 surface-temperature persistence.** Use USGS Landsat 4–9 Level-2 surface-temperature scenes, scene QA, and multi-date robust anomalies after seasonal/topographic normalization; detect persistent elongated thermal residuals rather than a single hot pixel. | Long-term repeated surface-temperature observations may reveal stable fault-fed fluid discharge or altered drainage outside known fault traces. It differs from static airborne bands and isolated site measurements, but overlaps conceptually with thermal indicators and must be tested for incremental value over ECOSTRESS. | Solar aspect, vegetation/water balance, agricultural irrigation, fire, urban/mining activity, emissivity and atmosphere. Require time-split spatial holdout and compare to a terrain/land-cover-only negative control. | USGS documents globally available Landsat Collection 2 surface-temperature scenes, public use, and collection dates. **General availability verified; an AOI-specific Landsat scene query was not run.** | **Third, unquantified**; medium-high cost (time-series preprocessing and confound adjustment). No DTI estimate. |

**Why ECOSTRESS is first:** it has an independent geophysical source and a scene catalog demonstrably intersecting the competition grid, and temperature is directly relevant to geothermal fluid discharge. It is still only a research hypothesis: it can detect vents without tracing faults, and environmental confounds can dominate. It must not be promoted unless its feature-alone AUC stays below the leakage-canary threshold, it improves the prescribed holdout best, and its final dots pass the registry gates. The holdout validation was **not run** because the local labels/features/evaluator are missing.

## Previous methods not to relabel as new

The focused-site source review found prior work on sparse/dotted H19-5 ridge networks, catalogue-distance pruning, LiDAR scarps and terrain gaps, gravity/magnetic edges, Euler/topological features, thermal/geochemical/vent priors, Anderson dip projection, and recent OPERA/INSAR and GNSS-related explorations. The list is not an exhaustive audit of every historical experiment, but it is enough to reject superficial renaming of those families as new.

## Official source review (manual links)

- [DrivenData problem description, datasets, metric, submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/): fetched during this review. It says faults are the target; the provided public faults are incomplete; the metric is distance-weighted Tversky with 300 m support, `alpha=0.2`, `beta=0.8`; and the submission is a single float32 GeoTIFF on the EPSG:32611 / 100 m grid, values from zero to one, with null/NaN outside bounds.
- [DrivenData data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/): fetched and redirected to login. No auth was available or requested; no private competition files were fetched.
- [Official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/): fetched on 2026-10-26. Time-varying snapshot only.
- [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and): official page describes USGS/DOE airborne magnetic and radiometric surveys and related lidar data.
- [Organizer's reference solution](https://github.com/drivendataorg/gems-prize-reference-solution): inspected from the public GitHub source. Its notebook is a U-Net benchmark, not the required hide-and-recover evaluator/writer for this protocol.
- [NASA/JPL OPERA products](https://www.jpl.nasa.gov/go/opera/products/disp-product-suite/): official product source. DISP-S1 is a surface-displacement time series; however, the focused GEMSDOE36 repo already considered it, so it is excluded from the new-candidate slate.
- [NASA ECOSTRESS product description](https://www.earthdata.nasa.gov/data/instruments/ecostress) and [LP DAAC](https://www.earthdata.nasa.gov/centers/lp-daac): official data-source pages.
- [NASA CMR ECOSTRESS granule query for the approximate competition footprint](https://cmr.earthdata.nasa.gov/search/granules.umm_json?collection_concept_id=C2076090826-LPCLOUD&bounding_box=-120.1%2C37.3%2C-116.1%2C40.8&page_size=1): official catalog search; response contained an intersecting `ECO_L2T_LSTE.002` record.
- [NASA ASTER overview](https://www.earthdata.nasa.gov/data/instruments/aster) and [CMR ASTER granule query](https://cmr.earthdata.nasa.gov/search/granules.umm_json?collection_concept_id=C3306888201-LPCLOUD&bounding_box=-120.1%2C37.3%2C-116.1%2C40.8&page_size=1): official archive and a cataloged intersecting granule.
- [USGS Landsat Collection 2 Surface Temperature](https://www.usgs.gov/landsat-missions/landsat-collection-2-surface-temperature): official product description and availability statement.
- [Nine-site source audit and historical `0.2778` review](https://github.com/buffedlizard55-lab/GEMSDOE32/tree/07806249f4ed3efe70b4fbf866183c32392b7853/docs/research): upstream research/audit artifacts are evidence about what those repos record, not organizer receipts.

## Work performed and hard blockers

- Repo inventory: only `README.md` existed at the start; no `data/`, `scripts/`, `src/`, tests, static site, cache, or validation code was present.
- Historical audit: nine public focus-site repos were read-only cloned to temporary review space; the audited rasters' hashes and formats were checked and uniqueness recomputed. No historical raster was copied into this repository.
- Official data page: login redirect reproduced. The missing competition feature/label/template files cannot be independently obtained here.
- Shared tool requirement: `evaluate_holdout.py`, `submission_writer.py`, and the cached template stack are absent locally. No shared-template fix was made; a private replacement was deliberately not created.
- Experiment count: zero new candidate experiments. The raster-pair audit is a historical duplicate check, not a holdout experiment. No weekly competition slot was spent.
- External data: catalog product availability was checked for ECOSTRESS and ASTER, but data were not downloaded or added. No source data are silently included in this repo.

## Next work, in order

1. Restore/attach the official competition inputs and the project's shared template/cache through the approved project workflow; verify their hashes and exact grid. Do not put private credentials in Git.
2. Bring the shared evaluator/writer and canonical registry into this project's supported workflow. Do not copy vendor scripts or create a one-off fork.
3. Check actual ECOSTRESS/ASTER file access, coverage, date/quality constraints, and license/attribution terms; add source manifests and hashes before computing anything.
4. Preregister only the ECOSTRESS increment, then test each feature alone for leakage and evaluate hide-and-recover with whole withheld segments, buffer, fold-local catalogue features, pixel-exact visible mask, pooled official DTI, evaluator version, withheld-positive count, and 95% CI. Stop immediately if uniqueness crosses either lane threshold.
5. Continue to ASTER only if the first preregistered candidate is rejected or passes the mandated experiment schedule. Do not put a slot into the selector without a validated improvement over the current holdout best.
6. Generate and publish a TIF only after a negative/positive run card, final registry check, and strict format/range validation all pass. Store the SHA-256 and an exact portal receipt separately.

## Three-pass completion record

- **Pass 1 — implementation:** reviewed the starting repository, recorded the project charter in the README, added this evidence-backed executive report, and published a static front page whose prominent state is “NO APPROVED TIFF — DO NOT SUBMIT.”
- **Pass 2 — critical review:** checked every historical value against the supplied list and the upstream audit labels; checked exact TIFF hashes; recomputed the pairwise correlations and dot overlaps; looked for recent related methods in the nine focus repositories; verified the DrivenData data-page login redirect; and checked the cited USGS, NASA/JPL, LP DAAC, and NASA CMR records. Corrected the novelty slate to exclude OPERA/InSAR because GEMSDOE36 already considered it.
- **Pass 3 — final gate:** rechecked all requirements against the run protocol. No candidate, TIF, score estimate, slot promotion, or shared-tool modification is claimed. The missing local inputs/evaluator block a valid holdout, so the result remains deliberately negative.

## Final run card (negative result)

```json
{
  "hypothesis": "No candidate was tested. Primary next hypothesis: persistent ECOSTRESS L2 surface-temperature anomalies may trace concealed geothermal-fluid conduits and associated unmapped faults.",
  "mechanism": "Robust scene-normalized thermal residuals and repeat-observation persistence may expose fluid discharge where no clear scarp or potential-field edge is present.",
  "named_non_fault_process_that_could_mimic_it": "Soil-moisture and vegetation stress, solar/topographic illumination, lithologic emissivity, wildfire, mining, and irrigation.",
  "holdout_dti": {
    "label": "HOLDOUT-DTI",
    "evaluator_version": null,
    "withheld_positives": null,
    "dti": null,
    "ci95": null,
    "status": "NOT RUN: shared evaluator, labels, and feature cache are absent from this repository."
  },
  "correlation_overlap_vs_registry": {
    "candidate_surface_checked": false,
    "candidate_final_dots_checked": false,
    "correlation_threshold": 0.9,
    "overlap_threshold": 0.7,
    "radius_px": 3,
    "status": "NOT RUN: no candidate raster exists. Historical focus-site winners were audited separately; all 36 pairs failed the overlap threshold."
  },
  "raster_sha256": null,
  "validator_output": {
    "no_nan_inside_footprint": null,
    "values_in_0_1": null,
    "crs_shape_transform_match": null,
    "status": "NOT RUN: no candidate TIFF was generated."
  },
  "submission_name": null,
  "submission_note": "Negative result: no local shared stack/evaluator; no TIF emitted. Do not submit.",
  "verdict": "negative"
}
```
