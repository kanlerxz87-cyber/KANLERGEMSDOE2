# KANLERGEMSDOE2 — evidence-first GEMS research

> **Session rule:** read this README and [`docs/research/experiment-plan.md`](docs/research/experiment-plan.md) before every project change. Update the evidence ledger before describing any candidate as better, unique, validated, or ready to submit.

## Mission and values

Build an auditable, mostly automated research and submission-readiness workflow for the DOE GEMS Prize fault-mapping challenge. Aim to improve the probability of winning, but never trade scientific validity, competition integrity, or the truthfulness of a result for a speculative score. **Maximize P(Win** means preserve scarce submission slots for candidates that beat a defensible holdout baseline; **Own the Outcome** means publish negative results, blockers, provenance, and corrections as clearly as successes.

The goal is scientific discovery of unmapped geothermal-relevant faults, not merely reproducing the known catalogue. A hidden expert-labelled fault is the relevant prediction target; a good catalogue-recovery score alone is not proof of discovery or a calibrated estimate of public/private leaderboard performance.

## Hard operating rules (carry forward unchanged)

1. **One method lane per run.** Before placement, compare the candidate's surface to every available registry raster; after placement, compare the final dots. A Spearman correlation magnitude above `0.90`, or more than `70%` of candidate dots within 3 pixels of one registry raster's dots, means duplicate/lane drift: record it and stop. Do not weaken the literal rule to rescue a candidate.
2. **Reuse shared tools; do not fork them.** Reuse the template's cached feature stack, `evaluate_holdout.py`, and `submission_writer.py` once available. Hold out whole fault segments with a buffer; derive every catalogue-based feature from visible faults only; mask visible faults pixel-exactly; evaluate pooled distance-weighted Tversky (alpha `0.2`, beta `0.8`, 300 m triangular kernel). Fix a shared-tool defect once in its canonical template, then report it. This checkout currently contains none of those tools or cached inputs, so do not pretend they were run.
3. **Label every number.** A measured local score must say `HOLDOUT-DTI`, evaluator version, withheld-positive count, and 95% CI. An organizer score must say `ORGANIZER-CONFIRMED` and be tied to a submission-page receipt. Owner-provided site claims are `OWNER-REPORTED`. A projection is never a score; do not project a leaderboard score without a validated calibration model.
4. **Leakage canary.** Test each feature alone on the holdout before trusting a model. Any AUC above `0.90` is leakage until disproven.
5. **Automatic fail-closed decision.** No human geological inspection is a substitute for the computational gates. A file is not authorized to submit unless its scientific holdout, canary, uniqueness, and exact-format gates all pass, evidence is reproducible, and the separate slot selector approves. A format-valid file can still be a scientific negative. When a required gate cannot run, the verdict is **NOT APPROVED / DO NOT SUBMIT**.
6. **Run card and budget.** Each experiment ends in a machine-readable card: hypothesis; mechanism; named non-fault mimic; `HOLDOUT-DTI` plus CI and evaluator details (or explicit `NOT RUN`); surface/final-dot correlation and overlap versus registry; TIFF SHA-256 (or `NOT GENERATED`); format validator output (or `NOT RUN`); submission name/note (or `NONE`); verdict `promote` or `negative`. Maximum 3 experiments or 2 hours per run. Never select or spend a weekly competition slot during hypothesis validation.
7. **No copying or cosmetic novelty.** Do not copy an earlier submission or make an existing raster appear new by renaming, changing nodata, or perturbing it. A genuinely new prediction surface still must pass the uniqueness gates.

## Current review — 2026-10-26

This checkout began with only a 16-byte README and one initial commit. It has **no source code, cached feature stack, competition data, raster registry, evaluator, submission writer, template raster, or previous local run evidence**. The environment initially had no `rasterio`/`numpy`. Competition data are behind DrivenData sign-in; no credentials or authenticated data are present. Consequently no holdout, canary, registry uniqueness test, or reference-grid check can honestly be run here. **No scientifically valid competition TIFF was generated. No file from this checkout is OK to submit.** This is intentional: creating a blank/zero TIFF would not be a valid unique scientific discovery and would repeat a known “zeros” encoding pattern.

The official GEMS problem page says submissions are a one-band `float32` GeoTIFF on the training grid (EPSG:32611, 100 m; matching CRS, bounds and transform), with values in `[0,1]` and null/NaN outside the bounds. It defines distance-weighted Tversky with alpha `0.2`, beta `0.8`, and a 300 m triangular kernel. See the [official problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) for the full specification.

### Focus-site historical comparison (claims supplied in the request)

These values are **OWNER-REPORTED claims transcribed from the user's prompt**, not independently authenticated organizer receipts. They are historical comparisons, not HOLDOUT-DTI and not estimates of future leaderboard results. File names are as provided; this checkout cannot verify/download/hash them. Since they are already prior submissions, **none qualifies as a new unique submission**. Cross-site uniqueness is `UNVERIFIED` until actual raster bytes are audited against the whole registry.

| Site | Highest-listed prior filename | Reported result | Evidence class | Unique new submission? | Decision here |
|---|---|---:|---|---|---|
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif` | 0.2477 | OWNER-REPORTED | Unverified; historical | Do not resubmit |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` | 0.2600 | OWNER-REPORTED | Unverified; historical | Do not resubmit |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif` | 0.2449 | OWNER-REPORTED | Unverified; historical | Do not resubmit |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` | 0.2710 | OWNER-REPORTED | Unverified; historical | Do not resubmit |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif` | 0.2600 | OWNER-REPORTED | Unverified; historical | Do not resubmit |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | `h27-4-solo-d28-20261004-8acb75e1-nan.tif` | 0.2708 | OWNER-REPORTED | Unverified; historical | Do not resubmit |
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` | 0.2778 | OWNER-REPORTED (no receipt in source page) | Unverified; historical | Do not resubmit; benchmark only |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | `h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` | 0.2632 | OWNER-REPORTED | Unverified; historical | Do not resubmit |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` | 0.2750 | OWNER-REPORTED | Unverified; historical | Do not resubmit |

**Highest result in that supplied nine-site list:** GEMSDOE32, 0.2778 OWNER-REPORTED. It does not establish why it scored well, nor whether an untested method can exceed it. The metric favors probabilistic coverage near withheld faults and penalizes false negatives four times as strongly as false positives (`beta/alpha = 4`); this can rationalize why a broad, well-placed map could do well, but the specific causal explanation cannot be established without its raster, official receipt, and evaluator. It is not scientifically responsible to claim a higher expected score from the list alone.

**Leaderboard discrepancy:** the prompt mentions 0.3195 and 0.4413. The [official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) was fetched for this review and displayed a current leader score of **0.4437** at retrieval. This is public leaderboard data, not a private-round or final-prize result. Recheck the official page before relying on it; do not use the prompt's older numbers as current. The linked owner-maintained pages also contain differing archived/current statuses; see the [source and irregularity audit](docs/research/source-audit.md).

## What is implemented in this checkout

- A public-facing static project page at [`docs/index.html`](docs/index.html), with a clear no-file-approved warning, nine-site table, automatic submission instructions, ranked research hypotheses, limitations, and official sources.
- A fail-closed GeoTIFF format checker at [`scripts/validate_submission.py`](scripts/validate_submission.py). It requires a local sample/template raster and candidate; it checks the exact grid, EPSG:32611 and 100 m template, single `float32` band, footprint mask, finite in-footprint cells, and `[0,1]` range. It **does not** measure scientific quality, uniqueness, leaderboard score, or portal acceptance. Install the checker dependencies with `python -m pip install -r requirements-validation.txt`; run its synthetic tests with `python -m unittest discover -s tests`.
- A bounded, preregistered research plan at [`docs/research/experiment-plan.md`](docs/research/experiment-plan.md), a page-by-page [source irregularity audit](docs/research/source-audit.md), and a machine-readable [negative run card](docs/evidence/run-card.json). No experiment is marked as run, and no method is promoted in the absence of the shared template tools/data.
- A [three-pass implementation/review log](docs/research/review-log.md) documenting what was checked and what remains blocked.

## Next work / external limitations

1. Obtain competition data lawfully by signing in to DrivenData and placing `training_features.tif`, `labels.tif`, `sample_submission.tif` (or the currently supplied equivalent), and linked source data into ignored `data/`. This sandbox cannot access the login-gated download, and no authentication is requested or stored here.
2. Import the canonical shared template/evaluator/writer and cached stack into this branch (or connect this project to the canonical source); do not make a private competing implementation. Reconcile the named script interfaces before running anything.
3. Inventory all nine sites' TIFF bytes, source revisions, receipts, run cards, and registry surfaces. The published pages contain differing or updated snapshots and owner claims; preserve dates/hashes and resolve conflicts from artifacts rather than summaries.
4. Reproduce the incumbent and candidate holdouts with whole-segment spatial blocks, exact visible-only feature construction/masking, leakage canaries, 95% paired spatial-block CIs, and strict pre-/post-placement duplicate checks. Use at most three experiments/two hours; no weekly slot until the selector independently approves.
5. Run `python scripts/validate_submission.py --template data/sample_submission.tif --candidate <candidate.tif>` against the actual organizer template. Keep the JSON report and byte hash with the candidate; validate `[0,1]` to prevent the reported range error.

Official/primary references and a manual submit checklist are on the [project page](https://kanlerxz87-cyber.github.io/KANLERGEMSDOE2/).
