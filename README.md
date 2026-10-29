# KANLERGEMSDOE2 — DOE GEMS fault discovery

> **CURRENT STATUS — 2026-10-29: DO NOT SUBMIT.** New candidate filename: **NONE**. Approved download: **NONE**. New leaderboard-score estimate: **NOT ESTIMABLE**. No candidate surface, dots, holdout, TIFF, or live slot exists. Surface novelty was not computed; final-dot novelty is not applicable, not passed. The frozen 37,654-dot preflight forces at least 82.3418% overlap with one registered raster, above the 70% limit. See the [three-pass review](evidence/review_20261029.md), [refreshed nine-site claims and current remote HEADs](evidence/submission_table_20261029.json), and [five-mechanism prior-art screen](research/2026-10-29_focus-nine-hypotheses.md).
>
> **Historical parallel artifact — NOT APPROVED.** PR #53 added a 20,000-dot blind-interior TIFF, but its generator changes the frozen 37,654-dot budget to bypass the literal lattice lower-bound stop. It has no holdout replay, and its local 29-raster check is not full-registry clearance. Its own format receipt says `submission_authorized: false`. This review did not create or test that artifact; do not treat it as a candidate. See [the audit note](evidence/pr53_artifact_review_20261028.md) and [its run card](evidence/run_card_unique_7da04408edc9.json).
>
> The [executive summary](EXECUTIVE_SUMMARY.md) and [GitHub Pages dashboard](docs/index.html) use the same explicit negative decision. Historical proxy comparisons do not establish a leaderboard win; no organizer receipt binds the reported scores to the listed file hashes.

## Start here

- [GitHub Pages decision dashboard](https://kanlerxz87-cyber.github.io/KANLERGEMSDOE2/) · [local dashboard source](docs/index.html)
- [Executive summary and nine-site comparison](EXECUTIVE_SUMMARY.md) · [2026-10-29 three-pass review](evidence/review_20261029.md)
- [Refreshed score claims / current HEAD table](evidence/submission_table_20261029.json) · [five-mechanism prior-art screen](research/2026-10-29_focus-nine-hypotheses.md)
- [Previous concurrent review](REVIEW_2026-10-28.md) · [artifact numeric inspection](evidence/review_run_card_20261028.json) · [parallel preflight replay](evidence/preflight_replay_20261028.json)
- [Current negative JSON run card](evidence/current_run_card.json) · [independent replay and three-pass review](evidence/review_20261028_lattice_and_site.md) · [exact-byte release audit](evidence/release_audit_20261028.json)
- [DSLUP revalidation](evidence/dslup_literal_revalidation_20261027.json) · [three-pass review](evidence/review_20261027_session3.md)
- [Standing prompt and values](PROMPT.md) · [frozen lane and protocol](registry/preregistration_htcads.json) · [preregistration status](registry/PREREGISTRATION_STATUS.md)
- [Historical preregistration notes](research/2026-10-27_htcads_hypotheses.md) · [superseded 2026-10-28 slate](research/2026-10-28_focus-nine-hypotheses.md) · [focus-nine evidence supplement](evidence/review_20261028_focus_nine.md) · [dated source catalog](registry/source_catalog_20261027.json)

## Why the release stopped

At the frozen budget of **37,654** positive pixels, a SHA-pinned owner-mirror registry lattice covers 5,160,724 of 5,167,373 footprint pixels within three pixels. Only 6,649 pixels remain uncovered. Therefore **at least 31,005 / 37,654 = 82.341849%** of *any* placement necessarily overlaps that single registry raster, above the user's 70% stop. The literal rule does not exempt calibration controls. The preflight stopped **before fitting or placing dots**. Altering the frozen budget or declaring an exception to evade this gate would violate the standing protocol.

The earlier DSLUP research TIFF is byte-verified (SHA-256 `8f66f32c56482501808977ac504a0abf517ff75db0af2b56774c0f08d476fbe3`): **37,647 / 37,654 = 99.9814%** of its dots overlap the same lattice. Its local shape, CRS, transform and in-footprint range pass, but uniqueness fails. [Download its current negative validator result](evidence/dslup_literal_revalidation_20261027.json), not an authorization. The older HTCADS TIFF (SHA-256 `f482d3bad4b390470be06363b60867c8e42942101271caf4fa82ae3c3975abeb`) likewise fails and is research only. Historical evidence files are preserved for audit and may contain superseded detector-only claims.

Two concurrent PRs added research TIFFs while this review was underway. **Neither is approved:** PR #34's 37,654-dot file has 37,652/37,654 (99.9947%) witness overlap and 184 known-fault dots. PR #36's 15,000-dot file has 66.0% witness overlap, but deliberately places 5,100 dots in lattice gaps and lowers the frozen budget to evade the gate; 107 dots are on catalogue, with no measured holdout or full-registry clearance. Its prior promotion is superseded. See the [executive table](EXECUTIVE_SUMMARY.md) and [independent review](evidence/off36_independent_check_20261027.json).

## What the scores do and do not establish

The **0.2778** attributed to GEMSDOE32 is USER/OWNER-REPORTED; no organizer receipt ties it to the B2 file hash. Exact mask analysis shows GEMSDOE32 is GEMSDOE25 with 6,436 dots near the mirrored known-fault mask removed, but cannot reveal the hidden-label cause of the reported score. GEMSDOE25 and 30 have identical positive masks; GEMSDOE36 contains the GEMSDOE32 mask plus 1,200 dots.

All nine requested peer repository HEADs were refreshed on 2026-10-29 and differ from the historical artifact refs. This is a source update, not a live standings check. **GEMSDOE28's 0.2710 is a disputed supplied claim:** its current page retains the claim but its current score registry says its current downloads are unscored/no own scored artifact, and the current all-finite page file has a different hash from the old pinned NaN-outside file. The 0.2708 H27-4 site/file attribution is also unresolved. Do not promote either as organizer-confirmed.

A current GEMSDOE32 peer correction says its favorable H51-1 **HOLDOUT-DTI 0.115134** is a fold-local re-emission arm, **not** the downloadable TIFF. The peer's saved-byte static recheck reports 0.002289 [0.001847, 0.002676] for the H51 TIFF versus 0.004515 [0.003837, 0.005278] for B2 under that peer evaluator (N=22,232); the saved file also fails the peer's literal r13 lattice rule. This peer evidence is not our experiment or a leaderboard score and does not support a public-score improvement.

The archived DSLUP procedure reports **HOLDOUT-DTI 0.125925**, `GEMSDOE32-HIDE-RECOVER-v3.0`, 22,232 withheld-positive occurrences, 95% CI [0.112880, 0.138176]. Another historical KG2 benchmark reports **HOLDOUT-DTI 0.177056**, `gems-segment-pooled-v1`, 60,988 withheld-positive pixels, 95% CI [0.163673, 0.190831]. The two evaluators and populations differ, so these values are not directly comparable. Neither original OOF prediction set has been independently replayed here. Neither is a leaderboard score or a validated estimate for any new submission. SGMC prevalence-calibrated numbers rely on an **unverified inferred hidden-truth count** and are research transformations, not measured holdout DTI, organizer scores, or valid promotion gates.

The latest local public-leaderboard snapshot is dated 2026-10-28 00:05 UTC: #1 **0.4544**, #5 **0.3566**, #25 **0.3195**. It was not refreshed on 2026-10-29 and does not confirm any focus-site file scores. The [feed](docs/data/public_leaderboard.json) is a dated snapshot, not a live board; consult the [official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) only through authorized access.

## Safe workflow and current limitations

1. Read [`AGENTS.md`](AGENTS.md), this README, the preserved standing brief in [`PROMPT.md`](PROMPT.md), and the frozen lane before doing work. Values: **Maximize P(Win)** and **Own the Outcome**.
2. No fresh lane, no budget change, no exemptions and no automated upload are authorized by this result. Resolve the literal conflict explicitly and specify a new method/lane before a new run. Stay within the user's ≤3 experiments or 2 hours.
3. Reconstruct catalogue features from visible faults separately for each spatial fold, hide whole connected segments with a buffer, mask known-fault pixels exactly, run a separate leakage canary on **every** feature, and compare pooled DTI and paired spatial CI to a comparable baseline. AUC >0.90 is leakage until disproven.
4. Verify the full current registry for **both** surface rank correlation and final-dot overlap; verify organizer-authenticated template/labels; replay any historical baseline, verify the portal exterior behavior and current account quota; run an independent selector. Shared validators currently intentionally have **no positive authorization path**.
5. Only after an approved selector produces an exact SHA, the user may upload that TIFF/one-file ZIP to DrivenData → Submit → Make new submission, use the approved unique name and ≤140-character note, retain the receipt, and make the competition's single final selection. **This is future guidance, not approval to submit an existing file.**

Competition data used here are SHA-verified **owner-hosted mirrors**, not authenticated organizer downloads; the official data page required login. A concurrent [availability audit](evidence/data_availability_20261027.json) reported 15 of 30 external mirror files unavailable. The earlier portal rejection bytes and receipt were not retained, so its precise cause is unknown. A finite all-zero exterior passed the local numeric checks; the official page says null/NaN outside bounds. Portal acceptance of either encoding for the irregular mirrored footprint remains unverified.

GitHub Pages currently has both legacy main-branch publishing and an Actions deploy configured. A parallel [Pages audit](evidence/pages_deployment_20261027.json) reports a 403 when switching to an Actions-only source; a repository administrator must resolve that setting and verify the deployed feed. Until then, treat the leaderboard as a dated snapshot, not guaranteed live.

## Reproduce the non-submission audit

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python scripts/restore_data.py --group core --target-dir data/review_20261027
python scripts/restore_data.py --group scored --target-dir data/review_20261027
GEMS_DATA_DIR="$PWD/data/review_20261027" python scripts/restore_focus_sites.py
GEMS_DATA_DIR="$PWD/data/review_20261027" python scripts/audit_release.py \
  --out evidence/release_audit_20261027.json --card-out evidence/current_run_card.json
GEMS_DATA_DIR="$PWD/data/review_20261027" python scripts/validate_submission.py \
  --tif docs/downloads/kanlergems2-dslup-uniq-q15k-37654dots-20261027T181253Z-c71122d5-zeros.tif \
  --run-card evidence/dslup_unique_slot_run_card.json \
  --out evidence/dslup_literal_revalidation_20261027.json  # exits 1: expected negative
python scripts/build_site.py
python -m compileall -q src scripts tests
python -m pytest -q
```

See the [review record](evidence/review_20261027_session3.md) for exact restored artifacts, checks and limitations. An archived runner is not a submission workflow. Public pages are generated and published by [the Pages workflow](.github/workflows/pages.yml); a public feed never conveys account quota or a file-specific score.

## Official source starting points

[Competition objective, DTI and file format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) · [official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf) · [known-fault masking clarification](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516) · [official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) · [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · [DOE INGENIOUS](https://gdr.openei.org/submissions/1391) · [USGS 3DEP](https://www.usgs.gov/3d-elevation-program) · [NASA OPERA](https://www.earthdata.nasa.gov/data/projects/opera).

## Preserved standing project brief

The following prior-session prompt record is retained as it appeared before this audit. The transcript is not available verbatim in this session; the quoted earlier `0 NaNs` shorthand must be read with the clarified current exterior caveat above.

<details>
<summary><strong>📋 Preserved Standing Project Prompt &amp; PARALLEL-RUN PROTOCOL (Read at the Start of Every Session)</strong></summary>

See also [`PROMPT.md`](PROMPT.md).

> **Current conditional enforcement (2026-10-29):** The historical “MUST GENERATE” wording below is not authorization to bypass a failing gate. Generate a candidate only if every frozen-lane, novelty, holdout, leakage, format, and approval gate passes. If any gate fails, candidate filename and approved download are **NONE**; clearly state **DO NOT SUBMIT**. Never change the frozen budget or placement to evade a stop.
>
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
