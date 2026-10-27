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

CI found one packaging defect not visible in a populated workspace: the unanchored `data/` ignore excluded the official reference snapshot's empty `data/.gitkeep`, which is included in the provenance manifest. Scoped the ignore to root `/data/`, tracked the marker, and verified all 29 tests against a clean `git archive` checkout. Added machine-readable CI failure annotations without swallowing errors.

---

## KG2-H1 (`FVCA-SUBMOD`) Three-Pass Verification & Forensic Irregularity Log — `2026-10-26 UTC`

### Pass 1: Implement & Verify (`KG2-H1` Geothermal Vent Back-Projection + CELF Submodular Pipeline)
- Restored and SHA-256-verified all 14 official/pinned competition and external public datasets (`features.tif`, `labels.tif`, `sample_submission.tif`, SGMC, USGS Quaternary faults, GeoDAWN `tc`, USGS TIGER roads, DOE GDR #1391 geothermal wells/springs, `2m_temperature_probe_n83geo` `2,782` probes, and `Paleo_geothermal_final.csv` `281` sinter/travertine/tufa deposits) via autonomous `scripts/download_competition_data.sh`.
- Preregistered 5 geological hypotheses (`KG2-H1 .. KG2-H5`) in `research/hypotheses.md` with physical equations, target layers, unmapped-fault capture rationale, named non-fault process mimics, official data obtainability, and expected DTI gain vs compute cost.
- Implemented `scripts/build_features.py` (60-channel feature-major float32 stack `<2.5 GB` RSS) and executed the two-sided single-feature leakage canary (`SegmentHoldout.canary()`, `evidence/canaries.json`): all 60 channels passed (`max(AUC, 1 - AUC) = 0.629717 <= 0.90`).
- Implemented `src/gems/submodular_celf.py` (exact Prentice-Pyke / Elkan-Noto Bayes case-control posterior calibration + Minoux CELF 300 m triangular-kernel submodular coverage allocator) and `scripts/run_experiments.py` (3-arm controlled ablation `EXP-1`, `EXP-2`, `EXP-3` using leak-free 4-quadrant out-of-fold 2-stage Auto-Context `LightGBM` with `extra_trees=True`).
- Generated canonical single-band float32 GeoTIFF `docs/downloads/kanlergemsdoe2-kg2h1-fvca-submod-20261026T235000Z-cab53e1b-zeros.tif` (`3730 × 3292`, `EPSG:32611`, `0` NaN/Inf, `[0.0, 1.0]`, `38,500` off-catalogue binary dots) and single-TIFF `.zip`, setting new local out-of-fold bests on `SegmentHoldout` (`0.169279` vs `0.153670` `E1` and `0.161630` `D2.8 vis-B2`, `4/4` fold wins) and `GEMSDOE32-HIDE-RECOVER-v3.0` (`0.106071` `EXP-2`, `0.106529` `EXP-3 CELF` vs `0.099202`).
- Audited continuous surface and final dots against all 72 unique rasters across the GEMSDOE portfolio (`evidence/uniqueness_fvca_72.json`): passed vs all 9 focus sites (`max 44.74%` 3-px overlap; `33.36%` vs `GEMSDOE32`), triggered Parallel-Run Protocol Rule 1 duplicate stop against `10GEMSDOE`'s dense supervised scarp surface (`80.68%` 3-px overlap), logged transparently, and assigned `verdict = "negative"` (`ok_to_submit = false`).

### Pass 2: Review, Bug Fixes, Edge Cases & Irregularities Caught
- **Memory & Numerical Stability Fixes:** Replaced sample-major `(5.17M, 60)` memmap writes, repeated full-grid `distance_transform_edt(..., return_indices=True)`, and tall `(5.17M, 4)` `np.linalg.lstsq` SVDs with feature-major `(60, 5.17M)` sequential row writes, single precomputed footprint-EDT index maps, and `4 × 4` normal equations (`peak RSS = 2.79 GiB` on `3.8 GiB` / `0` swap host).
- **Irregularities Flagged & Mitigated:**
  - `IR-KG2-TC-MISLABEL`: `features.tif` Band 6 (`tc`) is GeoDAWN Radiometric Total Count (`Spearman = 0.99995`), not magnetic tilt curvature; computed true potential-field tilt derivatives directly from `B04`/`B05`.
  - `IR-KG2-BORDER-CLIFF`: Repaired `3,061` footprint-edge `-3.4028235e38` nodata sentinel cells in `B02–B05` via nearest-interior EDT lookup before computing spatial gradients.
  - `IR-KG2-SCARP-CONVERGENCE`: Documented why unweighted binary classifiers trained on `y = labels.tif` converge onto exposed range-front scarps (`73%–81%` 3-px overlap with `10GEMSDOE H25/H28` and `GEMSDOE32 H45`) and refused Perturb-to-Evade (`IR-A8A-NOVELTY-01`).
  - `IR-KG2-LLI-BIAS-01`: Verified empirically that `LLI-S3` (`(d_cat, d_H19-5)` strata) under-projects non-`H19-5` methods by `0.10–0.17` (`0.1319` vs `0.2336` live on `10GEMSDOE H28`; `0.0747` vs `0.2478` live family on `GEMSDOE70`); labeled strictly as `PROJECTION`.
  - `IR-47-TARGETS` & `IR-47-PRIZES`: Corrected outdated external #1 score (`0.4437` on 2026-10-26 vs `0.4413` Oct 23 snapshot) and prize pool (`$50,000` Initial / `$250,000` Final, total `$300,000`).
- **Cross-Document & Link-Integrity Fixes Caught in Pass 2:**
  - Reconciled `GEMSDOE32` `SegmentHoldout` reporting in `evidence/focus_sites.json` (`0.16163` fold-local `D2.8 vis-B2` reconstruction alongside `0.00671` static-collar-censored score) and synchronized exact 8-hex SHA-256 prefixes across `README.md`, `evidence/focus_sites.json`, and `docs/index.html`.
  - Discovered 18 broken relative links in inherited `docs/lane-e1-xg-hgb.html` pointing outside `docs/` or to quarantined files; regenerated `docs/lane-e1-xg-hgb.html` cleanly from `scripts/build_site.py` and added an automated HTML relative-link test across all `docs/*.html`.
  - Converted `tests/test_submission.py` from plain pytest functions (previously ignored by `unittest discover` in `scripts/run_tests.py`) into full `unittest.TestCase` classes safe on clean CI checkouts without `/data/`.

### Pass 3: Full End-to-End Recheck (CI Idempotency, Clean-Checkout Safety & Snapshot Budget)
- Verified `python scripts/run_tests.py` executes 37 unit tests across `test_audit.py`, `test_gate.py`, and `test_submission.py` with `0` failures/errors.
- Verified `python scripts/build_site.py` runs deterministically in `<0.5s` without requiring `.cache/` or `/data/`, and `git diff --exit-code -- docs research/run_card.json` exits `0` exactly as enforced by `.github/workflows/ci.yml`.
- Verified quarantined TIFFs remain strictly outside `docs/`, the canonical research GeoTIFF passes every format/range/CRS/transform check, and `promotion_gate.py` + `select_submission.py` deterministically enforce `verdict = "negative"` (`ok_to_submit = false`).

