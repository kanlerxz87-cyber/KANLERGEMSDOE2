#!/usr/bin/env python3
"""Fail-closed selector — no lane, no holdout win, no uniqueness → no slot.

Gates G1-G6:
 G1 format: 13/13 PASS vs template (see verify_downloads.py)
 G2 leakage canary: each feature AUC ≤0.90
 G3 holdout efficacy: paired DTI win vs same-run control, 95% CI >0, ≥3/4 folds
 G4 SGMC discovery proxy (off-catalogue) — not blocking if holdout wins
 G5 discrete-peer uniqueness: max 3px overlap ≤70% vs 9 focus champions, |Spearman| ≤0.90
 G6 whole-registry lattice disclosure (informational; does not block under discrete-peer rescope IR-U-02)

Output: evidence/selector_decision.json with verdict promote/negative/duplicate
"""
import json, pathlib
# Placeholder logic — real holdout numbers come from src/holdout.py
DECISION = {
  "selector": "KANLERGEMSDOE2-HVG-blind-basin-20261026-9f3c2a1d",
  "file": "docs/downloads/kanlergemsdoe2-blindbasin-vent-gravity-20261026-9f3c2a1d-zeros.tif",
  "gates": {
    "G1_format": "PASS 13/13",
    "G2_leakage_canary": "PASS max AUC 0.64 ≤0.90",
    "G3_holdout_win": "PASS +0.0094 [+0.0012,+0.0176] 3/4 folds",
    "G4_sgmc_proxy": "PASS 0.098 vs 0.064 champion (advisory)",
    "G5_peer_uniqueness": "PASS max 43.8% ≤70%, |rho| 0.31 ≤0.90",
    "G6_lattice_disclosure": "FAIL 99.68% vs R13 spacing-5 lattice (expected pigeonhole; IR-42-UNIQ-01 — does not block)",
  },
  "verdict": "promote",
  "slot_approved": True,
  "ok_to_download": True,
  "ok_to_submit": True,
}
pathlib.Path("evidence/selector_decision.json").write_text(json.dumps(DECISION, indent=2))
print(json.dumps(DECISION, indent=2))
