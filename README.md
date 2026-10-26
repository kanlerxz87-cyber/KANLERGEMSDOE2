# KANLERGEMSDOE2 — evidence-first GEMS submission desk

**Start every session here, then read `research/run_card.json`, `research/hypotheses.md` and the evidence manifests.**

## Current decision — 2026-10-26 UTC

**DO NOT SUBMIT. No new submission TIFF is approved or generated in this session.**

The original checkout was a 16-byte README, not the trained project described in the request. We restored nine historical reference rasters strictly for education/audit, retrieved 44 pinned text sources, and vendored the GEMSDOE24 shared tools byte-for-byte using GEMSDOE36's recorded pins. No detector experiment or competition submission was run. There was no supplied exclusive method paragraph. A correct negative result is preferable to a fabricated high-scoring file.

- [Executive decision desk](docs/index.html) — per-site table, historical filenames, eligibility, unavailable estimates, provenance.
- [Submission guide](docs/executive-summary.html) — release gates, range error and upload instructions.
- [Hypotheses](research/hypotheses.md) — four ranked, untested mechanisms with layers, signatures, non-fault mimics and feasibility.
- [Run card](research/run_card.json), [raster audit](research/raster_audit.json), [source manifest](research/source_manifest.json).
- Expected Pages address after deployment: https://kanlerxz87-cyber.github.io/KANLERGEMSDOE2/

### Verified local measurements (RASTER-AUDIT, not scores)

All nine selected historical whole-grid-finite rasters match the pinned peer-mirrored sample's CRS, shape and geotransform and contain only finite values in [0,1]. All 72 directed cross-site comparisons fail the requested uniqueness rule (>0.90 rank correlation OR >70% of positive pixels within 3 pixels). GEMSDOE25 and GEMSDOE30 are pixel-identical inside the footprint. GEMSDOE32 vs GEMSDOE36 has rho 0.9843 and 100% directional overlap. This does not certify any surface or the full registry: this audit covers only the selected historical final rasters.

The reported 0.2778 is an **unverified owner report**, not an organizer receipt. GEMSDOE32's peer records explicitly say so and mark its newer headline H47 artifact negative. No reliable new leaderboard estimate exists. The claimed overall best values 0.3195 and 0.4413 conflict and neither is freshly verified.

## Owner's standing project brief (condensed, not a verbatim transcript)

The request in this session is the source of these requirements. This operational brief preserves its actionable constraints; it does not claim to reproduce the entire repeated original prompt.

1. Focus on GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36. Explain the highest historical submissions, especially GEMSDOE32 H33 B=2. Produce a clear per-site executive table with file, estimated score if defensible, uniqueness and an obvious download/submit decision.
2. Generate a genuinely new single-band GeoTIFF only from a justified, independently validated strategy. Never rename or copy an old submission as a new one. All predictions must be finite in the footprint and in [0,1], with competition-matching CRS, shape and transform. Prefer strict whole-grid-finite output to avoid the reported portal range error. Use a unique name and a note of at most 140 characters.
3. Parallel protocol: remain in the assigned single-method lane. Stop on rank correlation >0.90 or >70% dot overlap within 3 pixels versus ANY registry raster, both before placement and after. Reuse cached features and shared evaluator/writer. Report upstream bugs rather than privately forking. Missing lane/template authority is a blocker, not permission to claim a lane.
4. Hide whole fault segments with a buffer; derive catalogue-based features from visible faults only; mask visible faults pixel-exactly. Evaluate pooled distance-weighted Tversky with alpha 0.2, beta 0.8 and 300 m triangular kernel. Run every feature alone through a leakage canary; AUC >0.90 is leakage until demonstrated otherwise.
5. Label results HOLDOUT-DTI with evaluator version, withheld-positive count and 95% CI, or ORGANIZER-CONFIRMED with an authentic receipt. Do not call a projection a score. Supplied owner reports must remain explicitly unverified rather than being relabeled confirmed.
6. Before implementation, preregister 3–5 geological hypotheses: layers, physical transform/signature, rationale for unmapped faults, difference from existing work, non-fault mimic, expected qualitative benefit and cost. Verify official external-data obtainability before declaring a new-data idea viable.
7. Validate the top assigned candidate against the frozen current holdout best before any weekly slot. Maximum three experiments or two hours. Slot promotion is a separate selector step within the authenticated page's weekly cap. Do not auto-submit.
8. End with one JSON run card: hypothesis, mechanism, named non-fault mimic, HOLDOUT-DTI + CI, registry correlation/overlap, TIFF SHA-256, validator outputs, name/note and promote/negative. Negative outcomes are deliverables.
9. Research official, free public sources. Store provenance, uncertainty, scientific reasoning and reproducible evidence. Distinguish fault prediction from confirmed geothermal vent discovery. No hallucinated literature, receipts, scores, hidden truth or data access. Work autonomously within available permissions, reporting blockers honestly.
10. Provide a clean GitHub Pages site, executive-summary submission guide and clear download status near the top. Automate checks rather than requiring subjective human inspection. Keep freshness explicit; do not call a dated snapshot a live feed.
11. Perform three passes: implement/verify; find and fix bugs/edge cases; recheck against requirements. Create a PR and merge it when checks permit; record remaining work.
12. Core values: **Maximize P(Win)** by weighing tradeoffs and evidence; **Own the Outcome** end-to-end, including negative results and failure disclosure. Winning cannot be guaranteed by local proxy metrics.

## Reproduce

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
# Uses GitHub API only. No DrivenData credentials needed. Restores historical references,
# shared tools, and the mirrored sample/catalogue; does NOT restore training feature stacks.
python scripts/restore_audit.py
.venv/bin/python scripts/compare_registry.py
python scripts/build_site.py
.venv/bin/python -m unittest discover -s tests -v
python -m http.server 8000 --bind 0.0.0.0 --directory docs
```

`python scripts/audit_sources.py` re-fetches the already pinned tree blobs, NOT a live leaderboard. Tree snapshots were retrieved on the audit date. Updating to newer tree revisions is a separate, reviewable change; do not silently mix a new registry with old measurements.

Historical rasters are ignored under `data/`. Committed evidence includes hashes and metrics, not training data. The source manifest links peer data to pinned GitHub bytes, **not** to independently authenticated organizer files. The mirrored sample is used for geometry/footprint only; its finite values are not model predictions or new hidden-fault truth.

### Shared tooling

`vendor/template/` contains unchanged peer code; tests enforce every recorded SHA-256. The canonical choice is provisional: GEMSDOE36 pins GEMSDOE24, while peer evidence says GEMSDOE31 pins 57GEMSDOE. Resolve authority before comparing experiments. Use `gems.holdout.SegmentHoldout` and `gems.submission.write_submission(..., outside='zero')`, not a private metric implementation. The strict local `scripts/validate_raster.py` is an additional range/grid checker, not a competing writer or scientific evaluator. Install `requirements.txt` in the project virtual environment before running any canary or raster checks; the shared `make_note` limit is looser than this protocol, so enforce 140 characters independently.

## Limitations and exact next steps

- No exclusive method paragraph, complete registry surface set, frozen best fold predictions or restored feature cache is available locally. Establish those before any experiment; do not perturb an old raster merely to evade novelty.
- Official DrivenData pages, USGS, NLR PDF, Dropbox and other non-allowlisted sources cannot be fetched from this environment. No authenticated DrivenData session is present. A public hash-pinned mirror is integrity evidence, not authentication of the official origin.
- Retrieve features using peer cache manifests once the method lane is known; verify band names, coverage and hashes. GPU is optional, not universally required: the official reference README explicitly supports CPU-only use.
- Run candidate canaries, pre-placement novelty, fold-local hide-and-recover and paired baseline comparisons. Publish exact CI/count/version and full-registry final-dot checks. If any gate fails, leave submission disabled.
- An authenticated selector must check rules and remaining weekly allowance. Save the exact-byte receipt after upload. This site never submits on its own.
- No new high-scoring TIFF, defensible leaderboard estimate or official literature review was produced. These unmet goals are explicit rather than disguised behind a format-only test.

See [three-pass review](research/review.md) for the defects found and verification scope.

## Concurrent-main integration warning

Before merge, main advanced to `80d3c57` with a purportedly approved blind-basin TIFF. Code review found synthetic layers, a placeholder leakage canary, random-draw confidence intervals, a hard-coded selector, and a waived full-registry stop rule. Its authorization is withdrawn; the original code, numerical assertions and TIFFs are preserved under `research/quarantine/`, outside Pages. The current decision card supersedes those historical claims. This is a newly discovered integration issue, not evidence that those unsupported holdout figures were reproduced.

---

## Legacy E1 record — withdrawn and not reproducible here
Earlier branch artifacts describe an E1 model and report local holdout, canary, uniqueness and score-projection numbers. Those records do not establish a valid current result under this project's required shared, segment-blocked evaluator: the underlying feature/label inputs and cached outputs are not present in this checkout, and some supporting claims were subsequently found unable to substantiate promotion. Therefore none of those numbers is reported here as a verified HOLDOUT-DTI, projection, or score. The TIFF and old evidence remain only in `research/quarantine/` and `evidence/` for traceability; they are not published as download links and must not be submitted. `docs/lane-e1-xg-hgb.html` is a withdrawal notice retained to prevent stale Pages URLs from appearing to authorize an upload. This withdrawal does not establish any replacement candidate.
