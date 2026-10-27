# Preregistered Hypotheses & Experimental Protocol — Session `KG2-S2 / DSLUP-3D` (`2026-10-27`)

**Status:** Frozen BEFORE running any holdout fit, allocation, or emission experiment in this session.
**Branch:** `arena/33f25930-kanlergemsdoe2`.
**Evaluators (shared, unchanged):** `gems32.holdout.evaluate_hide_and_recover` (`GEMSDOE32-HIDE-RECOVER-v3.0`) and
`gems32.holdout.evaluate_sgmc_with_ci` (`GEMSDOE32-SGMC-CAL-v3.0`), seed `20261026`, `alpha = 0.2`, `beta = 0.8`,
`300 m` triangular kernel, pixel-exact visible-fault masking, whole-segment withholding with `15 px` collar.
**Experiment budget:** Hard cap `<= 3` experiments, `<= 2` hours wall time (Protocol Rule 6).

---

## 1. Assigned Lane (single method paragraph — Protocol Rule 1)

> **Lane `KG2-S2` (`DSLUP-3D`):** *Depth-Scaled Listric Updip Continuation & Blind-Basin Dual-Population
> Reallocation.* We replace the uniform fixed-height (400 m) FFT upward-continuation updip gravity crest
> migration of the promoted `HTCADS-DualRegime (EXP-2)` lane with a **locally depth-to-basement-scaled,
> listric-dip 3-height (150 / 400 / 800 m) upward-continuation crest-migration projector** whose per-pixel
> updip horizontal offset is `s(z) = depth / tan(dip_eff(depth)) / 100 m`, `dip_eff` shallowing linearly from
> `62°` at the surface to `38°` at `>= 2.5 km` basement depth (listric normal-fault geometry, Basin & Range),
> weighted by **multi-height horizontal-gradient strike coherence** (`cos² Δstrike` between 150 m and 800 m
> continuation ridges) to suppress shallow alluvial noise; this DSLUP ridge replaces `grav_updip_proj`
> (channel 4) in BOTH the 27-channel sharp out-of-quadrant GBDT and the first-principles Multi-Physics
> Conduit pillar, and the final 300 m submodular CELF allocation is split into a **dual-population budget**
> that reserves an explicit tranche of dots for concealed-basin hydro-geothermal conduits
> (deep basement + outside 1 m LiDAR validity) before packing the remaining budget on the main surface with
> a 300 m exclusion around the basin tranche. Everything else (holdout, submission writer, noisy-OR tip/relay
> specialist, zero-mean ortho-LiDAR specialist, leakage canary) is reused unchanged from the template.

This lane executes the previous session's recorded roadmap item (3): *"extend uniform 400 m FFT upward
continuation to locally depth-scaled 3D listric fault continuation."*

**Duplicate-stop rule (Rule 1), tightened for this session:** the audit registry now contains **all 1,644
unique prediction rasters** inventoried across 114 GEMSDOE-family repositories (102 `buffedlizard55-lab`
GEMSDOE repos + `KANLERGEMSDOE1-3`, `EUGGEMSDOE1-3`, `WBGGEMSDOE1-3`, `GINNYGEMSDOE1-3`), **including this
repository's own three previously emitted rasters** (`11a2f251`, `f5a469e94b14`, `cab53e1b`). Gates:
max `|Spearman|` `< 0.90` on the pre-placement surface AND final dots; max directional 3-px dot overlap
`<= 0.70` against every competing detector **including our own prior submissions**. Any breach → log as
duplicate, verdict `negative`, stop.

---

## 2. Ranked Untried Hypotheses (`KG2-S2-H1` … `KG2-S2-H5`)

| Rank | ID | Hypothesis | Layers (exact) | Physical signature / transform | Why it catches faults MISSING from USGS/INGENIOUS | Differs from everything already implemented | Expected DTI gain / cost |
|---|---|---|---|---|---|---|---|
| 1 | `KG2-S2-H1` (**selected**) | **Depth-scaled listric updip continuation (DSLUP)** | `training_features.tif` band 13 (`iso_grav_anom`), band 15 (`depth_to_base_surf`); no labels, no SGMC | 3-height FFT upward continuation (150/400/800 m) of the isostatic gravity anomaly; crest-migration unit vector from the continuation-difference gradient; per-pixel **listric** updip offset `s = depth/tan(62°−24°·min(depth/2500,1))/100 px` clipped to `[1.5, 11] px`; Hessian ridge of the migrated horizontal-gradient field | Catalogue faults were mapped from *surface* scarps. Over deep (0.5–2.5 km) basin fill the gravity gradient crest sits 0.5–1.5 km basinward of the buried fault's sub-alluvial emergence line; a FIXED 400 m continuation (3.5 px shift, prior EXP-2) under-corrects exactly where faults are blind (deep basins need 5–11 px) and over-corrects on shallow piedmont. Depth scaling puts dots on the emergence line itself | Prior `HTCADS EXP-2` used one fixed height & constant 3.5 px shift; `GEMSDOE92 listricdip-updip50` (live 0.0255) shifted a *topographic* scarp surface up-slope by a constant, no potential fields, no continuation; nothing else in the 1,644-raster registry does depth-scaled continuation | +0.004…+0.012 HOLDOUT-DTI; low cost (3 FFTs) |
| 2 | `KG2-S2-H2` (**selected**) | **Blind-basin dual-population dot budget** | `depth_to_base_surf`, LiDAR validity mask, hydro-geothermal pillar channels 14–23 of the cached stack | Reserve a pre-registered tranche (`6,000` of `37,654` dots) for pixels with deep basement (top-40% basin depth) outside 1 m LiDAR coverage, scored by the hydrothermal/vent pillar gated on DSLUP structural ridges; remaining dots packed by ordinary CELF with 300 m exclusion around the tranche | The exact-ledger inversion (`R² = 0.9985`) proved scoring above the 0.278 H19-5 plateau REQUIRES new true positives off the scarp manifold; ~75% of Great Basin geothermal systems are blind (Faulds & Hinz 2015) and sit under exactly these pixels | No registry raster allocates an explicit concealed-basin tranche; prior own EXP-2 dots are 69.6% inside LiDAR coverage — this mechanically decorrelates the dot set from our own prior submission as well | +0.000…+0.008 HOLDOUT-DTI; low cost |
| 3 | `KG2-S2-H3` (**selected**) | **Multi-height strike-coherence gate** | continuation ridges at 150 m & 800 m | `w = 0.5 + 0.5·cos(2Δstrike)` between shallow and deep continuation ridge strikes; multiplies DSLUP ridge | Basement-rooted faults keep strike across continuation heights; alluvial channel edges / shallow noise do not — removes false positives in the very basins H2 targets | Untried in any prior lane here or in the audited registry | +0.001…+0.004; negligible cost |
| 4 | `KG2-S2-H4` | OPERA Sentinel-1 `DISP-S1` InSAR aquifer-compartment phase steps | NASA ASF DAAC (CC0) | Seasonal phase steps across buried fault seals | Sub-mm/yr slip faults invisible to all geodetic bands in the stack | **BLOCKED**: `asf.alaska.edu` outside sandbox outbound allowlist (`github.com`/`pypi.org` only) — documented, not viable this session | High / blocked |
| 5 | `KG2-S2-H5` | ASTER TIR silica sinter emissivity + SWIR argillic halo | NASA LP DAAC `AST_05`/`AST_07XT` (public domain) | Reststrahlen 8.3–9.1 µm emissivity minima over fossil sinter aprons | Fossil vents along unmapped conduits | **BLOCKED**: `lpdaac.usgs.gov` unreachable from sandbox — documented, not viable this session | Moderate–High / blocked |

## 3. Preregistered experiments (frozen)

- **EXP-A (`DSLUP-Core`)**: H1+H3 only. DSLUP channel replaces `grav_updip_proj` in GBDT + physics pillar; isotropic `B = 2.0` collar; single CELF; `37,654` dots.
- **EXP-B (`DSLUP-BlindBasin`)**: EXP-A + H2 dual-population allocation (`6,000` basin tranche + `31,654` main).
- **EXP-C (`DSLUP-AnisoTip`)**: EXP-B + axial strike-continuity smoothing + anisotropic tip-preserving (`d > 1.45 px`) / flank-depleting (`d > 2.15 px`) collar + Dinkelbach marginal bar `0.0020`.

**Controls & benchmarks:** fresh REF = `GEMSDOE32 B=2` champion proxy on the identical evaluator
(hide-recover uncensored + SGMC-CAL), plus the recorded prior promoted `HTCADS EXP-2` numbers
(`0.112353` / `0.078913`, same deterministic evaluator & seed, `evidence/htcads_experiments.json`).

**Promotion gate (automated, fail-closed, no human inspection):** format-valid `-zeros.tif`
(`EPSG:32611`, `3730 × 3292`, exact transform, float32, all `12,279,160` cells finite in `[0, 1]`, 0 NaN,
0 dots on `existing_faults == 1`), leakage canary pass, BOTH uniqueness gates vs all 1,644 + own rasters,
hide-recover HOLDOUT-DTI strictly above fresh REF with paired 95% CI lower bound `> 0`, AND SGMC-CAL above REF.
Preference among passing experiments: highest hide-recover HOLDOUT-DTI; tie-break lower overlap vs own `11a2f251`.
If NONE passes: verdict `negative`, keep prior promoted file as the only OK-to-submit artifact. Negative results
are deliverables.
