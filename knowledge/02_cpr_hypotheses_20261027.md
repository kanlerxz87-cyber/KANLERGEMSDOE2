# KG2-CPR Lane — Hypotheses, Results, Negative Verdict (2026-10-27)

Frozen before training in [`registry/preregistration_cpr.json`](../registry/preregistration_cpr.json).
Raw receipts: [`evidence/cpr_experiments.json`](../evidence/cpr_experiments.json) ·
[`evidence/cpr_run_card.json`](../evidence/cpr_run_card.json) ·
[`evidence/ledger_recomputation_20261027.json`](../evidence/ledger_recomputation_20261027.json) ·
[`evidence/promoted_reverification_20261027.json`](../evidence/promoted_reverification_20261027.json).
Code: [`scripts/run_cpr_experiments.py`](../scripts/run_cpr_experiments.py) (340 s wall, 3/3 experiments).

## Five ranked hypotheses (summary)

| Rank | ID | Idea | Outcome |
|---|---|---|---|
| 1 | H-C1 | Soft DTI-credit regression target `y=k(d)` (official 300 m triangular kernel) instead of binary dilated positives | **Confirmed on hide-and-recover, rejected for blind discovery** (see below) |
| 2 | H-C2 | OOF-priced CELF dot budget (Dinkelbach: emit while marginal `q > 0.2·DTI`) | Curve rises monotonically to 46k on hide-and-recover — no interior optimum vs catalogue-like truth |
| 3 | H-C3 | 1-px crest snapping of emitted dots | **Falsified**: −0.0080 / −0.0100 paired Δ (CIs strictly negative) |
| 4 | H-C4 | Geodesic least-cost tip linkage | Deferred (protocol budget spent) |
| 5 | H-C5 | NASA OPERA DISP-S1 InSAR playa barrier steps | Not viable from this sandbox (ASF/Earthdata hosts off-allowlist); free official source named in preregistration |

## Results (all `HOLDOUT-DTI`, evaluator `GEMSDOE32-HIDE-RECOVER-v3.0`, N=22,232 withheld positives)

Budget curve on OOF cells: 18k→0.129809 · 24k→0.140773 · 30k→0.145459 · 34k→0.147492 ·
37,654→**0.147951** [0.1341, 0.1614] · 42k→0.148481 · 46k→0.148538.
Champion reference reproduced exactly: 0.099202 [0.0860, 0.1127]; paired Δ for CPR-1 = +0.048749 [+0.0361, +0.0613].

Secondary blind evaluator (`GEMSDOE32-SGMC-CAL-v3.0`, N=62,703): CPR-1 **0.056742**,
CPR-2 0.056751, CPR-3 0.051120 — all *below* the 0.2778 champion (0.064121) and far below
HTCADS EXP-2 (0.078913, re-verified 2026-10-27 on restored data).

Uniqueness (Rule 1, 20 footprint-distinct restored registry rasters incl. focus-9 champions and all
in-repo candidates): CPR-1 max 3-px overlap **0.780979** vs `gems10-h25-ctx-ridge`, 0.765 vs the
promoted HTCADS EXP-2 → **duplicate stop**. Surface |Spearman| max 0.2018 (passes; dots fail).

## Interpretation (why this negative result matters)

Soft targets teach the model to center mass on *catalogue-style* scarps (79.2% of CPR dots within
10 px of the catalogue; median 5 px). Hide-and-recover withholds catalogue faults, so it rewards
exactly that behaviour — the same trap as FVCA (`IR-KG2-SCARP-CONVERGENCE`). The live test set is
expert-mapped **off-catalogue** faults; the only in-repo candidate that improves on *both*
orthogonal populations remains HTCADS EXP-2, whose 55% label-free physical-conduit weight carries
blind geothermal signatures (updip gravity, demagnetization, MT clay-cap edges, GDR-1391 thermal
back-projection) that no label-trained model in this fleet has matched off-catalogue.

Projection warning, quantified: naive HR→live projection for CPR-2 is 0.4986 while its SGMC→live
projection is 0.2401. Any future lane must report **both** projections and treat disagreement as a
catalogue-bias alarm, never average them away.

## Irregularities logged this session

- `IR-CPR-LEDGER-01`: previously published ledger point values (R²=0.998523, TPw=5,151.3,
  K=13,734.7) do not reproduce from the stated chain; exact OLS gives **R²=0.999589,
  TPw≈5,210 px, K≈14,020 px** (conclusion unchanged). See ledger recomputation receipt.
- `IR-CPR-README-02`: README focus-9 table carried stale filenames/SHA truncations vs the
  fetched champion files; corrected against `evidence/nine_site_audit.json` + fresh SHA-256.
