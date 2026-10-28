# Executive summary — KANLERGEMSDOE2

**Decision (2026-10-27): NEGATIVE — DO NOT SUBMIT.** There is no new candidate TIFF to download or submit, no current HOLDOUT-DTI, and no defensible score estimate. The frozen 37,654-dot budget has an exact lower bound of **82.3418%** overlap within 3 px of one registered witness, above the literal 70% limit. This stops the work before fitting and placement; the budget or registry cannot be changed to evade the rule.

## What is evidence, and what is not

- GEMSDOE32’s **0.2778** is **USER/OWNER-REPORTED**. The reviewed records contain no organizer submission-page receipt tying it to its pinned TIFF. It is not `ORGANIZER-CONFIRMED` and is not a holdout score.
- Exact raster geometry shows GEMSDOE32’s 37,654-dot mask is GEMSDOE25’s mask after removing 6,436 pixels within 2 px of the restored known-fault mask; the XOR is zero. That pruning could plausibly alter false-positive cost, but hidden truth is unavailable. The metric uses a 300 m triangular distance kernel with α=0.2 and β=0.8; known-fault masking is pixel-exact, not a 2-pixel buffer. Removing an unhelpful near-catalogue dot could reduce false-positive mass, while deleting a prediction near new truth could lose distance-weighted credit or add false-negative cost (the larger coefficient). The change could help, hurt, or do neither; causation and any hidden score cannot be established.
- The dated public-leaderboard snapshot observed 2026-10-27 records #1 = 0.4544, #5 = 0.3566, #25 = 0.3195 and #50 = 0.2857. It conflicts with the earlier statement that 0.3195 was highest. It is not live; ranks may change.
- The historical HTCADS research file [`kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif`](docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif) has SHA-256 `f482d3bad4b390470be06363b60867c8e42942101271caf4fa82ae3c3975abeb`. It has 37,642/37,654 dots (99.9681%) within 3 px of the witness. It is **research only, not authorized for submission**.
- Its local float32/range/grid checks pass against the pinned owner-mirror template, but its outside-footprint zeros differ from the sample’s NaN convention. The official format text says null/NaN outside; no portal acceptance receipt or retained diagnosis of the earlier range error is available.
- All nine focus-site historical files exceed the 70% directional 3-px overlap threshold against at least one other focus site. This is a focus-set comparison, not a full current-registry replay.
- Feature index 28 was mislabeled `anderson_slip_tendency`: the shared code now correctly names its cosine-squared alignment to a fixed 62° axis `strike_alignment_fixed_62deg`. Values are unchanged; this feature is not a stress-tendency calculation. HTCADS thermal-plume directions use a terrain-elevation-gradient proxy, not measured groundwater head.

## Decision table and next steps

The auditable [executive summary subpage](docs/executive-summary.html) contains the per-site table with exact file identities, USER/OWNER-REPORTED scores, overlap, historical download links, and the explicit no-estimate/no-submit status. The [current dashboard](docs/index.html) shows the negative decision first. The [three-hypothesis research slate](research/2026-10-27_htcads_hypotheses.md) is untested, not a score forecast, and not authorization to extend the already completed three-arm lane.

No shared cache was available (`data/` and `.cache/` are absent), so no new model fit, leakage canary, holdout, or TIFF emission was attempted. The complete live registry and pre-placement surface were not replayed. No live slot was spent.

Future evaluation can proceed only if the protocol is formally resolved without silently exempting the witness, authorized data/cache are restored and hash-checked, and the complete pre-fit uniqueness gate passes. Then use shared tooling, per-feature canaries, buffered whole-segment hide-and-recover, and an independent selector; report each metric as `HOLDOUT-DTI` with evaluator, withheld-positive N and 95% CI. No automatic upload or slot selection.

## Evidence and review

- [Current negative JSON run card](evidence/current_run_card.json)
- [Release audit and exact overlap lower bound](evidence/release_audit_20261027.json)
- [Dated official-source snapshot](registry/official_sources_20261027.json)
- [Three-pass review record](evidence/three_pass_review_20261027.md)
- [Full standing brief and protocol](PROMPT.md)

**Arena Core Values: Maximize P(Win) · Own the Outcome.**
