# Three-pass implementation and verification log

**Date:** 2026-10-26 UTC. **Scope:** current checkout only. No competition model experiment was run.

## Pass 1 — implement

- Inspected the repository and confirmed it initially contained only a minimal README and no project code/data.
- Added a persistent project charter and evidence/decision rules in the README.
- Added an executive-summary GitHub Pages UI with a visible no-submit warning, the nine historical claim rows, unestimable projected leaderboard column, hypotheses, and a step-by-step upload gate.
- Added four preregistered candidate concepts, method distinctions to verify, physical mimics, relative ranking/cost, a source irregularity log, and a negative run card.
- Added a reusable, fail-closed GeoTIFF format checker that compares to a supplied template and checks CRS/grid, EPSG:32611, 100 m, single float32 band, footprint, finite values, and `[0,1]` in-footprint range.

## Pass 2 — bug and assumption review

- Found and corrected a synthetic fixture defect: its valid candidate had not propagated the template's nodata cell, so the new checker correctly rejected it. The fixture now has an exact matching mask.
- Tightened checks to reject a non-`.tif` candidate name, multiband template, empty template footprint, non-EPSG:32611 template, and non-100 m template.
- Verified the checker does not authorize upload: its report scope explicitly excludes holdout, uniqueness, and organizer acceptance.
- Flagged current/archived owner-site status inconsistencies and the mismatch between prompt leaderboard figures and the official public leaderboard snapshot. Do not treat owner-authored pages as receipts.

## Pass 3 — requirement recheck

- Rechecked all nine site IDs and filenames/scores against the supplied prompt; they are labelled `OWNER-REPORTED`, historical, and unverified against bytes/receipts. Cross-site uniqueness is not claimed.
- Rechecked current public leaderboard directly; it displayed 0.4437 for its first row at retrieval. The README and source audit distinguish this public page snapshot from private/final competition results and from a submission receipt.
- Rechecked official problem description for task, metric, grid and format requirements. The official data URL resolves to a login page in the unauthenticated retrieval context; no credentials were requested or used.
- Ran five synthetic unit tests: valid fixture passes; out-of-range, nonfinite in-footprint, transform mismatch, and mask mismatch fail. `py_compile` passes. Missing-data invocation fails closed with exit code 1. `git diff --check` passes.
- Served the project locally on port 8000: `/`, `/docs/`, the experiment plan, and source audit all returned HTTP 200; page content included all nine focus sites and the no-submit warning.
- Final hard result: no official competition inputs/cached stack/evaluator/writer/registry were available. There is no candidate TIFF, no holdout number, no uniqueness pass, no submission name/note, and no submission approval. No competition slot was used. The run card records these as `NOT RUN` / null rather than inventing results.
