# Implementation and verification passes — 2026-10-26

These passes are an audit of this repository, not a claim that the stopped scientific lane was completed. All times below are UTC. In the K2 lane, no geological model, surface, candidate dots, feature canary, holdout, TIFF, portal upload, or weekly-slot selection was produced. Other parallel lanes are preserved separately and are not presented as K2 results.

## Pass 1 — implement and verify the available evidence

* Inspected the official problem description, reference implementation, selected nine repositories, their archived results and the shared template. Created a preregistered four-hypothesis slate and fixed K2-SCALE's 37,654-dot budget before the geometry preflight.
* Restored the pinned owner-mirror inputs and nine pinned historical TIFFs. Verified their hashes, alignment and in-footprint values; computed directed three-pixel overlaps and D2.8/B1/B2 lineage. Owner claims remain unauthenticated.
* Proved the 82.34% single-lattice lower bound and stopped before placement, as required. Recorded a negative card, explicit unmeasured fields, supporting receipts, source-linked research and a static no-submit dashboard. Added a fail-closed saved-byte format wrapper, without changing the shared numerical tools.

## Pass 2 — challenge assumptions and repair local defects

* Reproduced the root shared evaluator's empty-canary, visible-mask and missing-registry problems with synthetic inputs; documented why they must be fixed in the upstream shared template. Found the owner-mirror sample/labels equality and conflicting outside-mask/portal claims. No upstream fix or portal acceptance is asserted.
* Corrected the geometry helper to avoid mutating its caller's registry mask, covered the strict `>70%` boundary, and added checks for masked in-footprint values and invalid/out-of-range samples. Kept missing scores, format fields and candidate identifiers as null rather than inferred passes.
* Removed the external CSS font import; fixed GitHub-head refresh so the timeout covers response-body parsing as well as headers, and tested unchanged, changed, rate-limit, offline, malformed, missing-snapshot and stalled-body responses. Wrapped the mobile navigation after visual inspection found links clipped offscreen.

## Pass 3 — independent reproduction and request cross-check

* Made single-TIFF validation fail closed when the candidate or template uses external GDAL sidecars not covered by the TIFF hash, and rechecked all file hashes after inspection. Added regression tests for both candidate and template sidecars.
* Ran `scripts/reproduce_audit.sh` from an **empty separate cache**: downloaded the public template, all 17 owner-mirror inputs, the lattice, and all nine historical rasters. The clean rerun matched both committed evidence objects in every field except the observation timestamp. It did not generate a candidate or access DrivenData.
* Ran 25 Python tests, the Node feed tests and deterministic `build_k2_site.py --check`. The only Python warnings were Rasterio's upstream affine-multiplication deprecation warnings. Local link and fragment checks cover all four site pages.
* Exercised all four local routes in headless Chromium at 1440×900, 390×844 and 320×700; checked viewport overflow and navigation bounds, and tested the GitHub feed with mocked unchanged/changed/unavailable responses. No JavaScript page errors were observed. This does not establish browser compatibility across all devices or live GitHub API availability.
* Reconciled concurrent main-branch work without deleting its quarantined artifacts. A retrospective, hash-pinned E1 pixel audit measured 37,395 of 37,654 dots within the registered lattice halo (99.31%); the original E1 comparison had excluded that lattice. No E1 holdout was replayed.
* Preserved the owner request and values in the README; checked that current status is visibly **do not submit**, historical files are research-only, forecasts are not invented, and the feed does not purport to verify scores or slot readiness.
* Remaining request gaps are explicit: no unique TIF, holdout comparison, authenticated score-to-file receipt, verified live quota or upstream evaluator repair. These cannot be truthfully certified from the completed work; see [audit](audit.md) and [irregularities](irregularities.md) for the next steps.
