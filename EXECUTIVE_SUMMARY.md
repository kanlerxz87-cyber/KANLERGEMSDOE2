# Executive summary — submission decision

> **DO NOT SUBMIT.** No file is cleared for upload. The [independent replay](evidence/review_20261028_replay.json) confirms the lattice stop; historical proxies do not establish a leaderboard win. The reported scores below are user/owner-reported, not organizer-confirmed. No credible leaderboard estimate is available for a new candidate.

The prior HPTR research TIFF ([download for research only](docs/downloads/kanlergems2-hptr-exp-2-37654dots-20261028T014401Z-675d0ff8-zeros.tif)) is locally finite and matches the owner-mirror grid, but 37,640 of 37,654 dots (99.963%) overlap the lattice within 3 pixels. Its surface and holdout were not replayed. The SGMC-CAL transform relies on an inferred hidden-truth count and is not measured HOLDOUT-DTI. [Archived card](evidence/session3_hptr_run_card_20261027.json).

## 2026-10-29 verification update

- **Status: DO NOT SUBMIT (unchanged).** Independently recomputed from restored bytes: footprint 5,167,373 px; registry control witness (SHA-256 `b4570b40…47dc9b2`) leaves 6,649 px uncovered within 3 px. At 37,654 dots the minimum overlap is **82.34%** > 70%, so every placement is a forced duplicate under the literal rule. [Evidence](evidence/counting_bound_20261029.json) · [script](scripts/verify_counting_bound.py).
- The largest dot count this single control does not force is **22,163**. Using it requires an explicit protocol change from you, plus holdout DTI and checks against all 359 other registry rasters. Neither exists yet.
- Scores in the table below remain USER/OWNER-REPORTED. No leaderboard estimate is produced for any new file.

## Current research file and decision

| Filename / SHA-256 | Research holdout (not a leaderboard estimate) | Literal uniqueness | Decision |
|---|---|---|---|
| [DSLUP TIFF](docs/downloads/kanlergems2-dslup-uniq-q15k-37654dots-20261027T181253Z-c71122d5-zeros.tif) · `8f66f32c56482501808977ac504a0abf517ff75db0af2b56774c0f08d476fbe3` | **HOLDOUT-DTI 0.125925**, `GEMSDOE32-HIDE-RECOVER-v3.0`, 22,232 withheld-positive occurrences, 95% CI [0.112880, 0.138176]. Archived procedure result, not independently replayed. | **FAIL:** 37,647/37,654 dots = **99.9814%** within 3 pixels of one registry lattice. Pre-placement surface not replayed. | **DO NOT SUBMIT** |
| [KG2 historical benchmark](docs/downloads/kanlergemsdoe2-kg2-mghv-exp-1-37654-20261026-f5a469e94b14-zeros.tif) · `cf1d07726f5fb838dc75d9ffa00d5d6b6da7d5120f0362026ca241d454ce3c6e` | **HOLDOUT-DTI 0.177056**, `gems-segment-pooled-v1`, 60,988 withheld-positive pixels, 95% CI [0.163673, 0.190831]. Historical receipt, not independently replayed. | **FAIL:** 37,494/37,654 = **99.5751%** within 3 pixels of the lattice. | **DO NOT SUBMIT** |
| [Parallel PR #34 research TIFF](docs/downloads/kanlergemsdoe2-unique-hypothesis1-binary-20261027.tif) · `f0cb191420da26d19ceccfd65f8987537f714d1b28660f8e3690ff2008a2b539` | Not measured or replayed. | **FAIL:** 37,652/37,654 = **99.9947%** vs lattice; 184 on-catalogue dots. | **DO NOT SUBMIT** |
| [Parallel PR #36 research TIFF](docs/downloads/36GEMSDOE-off-catalogue-blind-geothermal-targeting-20261027T234345Z-2ecaae7a056e-zeros.tif) · `0e7e1da78fb80ba3ce0849cd32967836d4f3d73206426d43435fbe3958a446c4` | Not measured or replayed. | **NOT CLEARED:** 15,000 dots, 66.0% witness overlap, but 5,100 dots placed in lattice gaps to evade the gate, violating the frozen lane; 107 on-catalogue dots. Full registry not verified. | **DO NOT SUBMIT** |

The two historical HOLDOUT-DTI values use different evaluators and populations and cannot be directly ranked. No new holdout has been generated for a paired comparison. PR #36's previously positive card and sidecar are superseded and preserved under `evidence/superseded/`.

[Exact-byte negative validator receipt](evidence/dslup_literal_revalidation_20261027.json) · [current JSON run card](evidence/current_run_card.json) · [full local release audit](evidence/release_audit_20261027.json). Local finite [0,1], shape, CRS and transform checks do not demonstrate portal acceptance or satisfy novelty. Current submission name and note are **not applicable** because no file is approved.

The historical SGMC-CAL 0.098140 number is an unvalidated transform using an inferred hidden-truth count; it is **not** a holdout DTI, a leaderboard score or a promotion gate. No valid leaderboard estimate is available for a new candidate.

## Nine highest reported sites

The following values are USER/OWNER-REPORTED, not organizer-confirmed; submission-page receipts tying hashes to scores were unavailable. Each local file is historical and research only. The overlap column compares the row's dots to its most similar other *focus-site* raster within 3 pixels; this is not a complete-registry clearance.

| Site | Reported score | Leaderboard estimate | Focus-site overlap | Historical download / decision |
|---|---:|---|---|---|
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/) | 0.2778 | Unavailable | 100.00% vs GEMSDOE36 | [Research only](docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif) — DO NOT SUBMIT |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/) | 0.2750 | Unavailable | 97.58% vs GEMSDOE27 | [Research only](docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif) — DO NOT SUBMIT |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | 0.2710 | Unavailable | 100.00% vs GEMSDOE25 | [Research only](docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif) — DO NOT SUBMIT |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/) | 0.2708 | Unavailable | 100.00% vs GEMSDOE25 | [Research only](docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif) — DO NOT SUBMIT |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | 0.2632 | Unavailable | 99.71% vs GEMSDOE27 | [Research only](docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif) — DO NOT SUBMIT |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | 0.2600 | Unavailable | 100.00% vs GEMSDOE30 | [Research only](docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif) — DO NOT SUBMIT |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | 0.2600 | Unavailable | 100.00% vs GEMSDOE25 | [Research only](docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif) — DO NOT SUBMIT |
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | 0.2477 | Unavailable | 100.00% vs GEMSDOE25 | [Research only](docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif) — DO NOT SUBMIT |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | 0.2449 | Unavailable | 98.02% vs GEMSDOE24 | [Research only](docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif) — DO NOT SUBMIT |

### What can explain GEMSDOE32's reported 0.2778?

Its mask equals GEMSDOE25's after 6,436 dots within two pixels of mirrored known faults are removed. Reducing such redundant emitted mass is a plausible mechanism, but no hidden labels, file-specific receipt or original scoring replay are available to establish why the scores differ. GEMSDOE25 and GEMSDOE30 have the same positive mask; GEMSDOE36 includes GEMSDOE32 plus 1,200 dots. These geometric observations are not score verification.

## Submission instructions — future, conditional only

Do not perform these steps with an existing file. First obtain an explicitly authorized method and resolve the registry contradiction, independently replay fold-safe features and baseline with segment holdout, complete every registry and leakage gate, validate against organizer-authenticated data, and check quota in the current account. The selector and all positive evidence are currently missing.

If a future independent selector approves a uniquely named file, verify its exact SHA-256 and the organizer's current one-band float32 [0,1], CRS, resolution, extent, and exterior requirements. Open [DrivenData GEMS](https://www.drivendata.org/competitions/306/competition-doe-gems/) → **Submit → Make new submission**, upload that approved TIFF (or ZIP containing only that TIFF), enter its unique name and the approved ≤140-character note, and retain the receipt. Verify current account-specific weekly quota before uploading; choose **one** final entry for both rounds before the official deadline. This repository does not upload or reserve a slot.

## Explicit limitations

- Core, lattice, features, LiDAR and historical focus files were SHA-checked against owner-hosted mirror records, **not independently authenticated as organizer files**. Official data requires login.
- The rejected file and portal error receipt are unavailable. The official page says null/NaN outside bounds; the mirror has an irregular footprint, whereas the locally checked DSLUP file is finite with zeros outside. Neither exterior encoding is portal-confirmed here.
- The current full registry and archived pre-placement surface/OOF predictions were not independently replayed; a single valid witness proves failure but does not establish the maximum across the fleet.
- No new geological fit, leakage screen, holdout score, TIFF or leaderboard score was produced in this review. Hypotheses and named confounders are in [the preregistration research note](research/2026-10-27_htcads_hypotheses.md).

Sources: [official problem and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf), [known-fault masking clarification](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516), [official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/), and [scientific source catalog](registry/source_catalog_20261027.json).
