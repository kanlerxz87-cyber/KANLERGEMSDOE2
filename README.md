# KANLERGEMSDOE2 — DOE GEMS fault discovery

> **CURRENT DECISION: DO NOT SUBMIT.** No new GeoTIFF passed the requested gates, and no competition slot was used in the 28 October 2026 review. Existing TIFFs can be downloaded **for research only**. A different file hash or a local range check is not submission approval.

## Start here

- [Decision dashboard](https://kanlerxz87-cyber.github.io/KANLERGEMSDOE2/) · [nine-site executive table](EXECUTIVE_SUMMARY.md) · [generated local site](docs/index.html)
- [Current negative run card](evidence/current_run_card.json) · [28 October independent audit](evidence/release_audit_20261028_independent.json) · [submission-table data](evidence/submission_table_20261028.json)
- [Corrected 0.2778 forensic](research/2026-10-27_gmv_forensic_02778.md) · [four ranked hypotheses](research/2026-10-27_htcads_hypotheses.md)
- [Standing prompt and values](PROMPT.md) · [frozen HTCADS lane](registry/preregistration_htcads.json) · [preregistration status](registry/PREREGISTRATION_STATUS.md)

## Why no file can be promoted in this lane

The registered, SHA-pinned `13gems` lattice covers **5,160,724 of 5,167,373** in-footprint cells within an inclusive 3-pixel radius. Only **6,649** cells are uncovered. Thus for any 37,654 distinct dots, at least **31,005 / 37,654 = 82.341849%** must overlap this one raster; the protocol stops above 70%. The witness SHA-256 is `b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2`.

Excluding exact known-fault pixels leaves only **6,514** uncovered eligible cells, so at least **31,140 / 37,654 = 82.700377%** must overlap. A budget of **N ≤ 21,713** is necessary to avoid a forced violation in that restricted domain, **not** permission to change the frozen budget and **not** proof of novelty. No exemption is stated for a calibration raster. The runner stopped before fitting or placement. One witness proves failure but not complete-registry clearance; the pre-placement surface and full registry were not checked.

The historical [HTCADS](docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif) (SHA-256 `f482d3bad4b390470be06363b60867c8e42942101271caf4fa82ae3c3975abeb`) and [HPTR](docs/downloads/kanlergems2-hptr-exp-2-37654dots-20261028T014401Z-675d0ff8-zeros.tif) (SHA-256 `2d53632cb161a2172806bae5e82f8c456d5717112504f45ca7ec91a1c1ba8ff3`) research TIFFs have respectively **37,642/37,654** and **37,640/37,654** dots within 3 px of the witness. Both are locally finite and in [0,1] across the mirror grid, but **neither is unique or approved**; organizer acceptance of their exterior encoding is unknown. Earlier HPTR, LOPE and TRBVC canary, holdout and improvement claims remain historical receipts and were not independently replayed here. Do not treat them as validated breakthroughs or leaderboard scores.

## What the nine sites tell us

GEMSDOE32's **0.2778** is the highest **USER/OWNER-REPORTED** score in the focus set; no organizer receipt ties it to a file hash. Its positive mask equals the GEMSDOE25 mask after removing **6,436** dots within 2 pixels of the mirrored catalogue, and GEMSDOE36 contains all GEMSDOE32 dots plus **1,200** more. That geometry suggests a thinning hypothesis, not a proven cause of the score. DrivenData staff say only the exact known-fault pixels are masked; nearby predictions are scored normally and can match new faults. They are **not automatically false positives**. Hidden labels and submission receipts are unavailable.

The public leaderboard has higher observed scores from other participants; this does not prove that a new lane or file will exceed 0.2778. No new holdout, leakage-canary measurement, leaderboard estimate or raster hash is claimed in this review. The archived DSLUP **HOLDOUT-DTI 0.125925** is a prior receipt, `GEMSDOE32-HIDE-RECOVER-v3.0`, N=22,232 withheld-positive occurrences, 95% CI [0.112880, 0.138176]; its original out-of-fold predictions were not replayed and it is not a leaderboard score.

The [public feed](docs/data/public_leaderboard.json) uses the official leaderboard's first public table partial and records the UTC observation time. If refresh fails it exposes a dated stale snapshot, never a current score or account quota. Check the [official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) for current ranks. Pages Actions successfully deployed during review even though a legacy Pages source is also configured; a denied settings-change attempt by itself does not prove a deployment problem.

## Inputs, safety and next steps

- On 28 October the [input audit](evidence/data_availability_20261028.json) SHA-verified **4/4 core, 12/12 scored and 30/30 external** manifest entries from owner-hosted mirrors, plus all nine focus TIFFs in the release audit. These hashes do not authenticate organizer or official-source provenance. Large caches are ignored and may need restoration.
- The [preparation receipt](evidence/data_preparation_recheck_20261028.json) records a rebuilt generic **5,167,373 × 30** feature stack and checked band order. This is **not** an HTCADS-specific stack build, a leakage canary, or a holdout replay.
- The reported portal error, `Predicted values must be in range [0, 1]`, cannot be diagnosed without the rejected file and receipt. The official format calls for a single float32 band matching CRS, shape and transform, [0,1] inside, and null/NaN outside bounds; the zero-exterior files pass local whole-array checks but lack portal acceptance receipts.
- If the user explicitly resolves the conflicting registry rule, preregister the assigned lane before resuming. Use shared tools, rebuild catalogue-derived features from visible segments for each buffered spatial fold, run every single-feature leakage canary, compare pooled DTI and paired spatial CI to the same-evaluator best, and check both surface and final dots against the complete registry. A separate account-aware selector must verify quota and preserve an actual organizer receipt. No human geological-inspection fallback or automatic live upload is used.
- Values: **Maximize P(Win)** and **Own the Outcome**. Three audit/implementation passes and their limitations are recorded in [the current review](evidence/review_20261028_independent.md).

## Reproduce the negative audit

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python scripts/restore_data.py --group all --target-dir data/review_local
GEMS_DATA_DIR="$PWD/data/review_local" python scripts/restore_focus_sites.py
python scripts/audit_data_inputs.py --data-dir data/review_local --out data/review_local/input_audit.json
GEMS_DATA_DIR="$PWD/data/review_local" python scripts/prepare_data.py --receipt data/review_local/preparation_receipt.json
GEMS_DATA_DIR="$PWD/data/review_local" python scripts/audit_release.py \
  --out data/review_local/release_audit.json --card-out data/review_local/run_card.json
GEMS_DATA_DIR="$PWD/data/review_local" python scripts/run_htcads_experiments.py  # expected DUPLICATE STOP; exit 1
python scripts/build_site.py
python -m compileall -q src scripts tests
python -m pytest -q
```

The builder uses the checked-in dated audit and matching current card; the commands above write new cache receipts and do not replace them. See [the review record](evidence/review_20261028_independent.md) for the 28 October checks and remaining limitations.

## Official source starting points

[Competition objective, DTI and file format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) · [official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf) · [known-fault masking clarification](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4) · [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) · [USGS GeoDAWN](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7) · [DOE INGENIOUS](https://gdr.openei.org/submissions/1391) · [USGS 3DEP](https://www.usgs.gov/3d-elevation-program) · [NASA OPERA DISP-S1](https://www.earthdata.nasa.gov/data/catalog/asf-opera-l3-disp-s1-v1-1).

## Preserved standing project brief

The following prior-session prompt record is retained as it appeared before this audit. The transcript is not available verbatim in this session; the quoted earlier `0 NaNs` shorthand must be read with the clarified current exterior caveat above.

<details>
<summary><strong>📋 Preserved Standing Project Prompt &amp; PARALLEL-RUN PROTOCOL (Read at the Start of Every Session)</strong></summary>

See also [`PROMPT.md`](PROMPT.md).

> **Core Values:** **Maximize P(Win)** and **Own the Outcome**. No human-inspection fallback exists: automated validation gates fail closed.
>
> Review the repo and execute any next steps from previous sessions first.
>
> Focus on the highest-scoring submissions from the 9 focus sites (`GEMSDOE24`, `GEMSDOE25`, `GEMSDOE27`, `GEMSDOE28`, `GEMSDOE30`, `GEMSDOE31`, `GEMSDOE32`, `GEMSDOE33`, `GEMSDOE36`) and cross-check across all listed GEMSDOE and sister sites (`KANLERGEMSDOE1..3`, `EUGGEMSDOE1..3`, `WBGGEMSDOE1..3`, `GINNYGEMSDOE1..3`, `GEMSDOEkarage1..3`, `ApartGEMSDOE1..3`, `GEMSDOESASS1..3`, `GEMSDOE..GEMSDOE92`, including `kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros`).
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
