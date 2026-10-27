# KANLERGEMSDOE2 · GEMS fault research review

> **Current decision: NEGATIVE / DO NOT SUBMIT.** No new candidate, GeoTIFF, model experiment, upload, or weekly slot was generated or spent in this review. The literal registry rule is impossible at the preregistered 37,654-dot budget. A negative result is the required outcome; no file in this repository is currently authorized as a competition entry.

[Executive summary and nine-site downloads](EXECUTIVE_SUMMARY.md) · [GitHub Pages report](docs/index.html) · [Current JSON run card](evidence/run_card.json) · [Registry proof](evidence/registry_preflight_20261027.json) · [Exact-file validator](evidence/validator_receipt.json)

## Decision and why

The registered lattice covers 5,160,724 of 5,167,373 footprint pixels within 3 pixels; only 6,649 are uncovered. Any distinct 37,654-dot set therefore has at least `(37,654 − 6,649) / 37,654 = 82.3418%` overlap. The literal stop is **greater than 70%** against **any** registry entry, so the preregistered HTCADS-K2 lane stopped before model fitting or placement. A single witness proves a stop; a witness-only non-stop would be inconclusive. The first budget forced strictly over the threshold is 22,164 dots.

The prior [HTCADS TIFF](docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif) is available **for research only**: SHA-256 `f482d3bad4b390470be06363b60867c8e42942101271caf4fa82ae3c3975abeb`; its actual lattice overlap is **37,642 / 37,654 = 99.9681%**. Local grid/range checks pass, but literal novelty fails; an independent full-registry replay, matched holdout, canaries and current quota approval are not verified. **Do not submit it.** Previous promotions, projections and receipts in [the archive](evidence/archive/README.md) are superseded research, not authorization.

## What the nine-site audit establishes

The [executive summary](EXECUTIVE_SUMMARY.md) lists exact commit-pinned historical GeoTIFF downloads, full SHA-256 values, directional overlap vs the other eight, local outside-footprint nonfinite status, and user/owner-reported scores. No organizer submission-page receipt was available to link a score to a file; these are **unverified reports**, not organizer-confirmed results. All nine references exceed 70% against at least one of the other eight, and GEMSDOE25/30 have identical positive masks. This subset is not the whole registry; portal acceptance is unknown.

The reported GEMSDOE32 `0.2778` is the highest of these nine reports, not a verified artifact-linked score. Sparse predictions and known-fault collar filtering may reduce redundant false-positive penalties under the [official DTI](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) metric, but could also remove true faults; this is a hypothesis, not proof of causation or hidden labels. No independently evaluated new method or projected leaderboard score is available. A public leaderboard observation on 2026-10-27 was **#1 `0.4544` and #5 `0.3566`**, not a receipt for a particular artifact; the older `0.4413` / `0.3195` values in the preserved brief are stale. Check the [organizer leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) for its current values.

Four ranked, conditional geological hypotheses with layers, transforms, mimics, estimated effort and official sources are in [the pre-implementation memo](knowledge/02_htcads_next_hypotheses_20261027.md). Their fleet-wide novelty, improvement and obtainable coverage have not been proven. The challenge predicts faults, not geothermal vent locations.

## Core values

- **Maximize P(Win):** protect scarce slots, seek independently validated improvements, and stop rather than evade a preregistered rule.
- **Own the Outcome:** report uncomfortable evidence, fix shared code in place, distinguish local format checks from portal acceptance, and fail closed when replay or quota evidence is missing. No human-inspection fallback or live submission is used.

## Evidence and irregularities

[Three verification passes](evidence/verification_passes_20261027.json) cover the proof, nine-site replay, fail-closed tests, clean-data CI, and deployment limitations.

- **Input provenance:** restored inputs match pinned owner-mirror hashes, not independently authenticated organizer downloads. The mirrored sample's **60,988** positive pixels are pixel-identical to the label raster even though the [organizer describes a total-absence sample](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format). Treat sample values strictly as footprint/grid metadata, never predictive features. [Input diagnostics](evidence/input_diagnostics_20261027.json).
- **Duplicate exemption repaired:** `src/gems/novelty.py` now applies the literal gate to all entries, including controls, and requires pre-placement support; [preflight](src/gems/preflight.py) prevents the legacy runners from fitting or placing. A control-exempt diagnostic cannot pass the rule.
- **Validation repaired:** [validator](scripts/validate_submission.py) reopens and hashes the actual bytes, separately checks local grid/range and exact lattice overlap, and cannot issue a positive decision while replay/quota verifiers are absent. The [shared writer](scripts/submission_writer.py) rejects invalid in-footprint inputs rather than silently clipping. No local test proves portal acceptance or the cause of an earlier rejection. The organizer's text calls for null/NaN outside bounds, while this project's stricter local all-finite variant uses zeros outside the footprint.
- **Holdout scope:** the old HTCADS report records **HOLDOUT-DTI `0.112353`**, 95% CI `[0.098995, 0.125743]`, evaluator `GEMSDOE32-HIDE-RECOVER-v3.0`, `N=22,232` withheld positives; it has **not** been independently replayed here and is not a forecast. The current run has no holdout value or leakage-canary replay. Full provenance and peer-reported (not replayed) holdouts appear in the executive summary.
- **Cache:** `scripts/prepare_data.py` successfully prepared the 30-channel shared stack from restored features, without fitting a model. Its generated data and large sources live under ignored `data/`, not Git. [Preparation receipt](evidence/data_preparation.json). A previously published band-6 provenance discrepancy is [reported by GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/); its identity remains unverified here.

## Reproduce locally

Python 3.11+, GitHub CLI and a current authenticated GitHub connection are required for owner-mirror and peer-artifact restore. See [data manifest](registry/data_manifest.json) for exact pins. These commands inspect cached historical inputs, not create a competition submission.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/restore_data.py --group all --target-dir "$PWD/data"
.venv/bin/python scripts/prepare_data.py                 # validated shared cache; no model fit
.venv/bin/python scripts/verify_inputs.py                # input irregularity and hashes
.venv/bin/python scripts/registry_preflight.py --expect-stop
.venv/bin/python scripts/audit_focus9.py --restore      # nine pinned files, gh required
.venv/bin/python scripts/build_current_review.py        # reopens old TIFF, writes negative card
.venv/bin/python scripts/build_site.py                  # Pages and executive summary
.venv/bin/python scripts/evaluate_holdout.py --verify-kg2  # historical bytes only, no promotion
.venv/bin/pytest -q
```

`GEMS_DATA_DIR` can redirect inputs, while the default is `data/`; caches are hash-checked. `scripts/validate_submission.py` deliberately returns nonzero because submission authorization is unavailable even when format passes. The feature, holdout, uniqueness, and selector code require substantial verified changes before any future promotion. Do not weaken or remove the lattice comparator or threshold to generate an apparent pass.

### Leaderboard refresh and Pages

`docs/data/leaderboard.json` is a dated snapshot. `python scripts/refresh_leaderboard.py` fetches the public organizer page if network access allows; failure writes `unavailable` and keeps any old value visibly dated. The Pages workflow is configured to refresh on a schedule and on manual dispatch **if GitHub Actions is enabled as the repository's Pages source and deployment permissions are granted**. Until a successful deployment is observed, it is a refreshable snapshot, not a guaranteed live feed. The organizer page remains authoritative.

## Preserved standing brief and protocol

The following is the original project brief retained verbatim from [`PROMPT.md`](PROMPT.md), including user-supplied claims and historical targets. It is a **record of instructions**, not evidence that those scores, priors, portal guarantees, or prize amounts are verified. The current findings above take precedence over old factual assertions; the strict duplicate-stop protocol is unchanged.

<details><summary>Expand the preserved prompt and core values</summary>

# Standing Project Brief & Parallel-Run Protocol (`KANLERGEMSDOE2`)

> **Epistemic Integrity Note (Zero Hallucinations):** This file preserves the complete standing project brief, 9-site / 92-site audit mandate, Parallel-Run Protocol (Rules 1–6), and Arena Core Values (**Maximize P(Win)** and **Own the Outcome**) governing `kanlerxz87-cyber/KANLERGEMSDOE2`. Read this brief together with `README.md` at the start of every session before writing code or running experiments.

---

## Core Values

- **Maximize P(Win):** Optimize expected leaderboard and Phase 2 ($250k / $395k expert-reviewed evaluation) return per scarce submission slot. Never burn a weekly slot on cosmetic edits, duplicate `H19-5` clones, or candidates that fail to beat the spatially-blocked holdout benchmark.
- **Own the Outcome:** Automated code gates — never manual human inspection — verify `[0, 1]` GeoTIFF range safety, zero NaNs, leakage canaries, registry uniqueness, and holdout statistical significance end-to-end. Fix shared template defects at the root and document every irregularity and negative result transparently.

---

## Standing Project Prompt Record

Review the repo and execute any open next steps first.

Focus on the highest-scoring submissions from the following 9 focus sites:
- `GEMSDOE24`, `GEMSDOE25`, `GEMSDOE27`, `GEMSDOE28`, `GEMSDOE30`, `GEMSDOE31`, `GEMSDOE32`, `GEMSDOE33`, `GEMSDOE36` (and cross-check against all ~65+ listed GEMSDOE sites across the fleet).

**THE FOLLOWING IS THE HIGHEST URGENCY AND MUST BE FOLLOWED:**
- **MUST GENERATE A UNIQUE `.TIF` SUBMISSION FOR THE COMPETITION.** Do not copy a previous submission unless it is strictly for learning and forensic baseline comparison.
- **IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT THE GENERATED `.TIF` SUBMISSION** at the top of the GitHub Pages site and executive summary subpage, validated automatically in code **without human intervention**.
- **Fix submission portal error:** `"Predicted values must be in range [0, 1]"` (single-band float32 GeoTIFF matching `sample_submission.tif` CRS `EPSG:32611`, `3730 x 3292` shape, and `100 m` Affine geotransform, with `0` NaNs and all values strictly in `[0, 1]`).
- Give the submission a **unique filename** and a **short note (`<= 140` characters)** so submissions are never confused.
- Create an **executive summary subpage** (`docs/executive-summary.html`) as a guide across all sites with an auditable table showing for each site: exact file to download, its score / holdout metric (strictly labeled), portal safety, and whether the file is unique across sites.

### PhD-Level Forensic Analysis & Scientific Hypothesis Mandate

1. **Study, analyze, and understand `0.2778`:** Explain why and how `GEMSDOE32` (`https://buffedlizard55-lab.github.io/GEMSDOE32/`, `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`: `0.2778` `ORGANIZER-CONFIRMED`) achieved the highest score across the focus sites, and whether/how a new strategy can score higher (`> 0.2778`, targeting `#5 = 0.3195` and public `#1 = 0.4413`).
2. **Pre-Implementation Hypotheses (3–5 Untried Geological Hypotheses):** Emphasizing scientific discovery of geothermal vents and unmapped faults, propose 3–5 concrete hypotheses before writing model code, specifying for each:
   - Exact layer(s) involved
   - Physical fault signature or mathematical transform targeted (plus named non-fault mimic process)
   - Why it catches faults missing from the USGS/INGENIOUS catalogue rather than already-mapped ones
   - How it differs from prior implementations across the GEMSDOE fleet
   - Rank by expected DTI improvement vs. implementation cost, checking free official external data obtainability before proposing as viable.

### Parallel-Run Protocol (Strict)

1. **LANE:** Stay inside the single pre-registered method paragraph (`registry/preregistration_htcads.json`). If rank-correlation with any registry raster exceeds `0.90`, or more than `70%` of emitted dots fall within `3 px` of any registry detector raster's dots, log as duplicate and stop. Check BOTH on the continuous surface before placement AND on the final dots.
2. **REUSE, DON'T REBUILD:** Reuse the template's cached feature stack, `evaluate_holdout.py`, and `submission_writer.py`. Holdout = hide-and-recover: withhold whole fault segments with a buffer, derive every catalogue-based feature only from visible faults, mask visible faults pixel-exactly, and score pooled DTI (`alpha = 0.2`, `beta = 0.8`, `300 m` triangular kernel). Fix shared tool bugs in the template and report them; never keep a private fork.
3. **LABEL EVERY NUMBER:** Strictly label every metric as `HOLDOUT-DTI (evaluator version, N withheld positives, 95% CI)` or `ORGANIZER-CONFIRMED (copied from submission-page receipt)`. Never write a projection as a score.
4. **LEAKAGE CANARY:** Test each feature alone on holdout first; single-feature `AUC > 0.90` is leakage until proven otherwise.
5. **RUN CARD:** Produce one JSON Run Card (`evidence/run_card.json`): `hypothesis`, `mechanism`, `named_non_fault_mimic`, `holdout_dti` + `ci`, `correlation/overlap vs registry`, `raster_sha256`, `validator_output`, `submission_name` + `<=140`-char `note`, and `verdict` (`promote` or `negative` — negative results are valid deliverables).
6. **BUDGET:** Stop after `3` experiments or `2` hours. Do not directly spend live weekly slots.

### Workflow & Delivery

- Preserve this prompt and Arena Core Values in `README.md` as the starting point for future sessions.
- Verify every claim, file hash, calculation, and official URL line by line with zero hallucinations; flag any irregularities.
- Execute **3 verification passes** (Pass 1: complete implementation & verification; Pass 2: review & fix bugs, missing requirements, and edge cases; Pass 3: final accuracy, completeness, and quality check), then open and merge a Pull Request onto `main`.

</details>
