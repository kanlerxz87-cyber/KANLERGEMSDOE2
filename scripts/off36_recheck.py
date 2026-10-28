#!/usr/bin/env python3
"""Independent, read-only recheck of the PR #36 'off-catalogue' 36GEMSDOE file.

Writes evidence/off36_independent_check_20261027.json. Never changes the run card.
Measures: format, on-catalogue dots, lattice 3-px overlap, share of dots in lattice-gap
pixels, and max 3-px overlap vs every locally restored registry raster.
"""
import hashlib, json, sys
from pathlib import Path
import numpy as np, rasterio
from scipy.ndimage import binary_dilation

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems.release_audit import load_reference, assess_file  # noqa: E402
from gems32.paths import data_dir  # noqa: E402

TIF = ROOT / "docs/downloads/36GEMSDOE-off-catalogue-blind-geothermal-targeting-20261027T234345Z-2ecaae7a056e-zeros.tif"
OUT = ROOT / "evidence/off36_independent_check_20261027.json"
DISK3 = np.array([[y * y + x * x <= 9 for x in range(-3, 4)] for y in range(-3, 4)])


def main() -> None:
    ref = load_reference(ROOT, data_dir())
    foot = ref["foot"]
    a = assess_file(TIF, ref)
    with rasterio.open(TIF) as ds:
        x = ds.read(1)
    dots = foot & (x > 0)
    n = int(dots.sum())
    gap = foot & ~binary_dilation(ref["reference"], structure=DISK3)
    competing = {}
    for p in sorted((data_dir() / "scored").glob("*.tif")):
        with rasterio.open(p) as ds:
            b = ds.read(1)
        other = foot & np.isfinite(b) & (b > 0)
        competing[p.name] = round(float((dots & binary_dilation(other, structure=DISK3)).sum() / n), 6)
    worst = max(competing.items(), key=lambda kv: kv[1])
    out = {
        "schema": "gems.off36-independent-check.v1",
        "file": TIF.name,
        "sha256": hashlib.sha256(TIF.read_bytes()).hexdigest(),
        "dots": n,
        "values_unique": sorted(float(v) for v in np.unique(x)),
        "nan_count": int(np.isnan(x).sum()),
        "outside_footprint_positive": int((~foot & (x > 0)).sum()),
        "on_catalogue_positive_pixels": a["on_catalogue_positive_pixels"],
        "lattice_overlap_3px": round(a["witness_overlap_fraction"], 6),
        "dots_in_lattice_gap_pixels": int((dots & gap).sum()),
        "dots_in_lattice_gap_fraction": round(float((dots & gap).sum() / n), 6),
        "restored_registry_rasters_checked": len(competing),
        "max_overlap_3px_restored_registry": {"file": worst[0], "fraction": worst[1]},
        "per_raster_overlap_3px": competing,
        "holdout_dti": None,
        "limit": 0.70,
        "literal_rule_duplicate": bool(a["duplicate_under_literal_rule"]),
    }
    OUT.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: out[k] for k in ["dots", "lattice_overlap_3px", "dots_in_lattice_gap_fraction", "restored_registry_rasters_checked", "max_overlap_3px_restored_registry", "on_catalogue_positive_pixels"]}, indent=1))


if __name__ == "__main__":
    main()
