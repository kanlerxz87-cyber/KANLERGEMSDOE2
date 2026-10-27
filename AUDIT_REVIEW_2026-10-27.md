# Repository review — 2026-10-27

> **Historical review, superseded in part.** A subsequent independent re-audit and current decision are in [`evidence/focus_reaudit_20261027.json`](evidence/focus_reaudit_20261027.json) and [`run_card.json`](run_card.json). This review was written before dependencies and mirrored inputs were restored; its statements about unavailable local tooling refer to that earlier review only.

## Decision: no current file is authorized for a competition slot

The repository contains substantial prior work and a downloadable GeoTIFF, but its published "OK TO DOWNLOAD & SUBMIT" conclusion is not supported by the repository's own strict protocol evidence. The conservative outcome is **NEGATIVE / DO NOT SUBMIT** until the registry comparison and validator evidence are reconciled. A valid-looking file is not a score, and holdout DTI is not an organizer-confirmed leaderboard score.

### Blocking audit findings

1. **The uniqueness gate is internally contradictory.** `evidence/kg2_run_card_20261026.json` reports the candidate's post-placement overlap against one registry raster as `0.995751` (99.5751%), with the peer identified as `GEMSDOE24:13gems_20261001_r13-lattice-s5_v2_nan-outside.tif`. This exceeds the user-specified 70% limit. Although this peer is classified in the artifact as a space-filling calibration lattice and the artifact separately reports 69.1799% maximum against competing detectors, the stated protocol says *any registry raster*. No exception was provided. Thus the strict lane uniqueness gate fails, and the candidate must be treated as duplicate/drifted under that rule.
2. **The different candidate audit is not interchangeable.** The `KG2-MGHV-EXP-1` writer record in the same run card says `ok_to_upload: false`, `submission_authorized: false`, and `official_format_compliant: false`; the historical receipt did not authenticate the official input. Subsequent local checks match the pinned mirror but cannot determine organizer acceptance. This is not evidence for the HTCADS file, and neither artifact authorizes a slot.
3. **The website's prominent green promotion claims conflict with its evidence.** The root run card records 360 registry rasters, and its literal all-registry overlap fails. The older `evidence/validator_receipt.json` says all five gates pass, but its Gate 3 definition excludes a space-filling control, contrary to the protocol quoted by the user. This is a policy mismatch, not proof of strict uniqueness.
4. **Independent execution is limited in this checkout.** Python has no `rasterio` and `pytest` is unavailable (`pytest: command not found`); therefore this review did not independently reopen the TIFF or rerun the raster tests. The TIFF SHA-256 was checked with `sha256sum` and matches the stored receipt (`f482d3...75abeb`); that proves file identity only, not CRS/range/score.
5. **The site's stated holdout leaderboard projection must not be promoted as a score.** The files report holdout metrics, not organizer receipts. Do not infer a live score above 0.2778, 0.3195, or 0.4413 from these results. Actual score is known only after an organizer receipt/leaderboard entry.

## Nine-site executive summary (user-provided receipts; not independently fetched in this review)

The scores below are reproduced from the supplied brief, therefore are **UNVERIFIED USER/OWNER REPORTS**, not organizer-confirmed receipts. Their exact TIFF identities and uniqueness require the archived registry audit; site score does not imply a unique submission.

| Site | Highest listed submission | Reported score | Review note |
|---|---|---:|---|
| GEMSDOE24 | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | 0.2477 | The brief also lists later lower-score submission 0.0859. |
| GEMSDOE25 | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | 0.2600 | Brief lists a later 0.0742 result. |
| GEMSDOE27 | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | 0.2449 | Later listed entries are 0.2190 and 0.2250. |
| GEMSDOE28 | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | 0.2710 | Highest among the listed 28 entries; nearby variants score 0.2707–0.2708. |
| GEMSDOE30 | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | 0.2600 | A result of 0.1462 is also listed. |
| GEMSDOE31 | `h27-4-solo-d28-20261004-8acb75e1-nan` | 0.2708 | Highest listed for 31. |
| GEMSDOE32 | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | 0.2778 | Highest listed among these nine; not evidence that a new model will score higher. |
| GEMSDOE33 | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | 0.2632 | Higher than the later 0.0963 entry. |
| GEMSDOE36 | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | 0.2750 | Higher than the later 0.1647 entry. |

## Scientific / process review

The highest listed GEMSDOE32 result is consistent with a useful general principle: a sparse prediction set can score better than a dense one when false-positive penalty dominates and the evaluation is tolerant within 300 m. That is a plausible explanation, **not a verified causal reconstruction** of the private leaderboard score. The repository's own artifacts attribute gains in related candidates to pruning catalogue-adjacent predictions and sparse spatial allocation; they do not establish that the 0.2778 score can be surpassed on the private test set.

The historical experiments are already at the stated three-experiment budget. The recorded spatial holdout results in `run_card.json` are `HOLDOUT-DTI (gems-segment-pooled-v1; 60,988 withheld positive pixels; 95% CI 0.1637–0.1908)` for EXP-1, 0.1700 [0.1570, 0.1831] for EXP-2, and 0.1651 [0.1526, 0.1779] for EXP-3. These are the values in the saved run card and were not rerun here. The recorded top experiment is below 0.2778 numerically; the two values are not directly interchangeable because one is holdout and the other is an unverified user/owner report.

The preregistered hypotheses and methods are in `knowledge/01_preregistered_hypotheses_kg2_20261026.md`; further experiments should not be added to that same capped run. The separate future-data ideas (e.g. InSAR and ASTER) are not viable until access, coverage, licensing, preprocessing and spatially blocked validation are demonstrated. No new experiment or external-data claim is made in this review.

## Manual review sources

- Competition overview/rules: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- Competition about: https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/
- Leaderboard: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
- Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
- USGS GeoDAWN dataset: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- GDR submission #1391: https://gdr.openei.org/submissions/1391

## Current run card (strict, fail-closed)

The former illustrative card here mixed the KG2 overlap/holdout with the HTCADS hash. Those measurements concern different artifacts and are not a coherent run card. See [`run_card.json`](run_card.json) for the current HTCADS decision and [`evidence/kg2_run_card_20261026.json`](evidence/kg2_run_card_20261026.json) for the superseded KG2 history. Both are **negative**.
