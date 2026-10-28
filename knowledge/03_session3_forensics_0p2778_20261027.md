# Session 3 forensics: why GEMSDOE32 reported 0.2778, and what it means for a unique submission

Date: 2026-10-27 · Receipt: [`evidence/session3_independent_recheck_20261027.json`](../evidence/session3_independent_recheck_20261027.json) · Script: [`scripts/session3_recheck.py`](../scripts/session3_recheck.py)

> **Current decision: research only; do not submit any of the files described below.** This is a historical geometric review, not an authenticated score receipt, protocol change, holdout replay or portal acceptance. The literal all-registry rule has no lattice exception. The current card is [`evidence/current_run_card.json`](../evidence/current_run_card.json).

Labels: **VERIFIED** = recomputed from pinned bytes in this session. **OFFICIAL** = stated by the organizer or the official rules (linked). **USER-REPORTED** = a score supplied by the owner with no submission-page receipt. **INFERENCE** = a reading that the evidence supports but does not prove.

## 1. Official facts the analysis depends on

| Fact | Label | Source |
|---|---|---|
| Metric is a distance-weighted Tversky index with α=0.2 (FP) and β=0.8 (FN); triangular kernel, range 300 m (3 px at 100 m). | OFFICIAL | [DrivenData problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) |
| Submission is a single-band `float32` GeoTIFF, EPSG:32611, 100 m, same bounds, values between 0 and 1; data outside the bounds is null or NaN. | OFFICIAL | [DrivenData problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format) · [official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) |
| Rules mention three submissions per week; staff say the submission-page limit takes precedence. Current account quota was not checked. | OFFICIAL / account unknown | [rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) §3.2 · [staff clarification](https://community.drivendata.org/t/submission-amount-question/11553) |
| Pixels on known USGS/INGENIOUS faults are masked, pixel-exactly (identical to the training fault labels). Predictions near a known fault but far from a new-fault ground-truth pixel are fully penalized; the buffer does not apply to known faults. | OFFICIAL (DrivenData staff, 16 and 21 Sep 2026) | [community thread](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4) |
| New-fault ground-truth pixels can lie within 300 m of a known trace. | OFFICIAL (same thread) | same |
| Public leaderboard observed 2026-10-27: #1 0.4544, #5 0.3566. | OFFICIAL (page observation; not a receipt for any team) | [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) |

## 2. Verified geometry of the nine focus files

Dots are in-footprint pixels with value > 0. "Off-fault" excludes pixels on the known-fault mask (no focus file has dots on those pixels).

| Site | Positive dots | Off-fault dots ≤1 px of a known fault | ≤2 px | ≤3 px | Reported score (USER-REPORTED) |
|---|---:|---:|---:|---:|---:|
| GEMSDOE24 | 60,069 | 5,355 | 8,769 | 11,938 | 0.2477 |
| GEMSDOE25 | 44,090 | 3,891 | 6,436 | 8,607 | 0.2600 |
| GEMSDOE27 | 61,328 | 5,413 | 8,875 | 12,187 | 0.2449 |
| GEMSDOE28 | 37,660 | 0 | 2,353 | 4,377 | 0.2710 |
| GEMSDOE30 | 44,090 | 3,891 | 6,436 | 8,607 | 0.2600 |
| GEMSDOE31 | 40,199 | 0 | 2,545 | 4,716 | 0.2708 |
| **GEMSDOE32** | **37,654** | **0** | **0** | **2,171** | **0.2778** |
| GEMSDOE33 | 41,865 | 1,377 | 3,894 | 6,024 | 0.2632 |
| GEMSDOE36 | 38,854 | 0 | 0 | 2,281 | 0.2750 |

All nine focus files are binary inside the footprint (values exactly 0 and 1; VERIFIED). Their outside-footprint encoding varies: GEMSDOE24, 25, 27, 28 and 31 use NaN outside, while GEMSDOE30, 32, 33 and 36 use zeros outside. Reported scores are not file-linked organizer receipts, so neither exterior encoding is proven accepted by the portal. The official wording is "null or nan" outside bounds; whether it applies to this irregular exterior is not established here. Each has a directional 3-px overlap of at least 0.975 with another focus file (VERIFIED; the lowest is GEMSDOE36 vs GEMSDOE27 at 0.9758; see the receipt). The nine files are therefore not unique relative to each other.

## 3. The 0.2778 lineage (VERIFIED)

- GEMSDOE32 is an **exact subset** of GEMSDOE25 (checked pixel by pixel).
- The dots removed from GEMSDOE25 to make GEMSDOE32 number **6,436**, and **every** removed dot lies within 2 px of a known fault. None lies on a known-fault pixel.
- 44,090 − 6,436 = 37,654, the GEMSDOE32 count.
- GEMSDOE36 (0.2750) keeps every GEMSDOE32 dot and adds 1,200 more (lineage receipt in `release_audit_20261027.json`).

## 4. Why 0.2778? Strongest reading (INFERENCE)

Under the metric, a predicted pixel that is not a masked known-fault pixel and lies more than 300 m from any new-fault ground-truth pixel contributes its full weight to the false-positive term. Dots that hug a mapped trace, but are not on it, are therefore costly unless an unmapped fault sits within 300 m of them. The organizer's own statement that new faults can lie near known traces means these dots are not always worthless, so pruning them is a trade-off, not a free gain.

The reported sequence 0.2600 → 0.2778 matches removing the 6,436 near-trace dots and keeping the other 37,654 dots. That is consistent with pruning reducing false-positive cost more than it reduced true-positive credit. **This is a single reported score, so it is not verified causation.** No receipt exists, and no organizer breakdown of TP and FP is available.

## 5. What this implies for a score above 0.2778

1. **Pruning cannot produce a unique file.** Any subset of GEMSDOE32 has 100% overlap with it, which the literal rule classes as a duplicate. Further pruning therefore adds no novelty.
2. **Different placement is not enough.** Session-2 DSLUP has a different hash and placement, but its literal-rule overlap with the lattice is 99.98%, so the rule rejects it (see §6).
3. **The local evaluator is not calibrated.** Historical proxy evaluations were not replayed here; holdout ranks cannot be read as leaderboard estimates.
4. **Only a file-linked organizer receipt establishes a submitted score.** The rules mention three submissions per week, but the account's current quota is unverified and the literal rule forbids any candidate from this line of work.

## 6. The literal-rule conflict, quantified (VERIFIED)

- Lattice `13gems_20261001_r13-lattice-s5_v2_nan-outside.tif` (sha256 `b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2`, 206,895 positive dots) covers **5,160,724 of 5,167,373** footprint pixels within 3 px. **6,649** pixels remain uncovered.
- For N distinct in-footprint dots, overlap is at least N − 6,649. At N = 37,654 this is 31,005 dots, or **82.34%**, which exceeds 70% for any placement.
- The bound drops below 70% only for N ≤ 22,163, and then only if at least 30% of dots fall in the 6,649 gap pixels. That is placement gaming and is not recommended.
- Session-2 candidate `c71122d5`: witness overlap **99.98%** (VERIFIED), Spearman vs witness **0.0005** (VERIFIED, below the 0.90 threshold). This witness fails the overlap rule; the full registry, pre-placement surface, independent holdout and account quota also remain unverified.

## 7. Irregularities found this session (flagged for review)

1. **Status conflict.** The Session-2 card said PROMOTE; `status_feed.json` said `ok_to_submit: false`; the literal rule (PR #25) was still in force. Resolved to NOT OK in the site builder and feed.
2. **Unreproducible "1,201 rasters checked".** `scripts/run_dslup_experiments.py::_collect_registry_rasters_v2` globs `/tmp/explore/GEMSDOE*/…`, which is absent here. The committed registry has 360 entries (359 competitors, 1 control), and 12 registry rasters are restored. The 1,201 figure is therefore unverified.
3. **Validator cannot return OK.** `scripts/validate_submission.py` documents that full-registry replay, pre-placement replay and quota verification are unimplemented.
4. **Score provenance.** The 0.2778 and eight sibling figures are USER/OWNER-REPORTED. No submission-page receipt is stored.
5. **Brief numbers differ from the official page.** The brief quotes 0.4413 (top) and 0.3195; the official page observed on 2026-10-27 shows 0.4544 and 0.3566.
6. **Open PR #33** (`arena/89a5e815-kanlergemsdoe2`) proposes another promotion. It was not reviewed in this session.
8. **PR #34 candidate (`kanlergemsdoe2-unique-hypothesis1-binary-20261027.tif`, sha256 `f0cb1914…b539`, merged from main during this session).** Format passes. Verified: 99.99% of its dots lie within 3 px of the registered lattice (literal duplicate). It has **184** dots on known-fault pixels, not the "0" its note states. Its "<2% overlap vs focus files" does not reproduce: in this repository's directional 3-px metric the largest focus overlap is 21.7%, and the DSLUP overlap is 36.8%. The organizer masks known-fault pixels, so the 184 dots are score-neutral, but the stated claim is false. Its note's "download OK" wording is also superseded by the fail-closed status: the file is a research download only.
9. **The pinned lattice file is registered.** The brief lists it under 13GEMSDOE with a USER-REPORTED 0.0904. Whatever its historical label, the literal protocol exempts no calibration raster; a selector cannot waive the stop.

## 8. Upload-error note (open)

The owner's earlier upload was rejected with "Predicted values must be in range [0, 1]". The file that was uploaded is not in this repository, so its cause is unknown. Two plausible causes are a NaN outside the footprint, or values outside [0, 1] in the uploaded file. The repository's local check passes for the zero-outside encoding and for NaN-outside encoding (the format audit reports `inside_range_0_1` true for every candidate). Neither local check proves portal acceptance, which needs a submission-page receipt.

## 9. Decision for the owner (no manual inspection is involved)

- **Apply the literal rule.** No file from the current line of work is cleared. Work can continue on data provenance and registry-replay gaps without fitting or placing a new model.
- A future change to the literal rule or budget requires an explicit new user authorization and preregistration; neither the current selector nor this document may supply an exemption.
- Reducing the frozen budget to seek lattice gaps is placement gaming, not a geological validation.

The site reports NOT OK TO SUBMIT for every file.

## 10. PR #36 override (merged to main during this session)

- PR #36 added `36GEMSDOE-off-catalogue-blind-geothermal-targeting-…-zeros.tif` (15,000 dots, SHA-256 `0e7e1da7…a446c4`) and a run card with `verdict: promote`, `ok_to_submit: true`.
- Independent recheck (`scripts/off36_recheck.py` → `evidence/off36_independent_check_20261027.json`): lattice 3-px overlap 66.00%, with 5,100 of 15,000 dots (34%) in lattice-gap pixels; 107 on-catalogue dots (card: 0); max non-lattice overlap vs the 12 restored registry rasters 28.59% (card: 22.37%, not reproduced); holdout DTI not measured.
- Decision: promote **not adopted**. Reasons: no holdout result (the brief requires one before spending a slot); placement chosen to pass the lattice gate (AGENTS.md prohibits); budget reduced to 15,000 from 37,654.
- Authoritative card stays `negative` / `ok_to_submit: false`. Archived promote card: `evidence/superseded/current_run_card_pr36_promote_20261027.json`. `scripts/generate_unique_submission.py` is forced to negative and writes to `evidence/research/`.
- Current decision: the literal rule and frozen budget stand. Keep this artifact for forensic research only; a selector cannot waive either requirement. Organizer-authenticated data and a genuinely fold-safe future evaluation remain unresolved.
