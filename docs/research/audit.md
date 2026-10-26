# Audit, explanation and decision

**Decision: no K2 candidate TIFF was generated or approved.** This is a negative, pre-placement K2 result, not a holdout result and not a new submission. The complete machine-readable [run card](../../evidence/run-card.json), [geometry receipt](../../evidence/lattice-feasibility-20261026.json), and [nine-file audit](../../evidence/focus-audit-20261026.json) contain the actual scope and missing fields.

## What was checked

The repository started with only a short README; there was no previous local pipeline or cache. The pinned public GEMSDOE33 template and all 17 of its hash-pinned owner-mirror inputs were restored outside Git. The template's source and dependencies are identified in `scripts/reproduce_audit.sh`. A matching SHA-256 verifies the owner mirror, **not** that its bytes are the organizer's original files or that redistribution/competition rights are established. The official data and submission pages redirect to login; no DrivenData upload or weekly quota check was made.

Nine source-pinned historical TIFFs were independently fetched, hash-checked, opened on the mirror template grid and compared as binary in-footprint arrays. The measured pairwise dot fractions in the audit are **directed**: the denominator is the dots in the row candidate. All nine historical rasters have more than 70% of their dots within three pixels of at least one other historical focus-site raster. In addition, GEMSDOE25 and GEMSDOE30 have exactly identical in-footprint prediction arrays, despite different file encodings. These are archived research references, not recommended new submissions. Original pre-placement surfaces and the full, changing parallel registry were not audited by this nine-file comparison.

The historical values in the user brief are owner-reported claims. No submission-page receipt linking the named uploaded bytes to any claim is available here. A value from a different holdout protocol is not comparable to an organizer result or a calibrated forecast. The user's two stated leader values conflict; the [official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) is the appropriate place to check current standings. The site does not automatically monitor or copy it in light of [DrivenData's terms](https://www.drivendata.org/termsofuse/).

## Why the reported GEMSDOE32 result may have improved

For the pinned mirror rasters and catalogue, the following is **directly reproducible pixel algebra**, not an inference about hidden truth:

* GEMSDOE25 D2.8 contains 44,090 positive cells. Its in-footprint values equal the pinned GEMSDOE30 D2.8 values.
* Remove D2.8 dots at Euclidean catalogue distance ≤1 pixel: 3,891 dots are removed, and the remaining mask equals the GEMSDOE31 historical mask exactly.
* Remove D2.8 dots at distance ≤2 pixels: 6,436 are removed, leaving 37,654; that mask equals GEMSDOE32 B2 exactly. Relative to the first prune this removes a further 2,545 dots.
* The audited GEMSDOE36 mask contains every GEMSDOE32 B2 dot and adds 1,200 others. These facts do not authenticate score/file associations.

The official [distance-weighted Tversky metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric) is `S = T / (T + αF + β(G − T) + ε)`, where `T` is weighted true-positive credit, `F` is weighted false-positive mass, `G` is the number of positive truth pixels, `α = 0.2`, `β = 0.8`, and the linear distance kernel has 300 m support. Dot thinning can reduce false-positive mass while preserving some nearby truth credit. If pruning removes little weighted true-positive credit but appreciably reduces false-positive mass, the index can increase. That is a plausible mechanism for the **owner-reported** progression, not proof of why it occurred.

More precisely, with `D = T + αF + β(G − T) + ε`, removing weighted credit `δT ≥ 0` and weighted false-positive mass `δF ≥ 0` improves the ratio precisely when `δT × [1 − (1 − β)S] < αS × δF`. The actual `δT` and `δF` against organizer-held labels are unavailable. Existing-fault pixels are masked pixel-exactly according to [DrivenData staff](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4), but new faults **can** occur within 300 m of a mapped fault; a proximity exclusion can therefore lose genuine credit. Do not infer causality, optimal spacing, or a winning forecast from these historical claims.

Can a new approach exceed the reported 0.2778? **Possible in principle, unproven here.** We have neither an organizer-confirmed receipt for that claim nor independent hidden labels nor a calibrated mapping from mapped-fault holdouts to leaderboard scores. No current candidate has been evaluated or demonstrated to beat it.

## Parallel E1 artifact: a retrospective lattice check

While this lane was running, other sessions merged research into `main`. One E1 raster was already quarantined with a negative verdict; its original run card excluded calibration lattices from its nine-file registry comparison. We re-opened the archived file at main commit `4ff78870f8e9d92520a3d0e74ca7f7a388e488ba` (SHA-256 `8e35f810f2426f6e70e68f1075439352b363ba1059b40d6237ed306275f5b154`) on the pinned mirror footprint. **37,395 of its 37,654 positive dots (99.31%)** lie within three pixels of the same registered lattice. This independently measured directed overlap exceeds the 70% stop, even though the prior nine-file comparison was below its threshold. See the [retrospective receipt](../../evidence/parallel-e1-lattice-audit-20261026.json) and `scripts/audit_archived_e1.py`.

The check covers only this lattice and the final archived raster, not E1's original pre-placement surface or the full registry. Other sessions' reported E1 holdouts and canaries were not independently replayed here. The artifact remains quarantined; no E1 TIFF is recommended or uploaded by this session. This is distinct from K2's **mathematical lower bound**, where no candidate existed.

## The geometry stop, before placement

The preregistered K2-SCALE plan fixed a 37,654-dot budget. The registered spacing-five lattice is present in the GEMSDOE32 focus registry via a GEMSDOE24 calibration path. Using the actual pinned template footprint and registered lattice (Euclidean distance, ≤3 pixels), the audit found only 6,649 footprint cells **outside** the lattice halo. For any raster with `N` distinct positive pixels, at most `B` can be outside the halo, so at least `max(0, N − B)` must lie inside it. At `N = 37,654` and `B = 6,649`, the lower bound is `31,005 / 37,654 = 82.34%`, already above the mandatory 70% threshold. This conclusion holds for **every possible arrangement** at that budget; no predictive surface or dot placement is needed to establish it.

This is not a proof that every possible smaller candidate must fail, nor a reason to remove the lattice from the registry. At most 22,163 distinct dots could satisfy this **necessary** single-lattice condition; that does not mean any such candidate would pass the other registry, holdout, canary or format gates. Do not change the budget post hoc within this stopped lane. The stop means surface rank correlation, actual dot overlap, feature AUC, withheld-positive count, HOLDOUT-DTI and CI, raster SHA-256 and validator outputs are all **not measured**, not zero and not passing. No TIFF was written.

## Official science and data sources

* [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and): airborne magnetic/radiometric data and coordinated LiDAR; the page labels the work CC0. Survey height and flight geometry may create variation in apparent signal.
* [USGS structural assessment of geothermal systems](https://www.usgs.gov/publications/three-dimensional-geologic-mapping-assess-geothermal-potential-examples-nevada-and): fault intersections/terminations and stress state are relevant to fluid flow. This supports a mechanism, not a guarantee that each anomaly is a fault or vent.
* [USGS Surprise Valley counterexample](https://www.usgs.gov/publications/structural-controls-geothermal-circulation-surprise-valley-california-a-re-evaluation): suggestive geophysical anomalies did not demonstrate a single continuous hypothesized fault.
* [DOE GDR INGENIOUS #1391](https://gdr.openei.org/submissions/1391): public CC BY 4.0 inventory includes named wells/springs, paleo features and shallow probes; individual product coverage and fitness still require verification.
* [USGS 3DEP](https://www.usgs.gov/3d-elevation-program): official free elevation data. Actual competition-region 1 m tiles were not retrieved in this environment.
* [Official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution/tree/aebe92f7c8a990f0e3443451b7a825d9afd6336b) and [official problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). External data use and sponsor sharing are subject to the [competition rules](https://www.drivendata.org/competitions/306/competition-doe-gems/rules/).

## Practical next steps

1. Resolve the user-defined literal overlap protocol versus the registered space-filling calibration lattice; do not silently exclude the lattice. Any future alternative must be explicitly authorized, preregistered and independently checked.
2. Fix the three root shared-evaluator defects documented in [irregularities](irregularities.md) **in the upstream shared template**, then pin and test the corrected commit. This checkout has read-only access to that other repository and must not maintain a private evaluator fork.
3. Obtain organizer-authenticated competition bytes and clarify external data rights; compare their grid and footprint with the owner mirror without exposing credentials. Restore genuine 1 m tiles or the exact official new products only when permitted and obtainable.
4. For a fresh authorized lane, run per-feature canaries, fold-local visible-only whole-segment hide-and-recover and same-evaluator paired confirmation; use the shared writer, re-open the exact final TIFF, check the complete current registry at both stages, and let a separate selector decide whether a weekly slot is justified.
