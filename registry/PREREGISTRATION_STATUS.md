# Status of the frozen HTCADS preregistration

`preregistration_htcads.json` is preserved byte-for-byte as a historical record. Its `max_detector_3px_dot_overlap` terminology was used to exempt a lattice control in earlier code. The user's standing protocol says **any registry raster**; the control is not exempt. The old detector-only promotion is withdrawn. The current budget-specific stop is in [`../evidence/release_audit_20261027.json`](../evidence/release_audit_20261027.json) and [`../evidence/current_run_card.json`](../evidence/current_run_card.json).

Any numeric expected improvements in the frozen preregistration are historical hypotheses, not measured scores or leaderboard predictions. Do not change the frozen method or budget merely to evade the literal gate. The stricter registered absolute-rank cap remains a conservative additional check.

## Code-semantics review — 2026-10-27

The frozen JSON is intentionally unchanged. A source audit found that `SUBSURF_FEATURE_NAMES[28]` said `anderson_slip_tendency`, while `src/gems32/htcads.py` computed `cos(dom_strike_fp - 62°)^2`. That is axial strike alignment to a fixed reference, not a slip-tendency calculation: the expression uses no stress tensor, fault-plane normal, friction, or slip model. The shared feature name and pillar comments were corrected to `strike_alignment_fixed_62deg`; the numeric feature values are unchanged. Existing run cards and canary receipts keep their historic label and must not be cited as Anderson-slip evidence.

The thermal plume's direction vector is derived from smoothed detrended surface elevation (`det_elev`). No measured groundwater hydraulic head is an input. Code comments and the current research note now call this a terrain-gradient proxy; it is not an observed hydraulic gradient or groundwater-flow vector.

No candidate was fitted, no holdout was run, no new GeoTIFF was emitted, and no live slot was spent. The three pre-registered HTCADS experiment arms are historical; this review authorizes no additional experiment. See [`../evidence/three_pass_review_20261027.md`](../evidence/three_pass_review_20261027.md) for the source/code/release review record.
