# KANLERGEMSDOE2 — geothermal fault discovery

> ## CURRENT DECISION: NEGATIVE / DO NOT SUBMIT
>
> No TIFF is approved for a live slot. This review created **no** new raster, holdout result, score estimate, or submission. The archived HTCADS, DSLUP, and later parallel hypothesis-1 TIFFs may be downloaded **for research only**. Earlier control-exempt promotion claims are superseded; no such exemption was authorized.
>
> **[Decision dashboard](docs/index.html)** · **[Executive comparison](docs/executive-summary.html)** · **[JSON run card](evidence/current_run_card.json)** · **[Exact-byte audit](evidence/release_audit_20261027.json)**

## Why the lane stopped

The fixed lane requires **37,654 distinct dots**, but a registered spacing-5 lattice has only **6,649** footprint pixels farther than 3 px from it. At least `37,654 - 6,649 = 31,005` dots must therefore overlap the lattice: **82.3418%**, above the literal **>70%** stop. The registered witness is not exempt. The bound is specific to this budget and does not prove every smaller raster fails; quietly changing the budget to evade the gate is not permitted.

The archived [HTCADS TIFF](docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif) (SHA-256 `f482d3bad4b390470be06363b60867c8e42942101271caf4fa82ae3c3975abeb`) overlaps that witness **37,642/37,654 = 99.9681%**. The [DSLUP research TIFF](docs/downloads/kanlergems2-dslup-uniq-q15k-37654dots-20261027T181253Z-c71122d5-zeros.tif) overlaps **37,647/37,654 = 99.9814%**; its former validator falsely returned a promotion after excluding controls. [Corrected receipt](evidence/dslup_literal_validation_20261027.json).

A TIFF added by a concurrently merged PR was also independently reopened: [`kanlergemsdoe2-unique-hypothesis1-binary-20261027.tif`](docs/downloads/kanlergemsdoe2-unique-hypothesis1-binary-20261027.tif), SHA-256 `f0cb191420da26d19ceccfd65f8987537f714d1b28660f8e3690ff2008a2b539`, overlaps **37,652/37,654 = 99.9947%** and has **184 positive pixels on the restored known-fault catalogue**, contrary to its earlier note. It is **not unique under the literal rule; do not submit**. See its [corrected audit](evidence/parallel_hypothesis1_literal_audit_20261027.json).

## What the historical scores show

The highest of the nine supplied numbers is GEMSDOE32 **0.2778, USER/OWNER-REPORTED**, with no submission-page receipt. Its positive mask equals GEMSDOE25's after removing 6,436 dots within 2 px of the restored catalogue; GEMSDOE25 and 30 have identical positive masks, and GEMSDOE36 contains all GEMSDOE32 dots plus 1,200. Pruning may improve precision, but hidden-label attribution and a causal explanation are unproven. A higher result is possible in principle, but no new candidate has demonstrated one. All nine exceed 70% directional overlap with another of the nine; see the [per-site table](docs/executive-summary.html).

The previous HTCADS receipt records **HOLDOUT-DTI 0.112353**, evaluator `GEMSDOE32-HIDE-RECOVER-v3.0`, **22,232 withheld-positive occurrences**, 95% CI **[0.098995, 0.125743]**. This historical result was not independently replayed and is not an organizer score or leaderboard forecast. The public leaderboard snapshot observed on 2026-10-27 had #1 **0.4544**, #5 **0.3566**; neither number scores this candidate. The six-hour Pages feed attempts refresh and labels failures/stale snapshots.

Four qualitative [research hypotheses](research/2026-10-27_htcads_hypotheses.md) describe layers, physical mechanisms, named non-fault mimics, prior-work differences, costs and official data sources. None was fitted here; the top direction is multi-height magnetic/gravity cross-gradient stability plus independent hydrothermal corroboration.

## Range error and data limits

The exact rejected bytes and portal diagnostic were not supplied, so the cause of `"Predicted values must be in range [0, 1]"` is **unknown**. The audited research TIFFs are locally single-band float32 on the pinned owner-mirror EPSG:32611, 100 m, 3,730×3,292 grid, finite and in [0,1]; that is **not** an organizer acceptance receipt. They use zeros outside the footprint while the mirrored sample and official text use NaN/null; neither encoding is proven accepted. Check the actual file, footprint, grid, nodata tag, NaNs/infinities and range before any future submission.

Core **4/4**, scored **12/12**, and the **9/9** focus TIFFs were restored from hash-pinned owner mirrors. Of 30 external entries, **15 verified; 15 unavailable (404)**: 13 derived 10 m DEM channels, their manifest, and one heat-flow CSV. Later available entries were still checked; the [availability receipt](evidence/data_availability_20261027.json) lists each. The 30-column shared base feature cache was prepared. Hashes establish identity to owner mirrors, not independently authenticated organizer or official-source origin; exact external files and replay caches remain incomplete.

## Reproduce locally (no upload)

Python 3.11, a GDAL-compatible rasterio wheel, GitHub access and several GB of disk/RAM are needed. Bulk inputs and `.venv` are ignored and must be restored in a fresh workspace. Expected failures are reported, never converted to success:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/restore_data.py --group core
.venv/bin/python scripts/restore_data.py --group scored
.venv/bin/python scripts/restore_data.py --group external  # exits 1 while 15 pinned entries are unavailable
.venv/bin/python scripts/restore_focus_sites.py
.venv/bin/python scripts/prepare_data.py                  # optional 30-column cache
.venv/bin/python scripts/audit_release.py                 # exact-byte witness and negative card
.venv/bin/python scripts/build_site.py
.venv/bin/python -m pytest -q
```

`GEMS_DATA_DIR` overrides `.cache/gems_data`. Restore receipts are per group in ignored `data/`. The current shared validator and its legacy compatibility entry point refuse upload when references, full novelty, independent replay or quota are missing. Legacy experiment CLIs are disabled; they used partial/exempt registries and cannot safely run in this lane. Fixes also reject invalid evaluator/writer inputs instead of silently clipping them, and align the idealized marginal threshold to `alpha × DTI`.

Only after the protocol conflict is explicitly resolved, a new properly assigned lane passes complete surface/final registry checks, every feature canary, buffered visible-only holdout with confidence intervals, and the current account quota is verified may a separate selector approve an exact file. Then follow the [official submission page](https://www.drivendata.org/competitions/306/competition-doe-gems/) and save its receipt. No weekly slot was selected or spent in this review.

## Values and starting brief

**Maximize P(Win):** Protect scarce live slots; prefer a valid negative result to an unverified projected gain.
**Own the Outcome:** Restore/check bytes, verify sources, fix shared tools, use automatic fail-closed checks, document uncertainty, and do not rely on a manual geological inspector.

Read this README, the condensed brief below, and [`PROMPT.md`](PROMPT.md) at the start of every session. The preserved request is a structured summary, not a verbatim transcript; it records earlier score targets as historical; it does not override the current stop or confer score authenticity. See [`AGENTS.md`](AGENTS.md) for the operative safety contract and [`docs/irregularities.html`](docs/irregularities.html) for unresolved blockers.

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
