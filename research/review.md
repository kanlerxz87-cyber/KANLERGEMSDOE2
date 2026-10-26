# Three-pass verification — 2026-10-26

## Pass 1: implement and verify

- Inspected the entire initial checkout: only README, no previously built pipeline.
- Retrieved recursive trees for all nine priority peer repositories and the organizer reference repository; retained 44 pinned text blobs with SHA-256 provenance.
- Restored nine historical rasters for educational audit, the mirrored sample/catalogue, and seven byte-identical shared-tool files. No competition upload, detector experiment, or new TIFF generation.
- Executed 72 directed final-raster comparisons on the sample footprint; all fail the literal novelty gate. All nine historical finite variants pass strict range/grid checks. Two are footprint-pixel-identical.
- Added static executive summary and submission subpage, research proposals, run card, reproducible restoration/comparison scripts and CI.

## Pass 2: defects and edge cases fixed

- GitHub contents API returns empty content for some larger files. Initial template restoration stopped on a checksum mismatch rather than accepting empty data. Added a Git-blob fallback and empty-payload rejection; restored template hash then matched exactly. This was a transport issue, not evidence that upstream data bytes were wrong.
- Initial source links used blob SHA in the commit position. Corrected to pinned tree revision URLs; blob API and content hashes remain separately recorded.
- Closed an initially unclosed validator file handle exposed by test ResourceWarnings.
- Tested NaN, both infinities, negative nodata sentinel, negative/above-one probabilities, shape/CRS/transform mismatch, multiband input, empty novelty masks/support, shifted duplicates and nonduplicate supports.
- Tested shared writer's explicit invalid-input rejection and round-trip output. No silent sanitization introduced.
- Enforced that format validation never itself authorizes submission. All negative run-card fields use null, not invented numbers.

## Pass 3: requirement and scientific integrity recheck

- Per-site historical filenames/results are distinguished from new-file eligibility. No estimate, official receipt, high-scoring candidate or full-registry novelty certificate is invented.
- No method paragraph was supplied. Four candidate mechanisms are explicitly untested proposals, not claims of exclusive/global novelty. Official new-data obtainability remains unverified, especially raw drainage inputs.
- The nine historical rasters share substantial support. The literal stop-on-duplicate protocol precludes recycling them. No random displacement, metadata change, or renamed copy is offered as a new submission.
- Shared evaluator/writer hashes tested byte-for-byte; synthetic contract fixture checks whole components hidden everywhere. Synthetic tests are not scientific HOLDOUT-DTI results.
- Sources unavailable under the network allowlist are clearly marked unverified, not described as researched. Conflicting leaderboard claims remain unresolved.
- The README is an explicit condensed operating brief, not a claim to preserve the full repeated user prompt verbatim.
- This deliverable does NOT fulfill the requested unique high-scoring competition TIFF: no such file passed the prerequisites, and publishing a fake approved download would violate the stronger protocol. Remaining work is recorded in README and run card.

Verification: 16 automated tests passed locally. Actual nine-raster audit was rerun after restoration; SHA-256 data and all comparisons are committed. File-format PASS is not organizer acceptance or scientific validation. Pages publishing and PR merge are checked separately through GitHub.

## Integration re-review (concurrent main)

Main changed after the initial checkout. Resolved conflicts while preserving prior files under `research/quarantine/`. Inspected generator, canary, evaluator and selector line-by-line: synthetic layers, placeholder AUC, normally distributed pseudo-CIs and hard-coded authorization cannot substantiate the prior promotion. Removed these paths from the active/published pipeline, withdrew the old positive card, retained original bytes privately in Git and replaced the selector with a call to the existing fail-closed gate. Added dependency installation to the inherited Pages workflow and removed its build-error-masking shell fallback. Legacy submission URLs now clearly withdraw authorization. This integration adds prior gate tests to the test suite; final test count is recorded by the CI run rather than the earlier 16-test baseline.

Final integrated verification: 29 automated tests pass locally (16 audit/format/shared-contract tests, 9 inherited fail-closed gate tests, 4 integration safety regressions). Source snapshots and quarantined originals retain their bytes. The original concurrent README is archived as well, so withdrawn claims remain traceable. Local links in active HTML resolve. The downloader and data preparer now fail rather than declaring readiness with missing training data or synthetic masks. The Pages description no longer claims an approved validated submission.
