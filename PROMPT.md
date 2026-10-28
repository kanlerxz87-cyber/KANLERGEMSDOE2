# Standing Project Brief & Parallel-Run Protocol (`KANLERGEMSDOE2`)

> **Epistemic integrity:** This is a condensed standing brief, not a verbatim transcript. Read it together with the project README, `AGENTS.md`, and frozen lane files at the start of each session. **Current decision (2026-10-27): NEGATIVE — DO NOT SUBMIT.** No new TIFF or score was produced. Historical user/owner reports are not organizer receipts; projections are not scores.

## Core Values

- **Maximize P(Win):** Optimize scientifically defensible expected return per scarce submission slot. Protect slots from duplicates, cosmetic edits, and candidates that fail the independent spatial validation or literal uniqueness gate. Do not assert a leaderboard score from a holdout or projection.
- **Own the Outcome:** Automate safety checks; do not substitute human visual inspection for automated gates. Check float32 `[0,1]` values and no NaN/Inf inside the footprint; respect the official exterior convention; test leakage, registry uniqueness, and buffered holdout significance. Fix shared-template defects at their root and document every irregularity and negative result.

---

## Standing Project Prompt Record

Review and improve the geothermal-fault submission project while preserving the nine focus sites:

`GEMSDOE24`, `GEMSDOE25`, `GEMSDOE27`, `GEMSDOE28`, `GEMSDOE30`, `GEMSDOE31`, `GEMSDOE32`, `GEMSDOE33`, and `GEMSDOE36`.

The broader historical request names `KANLERGEMSDOE1..3`, `EUGGEMSDOE1..3`, `WBGGEMSDOE1..3`, `GINNYGEMSDOE1..3`, and `GEMSDOE` sites. Do not claim fleet-wide uniqueness or novelty unless the relevant complete registry and source implementations have actually been checked.

### Submission goal and fail-closed constraint

- The user wants a **unique competition TIFF** and a clear download/submit decision at the top of the site and executive summary. Produce one only if all frozen gates permit it; **the desired output does not override a literal duplicate stop**. The current 37,654-dot budget has a witness-derived lower bound of 82.3418% overlap against a 70% cap. Do not fit, place, emit, promote, or upload while this stop applies. Do not evade it by changing the budget, silently exempting a registry raster, hand-picking dots, or changing filenames.
- Investigate the portal error `Predicted values must be in range [0, 1]`. Audit the exact single-band float32 TIFF against the authenticated sample’s EPSG:32611 CRS, 3730 × 3292 shape, 100 m affine grid, whole-array and in-footprint values, NaN/Inf handling, and exterior convention. Official text says null/NaN outside bounds. A local range/grid pass is not organizer acceptance; preserve the error diagnosis as unknown if no organizer explanation is retained.
- A future authorized submission must have an exact unique filename and a note of at most 140 characters. Do not create a submission name for a file that does not exist or is not cleared.
- Keep `docs/executive-summary.html` as an auditable guide/table across sites: exact pinned historical file identity, score evidence class, local format status versus portal acceptance, 3-px focus-set uniqueness, and an explicit no-file/no-estimate current row.

### Forensic and hypothesis requirements

1. Explain why GEMSDOE32’s `0.2778` is only USER/OWNER-REPORTED, not receipt-confirmed. Describe geometric differences that could plausibly contribute, but do not claim causation, hidden-score recovery, or an organizer-confirmed score without a matching receipt.
2. Before any future model code, prepare 3–5 ranked, physically grounded hypotheses. Each needs exact layers, a physical signature/transform, why it could detect catalogue-missing faults, a named non-fault mimic and control, differences from inspected source implementations, implementation cost, and free/official data-access feasibility. Do not call an idea “untried” until relevant code is checked; do not claim fleet-wide novelty from a partial repository scan.
3. Stay in the assigned preregistered lane. The current research slate gives three qualitative priorities, no numeric DTI prediction, and no permission to extend the historical three-arm HTCADS lane.

### Parallel-run protocol (strict)

1. **LANE / UNIQUENESS:** Stay within `registry/preregistration_htcads.json`. Compare rank correlation and >70% of dots within 3 px against **every** registry raster, with no calibration-control exemption unless the protocol is formally changed. Check the continuous surface before placement and final dots after placement. Either threshold failing means duplicate and stop. At the current frozen budget, the pre-fit lower bound already fails.
2. **SHARED TOOLING:** Only after the hard stop clears, reuse the shared cached stack, `evaluate_holdout.py`, and `submission_writer.py`. Hold out whole fault segments with a buffer; derive every catalogue-based feature only from fold-visible faults; mask visible faults pixel-exactly; score pooled DTI with α=0.2, β=0.8, and the 300 m triangular kernel. Fix shared tools in the common template, not a private fork.
3. **SCORE LABELS:** Label each holdout metric `HOLDOUT-DTI` with evaluator version, withheld-positive N, and 95% CI. Use `ORGANIZER-CONFIRMED` only with an actual submission-page receipt. Never report a projection as a score.
4. **LEAKAGE CANARY:** Test each feature alone. AUC >0.90 is leakage until adequately explained; fail closed.
5. **ONE CURRENT RUN CARD:** Maintain `evidence/current_run_card.json`; prior cards remain historical. Include hypothesis, mechanism, named non-fault mimic, HOLDOUT-DTI and CI (or explicit not-measured state), registry correlation/overlap, raster SHA-256 (or null if no TIFF), validator results, submission name and ≤140-character note (or null if no candidate), and `negative`/`promote` verdict.
6. **BUDGET / SLOTS:** Stop after 3 experiments or 2 hours. Do not automatically spend/select a live slot. The historical HTCADS three experiment arms are already recorded; this review authorizes no additional experiment.

### Workflow and delivery

- Preserve this project brief and Arena Core Values in `README.md` for future sessions.
- Verify claims, hashes, calculations and official URLs; flag source irregularities and evidence gaps.
- Complete three review passes: (1) source/data and implementation verification, (2) scientific/code review and bug fixes, (3) final accuracy, tests, links and release-quality review.
- Try to create and merge a PR onto `main` only if the active Arena branch and environment permit. Never switch or push to a different branch.

## Corrected dated leaderboard reference

The original user message cited `#1 = 0.4413` and `0.3195` as the fifth-place score. The repository’s official-source snapshot, observed 2026-10-27 (date precision only), instead records `#1 = 0.4544`, `#5 = 0.3566`, `#25 = 0.3195`, and `#50 = 0.2857`. This is a dated snapshot, not a live observation; rank can change. It does not predict this project’s score.

See `README.md` for current decision, site links and review artifacts; `registry/PREREGISTRATION_STATUS.md` for the frozen lane; and `evidence/three_pass_review_20261027.md` for the current audit record.
