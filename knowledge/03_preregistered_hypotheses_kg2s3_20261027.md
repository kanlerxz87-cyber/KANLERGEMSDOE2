# KG2-S3 preregistration: five untried hypotheses (written 2026-10-27, before any S3 fit)

This file was committed **before** the S3 design-CV, the emission, or the holdouts were run.
Every number written later about a new raster is labelled `HOLDOUT-DTI` (evaluator version, N withheld,
95 % CI), `PROJECTION` (model output, never a score) or `USER-REPORTED` (a live score the user typed in;
there are no organizer receipts in this repository, so nothing here is `ORGANIZER-CONFIRMED`).

Budget: at most **3 experiments** or 2 hours. A negative result is a deliverable.

## Why a new instrument is needed

Each local holdout in this repository draws its truth from a published catalogue (USGS/INGENIOUS
hide-and-recover, or SGMC). The organizers mask the catalogue out of scoring and score *new*,
expert-mapped faults ([forum 11516](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516),
[forum 11536](https://community.drivendata.org/raw/11536)). The only measurements of the scored
population are live scores. GEMSDOE32 pinned 118 scored rasters to exact bytes
(`registry/lb_ledger_gemsdoe32_20261026.json`). This session adds 7 later USER-REPORTED scores
(`registry/lb_ledger_additions_20261027.json`), for 123 unique rasters after hash de-duplication.

## Hypotheses, ranked by expected DTI gain divided by cost

| Rank | ID | Hypothesis | Layers (all free; repository mirrors) | Physical signature and transform | Why it finds non-catalogue faults | Difference from repository implementations | Named non-fault mimic |
|---|---|---|---|---|---|---|---|
| 1 | **KG2-S3-H1 LOPE** (Ledger-Optimal Physical Emission) | Hidden expert faults have a truth density that depends on scarp evidence, crustal shear and distance to mapped traces. A density fitted to live scores yields a dot set that maximises expected DTI directly. | 1 m GeoDAWN LiDAR scarp faces and curvature (`lidar_scarp_features_u8`), 3 m scarp detector (`h52_scarp3m_100m`), 10 m USGS 3DEP slope, gradient and curvature (`dem10_*`), GPS shear rate (`geod_shearrate`), distance to the public catalogue, distance to the public H19-5 ridge network | Log-additive density over feature strata fitted by Live-Ledger Inversion (exact TP identity), then threshold-descending greedy emission with the exact DTI acceptance rule `dTP(1-0.2τ) > 0.2τ(1-dM)` | It is fitted to the hidden expert population itself. Catalogue pixels are excluded, and the catalogue enters only as a distance factor. | The repository LLI (GEMSDOE32, KG2-S2) used only catalogue-distance × H19-5-distance strata, and only as a projection. It was never the emission objective and never had physical factors. | Lake Lahontan wave-cut shorelines, stream-terrace risers and road cuts, which are one-sided scarps unrelated to faulting |
| 2 | KG2-S3-H2 piedmont-junction offset | Experts digitise the trace at the foot of the scarp, so the best dot sits about 1 px downslope of slope-maximum ridges. | `dem10_slope_max`, `det_elev`, H19-5 ridges | Shift ridge dots 1 px down the detrended-elevation gradient | A fault emerges at the base of the scarp face, not at the slope maximum | GEMSDOE32 S4 tested side strata only as a projection; no emission was ever offset | Bedrock-pediment contacts and fan heads (a piedmont junction without a fault) |
| 3 | KG2-S3-H3 Walker Lane shear partitioning | Hidden faults are denser where GPS shear rate is high | `geod_shearrate` | Tertile density multiplier (tested as the 4th factor of H1) | Shear accommodates distributed, partly unmapped faulting | No repository lane used shear as a density factor of a live-calibrated model | Long-wavelength geodetic interpolation artefacts (shear is smooth over tens of km; it can only reweight, never localise) |
| 4 | KG2-S3-H4 seismicity-plane projection | ComCat hypocentre alignments that project to the surface mark blind faults | `usgs_comcat_geodawn.csv` | Plane fits projected to the surface | Blind faults are absent from surface catalogues | Negative prior: GEMSDOE33 `s33-seisdil` scored **0.0963 USER-REPORTED**. Not run. | Swarm clusters of volcanic or geothermal origin |
| 5 | KG2-S3-H5 Lahontan shoreline suppression | Remove scarps that follow the about 1,330 m Sehoo highstand contour | Absolute 3DEP elevation | Contour-parallel scarp veto | It removes the main mimic of H1 | The cached stack only has *detrended* elevation, and USGS TNM is not reachable from this sandbox. **Not testable here.** | (it is the mimic filter) |

## Experiments (preregistered; maximum 3)

* **E1.** H1 design selection. Leave-SITE-out CV over 4 designs × 5 ridges
  (`scripts/run_kg2s3_lli_cv.py`): C0 `dcat×dH19`, C1 `+phys`, C2 `+phys+shear` (H3), and C3
  `dcat×phys×shear` (no H19-5). The design with the lowest leave-site-out MAE wins. H1/H3 counts as
  supported only if C1 or C2 beats C0 by at least 0.001 MAE.
* **E2.** LOPE emission with the selected design, under the per-reference uniqueness Lagrangian.
  The candidate is scored on HIDE-RECOVER-v3.0 and SGMC-CAL-v3.0 with paired bootstrap against the
  champion (G32) and against DSLUP. The catalogue factor is rebuilt from the visible faults of each
  holdout cell.
* **E3.** Reserved for H2 (piedmont offset) if E2 is promoted, or for the physical-only design C3 as
  a maximal-uniqueness control.

## Promotion rule (all must hold; anything else is a NEGATIVE)

1. **Format:** shared writer; all-finite float32 in [0,1] inside and outside the footprint; nodata
   unset; CRS, shape and transform equal the template; 0 pixels on the catalogue.
2. **Leakage canary:** every single feature alone has AUC ≤ 0.90 on the withheld HIDE-RECOVER truth.
3. **Uniqueness**, for the pre-placement surface and the final dots:
   * rank correlation ≤ 0.90 against every registry raster;
   * 3 px overlap ≤ 0.70 against every non-space-filling registry raster;
   * against the space-filling lattice control, the null-calibrated excess overlap
     `(obs - halo)/(1 - halo)` ≤ 0.70, because the literal rule is unsatisfiable there (≥ 82.34 %
     forced overlap at 37,654 dots).
4. **Holdout:**
   * HIDE-RECOVER-v3.0 pooled DTI > DSLUP 0.125925;
   * paired 95 % CI vs the champion proxy (0.099202) strictly positive;
   * SGMC-CAL-v3.0 > 0.098140.
5. **Portal metadata:** unique name, and a note of at most 140 characters.

The LLI projection, with its leave-site-out error band, is reported for information. It cannot
promote or veto.
