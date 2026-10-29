# Official sources and access status — GEMS Prize (DOE) — 2026-10-29

This note stores research/knowledge drawn from official sources, as inspected and
recorded in this repository. No page was fetched in this session; the claims below
are taken from the committed record (registry/official_sources_20261027.json,
evidence/, knowledge/) and remain as recorded. Nothing here is an organizer
receipt, an organizer score confirmation, or authorization to submit.

## Official sources on record

| id | Source | URL | What it establishes | Access status |
|----|--------|-----|---------------------|---------------|
| OS-1 | GEMS Prize problem description (metric, submission format) | https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ | Distance-weighted Tversky metric, alpha=0.2 beta=0.8; triangular kernel R=300 m (3 px at 100 m); submission is float32 single layer, values in [0,1], EPSG:32611, 100 m, same bounds as training data; data outside bounds is null or nan | Public page; recorded quote and irregularity (NaN-vs-finite exterior convention not established by this sandbox) |
| OS-2 | GEMS Prize Official Rules (PDF, September 2026) | https://docs.nlr.gov/docs/fy26osti/96647.pdf | Competition rules; three submissions per week (as cited in the committed record) | Public PDF |
| OS-3 | DrivenData GEMS reference solution | https://github.com/drivendataorg/gems-prize-reference-solution | Official reference implementation | Public repository (github.com) |
| OS-4 | USGS 3DEP (terrain source) | https://www.usgs.gov/3d-elevation-program | Official terrain/elevation source | Public catalog |
| OS-5 | DOE Geothermal Data Repository submission 1391 | https://gdr.openei.org/submissions/1391 | Cited for 2 m temperature probes, wells/springs (thermal-transport hypothesis) | Public catalog; bytes not authenticated in this checkout |
| OS-6 | USGS GeoDAWN airborne magnetic and radiometric surveys | https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and | Cited for TMI, radiometric K/Th (alteration-edge hypothesis) | Public catalog; bytes not authenticated in this checkout |
| OS-7 | NASA OPERA | https://www.earthdata.nasa.gov/data/projects/opera | Cited for DISP-S1 displacement gradients (seasonal deformation hypothesis) | Public catalog; specific footprint tile/time series not in audited availability inventory |
| OS-8 | DrivenData staff clarification: known-fault masking | https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4 | Known-fault masking clarification | Public forum thread |

## In-repo records that cite these sources

- knowledge/01_focus9_gemsdoe32_phd_synthesis_20261027.md — metric contract, [0,1] error root cause and fix, score anatomy (alpha=0.2, beta=0.8, R=300 m).
- registry/official_sources_20261027.json — machine-readable source ledger with verified claims, quotes, and irregularities.
- docs/executive-summary.html, docs/submission-table.html, docs/index.html — link to OS-1/OS-2/OS-3 with the duplicate competition URL corrected (competitions/306/ once).
- research/2026-10-28_focus-nine-hypotheses.md — cites OS-5, OS-6, OS-7 with explicit "no download/availability claim is made" caveats.

## Standing caveats

- No hidden labels, organizer submission-page receipt, or authenticated competition bytes are available in this sandbox; the official data page is login-gated in the recorded audit.
- Owner-mirror hashes prove byte identity to pinned mirrors, not organizer origin.
- Nothing above establishes organizer acceptance of the zeros-outside footprint exterior convention; verify against the current authenticated sample before upload.
