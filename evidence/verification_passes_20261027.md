# Three-pass verification record — 2026-10-27 UTC

1. **Implement and verify.** Restored hash-pinned core (4/4), scored (12/12)
   and focus (9/9) mirrors; reproduced the registered-lattice counting bound and
   exact-byte audits; corrected the metric, holdout, writer, restoration, shared
   validator and published decision. Recorded 15/30 external files unavailable.
2. **Review and fix.** Exercised invalid arrays, label grids, negative/empty
   truth, exact identity, restoration failures, legacy bypasses, stale status,
   and site-builder failure ordering. Refreshed official-source inventory and
   checked every focus score is labelled user/owner reported. Found and retracted
   the false claims in parallel PR #34's TIFF and in the old control-exempt gate.
3. **Recheck and fix.** Recomputed the counting audit independently, reverified
   core and scored hashes, checked 99 local HTML links and compiled the source.
   Incorporated concurrent PRs #35/#36 without discarding their artifacts;
   independently rechecked the PR #36 bytes and its 15,000-dot/34%-gap
   construction, and retracted its promotion in the public validation sidecar.
   Preserved its original sidecar byte-for-byte in `evidence/superseded/`.
   Disabled the generator and corrected the historical forensics document.

The parallel PR's recorded suite before the follow-up integration was **75 passed,
1 warning** (rasterio/Affine pending deprecation). `python -m compileall -q src scripts`, `git diff --check`,
`evaluate_holdout.py --verify-kg2` (archived metadata only), the site builder,
and local link checks passed. No model was trained, no new TIFF was emitted by
this lane, no holdout was newly measured, and no live slot was spent. The
parallel PR #36 artifact existed before this integration and is research only.

## Follow-up integration recheck — 2026-10-28 UTC

- The full combined suite passed **96 tests with the restored cache** (one
  rasterio pending-deprecation warning) and **96 tests with an empty data
  directory**. The earlier separate review had recorded 69 passes in each mode.
- The independent distance-transform implementation again matched the lattice
  coverage and all six candidate counts. Both site builds were byte-identical;
  compileall, local-link tests, and diff whitespace checks passed.
- The shared and legacy writers now reject an incorrect reference grid before
  writing and stage/audit TIFFs atomically; a synthetic test confirms a failed
  staged audit cannot overwrite earlier bytes. No competition TIFF was emitted.

This record does not assert organizer acceptance, full-registry replay,
account quota verification, or source authenticity of owner mirrors.

GitHub Pages setting recheck: main-root legacy publication and an Actions deploy
coexist. The attempt to switch to Actions returned HTTP 403 for the integration;
the published feed is not guaranteed current until repository administration
resolves the source. See `pages_deployment_20261027.json`.
