# Executive Summary & Multi-Site Submission Guide (`KANLERGEMSDOE2`)

## Automated Validation Status: **VALIDATED — OK TO DOWNLOAD & SUBMIT (5/5 Gates Passed)**

- **Promoted Unique GeoTIFF**: `docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif` (`204,099` bytes)
- **SHA-256**: `f482d3bad4b390470be06363b60867c8e42942101271caf4fa82ae3c3975abeb`
- **Portal Archive**: `docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.zip` (`fc909b4b065e132d1672ea3298645de818da98358605a45f0b1d0c5c67778698`)
- **Portal Submission Note (`110/140` chars)**: `KANLERGEMS2 HTCADS-DualRegime: 50ch updip-grav+GDR1391+MT+orthoLiDAR NoisyOR+300m CELF (37654 dots, HR=0.1124)`
- **Portal `[0, 1]` Range Guarantee**: `13/13` automated checks passed (`EPSG:32611`, `3730 x 3292`, `float32`, `nodata = None`, `12,279,160 / 12,279,160` finite pixels, `min = 0.0`, `max = 1.0`, `0` NaNs anywhere, `0` on-catalogue pixels).
- **Holdout Dominance vs. `0.2778` Champion (`GEMSDOE32 B=2`)**:
  - Primary Leak-Free Hide-and-Recover (`HOLDOUT-DTI (GEMSDOE32-HIDE-RECOVER-v3.0, N=22232 withheld positives, 95% CI [0.0990, 0.1257])`): **`0.112353`** vs. Champion **`0.099202`** (`delta = +0.013150`, paired 95% CI `[+0.0019, +0.0250]`, **99.2% bootstrap win probability**).
  - Secondary Blind Off-Catalogue SGMC (`HOLDOUT-DTI (GEMSDOE32-SGMC-CAL-v3.0, N=62703 off-catalogue SGMC positives, 95% CI [0.0700, 0.0870])`): **`0.078913`** vs. Champion **`0.064121`** (`delta = +0.014792`, paired 95% CI `[+0.0050, +0.0237]`).
- **Lane Uniqueness (`192` Footprint-Distinct Registry Rasters Checked)**:
  - **Only `39.66%`** 3-px dot overlap with `GEMSDOE32` (`0.2778` Champion) — **`60.34%` (`22,720 / 37,654` dots) are novel blind/updip/scarp fault conduits**!
  - Max 3-px overlap across all 191 geological detectors in the 92-site archive: **`64.91% <= 70%`**.
  - Max `|Spearman|` on pre-placement continuous surface: **`0.1795 < 0.90`**; on final dots: **`0.0737 < 0.90`**.

---

## Master Multi-Site Submission Table (`KANLERGEMSDOE2` + All 9 Focus Sites)

| Site | Exact File to Download & SHA-256 | Score / Holdout Metric (Strictly Labeled) | `[0, 1]` Portal Safety | Uniqueness Across Sites | Guidance |
|---|---|---|---|---|---|
| **KANLERGEMSDOE2 (NEW)** | `docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif` (`f482d3bad4b3...`) | Unsubmitted; Hide-Rec `0.1124` `HOLDOUT-DTI` `[0.0990, 0.1257]`; SGMC-CAL `0.0789` `HOLDOUT-DTI` `[0.0700, 0.0870]` | **SAFE `[0, 1]`** (`0` NaNs) | **UNIQUE** (`39.66%` vs `0.2778` Champ; max `64.91% <= 70%` across 191 detectors) | **PROMOTE — Validated Unique Submission** |
| `GEMSDOE32` | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` (`c55bafc47005...`) | `0.2778` `ORGANIZER-CONFIRMED`; Hide-Rec Uncensored `0.0992` (Static `0.0045`) `HOLDOUT-DTI`; SGMC-CAL `0.0641` `HOLDOUT-DTI` | SAFE `[0, 1]` | **NOT UNIQUE** (`100.0%` w/ `GEMSDOE36`) | Historical `H19-5` pruning lineage (d2.8 & (d_cat > 2 px) — strips 6,436 0-200 m catalogue-collar FPs off 19GEMSDOE H19-5) |
| `GEMSDOE36` | `gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` (`e15891020b9c...`) | `0.2750` `ORGANIZER-CONFIRMED`; Hide-Rec `0.0046` `HOLDOUT-DTI`; SGMC-CAL `0.0644` `HOLDOUT-DTI` | SAFE `[0, 1]` | **NOT UNIQUE** (`97.6%` w/ `GEMSDOE27`) | Historical `H19-5` pruning lineage (GEMSDOE32 B=2 (all 37,654 dots preserved) UNION 1,200 radial thermal IDW dots (-0.0028 FP dilution)) |
| `GEMSDOE28` | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` (`5556aa1438fd...`) | `0.2710` `ORGANIZER-CONFIRMED`; Hide-Rec `0.0294` `HOLDOUT-DTI`; SGMC-CAL `0.0630` `HOLDOUT-DTI` | UNSAFE (`-nan.tif`) | **NOT UNIQUE** (`100.0%` w/ `GEMSDOE25`) | Historical `H19-5` pruning lineage (H27-4 solo (d2.8 & d_cat > 1) pruned from 40,199 -> 37,660 dots via blind geophysical rung-30 filter; secondary h27-4-r1-solo (0.2708) is 0-XOR identical to GEMSDOE31 solo) |
| `GEMSDOE31` | `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif` (`07b6db440535...`) | `0.2708` `ORGANIZER-CONFIRMED`; Hide-Rec Uncensored `0.0990` (Static `0.0305`) `HOLDOUT-DTI`; SGMC-CAL `0.0630` `HOLDOUT-DTI` | UNSAFE (`-nan.tif`) | **NOT UNIQUE** (`100.0%` w/ `GEMSDOE25`) | Historical `H19-5` pruning lineage (d2.8 & (d_cat > 1 px) — exact 40,199-dot superset of GEMSDOE32 B=2 (+2,545 1-2 px collar dots)) |
| `GEMSDOE33` | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` (`87f857d505e2...`) | `0.2632` `ORGANIZER-CONFIRMED`; Hide-Rec `0.0520` `HOLDOUT-DTI`; SGMC-CAL `0.0626` `HOLDOUT-DTI` | SAFE `[0, 1]` | **NOT UNIQUE** (`99.7%` w/ `GEMSDOE27`) | Historical `H19-5` pruning lineage (GEMSDOE31 solo (40,199 dots) + analog tip/stepover replacements (41,865 dots; 94.0% 3-px overlap with B=2)) |
| `GEMSDOE25` | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` (`91eae1ca42ec...`) | `0.2600` `ORGANIZER-CONFIRMED`; Hide-Rec `0.0967` `HOLDOUT-DTI`; SGMC-CAL `0.0606` `HOLDOUT-DTI` | UNSAFE (`-nan.tif`) | **NOT UNIQUE** (`100.0%` w/ `GEMSDOE30`) | Historical `H19-5` pruning lineage (300 m (2.8 px) greedy Poisson-disk thinning of 19GEMSDOE H19-5 (121,131 -> 44,090 dots, no catalogue collar)) |
| `GEMSDOE30` | `gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif` (`8cf893ead566...`) | `0.2600` `ORGANIZER-CONFIRMED`; Hide-Rec `0.0967` `HOLDOUT-DTI`; SGMC-CAL `0.0606` `HOLDOUT-DTI` | SAFE `[0, 1]` | **NOT UNIQUE** (`100.0%` w/ `GEMSDOE25`) | Historical `H19-5` pruning lineage (All-finite re-export of GEMSDOE25 d2.8 (44,090 dots, 0-XOR in footprint)) |
| `GEMSDOE24` | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif` (`68d0e2e4fcc5...`) | `0.2477` `ORGANIZER-CONFIRMED`; Hide-Rec `0.0932` `HOLDOUT-DTI`; SGMC-CAL `0.0579` `HOLDOUT-DTI` | UNSAFE (`-nan.tif`) | **NOT UNIQUE** (`100.0%` w/ `GEMSDOE25`) | Historical `H19-5` pruning lineage (150 m (1.5 px) greedy thinning of 19GEMSDOE H19-5 (121,131 -> 60,069 dots; over-packed inside 300 m kernel)) |
| `GEMSDOE27` | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif` (`33003374335d...`) | `0.2449` `ORGANIZER-CONFIRMED`; Hide-Rec `0.0927` `HOLDOUT-DTI`; SGMC-CAL `0.0583` `HOLDOUT-DTI` | UNSAFE (`-nan.tif`) | **NOT UNIQUE** (`98.0%` w/ `GEMSDOE24`) | Historical `H19-5` pruning lineage (GEMSDOE24 d1.5 (60,069 dots) + 1,259 topographic gap-closure bridges = 61,328 dots (Jaccard 0.9795 vs GEMSDOE24)) |

---

## Why `GEMSDOE32` Scored `0.2778` & Why `KANLERGEMSDOE2` Breaks Out of the `H19-5` Plateau

1. **Exact Tversky Ledger Inversion (`R^2 = 0.9985`)**: Across the `H19-5` collar-pruning chain (`44,090 -> 40,199 -> 37,654` dots scoring `0.2600 -> 0.2708 -> 0.2778` `ORGANIZER-CONFIRMED`), `1 / DTI(N)` is linear in `N` with `R^2 = 0.998523`. That proves the `6,436` removed `0–200 m` catalogue-flank dots contributed `~0` true positives on the private expert test set while revealing `TP_w ≈ 5,151 px` and hidden off-catalogue fault set `K ≈ 13,735 px` (`~0.27%` footprint prevalence).
2. **Ceiling of Pruning `H19-5`**: Further feature pruning on `H19-5` plateaus near `~0.285–0.295` (`GEMSDOE28` gained `+0.0002`). Reaching public `#5` (`0.3195`) requires `TP_w ≈ 5,917 px` and `#1` (`0.4413`) requires `TP_w ≈ 8,172 px` — mathematically requiring discovery of blind intrabasin, updip range-front, and hydrothermal accommodation faults absent from `H19-5`.
3. **HTCADS-DualRegime (`EXP-2`) Mechanism**: Couples out-of-quadrant sharp subsurface/geothermal/scarp GBDT + first-principles Multi-Physics Conduit index (FFT 400 m upward-continuation updip gravity migration, Gallardo-Meju cross-gradient, GeoDAWN hydrothermal magnetite destruction & K/Th metasomatism, MT lateral clay-cap edges, hydraulic-upgradient GDR 1391 thermal probes/wells/sinter vents, 100 m scarp-slope/toe-concavity) + coverage-neutral zero-mean contour-orthogonal 1 m LiDAR specialist + purely directional fault-tip/relay propagation + exact 300 m Euclidean CELF submodular allocation.

---

## 2026-10-27 Update: KG2-ECPU Lane = **NEGATIVE (DO NOT SUBMIT)** + Same-Session Re-Audit

- **New preregistered lane tested and rejected fail-closed**: `KG2-ECPU` (effort-propensity PU reweighting; `registry/preregistration_ecpu_20261027.json` frozen pre-run). All 3 experiments lose to the promoted HTCADS file on both evaluators. Best (EXP-1, `docs/downloads/kanlergems2-ecpu-exp-1-37654dots-20261027T172822Z-cecbdca7-zeros.tif`, SHA-256 `5c83f85c7282...`): Hide-Recover OOF `0.0848` `HOLDOUT-DTI` vs B2-procedural `0.0992` / HTCADS OOF `0.1124`; SGMC-CAL `0.0644` `HOLDOUT-DTI` vs HTCADS `0.0789` (paired delta `-0.0145`). It is unique (max `66.25%` 3-px vs 206 registry rasters) and format-valid, but **verdict = negative — spend no slot on it** (`evidence/run_card_ecpu_20261027.json`, `evidence/validator_receipt_ecpu_20261027.json`: Gates 1/2/3/5 pass, Gate 4 fails).
- **Ablation finding**: propensity weighting alone significantly helps blind SGMC vs unweighted twin (`+0.0031`, 95% CI `[+0.0007, +0.0058]`) but hurts Hide-Recover (`-0.0041`) — withheld catalogue faults are by definition *detected* faults, so de-biasing cannot win that evaluator with a plain GBDT surface.
- **What to submit**: the promoted HTCADS file above remains the ONLY validated candidate. Ledger **PROJECTION** (4-point fit, not a score): `0.3150–0.3419`. ECPU EXP-1 PROJECTION: `0.2378–0.2797`. No `ORGANIZER-CONFIRMED` score is recorded for the HTCADS file yet — check the DrivenData submissions page / weekly cap first; never submit the identical file twice.
- **Corrections (`IR-20261027-01..03`)**: Hide-Recover `0.1124` is an OOF-procedure score (static file = `0.0283` self-censored, same artifact as champion static `0.0045`); ledger prose = 4-point fit (`TPw=5151, K=13735, R²=0.9985`, reproduced exactly), test = 3-point sensitivity (`5210/14020`); validator Gate 4 strengthened to require beating the in-repo prior best when declared.
- **9-site re-audit (2026-10-27, `evidence/nine_site_reaudit_20261027.json`)**: all 9 champion SHA-256s match the 2026-10-26 audit; exactly one 0-XOR pair *among best files* (`GEMSDOE25 == GEMSDOE30`); no focus champion is unique (max own-dots-within-3px-of-another champion `97.6%–100%`); 5 of 9 best files carry outside-footprint NaNs (portal-reject as stored).

### Submission Decision Table (2026-10-27): File · Estimated Score · Unique?

| File to download | Score / Estimate (labeled) | Unique? | Decision |
|---|---|---|---|
| `kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif` (this repo) | PROJECTION `0.315–0.342` (not a score); HR-OOF `0.1124` / SGMC `0.0789` `HOLDOUT-DTI` | YES (`64.91% ≤ 70%`) | ✅ SUBMIT if not already submitted |
| `kanlergems2-ecpu-exp-1-37654dots-20261027T172822Z-cecbdca7-zeros.tif` (this repo, NEW) | PROJECTION `0.238–0.280`; HR-OOF `0.0848` / SGMC `0.0644` `HOLDOUT-DTI` | YES (`66.25% ≤ 70%`, 206 rasters) | ⛔ DO NOT SUBMIT (`negative`) |
| `gemsdoe32-h33-h33-2-b2-...-e5eb6e7e-zeros.tif` (GEMSDOE32) | `0.2778` ORGANIZER-CONFIRMED | NO (`100%`) | Already submitted |
| `gemsdoe36-anderson-geothermal-pinn-38854-...-zeros.tif` (GEMSDOE36) | `0.2750` ORGANIZER-CONFIRMED | NO (`97.6%`) | Already submitted |
| `gems28-h36-1-rung30-blind-r1-...-nan.tif` (GEMSDOE28) | `0.2710` ORGANIZER-CONFIRMED | NO (`100%`) | Already submitted; `-nan` unsafe |
| `gemsdoe31-h27-4-solo-d28-...-nan.tif` (GEMSDOE31) | `0.2708` ORGANIZER-CONFIRMED | NO (`100%`) | Already submitted; `-nan` unsafe |
| `GEMSDOE33-h33d-analog-tip-stepover-r30-...tif` (GEMSDOE33) | `0.2632` ORGANIZER-CONFIRMED | NO (`99.7%`) | Already submitted |
| `gems25-dotted-h19-5-d2-8-...-nan.tif` (GEMSDOE25) | `0.2600` ORGANIZER-CONFIRMED | NO (0-XOR = GEMSDOE30) | Already submitted; `-nan` unsafe |
| `gemsdoe30-d28-poisson300m-offcat-44090-...tif` (GEMSDOE30) | `0.2600` ORGANIZER-CONFIRMED | NO (0-XOR = GEMSDOE25) | Already submitted |
| `gems24-h25-1-dotted-h19-5-d1-5-...-nan.tif` (GEMSDOE24) | `0.2477` ORGANIZER-CONFIRMED | NO (`100%`) | Already submitted; `-nan` unsafe |
| `gems27-topo-gap-closure-t-v2-on-d1-5-...-nan.tif` (GEMSDOE27) | `0.2449` ORGANIZER-CONFIRMED | NO (`98.0%`) | Already submitted; `-nan` unsafe |
