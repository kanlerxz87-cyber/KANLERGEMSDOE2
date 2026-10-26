# Scientific and evidence review — 2026-10-26

## Decision

**No file in this checkout is authorized or available for submission.** We attempted one preregistered research probe, used no weekly slot, and stopped at the required pre-placement duplicate check. No candidate TIFF was written; its holdout DTI, CI, hash and file-format validation are therefore **not measured**. The next session must not silently retune or resume this lane.

## What the competition actually evaluates

[DrivenData's problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) specifies fault-presence confidence, not geothermal vents. Newly mapped faults constitute initial test truth; one selected raster is scored again against an expanded expert-reviewed set. [Organizer staff](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516) say pixels corresponding to known USGS/INGENIOUS faults are excluded in both scoring rounds. The project can automate its own checks, but cannot replace the organizers' expert review.

The official distance-weighted Tversky metric uses `alpha=0.2`, `beta=0.8` and `k(d)=max(1-d/300 m,0)`. To avoid a common algebra error, let `T` be the sum over truth pixels of each pixel's *maximum* weighted prediction, `U=sum_x p(x)` and `M=sum_x p(x)*max_g k(d(x,g))`. Then `FPw=U-M`, `FNw=|G|-T`, and, because alpha + beta = 1:

```text
DTI = T / [alpha*(T + U - M) + beta*|G| + epsilon]
```

`T` is generally **not** equal to `M`, so the simplified denominator `0.2*U+0.8*|G|` is not valid in general. Adding/removing a dot can change competing maxima for many truth pixels; calculate actual marginal `TPw`, `FPw` and `FNw`. Unknown private truth makes it impossible to infer a unique decomposition or guarantee a leaderboard gain from historic scalar scores.

## Why the owner-reported GEMSDOE32 result may be strongest

The supplied **0.2778 is an OWNER-REPORTED, UNVERIFIED historical claim**, not an organizer receipt or an estimate. We independently downloaded and SHA-256-checked the public rasters and compared their decoded in-footprint pixels:

- GEMSDOE25 D2.8 and GEMSDOE30 D2.8 have identical in-footprint predictions (44,090 positive cells).
- GEMSDOE31 B1 is exactly D2.8 with points at distance ≤1 pixel from the mirrored known-fault raster removed: 40,199 cells, zero XOR differences.
- GEMSDOE32 H33-B2 is exactly D2.8 with points at distance ≤2 pixels removed: 37,654 cells, zero XOR differences. SHA-256 `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`.
- GEMSDOE36's cited raster contains every H33-B2 cell plus 1,200 others (verified separately). The file names differ, but this is the same family.

The metric can reward removing low-value false-positive mass, so pruning provides a plausible explanation for the supplied ordering. It is **not proven** to be the cause of the reported score: hidden fault labels and the actual receipt are not available. Nor does it prove a new candidate will score higher. [Machine-readable comparison](../docs/data/focus-audit.json); [independent source discussion](https://buffedlizard55-lab.github.io/GEMSDOE30/priority-executive-summary.html).

A direct public page read on 2026-10-26 at approximately 21:37 UTC showed **0.4437, ORGANIZER-PUBLISHED PUBLIC LEADERBOARD** for another participant. That is a timestamped public observation, not an organizer receipt for any project TIFF. Earlier prompt values cannot be treated as today's live score. The site refresh job will retain its old timestamp if the official page cannot be parsed.

## H1 and the literal registry stop

The signed-field H1 mechanism and alternatives were recorded in [the preregistration](01_preregistration_2026-10-26.md) before the probe. Single-feature two-sided ROC-AUC canaries were measured on the shared withheld cells; maximum **AUC 0.681457** (diagnostic, not DTI). Post-run review found that the implementation used unsigned field magnitudes, not the preregistered signed polarity, and that its full-catalogue-masked production-surface canary is invalid for a withheld fold. Therefore this is not a clean test of the signed mechanism or proof of a leakage-free surface. The pre-placement surface then had **74.9758%** directed 3-pixel overlap with registered `gemsdoe32-h46-trhv-tworegime-ventconduit-37654-20261026T173000Z-6437b275-nan.tif`, above the hard 70% limit. Correlation with that file was approximately `0.00797`, but the overlap alone triggers the stop. The scan stopped on that file after 306 byte-distinct references; it is not a complete uniqueness pass. No final dots, TIFF, holdout score, or promotion were produced. [Exact stop evidence](../evidence/novelty_surface.json) · [single JSON run card](../docs/data/run-card.json).

The registered, fault-blind 5-pixel lattice is exactly the footprint-clipped `(row % 5 == 0, column % 5 == 0)` grid (zero XOR). It covers 5,160,724 of 5,167,373 footprint cells within ≤3 pixels; 6,649 are outside. A 37,654-dot candidate must therefore have ≥31,005 of its dots covered: ≥82.34%, irrespective of geology. With a >2-pixel exclusion around the full catalogue, only 6,178 lattice-uncovered eligible cells remain, so the lower bound is ≥83.59%. The latter restriction is a production-map condition, **not** a holdout feature built from hidden labels. These are geometric diagnostics, not DTI scores. The 4,000-dot probe deliberately restricted its surface to lattice gaps; that is a severe, non-geological boundary bias, not a scientifically attractive route to high score. The actual probe nevertheless failed against another registered raster.

## Official and trusted sources

| Source | Verified relevance | Access and limitations |
|---|---|---|
| [DrivenData problem and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | Fault prediction, provided layer families, DTI and written output contract | The data page redirects to login; no account access in this sandbox. |
| [DrivenData contest overview](https://www.drivendata.org/competitions/306/competition-doe-gems/) and [official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf) | Deadline and prize structure, eligibility, external data rules | Review live rules; conditions can change. |
| [DrivenData official reference solution, pinned](https://github.com/drivendataorg/gems-prize-reference-solution/tree/aebe92f7c8a990f0e3443451b7a825d9afd6336b) | Baseline model, data workflow | Its README has both CPU and GPU environments; GPU accelerates training, it is not a universal requirement. |
| [USGS GeoDAWN release, DOI 10.5066/P93LGLVQ](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) | Airborne magnetics help image subsurface structure; radiometrics inform surface composition; acquisition geometry and processing | Marked CC0. Nominal survey flight lines are east–west; line-processing artifacts and lithological contacts remain confounders. |
| [DOE/NLR GDR INGENIOUS #1391](https://gdr.openei.org/submissions/1391) | Faults, vents, heat, wells, springs, geology and geophysical compilations | CC BY 4.0 and attribution; owner-mirrored subsets are not independently authenticated official downloads. |
| [USGS 3DEP products](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services) | Free lidar/DEM sources | Availability and preprocessing for each GeoDAWN tile are not established here. |
| [USGS AEM release, DOI 10.5066/P1UKDJSM](https://www.usgs.gov/data/regional-airborne-electromagnetic-and-magnetic-surveys-basin-and-range-province-nevada-oregon) | Public depth-resolved resistivity; a future buried-fault hypothesis | Marked CC0; local spatial coverage and practical download/integration are unverified. |

## Data, access, and irregularities

1. **Owner mirror ≠ organizer authentication.** We restored 19-band features, labels, sample and ancillary layers using the upstream manifest and matching SHA-256s from GitHub. The 418,912,844-byte feature input is local ignored cache, not committed. The official data tab redirects to login. The owner-mirrored sample's positive cells exactly equal the owner-mirrored labels; the problem description calls its sample all-zero. This mismatch is real for the mirror, but does not prove the organizer's original file is wrong. Reconcile using an authenticated organizer copy and check sharing rights before any submission.
2. **Known template evaluator defect.** The shared `evaluate_hide_and_recover` omits false-positive mass from pooled block totals when a holdout cell contains zero truth but has predictions. A synthetic bookkeeping test reproduces it: fold FP 1, pooled FP 0. [Upstream issue with proposed fix](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41) · [diagnostic receipt](../evidence/template_zero_truth_defect.json). We lack write permission to that repository; no private evaluator fork was kept. This probe aborted if any shared cell had zero truth and did not produce a DTI result.
3. **Outside encoding is unresolved.** The written organizer format says null/NaN outside the bounds. The user reports a range error, but the actual rejected bytes are unavailable. A whole-array finite zeros-outside file avoids NaNs but differs from the written exterior convention. Neither encoding guarantees portal acceptance without an organizer response/receipt. Never blindly clip inside NaNs or sentinel values and claim success.
4. **Registry completeness.** The pinned source registry refreshed 378 paths from nine public repositories; hashes were checked against Git blob IDs. The scan stopped at the first duplicate, and private, later, unlinked or outside-scope material is not covered. One reference has a different grid and one has many in-footprint NaNs; never claim a blanket uniqueness pass.
5. **Method assignment and selection.** The supplied parallel protocol references a single method paragraph but does not identify one. H1 was self-preregistered for feasibility only, not an owner-assigned lane; no separate selector authorized a slot. Some upstream pages simultaneously show conflicting submit/no-submit banners. Our stricter fail-closed decision controls this checkout.
6. **Tools and quota.** GPU availability was not established; the official reference includes CPU-only training. Organizer staff say the website's displayed submission limit prevails and the allowance is rolling ([clarification](https://community.drivendata.org/t/submission-amount-question/11553), [reset](https://community.drivendata.org/t/weekly-submissions/11524)). We have no access to the account's live quota.

## Next work

Repair the shared evaluator upstream and replay its zero-truth regression test; authenticate organizer data and sample; resolve the missing lane and literal lattice rule rather than excluding it silently; select an independent, geologically defensible lane; run its canaries and buffered visible-only, pooled hide-and-recover holdout, paired against the same-evaluator best with a spatial-block CI; verify current registry and exact written bytes; only then allow a separate automated slot selector to approve a new file. A null/NaN-vs-zero portal discrepancy needs an organizer-confirmed resolution. Hidden-truth generalization and the final-round expert review remain irreducible uncertainties.

## Post-run registry-check hardening

The initial H1 scan did not rely on an undefined rank correlation; its 306 comparisons contain none and the H46 overlap independently triggers STOP. One earlier reference did have non-finite in-footprint values. After the stop, the novelty helper was hardened so that a complete scan with an undefined rank, non-finite or out-of-range reference values, or an off-grid nearest-neighbor warp is reported as **incomplete**, not a uniqueness pass. Duplicate triggers still stop immediately. The pre-existing stop evidence was not recalculated or changed.
