#!/usr/bin/env python3
"""Independently inspect published HPTR bytes, without training or authorization."""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]

def inspect(path: Path, expected_sha: str) -> dict:
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    with rasterio.open(path) as ds:
        a = ds.read(1)
        finite = np.isfinite(a)
        return {
            "file": path.name, "sha256": sha, "hash_matches_sidecar": sha == expected_sha,
            "bands": ds.count, "shape": list(ds.shape), "crs": str(ds.crs),
            "transform": list(ds.transform)[:6], "dtype": ds.dtypes[0], "nodata": ds.nodata,
            "all_cells_finite": bool(finite.all()), "nonfinite_cells": int((~finite).sum()),
            "all_cells_in_0_1": bool(finite.all() and ((a >= 0) & (a <= 1)).all()),
            "minimum": float(a[finite].min()) if finite.any() else None,
            "maximum": float(a[finite].max()) if finite.any() else None,
            "positive_cells": int((finite & (a > 0)).sum()),
            "official_template_match": None, "footprint_available": False,
            "organizer_acceptance_verified": False,
        }

def main() -> None:
    sidecar = next((ROOT / "docs/downloads").glob("*675d0ff8-validation.json"))
    ref = json.loads(sidecar.read_text())
    result = inspect(sidecar.parent / ref["raster_filename"], ref["raster_sha256"])
    card = {
        "schema": "gems.review-card.v1", "generated_utc": datetime.now(timezone.utc).isoformat(),
        "hypothesis": "No new lane supplied; review existing artifact only",
        "mechanism": "Independent byte hash and full-array numeric inspection; no model fit or emission",
        "named_non_fault_mimic": "Lithologic contacts and survey leveling seams (historical lane confounders)",
        "holdout_dti": None, "holdout_ci95": None,
        "holdout_status": "Not replayed; archived results are not current measurements or leaderboard estimates",
        "correlation_overlap_vs_registry": {"surface": None, "final_dots": None,
            "status": "Not replayed; archived sidecar records a literal registry failure, not clearance",
            "archived_literal_witness_overlap": ref["literal_spacing5_lattice_overlap"]},
        "raster_sha256": result["sha256"], "validator_output": result,
        "submission_name": None, "note": "Review only. No assigned new method lane; historical literal duplicate stop remains. Do not submit.",
        "experiments_run": 0, "weekly_slots_spent": 0, "ok_to_submit": False, "verdict": "negative",
    }
    (ROOT / "evidence/review_run_card_20261028.json").write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
    if not result["hash_matches_sidecar"] or not result["all_cells_in_0_1"]:
        raise SystemExit("Published artifact integrity/numeric check failed")
    print(json.dumps(card, indent=2, allow_nan=False))

if __name__ == "__main__":
    main()
