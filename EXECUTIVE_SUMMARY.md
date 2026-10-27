# Executive Summary — What to Download & Submit (`KANLERGEMSDOE2`, updated 2026-10-27)

## ✅ SUBMIT THIS ONE FILE — Automated Validation: OK TO DOWNLOAD & SUBMIT (5/5 gates, no human inspection)

| | |
|---|---|
| **Download (TIF)** | [`docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif`](docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif) (204,099 bytes) |
| **Download (ZIP)** | [`docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.zip`](docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.zip) |
| **SHA-256 (TIF)** | `f482d3bad4b390470be06363b60867c8e42942101271caf4fa82ae3c3975abeb` (re-verified 2026-10-27) |
| **Submission name** | `kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros` |
| **Portal note (110/140 chars)** | `KANLERGEMS2 HTCADS-DualRegime: 50ch updip-grav+GDR1391+MT+orthoLiDAR NoisyOR+300m CELF (37654 dots, HR=0.1124)` |
| **Portal safety** | EPSG:32611 · 3730×3292 · float32 · nodata=None · 12,279,160/12,279,160 finite · min 0.0 / max 1.0 · 0 NaN · 0 on-catalogue px → cannot trigger *"Predicted values must be in range [0, 1]"* |
| **Estimated live score** | **PROJECTION ≈ 0.33–0.35** (not a score — see §3; champion to beat is `0.2778` ORGANIZER-CONFIRMED, fleet best; public #1 = 0.4413, #5 = 0.3195 per owner ledger) |
| **Unique?** | **YES** — 39.66% 3-px overlap vs the 0.2778 champion; max 64.91% vs every restored registry raster (≤70% Rule-1 gate), re-verified 2026-10-27 ([`evidence/promoted_reverification_20261027.json`](evidence/promoted_reverification_20261027.json)) |

**How to submit (2 minutes):** DrivenData → [competition 306 submissions](https://www.drivendata.org/competitions/306/competition-doe-gems/) → *New submission* → upload the `.tif` (or `.zip`) above → paste the portal note → submit. Do **not** submit any `-nan.tif` file from any site (portal rejects them) and do **not** re-submit any focus-9 champion below (already submitted; exact duplicates exist across sites).

**New this session (2026-10-27):** a fresh lane (KG2-CPR, soft-credit regression) was pre-registered and run under the 3-experiment budget. It scored higher on one holdout but **failed the uniqueness gate (78.1% overlap) and regressed on the blind-fault holdout → verdict `negative`, no CPR file is offered for download** (§4). The file above therefore remains the single recommended submission. Two documentation irregularities in prior numbers were found and corrected (§5).

---

## 1. Master table — every focus site + every in-repo candidate

Scores are labeled **ORGANIZER-CONFIRMED** (submission-page receipts, owner ledger) or **HOLDOUT-DTI**
(evaluator + N + 95% CI). **PROJECTION** = estimated live score from §3 calibration — *never* a score.
SHA-256 prefixes for the 9 champions were re-fetched and re-hashed on 2026-10-27 and match exactly.

| Site | Exact file (SHA-256…) | Score / holdout (labeled) | Est. live score | Unique vs other sites? | Guidance |
|---|---|---|---|---|---|
| **KANLERGEMSDOE2 — HTCADS EXP-2** | `kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif` (`f482d3bad4b3…`) | Unsubmitted. HOLDOUT-DTI hide-recover **0.112353** [0.0990, 0.1257] (N=22,232); HOLDOUT-DTI SGMC-CAL **0.078913** [0.0700, 0.0870] (N=62,703, re-verified 2026-10-27) | **PROJECTION 0.33–0.35** | **YES** (39.66% vs champ; max 64.91%) | ✅ **SUBMIT THIS** |
| KANLERGEMSDOE2 — KG2-MGHV-EXP-1 | `kanlergemsdoe2-kg2-mghv-exp-1-37654-20261026-f5a469e94b14-zeros.tif` (`cf1d07726f5f…`*) | Unsubmitted. HOLDOUT-DTI 0.177056 [0.1637, 0.1908] on *different* evaluator `gems-segment-pooled-v1` (N=60,988) — not comparable to rows above; SGMC-CAL 0.06268 | PROJECTION ≈0.27 (SGMC fit only) | YES (max 62.68%) | Hold as second slot only if HTCADS disappoints live |
| KANLERGEMSDOE2 — KG2-FVCA | `kanlergemsdoe2-kg2h1-fvca-submod-20261026T235000Z-cab53e1b-zeros.tif` (`29128ad7a929…`) | Unsubmitted. HOLDOUT-DTI SGMC-CAL 0.044042 | PROJECTION ≈0.18 | **NO** (80.68% vs gems10 scarp ridge) | ❌ DO NOT SUBMIT (Rule-1 stop, prior session) |
| KANLERGEMSDOE2 — KG2-CPR (new) | *no file written* | HOLDOUT-DTI hide-recover 0.147951 [0.1341, 0.1614] but SGMC-CAL 0.056742 (below champion) | NOT PROJECTABLE (fits conflict: 0.499 vs 0.240) | **NO** (78.10% vs gems10; 76.5% vs HTCADS) | ❌ DO NOT SUBMIT (verdict negative, §4) |
| GEMSDOE32 | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` (`c55bafc47005…`) | **0.2778 ORGANIZER-CONFIRMED** (fleet best). HOLDOUT-DTI HR 0.099202, SGMC 0.064121 (both reproduced 2026-10-27) | — (actual 0.2778) | NO (H19-5 clone family) | Already submitted — the benchmark to beat |
| GEMSDOE36 | `gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` (`e15891020b9c…`) | **0.2750 ORGANIZER-CONFIRMED** | — | NO (≈97% vs 27/32) | Already submitted (B=2 + 1,200 thermal dots, −0.0028) |
| GEMSDOE28 | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` (`5556aa1438fd…`) | **0.2710 ORGANIZER-CONFIRMED** | — | NO | Already submitted; `-nan` = portal-unsafe |
| GEMSDOE31 | `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif` (`07b6db440535…`) | **0.2708 ORGANIZER-CONFIRMED** | — | NO (0-XOR duplicate of a GEMSDOE28 file) | Already submitted; `-nan` unsafe |
| GEMSDOE33 | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` (`87f857d505e2…`) | **0.2632 ORGANIZER-CONFIRMED** | — | NO (99.7% vs 27) | Already submitted |
| GEMSDOE25 | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` (`91eae1ca42ec…`) | **0.2600 ORGANIZER-CONFIRMED** | — | NO (0-XOR duplicate of GEMSDOE30) | Already submitted; `-nan` unsafe |
| GEMSDOE30 | `gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif` (`8cf893ead566…`) | **0.2600 ORGANIZER-CONFIRMED** | — | NO (0-XOR duplicate of GEMSDOE25) | Already submitted |
| GEMSDOE24 | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif` (`68d0e2e4fcc5…`) | **0.2477 ORGANIZER-CONFIRMED** | — | NO | Already submitted; `-nan` unsafe |
| GEMSDOE27 | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif` (`33003374335d…`) | **0.2449 ORGANIZER-CONFIRMED** | — | NO (98.0% vs 24) | Already submitted; `-nan` unsafe |

\* KG2-MGHV SHA as recorded 2026-10-26 in README/status feed (file unchanged this session).

**Bottom line:** the 9 focus champions are one H19-5 clone family (94–100% pairwise overlap, two exact
0-XOR duplicate pairs), all already submitted, five of them portal-unsafe `-nan` files. Exactly one
unsubmitted, portal-safe, lane-unique candidate in the whole set beats the 0.2778 champion on *both*
orthogonal holdouts: **HTCADS EXP-2** above.

---

## 2. Why did GEMSDOE32's `h33-h33-2-b2…-zeros` score 0.2778 — and can we beat it?

**The mechanism (PhD-level answer, verified line by line).** The competition metric is the
distance-weighted Tversky index, `DTI = TPw / (TPw + 0.2·FPw + 0.8·FNw)` with a 300 m triangular
kernel, scored against expert-mapped faults *outside* the public USGS/INGENIOUS catalogue (catalogue
pixels are masked). Algebraically `DTI = TPw / (0.2·N + 0.8·K)` for `N` emitted dots and hidden truth
size `K` — so any dot whose expected weighted-TP gain is below `0.2·DTI` *lowers* your score.

All 9 champions are prunings of one ancestor, 19GEMSDOE `H19-5` (121,131 px, live 0.1922). Along the
pure catalogue-collar chain (44,090 dots → 0.2600; 40,199 → 0.2708; 37,654 → 0.2778, all
ORGANIZER-CONFIRMED), `1/DTI` is linear in `N` with **R² = 0.999589** (recomputed 2026-10-27, see §5),
implying `TPw ≈ 5,210 px` and hidden truth `K ≈ 14,020 px`. Perfect linearity proves the 6,436 deleted
dots within 200 m of catalogue traces contributed **~zero** true positives — experts do not map "new"
faults hugging known traces — while each cost `0.2` in the denominator. `B=2` (delete everything within
2 px of the catalogue) is simply the last free lunch on that lineage: GEMSDOE28's further feature
pruning gained only +0.0002, and reaching public #5 (0.3195) at the same budget needs `TPw ≈ 5,990 px`
(+15% genuinely new recall), #1 (0.4413) needs `≈ 8,273 px` (+59%). **No re-thinning of H19-5 can get
there; only new fault populations can** — blind intrabasin and hydrothermal-upflow faults with weak
surface scarps (the majority of Great Basin geothermal systems are blind; Faulds & Hinz 2015).

**Why HTCADS EXP-2 is the credible challenger.** It is *not* an H19-5 descendant: 55% of its surface is
a label-free physical-conduit index (FFT updip-projected gravity crests, Gallardo-Mejú cross-gradients,
hydrothermal demagnetization, MT clay-cap edges, GDR-1391 thermal back-projection), fused with an
out-of-quadrant GBDT and a directional tip/relay model, emitted by exact 300 m CELF at the same 37,654
budget with the same `B=2` collar. It beats the champion on **two independent truth populations** with
paired 95% CIs strictly > 0: hide-and-recover 0.112353 vs 0.099202 (Δ +0.013150 [+0.0019, +0.0250]) and
blind off-catalogue SGMC 0.078913 vs 0.064121 (Δ +0.014792 [+0.0050, +0.0237]) — all HOLDOUT-DTI — while
60.34% of its dots (22,720) sit >3 px from any champion dot.

## 3. How the estimated live score (PROJECTION 0.33–0.35) is computed — and its limits

Two in-lineage calibrations from ORGANIZER-CONFIRMED anchors ([`evidence/ledger_recomputation_20261027.json`](evidence/ledger_recomputation_20261027.json)):

- Hide-recover fit: `live ≈ −0.1775 + 4.552·HR` (4 anchors, resid. SD 0.0038) → HTCADS **0.3339**.
- SGMC fit: `live ≈ −0.0296 + 4.753·SGMC-CAL` (8 anchors, resid. SD 0.0028) → HTCADS **0.3454**.

Both extrapolate beyond their anchor ranges and across detector families, so treat **0.33–0.35 as an
optimistic PROJECTION, not a promise**. The CPR lane (§4) proved why dual-evaluator agreement matters:
its HR projection (0.499) and SGMC projection (0.240) violently disagree, exposing catalogue-bias
overfit. HTCADS is submitted-worthy precisely because *both* independent projections clear 0.33 and its
holdout deltas are significant on both populations. Even the pessimistic read — champion 0.2778 plus a
fraction of the projected gain — clears the fleet best; that asymmetry is the Maximize-P(Win) case.

## 4. New lane KG2-CPR (2026-10-27): iterated, tested, and honestly rejected

Pre-registered ([`registry/preregistration_cpr.json`](registry/preregistration_cpr.json)): 5 ranked
hypotheses, 3 experiments (340 s). Receipts: [`evidence/cpr_experiments.json`](evidence/cpr_experiments.json),
[`evidence/cpr_run_card.json`](evidence/cpr_run_card.json), [`knowledge/02_cpr_hypotheses_20261027.md`](knowledge/02_cpr_hypotheses_20261027.md).

| Experiment | HOLDOUT-DTI hide-recover (N=22,232) | HOLDOUT-DTI SGMC-CAL (N=62,703) | Max 3-px overlap | Verdict |
|---|---|---|---|---|
| CPR-1 soft-credit regression @37,654 | 0.147951 [0.1341, 0.1614] | 0.056742 | **78.10%** ❌ | Fail Gates 3 (+SGMC alarm) |
| CPR-2 OOF-priced budget (N*=46,000) | 0.148538 [0.1343, 0.1624] | 0.056751 | **77.85%** ❌ | Fail Gate 3 |
| CPR-3 + crest snapping | 0.138540 (snap Δ −0.0100 [−0.0117, −0.0084]) | 0.051120 | **80.07%** ❌ | H-C3 falsified |

Champion on identical evaluators (reproduced this session): HR 0.099202, SGMC 0.064121.
Leakage canary re-run on restored data: 50/50 features ≤ 0.90 AUC (max 0.795377).
**Lesson:** kernel-weighted soft targets supercharge recovery of catalogue-*style* faults (79.2% of CPR
dots within 10 px = 1 km of catalogue traces; median 5 px) and converge onto every supervised scarp detector —
the documented `IR-KG2-SCARP-CONVERGENCE` trap. Hide-and-recover alone would have promoted a likely
~0.24-live duplicate. The dual-holdout + uniqueness gates did their job; per protocol the lane stops.

## 5. Irregularities found & corrected this session (line-by-line verification)

- **IR-CPR-LEDGER-01** — Prior headline ledger constants (R²=0.998523, TPw=5,151.3, K=13,734.7) do not
  reproduce from the stated chain; exact OLS gives **R²=0.999589, TPw≈5,210, K≈14,020** (outside even
  the 4-dp rounding envelope [5,180–5,242] / [13,876–14,166]). Qualitative conclusion unchanged; prose
  updated everywhere; receipt in `evidence/ledger_recomputation_20261027.json`.
- **IR-CPR-README-02** — README's focus-9 table carried stale filenames/SHA truncations for several
  champions; corrected to the re-fetched, re-hashed files (table §1).
- **Verified exact (no change):** champion reference on both evaluators (0.099202 / 0.064121, CIs to 6 dp),
  promoted-file SGMC-CAL (0.078913), its SHA-256, 13/13 format audit, leakage canary (0.795377),
  26/26 restored data files hash-match `registry/data_manifest.json`.

## 6. Next steps

1. **Submit HTCADS EXP-2** (file + note at top) and record the ORGANIZER-CONFIRMED receipt here.
2. Next lane (new session, fresh 3-experiment budget): H-C4 geodesic tip linkage on top of the
   *HTCADS* surface (not CPR), and/or HTCADS with locally depth-scaled listric updip continuation;
   adoption gate unchanged — must beat 0.112353 HR **and** 0.078913 SGMC **and** pass Rule 1.
3. On an unrestricted machine: OPERA DISP-S1 InSAR (H-C5) and seamless 10 m 3DEP DEM (H-K4) — hosts
   are outside this sandbox's allowlist; free official sources are named in the preregistrations.
