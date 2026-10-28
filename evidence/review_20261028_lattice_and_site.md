# Review, 2026-10-28 — negative, no slot used

## Pass 1 — exact-byte checks

Restored just the pinned owner-mirror labels, sample, spacing-5 lattice and nine focus-site rasters using `restore_data.restore_entry` and `restore_focus_sites.py`; all hashes matched their checked-in manifests. Then ran `scripts/replay_release_review.py --data-dir data/review_current --out evidence/review_20261028_replay.json`. This reopened the actual TIFFs and independently reproduced the previous footprint-specific lower bound and G25→G32→G36 geometry. The HPTR file is finite in [0,1], single-band float32 and matches the owner-mirror CRS/shape/transform, but 37,640/37,654 of its dots fall within three pixels of the lattice; it fails the user's rule. The bound applies to any 37,654 distinct in-footprint dots, not arbitrary budgets. The output does not establish organizer origin or acceptance.

## Pass 2 — critical review and correction

Identified conflicting claims in the README, executive summary, generated pages and machine-readable feed: a proxy comparison was described as beating a reported leaderboard score; SGMC-CAL was labeled as measured HOLDOUT-DTI although its inferred hidden prevalence is unverified; non-lattice-only overlaps were presented prominently despite the literal rule. Replaced the public promotions with a fail-closed archive notice. Preserved previous documents under `evidence/superseded/` as historical, not authoritative. Set the unsupported feed claim and unreviewed metrics to null, not false or a fabricated estimate. Added regression tests. No archived experimental evidence was rewritten.

## Pass 3 — recheck against request

The nine-site table includes exact research filenames, reported (not organizer-confirmed) scores, directional overlap and a do-not-submit decision. The reported GEMSDOE32 value is highest of the listed nine, but no hidden-label attribution is possible. The generated dashboard and submission guide make the negative decision explicit. Existing ranked hypotheses and source catalog remain linked; this session did not perform the requested new experiments because the literal preflight forces failure at the frozen budget. It did not produce a unique, validated TIF, estimate its leaderboard score, use a slot, or verify organizer receipts. The present request refers to a lane paragraph but does not designate one; the old HTCADS registration is historical. A new run requires an explicit resolution of the conflicting novelty rule and a specified lane, not an invented exemption.

Verification: `python -m compileall -q src scripts tests`, `python -m pytest -q`, `python scripts/evaluate_holdout.py --verify-kg2` (archive metadata only), and `python scripts/build_site.py`. Official reference-solution [README](https://github.com/drivendataorg/gems-prize-reference-solution) was fetched via the GitHub API; it instructs download from the competition site and supports CPU as well as GPU, so the prior blanket assertion that a GPU is strictly required is not established by that source. DrivenData, NLR, USGS and Dropbox hosts cannot be reached directly under this sandbox's outbound allowlist; existing source links are provided for review, not newly verified here. The leaderboard snapshot is dated and Pages remains legacy-configured; no live refresh was established.

Next: resolve the rule and lane; restore and authenticate official data/template; verify full registry and account quota; run per-feature canaries, fold-safe buffered segment holdout and paired baseline, then an independent selector. Do not upload an old raster as a workaround.

### Concurrent-main integration

A second session independently published a separate preflight and numeric-inspection review while this branch was open. Both reviews are retained; their results agree on the lattice stop. The generated site preserves the other session's top-of-page correction and omits unreplayed proxy metrics from the status feed. After resolving conflicts, the combined suite passed **122 tests**, with 14 Rasterio pending-deprecation warnings.

A further concurrent main update supplied a refreshed audit, validator receipt and stale-feed handling. These were retained and the combined test suite passed **124 tests** (14 Rasterio pending-deprecation warnings).
