# KANLERGEMSDOE2

## Project charter — read this before every project session

This is the durable starting brief for this repository. It captures the requirements from the project request so that future work stays aligned, auditable, and safe. The current repo initially contained only this README; the reviewed status and current decision are in [`docs/EXECUTIVE_SUMMARY.md`](docs/EXECUTIVE_SUMMARY.md).

### Mission and values

Build a scientifically defensible, auditable workflow for the DrivenData DOE GEMS Prize Challenge: detect faults not already represented in the public catalogue, produce a competition-format GeoTIFF only when validated, and make the evidence and download/submit decision obvious. Prioritize **Maximize P(Win)** and **Own the Outcome**: make decisions from evidence, report failures, and do not claim a win, score, or scientific discovery that has not been measured.

The competition target is **faults** as structural indicators of geothermal resources; it is not a direct geothermal-vent-location task. A fault proxy is not proof of permeability, heat, or a viable geothermal reservoir.

### Non-negotiable research and submission gates

1. **Stay in the assigned method lane.** Before creating or placing a candidate, compare its prediction surface against every registered raster. If absolute rank correlation exceeds `0.90`, or more than `70%` of candidate dots lie within `3 px` of a registry raster's dots, record a duplicate/lane failure and stop. Check again on final dots.
2. **Reuse the shared template.** Use its cached feature stack, `evaluate_holdout.py`, and `submission_writer.py`. Do not create a private fork or rebuild tools. If a shared tool is wrong, fix it in the shared template and report the change. This repository currently does not contain the template, feature cache, holdout evaluator, or writer; see the executive summary. Do not silently substitute tools from another project.
3. **Spatial holdout before any slot.** Hide whole fault segments with a buffer. Derive every catalogue-based feature only from visible faults; mask visible faults pixel-exactly. Score pooled DTI with `alpha=0.2`, `beta=0.8`, and the official `300 m` triangular kernel. A candidate must beat the current holdout best before it is even considered for a submission slot. The selector/promotion step is separate and subject to the competition's weekly cap.
4. **Leakage canary.** Test each feature alone on the holdout before trusting it. AUC above `0.90` is leakage until disproven.
5. **Truthful score labels.** Every performance value must be explicitly `HOLDOUT-DTI` (evaluator version, withheld-positive count, 95% CI) or `ORGANIZER-CONFIRMED` (copied from an exact submission-page receipt). A projection is never a score. Historical values without a receipt must be called unverified owner reports, not leaderboard facts.
6. **Unique artifact only.** Never copy a prior submission as a candidate. Historical rasters may be inspected for education/audit, not reused. A final artifact must pass the surface and dot uniqueness gates against the registry and all requested GEMSDOE sites.
7. **Competition-format validation.** The official problem page specifies a single-band `float32` GeoTIFF on the matching EPSG:32611, 100 m grid/bounds/transform, predictions in `[0,1]`, and null/NaN outside the study bounds. Validate the whole raster and the in-footprint values before publishing any download. A passing local validator is not an organizer acceptance receipt.
8. **Bound the work.** At most three preregistered experiments or two hours for a campaign. Keep a run card for every result, including negative results. Do not choose a submission in the research step.
9. **Sources and provenance.** Prefer free, official sources. Link each dataset/paper to the authoritative record, preserve retrieval/check timestamps and hashes, distinguish data availability from successful retrieval, and flag gaps. Never request or store DrivenData credentials in chat or the repository.
10. **No false download affordance.** A front page must say plainly whether a TIF exists and whether it is OK to submit. If a candidate fails or cannot be validated, say **DO NOT SUBMIT** and do not offer a misleading download button.

### Starting-point source links

- [Competition overview](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Official problem description, metric, and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [About / additional resources](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)
- [Competition data page (login required)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [Public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [Organizer's reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [INGENIOUS project](https://gbcge.org/current-projects/ingenious/)
- [Submission rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [EPSG:32611](https://epsg.io/32611)

### Session-start checklist

- Read this charter and [`docs/EXECUTIVE_SUMMARY.md`](docs/EXECUTIVE_SUMMARY.md) first.
- Check the actual state of `data/`, the shared template, feature-cache receipts, holdout scripts, and registry; never assume a prior session's files are present.
- Refresh the official leaderboard and source-availability feed with timestamps. Do not equate another team's public score or an old owner-reported score with a local holdout result.
- Preregister at most three experiments, run feature-alone leakage checks, and stop on a duplicate/lane failure.
- Only after a winning holdout, uniqueness, and format gate should a candidate be eligible for the separate selector. The selector—not the research report—must decide whether it is OK to submit.

## Current review outcome

As of the review documented in [`docs/EXECUTIVE_SUMMARY.md`](docs/EXECUTIVE_SUMMARY.md), this repo has no competition inputs, cached feature stack, shared holdout/evaluator/writer, or generated candidate TIFF. The requested prior-site TIFF comparison was performed as an audit only; it showed the focus-site historical winners fail the requested uniqueness threshold against one another. **There is no file in this repository that is approved to download or submit.** The appropriate verdict is negative, not a fabricated projection or a format-only TIFF.
