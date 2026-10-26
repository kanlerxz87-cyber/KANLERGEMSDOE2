# Follow-up pipeline review — 26 October 2026 UTC

## Decision

**Negative; no new detector experiment, submission TIFF, leaderboard estimate or competition upload.** No exclusive single-method paragraph is identifiable in the current request. This is not permission to appropriate another session's lane. The four preregistered proposals in [hypotheses.md](hypotheses.md) remain untested. No new official-source scientific findings are claimed by this code review.

## Pass 1 — inspect and contain

The checkout at `5211ac0` already contained a nine-reference audit. Contrary to the prior README's implication that conflicting pipelines were fully removed, several remained active:

| Finding from local source inspection | Consequence | Change |
|---|---|---|
| `scripts/run_experiments.py` built three detectors using the separate `src/gems/metric.py`, quadrant splits and a full-catalogue negative mask | Incompatible with the required shared whole-segment hide-and-recover contract; hidden labels influence negative selection | Original archived; entry point now exits with BLOCKED before imports/data access |
| `scripts/evaluate_holdout.py` evaluated already-generated global masks with the GEMSDOE32 evaluator | Does not establish fold-local generation or comparable baseline improvement | Original archived; entry point blocked pending lane-specific shared-template integration |
| `scripts/submission_writer.py` transformed `np.load(mask)>0` to binary values | NaN or negative values become false; positive infinity becomes true, hiding invalid model output | Replace with direct call to pinned shared writer; preserve probabilities and reject invalid footprint predictions |
| Legacy writer defaulted to `docs/downloads` and generated a file/ZIP without scientific gates | Could publish unapproved research as a submission download | Stage only under ignored `data/candidates/`; no ZIP, release, upload or publication; report explicitly negative |
| `scripts/build_site_e1_xg_hgb.py` contains unresolved merge markers and stale download/estimate claims | Broken executable and potential misleading alternative site | Original archived; compatibility alias invokes only canonical site builder |
| `src/gems` competes with the pinned shared package | Import order can silently select a different evaluator | Original modules archived; active shared implementation remains byte-identical |
| Several incompatible result JSONs remain in `evidence/` | Readers could mistake retired numbers for current evidence | Archived together with original generators; no numerical claims promoted |
| Function-style tests in `tests/test_submission.py` were not discovered by `unittest` | Prior claimed test coverage did not include these tests | Archived; new discoverable unittest safety contracts cover active staging code |

Original bytes are retained under `research/quarantine/session-5211ac0/`. They are **not validated scientific results**. Other historical quarantines remain unchanged. This is containment, not a working training pipeline.

## Pass 2 — edge cases and fixes

- Gate rejects non-object run cards and malformed nested sections rather than crashing. Boolean withheld-positive counts are not accepted as integers.
- Staging rejects malformed names, blank/long notes, wrong shapes, nonfinite or out-of-range footprint values, overwrites, output paths outside staging, and symlink escapes.
- Staging retains soft probabilities and reopens the TIFF for whole-grid range/grid checks. All authorization flags remain false even for passing fixtures.
- Shared-template byte hashes and scientific contract tests remain unchanged. No private evaluator fork was created. No shared-template defect was established or modified.
- CI compiles active Python modules as well as running tests, catching previously untested syntax failures. The branch trigger now names this session branch. Pin scikit-learn to the version installed for this review.

## Pass 3 — scientific and requirements check

The historical raster measurements are inherited, not rerun here; no new full-registry or surface uniqueness claim is made. They establish that the selected champions are too similar for the requested novelty protocol, not why a particular hidden leaderboard result occurred. GEMSDOE32's reported advantage could arise from point density, catalogue-flank exclusion and hidden-set coverage; a controlled ablation on frozen folds would be needed to separate those effects. Geological sophistication alone is not evidence of improved distance-weighted Tversky. A sparse geometry change can alter that metric without finding a new geothermal vent. Fault prediction and vent discovery must remain distinct.

The supplied highest-score claims conflict, and no organizer receipt resolves them. The historical 0.2778 is still an unverified owner report. It cannot calibrate a reliable new leaderboard estimate. The official reference source is pinned in [source_manifest.json](source_manifest.json): https://github.com/drivendataorg/gems-prize-reference-solution . This review does not claim freshly verified access to DrivenData, USGS, Dropbox, or the NLR paper; these hosts are outside the environment's outbound allowlist.

### Exact next-session sequence

1. Obtain the parallel coordinator's exclusive lane and resolve shared-template authority without changing branches.
2. Restore and hash-check required caches, catalogue and template. External rasters are present locally, but primary training/sample/catalogue placement is incomplete; file presence alone does not establish origin, band identity, footprint or fold-local validity.
3. Freeze complete registry **surfaces and dots**, segment splits, buffers and current-best fold predictions. Nine selected historical final rasters are not a complete registry.
4. Implement only the assigned mechanism using the shared evaluator and writer. Construct every catalogue-dependent feature from visible faults; run each feature's holdout canary; stop on leakage or duplicate thresholds before placement.
5. At most three experiments or two hours. Publish pooled HOLDOUT-DTI, withheld-positive count, evaluator hash/version, spatial 95% CI and paired improvement CI against the current best. Only then stage a candidate and check final-dot novelty.
6. A separate selector verifies exact artifact bytes and authenticated remaining weekly allowance. No automated slot was spent here.

The full repeated owner prompt has **not** been preserved verbatim; README contains a condensed standing brief. This remains an unmet documentation request rather than a false claim of completeness.

### Final verification record

A final publication sweep found the same conflict markers and stale experiment
claims in `docs/lane-e1-xg-hgb.html`, as well as published copies of the retired
result JSONs. Archived those bytes and replaced the old lane URL with a clear
withdrawal notice. Regression tests now scan published files for these markers
and prohibit the retired result filenames. No historical evidence was deleted.

Local verification: 38 discovered unittest tests pass; active Python compilation
passes; site generation is deterministic. `prepare_data.py` returns exit 1 with
all three required primary rasters absent. This is an expected blocker result,
not a successful data restoration. The inherited historical-raster audit was not
rerun. The installed dependencies and synthetic safety contracts do not validate
any candidate against hidden faults.

### Concurrent-main integration

Merged `origin/main` at `4ff7887` on the fixed Arena branch. Retained its additional
external-data hypothesis/source-screen documents and dated official-page observation
record. These records were produced by the concurrent session, not independently
re-fetched here. Preserved this safety review's negative audit run card and research
writer restrictions. Removed the obsolete hyphenated run-card alias as main did;
canonical `run_card.json` remains linked. No inherited observation is a project
submission receipt or a new experiment.
