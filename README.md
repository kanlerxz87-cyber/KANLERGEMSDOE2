# KANLERGEMSDOE2 — evidence-first GEMS submission research

**START HERE EVERY SESSION.** Read this README, [research protocol](docs/research.md), [current run card](docs/run-card.json), and [executive summary](docs/index.html) before making changes.

**Current verdict: negative / no approved submission.** The checkout initially contained only a one-line README. The current branch now includes commit-pinned third-party research snapshots and a fail-closed format checker, but no competition rasters, local feature cache, complete current registry, or active shared template pipeline. No new TIFF has been generated, zero experiments were run, and zero competition slots were used.

## Standing user brief (operational transcription, not the full verbatim chat)

The full original request remains in the Arena conversation; this is a faithful operational summary rather than a claim to preserve every repeated paragraph. Focus on GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36. Produce clear per-site executive summaries, obvious file/download status, estimated-score evidence and uniqueness status. Generate a genuinely unique competition TIFF only after scientific validation; never copy/rename a prior submission. Clearly distinguish HOLDOUT-DTI (version, withheld positives, 95% CI), organizer receipt-confirmed scores, owner reports and projections. Do not invent data, scores, sources or validation.

Parallel-run protocol: stay within the assigned single-method lane. **No method lane was actually supplied in this request.** Stop if rank correlation exceeds 0.90 or >70% of dots are within 3 pixels of any registry raster; test surfaces before placement and final dots. Reuse the shared cached stack, evaluate_holdout.py and submission_writer.py; fix shared tools upstream, never maintain private executable forks. Use whole-segment buffered hide-and-recover, visible-only catalogue features, pixel-exact visible-fault masking, pooled DTI alpha 0.2/beta 0.8 with a 300m triangular kernel. Test each feature alone; AUC >0.90 is leakage until explained. End with a JSON run card including mechanism, named non-fault mimic, holdout + CI, registry comparisons, SHA256, validator results, name/note <=140 characters and promote/negative verdict. Maximum three experiments or two hours. Promotion is a separate selector step under the authenticated weekly cap; do not upload automatically.

Before implementation, rank 3–5 geological hypotheses by expected benefit/cost, naming layers, physical transforms, off-catalogue mechanism, difference from existing work and confounders. Verify external official/free data availability before claiming viability. Freeze spatial evaluation and beat current holdout best before spending any slot. Research faults as a proxy for geothermal permeability, not proof of vents. Maintain an auditable source table with links, honest limitations and a clean GitHub Pages executive-summary/submission guide. Validate single-band TIFF values [0,1], finite footprint and exact organizer CRS/shape/transform. Do not require human raster inspection as a substitute for automated checks. Review in three passes; open and merge a PR only after testing. No secrets in chat or Git.

## Core values

**Maximize P(Win):** weigh risks and evidence; do not spend scarce leaderboard slots on unvalidated ideas. **Own the Outcome:** own the end-to-end result; treat negative experiments as useful deliverables, fix defects and document limitations. A truthful blocked state is better than a fabricated winning score.

## What exists now

- [Nine-site executive summary](docs/index.html), [submission guide](docs/submission.html), [ranked research plan](docs/research.md), [live-source irregularity notes](docs/research/source-audit.md), and [three-pass review log](docs/research/review-log.md).
- Commit-pinned public repository snapshots and tree inventories in `docs/evidence/`; third-party evidence is not organizer confirmation. Executable-looking files under evidence are **audit snapshots**, not a copied training pipeline.
- Fail-closed evidence gate: `scripts/promotion_gate.py`. This checks reported evidence structure; it does not itself run raster validation, prove provenance or authorize a slot. `scripts/validate_submission.py` checks an actual candidate against an organizer template for exact grid, EPSG:32611/100m, single float32 band, footprint mask, and finite `[0,1]` values. It does not assess science or uniqueness.
- Reproducible static builder and source-audit script. Refresh with `python scripts/audit_sources.py` (needs configured `gh`) then `python scripts/build_site.py`.

## Local checks / preview

```sh
python -m pip install -r requirements-validation.txt
python -m unittest discover -s tests -v
python scripts/build_site.py
python -m http.server 8000 --bind 0.0.0.0 --directory docs
```

Validate a candidate only after a scientific result and using the real sample template:

```sh
python scripts/validate_submission.py --template data/sample_submission.tif --candidate candidate.tif --json candidate-audit.json
```

## Limitations / next session

The competition data endpoint redirected to DrivenData login during this review. No authenticated organizer receipts or current submission cap are available in this checkout. Shared data/cache and complete registry are not placed locally; a data restore receipt in another repository is not proof of local availability. The claimed GPU-only training requirement is contradicted by the official reference README's CPU option. The prompt's historic leaderboard values conflict: the official public leaderboard displayed 0.4437 on 2026-10-26 when retrieved (a dated public snapshot, not a private/final result or receipt). Recheck the official page before using any leaderboard value. A per-site source conflict audit is linked above.

Resolve lane and dense-lattice registry conflict, verify template/cache/input hashes and semantic band metadata, then execute a maximum-three-experiment fold-local comparison. Don't begin by optimizing against the public score ledger. There is no scientifically justified new raster or score estimate yet.
