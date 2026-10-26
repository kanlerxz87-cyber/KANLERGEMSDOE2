# Three review and fix passes — 2026-10-26

These are performed reviews, not claims that inaccessible organizer data or private truth were checked. They cover the committed code, saved evidence, documentation and dashboard; the stopped scientific probe was not rerun.

## Pass 1 — scientific, protocol, and source audit

- Reopened the nine cited historical TIFFs, verified their SHA-256 and Git blob identity, measured pairwise overlap, and reproduced the D2.8 → B1 → H33-B2 pruning relationships. Classified all nine scores as unverified owner claims and flagged conflicting 28/31 source tables and a future-dated source banner.
- Corrected the reported 37,654-dot lattice bound by adding a visible **post-run erratum**: 82.34%, not the preregistration's 83.34%. Preserved the original sentence for chronology. Kept production-only catalogue exclusions out of the holdout design.
- Reviewed the DTI algebra and rejected the upstream `FP=P-TP` simplification: prediction-side and truth-side proximity terms differ. No hidden-truth inversion or leaderboard projection is claimed.
- Re-read the probe after the stop and disclosed the unsigned-vs-signed implementation deviation and invalid full-catalogue-masked surface canary. Kept only the validly computed individual-feature AUCs as diagnostics, not leakage proof.
- Reproduced the shared zero-truth FP-pooling defect on synthetic arrays, reported it in [upstream issue 41](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41), and kept the shared evaluator unmodified because this account lacks write access. No holdout was run here.

## Pass 2 — integrity, raster format, and fail-closed code

- Locked the historical registry inventory to its nine immutable commits and verified all 378 cached TIFF entries against Git tree blob IDs. The independent verifier repairs same-size-but-wrong cache entries, rejects truncated trees, oversized eligible omissions and path escapes, and does not mutate shared evaluator code.
- Hardened the novelty helper **after** the stopped run: empty registry, undefined rank, non-finite/out-of-range peer pixels, and off-grid resampling cannot produce a blanket uniqueness pass. The existing positive duplicate witness and evidence did not change. Added a persistent guard against restarting this stopped lane.
- Added an independent saved-byte GeoTIFF reader with explicit interior/exterior checks, file and template SHA-256, exact grid/CRS/band/dtype checks and no silent clipping. A historical zero-exterior file passed only the local alternative profile; its portal acceptance and promotion remain unknown/false. Tests cover NaN, infinity, invalid range, wrong grid, wrong dtype and wrong band count.
- Added an explicit null CI, positive count and `planned, not run` evaluator status to the sole negative run card. The actual start time remains unknown rather than fabricated. Reproduction uses pinned package versions and sequential shared-template data restores.

## Pass 3 — dashboard, accessibility, and release readiness

- Tested the rendered static dashboard in headless Chromium at 1440×1000 and 390×844: nine rows, no JavaScript/page errors, no page-wide horizontal overflow; the mobile audit table scrolls horizontally and displays a hint. Added a skip link, semantic headings, readable dated score, and a no-JavaScript fallback.
- Verified all local anchors and data links; historical raster links are labeled research-only. The leaderboard updater rejects unexpected tables and retains the original timestamp on network failure. A real sandbox refresh failed TLS and left the snapshot byte-identical; an Actions runner refresh remains to be observed.
- Ran `python -m pytest -q` (35 passed), `node --test tests/test_leaderboard_script.cjs` (3 passed), shell syntax and Python compilation. Rasterio/affine emitted deprecation warnings; no test failed.
- The repository's existing GitHub Pages configuration was legacy `main`/`/` before publication. A root redirect and `.nojekyll` provide a static fallback; the scheduled GitHub Actions publisher additionally needs Pages set to GitHub Actions. Core GitHub REST rate-limit exhaustion was observed while preparing release; PR, merge, and final live Pages/refresh status must be reported from their actual results, not assumed.
