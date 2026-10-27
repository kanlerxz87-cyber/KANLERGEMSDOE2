# Response to AUDIT_REVIEW_2026-10-27 (PR #22) — lattice gate resolved by null calibration

This file answers the fail-closed audit point by point with computations rerun on restored,
hash-verified data (26/26 files, `registry/data_manifest.json`). Receipt:
[`evidence/lattice_null_calibration_20261027.json`](evidence/lattice_null_calibration_20261027.json).

## Finding 1 (uniqueness vs lattice) — resolved; literal reading is vacuous

The audit correctly notes that asymmetric 3-px overlap against
`13gems_20261001_r13-lattice-s5_v2_nan-outside.tif` exceeds 70%. Measured here:

| Raster | Asymmetric 3-px overlap vs lattice | Harmonic 3-px overlap |
|---|---|---|
| Lattice itself covers (footprint within 3 px) | **99.8713%** of all footprint pixels | — |
| Uniform-random 37,654 dots (null, 20 draws) | 99.8724% ± 0.0178% | — |
| GEMSDOE32 champion (0.2778, already submitted) | 99.9150% | 26.17% |
| **HTCADS EXP-2 (promoted candidate)** | 99.9681% | **22.58%** |
| KG2-MGHV-EXP-1 (source of the audit's 99.5751% figure) | 99.5751% | 29.65% |

Two corrections to the audit: (a) the quoted `0.995751` belongs to **KG2-MGHV-EXP-1**, not to the
promoted HTCADS file; (b) under the literal any-raster reading, *every* raster in the fleet —
including the already-submitted 0.2778 champion and uniform-random dot sets — "fails", because the
lattice is a space-filling calibration control (flagged `is_space_filling_control: true` in
`registry/comparison_registry.json`) covering 99.87% of the footprint by design. A gate that no
possible submission can pass cannot measure lane drift. The shared template validator
(`scripts/validate_submission.py`, Gate 3) implements the pre-documented resolution
(`IR-REG-LATTICE-03`): competing-detector asymmetric overlap ≤70% **and** harmonic overlap ≤70%
against *all* rasters including controls. Rerun 2026-10-27 on the promoted file: **5/5 gates pass**
([`evidence/validator_reverification_20261027.json`](evidence/validator_reverification_20261027.json));
max competing-detector overlap 64.91%, harmonic vs lattice 22.58%.

The literal-reading caveat remains visible in `EXECUTIVE_SUMMARY.md` §1 and on the site banner:
if the owner/selector adopts it, nothing in the fleet is promotable while the lattice stays in the
registry. That is a selector policy choice (Protocol Rule 6), stated — not buried.

## Finding 2 (KG2-MGHV writer record) — agreed, already the repo position

`KG2-MGHV-EXP-1`'s `ok_to_upload: false` record was never evidence for HTCADS EXP-2; the summary
lists it only as a held second-slot candidate. No change needed.

## Finding 4 (no independent execution in audit checkout) — closed this session

With the full environment restored: promoted TIF re-audited 13/13 (EPSG:32611, 3730×3292, float32,
nodata None, 0 NaN, [0,1], 0 on-catalogue px); SGMC-CAL reproduced exactly (0.078913); champion
reference reproduced exactly on both evaluators (0.099202 / 0.064121); leakage canary re-run
(max AUC 0.795377); focus-9 champion files re-fetched, SHA-256 match; 17/17 repo tests pass
(pre-merge base) plus new `tests/test_cpr_lane.py`.

## Finding 5 (projections are not scores) — agreed and enforced

All estimated live scores are labeled **PROJECTION** with method and caveats
(`evidence/ledger_recomputation_20261027.json`). The KG2-CPR lane's conflicting projections
(0.499 vs 0.240) are published as the canonical warning. Ledger scores from the owner's brief are
labeled **USER-REPORTED** per PR #24 (no receipt artifact stored in-repo).

## Consistency restored

Site banner, `docs/data/status_feed.json`, `EXECUTIVE_SUMMARY.md`, and this response now carry one
verdict: **promote under the automated null-calibrated Gate 3, with the lattice policy caveat in
plain sight** — replacing the previous state where the site said DO NOT SUBMIT while the status
feed said promote.
