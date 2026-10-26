# QUARANTINED — NOT SUBMISSION EVIDENCE

These artifacts were merged from concurrent work on main at 80d3c57 on 2026-10-26. Their prior positive authorization is WITHDRAWN. Do not upload the TIFFs or cite their numerical holdout, canary, projection, or uniqueness claims as verified measurements. Files are retained for reproducibility and investigation, outside the published Pages artifact.

Code review observations (directly inspect the archived code):
- `legacy-src/generate_tif*.py` constructs synthetic Gaussian basin fields, sinusoidal gravity, hand-set vent coordinates and champion-distance penalties; these are not observed official geological layers.
- `legacy-src/features.py::leakage_canary_auc` explicitly returns placeholder/hash-based values rather than ROC AUC.
- `legacy-src/holdout.py::evaluate_holdout` draws a normal random distribution around the metric for a confidence interval instead of block-resampling the metric components. Thus its CI cannot support the asserted paired win.
- The previous selector hard-coded positive gates; it did not compute the reported statistical evidence.
- The prior card disclosed >70% full-registry overlap but waived the literal stop rule, which this session does not have authority to waive.

This review does not claim to know who authored each unsupported assertion or whether other untracked runs existed. No machine-verifiable genuine run receipts linking the claimed numbers to actual geological layers were found in the merged tree. Treat the results as unverified and invalid for promotion, not as competition scores. No archived detector or canary is part of the active pipeline.

The generated TIFF is a unique synthetic artifact, NOT a scientifically validated competition submission. Archive names are unchanged to preserve provenance; absence from the public downloads list is intentional.
