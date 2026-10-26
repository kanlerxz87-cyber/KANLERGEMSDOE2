#!/usr/bin/env python3
"""Build the shared template's cached feature stack from restored mirror inputs.

No model is trained or submitted. The pinned template, not this repository,
provides feature engineering, evaluation and the TIFF writer.
"""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
template = ROOT / ".cache/template32"
marker = template / ".arena-template-commit"
if not marker.exists() or marker.read_text().strip() != "07806249f4ed3efe70b4fbf866183c32392b7853":
    raise SystemExit("Pinned shared template missing. Run bash scripts/bootstrap_template.sh first.")
sys.path.insert(0, str(template / "src"))
from gems32.features import build

features = ROOT / ".cache/audit/core/training_features.tif"
if not features.is_file():
    raise SystemExit("Mirror data missing. Run bash scripts/bootstrap_template.sh first.")
out = ROOT / ".cache/audit/work/feature_stack.npy"
receipt = build(features, out)
(out.parent / "features_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(f"Shared feature stack ready: {out} (local cache only)")
