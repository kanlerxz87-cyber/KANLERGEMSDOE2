# Preregistered next-step research plan — GEMS

**Prepared:** 2026-10-26 UTC. **Status:** protocol and hypotheses only; no modeling or holdout run performed. **Budget:** at most 3 experiments or 2 hours after all prerequisites exist. **Competition slots used:** 0. **Lane:** select exactly one of the below after duplicate review; do not blend lanes. This is not a pre-approval to create or submit a raster.

## Evidence state and blockers

The local repository is empty of model code, templates, caches, features, labels, rasters, and evaluation tools. Thus the hypotheses below are provisional: their novelty against the many linked site repositories is **not verified**, the features cannot be tested for leakage, and there is no validated holdout best to beat. No numeric DTI improvement is predicted; “higher score” cannot be inferred from mechanism plausibility. Competition provided feature families listed on the official problem page may support these methods once the authorized feature TIFF is present. All candidates use only those competition-provided inputs—no additional external data is needed or proposed, so external-source availability is not a blocker.

## Ranked hypotheses (relative priority, not score projections)

| Rank | Candidate / geological mechanism | Layers / physical transform | Why it might find an unmapped fault rather than merely reproduce a known trace | Difference to confirm against the actual repo/site code | Expected DTI effect and cost |
|---:|---|---|---|---|---|
| 1 | **Cross-scale edge-decoupling at buried basement steps.** A fault may offset shallow conductive cover and deeper basement differently; the spatially persistent *offset* between the two boundaries may indicate a blind structure rather than an ordinary single contact. | Depth to conductive base + surface conductivity; isostatic gravity anomaly and slope; TMI horizontal/vertical gradients. Compute multi-scale edge ridges, estimate local orientations with structure tensors, and score coherent, orientation-compatible edge separation across scales (not raw edge coincidence). | A blind or buried fault may preserve a basement discontinuity under conductive cover while lacking a surface fault trace. The target is a concealed two-depth boundary geometry, not proximity to mapped fault labels. | Must check for existing depth/tilt/edge-discordance implementations in the imported shared template and all nine registries. Similarity cannot be ruled out from submission names alone. | **Unquantified; top test priority** because all layers are official/cached and one interpretable transform; **medium** implementation cost. No DTI estimate until holdout. |
| 2 | **Strain-gradient segmentation with geophysical corroboration.** Fault tips/stepovers may localize where a geodetic strain corridor changes width or orientation at a persistent crustal edge. | Dilatation, shear strain, second invariant of strain-rate tensor; TMI and gravity slopes. Apply multi-scale Hessian/structure-tensor ridge and change-point tests; require persistence in strain and one independent potential-field edge. | Tectonic deformation gradients can extend beyond the mapped surface trace, while requiring an independent geophysical boundary may reduce generic strain noise. | Check for prior strain or step-over models (e.g., named older lane is not enough to prove absence). | **Unquantified; second priority**, medium/high cost due scale/orientation controls and leakage safeguards. |
| 3 | **Earthquake-density anisotropy residual.** Fault-related seismicity can form a directional lineament not captured by broad density surfaces; local anisotropic residuals could highlight active unmapped strands. | Competition earthquake-density layer only; subtract broad background, compute directional multi-scale ridge/linearity and compare orientation to gravity/TMI edges. | Local directional clustering may continue a fault beyond catalogued segments, rather than simply rewarding distance to known faults. | The precise semantics of the local earthquake band must be confirmed from its official metadata; do not assume a band name based on generated site text. | **Unquantified; lower priority**, low/medium cost. Likely confounding by spatial sampling, catalog completeness, and non-fault seismicity. |
| 4 | **Topographic–potential-field contact discordance.** A structural break may have a geophysical expression where erosional relief is absent, while geomorphic scarps may be unrelated to faults. | Detrended elevation and its slope; TMI horizontal/vertical derivatives; gravity anomaly slope. Estimate edge persistence and cross-domain orientation agreement; explicitly compare matched control edges lacking geophysical support. | Isolates concealed breaks from visually persuasive but non-tectonic scarps; targets the catalogue's surface-mapping gaps, not the mapped fault pixels. | Check against existing scarp, ridge, and magnetic-contact methods before claiming novelty; high overlap with prior concepts is plausible. | **Unquantified; fourth**, low/medium cost; non-fault contacts and erosional boundaries are major mimics. |

### Named non-fault mimics (must be tested)

Fluvial channels and terrace risers; alluvial-fan margins; lithologic contacts; volcanic-flow boundaries; anthropogenic linear features; landslides; and spatially clustered seismicity unrelated to mapped fault structures. A fault-like transform is not diagnostic on its own.

## Run sequence after prerequisites are satisfied

1. **Inventory first:** pin exact shared-template revision and hashes; locate its existing cached features, holdout evaluator, submission writer, labels, footprint/template, and registry list. Reconcile evaluator/writer interfaces; fix shared tooling once rather than privately forking it. No data or API credentials in Git.
2. **Preregister one lane:** verify its exact transform is absent from the template and prior registry implementations; record candidate formula, scales, thresholds, folds, seed, mimics, and stopping rules before looking at holdout outcomes. If not demonstrably distinct, stop/reclassify as duplicate.
3. **Leakage canary:** test every candidate input feature alone. Any AUC >0.90 is presumptive leakage until its provenance/split has been independently proven safe. All catalogue-derived features must be recomputed from only visible segments per fold.
4. **Holdout:** withhold whole fault segments with a spatial buffer; pixel-exact mask of visible labels; score pooled distance-weighted Tversky at alpha=0.2, beta=0.8, 300 m triangular kernel. Report evaluator version, withheld-positive count, and paired spatial-block 95% CI against the same-evaluator incumbent. Do not conflate this with organizer score.
5. **Registry gate:** compare surface before placement and final dots after placement against every available registry raster. Stop if |Spearman| >0.90 or >70% of dots are within 3 pixels of any one raster. Report all tested rasters and counts; missing registry coverage means uniqueness is unknown, not passed.
6. **Spend no slot:** within at most three experiments/two hours, an experiment may be called a holdout improvement only if it beats the incumbent under the preregistered rule. Weekly slot selection is a separate process. A negative result is the correct deliverable when gates fail.
7. **Format gate:** only after a scientific candidate exists, run the shared writer and local checker against the exact competition sample template. Check file hash, one float32 band, CRS, shape, transform, mask/footprint, no NaNs in footprint and range [0,1]. Portal acceptance is still not known until an organizer response/receipt.

## One-run card template (fill with evidence; never invent values)

```json
{
  "hypothesis": "NOT RUN",
  "mechanism": "NOT RUN",
  "named_non_fault_mimic": "NOT RUN",
  "holdout_dti": {
    "label": "HOLDOUT-DTI",
    "evaluator_version": "NOT RUN",
    "withheld_positives": null,
    "ci95": null,
    "value": null
  },
  "correlation_overlap_vs_registry": "NOT RUN — registry absent",
  "raster_sha256": "NOT GENERATED",
  "validator_output": "NOT RUN — template/data absent",
  "submission_name": null,
  "submission_note": null,
  "verdict": "negative"
}
```

`negative` here means not promotable on current evidence; it is not a claim that the hypothesis is geologically false.
