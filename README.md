# KANLERGEMSDOE2 — evidence-first GEMS submission workflow

> **Maximize P(Win), without inventing evidence. Own the Outcome:** artifact safety, selector eligibility, and permission to submit are separate states.

This repository contains a unique HTCADS candidate GeoTIFF, frozen spatial-holdout evidence, an automated format/registry audit, and a static review portal. It does **not** contain an organizer score receipt for the historic focus-site values. No live slot was selected and no upload was performed in this review.

## Current status snapshot

| State | Result | Meaning |
|---|---|---|
| Format | **FORMAT_SAFE** | Exact template grid, one float32 band, full-array values in `[0, 1]`, no NaN/Inf |
| Download | **OK_TO_DOWNLOAD** | Unique TIFF and single-TIFF ZIP hashes verified |
| Selector | **ELIGIBLE** | Frozen evidence gates passed; not a live slot selection |
| Submission | **NOT_AUTHORIZED** | No slot selected; no upload made |
| Live score | **Not available** | No organizer receipt was fetched or generated |

**Candidate:** [`docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif`](docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif)<br>
**ZIP:** [`docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.zip`](docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.zip)<br>
**SHA-256:** `f482d3bad4b390470be06363b60867c8e42942101271caf4fa82ae3c3975abeb`

**Submission name:** `kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros`<br>
**Note (78/140):** `HTCADS EXP-2; 37,654 pixels; HOLDOUT-DTI GEMSDOE32-HIDE-RECOVER-v3.0; N=22,232`

## HOLDOUT-DTI evidence (not live scores)

- **Primary:** `0.112353` — HOLDOUT-DTI (GEMSDOE32-HIDE-RECOVER-v3.0, N=22232 withheld positives, 95% CI [0.0990, 0.1257]).
- **Secondary:** `0.078913` — HOLDOUT-DTI (GEMSDOE32-SGMC-CAL-v3.0, N=62703 off-catalogue SGMC positives, 95% CI [0.0700, 0.0870]).

Both are pre-existing frozen HTCADS run-card results; this review did not rerun model training or holdout evaluation. They are not projections of an organizer score.

## Historical focus-site values

All values below are **USER/OWNER-REPORTED · UNVERIFIED** and are not current organizer-confirmed standings. No DrivenData submission-page receipt is stored.

| Site | Reported value | Source record |
|---|---:|---|
| GEMSDOE32 | 0.2778 USER/OWNER-REPORTED · UNVERIFIED | [Pinned owner mirror](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/1398109a23f04a2ace71c1bd2f527cfba87860b5/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif) |
| GEMSDOE36 | 0.2750 USER/OWNER-REPORTED · UNVERIFIED | [Pinned owner mirror](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/61783525af4aa6dcf8da0bc68b06fa38b89ed27a/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif) |
| GEMSDOE28 | 0.2710 USER/OWNER-REPORTED · UNVERIFIED | [Pinned owner mirror](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/67dbdf4da84fc92a98dd9644ab816ed18ae36bcc/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif) |
| GEMSDOE31 | 0.2708 USER/OWNER-REPORTED · UNVERIFIED | [Pinned owner mirror](https://github.com/buffedlizard55-lab/GEMSDOE31/blob/abd9a45cc7adf046d7d3829eb6e8c980943f462d/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif) |
| GEMSDOE33 | 0.2632 USER/OWNER-REPORTED · UNVERIFIED | [Pinned owner mirror](https://github.com/buffedlizard55-lab/GEMSDOE33/blob/122e2240a835c9c84831943ee3489dbb48fd6e85/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif) |
| GEMSDOE25 | 0.2600 USER/OWNER-REPORTED · UNVERIFIED | [Pinned owner mirror](https://github.com/buffedlizard55-lab/GEMSDOE25/blob/5a60fb475b7171af93cfce795abe6d96c4021ea2/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif) |
| GEMSDOE30 | 0.2600 USER/OWNER-REPORTED · UNVERIFIED | [Pinned owner mirror](https://github.com/buffedlizard55-lab/GEMSDOE30/blob/3c3d7255fdbb3a94375eff086522463a8eaca449/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif) |
| GEMSDOE24 | 0.2477 USER/OWNER-REPORTED · UNVERIFIED | [Pinned owner mirror](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/2521cb676e172c141a4417e4925b73b6a896c1eb/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif) |
| GEMSDOE27 | 0.2449 USER/OWNER-REPORTED · UNVERIFIED | [Pinned owner mirror](https://github.com/buffedlizard55-lab/GEMSDOE27/blob/4d39bbf92edd51fdf47004df5873793a035592e5/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif) |

**Scientific note on GEMSDOE32's reported 0.2778:** the raster/hash and positive-pixel count can be verified; the score cannot be reconstructed from that file. The former three-point linear inversion was non-identifying and its hidden-set/zero-TP claims have been withdrawn. See the [audit and limitations](docs/irregularities.html).

## Reproduce and verify safely

```bash
python scripts/restore_data.py --group core
python scripts/audit_focus_sites.py
python scripts/validate_submission.py \
  --tif docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif \
  --run-card evidence/run_card.json \
  --zip docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.zip \
  --out evidence/validator_receipt.json
python scripts/evaluate_holdout.py docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif --out /tmp/candidate_holdout.json
```

The last command runs the canonical spatially blocked holdout evaluator on the named candidate; it does **not** train or implicitly launch MTR1. `python scripts/evaluate_holdout.py --verify-kg2` is a read-only compatibility check for archived KG2 files. Do not run any new experiment under the exhausted three-experiment cap.

Tests: `python -m pytest -q` (or `.venv/bin/pytest -q` in the prepared local environment).

## Sources, limitations, and review portal

- [Static review portal](docs/index.html) · [Executive summary](docs/executive-summary.html) · [Research and source links](docs/research.html) · [Audit and limitations](docs/irregularities.html)
- [Tracked per-site audit](evidence/nine_site_audit.json) · [Pinned-raster audit receipt](evidence/focus9_submission_audit_20261027.json) · [Focus-nine CSV](docs/data/nine_site_audit.csv) · [Current status JSON](docs/data/status_feed.json)
- [Official-source register](registry/sources.json) · [Untested hypotheses](knowledge/02_untried_hypotheses_20261027.md)

Competition data and several external layers were restored from owner-controlled GitHub mirrors. SHA-256 pins demonstrate byte integrity against the pinned mirror, not official-host authenticity. Direct official-host source data, current DrivenData standings, and submission receipts were not available to this review. See [`registry/sources.json`](registry/sources.json) for exact verification scope and links.

### PARALLEL-RUN PROTOCOL safeguards

- Keep the unique single-band TIFF on the exact competition grid and values in `[0,1]`.
- Keep format-safe/downloadable, selector-eligible, and authorized-to-submit as separate statuses.
- Before any future test, use spatially blocked whole-segment holdouts and visible-fault-only feature derivation; enforce the 0.90 correlation/AUC and 70% 3-pixel overlap limits.
- Label every model-performance metric `HOLDOUT-DTI` with evaluator, withheld-positive count, and confidence interval, or `ORGANIZER-CONFIRMED` only when copied from an organizer-controlled receipt; label diagnostics as format, registry, or provenance audits.
- Never present or publish a live-score projection. Never select or spend a live slot automatically.
- Read the complete standing project brief and parallel-run protocol in [`PROMPT.md`](PROMPT.md).
