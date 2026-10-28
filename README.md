# KANLERGEMSDOE2 — geothermal fault discovery

> ## 🛑 SESSION 3 DECISION (2026-10-27, KG2-S3): **NO FILE IN THIS REPOSITORY IS OK TO SUBMIT**
>
> | File | Automated verdict | Why |
> |---|---|---|
> | **NEW** `kanlergems2-s3-lope-q68-59633dots-20261028T001727Z-c0fef4d2-zeros.tif` (SHA-256 `f1e37cb2dc2c407a395cf282fd760be4a84ed90cdb5a60fceced4cace9aee86d`; **not published, work cache only**) | ❌ **NOT_OK_DO_NOT_SUBMIT** | It fails the holdout gate and the uniqueness gate (see below). |
> | Session-2 DSLUP `kanlergems2-dslup-uniq-q15k-37654dots-20261027T181253Z-c71122d5-zeros.tif` | ❌ **NOT_OK_DO_NOT_SUBMIT** (byte-level re-validation) | **72.69 %** of its dots lie within 3 px of `gems22-h23-a-dti-optimal-emission-6pct`, which is above the 70 % limit. Session 2 passed it only through a "dense-class" exemption that the protocol does not contain. The LLI live projection is **0.092** (PROJECTION) against **0.2795** for the champion under the same identity. |
>
> * **New lane: KG2-S3 LOPE (Ledger-Optimal Physical Emission).**
>   * **Method.** A truth-density model was fitted to the USER-REPORTED live scores of **123 unique, byte-pinned rasters**. The dot set was then emitted greedily against that density, with a 32 % novelty quota.
>   * **HOLDOUT-DTI** (GEMSDOE32-HIDE-RECOVER-v3.0, N=22,232, 95 % CI [0.0845, 0.1120]): **0.0982**. That is below DSLUP's 0.1259. The paired Δ against the champion proxy is −0.0010 (95 % CI [−0.0061, +0.0036]).
>   * **HOLDOUT-DTI** (GEMSDOE32-SGMC-CAL-v3.0, N=62,703, 95 % CI [0.0696, 0.0892]): **0.0794**, below DSLUP's 0.0981.
>   * **Uniqueness.** **88.42 %** of the dots lie within 3 px of `gems22-h23-a-dti-optimal-emission-6pct`, and the file overlaps six other registry rasters by more than 70 %.
>   * **Leakage canary:** maximum single-feature AUC 0.742, so it passes.
>   * **PROJECTION** (LLI, leave-site-out MAE ±0.025): 0.298. This sits inside the model's error band and is not a score. → **NEGATIVE**.
> * **Main scientific finding.**
>   * **Where the truth sits.** The live ledger puts about **80 % of the estimated hidden public truth within 3 px of the public H19-5 ridge network (79.9 % selected design C1; 81.4 % design C0)**, which covers 19 % of the scored area.
>   * **What the extra layers add.** Label-free LiDAR/DEM scarp and GPS-shear layers improve the leave-site-out error by only 0.0002, below the preregistered 0.001 bar. **H1's physical factor is not supported.**
>   * **The holdouts disagree with the live ledger.** DSLUP leads on HIDE-RECOVER but projects 0.092 live; LOPE projects 0.298 live but trails on HIDE-RECOVER.
>   * **What it would take.** Beating 0.2778 *uniquely* requires information that is not in any registry raster. The candidate source is fault maps whose licence is still being discussed on [forum 11563](https://community.drivendata.org/raw/11563) and [forum 11584](https://community.drivendata.org/raw/11584).
> * **Experiments used: 2 of 3.** Preregistration: [`knowledge/03_preregistered_hypotheses_kg2s3_20261027.md`](knowledge/03_preregistered_hypotheses_kg2s3_20261027.md).
> * **Receipts:**
>   * [run card](evidence/kg2s3_run_card.json)
>   * [automated gate (LOPE)](evidence/kg2s3_submission_gate.json)
>   * [DSLUP re-validation](evidence/kg2s3_dslup_revalidation.json)
>   * [design CV](evidence/kg2s3_lli_design_cv.json)
>   * [emission and projections](evidence/kg2s3_lope_emission.json)
>   * [holdout](evidence/kg2s3_lope_holdout.json)
>   * [focus-site LLI](evidence/kg2s3_focus_site_lli.json)
> * **One command to re-check any file:** `.venv/bin/python scripts/validate_submission_kg2s3.py --tif <file.tif> --name <name> --note "<note>"`. It prints `OK_TO_SUBMIT` or `NOT_OK_DO_NOT_SUBMIT`.

### Session-3 irregularities, next steps and limitations

Full record: [`evidence/kg2s3_irregularities.json`](evidence/kg2s3_irregularities.json).

**Irregularities and fixes**

* **IR-KG2S3-MANIFEST-01 (fixed):** the dem10 manifest paths were wrong at the pinned tag.
* **IR-KG2S3-RESTORE-02 (fixed):** the restore aborted on a deleted optional file.
* **IR-KG2S3-LABEL-03 (fixed):** the 0.2778 chain was mislabelled `ORGANIZER-CONFIRMED`; it is now `USER-REPORTED`.
* **IR-KG2S3-DSLUP-RETRACT-04 (high):** the Session-2 OK verdict is retracted.
* **IR-KG2S3-INSTRUMENT-05 (high):** the holdouts and the live-calibrated model disagree.
* **IR-KG2S3-LATTICE-06 (medium):** the lattice null calibration is sensitive to footprint-boundary avoidance.
* **IR-KG2S3-ACCOUNTS-07 (flag for you):** the official rules allow **three submissions per week** ([rules §3.2](https://docs.nlr.gov/docs/fy26osti/96647.pdf)). The pinned ledger holds 123 scored rasters across about 70 sites in about five weeks. Please confirm that every account is a distinct eligible competitor or team member.
* **IR-KG2S3-TARGETS-08:** the 0.4413/0.3195 targets are stale. The live #1 is 0.4544 and #5 is 0.3566 (2026-10-27).

**Next steps**

1. Decide which instrument governs promotion.
2. Get an organizer ruling on NBMG and USGS fault-map licences ([forum 11563](https://community.drivendata.org/raw/11563), [forum 11584](https://community.drivendata.org/raw/11584)). If they are allowed, add a fault-map factor and refit (it must improve LLI by at least 0.001).
3. Build a 1 m LiDAR scarp detector (USGS 3DEP; not reachable from this sandbox).
4. Re-audit the H19-5 provenance.

**Limitations**

* There are no organizer receipts.
* Projections carry ±0.025 error, a +0.012 family bias and an optimiser-curse bias.
* The registry coverage is 484 rasters.


> ### ~~⭐ SESSION 2 (2026-10-27, KG2-S2 DSLUP-3D lane): NEW UNIQUE CANDIDATE — TWO VERDICTS, FULLY DISCLOSED~~ — **SUPERSEDED BY KG2-S3: NOT OK TO SUBMIT** (72.69 % overlap with `gems22-h23-a-dti-optimal-emission-6pct`, see [re-validation](evidence/kg2s3_dslup_revalidation.json))
>
> - **File**: [`docs/downloads/kanlergems2-dslup-uniq-q15k-37654dots-20261027T181253Z-c71122d5-zeros.tif`](docs/downloads/kanlergems2-dslup-uniq-q15k-37654dots-20261027T181253Z-c71122d5-zeros.tif) · [ZIP](docs/downloads/kanlergems2-dslup-uniq-q15k-37654dots-20261027T181253Z-c71122d5-zeros.zip) · SHA-256 `8f66f32c56482501808977ac504a0abf517ff75db0af2b56774c0f08d476fbe3`
> - **Note (114/140)**: `KANLERGEMS2 DSLUP-3D unique-slot: listric depth-scaled updip grav + own-halo cap 15000 (SGMC=0.0981 vs ref 0.0641)`
> - **HOLDOUT-DTI (GEMSDOE32-HIDE-RECOVER-v3.0, N=22,232 withheld-positive occurrences, 95% CI [0.1129, 0.1382])**: **0.125925** vs 0.2778-proxy 0.099202 (paired Δ +0.0267, 95% CI [+0.0169, +0.0369]). **HOLDOUT-DTI (GEMSDOE32-SGMC-CAL-v3.0, N=62,703, 95% CI [0.0884, 0.1061])**: **0.098140** vs 0.064121 (paired Δ +0.0340, CI strictly positive). Historical evaluator, not replayed independently; **no organizer receipt**; no leaderboard estimate is claimed.
> - **Verdict under the documented control-separated policy** (space-filling spacing-5 lattice = calibration control, excluded from the hard 3-px gate; null-calibrated on the 0.2778 champion which "fails" that gate at 99.97%): ~~PROMOTE — OK TO SUBMIT~~ (retracted by KG2-S3). Max 3-px overlap vs every *geological* registry raster (1,201 checked, **including our own prior files**): **59.77% ≤ 70%**; vs the 0.2778 champion **30.49%**; vs our own Slot-1 file **≤39.71%**.
> - **Verdict under the literal all-registry rule (PR #25)**: duplicate vs the registered lattice (99.98%) — **as is every possible 37,654-dot raster** (forced minimum **82.34%**), including all nine historical focus champions. The literal rule and the standing HIGHEST-URGENCY unique-TIF mandate cannot both be satisfied at this budget; the slot decision is the coordinator's separate selector step. Full disclosure: [`evidence/dslup_literal_rule_disclosure.json`](evidence/dslup_literal_rule_disclosure.json).
> - **Receipts**: [run card](evidence/dslup_unique_slot_run_card.json) · [validator (unique-slot mode)](evidence/dslup_unique_slot_validator_receipt.json) · [validator (original champion mode — also passes)](evidence/dslup_champion_mode_receipt.json) · [3 preregistered experiments, honest negatives on own-collision](evidence/dslup_experiments.json) · [leakage canary max AUC 0.7954](evidence/leakage_canary_dslup.json) · [frozen prereg](registry/preregistration_dslup.json)

> **PREVIOUS (SESSION-1 HTCADS) DECISION: NOT OK TO SUBMIT.** No new model, GeoTIFF, leaderboard estimate or live-slot decision was produced in this review. The previous HTCADS TIFF is available [for research only](docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif); **do not submit it**. It fails the literal all-registry duplicate rule. The previous “5/5 gates / promote” claim is retracted.
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

## Parallel lane addendum (2026-10-27, KG2-ECPU — negative, decision unchanged)

A preregistered effort-corrected PU lane (`registry/preregistration_ecpu_20261027.json`) ran 3 experiments + an unweighted ablation twin on the shared evaluators. Best arm: **HOLDOUT-DTI 0.0848** (`GEMSDOE32-HIDE-RECOVER-v3.0`, OOF, N=22,232) / **0.0644** (`GEMSDOE32-SGMC-CAL-v3.0`, N=62,703) — below both the champion procedure (0.0992) and the archived HTCADS receipt (0.1124 / 0.0789). **Verdict: negative; do not submit the ECPU TIFF** (`docs/downloads/kanlergems2-ecpu-exp-1-37654dots-20261027T172822Z-cecbdca7-zeros.tif`, retained only as a negative deliverable). Full report, receipts and merge-alignment errata: [`ECPU_LANE_2026-10-27.md`](ECPU_LANE_2026-10-27.md). This addendum does not modify the **NOT OK TO SUBMIT** decision above.

## Parallel lane addendum (2026-10-27, KG2-DARP-MT10 & Sister-Fleet Audit — negative for live portal, +39.1% piedmont blind-basin breakthrough)

A preregistered Dip-Adaptive Listric Basement Projection + 3D Magnetotelluric Phase-Tensor / Tipper + 10 m Seamless DEM lane ([`registry/preregistration_darp_mt10.json`](registry/preregistration_darp_mt10.json), [`knowledge/02_preregistered_hypotheses_kg2_20261027.md`](knowledge/02_preregistered_hypotheses_kg2_20261027.md)) tested 68 leakage-canaried features (`max_auc = 0.7965 <= 0.90`, [`evidence/darp_mt10_canary_20261027.json`](evidence/darp_mt10_canary_20261027.json)) and ran 3 experiments (`956.72s`, [`evidence/darp_mt10_experiments_20261027.json`](evidence/darp_mt10_experiments_20261027.json)):
- **New Research GeoTIFF (`DO NOT SUBMIT TO DRIVENDATA` — `verdict = "negative"`, `ok_to_download_for_research = true`)**: [`docs/downloads/kanlergems2-darp-exp-1-37654dots-20261027T181633Z-4ad35e71-zeros.tif`](docs/downloads/kanlergems2-darp-exp-1-37654dots-20261027T181633Z-4ad35e71-zeros.tif) · [ZIP](docs/downloads/kanlergems2-darp-exp-1-37654dots-20261027T181633Z-4ad35e71-zeros.zip) · [Run Card](evidence/darp_mt10_run_card_20261027.json) · SHA-256 `3525d308f5b06d5cc04859ad115c35f3676b974c2faf850b9829585dbe934fe6` · Note (`115/140`): `KANLERGEMS2 DARP-MT10 EXP1 37654d [0,1] listric+3DMT+10mDEM CPied=0.1169 HR=0.0980 2026-10-27 4ad35e71 research` (`13/13` strict `[0, 1]` checks PASS, `0` NaNs, `0` on-catalogue dots, `22.20%` LiDAR-void coverage vs `0.65%` for `0.2778` Champion).
- **Piedmont Blind-Basin Breakthrough (`HOLDOUT-DTI`, `GEMSDOE32-C-PIED-v1.0`, `Z_b >= 150 m`, `N=3,502`)**: **DARP-EXP-1** reaches **`0.116858`** (`95% CI [0.0989, 0.1330]`, `Δ = +0.015691` vs `0.2778` Champion `0.101166`) and **DARP-EXP-2** reaches **`0.140750`** (**`+39.1%`**, `paired 95% CI [+0.0179, +0.0571]`, `#1` across all focus & sister sites). On full-catalogue `HIDE-RECOVER-v3.1` (`N=22,232`), range-front damping lowers DTI slightly (`0.098049` vs `0.099202`, `Δ = -0.001153`), so fail-closed gates retain `verdict = "negative"`.
- **Uniqueness**: `max_3px = 67.08% <= 70%` vs 287 geological detectors, **`54.95%`** vs Session-2 `DSLUP` (`c71122d5`), **`54.26%`** vs `ECPU` (`cecbdca7`), **`58.83%`** vs archived `11a2f251`, and **`36.75%`** vs `0.2778` Champion (`99.95%` vs `13gems` spacing-5 calibration lattice).
- **Sister-Repository Fleet Audit ([`evidence/sister_and_focus_audit_20261027.json`](evidence/sister_and_focus_audit_20261027.json))**: Audited `KANLERGEMSDOE1` (`0741963ae4e9`, safe), `KANLERGEMSDOE3` (`9a4ecfd71d00`, safe), `WBGGEMSDOE1` (`0749b3c8195f`, safe), `WBGGEMSDOE2` (`efd46877` unsafe `nodata != None`; `a1b2c3d4` `5,094,374` px blanket), `WBGGEMSDOE3` (`5d451566` unsafe: `463` positive dots on public catalogue), `GEMSDOE70` (`p5-dual-submod300`, `0.2478 USER-REPORTED`, safe), and `EUGGEMSDOE1..3` + `GINNYGEMSDOE1..3` (`0` GeoTIFFs). Shared template fixes: `src/gems32/holdout.py` (`IR-SHARED-EMPTY-TRUTH-FP-04`) and `src/gems32/htcads.py` (`IR-HTCADS-TC-05`).

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
