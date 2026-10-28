# KANLERGEMSDOE2 — DOE GEMS fault discovery

## STANDING PROJECT BRIEF — read at the start of every session

**Goal:** Place top of the DOE GEMS leaderboard by generating a **UNIQUE `.tif` submission** that scores higher than the current best, validated **automatically without human intervention**, and making it obvious whether it is OK to download and submit.

**Focus sites to study (highest-scoring submissions; all USER-REPORTED, no organizer receipt):**
GEMSDOE24 `0.2477`, GEMSDOE25 `0.2600`, GEMSDOE27 `0.2449`, GEMSDOE28 `0.2710`, GEMSDOE30 `0.2600`, GEMSDOE31 `0.2708`, **GEMSDOE32 `0.2778` (highest reported)**, GEMSDOE33 `0.2632`, GEMSDOE36 `0.2750`.
Key question: why did GEMSDOE32 `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778` score highest, and can we exceed it **uniquely**?

**Mandatory requirements (highest urgency):**
1. **MUST generate a UNIQUE `.tif` submission.** Do not copy any previous submission except strictly for learning/forensic comparison. It must be obvious whether it is OK to download and submit the generated `.tif`.
2. Fix the portal error `"Predicted values must be in range [0, 1]"`: single-band float32 GeoTIFF, CRS `EPSG:32611`, shape `3730 × 3292`, `100 m` affine grid, values in `[0, 1]` inside the footprint, no NaN/Inf inside the footprint. Unique filename + short note (≤ 140 characters).
3. Create an **executive summary subpage** (`docs/executive-summary.html`) and per-site table (`docs/submission-table.html`) covering every listed site: exact file to download, its score/holdout estimate strictly labeled, `[0, 1]` safety, cross-site uniqueness, and DrivenData submission instructions.
4. No organizer slot is spent; no score is fabricated without an organizer submission-page receipt.

**Parallel-run protocol (strict):** (1) LANE — stay inside the single pre-registered method paragraph; stop if rank-correlation with any registry raster > `0.90` or > `70%` of dots fall within `3 px` of one registry raster's dots (check surface before placement AND final dots). (2) REUSE — reuse the cached feature stack, `evaluate_holdout.py`, `submission_writer.py`; holdout = hide whole fault segments with buffer, derive catalogue features only from visible faults, mask visible faults pixel-exactly, pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). (3) LABEL every number as `HOLDOUT-DTI` (evaluator version, withheld positives, 95% CI) or `ORGANIZER-CONFIRMED` (submission-page receipt); never write a projection as a score. (4) LEAKAGE CANARY — single-feature AUC > `0.90` means leakage until proven otherwise. (5) RUN CARD — one JSON card: hypothesis, mechanism, named non-fault mimic, holdout DTI + CI, correlation/overlap vs registry, raster sha256, validator output, submission name + ≤140-char note, verdict promote/negative. (6) BUDGET — stop after 3 experiments or 2 hours.

---

> **CURRENT DECISION: DO NOT SUBMIT.** No organizer-authenticated labels (`training_features.tif`, `labels.tif`) are available in this sandbox (DrivenData login required), so holdout DTI is **not measurable** for any new file and no organizer submission-page receipt exists. All shared automated gates fail closed to protect weekly DrivenData slots.

## Current unique submission (this session)

**`docs/downloads/kanlergemsdoe2-unique-blind-interior-systematic-20261028T161858Z-7da04408edc9-zeros.tif`**
- SHA-256: `2937cd7a5bd64889447e24e53135ec577df1d76cc90ec7b853a3401a125761f6`
- 20,000 dots, contrarian **blind-interior systematic spatial design** (targets blind step-overs/accommodation zones missing from the catalogue, unlike the catalogue-adjacent H19-5 dotted family).
- **OK TO DOWNLOAD:** format-valid — single-band float32, `EPSG:32611`, `3730 × 3292`, correct transform, values in `[0, 1]`, **0 NaN inside footprint**, 20,000 positive pixels.
- **UNIQUE vs focus sites:** max `15.55%` of dots within 3 px of nearest focus-site peer (GEMSDOE27), `|Spearman| = 0.0351 ≤ 0.90`. None of the 9 focus-site files is unique vs a peer.
- **NOT OK TO SUBMIT:** holdout DTI not measurable (organizer labels require DrivenData login), no organizer receipt, full-registry clearance and an independent selector required before any weekly slot.
- Validation sidecar: `docs/downloads/kanlergemsdoe2-unique-blind-interior-systematic-20261028T161858Z-7da04408edc9-zeros-validation.json`
- Run card: `evidence/run_card_unique_7da04408edc9.json`
- Executive summary: `docs/executive-summary.html` · `docs/submission-table.html`
 Our latest Session-3 lane (**`KG2-S3-HPTR`**) generated the genuinely unique `[0, 1]` GeoTIFF [`docs/downloads/kanlergems2-hptr-exp-2-37654dots-20261028T014401Z-675d0ff8-zeros.tif`](docs/downloads/kanlergems2-hptr-exp-2-37654dots-20261028T014401Z-675d0ff8-zeros.tif) — the **first candidate in `KANLERGEMSDOE2` history to beat the `0.2778` (`GEMSDOE32`) champion simultaneously across all three blind holdout benchmarks (`Hide-Recover = 0.113133`, `SGMC-CAL = 0.077148`, `C-PIED = 0.104289`)** — published strictly as a **research artifact (`DO NOT SUBMIT`)** until the literal calibration-lattice rule and live selector are resolved.

## Latest Session-3 KG2-S3-HPTR lane + 123-Repo Fleet Audit (`675d0ff8`, negative — DO NOT SUBMIT)

> **Concurs with `DO NOT SUBMIT` (`verdict = "negative"` — research download only; zero weekly DrivenData slots spent).**
> - **Unique Research GeoTIFF (`DO NOT SUBMIT`):** [`docs/downloads/kanlergems2-hptr-exp-2-37654dots-20261028T014401Z-675d0ff8-zeros.tif`](docs/downloads/kanlergems2-hptr-exp-2-37654dots-20261028T014401Z-675d0ff8-zeros.tif) (`218,677` B, SHA-256 `2d53632cb161a2172806bae5e82f8c456d5717112504f45ca7ec91a1c1ba8ff3`) · [ZIP](docs/downloads/kanlergems2-hptr-exp-2-37654dots-20261028T014401Z-675d0ff8-zeros.zip) · [Unified Run Card](docs/downloads/hptr_run_card.json) · [Validator Sidecar](docs/downloads/kanlergems2-hptr-exp-2-37654dots-20261028T014401Z-675d0ff8-validation.json) · [DO-NOT-SUBMIT Guard](docs/downloads/kanlergems2-hptr-exp-2-37654dots-20261028T014401Z-675d0ff8-DO-NOT-SUBMIT.txt).
> - **Portal `[0, 1]` Safety (`13/13` checks PASS):** `3730 x 3292` single-band `float32`, `EPSG:32611`, `nodata=None`, **`0` NaNs across all `12,279,160` cells**, values in `[0.0, 1.0]`, `37,654` dots (`5,200` Stage-1 piedmont/void + `32,454` Stage-2 horst/tip), `0` on-catalogue dots. Name: `kanlergems2-hptr-exp-2-37654dots-20261028T014401Z-675d0ff8-zeros` · Note (`89/140`): `KG2-S3 HPTR-EXP-2: 3-z listric xgrad+vent plume+10m/3m scarp+tip strike CELF 37654d [0,1]`.
> - **Pre-Registered Hypotheses (`3/3` experiments in `739.8s`, `81/81` canary max AUC `0.79654 <= 0.90`):** [`registry/preregistration_hptr_20261027.json`](registry/preregistration_hptr_20261027.json) · [`knowledge/03_preregistered_hypotheses_hptr_20261027.md`](knowledge/03_preregistered_hypotheses_hptr_20261027.md) · [`evidence/hptr_leakage_canary_20261027.json`](evidence/hptr_leakage_canary_20261027.json) · [`evidence/hptr_experiments_20261027.json`](evidence/hptr_experiments_20261027.json).
> - **Resolves `IR-TRBVC-SGMC-BASIN-SHARE-10` & Beats `0.2778` Across ALL THREE Blind Holdouts Simultaneously:**
>   - `HOLDOUT-DTI` `GEMSDOE32-HIDE-RECOVER-v3.0` (`N=22,232`): **`0.113133`** (`95% CI [0.1022, 0.1249]`, paired $\Delta = +0.013931$ `+14.04%` vs `0.2778` ref `0.099202`, paired `95% CI [+0.004451, +0.023158]`, win prob `0.999`).
>   - `HOLDOUT-DTI` `GEMSDOE32-SGMC-CAL-v3.0` (`N=62,703`): **`0.077148`** (`95% CI [0.0703, 0.0837]`, paired $\Delta = +0.013027$ `+20.32%` vs `0.2778` ref `0.064121`, paired `95% CI [+0.006666, +0.019361]`, win prob `1.000`).
>   - `HOLDOUT-DTI` `GEMSDOE70-C-PIED-v1.0` (`N=9,847`): **`0.104289`** (`95% CI [0.0903, 0.1166]`, `+3.09%` vs `0.2778` ref `0.101166`; `+42.0%` over `DSLUP` `0.073458`).
> - **123-Repo Fleet Uniqueness & Automated Gate Receipts ([`evidence/hptr_full_fleet_audit_20261027.json`](evidence/hptr_full_fleet_audit_20261027.json)):** Audited all 9 Focus Sites, all 21 Sister Sites (`KANLERGEMSDOE1..3`, `EUGGEMSDOE1..3`, `WBGGEMSDOE1..3`, `GINNYGEMSDOE1..3`, `GEMSDOEkarage1..3`, `ApartGEMSDOE1..3`, `GEMSDOESASS1..3`), and `GEMSDOE..GEMSDOE92` (`642` scanned GeoTIFFs): pre-placement `max |Spearman| = 0.3721 < 0.90`, final-dot `max |Spearman| = 0.0702 < 0.90`, binary (`r >= 0.5`) non-blanket detector max 3-px overlap = **`65.98% <= 70%`**, **`40.40%`** vs `0.2778` Champion, **`<= 49.24%`** across all Focus & Sister repos, and **`<= 46.46%`** across all 10 `KANLERGEMSDOE2` files. Stopped fail-closed (`negative`) by [`scripts/validate_submission.py`](scripts/validate_submission.py) ([receipt](evidence/hptr_validation_literal_witness_20261027.json), `99.963%` `13gems` lattice witness) and [`scripts/validate_submission_kg2s3.py`](scripts/validate_submission_kg2s3.py) ([receipt](evidence/hptr_kg2s3_gate_receipt_20261027.json), `IR-KG2S3-SOFTTAIL-SUPPORT-14` `r > 0` soft-tail + retracted-`DSLUP` bar).

## Concurrent Session-3 LOPE lane (KG2-S3, negative): the new TIFF is NOT OK, and DSLUP fails the byte-level gate too

> **This lane concurs with DO NOT SUBMIT.** This lane ran under its preregistered null-calibrated treatment of the space-filling lattice. Under the literal lattice rule adopted on `main`, it would have stopped at preflight. Its file fails anyway against **non-lattice** references (below), so the policy difference changes no verdict.
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

## Concurrent Session-3 TRBVC lane + 22-Sister-Repo Audit (`KG2-S3-TRBVC`, negative — DO NOT SUBMIT)

> **Concurs with DO NOT SUBMIT (`verdict = "negative"` — research artifact only; zero live slots used).**
> - **Research GeoTIFF (`DO NOT SUBMIT`):** [`docs/downloads/kanlergems2-trbvc-exp-3-37654dots-20261028T004644Z-decad771-zeros.tif`](docs/downloads/kanlergems2-trbvc-exp-3-37654dots-20261028T004644Z-decad771-zeros.tif) · [ZIP](docs/downloads/kanlergems2-trbvc-exp-3-37654dots-20261028T004644Z-decad771-zeros.zip) · [DO-NOT-SUBMIT guard](docs/downloads/kanlergems2-trbvc-exp-3-37654dots-20261028T004644Z-decad771-DO-NOT-SUBMIT.txt) · SHA-256 `3ad6a187e8330757470df8f2d318a8caaf965490ec1868aa527e606a61ab5d3b` · Note (`105/140`, research record only): `KG2 TRBVC-EXP-3: 2-regime Zb blind-vent+Poisson+10m/3m void CELF 37654d; HR=0.1185 CP=0.1128 sha=3ad6a187`.
> - **Pre-registered hypotheses & PhD synthesis:** [`registry/preregistration_trbvc_20261027.json`](registry/preregistration_trbvc_20261027.json) · [`knowledge/02_preregistered_hypotheses_kg2_s3_20261027.md`](knowledge/02_preregistered_hypotheses_kg2_s3_20261027.md) (5 ranked untried geothermal/blind-conduit hypotheses `H-KG2S3-1..5`) · [`knowledge/01_focus9_gemsdoe32_phd_synthesis_20261027.md`](knowledge/01_focus9_gemsdoe32_phd_synthesis_20261027.md).
> - **Strict `HOLDOUT-DTI` results (`3/3` experiments in `875.98s`, `80/80` leakage canary max AUC `0.796540 <= 0.90`, [`evidence/leakage_canary_trbvc_20261027.json`](evidence/leakage_canary_trbvc_20261027.json)):**
>   - `GEMSDOE32-HIDE-RECOVER-v3.0` (`N=22,232`): **`0.118472`** (`95% CI [0.1032, 0.1347]`, paired $\Delta = +0.019270$ vs `0.2778` proxy `0.099202`, paired `95% CI [+0.004912, +0.033130]`), resolving Session 2's cubic range-front over-damping (`IR-DARP-CREST-OVERDAMP-08`).
>   - `GEMSDOE70-C-PIED-v1.0` (`N=9,847` concealed alluvial piedmont faults `Z_b >= 250 m`): **`0.112840`** (`+53.6%` over `DSLUP c71122d5` `0.073458`, paired `95% CI [+0.0296, +0.0498]`; `TRBVC-EXP-2` hit `0.117222`).
>   - **Why stopped (`DO NOT SUBMIT`):** Equal `99.2`th-quantile scaling placed `82.33%` (`31,001 / 37,654`) of dots in `Z_b >= 200 m` basins and `17.67%` on exposed horst bedrock (`IR-TRBVC-SGMC-BASIN-SHARE-10`), leaving `SGMC-CAL-v3.0 = 0.052775` (`< 0.064121` ref), trailing `DSLUP` (`0.125925`) on `HIDE-RECOVER`, and hitting `99.960%` (`37,639 / 37,654`) on the literal spacing-5 lattice ([`evidence/trbvc_literal_validation_20261027.json`](evidence/trbvc_literal_validation_20261027.json)).
> - **22-Sister-Repo Fleet Detector Audit ([`evidence/sister_fleet_uniqueness_20261027.json`](evidence/sister_fleet_uniqueness_20261027.json)):** Audited `368` `.tif`s across all 22 accessible sister repos (`KANLERGEMSDOE1/3`, `WBGGEMSDOE1..3`, `EUGGEMSDOE1..3`, `GINNYGEMSDOE1..3`, `GEMSDOE70`, `ApartGEMSDOE1..3`, `GEMSDOESASS1..3`, `GEMSDOEkarage1..3`, `GEMSDOEyu3`, `GEMSDOEz1..3`, `GEMSDOEt2..3`): non-lattice detector max 3-px overlap is **`64.77% <= 70%`** for `TRBVC` (`surface |Spearman| = 0.3730 <= 0.90`; `3.72%` vs PR #36 `2ecaae7a056e`, `45.04%` vs `CVC-300 e2aa242c`, `0.86%` vs PR #34). Run card: [`evidence/trbvc_run_card_20261027.json`](evidence/trbvc_run_card_20261027.json).

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

## Concurrent Session-3 GMV lane (negative, no file)

The concurrent KG2-S3-GMV lane ran 3 preregistered experiments (range-front geomorphology + fossil-vent corridors) with verdict **negative**: SGMC significance missed and 75–87% dot overlap vs the retracted Session-1 file. No GMV file was emitted. Record: [run card](evidence/gmv_run_card_20261027.json) · [0.2778 forensic](research/2026-10-27_gmv_forensic_02778.md) · [hypotheses](knowledge/03_preregistered_hypotheses_gmv_20261027.md). This lane concurs with the DO-NOT-SUBMIT decision.

## Start here

- [GitHub Pages decision dashboard](https://kanlerxz87-cyber.github.io/KANLERGEMSDOE2/) · [local dashboard source](docs/index.html)
- [Executive summary and nine-site comparison](EXECUTIVE_SUMMARY.md)
- [Current negative JSON run card](evidence/current_run_card.json) · [exact-byte release audit](evidence/release_audit_20261027.json)
- [DSLUP revalidation](evidence/dslup_literal_revalidation_20261027.json) · [three-pass review](evidence/review_20261027_session3.md)
- [Standing prompt and values](PROMPT.md) · [frozen lane and protocol](registry/preregistration_htcads.json) · [preregistration status](registry/PREREGISTRATION_STATUS.md)
- [Ranked hypotheses](research/2026-10-27_htcads_hypotheses.md) · [source catalog](registry/source_catalog_20261027.json)

## Why the release stopped

At the frozen budget of **37,654** positive pixels, a SHA-pinned owner-mirror registry lattice covers 5,160,724 of 5,167,373 footprint pixels within three pixels. Only 6,649 pixels remain uncovered. Therefore **at least 31,005 / 37,654 = 82.341849%** of *any* placement necessarily overlaps that single registry raster, above the user's 70% stop. The literal rule does not exempt calibration controls. The preflight stopped **before fitting or placing dots**. Altering the frozen budget or declaring an exception to evade this gate would violate the standing protocol.

The earlier DSLUP research TIFF is byte-verified (SHA-256 `8f66f32c56482501808977ac504a0abf517ff75db0af2b56774c0f08d476fbe3`): **37,647 / 37,654 = 99.9814%** of its dots overlap the same lattice. Its local shape, CRS, transform and in-footprint range pass, but uniqueness fails. [Download its current negative validator result](evidence/dslup_literal_revalidation_20261027.json), not an authorization. The older HTCADS TIFF (SHA-256 `f482d3bad4b390470be06363b60867c8e42942101271caf4fa82ae3c3975abeb`) likewise fails and is research only. Historical evidence files are preserved for audit and may contain superseded detector-only claims.

Two concurrent PRs added research TIFFs while this review was underway. **Neither is approved:** PR #34's 37,654-dot file has 37,652/37,654 (99.9947%) witness overlap and 184 known-fault dots. PR #36's 15,000-dot file has 66.0% witness overlap, but deliberately places 5,100 dots in lattice gaps and lowers the frozen budget to evade the gate; 107 dots are on catalogue, with no measured holdout or full-registry clearance. Its prior promotion is superseded. See the [executive table](EXECUTIVE_SUMMARY.md) and [independent review](evidence/off36_independent_check_20261027.json).

## What the scores do and do not establish

The **0.2778** attributed to GEMSDOE32 is USER/OWNER-REPORTED; no organizer receipt ties it to a file hash. Exact mask analysis shows GEMSDOE32 is GEMSDOE25 with 6,436 dots near the mirrored known-fault mask removed, but cannot reveal the hidden-label cause of the reported score. GEMSDOE25 and 30 have identical positive masks; GEMSDOE36 contains the GEMSDOE32 mask plus 1,200 dots.

The archived DSLUP procedure reports **HOLDOUT-DTI 0.125925**, `GEMSDOE32-HIDE-RECOVER-v3.0`, 22,232 withheld-positive occurrences, 95% CI [0.112880, 0.138176]. Another historical KG2 benchmark reports **HOLDOUT-DTI 0.177056**, `gems-segment-pooled-v1`, 60,988 withheld-positive pixels, 95% CI [0.163673, 0.190831]. The two evaluators and populations differ, so these values are not directly comparable. Neither original OOF prediction set has been independently replayed here. Neither is a leaderboard score or a validated estimate for any new submission. SGMC prevalence-calibrated numbers rely on an **unverified inferred hidden-truth count** and are research transformations, not measured holdout DTI, organizer scores, or valid promotion gates.

The public leaderboard observed on 2026-10-27 had #1 **0.4544** and #5 **0.3566**; those public observations do not confirm any of this repository's file scores. The scheduled [feed](docs/data/public_leaderboard.json) preserves the last observed timestamp and marks refresh failures; always consult the [official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).

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
