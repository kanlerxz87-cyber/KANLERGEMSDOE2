# Shared-template corrections and unresolved authority

The locally selected shared template is the pinned GEMSDOE24 package in `vendor/template/`; it is the **only active** metric/holdout/novelty/writer implementation in this repository. Upstream and locally patched SHA-256 values are retained in [pins.json](../vendor/template/pins.json). These changes have **not** been submitted to the upstream peer repository, and peer projects that use a different template do not automatically receive them. The owner prompt did not identify which of the conflicting peer template pins is authoritative across sessions. The older GEMSDOE32-derived E1 code is quarantined, not a second active implementation.

## 1. Isolated marginal-credit helper

The pinned upstream `marginal_inclusion_threshold` returned `alpha * s / (1 - alpha * s)`. For the specific isolated scenario of a new unit prediction with new credit `k` on **one** previously uncovered truth pixel, its contributions change by `ΔTP=k`, `ΔFP=1-k`, `ΔFN=-k`. When `alpha + beta = 1`, the denominator increases by `alpha`, so DTI improves exactly when `k > alpha * s`. The shared helper now returns that expression and rejects invalid inputs. It expressly does not claim applicability to general overlapping kernels or multiple truths. The actual `dti_components_exact` and `dti_score_fast` score calculations are unchanged. Synthetic tests verify the algebra on both sides of the threshold.

Reference: [official metric equations](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric).

## 2. Literal novelty checker

The previous shared checker validated only raster shape, could report a pass with an empty/constant reference or undefined rank, and could replace its primary `passed` verdict with a control-exempted verdict. The single shared `novelty.py` now requires a template, checks shape/CRS/transform/band count and finite in-range footprint values, fails closed on empty or undefined comparisons, and keeps `passed` as the literal all-entry result even when control classifications are supplied as diagnostics. The diagnostic method-only result is not authorization to ignore a raster. `compare_prospective_registry` passes the template through. Tests cover grid mismatch, missing template, constant support and the no-exemption rule.

The corrected helper and checker do not resolve whether a continuous raster should be considered a set of dots in the **owner's intended** policy. The pinned template's present implementation defines dots as positive pixels, and under that literal convention the [GEMSDOE48 witness](../evidence/registry_witness.json) blocks every nonempty candidate. No unapproved semantic change has been made.

## 3. Important remaining limits

- The shared canary accepts one global feature surface. The guarded local CLI permits only declared label-free static surfaces; catalogue-derived features need a fold-specific canary implementation in this same shared template before use. A declaration alone does not prove label independence.
- The evaluator cannot establish from a saved array that the model was trained without a withheld component; that provenance needs separately reproducible training/fold evidence.
- Existing `make_note` accepts more characters than this project's limit. The guarded writer enforces the requested 140-character limit itself. Zero-outside output avoids nonfinite values but is not a claim of portal acceptance or a substitute for an authenticated sample.
