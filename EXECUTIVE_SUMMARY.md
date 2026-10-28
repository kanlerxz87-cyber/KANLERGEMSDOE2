# Executive summary — 27 October 2026

> **No file is currently authorized for submission.** The former Session-2 and Session-1 promotion claims are withdrawn. The literal all-registry rule includes the spacing-5 lattice, so both previous TIFFs are duplicates. No new GeoTIFF, current holdout, leaderboard estimate or live-slot decision was produced in this review.

[Decision dashboard](docs/index.html) · [Nine-site comparison](docs/submission-table.html) · [Research](docs/research.html) · [Current JSON run card](evidence/current_run_card.json) · [Exact-byte recheck](evidence/release_recheck_20261027.json)

## Archived candidates — downloads for research only

| Historical file and SHA-256 | Recorded historical holdout procedure; not replayed here | Directional overlap vs registered lattice | Submit? |
|---|---|---:|---|
| [DSLUP TIFF](docs/downloads/kanlergems2-dslup-uniq-q15k-37654dots-20261027T181253Z-c71122d5-zeros.tif) · `8f66f32c56482501808977ac504a0abf517ff75db0af2b56774c0f08d476fbe3` | HOLDOUT-DTI **0.125925**, `GEMSDOE32-HIDE-RECOVER-v3.0`, 22,232 withheld-positive occurrences, 95% CI [0.1129, 0.1382]; HOLDOUT-DTI **0.098140**, `GEMSDOE32-SGMC-CAL-v3.0`, 62,703 off-catalogue positives, 95% CI [0.0884, 0.1061]. Historical procedures, not independently replayed and not a live score for the final TIFF. | **37,647 / 37,654 = 99.9814%** | **No** |
| [HTCADS TIFF](docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif) · `f482d3bad4b390470be06363b60867c8e42942101271caf4fa82ae3c3975abeb` | HOLDOUT-DTI **0.112353**, `GEMSDOE32-HIDE-RECOVER-v3.0`, 22,232 withheld-positive occurrences, 95% CI [0.098995, 0.125743]. Historical receipt, not replayed here. | **37,642 / 37,654 = 99.9681%** | **No** |
| [PR #34 hypothesis TIFF](docs/downloads/kanlergemsdoe2-unique-hypothesis1-binary-20261027.tif) · `f0cb191420da26d19ceccfd65f8987537f714d1b28660f8e3690ff2008a2b539` | No independent holdout or organizer receipt. | **37,652 / 37,654 = 99.9947%**; **184** on-catalogue dots. | **No** |
| [PR #36 reduced-budget TIFF](docs/downloads/36GEMSDOE-off-catalogue-blind-geothermal-targeting-20261027T234345Z-2ecaae7a056e-zeros.tif) · `0e7e1da78fb80ba3ce0849cd32967836d4f3d73206426d43435fbe3958a446c4` | No independent holdout or organizer receipt. | **9,900 / 15,000 = 66.00%** vs this one witness; **107** on-catalogue dots. | **No**: unapproved reduced budget and deliberate lattice-gap placement; full registry and other gates unverified. |

The [fresh DSLUP validator](evidence/dslup_literal_revalidation_20261027.json) reports a local range/grid pass, but fails literal uniqueness, complete-current-registry, surface, independent-replay and account-quota gates. The historical alternative policy is not authorized. A score estimated from holdout is **not available**.

## Nine focus sites — historical, unconfirmed, research only

Values below are **USER/OWNER-REPORTED**, not organizer-confirmed submission-page receipts. The nearest overlap is the fraction of each row's positive pixels within 3 pixels of another focus file, computed from hash-verified owner mirrors. It is directional and does not establish complete-registry coverage. Full hashes are in the [site table](docs/submission-table.html) and [audit](evidence/release_recheck_20261027.json). No file is recommended for a new slot.

| Site / exact archived TIFF | Reported historical value | Nearest 3-px overlap | Decision |
|---|---:|---|---|
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/) / [`gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`](docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif) | 0.2778 | 100.00% vs GEMSDOE36 | **Do not submit** |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/) / [`gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif`](docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif) | 0.2750 | 97.58% vs GEMSDOE27 | **Do not submit** |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) / [`gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif`](docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif) | 0.2710 | 100.00% vs GEMSDOE25 | **Do not submit** |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/) / [`gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif`](docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif) | 0.2708 | 100.00% vs GEMSDOE25 | **Do not submit** |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) / [`GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif`](docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif) | 0.2632 | 99.71% vs GEMSDOE27 | **Do not submit** |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) / [`gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif`](docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif) | 0.2600 | 100.00% vs GEMSDOE30 | **Do not submit** |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) / [`gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif`](docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif) | 0.2600 | 100.00% vs GEMSDOE25 | **Do not submit** |
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) / [`gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif`](docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif) | 0.2477 | 100.00% vs GEMSDOE25 | **Do not submit** |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) / [`gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif`](docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif) | 0.2449 | 98.02% vs GEMSDOE24 | **Do not submit** |

## What can be concluded about 0.2778?

GEMSDOE32's 0.2778 is the highest *reported* number in this nine-site set, not a verified file-linked receipt. Its positive mask equals GEMSDOE25's after removing **6,436** dots within 2 px of the known-fault mirror. GEMSDOE25 and GEMSDOE30 masks are identical; GEMSDOE36 includes all 32's dots plus 1,200. Pruning is consistent with a possible precision improvement, but these geometric observations neither establish score causation nor reveal hidden truth. Beating 0.2778 may be possible, but no current result or defensible numerical prediction demonstrates it.

The official public leaderboard observed on **2026-10-27** showed #1 **0.4544** and #5 **0.3566** ([source](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)); these are dated public observations, not receipts for these files. Results may change.

## Exact stop, data and limitations

- The registered lattice covers 5,160,724 of 5,167,373 footprint pixels within 3 px; only 6,649 are uncovered. At the frozen 37,654 distinct-dot budget, at least 31,005 must overlap (**82.3418%**), exceeding 70%. This is one decisive witness, not a full-registry replay; it does not prove every smaller raster fails. No exception or budget reduction is authorized.
- Owner-mirror checks verified core, scored and nine focus-site files. The all-group [restore receipt](evidence/data_restore_recheck_20261027.json) recorded **31/46 manifest files verified**, including **15/30 external**, and **15 failures**: 14 missing files from a deleted DEM10 ref and one missing heat-flow CSV. Hashes verify mirror identity, not organizer provenance. `.cache/gems_data` and its prepared feature matrix are not persisted in workspace snapshots.
- No independent holdout, all-feature canary, full current-registry surface audit or current account quota was established. Six declared benchmark run cards and three historical verifier modules are absent, so the current-best same-evaluator inventory remains incomplete and the selector fails closed. No weekly slot was spent in this review. Do not infer available quota or past portal status.
- A separate [distance-transform review](evidence/independent_witness_20261027.json) reproduced the exact lattice counts using an algorithm distinct from the original binary-dilation audit; it did not replay the full registry or a holdout.
- Local TIFF checks found single-band float32, EPSG:32611, 3,730 × 3,292, 100 m grid and whole-array finite values in [0,1]. The mirror sample uses NaN outside its irregular footprint; the prior files use zeros. The old range rejection's bytes and diagnosis are missing. Neither a local pass nor an encoding guess proves organizer acceptance.
- Four ranked, unfitted physical hypotheses with source availability, transforms, named mimics and qualitative benefit/cost appear in the [research slate](research/2026-10-27_htcads_hypotheses.md). They do not override the assigned lane or justify a new experiment before the stop is resolved.

## Future submission guide — not authorization

Only after an explicitly authorized protocol resolution, authenticated official data, literal complete-registry checks, independent fold-safe canaries and holdout replay, exact-byte validation and a separate quota-aware selector approval: open the [official competition](https://www.drivendata.org/competitions/306/competition-doe-gems/), choose Submit → Make new submission, select the approved single-band TIFF (or ZIP containing it), enter its unique name and note ≤140 characters, and preserve the actual submission-page receipt. No approved filename or note exists today. See the [official format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and current rules first.
