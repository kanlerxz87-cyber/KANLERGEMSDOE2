# KANLERGEMSDOE2 — fail-closed geothermal-fault research

> **Current decision (2026-10-27): NEGATIVE — DO NOT SUBMIT.** No new TIFF was produced and there is no cleared file to download for a competition slot. At the frozen **37,654-dot** budget, one registered raster forces a minimum **82.3418%** within-3-pixel overlap, above the literal 70% limit. The bound is exact for this footprint, witness and budget; it is not a complete registry audit and does not prove that every smaller budget fails. Do not evade it by changing the budget, exempting the calibration control, hand-picking dots, or renaming a file.

**Arena Core Values:** **Maximize P(Win)** · **Own the Outcome**. In this project, maximizing win probability includes protecting scarce slots, respecting the frozen lane, and reporting negative or unavailable results without converting projections into scores.

## Start here each session

Read this complete `README.md`, [`PROMPT.md`](PROMPT.md), [`AGENTS.md`](AGENTS.md), [`registry/preregistration_htcads.json`](registry/preregistration_htcads.json), and [`registry/PREREGISTRATION_STATUS.md`](registry/PREREGISTRATION_STATUS.md) before working. The brief below is operative; the frozen preregistration remains historical and may not be silently changed to bypass a gate.

## Current evidence in one minute

- **New candidate:** none. **New GeoTIFF SHA-256:** none. **Submission name:** none. **Live slots spent in this review:** 0. **New experiments:** 0.
- **Current HOLDOUT-DTI:** not measured; the gate stopped work before fitting. The historical run card records an earlier `HOLDOUT-DTI` only as a prior-session receipt, not replayed or promotable.
- **Prior research raster:** [`kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif`](docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif), SHA-256 `f482d3bad4b390470be06363b60867c8e42942101271caf4fa82ae3c3975abeb`. It is **not authorized for submission**: 37,642/37,654 dots (99.9681%) overlap the registered witness within 3 px. It uses zeros outside the footprint; the mirrored sample uses NaN outside. Local format checks are not portal acceptance.
- **Focus-site leader:** GEMSDOE32, **0.2778 USER/OWNER-REPORTED**. No organizer receipt tying that score to the pinned TIFF was located. It is not a holdout result or a score we reproduced.
- **Geometry, not causation:** the GEMSDOE32 37,654-dot mask equals GEMSDOE25 after removing 6,436 pixels within 2 px of the restored known-fault mask. That could plausibly change false-positive cost, but hidden truth is unavailable. The metric uses a 300 m triangular kernel, α=0.2 and β=0.8; known-fault masking is pixel-exact, not a 2-pixel buffer. Pruning could help, hurt, or do neither, especially because false negatives carry the larger coefficient. No causal score gain or hidden score can be established.
- **Dated public leaderboard record:** the official-source snapshot observed 2026-10-27 records #1 `0.4544`, #5 `0.3566`, #25 `0.3195`, #50 `0.2857`. This contradicts the earlier user statement that `0.3195` was #1/#5. It is a dated observation, not a live check; ranks can change.
- **Nine-site uniqueness:** none of the nine historical focus-site files is unique under the stated >70% directional 3-px rule against the focus set. Exact pinned identities, reported scores, overlaps and research-only download links are in the [executive summary](docs/executive-summary.html) and [comparison table](docs/submission-table.html).
- **Superseded promotion copy:** an archived DSLUP card contains a policy-specific `promote` verdict under an earlier control-separated reading. The current literal any-registry rule grants no control exemption; that old claim is not current authorization and must not be used to submit.
- **No raw data cache:** `data/` and `.cache/` are absent in this workspace. No model or holdout work was run from this review.

### HTCADS feature-semantics correction

`src/gems32/htcads.py` previously called feature 28 `anderson_slip_tendency`, but the code computed only `cos(dom_strike_fp − 62°)²`, an axial alignment to a fixed axis. It uses no stress tensor, fault-plane normal, friction, or slip model. The shared name is corrected to `strike_alignment_fixed_62deg`; pixel values are unchanged. Historical canaries and run cards retain their old feature label and must not be interpreted as Anderson slip-tendency evidence.

A separate physical caveat: HTCADS plume direction is computed from smoothed detrended terrain elevation, not measured groundwater hydraulic head. The code now calls it a terrain-gradient proxy; it is not an observed hydraulic gradient or groundwater-flow vector. Details and ranked future hypotheses are in [`research/2026-10-27_htcads_hypotheses.md`](research/2026-10-27_htcads_hypotheses.md).

## PARALLEL-RUN PROTOCOL (MANDATORY, STRICT, FAIL-CLOSED)

1. **Stay in the assigned lane.** Work only inside the preregistered HTCADS lane. Check the continuous surface **before placement** and final dots against **every** registry raster. Rank correlation `>0.90` or `>70%` of dots within 3 px of any registry raster means duplicate: log and stop. No calibration-control exemption exists unless the protocol is formally changed. The current lower bound forces a stop at the frozen budget.
2. **Use shared tooling only.** When—and only when—the hard stop permits—reuse the project’s cached feature stack, shared hide-and-recover evaluator and shared writer. Withhold whole fault segments with a buffer; derive catalogue features only from fold-visible faults; mask visible faults exactly; score pooled DTI using α=0.2, β=0.8 and the 300 m triangular kernel. Fix shared-tool defects in the common template, never in a private fork.
3. **Label score evidence.** Every holdout metric must be labeled `HOLDOUT-DTI` with evaluator version, withheld-positive N and 95% CI. Use `ORGANIZER-CONFIRMED` only when an actual submission-page receipt is archived. A projection is never a score. Current new HOLDOUT-DTI is **not measured**.
4. **Leakage canary.** Test each feature alone before model evaluation. AUC `>0.90` is leakage until adequately explained; fail closed.
5. **One current run card.** `evidence/current_run_card.json` is the current negative card; prior cards are historical. It records the hypothesis, mechanism, named non-fault mimic, HOLDOUT-DTI/CI, registry correlation/overlap, raster identity, validator output, submission name/note and verdict. A negative card is a valid deliverable.
6. **Budget.** Stop after three experiments or two hours. The historical three HTCADS arms are already recorded; this review authorizes no additional experiment. Never spend or choose a live slot automatically.
7. **No release by appearance.** No human visual review substitutes for automated gates. Do not generate, promote, link as a submission, or upload a TIFF if the literal gate fails.

## Preserved project prompt and acceptance criteria

The user’s standing request is preserved here in operational form so a future session can resume without losing constraints:

- Review and improve this geothermal-fault submission project; preserve the nine focus sites: `GEMSDOE24`, `GEMSDOE25`, `GEMSDOE27`, `GEMSDOE28`, `GEMSDOE30`, `GEMSDOE31`, `GEMSDOE32`, `GEMSDOE33`, and `GEMSDOE36`.
- Explain why GEMSDOE32’s `0.2778` is only user/owner-reported; describe plausible geometric differences but do not infer hidden truth or claim causation. Do not claim a method is untried until relevant code has been searched.
- Prepare 3–5 ranked, physically grounded hypotheses with exact layers/signatures, rationale for missing faults, named mimics, differences from inspected implementations, and data-access feasibility. Do not fit or validate a candidate while a hard stop applies. The current research slate lists three and makes no numerical DTI prediction or fleet-wide novelty claim.
- Reuse shared stack/evaluator/writer only when all gates permit. Report leakage, buffered holdout, pooled DTI, evaluator, N and CI; do not convert projections into scores. Keep one JSON run card and preserve negative results.
- Maintain an accurate executive summary/table with exact file identities and evidence classes; distinguish local TIFF format checks from portal acceptance; explain the prior range error only to the extent evidence allows.
- Keep submission notes at or below 140 characters; provide automated submission instructions and official-source links, but do not spend/select/upload a slot automatically.
- Record feed freshness and limitations, verify claims against trusted official sources, flag irregularities, and perform three review passes. Try a PR/merge only when the active branch and environment permit.
- A unique TIFF is desired only when it can pass the literal gate. The current frozen-budget lower bound prohibits fitting/emission and promotion; it must not be evaded. No current score estimate is available.

The original, longer, condensed prompt is also in [`PROMPT.md`](PROMPT.md); its older leaderboard values are superseded by the dated record above. See [`evidence/three_pass_review_20261027.md`](evidence/three_pass_review_20261027.md) for the audit passes and [`docs/data/status_feed.json`](docs/data/status_feed.json) for the machine-readable status.

## Site and evidence index

- [Current decision dashboard](docs/index.html) — negative verdict and dated public-leaderboard feed.
- [Executive summary](docs/executive-summary.html) — decision, nine-site comparison, score provenance, 0.2778 geometry and future automated workflow.
- [Historical submission table](docs/submission-table.html) — pinned files with research-only download links and overlap evidence.
- [Ranked hypotheses](docs/research.html) and the [full research note](research/2026-10-27_htcads_hypotheses.md).
- [Open issues / three passes](docs/irregularities.html), [current run card](evidence/current_run_card.json), [historical-promotion supersession manifest](evidence/supersession_manifest_20261027.json), [release audit](evidence/release_audit_20261027.json), and [official source record](registry/official_sources_20261027.json).

## Arena Core Values

- **Maximize P(Win):** seek the best scientifically defensible return per scarce slot; do not spend a slot on an unvalidated or duplicate candidate.
- **Own the Outcome:** automate safety checks, fix common tooling, label evidence honestly, and publish negative results and limitations without hand-waving.
