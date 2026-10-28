# KANLERGEMSDOE2 — geothermal fault discovery

> ### CURRENT DECISION — NEGATIVE: NO TIFF IS CLEARED TO SUBMIT
>
> **Do not download any repository TIFF for a DrivenData submission.** This review produced no new GeoTIFF, no current candidate score estimate, and used no live submission slot. Existing TIFFs are historical/research artifacts only.
>
> - **Hard stop:** the literal protocol treats *any* registered raster as a duplicate witness. At the frozen 37,654-dot budget, a registered 3-px lattice covers 5,160,724 of 5,167,373 footprint pixels, forcing at least 31,005 dots (82.34%) within 3 px—above the 70% limit. The prior HTCADS TIFF itself overlaps at 37,642/37,654 (99.968%). Do not exempt the lattice or lower the budget to evade the gate.
> - **Highest of the nine focus-site reports:** GEMSDOE32 **0.2778 USER/OWNER-REPORTED, unverified**. No organizer submission-page receipt ties the number to the exact TIFF. Its mirror mask is GEMSDOE25's after 6,436 near-catalogue dots are removed; that geometry suggests a precision/recall hypothesis, not a causal explanation or score guarantee.
> - **Leaderboard correction:** the official public leaderboard page observed on 2026-10-27 showed #1 = **0.4544**, #5 = **0.3566**; **0.3195 was #25**, not the top score. This is an official public-page observation, not a submission receipt; ranks change. See [`registry/official_sources_20261027.json`](registry/official_sources_20261027.json).
> - **No new-score projection:** public leaderboard scores, historical user reports and local HOLDOUT-DTI results are different evidence. We do not convert between them. The new submission estimate is **not available**.
>
> **Current run card:** [`evidence/current_run_card.json`](evidence/current_run_card.json) · **exact-byte audit:** [`evidence/release_audit_20261027.json`](evidence/release_audit_20261027.json) · **executive summary:** [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md) · [website decision dashboard](docs/index.html) · [website executive summary](docs/executive-summary.html)
>
> The old Session-2 DSLUP “OK TO SUBMIT” claim used a control-separated exception that conflicts with the literal all-registry rule. It is **withdrawn**. Its TIFF and related receipts remain archived for learning only; they are not cleared for submission.

## Why stop?

The user’s **PARALLEL-RUN PROTOCOL** says **any** registry raster triggers a duplicate if more than 70% of our dots are within 3 pixels. A registered spacing-5 lattice was previously exempted as a “calibration control”; the instruction has no such exemption. The archived audit used restored, SHA-checked owner mirrors; those ignored data/cache inputs are not present in this checkout:

- The prior TIFF overlaps the lattice at **37,642 / 37,654 = 99.9681%** of its dots.
- The lattice covers **5,160,724 / 5,167,373** pixels within 3 px, leaving **6,649** uncovered. For any placement of **37,654 distinct in-footprint dots**, at least `37,654 − 6,649 = 31,005` dots overlap: **82.3418% > 70%**.
- At **22,164 dots**, the strict `> 70%` lower-bound stop first becomes unavoidable. This proof is specific to the budget, footprint and witness; it does not prove every possible smaller raster fails. Do not quietly reduce the assigned budget or make an exemption to escape the gate.
- A witness is enough to prove failure. We did not replay a complete current registry, the candidate’s pre-placement surface, or the original model/holdout. Account quota remains unknown. Nothing here authorizes a submission.

The prior HTCADS research TIFF has SHA-256 `f482d3bad4b390470be06363b60867c8e42942101271caf4fa82ae3c3975abeb`. It is single-band float32, EPSG:32611, 3,730 × 3,292, 100 m grid, and its entire stored array is finite in `[0,1]`, with no catalogue-positive pixels. **Those are local checks, not an organizer acceptance receipt.** The owner sample uses NaN outside its irregular footprint; this file stores zeros there. The official format says null/NaN outside bounds, while the cause of the reported `[0,1]` rejection is unknown. Neither exterior encoding is proven accepted here. The TIFF remains historical/research-only; do not submit it.

## Nine-site investigation

The largest of the supplied focus-site numbers is **0.2778, USER/OWNER-REPORTED, unverified** for GEMSDOE32. There is no archived submission-page receipt establishing that score or the exact bytes. The official public leaderboard snapshot observed 2026-10-27 had #1 **0.4544**, #5 **0.3566**, and #25 **0.3195**; the older prompt targets are not current or candidate-specific scores. A Pages deploy attempts a six-hourly refresh and marks failure as stale, not as a new score.

Hash-pinned artifacts from all nine focus sites were inspected. All exceed 70% directional 3-px overlap with another member of the focus set. GEMSDOE25 and GEMSDOE30 have identical positive masks. GEMSDOE32’s mask equals GEMSDOE25’s mask after removing dots ≤2 px from the known-fault raster (6,436 removed); GEMSDOE36 contains all GEMSDOE32 dots plus 1,200. These geometric facts suggest a testable reason for improved *reported* scores—better precision from pruning—but do **not** prove which predictions matched hidden truth, why a reported score changed, or that a new candidate will score higher. Older claims of organizer confirmation and mathematical inference of hidden-label counts are withdrawn. See the [nine-site table](docs/executive-summary.html) and [full evidence](evidence/release_audit_20261027.json).

## Research and holdout

Four ranked, concrete hypotheses with physical signatures, named non-fault mimics, existing-method comparisons, and official data-access caveats are in [`research/2026-10-27_htcads_hypotheses.md`](research/2026-10-27_htcads_hypotheses.md). The top proposed direction is height-persistent cross-gradient corroboration with distinct hydrothermal support; it is **unfitted** and fleet novelty is not established.

The previous HTCADS run-card record reports **HOLDOUT-DTI 0.112353** (`GEMSDOE32-HIDE-RECOVER-v3.0`, **22,232 withheld-positive occurrences**, 95% CI **[0.098995, 0.125743]**). This is a historical, unreplayed holdout, not an organizer score or leaderboard projection. Prior-session notes mention a 30-column base cache, but the current checkout has no `data/` or cache inputs; HTCADS model/OOF caches and independent canary/holdout replay are not available here.

## Historical parallel-lane work (not the current assignment)

The repository contains earlier ECPU and DARP-MT10 experiments, plus sibling-repository audits. They are kept as research history; none overrides the current HTCADS lane, the literal any-registry duplicate rule, or this negative decision. They do not supply a current leaderboard estimate or authorize a submission.

- **ECPU:** three recorded experiments and an ablation were negative under their recorded holdout/selector gates. Its TIFF is archived as a negative research artifact; see [`evidence/ecpu_experiments_20261027.json`](evidence/ecpu_experiments_20261027.json), [`evidence/ecpu_leakage_canary_20261027.json`](evidence/ecpu_leakage_canary_20261027.json), and [`registry/preregistration_ecpu_20261027.json`](registry/preregistration_ecpu_20261027.json).
- **DARP-MT10:** its separate experiment record includes a positive diagnostic on a restricted piedmont holdout and a negative full-catalogue / literal-registry result. The restricted result is **HOLDOUT-DTI**, not a public score; the lane is not the current assignment and the candidate is not cleared. See [`evidence/darp_mt10_experiments_20261027.json`](evidence/darp_mt10_experiments_20261027.json), [`evidence/darp_mt10_run_card_20261027.json`](evidence/darp_mt10_run_card_20261027.json), and [`registry/preregistration_darp_mt10.json`](registry/preregistration_darp_mt10.json).
- **Sister-repository artifacts:** the recorded audit flags examples of blanket rasters, nodata/value issues, and on-catalogue predictions. It is an owner-mirror audit, not an organizer review: [`evidence/sister_and_focus_audit_20261027.json`](evidence/sister_and_focus_audit_20261027.json).

The current session remains at zero experiments because the frozen-budget witness proves the hard uniqueness gate cannot pass. Do not revive an earlier lane, candidate, or alternate uniqueness policy without a separately authorized protocol update.

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
<summary><strong>📋 Preserved Standing Project Prompt &amp; PARALLEL-RUN PROTOCOL (Read at the Start of Every Session)</strong></summary>

See also [`PROMPT.md`](PROMPT.md).

> **Core Values:** **Maximize P(Win)** and **Own the Outcome**. No human-inspection fallback exists: automated validation gates fail closed.
>
> Review the repo and execute any next steps from previous sessions first.
>
> Focus on the highest-scoring submissions from the 9 focus sites (`GEMSDOE24`, `GEMSDOE25`, `GEMSDOE27`, `GEMSDOE28`, `GEMSDOE30`, `GEMSDOE31`, `GEMSDOE32`, `GEMSDOE33`, `GEMSDOE36`) and cross-check across all listed GEMSDOE and sister sites (`KANLERGEMSDOE1..3`, `EUGGEMSDOE1..3`, `WBGGEMSDOE1..3`, `GINNYGEMSDOE1..3`, `GEMSDOE..GEMSDOE92`, including `kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros`).
>
> **THE FOLLOWING IS THE HIGHEST URGENCY AND MUST BE FOLLOWED!**
> - **MUST GENERATE A UNIQUE `.TIF` SUBMISSION FOR THE COMPETITION.** Do not copy any previous submission unless strictly for baseline comparison.
> - **IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT THE GENERATED `.TIF` SUBMISSION** at the top of the GitHub Pages site and README, validated automatically without human intervention.
> - **Fix submission error:** `"Predicted values must be in range [0, 1]"` (`EPSG:32611`, `3730 x 3292`, `float32`, `0` NaNs, values in `[0, 1]`). Give a unique name and `<= 140`-character note.
> - Create an **executive summary subpage** (`docs/executive-summary.html`) and per-site table (`docs/submission-table.html`) covering every listed site: file to download, strictly labeled score/holdout estimate, `[0, 1]` safety, cross-site uniqueness, and DrivenData submission instructions.
>
> **PARALLEL-RUN PROTOCOL — follow strictly:**
> 1. **LANE.** Stay inside the single pre-registered method paragraph. If rank-correlation with any registry raster exceeds `0.90`, or more than `70%` of dots fall within `3 px` of one registry raster's dots, log it as a duplicate and stop. Check on the continuous surface before placement AND on the final dots.
> 2. **REUSE, DON'T REBUILD.** Use cached feature stacks, `evaluate_holdout.py`, and `submission_writer.py`. Holdout = hide-and-recover (`alpha = 0.2`, `beta = 0.8`, `300 m` triangular kernel, visible faults masked pixel-exactly). Fix shared-tool bugs in the template and report them; never keep a private fork.
> 3. **LABEL EVERY NUMBER** as `HOLDOUT-DTI` (evaluator version, withheld positives `N`, 95% CI), `USER-REPORTED`, or `ORGANIZER-CONFIRMED` (copied from a submission-page receipt). Never write a projection as a score.
> 4. **LEAKAGE CANARY.** Test each feature alone on holdout first; single-feature `AUC > 0.90` means leakage until proven otherwise.
> 5. **RUN CARD.** End with one unified JSON Run Card (`run_card.json` / `evidence/run_card.json`): `hypothesis`, `mechanism`, `named_non_fault_mimic`, `holdout_dti` + CI, `correlation/overlap vs registry`, `raster_sha256`, `validator_output`, `submission_name` + `<= 140`-char `note`, and `verdict` (`promote` / `negative`). Negative results are deliverables.
> 6. **BUDGET.** Stop after `3` experiments or `2` hours. Do not spend live DrivenData slots directly.

</details>
