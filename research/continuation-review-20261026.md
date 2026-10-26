# Three-pass continuation review — 2026-10-26

Scope: active branch `arena/b5b715a7-kanlergemsdoe2`, starting at `5211ac0`, then fast-forward-integrating concurrent main `4ff7887` (PR #6). No scientific lane paragraph was provided. Zero new detector experiments and zero competition slots were used. This review does not claim to satisfy the requested high-scoring TIFF deliverable.

## Pass 1 — implement and verify

- Read README, scripts, prior run cards, source pins, nine-site audit and archived E1 implementation. Found unresolved conflict markers in the initial builder/page; PR #6 already fixed these, so integrated it rather than making a parallel repair.
- Attempted the existing pinned core-data mirror through GitHub API. Rate-limit failures were recorded in `evidence/data_restore_api_attempt.json`. Implemented pinned archive transport (selected members only, full SHA256/size verification, atomic installs) and restored all core/external manifest entries without credentials or synthetic fallback.
- Executed data preparation. The 19-band training raster is 418,912,844 bytes and matches the pinned SHA256. All restored TIFF grids match the template. Labels and existing faults are byte-identical, not independent truth. Data remain ignored under `data/`.
- Cached shared whole-component folds with a 15-pixel collar and hashed visible/train/valid/truth masks. The split contains 60,988 scored positive locations. This is a split audit, not HOLDOUT-DTI.
- Executed the unchanged shared `SegmentHoldout.canary` on 39 raw physical channels and 39 corresponding validity masks. All 78 diagnostics pass; maximum pooled/fold AUC across both polarities is 0.6297168688888889. These are LEAKAGE-CANARY diagnostics, not detector performance.
- Archived the competing E1 runner, feature builder, evaluator and writer byte-for-byte. New active entry points use the unchanged pinned `vendor/template` modules. No private metric fork or replacement writer.
- Added daily read-only repository revision monitoring. Scientific evidence and leaderboard claims remain pinned snapshots. Deploy uses the artifact built/tested in its upstream job.

## Pass 2 — bugs, assumptions and edge cases

- Previous `tests/test_submission.py` used free pytest functions, but CI invoked unittest: those two tests never ran. Converted them to discovered unittest methods; actual quarantined raster format and negative-card checks now execute.
- Previous local writer thresholded every input with `>0`, potentially turning invalid positive infinities/out-of-range values into valid-looking ones and destroying probability magnitudes. Active adapter rejects invalid input and preserves valid probabilities, writes through the shared writer, reopens for strict validation, creates an exact single-TIFF ZIP, and refuses automatic publication under `docs/`.
- Added tests for checksum mismatch preserving existing data, path traversal, malformed JSON cards, booleans used as counts, empty notes, inverse-AUC normalization, threshold equality, overwrite refusal, unsafe names, NaN/Inf/range errors and probability preservation.
- Fixed rendering that rewrote the authoritative run card on every build. Builder now reads it and refuses to render an unreviewed positive decision. Regression test confirms unchanged scientific card bytes.
- Inspected the Rasterio NodataShadowWarning: four-channel radiometric TIFFs tag the fourth quantitative channel as alpha while declaring nodata. Recorded color interpretation/mask flags and limitations. Coverage/canaries use nodata masks, not visual opacity. No silent removal of this irregularity.
- Documented incomplete input coverage and ambiguous `tc` physical metadata. A mask or a plausible band name is not evidence of scientific validity.
- Explicitly preserve the metric CLI's limitation: fold prediction arrays alone do not prove that a model used only visible catalogue features. Its output is metric-only and cannot authorize upload.

## Pass 3 — original requirements and clean verification

- Reran all nine historical raster format checks and 72 directed comparisons using locally SHA256-matched original bytes: nine format passes, 72 near-duplicate gate hits. This audit covers selected final rasters only, not full registry surfaces.
- The website retains the nine-site table, historical filenames, unavailable estimates, clear DO NOT SUBMIT decision and submission instructions. Data readiness, canaries, fold hashes and source-revision observation are available near the beginning. No unapproved TIFF or ZIP link is published.
- Four cached-data hypotheses remain ranked, distinguish specific signatures from the archived XG-HGB mechanism, and name non-fault mimics. A new-data hypothesis is not treated as viable merely because a product catalog exists. The exclusive lane is still absent, so the top proposal was not implemented.
- No score projection is manufactured, no prior submission is renamed as new, no dense registry probe is exempted, no format-only gate is called scientific approval, and no weekly slot is spent.
- All 44 automated tests pass locally, active Python parses, shared template SHA256 pins remain unchanged, and local HTML links resolve. Clean-index reproduction is checked before the PR.
- README now leads with current status and executable next steps. The owner's requirements are preserved as a clearly marked condensed standing brief, not a claim of a complete verbatim transcript. Old session narrative is archived instead of contradicting current data readiness.

## Still required

The next scientific run needs an exclusive method paragraph, complete frozen surface/dot registry, and comparable baseline predictions generated fold-locally on the same whole-component split. Raw-channel canaries do not replace transformed-feature/model canaries. Official-origin/permission verification and an authenticated selector/weekly-cap check remain necessary before a real slot. Peer mirror integrity is not organizer authentication. No new approved TIFF, HOLDOUT-DTI result, reliable leaderboard estimate, or receipt exists for this continuation.

## Concurrent-main integration recheck

Before PR #12 could merge, main advanced through PRs #7, #8 and #9. Integrated
`af1b44b` without weakening its quarantine or publication restrictions. Preserved
the full original-prompt appendix added by concurrent main in README. Kept its
legacy-command blocking and retired-result removal, and added compatibility for
its safe `stage(...)` API. Research writes are now restricted to ignored
`data/candidates`, including resolved-path/symlink escape checks; they cannot
publish into arbitrary directories. The explicit fold-array metric CLI remains
metric-only; an argument-free legacy call fails closed. The two independent
historical code archives remain for traceability; no retired scientific assertion
is republished. Final integrated suite: **54 tests pass**, including all concurrent
safety regressions. Clean-index tests/build/link validation were rerun after this
integration. No new detector or competition slot was added during resolution.

A second concurrent-main advance (`000cf5f`, PR #11) added the stopped K2-SCALE
lane, its literal lattice-feasibility audit and an additional dashboard. These
artifacts were retained, not relabeled as this continuation's results. The K2
GEMSDOE33 template-defect receipt concerns a different pinned evaluator from the
GEMSDOE24 raw canaries run here. No affected K2 function was used or privately
patched. The archived E1 lattice audit reinforces its DO NOT SUBMIT decision.

Integrated both dashboards with a visible data-audit link, preserved all K2 tests,
and published the tested root/docs/evidence layout from one build artifact. Range
error guidance now explicitly says the cause is unknown without the rejected file;
a zero-outside variant is troubleshooting only, not proven official compliance.
Final combined checks: **54 unittest tests, 81 pytest tests, and the Node source-feed
edge-case suite pass**. These suites overlap; the counts are not additive. No new
scientific hypothesis experiment or competition slot was used during integration.
