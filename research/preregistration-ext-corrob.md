# Pre-registration — Lane KANLER-EXT-CORROB (2026-10-26, written BEFORE experiments)

Session lane (single method paragraph, per parallel-run protocol): **label-free
multi-physics corroboration and multi-catalogue supervision on the restored
47-channel stack, emitted as spacing>=3 px binary dots outside a B=2 catalogue
gate, with emission budget selected on holdout.** Stay inside this lane.
Duplicate stop rule: surface Spearman |rho| > 0.90 OR > 70% of dots within 3 px
of ANY registry raster (9 focus bests + quarantined E1 TIF) => log duplicate, stop.
Checked on the surface before placement AND on final dots.

## What is already known (verified this session, byte-level)

- All 9 focus bests are nested subsets of one H19-5 dotted lineage:
  champion (37,654) subset of GEMSDOE31 best (40,199) subset of D2.8 (44,090);
  GEMSDOE25 = GEMSDOE30 pixel-identical; GEMSDOE36 = champion + 1,200 dots.
  (`evidence/champion_forensics.json`, `scripts/champion_forensics.py`)
- Live ladder (OWNER-REPORTED) tracks only emission: spacing D1.5->D2.8 and
  near-catalogue dot fraction 14.6% -> 6.3% -> 0.0% yields 0.2600 -> 0.2708 -> 0.2778.
- Fixed-mask visible-gated holdout ANTI-ranks that ladder (0.0992 > 0.0301 > 0.0045):
  B-gated final masks cannot score on withheld catalogue segments they were
  gated away from. It is therefore used ONLY in callable (fold-local re-emission)
  mode for surfaces, never to compare final masks. (`evidence/baselines_visible_gated.json`)
- Reproduced E1 card exactly: champion SGMC raw HOLDOUT-DTI 0.09606 [0.08431, 0.10822]
  (62,703 SGMC positives); E1 0.07521. Champion-surface proxy on hide-recover:
  0.09920 (the ungated D2.8 ancestor mask under the same evaluator).
- SGMC caveat: directly emitting SGMC faults scored 0.0512 / 0.0492 live
  (prompt list) while trivially maximising the SGMC evaluator. SGMC is a
  necessary-consistency check for non-SGMC-trained surfaces, not a target to
  train on without fold-local withholding (Exp 2 withholds by quadrant).

## Five ranked hypotheses (layers / signature / why off-catalogue / mimic / difference)

| Rank | ID | Layers | Physical signature | Why it catches faults missing from USGS/INGENIOUS | Non-fault mimic | Difference vs this repo (E1 XG-HGB) & cost |
|---|---|---|---|---|---|---|
| 1 | CORROB | RTP + isostatic gravity (training bands 2/13), tilt (8/2), 1 m LiDAR step/dipole (external bands 3, 6-7), LiDAR valid mask | Geometric mean of robust-normalised Hessian line responses + mag x grav cross-gradient + LiDAR scarp step/dipole, coverage-routed where LiDAR absent; NO label training | Expert test faults are ones single-dataset mapping missed; requiring independent physics to coincide retains covered/subtle faults while suppressing single-survey artefacts | Lithologic contacts, roads/mine benches, terrace risers | Unsupervised (E1 was supervised HGB); no catalogue-style fitting. Low cost |
| 2 | MCSUP | Same 47-ch stack | HistGradientBoosting with positives = catalogue faults UNION off-catalogue SGMC faults (fold-local), negatives >3 px from both | SGMC adds a blind/bedrock fault population, countering catalogue mapping bias (labels denser inside LiDAR coverage upstream IR-32-LIDAR-01) | SGMC lithologic contacts; SGMC positional error >300 m | E1 trained on catalogue positives only. Medium cost |
| 3 | EMIT | Winner surface of Exp 1/2 | Budget sweep {25,000 / 37,654 / 44,090} at spacing>=3 px, B=2; pick by pooled OOF DTI | Champion ladder proves emission geometry drove 0.1922->0.2778; copied 37-44k budgets may be suboptimal for a different-precision surface (isolated-dot bar k > alpha*DTI = 0.056 at 0.2778) | None (emission only) | E1 fixed budget at champion's 37,654 uncritically. Low cost |
| 4 | TEXDISP (deferred) | GeoDAWN K/Th/U (uint8 cache) + LiDAR strike | Cross-edge radiometric texture patch-translation consistency along scarps | Displaced stratigraphic texture marks unmapped strike-slip/dip-slip structures without catalogue proximity | Lithologic contacts, irrigation, survey seams | Not tried in repo; uint8 quantisation may destroy texture. High cost -> deferred |
| 5 | SEISMLIN (blocked) | USGS ANSS ComCat FDSN epicentres (free official https://earthquake.usgs.gov/fdsnws/event/1/) | Collinear microseismicity + nodal-plane strike agreement | Seismogenic blind faults under basin fill have no scarp/potential-field edge | Quarry blasts, aftershock clouds | Not tried in repo as features (bands 10/16 are only smoothed density/distance). BLOCKED: sandbox bash egress is github/pypi/npm only; USGS fetch verified unreachable from bash (see review). Viable only if fetched on an unrestricted machine |

## Pre-registered experiments (budget: 3, then stop)

- Exp 1 CORROB (above), budget 37,654.
- Exp 2 MCSUP (above), budget 37,654.
- Exp 3 EMIT budget sweep on the Exp 1/2 winner by quadrant-OOF.

## Pre-registered decision rule (no slot without all gates)

Primary: KANLER quadrant-blocked OOF v1 (whole-quadrant holdout, 15 px collar,
12 px erosion, visible-only B=2, alpha 0.2 beta 0.8 300 m triangular; 56,464
withheld label px) — fold-local emission for every surface.
Secondary paired gates vs champion: (a) callable GEMSDOE32-HOLDOUT-v3-visible-gated
vs champion-surface proxy 0.09920 (22,232 withheld); (b) SGMC raw vs champion
0.09606 (62,703 withheld), paired 16-tile bootstrap CI on the difference.
Promote-eligible only if: canary max AUC <= 0.90; surface AND dots pass
uniqueness; (a) and (b) both favour the candidate; validator passes.
Otherwise verdict = negative (deliverable), TIF labelled research-only.
MODEL ESTIMATE (never a score) = 0.2778 x SGMC_cand / SGMC_champ with
paired-bootstrap range. Promotion to a weekly slot remains a separate
selector step (`scripts/promotion_gate.py` + human slot check on DrivenData).
