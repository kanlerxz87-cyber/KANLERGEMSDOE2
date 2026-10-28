# Focus-nine review and next HTCADS experiment slate — 2026-10-28

## Decision first

**Negative / no submission. No new TIFF was generated in this review, and no file is approved to download and submit.** The assigned, frozen method is `HTCADS-K2` in [`registry/preregistration_htcads.json`](../registry/preregistration_htcads.json). Its exact novelty preflight lower bound is 31,005/37,654 = 82.3418% within 3 px of the registered spacing-5 raster, above the literal 70% limit. Per the working contract, stop before model fit, dot placement, or holdout scoring; do not reduce the dot budget or place dots in lattice gaps to evade the gate. No slot was used.

The review preserves the nine-site overview in [`docs/executive-summary.html`](../docs/executive-summary.html). It is not a current leaderboard feed or a submission selector.

## GEMSDOE32 (0.2778): what the files establish

The `0.2778` attributed to `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` is **USER/OWNER-REPORTED**, not organizer-confirmed: the repository contains no submission-page receipt binding that score to the pinned TIFF bytes. The bytes show that its positive-pixel mask is an exact subset of the GEMSDOE25 mask after removing 6,436 pixels within 2 pixels of the owner-mirrored known-fault mask; GEMSDOE36 retains the GEMSDOE32 mask and adds 1,200 pixels. Those are geometric facts, not a causal explanation of the reported score.

A plausible mechanism is that removing predictions near known traces reduces false-positive weight while retaining much of the useful spatial coverage. But the organizer's hidden labels, score decomposition, and receipt are absent, so the mechanism is an **INFERENCE**, not a verified cause. The official challenge definition uses distance-weighted Tversky scoring; review the [DrivenData problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and the [staff clarification on known-fault masking](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4). A historical `HOLDOUT-DTI` score is not a map to leaderboard DTI; there is no defensible score estimate for a new submission in this review.

## Next hypotheses (not fitted, not validated, no gain forecast)

The ordering below is a **qualitative research-priority ranking**, not a numeric expected DTI improvement. None has been run in this review. The lane method is not changed; these are narrowly testable contrasts within the frozen HTCADS-K2 description. Absence from repository search is not proof that no related feature exists in every external site; the distinction here is the proposed validation contrast.

| Rank | Hypothesis and layers | Target physical signature / why it may find an unmapped fault | Named non-fault mimic | Difference from tracked work | Cost / data check / priority |
|---|---|---|---|---|---|
| 1 | **Multi-height potential-field crest migration stability**. Cached `rtp`, `tmi_hg`, `iso_grav_anom`, `iso_grav_anom_hg`, `iso_grav_anom_vg`, plus registered upward-continuation products. | Track ridge crest displacement, strike, and persistence across continuation heights. A dipping fault concealed beneath basin fill may create a scale-dependent gravity/magnetic edge that is not represented by a surface scarp or known-fault trace. | Unfaulted lithologic contact; remanent magnetization; survey leveling seam. | Separates a multi-height trajectory-stability ablation from the frozen lane's broader potential-field ridge/cross-gradient fusion; do not claim the signal is wholly absent from prior fused models. | Medium CPU; no new external source is required, but competition data/cache must be restored. The 2026-10-27 audit records pinned owner-mirror inputs; this review did not load them or authenticate their official-source bytes. **Highest priority**, subject to preflight clearance. |
| 2 | **Thermal transport-direction uncertainty**. DOE GDR/INGENIOUS 2 m temperature probes, wells/springs, `cond_surf`, terrain gradient, and structural orientation. | Predeclare a bounded set of physically plausible up-gradient bearings; test whether thermal/chemical anomalies converge on a structural ridge across directions. This can expose a blind feeder offset from a surface manifestation, rather than rewarding a radial heat blob. | Shallow groundwater flow, seasonal surface-temperature effects, pumping, conductive playa sediment. | Tests direction sensitivity against the frozen lane's deterministic hydraulic back-projection. | Medium; the 2026-10-27 inventory says the owner mirror was present, but those bytes are not in today's checkout and provenance is not authenticated. Official source: [DOE GDR submission 1391](https://gdr.openei.org/submissions/1391). |
| 3 | **Alteration-edge / basement-step coincidence**. GeoDAWN `TMI`, upward-continued magnetic products, radiometric `K/Th`, `cond_surf` boundary, and gravity/magnetic cross-gradient. | Require a short-wavelength magnetic trough edge and radiometric alteration gradient to coincide with a basement step. A buried conduit margin may remain visible where erosion or alluvium has removed the topographic scarp. | Lithologic contacts, alteration unrelated to permeable faulting, survey seam. | Tests edge coincidence rather than a broad/radial thermal or alteration anomaly; related source channels occur in HTCADS, but this strict joint event has not been validated here. | Low–medium if the cached stack is intact. Source: [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and); only owner-mirror bytes are recorded as available. |
| 4 | **Seasonal deformation barrier aligned to a structural conduit**. NASA OPERA DISP-S1 displacement gradients with `cond_surf` and gravity-gradient structure. | Seek repeatable cross-fault displacement discontinuities indicative of a buried hydraulic barrier along a concealed fault. | Pumping/irrigation, atmospheric delay, decorrelation, line-of-sight geometry. | Time-series InSAR rather than static GPS strain. | High cost and **not viable now**: the specific footprint tile/time series is not present in the audited availability inventory. Official starting point: [NASA OPERA](https://www.earthdata.nasa.gov/data/projects/opera). No download/availability claim is made. |

### Required validation order after the novelty conflict is resolved

1. Confirm the permitted treatment of the registered calibration raster in writing; do not silently exempt it or alter the dot budget/placement.
2. Restore the authenticated competition template, feature stack, and labels. The available hashes in this repository identify owner-hosted mirrors, not organizer-authenticated bytes; the official data page is login-gated in the recorded audit.
3. Pre-register a single experiment within HTCADS-K2. Reuse the shared feature cache, `evaluate_holdout.py`, and `submission_writer.py`.
4. Hold out whole connected fault segments with a buffer; derive catalogue features only from visible faults; mask visible faults pixel-exactly. Canary every feature alone before fitting; AUC >0.90 is leakage until explained.
5. Compare using the specified pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel) and report evaluator version, withheld-positive count, and 95% CI. Do not report a leaderboard projection as a score.
6. Only a separate selector may consider a weekly submission slot after pre-placement surface correlation, final-dot overlap, all-registry coverage, format/exterior checks, and current account quota all pass.

## Audit/source links

- Exact-byte and focus-lineage record: [`evidence/release_audit_20261027.json`](../evidence/release_audit_20261027.json)
- Current negative Run Card: [`evidence/current_run_card.json`](../evidence/current_run_card.json)
- Focus rasters and hash ledger: [`registry/focus_sites_20261027.json`](../registry/focus_sites_20261027.json)
- Data availability and provenance caveats: [`evidence/data_availability_20261027.json`](../evidence/data_availability_20261027.json)
- Official rules: [NLR rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- Official reference implementation: [DrivenData GEMS reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- Official terrain source: [USGS 3DEP](https://www.usgs.gov/3d-elevation-program)

**Limitations:** no current hidden-label access, organizer receipt for the reported GEMSDOE32 score, independently replayed OOF caches, authenticated mirror provenance, or current account quota. This review intentionally did not fit a candidate, generate a TIF, or estimate a leaderboard score because the literal preflight is mathematically blocking under the assigned protocol.
