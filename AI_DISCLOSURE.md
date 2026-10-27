# AI & Algorithmic Provenance Disclosure (`KANLERGEMSDOE2`)

## Competition Compliance Statement

In accordance with the U.S. Department of Energy Geothermal Technologies Office (DOE GTO) and DrivenData *DOE GEMS Prize: Advancing Geothermal Exploration with Machine Learning* rules:

1. **Automated Agent Assistance:** Code engineering, forensic data auditing, statistical validation, scientific visualization, and documentation in this repository were developed autonomously using Arena.ai Agent Mode.
2. **Open-Source Reproducibility:** Every feature transform, model training step (`LightGBM` out-of-quadrant gradient-boosted decision trees + first-principles multi-physics operators + CELF submodular allocation), holdout evaluation (`GEMSDOE32-HIDE-RECOVER-v3.0` and `GEMSDOE32-SGMC-CAL-v3.0`), and `[0, 1]` GeoTIFF validation gate is 100% deterministic, open-source Python (`numpy`, `scipy`, `rasterio`, `scikit-learn`, `lightgbm`), and reproducible from `scripts/restore_data.py`, `scripts/prepare_data.py`, `scripts/run_htcads_experiments.py`, and `scripts/validate_submission.py`.
3. **Data Provenance & Zero Label Leakage:**
   - Only official competition rasters (`training_features.tif`, `existing_faults.tif`, `labels.tif`, `sample_submission.tif`) and open public-domain federal geoscience compilations (USGS GeoDAWN `DOI: 10.5066/P93LGLVQ`, DOE GDR `#1391` INGENIOUS `DOI: 10.15121/1881483`, USGS 3DEP 1 m LiDAR scarp derivatives, and USGS ScienceBase heat-flow/regional stress ratios) are used.
   - Off-catalogue USGS SGMC fault traces (`DOI: 10.3133/ds1052`) are strictly excluded from all feature construction and model fitting, and used solely as an independent external holdout diagnostic (`GEMSDOE32-SGMC-CAL-v3.0`).
   - All 50 engineered channels pass the single-feature spatially-blocked leakage canary (`max oriented AUC = 0.795377 <= 0.90`).
4. **No Proprietary / Closed-Weight External Prediction Rasters Used in Final Submission:** Our promoted GeoTIFF (`kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif`, SHA-256 `f482d3bad4b390470be06363b60867c8e42942101271caf4fa82ae3c3975abeb`) is generated 100% de-novo from raw physical layers + `existing_faults.tif`, with zero pixels copied from `19GEMSDOE` `H19-5` or any peer submission.
