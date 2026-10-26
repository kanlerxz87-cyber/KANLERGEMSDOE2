# KANLERGEMSDOE2 — evidence-first GEMS submission desk

**Start every session here, then read `research/run_card.json` and `research/hypotheses.md`.**

## Current executive decision — 2026-10-26 UTC

**DO NOT SUBMIT. There is no approved new competition TIFF.**

Data placement has been completed autonomously from a SHA256-pinned peer mirror.
Raw-feature leakage diagnostics pass. Neither result proves high leaderboard
performance or full-registry uniqueness. No new detector experiment or weekly
submission slot was used in this continuation.

- [Executive comparison: all nine priority sites](docs/index.html)
- [Submission instructions and range-error guidance](docs/executive-summary.html)
- [Ranked hypotheses](research/hypotheses.md) · [current run card](research/run_card.json)
- [Data readiness / band coverage](evidence/data_preparation.json)
- [Raw feature leakage diagnostics](evidence/raw_feature_canaries.json)
- [Official reference implementation](https://github.com/drivendataorg/gems-prize-reference-solution)
- Pages: https://kanlerxz87-cyber.github.io/KANLERGEMSDOE2/

### Historical champion finding

GEMSDOE32's H33 B=2 artifact has the highest **unverified owner-reported** result
among the requested nine sites. Its reported 0.2778 is not an organizer receipt or
a prediction for a new upload. Sparse placement and catalogue-flank pruning are
plausible explanations, not causal proof. All nine selected historical champions
fail the requested near-duplicate rule against each other; GEMSDOE25 and GEMSDOE30
are pixel-identical inside the footprint. These are historical **RASTER-AUDIT**
findings, not a complete-registry certificate. Reusing them cannot meet this request.
See [exact hashes and pairwise measurements](research/raster_audit.json).

The inherited [official-page-check record](evidence/official-page-check-20261026.json)
is timestamped, not a fresh leaderboard verification in this continuation. The
prompt's conflicting leader values must not be used as a calibrated score target.
A public leaderboard snapshot is not a submission-page receipt for our artifact.

## Latest continuation — data placement resolved (2026-10-26, branch b5b715a7)

Read this section **before** the historical session notes above. The merged checkout
was not empty. PR #6's conflict-marker repairs and source review were integrated,
not recreated. This continuation executed **zero detector experiments and zero
competition submissions**. The absent single-method paragraph still prevents
claiming an exclusive parallel lane. No new competition TIFF is approved.

### Completed autonomously

- Restored the **418,912,844-byte, 19-band training raster**, `labels.tif`,
  `existing_faults.tif`, `sample_submission.tif`, and all external entries in the
  pinned manifest. All final bytes match their SHA-256 pins. GitHub API access hit
  a rate limit; pinned codeload archives succeeded without credentials or manual
  data placement. See [restoration](evidence/data_restoration.json) and
  [data/band/coverage audit](evidence/data_preparation.json).
- Data grids match. The footprint has **5,167,373 pixels** (DATA-AUDIT, not a score).
  Core bands have missing cells inside it; LiDAR support is incomplete. Radiometric
  fourth bands carry an alpha display tag despite being quantitative channels;
  nodata masks take precedence. Core `tc` metadata is ambiguous. Neither sample
  values nor the byte-identical labels/catalogue are independent hidden truth.
- Cached whole-component, buffered fold masks under ignored `.cache/segment-folds/`;
  committed their hashes and counts in [segment_folds.json](evidence/segment_folds.json).
  **60,988 withheld pixels** describe this split, not a scored detector run.
- Ran the unchanged shared leakage canary on **39 raw channels + 39 validity masks**.
  Maximum pooled/fold AUC over both polarities: **0.629717**, below the 0.90 flag
  threshold (**LEAKAGE-CANARY**, not HOLDOUT-DTI). All diagnostics passed. This does
  not prove independence, transform safety, prediction quality or novelty.
- Archived the competing E1 runner/evaluator/writer under
  `research/quarantine/e1-legacy/`. Active adapters reuse `vendor/template`
  unchanged. The writer preserves probabilities, rejects NaN/Inf/out-of-range
  inputs, enforces a safe name and 140-character note, and cannot publish into
  `docs/`. Format PASS never authorizes upload.
- Added regression tests for real test discovery, syntax/conflict markers,
  malformed gate inputs, atomic archive validation and probability preservation.
  Site rendering no longer overwrites the authoritative scientific run card.
- Added a read-only daily Git revision monitor and deploys the **built** Pages
  artifact, not a second unchecked checkout. It does not refresh leaderboard scores,
  reinterpret older results, or silently change pinned reference rasters.

### Reproduce this continuation

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHON=.venv/bin/python bash scripts/download_competition_data.sh
.venv/bin/python scripts/prepare_data.py --out evidence/data_preparation.json
.venv/bin/python scripts/audit_feature_canaries.py  # pretraining audit, no detector
.venv/bin/python scripts/run_tests.py
.venv/bin/python scripts/build_site.py
.venv/bin/python scripts/check_site.py
```

All large data/caches remain ignored. Archives are downloaded at pinned revisions
and only selected entries are extracted; checksums fail closed. Mirror obtainability
is verified, but organizer origin and external-data permission remain separate.

### Next-session priorities and unresolved limits

1. Use the supplied method paragraph if one exists in the next request; it is absent
   here. The four ranked in-cache hypotheses in `research/hypotheses.md` remain
   proposals, not lane claims. Do not repeat the archived XG-HGB experiment as new.
2. Freeze the **complete** novelty registry, including surfaces and lattice probes;
   do not exempt dense probes to get a pass. Rebuild a baseline on the same cached
   whole-component folds using only visible catalogue features.
3. Test the assigned candidate's *transformed* features and final model, then use
   the shared paired pooled-DTI comparison. Stop at a duplicate or the three-run /
   two-hour budget. A score projection remains unavailable, not a fabricated number.
4. Only after a positive paired improvement, complete novelty checks and exact-byte
   validation may a separate selector approve a weekly slot. No account/session or
   remaining cap is available here; no portal action is attempted.

The requested unique **high-scoring** submission is still unmet. Data placement
is no longer its blocker. A negative run card honestly records the remaining gates.
The standing brief above is a condensed operational record, not a verbatim archive
of the entire repeated prompt and historical leaderboard list.

## Owner's standing project brief (condensed, not a verbatim transcript)

The request in this session is the source of these requirements. This operational brief preserves its actionable constraints; it does not claim to reproduce the entire repeated original prompt.

1. Focus on GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36. Explain the highest historical submissions, especially GEMSDOE32 H33 B=2. Produce a clear per-site executive table with file, estimated score if defensible, uniqueness and an obvious download/submit decision.
2. Generate a genuinely new single-band GeoTIFF only from a justified, independently validated strategy. Never rename or copy an old submission as a new one. All predictions must be finite in the footprint and in [0,1], with competition-matching CRS, shape and transform. Prefer strict whole-grid-finite output to avoid the reported portal range error. Use a unique name and a note of at most 140 characters.
3. Parallel protocol: remain in the assigned single-method lane. Stop on rank correlation >0.90 or >70% dot overlap within 3 pixels versus ANY registry raster, both before placement and after. Reuse cached features and shared evaluator/writer. Report upstream bugs rather than privately forking. Missing lane/template authority is a blocker, not permission to claim a lane.
4. Hide whole fault segments with a buffer; derive catalogue-based features from visible faults only; mask visible faults pixel-exactly. Evaluate pooled distance-weighted Tversky with alpha 0.2, beta 0.8 and 300 m triangular kernel. Run every feature alone through a leakage canary; AUC >0.90 is leakage until demonstrated otherwise.
5. Label results HOLDOUT-DTI with evaluator version, withheld-positive count and 95% CI, or ORGANIZER-CONFIRMED with an authentic receipt. Do not call a projection a score. Supplied owner reports must remain explicitly unverified rather than being relabeled confirmed.
6. Before implementation, preregister 3–5 geological hypotheses: layers, physical transform/signature, rationale for unmapped faults, difference from existing work, non-fault mimic, expected qualitative benefit and cost. Verify official external-data obtainability before declaring a new-data idea viable.
7. Validate the top assigned candidate against the frozen current holdout best before any weekly slot. Maximum three experiments or two hours. Slot promotion is a separate selector step within the authenticated page's weekly cap. Do not auto-submit.
8. End with one JSON run card: hypothesis, mechanism, named non-fault mimic, HOLDOUT-DTI + CI, registry correlation/overlap, TIFF SHA-256, validator outputs, name/note and promote/negative. Negative outcomes are deliverables.
9. Research official, free public sources. Store provenance, uncertainty, scientific reasoning and reproducible evidence. Distinguish fault prediction from confirmed geothermal vent discovery. No hallucinated literature, receipts, scores, hidden truth or data access. Work autonomously within available permissions, reporting blockers honestly.
10. Provide a clean GitHub Pages site, executive-summary submission guide and clear download status near the top. Automate checks rather than requiring subjective human inspection. Keep freshness explicit; do not call a dated snapshot a live feed.
11. Perform three passes: implement/verify; find and fix bugs/edge cases; recheck against requirements. Create a PR and merge it when checks permit; record remaining work.
12. Core values: **Maximize P(Win)** by weighing tradeoffs and evidence; **Own the Outcome** end-to-end, including negative results and failure disclosure. Winning cannot be guaranteed by local proxy metrics.


## Historical evidence and scientific integrity

Prior E1 results and the earlier withdrawn synthetic-input candidate remain in
`research/quarantine/`, not as website downloads. E1's incomplete-registry check,
noncomparable evaluator and SGMC-ratio projection are not promotion evidence.
The prior implementations are archived byte-for-byte in `research/quarantine/e1-legacy/`.
Active evaluator/writer adapters now use the unchanged pinned GEMSDOE24 template.
Cross-project template authority remains a coordination issue, not permission for
private forks. Original audit notes are in `research/session-history/`.

The four existing in-cache geological hypotheses are proposals, not globally novel
claims. The inherited external-data review documents official catalog metadata,
not successful scene retrieval, legal eligibility or geothermal vent discovery.
The competition target is faults; a detected fault is not a confirmed geothermal vent.

The Git revision monitor is scheduled daily, subject to GitHub Actions availability.
It never silently refreshes historical scores, baseline predictions or registry pins.
It is not a live leaderboard feed. An unavailable remote is reported as unavailable.

## Verification

See [three-pass continuation review](research/continuation-review-20261026.md).
Software fixtures are synthetic unit tests only, never scientific HOLDOUT-DTI.
Large inputs and caches stay in ignored `data/` and `.cache/`, outside Git/Pages.
