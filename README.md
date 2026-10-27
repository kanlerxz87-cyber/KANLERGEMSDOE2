# KANLERGEMSDOE2 — DOE GEMS Geothermal Fault & Vent Discovery Desk

**Start every session here, then inspect [`research/run_card.json`](research/run_card.json), [`research/hypotheses.md`](research/hypotheses.md), [`evidence/fvca_experiments.json`](evidence/fvca_experiments.json), and [`docs/index.html`](docs/index.html).**

---

## Current Automated Submission Verdict — `2026-10-26 UTC`

> ### **VERDICT: DO NOT SUBMIT TO DRIVENDATA PORTAL THIS WEEK (`verdict = "negative"` — SAVE WEEKLY SLOT)**
>
> - **Generated Unique GeoTIFF (Research / Audit Artifact):** [`docs/downloads/kanlergemsdoe2-kg2h1-fvca-submod-20261026T235000Z-cab53e1b-zeros.tif`](docs/downloads/kanlergemsdoe2-kg2h1-fvca-submod-20261026T235000Z-cab53e1b-zeros.tif) (`809 KB`, SHA-256 `29128ad7a9290d2afb008e944ea20171d2224ba0b77ec81aadc2ce416a13491f`) + [single-TIFF `.zip`](docs/downloads/kanlergemsdoe2-kg2h1-fvca-submod-20261026T235000Z-cab53e1b-zeros.zip) (`174 KB`).
> - **G1 · Strict GeoTIFF & `[0, 1]` Portal Range Gate:** **PASS** — `float32`, `EPSG:32611`, `3730 × 3292`, geotransform `(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)`, `nodata=None`, `0` NaN/Inf across all `12,279,160` cells, values strictly in `[0.0, 1.0]`, `38,500` off-catalogue binary dots (`0` pixels on `labels.tif`).
> - **G2 · 60-Feature Single-Feature Leakage Canary:** **PASS** — two-sided `max(AUC, 1 - AUC) = 0.629717 <= 0.90` across all 60 channels (`gems-segment-pooled-v1`).
> - **G3a · Uniqueness vs. All 9 Focus Sites (`GEMSDOE24..36`):** **PASS** — max 3-px dot overlap = `44.74% <= 70%` (`33.36%` vs `GEMSDOE32` `0.2778` champion; `|Spearman| <= 0.248`).
> - **G3b · Expanded 72-Raster Portfolio Duplicate Stop (Protocol Rule 1):** **STOP TRIGGERED (`FAIL`)** — `80.68%` directional 3-px overlap with `10GEMSDOE`'s dense `174,232`-pixel supervised scarp ridge (`gems10-h25-ctx-ridge`, `0.2286` live) and `75.56%` with `gems10-h28-dotted-ridge` (`0.2336` live). Logged transparently as a convergent supervised-scarp duplicate and stopped at Experiment `3/3` without Perturb-to-Evade.
> - **G4/G5 · Spatially-Blocked Holdout & Slot Protection:** `EXP-2` sets a **new local out-of-fold high** on canonical `SegmentHoldout` (`HOLDOUT-DTI = 0.169279`, `95% CI [0.155449, 0.183430]`, `n=60,988`), beating prior `E1` (`0.153670`, paired 95% CI `[+0.008142, +0.023613]`) and winning **4/4 quadrants** over the `0.2778` champion's fold-local proxy (`D2.8 vis-B2 = 0.161630`), plus `0.106071` (`EXP-3 CELF = 0.106529`) vs `0.099202` on `GEMSDOE32-HIDE-RECOVER-v3.0` (`n=22,232`). However, the conservative 10 km block-bootstrap paired 95% CI vs `D2.8 vis-B2` (`[-0.005028, +0.020520]`) spans zero and supervised `y = labels.tif` learners empirically ceiling at `0.2336–0.2478` live (`< 0.2778`), so **no new TIFF is approved for live portal submission**.

- **GitHub Pages Hub:** [`docs/index.html`](docs/index.html) (expected deployment URL: `https://kanlerxz87-cyber.github.io/KANLERGEMSDOE2/`)
- **Step-by-Step DrivenData Submission Guide:** [`docs/executive-summary.html`](docs/executive-summary.html)
- **Canonical JSON Run Card:** [`research/run_card.json`](research/run_card.json) · **Selector Decision:** [`evidence/selector_decision.json`](evidence/selector_decision.json)

---

## 1. Executive Summary Table — Focus Sites (`GEMSDOE24..36`) & `KANLERGEMSDOE2`

Every number carries its required evidence label: **`OWNER-REPORTED`** (cross-repo ledger report; not `ORGANIZER-CONFIRMED` because no portal screenshot/receipt is stored in Git), **`HOLDOUT-DTI`** (measured local spatially-blocked evaluator), or **`PROJECTION`** (out-of-sample calibrated `LLI-S3` model over 111 live-scored rasters, `LOO MAE = 0.0220`, never a score).

| Site | Canonical Artifact (`SHA-256` prefix · Dots) | Live Score (`OWNER-REPORTED`) | `SegmentHoldout v1` (`n=60,988`) | `HIDE-RECOVER v3` (`n=22,232`) | `LLI-S3` (`PROJECTION`) | Uniqueness vs. Other GEMSDOE Sites | OK to Download & Submit? |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **GEMSDOE24** | `gems20-h20-5-d15-20261001-f92dd2da-zeros.tif` (`3e0730e8…` · `60,069`d) | `0.2477` | `0.17183` | `0.09315` | `0.2668` | **FAIL** (`100.0%` 3-px ov w/ `G30`) | **NO** — Superseded `H19-5` `D1.5` ancestor |
| **GEMSDOE25** | `gems20-h20-5-d28-20261001-48215c27-zeros.tif` (`3e78737f…` · `44,090`d) | `0.2600` | `0.16163` | `0.09674` | `0.2700` | **FAIL** (`100.0%` identical to `G30`) | **NO** — Superseded by `G32` `B=2` |
| **GEMSDOE27** | `gems27-s27-2-antishore-20261004-ee5b14ca-zeros.tif` (`a9bf76b5…` · `61,328`d) | `0.2190` | `0.17264` | `0.09275` | `0.2646` | **FAIL** (`98.0%` 3-px ov w/ `G24`) | **NO** — Lower live score (`0.2190`) |
| **GEMSDOE28** | `gems28-h28-collar-b2-20261004-zeros.tif` (`7c74270a…` · `37,660`d) | `0.2710` | `0.04618`* | `0.02936`* | `0.2761` | **FAIL** (`100.0%` 3-px ov w/ `G30`) | **NO** — `H19-5 B=2` variant (`+6`d vs `G32`) |
| **GEMSDOE30** | `gems20-h20-5-d28-20261001-48215c27-zeros.tif` (`8cf893ea…` · `44,090`d) | `0.2600` | `0.16163` | `0.09674` | `0.2700` | **FAIL** (`100.0%` identical to `G25`) | **NO** — Exact footprint duplicate of `G25` |
| **GEMSDOE31** | `gems31-h31-collar-b1-20261004-zeros.tif` (`acd85393…` · `40,199`d) | `0.2708` | `0.04906`* | `0.03052`* | `0.2787` | **FAIL** (`100.0%` 3-px ov w/ `G30`) | **NO** — Intermediate `B=1` step |
| **GEMSDOE32** | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` (`c55bafc4…` · `37,654`d) | **`0.2778`** | `0.16163`† | `0.09920`† | **`0.2843`** | **FAIL** (`100.0%` subset of `G36`/`G25`) | **ACTIVE CHAMPION** (Already submitted; do not re-upload) |
| **GEMSDOE33** | `gems33-h33-variant-20261004-zeros.tif` (`87f857d5…` · `41,865`d) | `0.2632` | `0.08641`* | `0.05197`* | `0.2773` | **FAIL** (`99.7%` 3-px ov w/ `G27`) | **NO** — Superseded `H19-5` variant |
| **GEMSDOE36** | `gemsdoe36-h36-hybrid-38854-zeros.tif` (`e1589102…` · `38,854`d) | `0.2750` | `0.00693`* | `0.00458`* | `0.2826` | **FAIL** (`97.6%` superset of `G32`) | **NO** — `+1,200`d over `G32` hurt live DTI (`-0.0028`) |
| **KANLERGEMSDOE2 (`KG2-H1`)** | `kanlergemsdoe2-kg2h1-fvca-submod-20261026T235000Z-cab53e1b-zeros.tif` (`29128ad7…` · `38,500`d) | *Not submitted* | **`0.16928`** `[0.1554, 0.1834]` | **`0.10607`** (`EXP-3`: `0.10653`) | `0.0728`‡ | **PASS vs Focus-9** (`max 44.7%`; `33.4%` vs `G32`) · **STOP vs 72-Reg** (`80.7%` vs `G10-H25`) | **NO (`verdict = negative`)** — Research/audit artifact only; preserve weekly slot |

*\*Static rasters `G28, G31, G33, G36` pre-erased full-map `labels.tif` collars (`B=1..2`), censoring withheld catalogue segments when scored as static masks (`IR-32-INSTR-01`). †`GEMSDOE32` is evaluated via its exact leak-free fold-local reconstruction (`D2.8` with fold-local `d_visible > 2.0`; raw static `g32_champion.tif` scores `0.00671` / `0.00452`). ‡`LLI-S3` uses only `(d_catalogue, d_H19-5)` strata and systematically under-projects non-`H19-5` methods by `0.10–0.17` (`IR-KG2-LLI-BIAS-01`: projects `0.1319` for `10GEMSDOE H28` = `0.2336` live, and `0.0747` for `GEMSDOE70` LOQO whose family scored `0.2478` live).*

---

## 2. PhD Forensic Explanation: Why `GEMSDOE32` Achieved `0.2778` & How to Beat It

1. **Base Multi-Physics Ridge Network (`19GEMSDOE H19-5`, `121,131` px, `0.1922` live):** Fuses four physical conduits at a power-law scaling budget (`2.45%` of the footprint): (L1) elastic crack-tip & step-over stress wings off mapped fault terminations, (L2) DOE GDR #1391 hydrothermal upflow conduits (`27,092` wells/springs, `2,782` 2m temperature probes, `281` sinter/travertine/tufa deposits), (L3) USGS 3DEP 1m/10m topographic openness/LRM scarps, and (L4) GeoDAWN horizontal-gradient gravity/magnetic worms. Out-of-sample Live-Ledger Inversion (`LLI-S3`, 111 live-scored rasters, `LOO Spearman = 0.927`) shows `73–96%` of hidden public truth lies within `300 m` of `H19-5`.
2. **Poisson-Disk Dot Thinning (`0.1922 -> 0.2477 -> 0.2600`):** Under Distance-Tolerant IoU (`alpha = 0.2` FP weight, `beta = 0.8` FN weight, `300 m` linear kernel `K(d) = max(0, 1 - d/3)`), spacing binary dots at `s = 2.8 px` along a 1-px ridge retains `~77%` of line recall while cutting false-positive mass `2.75x` (`121,131 -> 44,090` dots, `GEMSDOE25/30`).
3. **Exact `B=2` Catalogue-Depletion Collar Pruning (`0.2600 -> 0.2708 -> 0.2778`):** Organizers mask `labels.tif` and did not re-digitize sub-200 m parallel offsets of existing catalogue traces as "new" faults (`0.01–0.07x` far-field truth density at `d_cat <= 2 px`). Deleting `3,891` `D2.8` dots at `d_cat <= 1 px` gave `0.2708` (`GEMSDOE31`, `40,199`d), and deleting `2,545` more at `1 < d_cat <= 2 px` (`6,436` total removed -> `37,654` dots, 0-XOR verified) produced `GEMSDOE32`'s **`0.2778`**.
4. **Why External Leaders Reach `0.3195` / `0.4413` (`0.4437` on 2026-10-26) & How to Surpass `0.2778`:**
   - Unweighted supervised classifiers on `y = labels.tif` (`10GEMSDOE H28` = `0.2336`, `GEMSDOE70 P8` = `0.2478`, and our `KG2-H1` = `80.7%` convergent with `G10-H25`) suffer **Positive-Unlabeled (PU) range-front bias**: exposed mountain-front scarps dominate `labels.tif`, starving blind alluvial-basin faults (`B15 > 250 m`) and LiDAR tile gaps.
   - Surpassing `0.2778` cleanly without copying `H19-5` requires: (a) **inverse-propensity PU weighting** `1 / P(labeled=1 | fault=1, slope, LiDAR_valid, depth_to_basement)` so our `FVCA` up-slope hydrothermal vent back-projection allocates dots into blind piedmont/basin conduits where `10GEMSDOE` and `H19-5` are sparse; (b) **continuous soft-amplitude Tversky emission** `p(x) in [0, 1]` calibrated to local TP/FP odds; and (c) **raw USGS 3DEP 1m/10m continuous DEM + Sentinel-1 InSAR velocity gradients (`KG2-H5`)** outside sandbox egress restrictions.

---

## 3. Controlled 3-Experiment Results (`KG2-H1: FVCA-SUBMOD`)

| Arm | Channels & Emitter | `SegmentHoldout v1` (`HOLDOUT-DTI`, `n=60,988`) | `HIDE-RECOVER v3.0` (`HOLDOUT-DTI`, `n=22,232`) | Key Finding |
| :--- | :--- | :---: | :---: | :--- |
| `BASE_E1_XGHGB` | 44 ch · 1-stage HistGB + 3-px disk (`37,654`d) | `0.153670` `[0.14092, 0.16721]` | `0.098439` `[0.08222, 0.11441]` | Prior `KANLERGEMSDOE2` baseline |
| `BASE_CHAMP_D28_VISB2` | `D2.8` + fold-local `d_visible > 2.0` (`37,654`d) | `0.161630` `[0.15118, 0.17209]` | `0.099202` `[0.08595, 0.11267]` | `0.2778` champion leak-free proxy |
| **`EXP-1`** | 44 ch (EDT-repaired + TIGER-LiDAR + `KG2-H3`) · 2-stage Auto-Context + 3-px disk (`38,500`d) | `0.158138` `[0.14453, 0.17166]` | `0.099228` `[0.08377, 0.11379]` | `+0.00447` over `E1` from border repair + road-cleared LiDAR + Auto-Context |
| **`EXP-2`** *(Selected)* | **60 ch (`+16` FVCA geothermal back-projection & Coulomb dilatancy)** · 3-px disk (`38,500`d) | **`0.169279`** `[0.15545, 0.18343]` | `0.106071` `[0.09002, 0.12150]` | **`+0.01114` jump from geothermal vent physics**; `4/4` fold wins vs `D2.8 vis-B2` |
| **`EXP-3`** | 60 ch (`FVCA`) · **Exact 300 m CELF submodular allocator** (`38,500`d) | `0.163360` `[0.14793, 0.17855]` | **`0.106529`** `[0.08940, 0.12324]` | Best on sparse 20%-withheld `HIDE-RECOVER-v3.0`; `-1,532` px `FP_w` |

---

## 4. Reproducible Commands

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 1. Restore & SHA-256-verify all 14 competition + external geothermal datasets (.cache/gems_data/)
bash scripts/download_competition_data.sh
.venv/bin/python scripts/prepare_data.py

# 2. Build 60-channel EDT-repaired FVCA feature stack & run 60-feature leakage canary
.venv/bin/python scripts/build_features.py
.venv/bin/python scripts/run_experiments.py

# 3. Validate GeoTIFF, run automated fail-closed selector, rebuild GitHub Pages, and run all unit tests
.venv/bin/python scripts/validate_raster.py docs/downloads/kanlergemsdoe2-kg2h1-fvca-submod-20261026T235000Z-cab53e1b-zeros.tif data/sample_submission.tif
.venv/bin/python scripts/build_site.py
.venv/bin/python scripts/select_submission.py
.venv/bin/python scripts/run_tests.py
```

---

## 5. Honest Limitations, Flagged Irregularities & Next Steps

1. **Supervised Scarp Convergence (`IR-KG2-SCARP-CONVERGENCE`):** While `KG2-H1` achieved `0.16928` on `SegmentHoldout` and `<44.8%` overlap across all 9 focus sites, training unweighted on `y = labels.tif` caused `80.68%` of emitted dots to fall within `300 m` of `10GEMSDOE`'s `174,232`-pixel supervised scarp halo (`gems10-h25-ctx-ridge`). **Next step:** Train an inverse-propensity-weighted blind-basin specialist (`B15 > 200 m` or low `B19` slope) where `FVCA` up-slope hydrothermal back-projection operates orthogonally to exposed range-front classifiers.
2. **Paired 95% Block-Bootstrap Width:** Across 10 km spatial blocks (`SegmentHoldout`), `EXP-2` beat `D2.8 vis-B2` in `4/4` folds (`+0.00765` pooled), but block-level spatial variance yields a `[-0.00503, +0.02052]` paired 95% CI.
3. **Band `B06` Metadata Mislabel (`IR-KG2-TC-MISLABEL`) & Perimeter Sentinels (`IR-KG2-BORDER-CLIFF`):** `B06` (`tc`) is GeoDAWN Radiometric Total Count (`Spearman = 0.99995`), not magnetic tilt curvature; `3,061` `-3.4e38` border sentinels were repaired via nearest-EDT interpolation in `scripts/build_features.py`.
4. **Sandbox Network Egress Block on `KG2-H5`:** NASA ASF Sentinel-1 InSAR (`search.asf.alaska.edu`) and raw USGS 3DEP DEM downloads (`apps.nationalmap.gov`) are outside this sandbox's outbound allowlist and remain queued for an unrestricted workstation.
5. **Historical Quarantine Integrity:** Prior PR #3 (`blindbasin-vent-gravity`, synthetic layers/placeholder gates) and PR #5 (`E1 XG-HGB`, `0.1252` quadrant OOF) remain archived in `research/quarantine/` with `prior_blindbasin_authorization = "withdrawn"`.

---

## 6. Standing Project Prompt & Operational Brief (Session Starting Point)

```text
Review our project at https://github.com/kanlerxz87-cyber/KANLERGEMSDOE2 for the DrivenData DOE GEMS
Geothermal Exploration Machine-learning Submission competition (https://www.drivendata.org/competitions/306/competition-doe-gems/).

Core Standing Requirements & Parallel-Run Protocol:
1. Focus on highest-scoring submissions across GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, and 36
   (champion 0.2778 on GEMSDOE32 h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros; leaderboard context 0.3195 / 0.4413 / 0.4437).
   Explain at a PhD level why GEMSDOE32 achieved 0.2778 and how a submission can score higher.
2. Build a clean GitHub Pages site (docs/) with an executive summary table for every focus site showing:
   file to download, properly labeled score/estimate, uniqueness vs all other GEMSDOE sites, and an
   unmistakable automated gate verdict on whether the generated TIF is OK to download and submit, plus
   an executive summary subpage explaining step-by-step how to submit on DrivenData (file + <=140-char note).
3. Generate a genuinely unique single-band float32 GeoTIFF submission (never copy or trivially perturb a
   prior submission), automatically validated for range [0, 1] ("Predicted values must be in range [0, 1]"),
   zero NaNs inside footprint (whole-grid-finite -zeros.tif), and exact sample_submission.tif CRS (EPSG:32611),
   shape (3730 x 3292), and geotransform.
4. Parallel-Run Protocol:
   - Rule 1: Stay inside one preregistered single-method lane. If |Spearman| > 0.90 or >70% of dots fall
     within 3 px of ANY registry raster (checked BOTH on continuous surface before placement AND on final dots),
     log as duplicate and stop. Never Perturb-to-Evade.
   - Rule 2: Reuse vendored template evaluators/writers (SegmentHoldout, novelty.py, submission.py). Hide whole
     fault segments with a buffer, derive catalogue features from visible faults only, mask visible faults
     pixel-exactly, and score pooled DTI (alpha=0.2, beta=0.8, 300 m triangular kernel). Fix upstream bugs once.
   - Rule 3: Label every number as HOLDOUT-DTI (evaluator version, withheld positives, 95% CI),
     ORGANIZER-CONFIRMED (backed by portal receipt), OWNER-REPORTED (unverified peer ledger), or PROJECTION
     (never write a projection as a score).
   - Rule 4: Single-feature leakage canary on every feature before trusting results (two-sided AUC <= 0.90).
   - Rule 5: Emit one canonical JSON Run Card (hypothesis, mechanism, named non-fault mimic, holdout DTI + CI,
     registry correlation/overlap, raster sha256, validator output, submission name + <=140-char note,
     verdict promote / negative). Negative results are valid deliverables; protect rolling 3/week slots.
   - Rule 6: Budget cap of at most 3 experiments or 2 hours per run; slot promotion is a separate selector step.
5. Verify everything autonomously from official free public sources with zero hallucinations; execute 3 passes
   (Pass 1: implement & verify; Pass 2: review & fix bugs/assumptions/edge cases; Pass 3: full re-check),
   follow Arena Core Values (Maximize P(Win) and Own the Outcome), and open & merge PR onto main.
```
