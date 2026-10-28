# Preregistered Hypotheses & Experimental Protocol — Session `KG2-S3 / GMV` (`2026-10-27`)

**Status:** Frozen BEFORE running any holdout fit, allocation, or emission experiment in this session.
**Branch:** `arena/e896cd9a-kanlergemsdoe2`.
**Evaluators (shared, unchanged):** `gems32.holdout.evaluate_hide_and_recover` (`GEMSDOE32-HIDE-RECOVER-v3.0`) and
`gems32.holdout.evaluate_sgmc_with_ci` (`GEMSDOE32-SGMC-CAL-v3.0`), seed `20261026`, `alpha = 0.2`, `beta = 0.8`,
`300 m` triangular kernel, pixel-exact visible-fault masking, whole-segment withholding with `15 px` collar.
**Experiment budget:** Hard cap `<= 3` experiments, `<= 2` hours wall time (Protocol Rule 6).

---

## 1. Assigned Lane (single method paragraph — Protocol Rule 1)

> **Lane `KG2-S3` (`GMV`):** *Range-front tectonic-Geomorphology + fossil-vent alignMent + dual-tranche Validation-gated
> allocation.* We append a label-free tectonic-geomorphology suite computed ONLY from detrended elevation, slope and
> potential-field horizontal gradients — segment-scale mountain-front sinuosity `Smf` on skeletonized range-front scarps
> (straighter fronts score higher), valley-scale floor-width-to-height ratio `Vf` on D8-routed valleys (narrow deep
> valleys score higher), block-scale tilt-coherence (an asymmetric-uplift-family measure over 2–5 km windows), and
> multi-scale TPI-break discordance `|TPI300 − TPI1200|` ridges — plus fossil-vent alignment corridors from WEIGHTED
> RANSAC line fitting through GDR paleo-sinter/travertine/tufa vents, warm wellspring geothermometer highs and
> depth-filtered ComCat epicenters (±300 m corridors scored by collinearity support × gravity/magnetic step coincidence,
> TIGER-road deconfounded). Both families enter the SAME out-of-quadrant LightGBM + Multi-Physics Conduit Noisy-OR +
> exact 300 m submodular CELF pipeline as the template, with an explicit 6,000-dot vent-corridor tranche ahead of the
> main pack. Everything else (holdout, submission writer, leakage canary, tip/relay specialist, zero-mean ortho-LiDAR
> specialist) is reused unchanged from the template.

**Duplicate-stop rule (Rule 1):** max `|Spearman|` `<= 0.90` on the pre-placement surface AND final dots; max directional
3-px dot overlap `<= 0.70` against every competing detector raster **including our own prior submissions** (`11a2f251`,
`f5a469e94b14`, `cab53e1b`, `c71122d5`, `cecbdca7`, `4ad35e71`). Dense structure-blanket probes (`cov3 > 0.30`,
IR-KG2S2-REG-DENSE-01) are logged as probes with harmonic overlap reported; the literal all-registry reading is ALSO
computed and disclosed because the calibration lattice provably forces `>= 82.34%` at this budget
(`evidence/release_audit_20261027.json`). Any detector breach → log as duplicate, verdict `negative`, stop.

---

## 2. Ranked Untried Hypotheses (`KG2-S3-H1` … `KG2-S3-H5`)

| Rank | ID | Hypothesis | Layers (exact) | Physical signature / transform | Why it catches faults MISSING from USGS/INGENIOUS | Differs from everything already implemented | Expected DTI gain / cost |
|---|---|---|---|---|---|---|---|
| 1 | `KG2-S3-H1` (**selected**) | **Range-front tectonic-geomorphology suite (Smf/Vf/tilt/TPI-discordance)** | `training_features.tif` bands 12 (`det_elev`), 19 (`det_elev_slope`), 18 (`iso_grav_anom_hg`), 3 (`tmi_hg`), 13 (`iso_grav_anom`), 2 (`rtp`); LiDAR validity mask only | Segment-scale mountain-front sinuosity `Smf = L_seg/L_straight` on skeletonized high-slope fronts (score `1/Smf`); valley-scale `Vf = floor_width/(divide_h − floor_h)` on D8-routed valleys; 2–5 km block tilt-coherence (asymmetric-uplift family); Hessian ridge of `|TPI300−TPI1200|`; all Noisy-OR gated on gravity/magnetic HG steps | The catalogue maps *preserved scarps*. Active range-front faults buried under fans lose scarp relief but keep straight fronts (low Smf), incised valleys (low Vf) and tilted blocks — tectonic activity indices respond to ongoing uplift, not scarp preservation | Template stack has only PIXEL-scale `piedmont_break_s1/s3`, `piedmont_apron_zone`, raw `tpi_300m/1200m`. No segment-scale Smf, no valley-scale Vf, no basin/tilt measure exists in this repo; no focus-site lane computes them (verified against `registry/focus_sites_20261027.json` method notes) | +0.004…+0.012 HOLDOUT-DTI; medium cost (D8 routing + skeletons, CPU-only) |
| 2 | `KG2-S3-H2` (**selected**) | **Fossil-vent + warm-spring + ComCat RANSAC alignment corridors** | `paleo_geothermal_regional.zip` (sinter/travertine/tufa), `gdr_wellspring_in_footprint.csv` (warm subset), `gdr_volcanic_vents_in_footprint.csv`, `usgs_comcat_geodawn.csv` (in-valid, depth ≤ 12 km), bands 18/3/11/9, `tiger_road_distance_m.tif` | Weighted RANSAC line fitting (sinter 2.5 / volcanic 1.5 / warm-spring-by-geotherm / ComCat-by-magnitude); keep lines with ≥3 supporters; ±300 m corridors scored by support × line-length × HG-step coincidence × road-clearance | Fossil vents mark conduits with ZERO surface scarp; single-vent buffers (template) cannot see the feeding STRUCTURE — multi-vent collinearity reveals it. ~75% of Great Basin systems are blind (Faulds & Hinz 2015) | Template blurs vent points (`gdr_sinter_vent_strike` = Gaussian σ=7 px point field) and back-projects plumes upslope; NO lane in this repo or the 9 focus sites fits lines through vents/springs/quakes | +0.002…+0.009 HOLDOUT-DTI; low cost |
| 3 | `KG2-S3-H3` (deferred) | **Fault-bounded playa-margin lineaments** | bands 17 (`cond_surf`), 12, 19, 18, 13 | Playa polygons from conductivity+elevation+slope; margin curvature maxima gated on gravity HG; contour-parallel (shoreline) margins suppressed | Basin-bounding faults hide under playa fill; playa EDGES are the fault trace | `KG2-MGHV` SUPPRESSED playas as mimics; inversion as targets is untried | +0.001…+0.006; low cost; deferred (budget) |
| 4 | `KG2-S3-H4` (deferred) | **Multi-density Bouguer stability ridges** | bands 13 (`iso_grav_anom`), 12 (`det_elev`) | Bouguer anomaly at slab densities 2000/2400/2670 kg/m³; HG ridges stable across all three | Basement steps persist across density assumptions; fill artifacts do not | Untried in repo and focus sites | +0.001…+0.005; low cost; deferred (budget) |
| 5 | `KG2-S3-H5` (deferred) | **QFaults slip-rate-weighted tip continuation** | `gdr_qfaults_traces.csv` + visible-only masking | Slip-rate-weighted tip cones along QFault strike; MUST be recomputed per visible fold | Continuations beyond mapped tips | GEMSDOE33 analog geometry is unweighted; weighting + visible-only discipline untried | +0.002…+0.007 but ELEVATED leakage/registry-collision risk → deferred pending visible-only audit |

**Named non-fault mimics & controls.** Lithologic fronts and faceted spurs (H1: require HG-step coincidence + contour
discordance); Lahontan shorelines (H1/H2: suppress contour-parallel energy, reuse `lidar_contour_ortho` discipline);
paleo-drainage-aligned deposits and road-following springs (H2: E–W/strike prior + TIGER clearance
`1−0.65·exp(−d/150 m)`); mine-blast clusters (H2: depth ≤ 12 km + HG coincidence); climatic playas (H3: slope/conductivity
check). `dist_known_fault_px` columns in GDR CSVs are FORBIDDEN (catalogue leakage) — same as FVCA.

**External-data obtainability (all verified this session, SHA-pinned owner mirrors of free official sources):**
paleo zip `84008 B`, wellspring `2146771 B`, volcanic vents `672 B`, ComCat `600662 B`, TIGER roads `10492276 B`,
2 m probes `1080530 B`, heat flow `909294 B` — all restored to `/tmp/gems_data/external/`. OPERA InSAR and ASTER remain
sandbox-blocked (prior sessions) and are NOT proposed.

## 3. Preregistered experiments (frozen)

- **EXP-A (`GMV-Geomorph`)**: H1 only. 4 new H1 channels replace nothing; appended to the sharp-column GBDT + physics
  pillar Noisy-OR; single CELF; `37,654` dots; `B = 2.0` visible collar.
- **EXP-B (`GMV-GeomorphVent`)**: EXP-A + H2 corridors + dual-population allocation (`6,000` vent-corridor tranche +
  `31,654` main with 300 m exclusion around the tranche).
- **EXP-C (`GMV-AnisoAlloc`)**: EXP-B + axial strike-continuity smoothing + anisotropic tip-preserving/flank-depleting
  collar + Dinkelbach marginal bar `0.0020` (allocation ablation only; no new features).

**Controls:** fresh champion-proxy REF = focus `GEMSDOE32` file evaluated on the identical evaluator
(`docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`, SHA
`c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`), plus recorded DSLUP unique-slot
(`0.125925` / `0.098140`) and HTCADS EXP-2 (`0.112353` / `0.078913`) receipts as same-evaluator context.
Promotion requires: canary PASS, detector-uniqueness PASS (both surface and dots), and paired 95% CI strictly positive
vs champion proxy on BOTH evaluators; the literal-lattice reading is disclosed either way.
