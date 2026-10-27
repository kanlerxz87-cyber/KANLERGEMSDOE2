# KANLERGEMSDOE2 — geothermal fault discovery

> **CURRENT DECISION: NOT OK TO SUBMIT.** No new model, GeoTIFF, score estimate or live-slot decision was produced in this review. The earlier Session-2 “control-separated” approval and Session-1 approval are withdrawn: the user's literal rule has no lattice exception. The [negative run card](evidence/current_run_card.json) and [fresh exact-byte audit](evidence/release_recheck_20261027.json) govern; archived artifacts are research only.

[Decision dashboard](docs/index.html) · [Executive summary & submission guide](docs/executive-summary.html) · [Nine-site comparison](docs/submission-table.html) · [Research slate](research/2026-10-27_htcads_hypotheses.md)

## Why we stopped

The registered spacing-5 lattice covers **5,160,724 of 5,167,373** footprint pixels within 3 pixels; only **6,649** lie outside that neighborhood. Any placement of **37,654 distinct in-footprint dots** must overlap at least **31,005 / 37,654 = 82.3418%**, exceeding the strict 70% limit. The witness proves failure, not full registry coverage. The proof is specific to this budget, footprint, radius and witness; it does not cover every smaller raster. Do not remove the lattice or reduce the frozen budget to evade the rule.

The previously promoted [DSLUP TIFF](docs/downloads/kanlergems2-dslup-uniq-q15k-37654dots-20261027T181253Z-c71122d5-zeros.tif) has **37,647 / 37,654 = 99.9814%** overlap, SHA-256 `8f66f32c56482501808977ac504a0abf517ff75db0af2b56774c0f08d476fbe3`. The previous [HTCADS TIFF](docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif) has **37,642 / 37,654 = 99.9681%**, SHA-256 `f482d3bad4b390470be06363b60867c8e42942101271caf4fa82ae3c3975abeb`. Both are **research-only; do not submit**. The [fresh DSLUP validator](evidence/dslup_literal_revalidation_20261027.json) fails the literal witness and the missing full-registry, surface, independent replay and quota gates.

Parallel work merged while this review was underway. Its [37,654-dot PR #34 TIFF](docs/downloads/kanlergemsdoe2-unique-hypothesis1-binary-20261027.tif) overlaps the lattice **99.9947%** and has **184** on-catalogue dots, contrary to its old note. Its [15,000-dot PR #36 TIFF](docs/downloads/36GEMSDOE-off-catalogue-blind-geothermal-targeting-20261027T234345Z-2ecaae7a056e-zeros.tif) has **66.00%** overlap with this one witness, but uses an unapproved reduced budget and targeted lattice-gap placement, has **107** on-catalogue dots, and has no independent holdout or complete registry clearance. The frozen-budget lower bound does **not** apply to that smaller TIFF. Both are **research only; do not submit**. See the [independent review](evidence/independent_witness_20261027.json) and [15,000-dot validator](evidence/off36_literal_revalidation_20261027.json).

Both TIFFs pass local single-band float32, grid and [0,1] checks against the **owner mirror**, not an authenticated organizer sample. They use zeros outside the irregular footprint while the mirror uses NaN; neither encoding is proven accepted. The reported prior form rejection, `Predicted values must be in range [0, 1]`, has no retained rejected bytes or organizer diagnosis. No local check proves the cause or portal acceptance.

## Nine-site findings

The largest supplied historical number is GEMSDOE32 **0.2778, USER/OWNER-REPORTED, unverified**; no submission-page receipt ties that number to the file. Each of the nine exact owner-mirror masks exceeds 70% directional overlap with another focus raster. GEMSDOE25 and 30 have identical positive masks; GEMSDOE32 equals 25 after removing 6,436 dots within 2 px of known faults; GEMSDOE36 contains 32 plus 1,200 dots. Pruning might improve precision, but these facts cannot prove why reported scores changed or what will match hidden labels. See the [full per-site table](docs/submission-table.html).

The official public leaderboard snapshot observed **2026-10-27** was #1 **0.4544** and #5 **0.3566**; these are leaderboard observations, not file-linked receipts or forecasts. An automatic Pages refresh shows dated snapshots and flags refresh failures. The [research slate](research/2026-10-27_htcads_hypotheses.md) ranks four physical hypotheses, identifies exact inputs and mimics, and labels access and novelty uncertainties. None was fitted. Historical holdouts are labeled HOLDOUT-DTI with evaluator, positive count and CI in the [executive summary](EXECUTIVE_SUMMARY.md); they were not independently replayed here and are not projections.

## Reproduce the negative audit (no upload)

Requires Python 3.11, GitHub access and sufficient local disk/RAM. GitHub mirror SHA-256 confirms identity to the manifest, **not** official organizer provenance. The competition's authenticated data page requires login. Bulk inputs and the prepared 30-column feature cache default to `.cache/gems_data`, which is ignored **and excluded from workspace snapshots**; restore them again in a fresh workspace or set `GEMS_DATA_DIR` to durable external storage.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
bash scripts/download_competition_data.sh --group core
bash scripts/download_competition_data.sh --group scored
.venv/bin/python scripts/restore_focus_sites.py
# Known partial failure: 15 of 30 external files were unavailable (14 deleted-ref, 1 missing CSV).
# This command continues through all entries, writes data/restore_receipt_external.json, and exits 1.
bash scripts/download_competition_data.sh --group external
# Optional after core restore; no training or label fitting:
.venv/bin/python scripts/prepare_data.py
.venv/bin/python scripts/audit_release.py --out evidence/release_recheck_20261027.json --card-out evidence/current_run_card.json
.venv/bin/python scripts/validate_submission.py --tif docs/downloads/kanlergems2-dslup-uniq-q15k-37654dots-20261027T181253Z-c71122d5-zeros.tif --run-card evidence/dslup_unique_slot_run_card.json --out evidence/dslup_literal_revalidation_20261027.json  # expected exit 1
.venv/bin/python scripts/verify_witness_independently.py  # alternative distance-transform implementation
.venv/bin/python scripts/build_site.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/evaluate_holdout.py --verify-kg2  # archived hash checks only
```

The [partial restore receipt](evidence/data_restore_recheck_20261027.json) records **31/46** manifest files verified and all **15** missing entries; nine focus-site TIFFs were restored separately. It is a dated snapshot, not a guarantee the remote mirrors remain available. The restore tool stages and hashes each file before replacement; it never treats a failed entry as verified. The assigned HTCADS runner stops at the literal preflight. Old parallel-lane entry points are disabled pending a valid assigned protocol and independent replay; their historical code is retained for forensic review.

## Next steps, not current permission

An explicitly authorized protocol resolution is needed before a new placement at this fixed budget. Thereafter: authenticate the official data, recover or replace unavailable sources with verified provenance, inventory the complete current registry, independently rebuild fold-visible features and each feature canary, replay a comparable spatially blocked holdout against the current best with confidence intervals, validate exact output bytes, and verify current account quota in a separate selector. Six declared benchmark run cards and three historical verifier modules are absent, so the same-evaluator current-best inventory is incomplete and the selector fails closed. Only then can any future slot be considered. Do not automatically submit or manufacture a score.

## Values and starting brief

**Maximize P(Win):** Protect scarce live slots; prefer a valid negative result to an unverified projected gain.

**Own the Outcome:** Check bytes and sources, fix shared tools, automate fail-closed gates, and record uncertainty without a manual geological-inspection fallback.

Read this README, the preserved brief below, and [`PROMPT.md`](PROMPT.md) at the start of every session. Earlier score targets in the preserved prompt are historical and do not override the current stop. [`AGENTS.md`](AGENTS.md) contains the operative repository contract.

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
