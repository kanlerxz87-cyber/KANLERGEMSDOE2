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

The reported 0.2778 is an **unverified owner report**, not an organizer receipt. GEMSDOE32's peer records explicitly say so and mark its newer headline H47 artifact negative. Leaderboard conflict resolved 2026-10-26: the organizer-published public board then read 0.4437 (#1) — 0.4413/0.3195 were stale snapshots (`evidence/leaderboard_snapshot_20261026.json`). Byte autopsy addendum: champion dots ⊂ GEMSDOE31 best ⊂ D2.8 exactly; near-catalogue dot share 14.6%→6.3%→0.0% tracks 0.2600→0.2708→0.2778; fixed-mask hide-recover anti-ranks that ladder (B-gate artefact — gate only on fold-local emission).

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

`vendor/template/` contains unchanged peer code; tests enforce every recorded SHA-256. The canonical choice is provisional: GEMSDOE36 pins GEMSDOE24, while peer evidence says GEMSDOE31 pins 57GEMSDOE. Resolve authority before comparing experiments. Use `gems.holdout.SegmentHoldout` and `gems.submission.write_submission(..., outside='zero')`, not a private metric implementation. The strict local `scripts/validate_raster.py` is an additional range/grid checker, not a competing writer or scientific evaluator. Shared canary needs scikit-learn, which is not required for this audit and is not installed here. The shared `make_note` limit is looser than this protocol; enforce 140 characters independently.

## Limitations and exact next steps

- Uniqueness registry here = 10 rasters (9 focus bests + E1), NOT every raster on the ~100 prompt sites (IR-EXT-02). Restore the full registry byte-wise before claiming a full-registry uniqueness certificate; never perturb an old raster merely to evade novelty.
- No organizer receipt exists for any new or historical file; all historical scores remain OWNER-REPORTED. No authenticated DrivenData session here; hash-pinned mirrors are integrity evidence, not official-origin authentication. DrivenData public pages + community clarifications were read 2026-10-26 via the fetch tool; sandbox bash egress remains github/pypi/npm only (USGS FDSN verified unreachable from bash).
- Next lanes (ranked in `research/preregistration-ext-corrob.md`): (1) full-footprint GPU segmentation (Tversky loss) fixing reference tile-skip blind spots; (2) USGS ANSS/FDSN seismicity lineaments — fetch the catalog on an unrestricted machine first; (3) radiometric texture displacement (uint8 cache limits); (4) raw-3DEP drainage offsets. Each needs its own pre-registration + 3-experiment budget and must beat E1 OOF 0.1252 with a positive paired CI before any slot.
- An authenticated selector must check rules and remaining weekly allowance. Save the exact-byte receipt after upload. This site never submits on its own.
- Two honest negative lanes (E1, EXT) now bound what this data + CPU methods deliver (~0.22 MODEL ESTIMATE). Beating 0.2778 — let alone the 0.4437 public lead — needs a categorically stronger detector (GPU segmentation and/or expert-style 1 m mapping), not another emission tweak of these surfaces.

See [three-pass review](research/review.md) for the defects found and verification scope.

## Concurrent-main integration warning

Before merge, main advanced to `80d3c57` with a purportedly approved blind-basin TIFF. Code review found synthetic layers, a placeholder leakage canary, random-draw confidence intervals, a hard-coded selector, and a waived full-registry stop rule. Its authorization is withdrawn; the original code, numerical assertions and TIFFs are preserved under `research/quarantine/`, outside Pages. The current decision card supersedes those historical claims. This is a newly discovered integration issue, not evidence that those unsupported holdout figures were reproduced.

---

## Parallel lane E1 XG-HGB — merged as negative deliverable (2026-10-26)
A separate lane (supervised 47-channel HistGradientBoosting incl. magnetic×gravity cross-gradient boundary; spacing≥3 px, B=2) was merged after main's evidence-first restructure. Its TIF now lives at `research/quarantine/prior-docs/downloads/kanler-e1-xg-hgb-37654d-20261026T214616Z-7ab68c3efd-allfinite.tif` (quarantine = research only, consistent with this README's DO NOT SUBMIT decision). Results: quadrant-OOF HOLDOUT-DTI 0.1252 [0.097,0.157] (56,464 withheld), canary max AUC 0.580, uniqueness vs 9 focus bests max |ρ| 0.089 / max 3-px overlap 40.9%, format PASS — but SGMC HOLDOUT-DTI 0.0752 vs champion 0.0961, MODEL ESTIMATE ~0.22 < 0.2778 → **verdict negative; do not submit**. Lane page: `docs/lane-e1-xg-hgb.html`; card: `evidence/run_card_e1_xg_hgb.json`. This does not change the current decision above.

---

## Lane KANLER-EXT-CORROB — negative deliverable (2026-10-26)
Pre-registered (`research/preregistration-ext-corrob.md`) before running. Exp1 CORROB (label-free geometric-mean corroboration: OOF 0.0792; clean SGMC 0.1015 vs champion 0.0961 but callable hide-recover 0.0499 vs proxy 0.0992 — split), Exp2 MCSUP (catalogue∪SGMC positives @37,654: OOF 0.1181), Exp3 EMIT (budget sweep → MCSUP @44,090: OOF **0.1264 [0.098, 0.154]**, 56,464 withheld; SGMC-OOF fold-local 0.1337; canary max AUC 0.580; uniqueness vs 10 rasters max |ρ| 0.101 / max 3-px overlap 39.1%, 26.8% vs champion; format PASS). Since OOF only ties E1 (0.1252) and MCSUP's flattering global SGMC (0.3288) / hide-recover (0.1598) are training-contaminated (IR-EXT-01, excluded), the headline MODEL ESTIMATE is **~0.22 [0.18, 0.26] < 0.2778 → verdict negative**. Unique file (research download only): `docs/downloads/kanler-ext-mcsup-44090d-20261026T223149Z-5553e712b0-allfinite.tif`, name `KANLER-EXT-MCSUP-44090D-5553E712B0`, sha256 `06c56b9a…ae666`. Card: `evidence/run_card_ext.json`; review: `research/review-ext-lane.md`; lane page: `docs/lane-ext-corrob.html`.
