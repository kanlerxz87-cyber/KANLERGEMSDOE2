# Three-pass review record — 2026-10-27

**Release decision: NEGATIVE — DO NOT SUBMIT.** This review made no model fit, holdout run, new TIFF, live submission, or leaderboard-score claim. The literal 37,654-dot lower bound remains 82.3418% overlap against a registered witness, above the 70% stop. It is not a complete registry replay and is not generalized to other budgets.

## Pass 1 — source, evidence, and artifact identity

- Re-read `README.md`, `PROMPT.md`, `AGENTS.md`, the frozen HTCADS preregistration/status, current run card, release audit, source records, focus-site records, and current portal/status files.
- Confirmed GEMSDOE32’s `0.2778` is user/owner-reported in local records, with no matching organizer submission receipt found. The archived raster has a pinned SHA-256 and an auditable 3-pixel witness overlap; local format checks do not establish organizer acceptance.
- Reconciled the date-only public-leaderboard snapshot: #1 0.4544, #5 0.3566, #25 0.3195, #50 0.2857 as recorded on 2026-10-27. No live external page was fetched in this pass; the snapshot may be stale.
- Confirmed `data/` and `.cache/` are absent. The complete current registry and prior continuous surface were not replayed.

## Pass 2 — scientific/code review and corrections

- Traced `SUBSURF_FEATURE_NAMES[28]` to `X_sub[:, 28]` in `src/gems32/htcads.py`. The formula is `cos(dom_strike_fp − 62°)^2`; it is axial fixed-angle strike alignment, not Anderson slip tendency. Corrected the shared feature name and pillar comments to `strike_alignment_fixed_62deg`, extracted the unchanged formula into a small helper, and added tests for axial periodicity and semantics. Historical run cards/canaries retain their original name and are explicitly not treated as evidence of a stress calculation.
- Traced the plume vector to the gradient of smoothed `det_elev`. The code does not use measured groundwater hydraulic head. Updated the function documentation and preregistration status to describe the input as a terrain-gradient proxy.
- Rechecked relevant `htcads.py`, `dslup.py`, and `darp_mt10.py` paths before revising the research slate. The slate now has three qualitative priorities with exact layers, physical signatures, blind-fault rationale, non-fault mimics/controls, in-repository overlaps, and data-access limits. No claim of fleet-wide novelty is made.

## Pass 3 — release, tests, and remaining limitations

- Rebuilt the static pages from the negative current card only. The overview leads with “NEGATIVE — DO NOT SUBMIT”; the executive table contains all nine exact historical file identities, local-format/portal-unknown labels, score evidence classes, overlap, research-only downloads, and no new-file estimate. The generated feed contains no positive candidate authorization.
- Added `evidence/supersession_manifest_20261027.json` to flag historical policy-specific “promote” receipts without mutating their original verdicts; the current site and README link to that notice.
- The first automated test attempt found four integration issues; the second found two remaining legacy-contract assertions. The feed/table compatibility fields and README heading were reconciled, the terrain-proxy test was corrected to match the actual docstring, the review-note link was added, and regression assertions now reject stale positive portal copy before the final run.
- Final test result: `./.venv/bin/python -m pytest -q` — **48 passed in 5.95s**; `python -m compileall -q src scripts tests` passed. `python scripts/build_site.py` completed successfully from the negative card and exact pinned artifacts.
- The CI archival step `scripts/evaluate_holdout.py --verify-kg2` passed recorded hash/ZIP/metadata checks only. It did not rerun the holdout, fit a model, emit a raster, or authorize upload; its output itself reports the current literal-rule verdict as negative.
- No new TIFF or live score was generated. The public leaderboard, competition login-walled data, complete fleet registry, current quota and portal acceptance remain unverified in this environment. A unique submission is prohibited by the literal frozen-budget stop.
