# Executive summary — 2026-10-29 decision

## Decision in one line

**DO NOT SUBMIT.**

| Item | Current status |
|---|---|
| New candidate filename | **NONE** |
| Approved candidate download | **NONE**. Existing downloads are historical research files only. |
| New leaderboard-score estimate | **NOT ESTIMABLE**; No credible leaderboard estimate is supported, and no projection is claimed. |
| Uniqueness | **No candidate exists.** Surface Spearman is not computed; final-dot uniqueness is not applicable, not passed. The complete current registry is not cleared. |
| Approval | **DO NOT SUBMIT** — no `OK TO SUBMIT` path. |
| Experiments / local holdouts / slots used this session | **0 / 0 / 0** |

The frozen `HTCADS-K2` lane fixes the candidate budget at 37,654 dots. One registered witness leaves 6,649 of 5,167,373 footprint pixels outside its 3-pixel halo, forcing at least 31,005 dots to overlap: **31,005 / 37,654 = 82.3418%**, greater than the literal 70% stop. Work stopped before model fitting, a surface, dot placement, holdout, or TIFF. The budget and placement were not changed to evade the gate.

**This is the filename/download/score/uniqueness/approval decision:** there is no new TIFF to download, there is no defensible score estimate, uniqueness was not passed, and no upload is approved. See the [three-pass review](evidence/review_20261029.md), [current-head score/source table](evidence/submission_table_20261029.json), and [current run card](evidence/current_run_card.json).

## Nine highest reported submissions — historical claims, not current standings

The list is the highest reported file/score pair retained in the historical focus-nine snapshot. The current public GitHub `HEAD` for every listed site was refreshed on 2026-10-29; all nine differ from the old pinned artifact ref. A refreshed source HEAD is not a leaderboard check. **No organizer submission receipt binding these scores to the listed raster hashes was found.** “No” in the uniqueness column means high overlap within this nine-file subset, not a complete-registry audit.

| Site | Highest reported claim | Historical file (research only) | Current source HEAD | Score/file evidence status | Leaderboard estimate | Focus-nine uniqueness |
|---|---:|---|---|---|---|---|
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/) | **0.2778** | [B2 TIFF](docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif) · SHA `c55bafc47005…` | [`97597a066d1c`](https://github.com/buffedlizard55-lab/GEMSDOE32/tree/97597a066d1c61d2c226fdba349716f41b30c1c6) | USER/OWNER-REPORTED; no receipt ties score to hash. | Unavailable | **No** — 100.000% within 3 px of G36 |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/) | 0.2750 | [Anderson PINN TIFF](docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif) · SHA `e15891020b9c…` | [`e280188adbbe`](https://github.com/buffedlizard55-lab/GEMSDOE36/tree/e280188adbbe762e6b7ac6f3b8e105e8e7915026) | Owner-reported in current peer registry; no receipt found. | Unavailable | **No** — 97.578% vs G27 |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | **0.2710 — disputed** | [H36-1 TIFF](docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif) · SHA `5556aa1438fd…` | [`9509b73eaf35`](https://github.com/buffedlizard55-lab/GEMSDOE28/tree/9509b73eaf35f66d0b23fce63b2540ceff2a88e0) | Current executive page retains 0.2710 as a supplied claim, but the current registry says current downloads are unscored / no own scored artifact. Current page file variant hash differs. **Not verified as a G28 score.** | Unavailable | **No** — 100.000% vs G25 |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/) | 0.2708 | [H27-4 TIFF](docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif) · SHA `07b6db440535…` | [`06930b9d0347`](https://github.com/buffedlizard55-lab/GEMSDOE31/tree/06930b9d03473a9313094a4f2312c4fc6efd4fbb) | User-reported; no receipt. H27-4 is also cross-attributed to G28 in peer records. | Unavailable | **No** — 100.000% vs G25 |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | 0.2632 | [H33d TIFF](docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif) · SHA `87f857d505e2…` | [`3eaf85efb49f`](https://github.com/buffedlizard55-lab/GEMSDOE33/tree/3eaf85efb49f364b84f8be04e8b084b12d0303b9) | Historical user-reported claim; no receipt. Current PHCONG results are research evidence, not a public score. | Unavailable | **No** — 99.709% vs G27 |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | 0.2600 | [D2.8 TIFF](docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif) · SHA `91eae1ca42ec…` | [`fb1db3727477`](https://github.com/buffedlizard55-lab/GEMSDOE25/tree/fb1db37274776a29dbc48abe55b2e531f2ba6aad) | Owner-reported historical claim; no new organizer score. | Unavailable | **No** — 100.000% vs G30; exact positive-mask match |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | 0.2600 | [D2.8 TIFF](docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif) · SHA `8cf893ead566…` | [`31696c6541cf`](https://github.com/buffedlizard55-lab/GEMSDOE30/tree/31696c6541cfc54620ff850a748c51625461f27f) | Owner-reported historical claim in cross-site ledgers; no receipt found. | Unavailable | **No** — 100.000% vs G25; exact positive-mask match |
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | 0.2477 | [D1.5 TIFF](docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif) · SHA `68d0e2e4fcc5…` | [`5e3fa8ff58ac`](https://github.com/buffedlizard55-lab/GEMSDOE24/tree/5e3fa8ff58acddb2d95a1eed30ca98a40ff14421) | Owner/task-reported; current submission ledger calls the local artifact unscored/not yet live-scored. No exact score/file receipt. | Unavailable | **No** — 100.000% vs G25 |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | 0.2449 | [T-v2 TIFF](docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif) · SHA `33003374335d…` | [`6704fa2a5133`](https://github.com/buffedlizard55-lab/GEMSDOE27/tree/6704fa2a5133e751df2516feb2e32565ad5fc1df) | Historical owner/task-reported claim; no receipt found. | Unavailable | **No** — 98.019% vs G24 |

Every historical file is **research-only — DO NOT SUBMIT**. The stored-value checks in the source table are mirror-byte audits, not portal acceptance. G28’s 0.2710 and G31’s 0.2708 attributions remain unresolved; the reported values are not silently promoted to verified results. All nine current HEADs and per-repository claim notes are recorded in [`evidence/submission_table_20261029.json`](evidence/submission_table_20261029.json).

## What the evidence says about GEMSDOE32's 0.2778

The 0.2778 remains the highest supplied historical claim among these sites, not an authenticated score-file pair and not a causal finding.

- G25 and G30 have identical 44,090-positive masks (XOR 0) and each carry a reported 0.2600.
- G32 B2 has 37,654 positives and matches G25 after removing 6,436 pixels within 2 px of the mirrored known-fault mask. This is consistent with precision-oriented thinning, but does **not** show that pruning caused the reported score difference.
- G36 contains the G32 mask plus 1,200 dots in the recorded lineage and carries a 0.2750 claim. Geometry does not establish a score ordering.
- Hidden labels, a receipt tying 0.2778 to the B2 hash, and an independently replayed organizer evaluation are unavailable. Score/file mismatch, an alternate evaluation, or another submission version remain possible.

A newer GEMSDOE32 peer correction matters for the question of improvement. The initial H51-1 run card reports fold-local re-emission **HOLDOUT-DTI 0.115134 [0.101496, 0.128693]**, evaluator `GEMSDOE32-HIDE-RECOVER-v3.0`, N=22,232, versus a B2 proxy of 0.099202 [0.085951, 0.112668]. The current peer `registry/current_status.json` corrects that **0.115134 is not the downloadable TIFF bytes**. Its saved-byte static recheck reports H51 **0.002289 [0.001847, 0.002676]** versus B2 **0.004515 [0.003837, 0.005278]** under that same evaluator and N; no paired CI for the static difference is supplied. The peer's secondary SGMC-CAL diagnostic is 0.063032 vs 0.064121, with overlapping intervals. The saved H51 candidate also fails its literal r13 calibration-lattice rule (>99% overlap; peer status files differ on the exact percentage). This is peer-reported holdout/audit context, **not our experiment and not a leaderboard score**. It does not support an improvement claim.

The most recent local public-board record is the dated snapshot at 2026-10-28 00:05 UTC (#1 0.4544, #5 0.3566, #25 0.3195). It was not refreshed in this review; it cannot establish current standings or a score/file relationship.

## Geological hypothesis screen

Five physically distinct mechanism families were screened for unmapped-fault relevance, mimics, prior-work differences, costs, and official-source accessibility. **Zero are cleared as novel and eligible**; no feature was fitted and no gain was forecast. The detailed screen is [`research/2026-10-29_focus-nine-hypotheses.md`](research/2026-10-29_focus-nine-hypotheses.md):

1. Cross-strike basement–alteration–conductivity ordering — overlaps local HTCADS/DARP and peer XFRONT/basement-conductivity work.
2. Low-amplitude multi-scale potential-field phase ridges — implemented/reported by current GEMSDOE33 PHCONG and close phase-edge peers.
3. Fault-relative extensional dilation share — overlaps local HTCADS, DARP, FVCA hypotheses/experiments, and related peer work.
4. Alluvial-fan drainage vorticity / knickzones — exact local HTCADS H-K4 and ECPU H-N3 preregistrations; registered/deferred, not “untried.”
5. Seasonal OPERA aquifer-barrier deformation — already a deferred local H-K5/OPERA prior; no current tile/time series is verified.

These are a targeted prior-art review, not proof of global novelty. The local 600-file manifest is dated 2026-10-27 and the 360-raster comparison registry is historical, not a complete current fleet audit. Official data pages were not freshly retrieved; previous source links or owner mirrors do not prove current official bytes, tile coverage, or provenance. The competition `data/` directory is absent.

## Validation and submission gate

No TIFF is approved. Do not upload a historical file or create a different-budget variant. If a future compatible method lane is explicitly authorized after resolving the novelty rule without changing the frozen budget or placement, the minimum path is:

1. Refresh and audit the full raster registry; compute pre-placement surface rank correlation and post-placement final-dot overlap separately against every raster. Require both Spearman limits `<=0.90` and `<=70%` of dots within 3 px.
2. Reuse the cached feature stack/shared writer and holdout tooling. Derive catalogue features only from fold-visible fault segments; withhold whole fault segments with a buffer; mask visible faults pixel-exactly.
3. Use pooled DTI with `alpha=0.2`, `beta=0.8`, and the 300 m triangular kernel. Canary every feature; single-feature AUC `>0.90` is leakage until independently explained.
4. Report every actual result as `HOLDOUT-DTI` with evaluator/version, withheld-positive N, and 95% CI. A projection is never a score. No leaderboard estimate is claimed without a defensible calibration/receipt.
5. Stop after three experiments or two hours. Only a separate selector plus current quota check can authorize a live slot. Validate the exact saved bytes and organizer template; portal acceptance requires an actual receipt.

No manual inspection substitutes for automated validation. Current run card is [`evidence/current_run_card.json`](evidence/current_run_card.json). Historical local artifact reviews and exact-byte audits are preserved separately; none overrides this decision.
