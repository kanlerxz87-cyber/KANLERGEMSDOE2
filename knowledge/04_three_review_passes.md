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
- Verified all local anchors and data links; historical raster links are labeled research-only. An initial local updater prototype retained the timestamp on a TLS failure. A later concurrent safety review prohibited automated DrivenData monitoring, so that prototype and the scheduled refresh were removed before release; the snapshot is static and explicitly dated.
- Ran `python -m pytest -q` (35 passed), `node --test tests/test_leaderboard_script.cjs` (3 passed), shell syntax and Python compilation. Rasterio/affine emitted deprecation warnings; no test failed.
- The repository's existing GitHub Pages configuration was legacy `main`/`/` before publication. A root redirect and `.nojekyll` provide a static fallback; the scheduled GitHub Actions publisher additionally needs Pages set to GitHub Actions. Core GitHub REST rate-limit exhaustion was observed while preparing release; PR, merge, and final live Pages/refresh status must be reported from their actual results, not assumed.

## Concurrent-main integration follow-up

While the PR was being opened, five earlier parallel PRs landed on `main`. Their research, source snapshots, prior safety decisions and quarantined TIFFs were preserved; the full original user prompt was recovered into the README. The former generated dashboard is explicitly labeled as a historical archive, and its guide was corrected not to claim zero-outside portal acceptance. The old site builder was adjusted to generate that archive without overwriting the new decision dashboard. Data-entrypoint and earlier README snapshots are retained under `research/concurrent-main-snapshot/`.

The first combined `pytest` run accidentally discovered two archived vendor test files with unavailable imports; a `pytest.ini` test-path boundary now excludes quarantine and keeps active tests. After integration **73 pytest tests and 3 JavaScript tests passed**, plus all 38 prior unittest contracts. Existing archived materials do not authorize a submission, and no additional experiment or slot was used by this lane.

A further concurrent safety PR (#8) landed during integration. Its explicit E1 withdrawal and stale-route regression test were preserved. Final combined local verification after that merge: **74 pytest tests, 39 legacy unittest tests, and 3 JavaScript tests passed**; the archive build remained deterministic. No parallel branch was checked out or pushed by this session.

A subsequent concurrent K2-SCALE safety PR landed during the final merge attempt. We preserved its separate mathematical stop, evidence, prompt transcription, GitHub-head freshness feed, tests, and root dashboard; the H1 report is linked as a separate audit. The merged repository rules prohibit automatic DrivenData monitoring, so the leaderboard is now a dated static observation with a direct official link. No candidate or slot was created in either stopped lane. Integrated verification after this merge: **94 pytest tests, 39 prior unittest contracts, 3 JavaScript tests plus the GitHub-feed cases**, and both deterministic site builders passed. The exact-original prompt has two differing transcriptions; both are retained rather than silently declaring one canonical.

## Integration review: PR #12 data restoration (2026-10-26 UTC)

- Merged the later peer-mirror restoration, 39 raw-channel and 39 missingness canaries, whole-component folds, fail-closed writer/gate hardening and independent public-GitHub source-head freshness checks. Their max canary AUC was 0.629717, not a held-out DTI or proof that transformed/fitted features are leakage-free. Preserve their separate authoritative run card; none overrides H1’s negative decision.
- Keep all three dashboards available: the K2 root, the current data-readiness desk at `docs/index.html`, and H1 at `docs/h1-audit.html`. Kept the latest upstream data-preparation entry point, moved H1’s separate shared-stack helper to `scripts/build_shared_stack.py`, retained both README/prompt snapshots, and rebuilt the sites.
- Reused local SHA-verified mirror bytes to populate ignored `data/`, then ran the latest download/preparation entry point successfully; provenance remains peer-mirror, not organizer-authenticated. No experiment or slot was consumed.
- Integration checks: 112 pytest tests and 54 inherited unittest contracts passed; three Node UI tests and GitHub-feed offline/rate-limit cases passed; both deterministic builders, local link audit and desktop H1 navigation passed. Scheduled monitoring checks only public GitHub revisions, never the DrivenData site.

## Post-merge safety recheck — saved-byte masks

- A synthetic 2×3 reproduction showed that finite zero pixels with TIFF metadata `nodata=0` could be masked inside the footprint while both local read-back validators incorrectly reported a format pass. This was a software contract test, not a geological experiment or competition result.
- Hardened both repository-owned validators (without modifying or forking the pinned shared writer): require valid in-footprint GDAL masks, reject external candidate/template sidecars, and verify candidate and template hashes are stable across the audit. The whole-grid validator also checks TIFF driver, float32 single band, EPSG:32611 and an unambiguous reference footprint. Added tests for finite nodata sentinels, internal/external masks, ambiguous templates and mutation during validation.
- Re-audited the same historical H33 research-only zero-outside file. Its saved bytes and grid pass the stricter local profile with zero masked interior pixels; portal acceptance remains unknown, the official outside-footprint encoding remains unresolved, and this is not a candidate or selector approval.
- Post-fix verification: **118 pytest tests**, **54 unittest contracts**, 3 Node UI tests, GitHub-feed edge cases, deterministic builders and local link checks passed. No scientific experiment or competition slot was used in this recheck.
