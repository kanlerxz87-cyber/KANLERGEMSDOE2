# Repository review — 2026-10-28

## Decision: NOT OK TO SUBMIT

No new method paragraph accompanies the repeated parallel-run prompt. The frozen lane already has a literal-registry stop; do not silently select another archived lane, change its budget, exempt a calibration raster, or generate a cosmetic variant. Zero new experiments and zero weekly slots were used. This is a review, not a completed competition run.

The independent full-array inspection in `review_run_card_20261028.json` verifies the published HPTR artifact hash, finite values and range. It does **not** authenticate an official template, replay the pre-placement surface, catalogue mask, canaries, holdout, or full fleet, nor verify portal acceptance. Those fields are explicitly unknown, not passes.

## Executive findings for all nine sites

Use the existing [nine-site table](../docs/submission-table.html) and [pinned manifest](../registry/focus_sites_20261027.json) for exact names, historical download links, reported results and directional overlap. No historical file is recommended for upload. The reported ordering is GEMSDOE32, 36, 28, 31, 33, 25=30, 24, 27. This ordering is **USER-REPORTED**, not organizer-confirmed and not a new measurement. The newer failed alternatives in the prompt do not establish a better submission.

**Estimated leaderboard score for every new or historical download: unavailable as a validated estimate.** Existing LLI figures are exploratory projections fitted to user-reported results; leave-site-out prediction error is not a submission-specific confidence interval. Do not use them for promotion.

### Why GEMSDOE32 might outperform its parent

The archived mask comparison reports GEMSDOE32 removes 6,436 dots from GEMSDOE25; GEMSDOE25 and GEMSDOE30 share a positive mask, and GEMSDOE36 adds 1,200 dots to GEMSDOE32. These are archived artifact comparisons, not independently replayed in this review. Removing redundant predictions can reduce false-positive cost with little loss of distance-weighted recall. This is a plausible mechanism, not proof that each removed dot was a false positive or that hidden weighted TP stayed constant.

The rounded, user-reported leaderboard values cannot identify the true hidden labels, their count, or the causal reason for a score difference. Historical statements that pruning removed *pure false positives*, that a fraction of hidden truth is known, or that a candidate *beats 0.2778 on holdout* are overclaims. A comparable holdout procedure can beat another holdout procedure; it cannot directly beat an unverified leaderboard number. SGMC-CAL transformations based on an inferred hidden-truth population are not measured competition DTI and must not be a promotion gate. Passing a leakage canary also does not prove absence of leakage.

## Research triage before implementation

These are **conditional study designs**, ranked by evidentiary value then cost, not predicted numerical DTI gains or authorized lanes. Existing HPTR/DARP/FVCA/TRBVC/LOPE/ECPU work already covers most obvious physics families. We cannot honestly claim these broad ideas are wholly untried. A new lane must define a genuinely distinct mechanism before implementation.

| Rank | Conditional design and specific layers | Physical signature, missing-fault rationale, confounder | Difference to establish; cost and status |
|---|---|---|---|
| 1 | Acquisition-seam invariance control: GeoDAWN magnetic and radiometric grids plus official flight-line/leveling metadata | Test whether candidate gradients persist across independent line groups rather than follow flight lines. Could reject survey artifacts and improve precision on concealed faults. Mimic: leveling seams. | A falsification control, not another persistence-weighted surface already used by HPTR. Medium/high cost; **not viable yet**: metadata not in the verified local cache. Official starting point: USGS GeoDAWN link below. Obtainability not verified here. |
| 2 | Displaced-channel paired-bank control: 3DEP DEM, hydrologic flow and terrain derivatives | Seek repeated lateral offsets of multiple independent channels with compatible slip sense, rather than single ridges. May reveal unmapped strike-slip structures. Mimic: drainage capture, roads, paleoshorelines. | Must differ from existing hydrothermal-piedmont and curvature lanes by explicit multi-channel displacement and negative controls. High cost; official source 3DEP, acquisition unavailable in this restricted session; not yet viable. |
| 3 | Repeat-time deformation falsification: OPERA displacement time series and existing basin-depth grid | Test persistent localized shear with seasonal and groundwater-common-mode removal, targeting active concealed deformation. Mimic: groundwater compaction, atmospheric phase, slope motion. | Temporal residual test rather than existing static GPS shear/LOPE covariates. High cost; not viable until coverage, licensing and free product availability are verified at NASA OPERA. No claim of local availability. |

Expected DTI improvement is **unknown for all three**. No externally dependent idea above is proposed as ready to run. A scientific null result is useful; fault recovery, not direct vent detection, is the prediction target. A geothermal causal narrative alone is not a fault-label validation.

## Access and next steps, in order

1. Retain the literal duplicate stop; resolve it only through an explicit protocol decision, never a private exemption. Supply a single method lane before a new run. Do not change the frozen dot budget to evade the known witness.
2. Restore ignored, hash-pinned core data and registry when available; owner mirrors are not authenticated official data. Obtain organizer template and provenance before treating grid equality as official validation.
3. Replay whole-segment buffered hide-and-recover with visible-only catalogue features, feature-alone canaries, paired spatial bootstrap against a comparable baseline, and both novelty checks. Stop on the first duplicate. Three experiments/two hours maximum.
4. Keep promotion separate. Current-account quota, rules eligibility and organizer acceptance cannot be learned from a public leaderboard. No authenticated DrivenData access exists here.
5. Only an independent selector with all evidence may approve an exact SHA. Existing executive instructions are conditional, not permission to upload a research TIFF.

Outbound network in this session is restricted to GitHub and package registries. DrivenData, USGS, NASA, NLR, Dropbox and the forum are not directly obtainable here. Their links below are source starting points for review, **not claims of fresh verification**. The official reference repository listing was reachable through GitHub during this review; that alone does not verify competition data or rules.

## Sources and provenance

- [Official problem/format/metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Official reference implementation](https://github.com/drivendataorg/gems-prize-reference-solution)
- [Official competition data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [Official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [USGS 3DEP](https://www.usgs.gov/3d-elevation-program)
- [NASA OPERA](https://www.earthdata.nasa.gov/data/projects/opera)

## Three passes

1. Inspected standing brief, frozen lane status, current card, nine-site manifest, published HPTR sidecar and site builder. Added independent numeric/hash inspection and explicit unknown fields.
2. Ran existing test suite: 111 passed. Identified misleading historical causal and score-comparison claims; added this superseding correction, linked at the top of the generated pages and summaries.
3. Added regression tests for hash mismatch, nonfinite/out-of-range data and top-of-page disclosure; rebuilt pages and reran tests. Final suite: **118 passed**, 14 upstream Rasterio pending-deprecation warnings; compileall and `git diff --check` passed. No new raster was emitted because the mandatory stop remains.
