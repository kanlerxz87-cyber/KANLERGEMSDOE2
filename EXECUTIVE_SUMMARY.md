# KANLERGEMSDOE2 — Executive summary

## Decision states

- **Format validation:** `FORMAT_SAFE` — single-band float32 TIFF on the sample grid, finite and within `[0, 1]` over the full array.
- **Download:** `OK_TO_DOWNLOAD` — the unique TIFF and single-TIFF ZIP hashes match.
- **Selector eligibility:** `ELIGIBLE` — recorded research gates passed; the full-registry pre-placement surface check is recorded, not reproduced in this review.
- **Submission authorization:** `NOT_AUTHORIZED` — no live slot selected; no upload performed.
- **Organizer receipt / live score:** none verified or available.

## Candidate

- File: `docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif`
- SHA-256: `f482d3bad4b390470be06363b60867c8e42942101271caf4fa82ae3c3975abeb`
- Format audit: one band, `float32`, `3730×3292`, `EPSG:32611`, exact template transform, full-array `[0, 1]`, no NaN/Inf.
- Primary **HOLDOUT-DTI**: `0.112353` — HOLDOUT-DTI (GEMSDOE32-HIDE-RECOVER-v3.0, N=22232 withheld positives, 95% CI [0.0990, 0.1257]).
- Secondary **HOLDOUT-DTI**: `0.078913` — HOLDOUT-DTI (GEMSDOE32-SGMC-CAL-v3.0, N=62703 off-catalogue SGMC positives, 95% CI [0.0700, 0.0870]).
- Both values are frozen run-card results, not rerun in this audit and not live-score projections.
- Submission note (78/140 characters): `HTCADS EXP-2; 37,654 pixels; HOLDOUT-DTI GEMSDOE32-HIDE-RECOVER-v3.0; N=22,232`

## Focus sites and score provenance

The historical values GEMSDOE24/25/27/28/30/31/32/33/36 are **USER/OWNER-REPORTED · UNVERIFIED**. No DrivenData receipt was verified. See [`evidence/nine_site_audit.json`](evidence/nine_site_audit.json) for the per-site raster/hash/format summary, source pins, and candidate comparisons.

The prior `R²=0.998523` inversion used to infer hidden-set size and zero true positives among pruned dots has been withdrawn as non-identifiable from the available score/count pairs.

## Current uniqueness evidence

Current final-dot comparisons were recomputed against the nine pinned focus-site TIFFs: max directed 3-pixel overlap `0.500345` (GEMSDOE27); max absolute final-raster Spearman `0.020971` (GEMSDOE27). The prior full-registry pre-placement surface result `0.179514` against `192` rasters is recorded but not independently reproduced because the pre-placement array was not retained.

## Review and next steps

No new experiment was run; the HTCADS lane has used all three preregistered experiments. The four untested ideas in [`knowledge/02_untried_hypotheses_20261027.md`](knowledge/02_untried_hypotheses_20261027.md) are a research queue only, not a new preregistration or score projection. Official sources and what was actually checked are in [`registry/sources.json`](registry/sources.json). The static site is not a live leaderboard poll and requires a separate user-controlled live-slot decision before any submission.
