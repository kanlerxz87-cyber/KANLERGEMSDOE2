# Working contract for future sessions

1. Read `README.md`, its preserved standing brief, `PROMPT.md`, `registry/preregistration_htcads.json`, `registry/PREREGISTRATION_STATUS.md`, and `evidence/current_run_card.json` before experiments or changes to the submission portal.
2. Current decision: **negative; do not submit any existing TIFF.** `evidence/release_audit_20261027.json` proves the previous candidate fails the user's literal all-registry 3-px rule. The 37,654-dot preflight bound is unavoidable for that budget. A calibration control is not exempt unless the user expressly changes the protocol; do not manipulate the budget or placement to evade it.
3. Work in the assigned lane and run the mandatory pre-placement surface and post-placement all-entry registry checks, single-feature leakage canaries, and buffered, whole-segment spatial holdout using visible-only catalogue features. A single witness is a failure proof, not full-registry clearance. Stop before model fitting/emission when the gate already fails. Respect the three-experiment/two-hour budget.
4. The holdout, nine scores and historical reports are not independently replayed or verified by submission-page receipts. Use `HOLDOUT-DTI` with evaluator, withheld-positive count and CI; call scores `ORGANIZER-CONFIRMED` only with a real receipt. Never turn a projection into a score or infer hidden truth from rounded leaderboard figures.
5. Match the official template, audit every stored value and distinguish its NaN exterior convention from any zero-filled alternative. Neither a local format check nor a named TIFF proves portal acceptance. No live slot is automatically spent or selected; require a separate, current, account-aware selector after all independent gates pass.
6. Source hashes identify owner-mirror bytes; they do not authenticate official provenance. Keep bulk data and generated work caches out of Git. Fix shared tools and report irregularities. Run the requested three review passes; never mask a negative result for presentation.
7. Core values: **Maximize P(Win)** and **Own the Outcome**. Protect weekly slots, automate checks, and state limitations plainly instead of relying on a human geological inspector.

## KG2-S3 LOPE lane (2026-10-27) standing state

- **No file in this repository is OK to submit.** `scripts/validate_submission_kg2s3.py` recomputes format and uniqueness from bytes (360 registry rasters plus 124 ledger rasters) and binds holdout receipts to the exact dots. It rejected the new LOPE file (holdout and uniqueness gates) and the Session-2 DSLUP file (72.69 % overlap with `gems22-h23-a-dti-optimal-emission-6pct`).
- Restore order: `restore_data.py --group core|external|scored`, `restore_focus_sites.py`, `fetch_lb_ledger.py`, `fetch_registry_rasters.py`, `prepare_data.py`.
- Live-ledger (LLI) numbers are PROJECTIONS (leave-site-out MAE about 0.025) and can never promote. Scores in the ledger are USER-REPORTED.
- Irregularities, next steps and limitations: `evidence/kg2s3_irregularities.json`.

## KG2-S3 HPTR lane (2026-10-27) standing state

- Emitted unique `[0, 1]` research GeoTIFF `docs/downloads/kanlergems2-hptr-exp-2-37654dots-20261028T014401Z-675d0ff8-zeros.tif` (`SHA-256 2d53632cb161a2172806bae5e82f8c456d5717112504f45ca7ec91a1c1ba8ff3`, `37,654` dots = `5,200` Stage-1 piedmont/void + `32,454` Stage-2 horst/tip, `0` NaNs across all `12,279,160` cells, `0` on-catalogue).
- Resolves `IR-TRBVC-SGMC-BASIN-SHARE-10` and `IR-DARP-CREST-OVERDAMP-08`: **first candidate in `KANLERGEMSDOE2` to beat `0.2778` (`GEMSDOE32`) simultaneously across all three blind holdouts** (`Hide-Recover = 0.113133` vs `0.099202`, `SGMC-CAL = 0.077148` vs `0.064121`, `C-PIED = 0.104289` vs `0.101166`), with `<= 65.98%` binary (`r >= 0.5`) 3-px overlap across all non-blanket detectors and `<= 49.24%` across all 9 Focus & 21 Sister repos (`evidence/hptr_full_fleet_audit_20261027.json`).
- **Remains `DO NOT SUBMIT` (`verdict = "negative"`):** stopped fail-closed by `scripts/validate_submission.py` (`99.963%` `13gems` spacing-5 lattice witness) and `scripts/validate_submission_kg2s3.py` (`IR-KG2S3-SOFTTAIL-SUPPORT-14` `r > 0` soft-tail + retracted-`DSLUP` bar). Run card: `evidence/session3_hptr_run_card_20261027.json`.


