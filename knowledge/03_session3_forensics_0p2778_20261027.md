# Session 3 forensics: why GEMSDOE32 reported 0.2778, and what it means for a unique submission

Date: 2026-10-27 · Receipt: [`evidence/session3_independent_recheck_20261027.json`](../evidence/session3_independent_recheck_20261027.json) · Script: [`scripts/session3_recheck.py`](../scripts/session3_recheck.py)

Labels: **VERIFIED** = recomputed from pinned bytes in this session. **OFFICIAL** = stated by the organizer or the official rules (linked). **USER-REPORTED** = a score supplied by the owner with no submission-page receipt. **INFERENCE** = a reading that the evidence supports but does not prove.

## 1. Official facts the analysis depends on

| Fact | Label | Source |
|---|---|---|
| Metric is a distance-weighted Tversky index with α=0.2 (FP) and β=0.8 (FN); triangular kernel, range 300 m (3 px at 100 m). | OFFICIAL | [DrivenData problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) |
| Submission is a single-band `float32` GeoTIFF, EPSG:32611, 100 m, same bounds, values between 0 and 1; data outside the bounds is null or NaN. | OFFICIAL | [DrivenData problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format) · [official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) |
| Three submissions per week. | OFFICIAL | [official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) §3.2 |
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

All nine focus files are binary inside the footprint (values exactly 0 and 1; VERIFIED). Their outside-footprint encoding varies: GEMSDOE24, 25, 27, 28 and 31 use NaN outside, while GEMSDOE30, 32, 33 and 36 use zeros outside. Both encodings carry reported scores (USER-REPORTED), so both appear to be accepted by the portal. The official wording is "null or nan" outside bounds, so zeros are not what the rules describe. Each has a directional 3-px overlap of at least 0.975 with another focus file (VERIFIED; the lowest is GEMSDOE36 vs GEMSDOE27 at 0.9758; see the receipt). The nine files are therefore not unique relative to each other.

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
2. **Uniqueness needs new dots in new places.** The Session-2 DSLUP file is such a placement. Its literal-rule overlap with the lattice is 99.98%, so the literal rule currently rejects it (see §6).
3. **The local evaluator is not calibrated.** It gives the 0.2778 champion a proxy of 0.0992 (HOLDOUT-DTI, historical evaluator, not replayed here), while the owner reports 0.2778 on the organizer metric. Holdout ranks cannot be read as leaderboard estimates.
4. **Only an organizer receipt calibrates the score.** The rules allow three submissions per week. Spending one needs an explicit owner decision, because the literal rule currently forbids any candidate from this line of work.

## 6. The literal-rule conflict, quantified (VERIFIED)

- Lattice `13gems_20261001_r13-lattice-s5_v2_nan-outside.tif` (sha256 `b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2`, 206,895 positive dots) covers **5,160,724 of 5,167,373** footprint pixels within 3 px. **6,649** pixels remain uncovered.
- For N distinct in-footprint dots, overlap is at least N − 6,649. At N = 37,654 this is 31,005 dots, or **82.34%**, which exceeds 70% for any placement.
- The bound drops below 70% only for N ≤ 22,163, and then only if at least 30% of dots fall in the 6,649 gap pixels. That is placement gaming and is not recommended.
- Session-2 candidate `c71122d5`: witness overlap **99.98%** (VERIFIED), Spearman vs witness **0.0005** (VERIFIED, below the 0.90 threshold). Only the overlap rule fails.

## 7. Irregularities found this session (flagged for review)

1. **Status conflict.** The Session-2 card said PROMOTE; `status_feed.json` said `ok_to_submit: false`; the literal rule (PR #25) was still in force. Resolved to NOT OK in the site builder and feed.
2. **Unreproducible "1,201 rasters checked".** `scripts/run_dslup_experiments.py::_collect_registry_rasters_v2` globs `/tmp/explore/GEMSDOE*/…`, which is absent here. The committed registry has 360 entries (359 competitors, 1 control), and 12 registry rasters are restored. The 1,201 figure is therefore unverified.
3. **Validator cannot return OK.** `scripts/validate_submission.py` documents that full-registry replay, pre-placement replay and quota verification are unimplemented.
4. **Score provenance.** The 0.2778 and eight sibling figures are USER/OWNER-REPORTED. No submission-page receipt is stored.
5. **Brief numbers differ from the official page.** The brief quotes 0.4413 (top) and 0.3195; the official page observed on 2026-10-27 shows 0.4544 and 0.3566.
6. **Open PR #33** (`arena/89a5e815-kanlergemsdoe2`) proposes another promotion. It was not reviewed in this session.
8. **PR #34 candidate (`kanlergemsdoe2-unique-hypothesis1-binary-20261027.tif`, sha256 `f0cb1914…b539`, merged from main during this session).** Format passes. Verified: 99.99% of its dots lie within 3 px of the registered lattice (literal duplicate). It has **184** dots on known-fault pixels, not the "0" its note states. Its "<2% overlap vs focus files" does not reproduce: in this repository's directional 3-px metric the largest focus overlap is 21.7%, and the DSLUP overlap is 36.8%. The organizer masks known-fault pixels, so the 184 dots are score-neutral, but the stated claim is false. Its note's "download OK" wording is also superseded by the fail-closed status: the file is a research download only.
9. **The pinned lattice file is a registered competitor raster, not a neutral control.** The brief lists it under 13GEMSDOE with a USER-REPORTED 0.0904. Calling it a "calibration control" is a policy argument, and the owner should decide it explicitly.

## 8. Upload-error note (open)

The owner's earlier upload was rejected with "Predicted values must be in range [0, 1]". The file that was uploaded is not in this repository, so its cause is unknown. Two plausible causes are a NaN outside the footprint, or values outside [0, 1] in the uploaded file. The repository's local check passes for the zero-outside encoding and for NaN-outside encoding (the format audit reports `inside_range_0_1` true for every candidate). Neither local check proves portal acceptance, which needs a submission-page receipt.

## 9. Decision for the owner (no manual inspection is involved)

- **A. Keep the literal rule.** No file from the current line of work is cleared. Work continues on research and on the registry-replay gap.
- **B. Adopt a written, pre-registered control-separated rule** that exempts space-filling calibration rasters from the 70% test. Then the Session-2 file is eligible on that test, pending the still-unimplemented full-registry replay.
- **C. Reduce the budget below 22,164.** Not recommended, because it passes only through placement gaming.

Until the owner chooses, the site reports NOT OK TO DOWNLOAD AND SUBMIT for every file.
