> **2026-10-27 Validated Promotion Receipt — OK TO DOWNLOAD & SUBMIT (`5/5` Automated Gates Passed):**
> - **Primary Promoted `2026-10-27` GeoTIFF (`LDAH-EXP2`):** [`docs/downloads/kanlergems2-ldah-exp-2-37654dots-20261027T021500Z-0ab4d26c-zeros.tif`](docs/downloads/kanlergems2-ldah-exp-2-37654dots-20261027T021500Z-0ab4d26c-zeros.tif) (`207,802` bytes · SHA-256 `6f7d6b0e149d763fe1026b86e1dc1a664a6d89c8fa7236012ddd23177b683727` · ZIP [`kanlergems2-ldah-exp-2-37654dots-20261027T021500Z-0ab4d26c-zeros.zip`](docs/downloads/kanlergems2-ldah-exp-2-37654dots-20261027T021500Z-0ab4d26c-zeros.zip))
> - **Submission Note (`132/140` chars):** `KANLERGEMS2 LDAH-TriRegime-Discovery: 62ch ListricUpdip+10mDEM+3mScarp+HF+ComCat TriRegime CELF (37654 dots, HR=0.1141, SGMC=0.0815)`
> - **Dual Holdout Superiority:** Beats **both** the `0.2778` `ORGANIZER-CONFIRMED` Champion (`GEMSDOE32 B=2`: `HR=0.099202`, `SGMC-CAL=0.064121`) **and** the prior `2026-10-26` `HTCADS-EXP2` baseline (`11a2f251-zeros.tif`, SHA-256 `f482d3bad4b390470be06363b60867c8e42942101271caf4fa82ae3c3975abeb`: `HR=0.112353`, `SGMC-CAL=0.078913`) on **both** evaluators simultaneously (`Hide-Rec = 0.114131`, `SGMC-CAL = 0.081514`), with **`24.02%`** 3-px overlap vs. `GEMSDOE32 B=2` (`75.98%` novel fault discovery) and **`69.50% <= 70.0%`** max detector overlap across all `288` valid-grid registry rasters. See [`AUDIT_REVIEW_2026-10-27.md`](AUDIT_REVIEW_2026-10-27.md) and [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md).

# KANLERGEMSDOE2 — U.S. DOE GEMS Geothermal Fault Discovery & Automated Submission System

---

## Arena Core Values

- **Maximize P(Win):** Every design decision targets maximum expected leaderboard and Phase 2 ($250k / $395k expert-reviewed evaluation) return per scarce rolling submission slot. Rather than burning slots on `H19-5` clones or cosmetic threshold tweaks, we invert the `0.2778` ledger mathematically, identify why prior supervised GBDTs suffered alluvial mapping bias (`IR-KG2-BUG-02`) and why prior `GEMSDOE32` attempts (`H38`, `H44`, `H45`, `ARENA47`, `H47`) failed closed on one of the two holdouts, and promote **only** a candidate (`2026-10-27` `LDAH-EXP2: LDAH-TriRegime-Discovery`, advancing over `2026-10-26` `HTCADS-EXP2: 11a2f251`) that beats both the `0.2778` Champion and all prior repository baselines on **both** orthogonal holdouts with strictly positive 95% confidence intervals while exploring **75.98% (`28,609` dots)** genuinely new fault conduits outside `GEMSDOE32 B=2`.
- **Own the Outcome:** Zero human-inspector fallback is relied upon. `scripts/validate_submission.py` verifies `13/13` GeoTIFF geometry and `[0, 1]` range invariants (`0` NaNs across all `12,279,160` cells, permanently preventing `"Predicted values must be in range [0, 1]"`), `62/62` single-feature leakage canaries (`<= 0.90`), registry uniqueness across `156` footprint-distinct rasters (`288` valid-grid peer downloads checked), and paired spatial cluster-bootstrap significance automatically. Shared template defects (`IR-SHARED-SOFT-01`, `IR-SHARED-SUB-02`, `IR-32-INSTR-03`, `IR-KG2-DRIFT-04`, `IR-KG2-MANIFEST-05`) are patched directly in `src/gems32/` and tested in `tests/` (`16/16` passing).

---

## Automated 5-Gate Verification Summary (`LDAH-EXP2` — `2026-10-27`)

| Gate (100% Automated in `scripts/validate_submission.py`) | Threshold | Measured Result on Promoted `LDAH-EXP2` GeoTIFF (`0ab4d26c-zeros.tif`) | Status |
|---|---|---|---|
| **Gate 1: Format & `[0, 1]` Portal Safety** | `EPSG:32611`, `3730x3292`, `float32`, `0` NaN, values in `[0, 1]`, `0` on-catalogue px | `13/13` checks true; `12,279,160 / 12,279,160` finite cells (`min=0.0`, `max=1.0`, `nodata=None`, `0` NaN, `0` cat px) | **PASS** |
| **Gate 2: Rule 4 Single-Feature Leakage Canary** | Single-feature spatially-blocked holdout `AUC <= 0.90` on all channels | `62 / 62` channels pass (`50` baseline + `12` `EXT27` discovery channels); `max_oriented_AUC = 0.795377` (`vis_aniso_prior`) | **PASS** |
| **Gate 3: Rule 1 Registry Uniqueness** | `|Spearman| <= 0.90` (surface & dots) AND `<= 70%` 3-px dot overlap vs all detector rasters | **24.02%** 3-px vs `0.2778` Champ; max vs all external GEMSDOE detectors = **57.48%** (`<= 70%`); vs prior `11a2f251` = **69.50%** (`<= 70%`); surface `|rho| = 0.1841`; dots `|rho| = 0.2286` | **PASS** |
| **Gate 4: Dual Spatially-Blocked Holdout Beat** | Beat `0.2778` Champion on `HIDE-RECOVER-v3.0` (paired 95% CI > 0) AND beat on `SGMC-CAL-v3.0` | **Hide-Rec**: **`0.114131`** vs `0.099202` (`+0.014929`, paired 95% CI **`[+0.00094, +0.02920]`**, **97.8%** win prob; beats `11a2f251 = 0.112353`)<br>**SGMC-CAL**: **`0.081514`** vs `0.064121` (`+0.017393`, paired 95% CI **`[+0.00630, +0.02757]`**; beats `11a2f251 = 0.078913` & `EXP-1 = 0.081431`) | **PASS** |
| **Gate 5: Portal Metadata & Protocol Budget** | Unique filename, note `<= 140` chars, `<= 3` experiments, `<= 2.0` wall hours | `132 / 140` chars; `3 / 3` experiments completed in `214.7 s` (`3.58 min <= 2.0 hr`) | **PASS** |

![KANLERGEMSDOE2 vs GEMSDOE32 0.2778 Spatial Discovery Map](docs/assets/fig1_htcads_vs_champion_map.png)

---

## 1. Executive Summary & 9-Site Multi-Site Audit (`GEMSDOE24..36` + 92-Site Fleet)

Full interactive guide: [`docs/executive-summary.html`](docs/executive-summary.html) · Standalone brief: [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md) · Raw receipt: [`evidence/nine_site_audit.json`](evidence/nine_site_audit.json).

### Key Multi-Site Audit Findings
1. **All 9 Focus-Site Champions (`0.2449 -> 0.2778` `ORGANIZER-CONFIRMED`) Share One Ancestor (`19GEMSDOE` `H19-5`):** Every top-scoring raster across `GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36` is a thinned or collar-pruned subset/extension of `19GEMSDOE`'s `H19-5` (`121,131` px, live `0.1922`), exhibiting **94.0% to 100.0%** pairwise 3-px overlap across all 9 sites and **two exact `0-XOR` pixel-identical cross-site duplicate pairs** (`GEMSDOE25 == GEMSDOE30` at `0.2600`; `GEMSDOE28_solo == GEMSDOE31` at `0.2708`). None of the 9 focus sites had an unsubmitted candidate passing both holdout and uniqueness gates on `2026-10-26`.
2. **`-nan.tif` Portal Rejection Trap (`IR-SHARED-SUB-02`):** Five of the 9 focus-site best files (`GEMSDOE24, 25, 27, 28, 31`) store `NaN` across `7,111,787` outside-footprint cells (`-nan.tif`), which immediately triggers DrivenData's `"Predicted values must be in range [0, 1]"` upload error. Always submit `-zeros.tif` (`nodata = None`, all `12,279,160` cells finite in `[0.0, 1.0]`).

### Master Multi-Site Submission Table

| Site | Exact File to Download & SHA-256 | Score / Holdout Metric (Strictly Labeled) | `[0, 1]` Portal Safety | Uniqueness Across Sites | Operational Guidance |
|---|---|---|---|---|---|
| **KANLERGEMSDOE2 (`2026-10-27` LDAH-EXP2 — PRIMARY)** | [`kanlergems2-ldah-exp-2-37654dots-20261027T021500Z-0ab4d26c-zeros.tif`](docs/downloads/kanlergems2-ldah-exp-2-37654dots-20261027T021500Z-0ab4d26c-zeros.tif) (`6f7d6b0e149d...`, `37,654` px) | Unsubmitted · Hide-Rec **`0.1141`** `HOLDOUT-DTI (GEMSDOE32-HIDE-RECOVER-v3.0, N=22232, 95% CI [0.1003, 0.1282])` · SGMC-CAL **`0.0815`** `HOLDOUT-DTI (GEMSDOE32-SGMC-CAL-v3.0, N=62703, 95% CI [0.0725, 0.0897])` | **SAFE `[0, 1]`** (`0` NaN) | **UNIQUE** (`24.02%` 3-px vs `0.2778`; `57.48%` max external peer; `69.50% <= 70%` vs `11a2f251`) | **PRIMARY RECOMMENDED SUBMISSION** (`verdict = promote`, 5/5 gates pass) |
| **KANLERGEMSDOE2 (`2026-10-26` HTCADS-EXP2)** | [`kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif`](docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif) (`f482d3bad4b3...`, `37,654` px) | Unsubmitted · Hide-Rec **`0.1124`** `HOLDOUT-DTI (GEMSDOE32-HIDE-RECOVER-v3.0, N=22232, 95% CI [0.0990, 0.1257])` · SGMC-CAL **`0.0789`** `HOLDOUT-DTI (GEMSDOE32-SGMC-CAL-v3.0, N=62703, 95% CI [0.0700, 0.0870])` | **SAFE `[0, 1]`** (`0` NaN) | **UNIQUE** (`39.66%` 3-px vs `0.2778`; `<= 64.91%` vs all 191 detectors) | **PRIOR SESSION BASELINE** (`verdict = promote`, 5/5 gates pass) |
| [`GEMSDOE32`](https://buffedlizard55-lab.github.io/GEMSDOE32/) | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` (`c55bafc47005...`, `37,654` px) | **`0.2778`** `ORGANIZER-CONFIRMED` · Hide-Rec Uncensored `0.0992` `[0.0860, 0.1127]` (Static `0.0045`) `HOLDOUT-DTI` · SGMC-CAL `0.0641` `HOLDOUT-DTI` | SAFE `[0, 1]` (`-zeros`) | **NOT UNIQUE** (`100.0%` in `GEMSDOE36/25/30`) | Historical 9-site champion (`d2.8 & d_cat > 2`); already submitted |
| [`GEMSDOE36`](https://buffedlizard55-lab.github.io/GEMSDOE36/) | `gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` (`e1589102fb59...`, `38,854` px) | **`0.2750`** `ORGANIZER-CONFIRMED` · Hide-Rec Static `0.0046` `HOLDOUT-DTI` · SGMC-CAL `0.0644` `HOLDOUT-DTI` | SAFE `[0, 1]` (`-zeros`) | **NOT UNIQUE** (`97.58%` w/ `GEMSDOE27`; `97.40%` w/ `B=2`) | `GEMSDOE32 B=2` + `1,200` thermal bridge dots; already submitted |
| [`GEMSDOE28`](https://buffedlizard55-lab.github.io/GEMSDOE28/) | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` (`5556aa1491ef...`, `37,660` px) | **`0.2710`** `ORGANIZER-CONFIRMED` · Hide-Rec Static `0.0294` `HOLDOUT-DTI` · SGMC-CAL `0.0630` `HOLDOUT-DTI` | **UNSAFE (`-nan`)** | **NOT UNIQUE** (`100.0%` in `GEMSDOE25`) | Feature-pruned `B=1` variant (`+0.0002` over `B=1`); `-nan` rejects |
| [`GEMSDOE31`](https://buffedlizard55-lab.github.io/GEMSDOE31/) | `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif` (`07b6db44b744...`, `40,199` px) | **`0.2708`** `ORGANIZER-CONFIRMED` · Hide-Rec Uncensored `0.0990` (Static `0.0305`) `HOLDOUT-DTI` · SGMC-CAL `0.0630` `HOLDOUT-DTI` | **UNSAFE (`-nan`)** | **0-XOR DUPLICATE** of `GEMSDOE28 h27-4-solo` (`100.0%`) | `d2.8 & d_cat > 1`; superseded by `B=2` (`0.2778`) |
| [`GEMSDOE33`](https://buffedlizard55-lab.github.io/GEMSDOE33/) | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` (`87f857d50412...`, `41,865` px) | **`0.2632`** `ORGANIZER-CONFIRMED` · Hide-Rec Static `0.0520` `HOLDOUT-DTI` · SGMC-CAL `0.0626` `HOLDOUT-DTI` | SAFE `[0, 1]` | **NOT UNIQUE** (`99.71%` w/ `GEMSDOE27`) | Tip/step-over re-rank of `H19-5`; superseded by `B=2` |
| [`GEMSDOE25`](https://buffedlizard55-lab.github.io/GEMSDOE25/) | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` (`91eae1ca6b11...`, `44,090` px) | **`0.2600`** `ORGANIZER-CONFIRMED` · Hide-Rec `0.0967` `HOLDOUT-DTI` · SGMC-CAL `0.0606` `HOLDOUT-DTI` | **UNSAFE (`-nan`)** | **0-XOR DUPLICATE** of `GEMSDOE30` (`100.0%`) | Uncollared `d2.8` thinning of `H19-5`; `-nan` rejects |
| [`GEMSDOE30`](https://buffedlizard55-lab.github.io/GEMSDOE30/) | `gemsdoe30-poisson300m-h19-5-d28-e56ea318-20261003T234340Z-allfinite.tif` (`8cf893ea2636...`, `44,090` px) | **`0.2600`** `ORGANIZER-CONFIRMED` · Hide-Rec `0.0967` `HOLDOUT-DTI` · SGMC-CAL `0.0606` `HOLDOUT-DTI` | SAFE `[0, 1]` (`allfinite`) | **0-XOR DUPLICATE** of `GEMSDOE25` (`100.0%`) | Zero-filled copy of `d2.8`; superseded by `B=2` |
| [`GEMSDOE24`](https://buffedlizard55-lab.github.io/GEMSDOE24/) | `gems24-dotted-h19-5-d1-5-20261002-7b78dc5242e8-nan.tif` (`68d0e2e49a80...`, `60,069` px) | **`0.2477`** `ORGANIZER-CONFIRMED` · Hide-Rec `0.0932` `HOLDOUT-DTI` · SGMC-CAL `0.0579` `HOLDOUT-DTI` | **UNSAFE (`-nan`)** | **NOT UNIQUE** (`100.0%` in `GEMSDOE25`) | Denser `d1.5` thinning of `H19-5` (`+15,979` redundant FPs) |
| [`GEMSDOE27`](https://buffedlizard55-lab.github.io/GEMSDOE27/) | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif` (`330033745cc8...`, `61,328` px) | **`0.2449`** `ORGANIZER-CONFIRMED` · Hide-Rec `0.0928` `HOLDOUT-DTI` · SGMC-CAL `0.0583` `HOLDOUT-DTI` | **UNSAFE (`-nan`)** | **NOT UNIQUE** (`98.02%` w/ `GEMSDOE24`) | `d1.5` + `1,259` gap bridges; standalone `H29-S` scored `0.2190` |

*Top Independent (Non-`H19-5`) Benchmarks Across the 92-Site Fleet:* `GEMSDOE70` (`0.2478` `ORGANIZER-CONFIRMED`, `37,654` px, `SGMC-CAL = 0.08570`, `43.60%` 3-px overlap w/ `KANLERGEMSDOE2`), `GEMSDOE49` (`0.2376`, `SGMC-CAL = 0.08817`, `43.92%` w/ `KANLERGEMSDOE2`), `GEMSDOE76` (`0.2343`), `GEMSDOE63` (`0.2303`), `GEMSDOE27 H29-S` (`0.2190`), `19GEMSDOE H19-5` (`0.1922`).

---

## 2. PhD-Level Forensic Analysis of `0.2778` & Path to `>0.3195` / `0.4413`

![Tversky Forensic Inversion and Dual Holdout Benchmark](docs/assets/fig2_tversky_forensic_inversion.png)

1. **Exact Tversky Ledger Inversion (`R^2 = 0.998523`):** Under Distance-Weighted Tversky (`alpha = 0.2`, `beta = 0.8`, `300 m` Euclidean triangular kernel, public catalogue masked), emitting `N` off-catalogue dots with weighted true-positive overlap `TP_w` against a hidden expert fault set of size `K` yields `1 / DTI(N) ≈ (0.8 K / TP_w) + (0.2 / TP_w) N`. Across the pure catalogue-collar pruning sequence on `H19-5` (`44,090 -> 40,199 -> 37,654` dots scoring `0.2600 -> 0.2708 -> 0.2778` `ORGANIZER-CONFIRMED`), `1 / DTI(N)` is linear in `N` with **`R^2 = 0.998523`**, proving:
   - **Zero-TP Catalogue Depletion Collar (`0 < d_cat <= 200 m`):** Deleting `6,436` dots within `<= 200 m` of public catalogue traces lost virtually **zero** true positives on the private expert test set while eliminating `0.2 * 6,436 = 1,287.2` false-positive denominator penalty.
   - **Inferred Hidden Test Set Scale:** `TP_w ≈ 5,151.3 px` and hidden off-catalogue fault truth **`K ≈ 13,734.7 px`** (`~0.269%` footprint prevalence; `12,632–13,735 px` across clustering bounds), giving `GEMSDOE32 B=2` `~37.51%` weighted recall.
2. **Why Pruning `H19-5` Cannot Reach `0.3195` (`#5`) or `0.4413` (`#1`):** Feature-pruning `H19-5` (`GEMSDOE28` `40,199 -> 37,660` dots) gained only `+0.0002` (`0.2708 -> 0.2710`), plateauing near `~0.285–0.295`. At `37,654` dots, reaching `#5` (`0.3195`) requires **`TP_w ≈ 5,917 px`** (`+14.9%` genuinely new fault recall) and reaching `#1` (`0.4413`) requires **`TP_w ≈ 8,172 px`** (`+58.6%` new recall). That mathematically requires discovering **blind intrabasin, updip range-front, and hydrothermal accommodation conduits** missed by `H19-5` (`Faulds & Hinz, 2015`).

---

## 3. Five Pre-Registered Geological Hypotheses (`H-K1..H-K5`) & 3-Experiment Ablation

Frozen prior to training in [`registry/preregistration_htcads.json`](registry/preregistration_htcads.json); full mathematical derivations and verified DOIs in [`docs/research.html`](docs/research.html) and [`registry/sources.json`](registry/sources.json).

| Rank | ID | Specific Layers | Physical Fault / Geothermal Signature | Why Missing from USGS/INGENIOUS Catalogue & Novelty | Obtainable Now? |
|---|---|---|---|---|---|
| **#1** | **`H-K1` (`HTCADS`)** | `training_features.tif` (sharp subsurface/MT/slope bands) + GeoDAWN `K,Th,U,TMI_up150` + GDR `#1391` (`wells/springs, 2m probes, sinter, vents`) + 3DEP 1m LiDAR + fold-visible `existing_faults.tif` | Scale-separated Out-of-Quadrant Sharp GBDT + First-Principles Multi-Physics Conduit index + zero-mean contour-orthogonal LiDAR log-odds residual + purely directional fault-tip/relay propagation + 300 m CELF | Catches blind Basin-and-Range geothermal conduits (~75% of Great Basin systems; Faulds & Hinz 2015) while immunizing against USGS Qfaults alluvial valley-floor mapping bias and LiDAR-void starvation | **YES — Validated & Promoted (`EXP-2`)** |
| **#2** | **`H-K2` (`WUDP`)** | `iso_grav_anom`, `rtp`, `tmi`, `TMI_up150`, `depth_to_base_surf` | 2D FFT upward-continuation (`z = 0, 150, 400 m`) crest-migration vector projecting hanging-wall HGM maxima updip to the surface fault trace (`Grauch & Hudson, 2007`) | Dipping (`50–65°`) normal faults shift raw gravity gradient crests `0.5–1.5 km` basinward outside the 300 m DTI kernel | **YES — Folded into `EXP-2` (`+0.0043` Hide-Rec lift)** |
| **#3** | **`H-K3` (`MTSE`)** | `cond_surf`, `iso_grav_anom_hg`, `det_elev_slope` | Lateral gradient of log-MT conductivity (`|\nabla \log(1+\sigma)|`) co-aligned with basement steps | Targets lateral smectite clay-cap fault seals rather than interior playa brine conductivity maxima | **YES — Folded into `H-K1`** |
| **#4** | **`H-K4` (`AFDK`)** | Seamless 10 m USGS 3DEP DEM + `det_elev_slope` | Transverse ephemeral-wash drainage-azimuth vorticity along piedmont fans | Captures low-slip (`<0.05 mm/yr`) oblique Walker Lane faults across the 24.6% 1 m LiDAR void | Deferred (USGS S3 host outside sandbox allowlist) |
| **#5** | **`H-K5` (`IPGC`)** | NASA/JPL OPERA `DISP-S1` Sentinel-1 InSAR + `cond_surf` | Sub-200 m horizontal step edges in seasonal poroelastic ground deformation across fault-gouge aquifer barriers | Detects zero-relief intrabasin playa barrier faults | Deferred (ASF DAAC host outside sandbox allowlist) |

### Controlled `2026-10-27` 3-Experiment `LDAH` Holdout Results (`214.7 s` Total Runtime `<= 2 hr` Budget)

On `2026-10-27`, we ingested 5 official external layers (`h52_scarp3m_100m.tif`, `usgs_comcat_geodawn.csv`, `usgs_heat_flow_wells_epsg32611.csv`, `acquisition_block_id_100m.tif`, `blm_closed_claim_distance_m.tif`) and 10 seamless 10 m USGS 3DEP DEM channels (`dem10/*.f32.npy`) into `.cache/gems_data/` (`41` SHA-256-verified entries in `registry/data_manifest.json`) to test 5 untried geological discovery hypotheses (`H-LDAH-1` Listric Updip Gravity Migration, `H-LDAH-2` Survey-Seam-Damped Magnetic Structure-Tensor Anisotropy, `H-LDAH-3` Relief-Normalized 10 m USGS 3DEP Piedmont Scarps & Concave Junctions bridging the `24.60%` 1 m LiDAR void, `H-LDAH-4` 3 m Quaternary Scarp Kinematic Coherence, and `H-LDAH-5` Borehole Conductive Heat-Flow Upflow, Updip ComCat Swarms, & BLM Epithermal Corridors):

| Arm | Description | `HOLDOUT-DTI`: `HIDE-RECOVER-v3.0` (`N=22,232`, 95% CI) | Paired Δ vs `0.2778` Champ (95% CI) | `HOLDOUT-DTI`: `SGMC-CAL-v3.0` (`N=62,703`, 95% CI) | Max Detector 3-px Overlap (`<= 0.70`) | Verdict |
|---|---|---|---|---|---|---|
| `REF` | `GEMSDOE32 B=2` (`0.2778 ORGANIZER-CONFIRMED`, uncensored `d_vis > 2`) | `0.099202` `[0.0860, 0.1127]` | `0.00000` (baseline) | `0.064121` `[0.0567, 0.0716]` | `100.0%` (clone block) | Baseline |
| `LDAH-EXP1` | `LDAH-VoidBridged-Dem10SGMC` (`w_pied=0.770, beta=0.835, w_tip=1.72`, `37,654` dots) | `0.108180` `[0.0942, 0.1225]` | `+0.00898` `[-0.0049, +0.0235]` | **`0.083318`** `[0.0741, 0.0917]` (`+0.01920`, CI `[+0.0078, +0.0300]`) | `67.36%` (`PASS`) | SGMC Specialist |
| **`LDAH-EXP2`** | **`LDAH-TriRegime-Discovery` (`w_pied=0.805, beta=0.818, w_tip=1.76`, `37,654` dots)** | **`0.114131`** `[0.1003, 0.1282]` | **`+0.01493` `[+0.0009, +0.0292]` (97.8% win; beats `11a2f251 = 0.1124`)** | **`0.081514`** `[0.0725, 0.0897]` (`+0.01739`, CI `[+0.0063, +0.0276]`; beats `11a2f251 = 0.0789`) | **`69.50%` (`24.02%` vs `0.2778`, `57.48%` max external, `PASS`)** | **PROMOTE (Primary)** |
| `LDAH-EXP3` | `LDAH-TipPriority-BasinBridge` (`w_pied=0.720, beta=0.850, tip_cut=0.0047`, `37,654` dots) | **`0.120090`** `[0.1055, 0.1351]` | **`+0.02089` `[+0.0049, +0.0378]`** | `0.070573` `[0.0621, 0.0784]` (`+0.00645`) | `65.60%` (`PASS`) | Valley-Bridge Specialist |

### Controlled `2026-10-26` 3-Experiment `HTCADS` Holdout Results (`603.0 s` Total Runtime `<= 2 hr` Budget)

| Arm | Description | `HOLDOUT-DTI`: `HIDE-RECOVER-v3.0` (`N=22,232`, 95% CI) | Paired Δ vs `0.2778` Champ (95% CI) | `HOLDOUT-DTI`: `SGMC-CAL-v3.0` (`N=62,703`, 95% CI) | Max Detector 3-px Overlap (`<= 0.70`) | Verdict |
|---|---|---|---|---|---|---|
| `REF` | `GEMSDOE32 B=2` (`0.2778 ORGANIZER-CONFIRMED`, uncensored `d_vis > 2`) | `0.099202` `[0.0860, 0.1127]` | `0.00000` (baseline) | `0.064121` `[0.0567, 0.0716]` | `100.0%` (clone block) | Baseline |
| `EXP-1` | `HTCADS-SubsurfGeo` (`100%` LiDAR-blind, `B=2.0`, `37,654` dots) | `0.108070` `[0.0955, 0.1203]` | `+0.00887` `[-0.0021, +0.0193]` | **`0.081431`** `[0.0727, 0.0894]` | `62.93%` (`PASS`) | Ablation |
| **`EXP-2`** | **`HTCADS-DualRegime` (`+H-K2` Updip Gravity `+` Zero-Mean Ortho-LiDAR, `B=2.0`, `37,654` dots)** | **`0.112353`** `[0.0990, 0.1257]` | **`+0.01315` `[+0.0019, +0.0250]` (99.2% win)** | **`0.078913`** `[0.0700, 0.0870]` (`+0.01479`) | **`64.91%` (`39.66%` vs `0.2778`, `PASS`)** | **PROMOTE** |
| `EXP-3` | `HTCADS-DinkelbachAniso` (Anisotropic tip `d > 1.45` / flank `d > 2.15`, `37,654` dots) | `0.111597` `[0.0987, 0.1243]` | `+0.01240` `[+0.0013, +0.0238]` | `0.076938` `[0.0683, 0.0848]` | `65.52%` (`PASS`) | Negative vs `EXP-2` |

![Focus-9 Uniqueness Matrix and Rule 4 Leakage Canary](docs/assets/fig3_focus9_uniqueness_matrix.png)

### Parallel Lane `KG2-H1: FVCA-SUBMOD` (`arena/e7db879b`, Informative Negative Deliverable) & Cross-Lane 72-Raster Verification

In parallel (`research/fvca_hypotheses.md`, `research/fvca_review.md`, `scripts/build_fvca_features.py`, `scripts/run_fvca_experiments.py`, `src/gems/submodular_celf.py`), we tested a pure supervised 60-channel 2-stage Auto-Context `LightGBM + ExtraTrees` lane (`KG2-FVCA-SUBMOD`) fusing EDT-border-repaired potential-field derivatives (`IR-KG2-BORDER-CLIFF`, `IR-KG2-TC-MISLABEL`), up-slope hydraulic back-projection (`+∇det_elev`) of DOE GDR #1391 2m probes (`2,782` probes), sinter/tufa deposits (`281` sites), chemical geothermometers (`27,092` wells/springs), K-on-Th alteration, playa-deconfounded MT clay-cap edges, and TIGER road-cleared 1m LiDAR scarps (`max single-feature canary AUC = 0.629717 <= 0.90`, `evidence/fvca_canaries.json`):
- **Geothermal Back-Projection Gain (`HOLDOUT-DTI`):** `EXP-1 (44ch)` `0.158138` $\to$ **`EXP-2 (60ch FVCA)` `0.169279` `[0.155449, 0.183430]`** on `gems-segment-pooled-v1` (`N=60,988`, `4/4` fold wins over `D2.8 vis-B2 = 0.161630`; `+0.015609` paired 95% CI `[+0.008142, +0.023613]` over `E1`) and `0.106071` (`EXP-3 CELF = 0.106529`) on `GEMSDOE32-HIDE-RECOVER-v3.0` (`N=22,232`).
- **Why `KG2-FVCA-SUBMOD` Triggered Automated Rule 1 Stop (`verdict = "negative"` — DO NOT SUBMIT `cab53e1b`):** While `KG2-FVCA-SUBMOD` (`docs/downloads/kanlergemsdoe2-kg2h1-fvca-submod-20261026T235000Z-cab53e1b-zeros.tif`, SHA-256 `29128ad7a9290d2afb008e944ea20171d2224ba0b77ec81aadc2ce416a13491f`, `38,500` dots) passed uniqueness vs. all 9 focus sites (`max 44.74%`, `33.36%` vs `GEMSDOE32`), unweighted training on `y = labels.tif` caused **`80.68% > 70%`** 3-px dot convergence onto `10GEMSDOE`'s dense supervised scarp surface (`gems10-h25-ctx-ridge`, `IR-KG2-SCARP-CONVERGENCE`) and yielded `0.044042` on blind `SGMC-CAL-v3.0`.
- **Independent Cross-Lane 72-Raster Audit (`evidence/cross_lane_72raster_audit.json`):** Auditing all three active `KANLERGEMSDOE2` rasters on the identical 72-raster GEMSDOE registry independently confirms that **`HTCADS-DualRegime (EXP-2)` (`11a2f251-zeros.tif`, max `64.91% <= 70%`)** and **`KG2-MGHV-EXP-1` (`f5a469e94b14-zeros.tif`, max `62.68% <= 70%`)** both genuinely clear the portfolio duplicate gate (`41.75%` / `29.04%` mutual 3-px overlap), proving empirically why Dual-Population Noisy-OR / Two-Regime submodular allocation is required to escape range-front scarp convergence. **Submit `HTCADS-DualRegime (EXP-2)` (`11a2f251-zeros.tif`), NOT `KG2-FVCA-SUBMOD` (`cab53e1b-zeros.tif`).**

---

## 4. Irregularities Logged, Limitations & Next-Session Recommendations

Complete table in [`docs/irregularities.html`](docs/irregularities.html):
- **Shared Tool & Data Irregularities Fixed/Quarantined:** `IR-SHARED-SOFT-01` (soft probability binarization bug in `holdout.py`), `IR-SHARED-SUB-02` (`-nan.tif` portal `[0, 1]` rejection), `IR-32-INSTR-03` (static `B=2` holdout self-censoring `0.0045` vs uncensored `0.0992` + `holdout.py:708` `d_visible_sub` fix), `IR-KG2-LEAK-01` (`sb_slip_tendency` `AUC=0.9994` Qfault trace leak quarantined), `IR-KG2-DATA-02` (`sample_submission.tif` contains `60,988` `1`s), `IR-KG2-ENC-03` (`Paleo_geothermal_final.csv` CP1252 `0xb0`), `IR-REG-LATTICE-03` (`r13-lattice-s5_v2` 5-px space-filling calibration grid), and `IR-PROV-04` (two `0-XOR` focus-site duplicate pairs).
- **Self-Caught Pass-1/2 Bugs Remediated (`IR-KG2-BUG-01..04`):** Fixed `d=3 px` isotropic `d_vis` annulus inversion, removed 50-km coordinate-proxy blobs, fixed `+det_elev` summit Hessian sign inversion (`det_elev_slope` + `-det_elev` toe concavity), and calibrated `pi_tip` (`0.028`) vs `pi_blind` (`P99.2 = 0.045`) portfolio balance.
- **Limitations & Next-Session Roadmap:** (1) Upload `kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif` to DrivenData and log the `ORGANIZER-CONFIRMED` live score; (2) on an unrestricted workstation outside the sandbox allowlist, ingest public NASA OPERA `DISP-S1` InSAR (`H-K5`) and seamless 10 m USGS 3DEP DEM (`H-K4`) across the `24.60%` 1 m LiDAR void swath; (3) extend uniform 400 m FFT upward continuation to locally depth-scaled 3D listric fault continuation.

---

## 5. End-to-End Reproducibility

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/pip install --no-deps -e .
.venv/bin/python scripts/restore_data.py             # Restore & SHA-256 verify all 41 competition + external + 10m DEM files
.venv/bin/python scripts/prepare_htcads_data.py      # Build 58-ch stack + verify 62-feature Rule 4 Leakage Canary (<=0.90)
.venv/bin/python scripts/audit_focus_sites.py        # Recompute 9-site + 92-site forensic audit
.venv/bin/python scripts/run_ldah_experiments.py     # Run 2026-10-27 LDAH EXP-1..3 + emit GeoTIFF + run 5 automated gates
.venv/bin/python scripts/validate_submission.py \
  --tif docs/downloads/kanlergems2-ldah-exp-2-37654dots-20261027T021500Z-0ab4d26c-zeros.tif \
  --run-card evidence/run_card.json --out evidence/validator_receipt.json
.venv/bin/python scripts/evaluate_holdout.py --verify-kg2
.venv/bin/pytest -v
```

---

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
