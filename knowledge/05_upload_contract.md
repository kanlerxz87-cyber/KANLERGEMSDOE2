# Upload contract and range-error investigation

## Current instruction: DO NOT SUBMIT

There is **no approved submission TIFF or ZIP** to download. This H1 lane produced no TIFF; research artifacts from parallel lanes remain quarantined. `docs/data/run-card.json` is the one negative run card, not a submission. Links to other sites' rasters are research references only and fail this checkout's literal novelty comparisons. The following checklist is conditional documentation for a *future* candidate, not authorization to select a slot.

## What the organizer says

The [published specification](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format) requires one float32 band on the training grid, projected CRS EPSG:32611, 100 m resolution, matching bounds, confidence values in [0,1], with null/NaN outside the bounds. The mirrored template grid is 3,730 rows × 3,292 columns, affine `(100, 0, 243350, 0, -100, 4508550)`. A ZIP is only an option if the portal itself accepts that extension; verify the current interface and use one TIFF inside. No organizer receipt for this checkout exists.

## How to validate actual bytes

Once a different, duly assigned lane has passed its independent science and uniqueness gates, use the **shared** `submission_writer.py` to write its new candidate, then independently reopen the exact on-disk `.tif` (do not just examine the in-memory array):

```bash
.venv/bin/python scripts/validate_saved_tiff.py path/to/new-candidate.tif \
  --template .cache/audit/core/sample_submission.tif \
  --outside nan --out path/to/byte-validation.json
```

The command requires the literal `.tif` extension, GTiff driver, one float32 band, EPSG:32611, exact template shape/CRS/transform, finite in-footprint pixels in [0,1], and numeric NaN in every exterior cell. It hashes the saved bytes before and after the read, reports the actual non-finite and masked-interior counts, and rejects candidate or template GDAL sidecars not covered by the TIFF hash. It fails closed for templates without a distinguishable non-finite exterior, masked finite template pixels or any nonconformity. `null` encodings via a separate GDAL mask or finite nodata sentinel are not certified by this conservative numeric-NaN check. No clipping or substitution occurs. Template footprint provenance must itself be independently confirmed.

`--outside zero` checks a whole-array-finite [0,1] alternative with zeros outside. This is **not** the written null/NaN exterior contract and its portal acceptance is unknown. [An example historical format receipt](../evidence/historical_h33_format.json) demonstrates this local check only; that historical TIFF remains disallowed. The user's “Predicted values must be in range [0, 1]” message has no retained rejected-file bytes here. It could reflect NaNs, out-of-range values, non-finite interior data, or other portal validation; the cause has not been established. Ask the organizer for clarification or obtain a documented portal receipt before claiming an encoding accepted.

## Required gates before any optional upload

1. Recorded method lane, physically defensible hypothesis, frozen experiment and honest non-fault mimics.
2. Repaired canonical evaluator; whole-segment buffered hideout with catalogue-derived features rebuilt from visible faults only, exact visible-fault masking, feature-alone leakage screens, pooled 300 m triangular-kernel DTI (α=.2, β=.8), withheld positive count, spatial 95% CI and same-evaluator baseline comparison. Beat the comparable current holdout best.
3. Fresh, integrity-verified **full current** registry; pre-placement surface and final-dot Spearman and directed 3-pixel overlap must pass all literal thresholds. The old historical lock is for reproducibility, not future clearance.
4. Shared writer and independent saved-byte format/hash validation. Match exact filename and SHA-256 to the one current run card; confirm licensing and organizer-derived input provenance. No guessed leaderboard score or projected score may be presented as an observed score.
5. An independent selector with the live rolling quota and weekly cap explicitly authorizes promotion. Only then download the **new** exact hash-matched `.tif` (or portal-accepted one-file ZIP), sign in to the [competition submission page](https://www.drivendata.org/competitions/306/competition-doe-gems/), upload that file with its unique run-card name and ≤140-character note, and retain the organizer's actual receipt. A format pass alone never authorizes a slot.

The organizer's final expert review is part of the competition and cannot be replaced by internal automation. No human inspection is a prerequisite for running the local checks; external input, eligibility, permissions, and receipt are separate facts.
