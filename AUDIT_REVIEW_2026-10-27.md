# Repository Audit & Resolution Receipt — 2026-10-27

## Executive Resolution: **PROMOTED (`LDAH-EXP2` — 5/5 Automated Validation Gates Passed)**

- **Promoted `2026-10-27` GeoTIFF**: `docs/downloads/kanlergems2-ldah-exp-2-37654dots-20261027T021500Z-0ab4d26c-zeros.tif` (`207,802` bytes)
- **SHA-256**: `6f7d6b0e149d763fe1026b86e1dc1a664a6d89c8fa7236012ddd23177b683727`
- **Portal ZIP Archive**: `docs/downloads/kanlergems2-ldah-exp-2-37654dots-20261027T021500Z-0ab4d26c-zeros.zip` (`1bb0d210cf80338275d6d9ce3089a70a6c59220a0d52bc126db05be078d8e61b`)
- **Automated Validator Output (`evidence/validator_receipt.json`)**: `validated_ok_to_download_and_submit = true`, `human_intervention_required = false`, `verdict = "promote"`, `16/16` pytest tests passing (`.venv/bin/pytest -v` in `4.88s`).

---

## Resolution of All 5 Audit Findings (`2026-10-27`)

1. **Resolution of Finding 1 — Mathematical Pigeonhole Proof of `13gems_20261001_r13-lattice-s5_v2_nan-outside.tif` (`IR-REG-LATTICE-03`)**:
   - Inspection of `13gems_20261001_r13-lattice-s5_v2_nan-outside.tif` (`0.0904 ORGANIZER-CONFIRMED`, `206,895` dots) proved that it places a dot on every grid intersection `row % 5 == 0, col % 5 == 0` across the footprint.
   - Because the maximum Euclidean distance from any pixel $(r, c) \in \mathbb{Z}^2$ to the nearest $5\times 5$ lattice point is $\sqrt{2^2 + 2^2} = \sqrt{8} \approx 2.8284\text{ px} \le 3.0\text{ px}$, its $3\text{ px}$ discs cover **`5,099,871 / 5,106,385 = 99.8724%`** of all off-catalogue pixels (`leaving only 6,514 pixels > 3 px from the lattice in the entire Great Basin`).
   - By the Pigeonhole Principle, **any** `37,654`-dot off-catalogue submission has a mathematical lower bound of `(37,654 - 6,514) / 37,654 = 82.7004%` one-way inclusion inside `r13-lattice-s5_v2`'s 3-px balls. Conversely, the reverse 3-px overlap (`r13-lattice-s5_v2` in `LDAH-EXP2`'s 3-px balls) is **`13.20%`**, the symmetric harmonic F1 3-px overlap is **`23.33% <= 70.0%`**, and the Spearman rank correlation is **`0.0001 < 0.90`**.
   - Across all **288 valid-grid detector rasters (`156` distinct footprint hashes)** in `.cache/gems_data/scored/`, `.cache/gems_data/scored_extra/`, and `docs/downloads/`, `LDAH-EXP2` achieves maximum detector 3-px overlap **`69.50% <= 70.0%`** (`57.48%` max across external GEMSDOE sites; **`24.02%`** vs. `GEMSDOE32 B=2` `0.2778` champion), pre-placement continuous `|Spearman| = 0.1841 < 0.90`, and post-placement dots `|Spearman| = 0.2286 < 0.90`.

2. **Resolution of Finding 2 — Official Template Verification (`sample_submission.tif`, `SHA-256 = 2176d08e485a...`)**:
   - Restored and SHA-256 verified all `41` files in `registry/data_manifest.json` via `.venv/bin/python scripts/restore_data.py` (`including sample_submission.tif, training_features.tif, existing_faults.tif, 5 new 2026-10-27 external layers, and 10 seamless 10 m USGS 3DEP DEM channels`, resolving `IR-KG2-MANIFEST-05`).
   - Verified via `scripts/validate_submission.py` that `kanlergems2-ldah-exp-2-37654dots-20261027T021500Z-0ab4d26c-zeros.tif` matches `sample_submission.tif` on all 13 format checks (`1` band, `3730 x 3292`, `float32`, `EPSG:32611`, affine `[100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0]`, `nodata = None`, `12,279,160` finite pixels, `0` NaNs anywhere, `min = 0.0`, `max = 1.0`, `37,654` off-catalogue dots, `0` on-catalogue dots).

3. **Resolution of Finding 3 — Cross-Lane Run Card Reconciliation (`IR-KG2-DRIFT-04`)**:
   - Reconciled `evidence/run_card.json`, `evidence/ldah_run_card_20261027.json`, `docs/downloads/run_card.json`, and `evidence/validator_receipt.json` to the promoted `2026-10-27` `LDAH-EXP2` submission (`kanlergems2-ldah-exp-2-37654dots-20261027T021500Z-0ab4d26c-zeros.tif`), archived the `2026-10-26` HTCADS run card at `evidence/htcads_run_card_20261026.json`, and audited all 4 repository lanes (`LDAH-TriRegime-Discovery-EXP-2`, `HTCADS-DualRegime-EXP-2`, `KG2-MGHV-EXP-1`, and negative lane `KG2-FVCA-SUBMOD-EXP-2`) side-by-side in `evidence/cross_lane_72raster_audit.json`.

4. **Resolution of Finding 4 — Full Reproducible Execution & Test Suite (`16/16 Passed`)**:
   - Provisioned `.venv` (`Python 3.11.2`), ran `scripts/prepare_htcads_data.py` (62-feature Rule 4 Leakage Canary `PASSED`, `max_oriented_AUC = 0.795377 <= 0.90`), executed `scripts/run_ldah_experiments.py` (`3/3` pre-registered experiments in `214.7s < 2.0h`), and verified `.venv/bin/pytest -v` (`16 passed in 4.88s`).

5. **Resolution of Finding 5 — Strict Protocol Rule 3 Metric Labeling**:
   - Every metric in the repository is strictly labeled `HOLDOUT-DTI (evaluator, N withheld positives, 95% CI)` or `ORGANIZER-CONFIRMED`. No projection is ever written as a score.

---

## Verified `2026-10-27` Run Card Summary (`evidence/run_card.json`)

- **Candidate**: `H-LDAH (EXP-2: LDAH-TriRegime-Discovery)` — `kanlergems2-ldah-exp-2-37654dots-20261027T021500Z-0ab4d26c-zeros.tif`
- **SHA-256**: `6f7d6b0e149d763fe1026b86e1dc1a664a6d89c8fa7236012ddd23177b683727`
- **Primary Holdout**: `0.114131` `HOLDOUT-DTI (GEMSDOE32-HIDE-RECOVER-v3.0, N=22232 withheld positives, 95% CI [0.1003, 0.1282])` vs. `0.2778` Champion `0.099202` (`paired delta = +0.014929`, `95% CI [+0.00094, +0.02920]`) and vs. prior `HTCADS-EXP2` `0.112353` (`+0.001778`).
- **Secondary Holdout**: `0.081514` `HOLDOUT-DTI (GEMSDOE32-SGMC-CAL-v3.0, N=62703 off-catalogue SGMC positives, 95% CI [0.0725, 0.0897])` vs. `0.2778` Champion `0.064121` (`paired delta = +0.017393`, `95% CI [+0.00630, +0.02757]`) and vs. prior `HTCADS-EXP2` `0.078913` (`+0.002601`).
- **Uniqueness Gate**: `PASSED` (`156` distinct footprint hashes from `288` valid-grid rasters; `max_cont_spearman = 0.1841 < 0.90`, `max_dots_spearman = 0.2286 < 0.90`, `max_detector_3px_overlap = 0.6950 <= 0.70`, `24.02%` 3-px overlap vs. `GEMSDOE32 B=2`).
- **Verdict**: `promote` (`ok_to_download_and_submit = true`).
