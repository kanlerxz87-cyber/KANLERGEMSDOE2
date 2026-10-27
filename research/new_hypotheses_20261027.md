# New geological hypotheses — 27 October 2026

Candidate hypotheses for improving DTI on the DOE GEMS Prize, ranked by expected DTI improvement vs implementation cost. Each names the specific layer(s), physical signature, why it catches catalogue-missing faults, the named non-fault mimic, and how it differs from prior implementations in this repo and across the GEMSDOE fleet.

## Hypothesis 1 — Off-catalogue blind-fault targeting (IMPLEMENTED — this session)

- **Layers:** USGS/INGENIOUS catalogue faults (labels.tif) + competition footprint only; no training features required.
- **Physical signature:** Euclidean distance transform from catalogue faults; dots placed >800 m from all mapped faults, targeting blind geothermal structures absent from the catalogue.
- **Why it catches catalogue-missing faults:** All high-scoring focus-site submissions (GEMSDOE24–33, 36) cluster dots ON or immediately adjacent to catalogue faults (the H19-5 dotted family). This targets the complementary territory — off-catalogue blind structures where undiscovered geothermal faults are most likely.
- **Named non-fault mimic:** Alluvial fans, paleochannels and survey-edge artefacts that lie off-catalogue but are not geothermal faults.
- **Differs from prior implementations:** First submission in this repo to place 100% of dots off-catalogue with a systematic grid + jitter design. All prior submissions are catalogue-adjacent dotted masks.
- **Expected DTI improvement:** Unknown (holdout not measurable without competition data). Rationale: leaderboard may reward off-catalogue precision (GEMSDOE32’s winner pruned 6,436 dots within 2 px of the catalogue).
- **Implementation cost:** Low (single script, no external data beyond labels.tif).
- **External data needed:** None beyond competition labels.tif (already restored).
- **Status:** IMPLEMENTED. File: `docs/downloads/36GEMSDOE-off-catalogue-blind-geothermal-targeting-20261027T234345Z-2ecaae7a056e-zeros.tif`. Validation: format pass, [0,1] pass, max competing overlap 22.37%, lattice overlap 66.00%. Verdict: promote per local gates; holdout unmeasured.

## Hypothesis 2 — Piedmont blind-basin depth-to-basement threshold (UNTESTED — needs DEM data)

- **Layers:** USGS 3DEP 10 m seamless DEM (bridging the 24.60% LiDAR void) + GDR 1391 2-m temperature probes.
- **Physical signature:** Depth-to-basement (Z_b) >= 150 m on piedmont alluvial cover, combined with shallow temperature anomalies. Blind faults beneath alluvium are invisible to surface mapping but generate conductive heat pathways.
- **Why it catches catalogue-missing faults:** Piedmont faults are buried under alluvial cover and absent from surface fault maps; geothermal systems leak through them. DARP-MT10’s C-PIED-v1.0 (0.1169) and EXP-2 (0.1407) show piedmont blind faults are a real signal.
- **Named non-fault mimic:** Basin-fill conductivity contrasts, paleochannel aquifers, near-surface clay lenses.
- **Differs from prior implementations:** DARP-MT10 used this for piedmont specifically but was fail-closed negative on full-catalogue HIDE-RECOVER. A dedicated piedmont-only submission would differ from the full-footprint dotted masks.
- **Expected DTI improvement:** High on piedmont subset (EXP-2 showed +39.1% vs 0.2778 champion on C-PIED), but unproven on full catalogue.
- **Implementation cost:** Medium (needs the 10 m DEM channels — ~147 MB total — plus temperature probe interpolation).
- **External data needed:** USGS 3DEP 10 m DEM (dem10_*.f32.npy in manifest) — freely available from USGS 3DEP; GDR 1391 2-m temperature probes (CC BY 4.0).
- **Status:** Not implemented. DARP-MT10 ran 3 experiments; verdict negative on full catalogue but positive on piedmont subset.

## Hypothesis 3 — Magnetotelluric phase tensor / tipper + listric basement projection (UNTESTED — DARP-MT10 explored)

- **Layers:** GeoDAWN airborne magnetic + radiometric (K, Th, U, TC) + USGS MT phase tensor / tipper + 10 m DEM.
- **Physical signature:** Listric basement projection (dip-adaptive) corroborated by 3D MT phase tensor tipper anomalies; blind detachment faults generate MT signatures invisible to surface mapping.
- **Why it catches catalogue-missing faults:** Listric/detachment faults root into basement and are not fully mapped at surface; MT phase tensor resolves subsurface conductivity structure.
- **Named non-fault mimic:** Conductive sedimentary basins, graphitic schist, clay alteration zones.
- **Differs from prior implementations:** DARP-MT10 tested 68 leakage-canaried features (max AUC 0.7965) with this combination. No GEMSDOE fleet submission uses MT phase tensor.
- **Expected DTI improvement:** DARP-EXP-2 reached 0.1407 on piedmont blind faults (#1 fleet-wide on that subset).
- **Implementation cost:** High (needs MT data, phase tensor computation, 3D inversion).
- **External data needed:** USGS MT data (GeoDAWN related), available from USGS ScienceBase / GDR.
- **Status:** DARP-MT10 lane completed (3 experiments, canary pass); verdict negative on full catalogue.

## Hypothesis 4 — Regional tectonic stress orientation vs fault strike (UNTESTED — contrarian)

- **Layers:** USGS Great Basin 10 km regional stress grid (S_hmin orientation, A_phi ratio) + catalogue faults + geothermal vents (GDR 1391).
- **Physical signature:** Faults optimally oriented for slip under the contemporary stress field (Andersonian theory) that are NOT in the catalogue. Geothermal fluids exploit critically stressed faults.
- **Why it catches catalogue-missing faults:** The catalogue maps surface traces; critically stressed blind faults may have little surface expression but control geothermal permeability. Stress-alignment filters out unfavorably oriented mapped faults.
- **Named non-fault mimic:** Paleostress fields (fossil), lithologic contacts parallel to stress, fold axes.
- **Differs from prior implementations:** No GEMSDOE fleet submission uses stress-orientation filtering. The manifest includes `gb_regional_stress_grid_10km.csv` but it was not used in any lane.
- **Expected DTI improvement:** Unknown; contrarian direction not yet tested.
- **Implementation cost:** Low-medium (CSV grid, vector math, no raster interpolation needed).
- **External data needed:** `gb_regional_stress_grid_10km.csv` (already in manifest, 47 KB) — derived from published Great Basin stress studies.
- **Status:** Not implemented. No external data blocking — manifest entry exists.

## Hypothesis 5 — Spring / well temperature anomaly proximal to blind structures (UNTESTED — contrarian)

- **Layers:** GDR 1391 "Well and Spring Temperature and Chemistry" (3,800 stations, 2,782 inside footprint) + catalogue faults + distance-to-vent.
- **Physical signature:** Elevated spring/well temperatures (>background + 2 sigma) located >500 m from any mapped fault — blind fault conduits bringing geothermal fluid to surface without mapped trace.
- **Why it catches catalogue-missing faults:** Geothermal springs often mark blind fault intersections; the catalogue only maps major Quaternary faults.
- **Named non-fault mimic:** Shallow aquifer warmth, cultural heat sources, near-surface volcanic heating unrelated to faults.
- **Differs from prior implementations:** The manifest includes `gdr_wellspring_in_footprint.csv` but its `dist_known_fault_px` column is label-derived and was explicitly excluded. No submission uses well/spring temperature as the primary targeting layer.
- **Expected DTI improvement:** Unknown; direct observation of geothermal surface expression is strong evidence but sparse (2,782 stations over ~123,000 km²).
- **Implementation cost:** Low (CSV interpolation to raster).
- **External data needed:** `gdr_wellspring_in_footprint.csv` (already in manifest, 2.1 MB, CC BY 4.0).
- **Status:** Not implemented.

## Ranking by expected DTI improvement vs cost

| Rank | Hypothesis | Expected DTI gain | Cost | External data needed | Viable this session? |
|------|-----------|-------------------|------|---------------------|---------------------|
| 1 | H1 Off-catalogue blind-fault targeting | Unknown (implemented) | Low | None | YES — implemented |
| 2 | H4 Stress orientation vs fault strike | Unknown | Low | `gb_regional_stress_grid_10km.csv` (manifest) | YES |
| 3 | H5 Spring/well temperature proximal anomaly | Unknown | Low | `gdr_wellspring_in_footprint.csv` (manifest) | YES |
| 4 | H2 Piedmont depth-to-basement >=150m | High on piedmont subset | Medium | 10 m DEM channels (~147 MB) | NO — needs DEM |
| 5 | H3 MT phase tensor + listric basement | High on piedmont subset | High | MT data (USGS ScienceBase) | NO — needs MT |

## Recommendation

Proceed with H1 (implemented, unique, validated for format and uniqueness). For the next session, test H4 and H5 — both use manifest data already available, both are contrarian (no fleet submission uses them), and both have low implementation cost. Run single-feature leakage canaries first (AUC > 0.90 = leakage) before any holdout scoring.
