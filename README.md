# KANLERGEMSDOE2 — geothermal fault discovery

> **CURRENT DECISION: NOT OK TO SUBMIT.** No new model, GeoTIFF, leaderboard estimate or live-slot decision was produced in this review. The previous HTCADS TIFF is available [for research only](docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif); **do not submit it**. It fails the literal all-registry duplicate rule. The previous “5/5 gates / promote” claim is retracted.
>
> **Research file:** `kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif`
> **SHA-256:** `f482d3bad4b390470be06363b60867c8e42942101271caf4fa82ae3c3975abeb`
> **Current card:** [`evidence/current_run_card.json`](evidence/current_run_card.json) · **byte audit:** [`evidence/release_audit_20261027.json`](evidence/release_audit_20261027.json) · **guide:** [executive summary](docs/executive-summary.html) · **site:** [decision dashboard](docs/index.html)

## Why stop?

The user’s **PARALLEL-RUN PROTOCOL** says **any** registry raster triggers a duplicate if more than 70% of our dots are within 3 pixels. A registered spacing-5 lattice was previously exempted as a “calibration control”; the instruction has no such exemption. From freshly restored, SHA-checked owner mirrors:

- The prior TIFF overlaps the lattice at **37,642 / 37,654 = 99.9681%** of its dots.
- The lattice covers **5,160,724 / 5,167,373** pixels within 3 px, leaving **6,649** uncovered. For any placement of **37,654 distinct in-footprint dots**, at least `37,654 − 6,649 = 31,005` dots overlap: **82.3418% > 70%**.
- At **22,164 dots**, the strict `> 70%` lower-bound stop first becomes unavoidable. This proof is specific to the budget, footprint and witness; it does not prove every possible smaller raster fails. Do not quietly reduce the assigned budget or make an exemption to escape the gate.
- A witness is enough to prove failure. We did not replay a complete current registry, the candidate’s pre-placement surface, or the original model/holdout. Account quota remains unknown. Nothing here authorizes a submission.

The file is single-band float32, EPSG:32611, 3,730 × 3,292, 100 m grid, and its entire stored array is finite in `[0,1]`, with no catalogue-positive pixels. **Those are local checks, not an organizer acceptance receipt.** The owner sample uses NaN outside its irregular footprint; this file stores zeros there. The official format says null/NaN outside bounds, while the cause of the reported `[0,1]` rejection is unknown. Neither exterior encoding is proven accepted here.

## Nine-site investigation

The largest of the supplied focus-site numbers is **0.2778, USER/OWNER-REPORTED, unverified** for GEMSDOE32. There is no archived submission-page receipt establishing that score or the exact bytes. The current public leaderboard snapshot, observed 2026-10-27, had #1 **0.4544** and #5 **0.3566**; the older targets in the preserved brief are historical, not current or candidate-specific scores. A Pages deploy attempts a six-hourly refresh and marks failure as stale, not as a new score.

Hash-pinned artifacts from all nine focus sites were inspected. All exceed 70% directional 3-px overlap with another member of the focus set. GEMSDOE25 and GEMSDOE30 have identical positive masks. GEMSDOE32’s mask equals GEMSDOE25’s mask after removing dots ≤2 px from the known-fault raster (6,436 removed); GEMSDOE36 contains all GEMSDOE32 dots plus 1,200. These geometric facts suggest a testable reason for improved *reported* scores—better precision from pruning—but do **not** prove which predictions matched hidden truth, why a reported score changed, or that a new candidate will score higher. Older claims of organizer confirmation and mathematical inference of hidden-label counts are withdrawn. See the [nine-site table](docs/executive-summary.html) and [full evidence](evidence/release_audit_20261027.json).

## Research and holdout

Four ranked, concrete hypotheses with physical signatures, named non-fault mimics, existing-method comparisons, and official data-access caveats are in [`research/2026-10-27_htcads_hypotheses.md`](research/2026-10-27_htcads_hypotheses.md). The top proposed direction is height-persistent cross-gradient corroboration with distinct hydrothermal support; it is **unfitted** and fleet novelty is not established.

The previous HTCADS receipt reports **HOLDOUT-DTI 0.112353**, evaluator `GEMSDOE32-HIDE-RECOVER-v3.0`, **22,232 withheld-positive occurrences**, 95% CI **[0.098995, 0.125743]**. This is a historical, unreplayed holdout, not an organizer score or reliable leaderboard projection. The 30-column base feature cache was restored/prepared; the HTCADS-specific model/OOF caches and independent canary/holdout replay were not recreated because the literal preflight already requires stopping.

## Reproduce the audit (no upload)

Python 3.11, GDAL-compatible rasterio wheels, GitHub access, and several GB of free disk/RAM are needed for bulk data. Source hashes establish identity to owner mirrors—not authenticity of organizer/USGS/DOE origin. Bulk data and `.venv` are ignored and must be restored again in a fresh workspace.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/restore_data.py --group all      # pinned owner mirrors
.venv/bin/python scripts/restore_focus_sites.py          # nine pinned TIFFs
.venv/bin/python scripts/prepare_data.py                 # optional base 30-column cache
.venv/bin/python scripts/audit_release.py                # rebuild audit + current negative card
.venv/bin/python scripts/build_site.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/evaluate_holdout.py --verify-kg2 # historical hashes only; negative
```

The fail-closed validator can inspect the previous artifact after data restoration; it **must exit 1** because the lattice witness fails and other promotion evidence is missing:

```bash
.venv/bin/python scripts/validate_submission.py \
  --tif docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif \
  --run-card evidence/run_card.json --out evidence/validator_receipt.json
```

`GEMS_DATA_DIR` overrides the default `.cache/gems_data`. Restore receipts are per group in ignored `data/`. The old HTCADS, KG2 and FVCA emission entry points are intentionally blocked: they cannot generate an unsafely promoted file while the conflict persists. Full independent validation and an account-aware selector must exist before any future promotion.

## Values and starting brief

**Maximize P(Win):** Protect scarce live slots; prefer a valid negative result to an unverified projected gain.
**Own the Outcome:** Restore/check bytes, verify sources, fix shared tools, use automatic fail-closed checks, document uncertainty, and do not rely on a manual geological inspector.

Read this README, the preserved brief below, and [`PROMPT.md`](PROMPT.md) at the start of every session. The preserved request records earlier score targets as historical; it does not override the current stop or confer score authenticity. See [`AGENTS.md`](AGENTS.md) for the operative safety contract and [`docs/irregularities.html`](docs/irregularities.html) for unresolved blockers.

<details>
<summary><strong>📋 Preserved Standing Project Prompt &amp; Parallel-Run Protocol (Read at the Start of Every Session)</strong></summary>

See also [`PROMPT.md`](PROMPT.md).

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
