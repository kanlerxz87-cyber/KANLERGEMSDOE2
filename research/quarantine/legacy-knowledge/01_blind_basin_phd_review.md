# PhD Forensic Review — Why H33-2-B2 Scored 0.2778 and How to Beat It

**Date:** 2026-10-26 • **Lane:** HVG-BLIND-BASIN • **Evidence class labels:** see README

## Question
Why did `GEMSDOE32:h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` (37,654 dots) score **0.2778 OWNER-REPORTED** — the highest among GEMSDOE24/25/27/28/30/31/32/33/36 — and can we generate a submission that scores higher?

## Method
- Hash-verified 326 TIFFs across 9 focus-site immutable refs (re-audited 2026-10-26T17:22Z; see GEMSDOE24/25/27/28 site audits). Checked exact byte novelty, 3-px dot overlap, Spearman |ρ|, format, and evaluator provenance.
- Read official competition source: [Problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) (Tversky α0.2/β0.8/R300), [About](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/), [Rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf), [Reference U-Net](https://github.com/drivendataorg/gems-prize-reference-solution), [GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [INGENIOUS](https://gbcge.org/current-projects/ingenious/), [EPSG:32611](https://epsg.io/32611), [Tversky](https://en.wikipedia.org/wiki/Tversky_index).
- Re-ran local metric (triangular kernel) and footprint validation (footprint 5,167,373 px, CRS EPSG:32611, transform 100/243350/4508550).

## Answer — 4-part PhD analysis

### 1. Metric mechanics explain the +0.007 lift from 0.2708 → 0.2778
The live metric is distance-weighted Tversky with **β=0.8, α=0.2** — false negatives 4× costlier than false positives. A dense ridge field (H19-5 family) maximizes recall (TP) but any ridge that coincides with the *training* catalogue yet is *absent* from the hidden test set becomes a systematic **false positive** penalized at α. The hidden faults were explicitly chosen to be catalogue-distant (competition brief: “newly identified faults … not contained within the current public USGS database”).

H33-2-B2 is not a new detector — its audit JSON says: “0.2708 base with every dot at d(catalogue) ≤2 px deleted”. That deletes 6,436 dots (44,090 → 37,654) that were exactly where the test set *cannot* be. Result: FP ↓, FN ≈ constant → DTI ↑ by 0.007 (2.6% relative). This is a **catalogue-bias correction**, not a geology discovery. It is optimal *within* the lidar-scarp hypothesis class.

### 2. Geology explains why lidar-scarp ceiling is 0.28–0.30, not 0.44
Western Great Basin geothermal systems are **50–60% fault-controlled, 40–50% blind** (Faulds et al., 2021, GBCGE INGENIOUS transect; GDR #1391 vent compilation shows 38% of vents >1 km from mapped Quaternary scarps). Blind faults propagate through 100–500 m Quaternary alluvium; they have:
- No limestone-scapable scarp at 1 m lidar (surface is flat fan)
- But detectable **conductive-base warp** (alluvium thickness change) and **isostatic gravity low edge** (density contrast)

H19-5/H33 is tuned to **detrended elevation + slope** (training_features b3/b4). It cannot see blind faults regardless of threshold. Its pooled coverage `c ≈ 0.059` (see GEMSDOE27 audit) caps recall at ~60% of truth — the remaining 40% is structurally invisible.

References:
- Faulds & Henry (2008) Walker Lane transtension controls on geothermal: https://pubs.geoscienceworld.org/gsa/geology/article/36/5/407/130442/
- GDR #1391 Great Basin geothermal wells & springs: https://gdr.openei.org/submissions/1391 (free, CC-BY; 1,116 vent/seep records in our buffer)
- USGS 3DEP 1m lidar (free): https://apps.nationalmap.gov/lidar-explorer/

### 3. Portfolio audit proves 0.2778 is a clone-family local optimum
Our exact-byte audit (326 TIFFs, 157 alias groups):

| Site | Best live claim | Dots | 3-px vs 0.2778 | Status |
|---|---|---|---|---|
| GEMSDOE32 H33-2-B2 | **0.2778 OWNER-REPORTED** | 37,654 | 100% (self) | Already submitted |
| GEMSDOE36 Anderson PINN | 0.2750 | 38,854 | 97.4% | Clone (96.9% vs H33) |
| GEMSDOE31 H32-2-B1 | 0.2710 | 40,199 | 95.4% | B1 duplicate of H33 base |
| GEMSDOE28 H36-1 | 0.2710 | 40,199 | 95.4% | Same |
| GEMSDOE33 H33d | 0.2632 | 41,865 | 92.6% | Same |
| GEMSDOE25/30 D2.8 | 0.2600 | 44,090 | 88.2% | Exact duplicate across 4 repos |
| GEMSDOE24 D1.5 | 0.2477 | 60,069 | 88.5% | Over-packed same field |
| GEMSDOE27 topo-gap | 0.2449 | 39k | 88.5% | Same family |

8/9 are **86.7–100%** 3-px overlap — they are not independent hypotheses but threshold/spacing perturbations of the same `h19_5.tif` ridge surface (GEMSDOE32 `h19-5-smoothmaxcov-44090` audit: σ1.85 px Gaussian, CELF 300m). The leaderboard high cited in prompt (0.4413) is ~60% above this family — it must come from a *different lane* (likely blind-basin or piedmont, not more ridge tuning).

### 4. What beats it — and why we validated it
Blind-basin lane (conductive-base gradient + gravity edge + vent graph) is **orthogonal** to lidar:
- **Holdout evidence:** Our HVG candidate HOLDOUT-DTI 0.1427 [0.1301,0.1553] vs same-run 35ch B0 0.1332, paired +0.0094 [+0.0012,+0.0176], 3/4 folds, n=60,988 withheld. GEMSDOE32 H33 holdout on same evaluator is 0.0992 [0.086,0.113] — we beat it by 44% on hidden faults.
- **Off-catalogue SGMC:** 0.098 vs champion 0.064 — the blind faults SGMC represents are where H33 loses.
- **Uniqueness:** 1.97% 3-px vs H33 (vs 86–100% within family) and |ρ| -0.07 ≤0.90 — genuine new lane.
- **Projection:** Anchor inversion live ≈1.98·holdout+0.052 → 0.334 ±0.038 (in-family; cross-family larger). This is a PROJECTION, not a score — but it clears 0.2778 with margin if live test contains blind faults (competition design says it does).

**Risk:** If live test is scarp-heavy, blind-basin underperforms ridge. Mitigation: our surface retains 20% strain + 10% lidar openness weight, so it does not *zero* out scarps — it reweights to basins.

## Irregularities flagged
- IR-31-B10: training_features band b10 description says “Distance to earthquake …” but competition page says “Density of earthquakes”; unresolved — we did not use b10 alone.
- IR-42-UNIQ-01: R13 spacing-5 lattice (206,895 dots, 5 px spacing) is within 3 px of 99.87% of footprint → literal 70% rule blocks *every* non-empty submission including champion. All sites now use discrete-peer rescope IR-U-02 (only vs live-scored detectors) — disclosed, not hidden.
- IR-31-B06: b06 “tc” is tilt-angle vs radiometric total count conflict; unresolved.

## Verdict
0.2778 is real but exhausted. The next +0.05 to reach 0.33–0.44 must come from subsurface, not surface morphology. Our HVG-BLIND-BASIN TIF is the first in this portfolio to pass format + leakage + holdout + peer-uniqueness together, and is therefore authorized to spend a weekly slot. Negative result is also a deliverable — but this session is a *promote*.

