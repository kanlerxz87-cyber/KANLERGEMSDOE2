# Executive summary — 27 October 2026

> **NEGATIVE / DO NOT SUBMIT.** No new TIFF, holdout score or live-slot decision was produced in this review. All linked files are research only. Earlier control-exempt promotion claims are superseded.

[Decision dashboard](docs/index.html) · [Comparison and instructions](docs/executive-summary.html) · [Research hypotheses](docs/research.html) · [Run card](evidence/current_run_card.json) · [Audit](evidence/release_audit_20261027.json)

## Historical nine-site comparison

Scores below are **USER/OWNER-REPORTED** without submission-page receipts. The overlap is the percentage of each row’s dots within 3 px of the named other focus file; it is not a full-registry test. No new leaderboard estimate is available.

| Site / exact research TIFF | Reported score | Nearest focus overlap | Local exterior | Verdict |
|---|---:|---|---|---|
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/) / [`gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`](docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif) | 0.2778 | 100.00% vs GEMSDOE36 | all finite | **Do not submit** |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/) / [`gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif`](docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif) | 0.2750 | 97.58% vs GEMSDOE27 | all finite | **Do not submit** |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) / [`gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif`](docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif) | 0.2710 | 100.00% vs GEMSDOE25 | NaN outside | **Do not submit** |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/) / [`gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif`](docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif) | 0.2708 | 100.00% vs GEMSDOE25 | NaN outside | **Do not submit** |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) / [`GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif`](docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif) | 0.2632 | 99.71% vs GEMSDOE27 | all finite | **Do not submit** |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) / [`gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif`](docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif) | 0.2600 | 100.00% vs GEMSDOE30 | NaN outside | **Do not submit** |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) / [`gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif`](docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif) | 0.2600 | 100.00% vs GEMSDOE25 | all finite | **Do not submit** |
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) / [`gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif`](docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif) | 0.2477 | 100.00% vs GEMSDOE25 | NaN outside | **Do not submit** |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) / [`gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif`](docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif) | 0.2449 | 98.02% vs GEMSDOE24 | NaN outside | **Do not submit** |

## Decision and findings

- A registered spacing-5 lattice leaves 6,649 uncovered footprint pixels. Any 37,654-dot placement has at least 31,005 dots within 3 px: **82.3418%**, above the literal 70% threshold. This bound does not cover all smaller budgets.
- HTCADS overlaps 37,642/37,654 (99.9681%); DSLUP overlaps 37,647/37,654 (99.9814%); the later parallel hypothesis-1 TIFF overlaps 37,652/37,654 (99.9947%) and has 184 on-catalogue positives. All are research only.
- Parallel PR #36 added a 15,000-dot file with 66% lattice overlap, but 34% of its dots were deliberately placed in lattice gaps; its budget was reduced, 107 dots hit the catalogue, and no independent holdout or full-registry check exists. Its prior promotion is retracted: **do not submit**. [Recheck](evidence/off36_independent_check_20261027.json) · [negative validator](evidence/off36_literal_validation_20261027.json).
- GEMSDOE32’s mask equals GEMSDOE25 after removing 6,436 pixels within 2 px of the catalogue. Pruning is a plausible precision explanation for 0.2778, not a proved causal decomposition; hidden truth and organizer receipts are unavailable.
- HTCADS historical **HOLDOUT-DTI 0.112353**, `GEMSDOE32-HIDE-RECOVER-v3.0`, N=22,232 withheld-positive occurrences, 95% CI [0.098995, 0.125743], is not independently replayed or a live-score estimate.
- GitHub Pages uses legacy main-root publishing while an Actions deploy also runs; the Pages-source update was denied (403). The public feed is dated and automatic live delivery is not guaranteed. [Deployment audit](evidence/pages_deployment_20261027.json).
- Range-error cause and organizer acceptance remain unknown. The research TIFFs pass local finite/range/grid checks but use zero exterior, whereas the mirrored sample and official description use NaN/null.
- Four science hypotheses with data availability and confounder controls are in the [research slate](research/2026-10-27_htcads_hypotheses.md). Core, scored and nine focus files restored; 15/30 external entries returned 404. [Detailed availability](evidence/data_availability_20261027.json).

## Future submission instructions — not authorization

Resolve the conflict without quietly changing the gate, preregister the lane, replay all registry, canary and holdout checks, verify the actual account quota and use a separate selector. Only if an exact file is approved, go to the [official competition page](https://www.drivendata.org/competitions/306/competition-doe-gems/), upload that TIFF or its one-TIFF ZIP, enter its unique name and note of at most 140 characters, and save the actual submission-page receipt. Nothing currently qualifies.
