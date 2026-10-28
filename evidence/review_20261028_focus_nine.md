# Focus-nine review supplement — 2026-10-28 UTC

This is the focus-site and hypothesis supplement to the repository-wide three-pass integrity review at [`review_20261028.md`](review_20261028.md). The repository-wide review supersedes historical claims about independent holdout replay and includes newer exact-byte checks.

## Pass 1 — inspect and implement

- Read the repository working contract, README standing prompt, frozen HTCADS-K2 preregistration, current run card, release audit, focus-site evidence, and current site generator before editing.
- Added a dated focus-nine hypotheses record with four ranked, method-constrained ideas. The ranking is qualitative; it makes no unsupported numerical DTI forecast and specifies layers, target signature, unmapped-fault rationale, non-fault mimics, prior-work distinction, source/data availability, cost, and a holdout-first path.
- Updated the executive-summary generator so all nine historical focus entries show a research-only file link, USER/OWNER-REPORTED score, unavailable leaderboard-score estimate, focus-peer 3-px overlap, local whole-array/exterior check, and explicit DO NOT SUBMIT decision.
- Updated the summary lead to state the exact 37,654-dot novelty preflight contradiction and that no TIFF, holdout result, leaderboard estimate, or slot use occurred in this review.
- Updated the run card for this review while preserving `negative`, `holdout_dti: null`, `raster_sha256: null`, and `submission_name: null`.

## Pass 2 — adversarial review and corrections

- Reviewed the table generator's evidence binding: it checks the local download SHA-256 against the pinned focus-site record before rendering. It does not convert reported live scores or holdout values into a leaderboard estimate.
- Retained the per-row “estimate unavailable” status rather than extrapolating from HOLDOUT-DTI, LLI, or rounded reported scores. All nine site scores remain USER/OWNER-REPORTED; no submission receipt is present in the reviewed evidence.
- Added tests for the nine sites, negative gate, absence of a fabricated estimate, four-hypothesis slate, and no-candidate Run Card.
- Initial targeted tests exposed two mismatches between test expectations and actual output precision/wording (`82.34%` display and “novelty gate”). Corrected the tests to match the rendered precision and the Run Card's actual status. No production behavior was weakened to make tests pass.
- The mandatory pre-placement gate fails before fitting: the registered lattice lower bound is 31,005 / 37,654 = 82.3418%, exceeding the literal 70% maximum. Therefore no holdout or leakage canary was run on a new candidate; doing so would violate the stop order.

## Pass 3 — final verification

- Rebuilt seven fail-closed pages with `python scripts/build_site.py` successfully.
- Ran the full suite: **114 passed, 8 warnings**. Warnings are Rasterio/Affine pending-deprecation warnings from the existing format-gate tests.
- `python -m compileall -q src scripts tests` passed.
- `python scripts/evaluate_holdout.py --verify-kg2` verified the archived raster hash/metadata and reproduced the recorded historical HOLDOUT-DTI value in its report; the command explicitly does **not** replay the holdout or authorize upload.
- `git diff --check` passed.
- Reviewed official manual-review links embedded in the pages and note: DrivenData problem/rules/reference solution, USGS GeoDAWN/3DEP, DOE GDR 1391, and NASA OPERA. The official data page/login, owner-mirror authentication, and footprint-specific OPERA availability remain limitations; no claim of fresh external-data acquisition is made.

## Final decision and limitations

**Negative. Do not submit any file in this repository. No new TIF was created.** The 0.2778 GEMSDOE32 figure is the highest value in the supplied focus list, but it is USER/OWNER-REPORTED, not organizer-confirmed; its raster is not spatially unique within the focus set. Geometric pruning lineage supports a plausible false-positive-reduction mechanism but cannot prove why the score occurred. The current run has no calibrated leaderboard estimate. Resolve the literal registry-rule conflict, authenticate the organizer data/template, and replay the shared holdout before any future selector considers a weekly slot.
