# Executive summary — submission decision

> **DO NOT SUBMIT.** No file is cleared for upload. The [independent replay](evidence/review_20261028_replay.json) confirms the lattice stop; historical proxies do not establish a leaderboard win. The reported scores below are user/owner-reported, not organizer-confirmed. No credible leaderboard estimate is available for a new candidate.

The prior HPTR research TIFF ([download for research only](docs/downloads/kanlergems2-hptr-exp-2-37654dots-20261028T014401Z-675d0ff8-zeros.tif)) is locally finite and matches the owner-mirror grid, but 37,640 of 37,654 dots (99.963%) overlap the lattice within 3 pixels. Its surface and holdout were not replayed. The SGMC-CAL transform relies on an inferred hidden-truth count and is not measured HOLDOUT-DTI. [Archived card](evidence/session3_hptr_run_card_20261027.json).

## 2026-10-29 status — read this first

**Answer to "which file can I submit?": none.** Every file for the nine focus sites fails the user's literal uniqueness rule, and the gate cannot be cleared at the lane's frozen 37,654-dot budget. The gate outcome below is a proof, not an opinion: it was re-derived on 2026-10-29 by an independent script and receipt ([`scripts/verify_budget_bound_20261029.py`](scripts/verify_budget_bound_20261029.py) → [`evidence/budget_bound_20261029.json`](evidence/budget_bound_20261029.json)).

**Why the gate is unavoidable at 37,654 dots.** A single registry witness (`13gems_20261001_r13-lattice-s5_v2_nan-outside.tif`, SHA-256 `b4570b406efe…`, 206,895 positive cells) lies within 3 px of **5,160,724 of 5,167,373** footprint cells. Only **6,649** cells lie outside that zone, so at least 37,654 − 6,649 = **31,005 dots (82.34%)** must fall within 3 px of it. The rule fails above 70%. The re-derivation agrees with the earlier replay ([`evidence/preflight_replay_20261028.json`](evidence/preflight_replay_20261028.json)).

**What would change this.** The 37,654 figure is not a competition rule. It is GEMSDOE32's dot count, which this lane copied. For the single witness alone, the largest budget that passes is **22,163 dots**. The full 360-raster registry could lower that further. Reducing the budget changes the lane, so it needs your explicit approval; it has not been done.

| Site | File to download | Estimated leaderboard score | Unique vs. the other focus sites? | Decision |
|---|---|---|---|---|
| GEMSDOE32 | [gemsdoe32-h33-…-zeros.tif](docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif) | None (user-reported 0.2778; no receipt) | **NO** — 100.00% within 3 px of GEMSDOE36 | **DO NOT SUBMIT** |
| GEMSDOE36 | [gemsdoe36-anderson-…-zeros.tif](docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif) | None (user-reported 0.2750; no receipt) | **NO** — 97.58% within 3 px of GEMSDOE27 | **DO NOT SUBMIT** |
| GEMSDOE28 | [gems28-h36-1-rung30-…-nan.tif](docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif) | None (user-reported 0.2710; no receipt) | **NO** — 100.00% within 3 px of GEMSDOE25 | **DO NOT SUBMIT** |
| GEMSDOE31 | [gemsdoe31-h27-4-solo-d28-…-nan.tif](docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif) | None (user-reported 0.2708; no receipt) | **NO** — 100.00% within 3 px of GEMSDOE25 | **DO NOT SUBMIT** |
| GEMSDOE33 | [GEMSDOE33-h33d-…-cb490425926e.tif](docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif) | None (user-reported 0.2632; no receipt) | **NO** — 99.71% within 3 px of GEMSDOE27 | **DO NOT SUBMIT** |
| GEMSDOE25 | [gems25-dotted-h19-5-d2-8-…-nan.tif](docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif) | None (user-reported 0.2600; no receipt) | **NO** — 100.00% within 3 px of GEMSDOE30 | **DO NOT SUBMIT** |
| GEMSDOE30 | [gemsdoe30-d28-poisson300m-…-91eae1ca.tif](docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif) | None (user-reported 0.2600; no receipt) | **NO** — 100.00% within 3 px of GEMSDOE25 | **DO NOT SUBMIT** |
| GEMSDOE24 | [gems24-h25-1-dotted-…-nan.tif](docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif) | None (user-reported 0.2477; no receipt) | **NO** — 100.00% within 3 px of GEMSDOE25 | **DO NOT SUBMIT** |
| GEMSDOE27 | [gems27-topo-gap-closure-…-nan.tif](docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif) | None (user-reported 0.2449; no receipt) | **NO** — 98.02% within 3 px of GEMSDOE24 | **DO NOT SUBMIT** |

The overlap column is the nearest *focus-site* raster only, from [`evidence/preflight_replay_20261028.json`](evidence/preflight_replay_20261028.json). It is not a full-registry check. **No row has a validated leaderboard estimate**, and the user-reported scores are not organizer receipts.

**Decision needed from you (not taken autonomously):**
1. **Approve a budget change** (for example ≤22,163 dots) to the lane. Then the full registry, a surface rank check, per-feature leakage canaries and a whole-segment holdout must all pass before any file is generated. None of these exist for a new file yet.
2. Or **accept a negative result**: no file is cleared, and the highest reported focus-site score (0.2778) remains unmatched by any validated submission.

**Irregularities for review (flagged, not resolved):**
- The request cites 0.3195 as "the highest score right now" and 0.4413 as the leaderboard high. The stored public snapshot ([`docs/data/public_leaderboard.json`](docs/data/public_leaderboard.json), observed 2026-10-28) has rank 1 = **0.4544** and rank 25 = **0.3195**. The two figures are not reconciled, and this sandbox cannot reach DrivenData to refresh them.
- Positive-cell counts disagree between sources. The 2026-10-28 replay counts cells with value `> 0` (for example GEMSDOE24 = 60,069). The older knowledge note counts `>= 0.5` (85,729). Any threshold-based claim needs one fixed definition before it is used.
- Sources are owner mirrors (SHA-pinned), not organizer-authenticated; the DrivenData data page requires login and was not reachable.

[Independent budget-bound receipt](evidence/budget_bound_20261029.json) · [Replay receipt](evidence/preflight_replay_20261028.json)

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
