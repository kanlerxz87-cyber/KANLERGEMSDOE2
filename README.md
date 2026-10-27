# KANLERGEMSDOE2 — geothermal fault research

> ## **DO NOT SUBMIT — no candidate is currently approved**
>
> The historical [HTCADS GeoTIFF](docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif) is available **for research/audit only**. **99.968%** of its dots lie within three pixels of a registry lattice, exceeding the user’s literal 70% limit. Earlier “promote” receipts excluded that raster and have been superseded. No new experiment, submission or weekly slot was used in this session.
>
> [Executive summary](EXECUTIVE_SUMMARY.md) · [Website source](docs/index.html) · [Current JSON run card](run_card.json) · [Nine-site evidence](evidence/focus_reaudit_20261027.json)

## Decision and evidence

| Gate | Current result |
|---|---|
| Literal novelty | **Fail.** The lattice also makes the 37,654-dot budget mathematically incompatible with the 70% stop: the minimum possible overlap is 82.34%. All three local historical candidates fail. |
| Format | Single-band float32, EPSG:32611, 3,730 × 3,292, matching the pinned mirror’s transform; every stored value is finite and in `[0, 1]`. This is a local array/grid check, **not a portal-acceptance guarantee**. |
| Outside-bounds wording | The historical TIFF fills outside its mirrored irregular footprint with zero. Official wording calls for null/NaN outside the bounds; whether that means the same footprint has not been independently established. |
| Holdout | Historical HTCADS **HOLDOUT-DTI 0.112353** (`GEMSDOE32-HIDE-RECOVER-v3.0`, 22,232 withheld positives, 95% CI `[0.098995, 0.125743]`) was not replayed. It is not a leaderboard score. |
| Account and quota | Official data and submissions pages require login. No submission receipt, remaining weekly quota, or independent replay certificate was available. The selector fails closed and does not upload. |

SHA-256 of the research file: `f482d3bad4b390470be06363b60867c8e42942101271caf4fa82ae3c3975abeb`. The nine sites’ supplied values are **user/owner reports**, not organizer-confirmed receipts. GEMSDOE32’s `0.2778` is the highest supplied value, but its causal explanation and whether an untested candidate can exceed it are unknown. See [research](research/2026-10-27-next-hypotheses.md) and the [executive table](EXECUTIVE_SUMMARY.md) for the evidence and limitations.

## Arena values

- **Maximize P(Win):** spend scarce evaluation opportunities on defensible scientific improvements, not duplicate artifacts or cosmetic changes.
- **Own the Outcome:** preserve provenance, verify in shared automated code, report uncertainty and negative results, and fail closed instead of relying on human inspection as a substitute for validation.

## Reproducibility and safe commands

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python scripts/build_site.py
# Expected exit code 1: negative, never upload (restore the template first for a full format audit)
python scripts/validate_submission.py \
  --tif docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif \
  --run-card run_card.json --out validation.json
```

The tests use synthetic data and bundled small artifacts. `scripts/restore_data.py --group all --target-dir data` can restore larger **third-party GitHub mirrors** by pinned SHA-256; mirror hashes do not prove official origin. Official inputs and account access still need independent verification. `scripts/audit_focus_history.py` re-downloads nine pinned GitHub TIFFs and checks their bytes, plus the local lattice; it does not replay all 360 registry entries or pre-placement continuous surfaces. Historical experiment/asset entrypoints are guarded. Do not run another candidate, adjust dots or silently exempt the lattice while the literal stop remains in force.

The [public organizer leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) is the live source of truth. A daily GitHub Pages workflow attempts to refresh a timestamped public snapshot; if the source is unavailable or changes layout, it retains the previous dated snapshot rather than guessing. It does not access or spend account quota.

## Files to read first

- [`PROMPT.md`](PROMPT.md): condensed standing brief and protocol; the complete original prompt was not preserved verbatim in the checkout.
- [`run_card.json`](run_card.json): current negative JSON decision with hash and actual validation results.
- [`evidence/focus_reaudit_20261027.json`](evidence/focus_reaudit_20261027.json): nine pinned files, overlap and decisive lattice comparisons.
- [`research/2026-10-27-next-hypotheses.md`](research/2026-10-27-next-hypotheses.md): four sourced proposals, not trained or scored.
- [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md): historical file table and future submission instructions.

---

<details>
<summary><strong>📋 Preserved Standing Project Prompt &amp; Parallel-Run Protocol (Read at the Start of Every Session)</strong></summary>

This is the previously preserved condensed prompt, not a verbatim complete original. See [`PROMPT.md`](PROMPT.md) and the user’s current instructions. Historical values and target ranks in this quotation are unverified unless a dated source or receipt says otherwise.

> **Core Values:** **Maximize P(Win)** and **Own the Outcome**. No human-inspection fallback exists: automated validation gates fail closed.
>
> Review the repo.
>
> Focus on the highest scoring submissions from the following sites: `GEMSDOE24`, `GEMSDOE25`, `GEMSDOE27`, `GEMSDOE28`, `GEMSDOE30`, `GEMSDOE31`, `GEMSDOE32`, `GEMSDOE33`, `GEMSDOE36` (and cross-check across all listed GEMSDOE sites).
>
> **THE FOLLOWING IS THE HIGHEST URGENCY AND MUST BE FOLLOWED!**
>
> MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION. DO NOT COPY A PREVIOUS SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION. BUT WE MUST GENERATE A UNIQUE TIF SUBMISSION. IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT THE GENERATED TIF SUBMISSION.
>
> There should be an easy to download submission tif file as described by the prompt. Read the entire prompt. A lot of sites mention inspection only and a human inspector, but the inspection needs to be done through the project and needs to be validated for submission without human intervention.
>
> Fix submission error: `"Predicted values must be in range [0, 1]"`. Give the submission a unique name and a short comment (`<= 140` chars) to tell submissions apart later. Create an executive summary subpage as a guide across all sites showing for each site what file to download, what its score is, and whether the file is unique across the sites.
>
> **PARALLEL-RUN PROTOCOL — follow strictly:**
> 1. **LANE.** Stay inside the single pre-registered method paragraph. If rank-correlation with any registry raster exceeds `0.90`, or more than `70%` of dots fall within `3 px` of one registry raster's dots, log it as a duplicate and stop. Check this on the continuous surface before placement AND on the final dots.
> 2. **REUSE, DON'T REBUILD.** Use the template's cached feature stack, `evaluate_holdout.py`, and `submission_writer.py`. Holdout = hide-and-recover: withhold whole fault segments with a buffer, derive every catalogue-based feature only from the visible faults, mask visible faults pixel-exactly, score pooled DTI (`alpha = 0.2`, `beta = 0.8`, `300 m` triangular kernel). If a shared tool is wrong, fix it once in the template and report it; never keep a private fork.
> 3. **LABEL EVERY NUMBER** as `HOLDOUT-DTI` (evaluator version, number of withheld positives, 95% CI) or `ORGANIZER-CONFIRMED` (copied from a submission-page receipt). A projection is never written as a score.
> 4. **LEAKAGE CANARY.** Test each feature alone on the holdout before trusting any result. Single-feature `AUC > 0.90` means leakage until proven otherwise.
> 5. **RUN CARD.** End with one JSON card: `hypothesis`; `mechanism`; `named_non_fault_mimic`; `holdout_dti` + CI; `correlation/overlap vs registry`; `raster_sha256`; `validator_output` (no NaN inside footprint, values in `[0,1]`, CRS/shape/transform match); `submission_name` + `note` (`<= 140` characters); `verdict` (`promote` / `negative`). Negative results are deliverables.
> 6. **BUDGET.** Stop after `3` experiments or `2` hours. Do not pick live submission slots directly.
>
> **PhD-Level Forensic Analysis & Pre-Implementation Hypotheses:**
> - Analyze why and how `GEMSDOE32` (`https://buffedlizard55-lab.github.io/GEMSDOE32/`, `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`: `0.2778`) got the highest score and whether we can score higher (`> 0.2778`, targeting `0.3195` and `0.4413`).
> - Before implementing, generate 3–5 untried geological hypotheses (emphasizing geothermal vents and unmapped faults), naming exact layer(s), physical signature/transform, why it catches faults missing from the USGS/INGENIOUS catalogue, how it differs from prior work, ranked by expected DTI improvement vs. cost, and checking free official external data obtainability first.
> - Work autonomously line by line verifying from official trusted sources with zero hallucinations; flag any irregularities; execute 3 passes (Pass 1 implement & verify, Pass 2 review & fix bugs/missing requirements/edge cases, Pass 3 final accuracy & completeness check), then create and merge a PR onto `main`.

</details>
