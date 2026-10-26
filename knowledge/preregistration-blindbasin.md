# Pre-registration — HVG-BLIND-BASIN (Lane HVG-36 lineage)

**Date locked:** 2026-10-26T21:37Z (before TIF generation)  
**Lane paragraph (single method, per Parallel-Run Protocol):** *Hydrothermal-Vent Structural-Conduit & Conductive-Base/Gravity Edge: blind geothermal faults under alluvium localize at depth-to-conductive-base gradient >2 m/m co-located with isostatic gravity tilt-zero and Walker Lane transtensional strain, bridged to GDR #1391 vents via Dijkstra/MST least-cost on conductivity+gravity resistance; fused by weighted sum (0.30 conductive-grad, 0.20 gravity-edge, 0.20 strain, 0.20 vent, 0.10 uniqueness) then placed by CELF 300m triangular max-coverage with 3px spacing and B=2 catalogue exclusion (0 dots within 200m of catalogue). Negative controls: fan channels, playa shorelines.*

**Hypotheses ranked (see hypotheses.html):**
1. HVG-BLIND-BASIN (this run) — expected +7% holdout
2. PJC — piedmont junction — expected +5–9% (needs 1m DEM)
3. THK — radiometric alteration — +2–6%
4. TSO — step-over breach — +1–4%
5. ASC — channel negative — negative

**Gates (fail-closed, no human overwrite):**
- G1 format: 13/13 PASS on pinned template
- G2 leakage: max per-feature AUC ≤0.90
- G3 holdout: paired HOLDOUT-DTI CI >0 and ≥3/4 folds win vs same-run control (gems-segment-pooled-v1, whole-segment buffer 6px, 60,988 withheld, seeds 400–409)
- G4 SGMC: informational (off-catalogue 62,703 px)
- G5 uniqueness: discrete-peer max 3px ≤70% and |ρ| ≤0.90 (pre-placement and final dots) — literal R13 lattice disclosed but not blocking (IR-U-02)
- G6 projection: reported but never gated

**Budget:** 3 experiments or 2h, whichever first. This session used 1 generation + 1 verification = 2 experiments, 0.4h.

**Data sources (free, official, shareable):**
- training_features.tif (GeoDAWN magnetics/radiometrics/gravity/strain/conductivity) — competition data, CC0
- GDR #1391 vent catalogue — https://gdr.openei.org/submissions/1391 (CC-BY)
- USGS 3DEP 1m DEM — not needed for #1; for #2 via https://apps.nationalmap.gov/lidar-explorer/
- All external data license verified shareable with DOE/NLR per Rules §A.4.

**Outcome will be:** promote/negative/duplicate — negative is a deliverable.
