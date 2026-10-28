# Review of concurrent PR #53 artifact — not approved

**Decision: DO NOT SUBMIT; not a candidate for the focus-nine task.** PR #53 (`Generate unique blind-interior TIF submission + executive summary`) was merged to `main` while PR #52 was being updated. This review did not generate, fit, or holdout-test its artifact, and no live slot was used.

The PR's run card describes a 20,000-positive-pixel blind-interior systematic raster. The frozen focus-nine protocol and mandatory preflight use a 37,654-dot budget; at that budget the registered spacing-5 lattice forces at least 31,005/37,654 = 82.3418% overlap within 3 px, above the 70% limit. PR #53 instead changes the budget to 20,000, for which its own computed lattice lower bound is 66.755%. Changing the budget to evade the frozen stop does not resolve it and is not authorized by this task.

Other limitations recorded by PR #53 itself:

- `holdout_dti` and its confidence interval are null; the card says organizer-authenticated labels were unavailable and no holdout replay was performed.
- The claimed final-dot comparison covers 29 locally available registry rasters, not the full current registry. It therefore cannot establish the required fleet-wide uniqueness.
- The format validator says `submission_authorized: false` and explicitly limits itself to format checks. Matching a local owner-mirror template and passing local range checks does not establish organizer acceptance.
- The emitted surface is a footprint-geometry-only systematic design. It is not the top focus-nine hypothesis tested under the frozen lane.

The TIFF, template, validation sidecar and run card are retained as provenance of a separate concurrent main-branch change, not as a deliverable or recommendation. This repository's current focus-nine decision remains **DO NOT SUBMIT**. Do not download this TIFF for competition use, do not report it as a measured candidate, and do not spend a live slot on it.

Evidence inspected: `evidence/run_card_unique_7da04408edc9.json`, `docs/data/run_card.json`, and `scripts/generate_unique_submission_tif.py` from merged PR #53. No holdout computation was run as part of this review.
