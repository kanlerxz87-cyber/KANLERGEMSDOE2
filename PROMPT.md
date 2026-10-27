# Standing project brief and parallel-run protocol

Read this file and `README.md` at the start of every session, together with the user's current instructions. **This is a condensed record, not a verbatim copy of the complete original prompt.** The current run's hard stop and provenance limitations are documented in `run_card.json` and `evidence/focus_reaudit_20261027.json`.

## Arena values

- **Maximize P(Win):** prioritize defensible scientific improvement and expected benefit per scarce submission slot, not cosmetic changes or duplicated predictions.
- **Own the Outcome:** verify through shared automated code, preserve negative findings and provenance, fix root causes, and fail closed rather than imply human inspection is a substitute for a gate.

## Project brief

Review the repository and outstanding prior-session work. Study the highest reported submissions from GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36; compare with the wider supplied registry as far as evidence allows. Explain the reported GEMSDOE32 value of 0.2778 and whether it can be beaten, without calling an unverified report or projection an organizer-confirmed result. Research geothermal/fault discovery using verifiable official sources; flag data, licensing and methodological irregularities.

The highest urgency is to **generate a unique competition GeoTIFF**, not copy a prior submission except for research, and make its automated submit/not-submit verdict prominent and its download easy to find. Resolve the reported “Predicted values must be in range [0, 1]” error by checking a single-band, float32 raster, grid, CRS, shape, transform, values and NaNs. Verify official format wording, especially outside the bounds; no local test guarantees organizer acceptance. Use a unique filename and a note no longer than 140 characters.

Publish an executive-summary website and a table of each priority site, exact historical downloadable file, appropriately labeled score evidence, format status and cross-site uniqueness. Include instructions for a future approved submission, an accessible responsive UI and current, dated source links. Do not imply that historical or negative files are approved.

Before implementing, rank three to five untried geological hypotheses by expected improvement and cost, detailing data layers, transforms, physical mechanism, named non-fault mimic, why a fault may be unmapped, differences from the repository and availability/licensing of free official data. Separate an external-data listing from independently verified official bytes. Do not claim the entire external fleet was checked when it was not.

## Parallel-run protocol

1. **Lane and hard stop:** stay inside the assigned preregistered method paragraph. If rank correlation with **any** registry raster is greater than 0.90, or more than 70% of candidate dots fall within 3 pixels of **any** registry raster's dots, log a duplicate and stop. Check continuous surfaces before placement and final dots afterward. Unknown or undefined comparisons fail closed. Do not create an implicit control-raster exception.
2. **Reuse shared infrastructure:** reuse the cached feature stack, `evaluate_holdout.py`, and `submission_writer.py`; correct shared defects in the template, not private forks. Hold out whole fault segments and buffers, derive all catalogue features solely from the visible faults, mask visible faults pixel-exactly, and compute pooled distance-weighted Tversky with α=0.2, β=0.8 and a 300 m triangular kernel.
3. **Label evidence:** `HOLDOUT-DTI` must state evaluator version, withheld positives and 95% CI; `ORGANIZER-CONFIRMED` must come from a submission-page receipt. A projection is never a score.
4. **Leakage canary:** evaluate every feature alone; AUC above 0.90 is suspected leakage until disproved.
5. **One JSON run card:** record hypothesis, mechanism, named non-fault mimic, holdout DTI and CI, registry correlation and overlap, raster SHA-256, actual validator output including NaN/range/CRS/shape/transform, submission name and note, and `promote` or `negative`. Negative results are deliverables.
6. **Budget and selection:** stop after three experiments or two hours, do not spend a live weekly slot directly, and do not submit a candidate that fails to beat the current comparable holdout best. A separate selector must independently respect the submission-page cap.

Work autonomously and verify facts against trusted sources. Conduct three implementation, review/fix and final accuracy passes; create and merge a pull request to `main` if permitted; report remaining work honestly.

## Current literal stop

All three historical local candidates exceed 99.5% directional dot overlap with the pinned registry lattice. Its 3-pixel coverage also makes the usual 37,654-dot budget mathematically incompatible with the 70% limit. No new candidate, experiment or submission slot was attempted in this session. Do not adjust dots, silently exempt a raster or promote a result unless the protocol owner explicitly resolves the conflict and the independent gates are satisfied.
