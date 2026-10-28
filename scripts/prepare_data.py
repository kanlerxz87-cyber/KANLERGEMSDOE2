#!/usr/bin/env python3
"""Validate restored inputs and build a memory-mapped, label-free feature matrix.

No GPU required. This is a deliberately small CPU detector with geological
inputs, not the old unavailable CNN pipeline. Raw bulk rasters stay ignored.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import gaussian_filter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems import arcs, footprint, geofeatures, paths  # noqa: E402
from gems.validator import sha256_file  # noqa: E402


def _input_key(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        try:
            return f"data/{p.relative_to(paths.DATA_DIR)}"
        except ValueError:
            return p.name

BASE_BANDS = (
    "rtp",
    "tmi_hg",
    "tmi_vg",
    "iso_grav_anom",
    "iso_grav_anom_hg",
    "iso_grav_anom_vg",
    "det_elev",
    "det_elev_slope",
    "tmi",
    "cond_surf",
    "depth_to_base_surf",
    "geod_dilaterate",
    "geod_shearrate",
)
LIDAR_BANDS = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)  # strike converted to circular encoding below.


def validate_band_order(descriptions, expected_names):
    """Verify the mirror's named band order before assigning physical semantics.

    This checks metadata consistency, not whether the owner-mirrored bytes are
    authentic organizer data or whether their descriptions are scientifically true.
    """
    if len(descriptions) != len(expected_names) or any(not d for d in descriptions):
        raise ValueError("Feature raster must have a nonempty description for every band")
    observed = [d.split(" - ", 1)[0].strip() for d in descriptions]
    if observed != list(expected_names):
        raise ValueError("Feature raster band descriptions do not match the configured band order")


def verify_cached_preparation(dest, meta_path, input_paths, expected_shape, expected_names):
    """Fail closed on stale bytes, inputs, or layout instead of trusting cache presence."""
    metadata = json.loads(Path(meta_path).read_text())
    if metadata.get("names") != list(expected_names) or metadata.get("shape") != list(
        expected_shape
    ):
        raise ValueError("Prepared cache layout changed; explicit --force required")
    if metadata.get("sha256") != sha256_file(dest):
        raise ValueError("Prepared feature cache checksum mismatch; explicit --force required")
    expected_inputs = {_input_key(p): sha256_file(p) for p in input_paths}
    if metadata.get("inputs") != expected_inputs:
        raise ValueError("Prepared cache inputs changed; explicit --force required")
    arr = np.load(dest, mmap_mode="r", allow_pickle=False)
    if arr.shape != tuple(expected_shape) or arr.dtype != np.dtype("float32"):
        raise ValueError("Prepared cache array layout does not match metadata")
    return metadata


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument(
        "--receipt", type=Path, default=paths.DATA_DIR / "preparation_receipt.json",
        help="Output receipt (default: in the data cache); use a new path to preserve prior receipts",
    )
    args = ap.parse_args()
    out = paths.DATA_DIR / "prepared"
    out.mkdir(parents=True, exist_ok=True)
    dest = out / "features.npy"
    meta_path = out / "features.json"
    if dest.exists() != meta_path.exists() and not args.force:
        raise ValueError("Incomplete prepared cache; explicit --force required")
    fp = footprint.load_footprint()
    idx = np.flatnonzero(fp.ravel())
    template = paths.DATA_DIR / "sample_submission.tif"
    if not template.exists():
        template = paths.DATA_DIR / "bridge/sample_submission.tif"  # legacy layout
    source = paths.DATA_DIR / "training_features.tif"
    lidar = paths.DATA_DIR / "external/lidar_scarp_features_u8.tif"
    manifest = ROOT / "registry/data_manifest.json"
    protected = [template, source, lidar, dest, meta_path,
                 dest.with_name("features.partial.npy"), manifest,
                 ROOT / "docs/data/footprint.bin"]
    if manifest.is_file():
        protected.extend(paths.DATA_DIR / e["dest"] for e in json.loads(manifest.read_text())["files"])
    if args.receipt.resolve() in {p.resolve() for p in protected}:
        raise SystemExit("Preparation receipt must not overwrite an input or feature cache")
    with rasterio.open(template) as t, rasterio.open(source) as s, rasterio.open(lidar) as lidar_ds:
        for d in (s, lidar_ds):
            if d.shape != t.shape or d.crs != t.crs or d.transform != t.transform:
                raise SystemExit("Input grid mismatch; no silent reprojecting")
        if s.count != len(geofeatures.BAND_ORDER):
            raise SystemExit(f"Expected {len(geofeatures.BAND_ORDER)} competition bridge bands")
        validate_band_order(s.descriptions, geofeatures.BAND_ORDER)
        if not np.array_equal(np.isfinite(t.read(1)), fp):
            raise SystemExit("Template and committed footprint disagree")
    names = (
        list(BASE_BANDS)
        + [f"lidar_{b}" for b in LIDAR_BANDS]
        + [
            "lidar_cos2strike",
            "lidar_sin2strike",
            "det_local_relief",
            "det_gradient",
            "arc_rtp",
            "arc_det_elev",
            "arc_agreement",
        ]
    )
    if dest.exists() and meta_path.exists() and not args.force:
        checked = verify_cached_preparation(
            dest, meta_path, (template, source, lidar), (len(idx), len(names)), names
        )
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(checked, indent=2) + "\n")
        print(json.dumps(checked, indent=2))
        return
    arr = np.lib.format.open_memmap(
        dest.with_name("features.partial.npy"),
        mode="w+",
        dtype=np.float32,
        shape=(len(idx), len(names)),
    )
    stored = {}
    with rasterio.open(source) as s:
        for i, name in enumerate(BASE_BANDS):
            a = s.read(geofeatures.BAND_ORDER.index(name) + 1).astype(np.float32)
            a[~fp | ~geofeatures._valid(a)] = np.nan
            arr[:, i] = a.ravel()[idx]
            if name in ("rtp", "det_elev"):
                stored[name] = a
            print("source", name, flush=True)
    col = len(BASE_BANDS)
    with rasterio.open(lidar) as s:
        valid = s.read(12) > 0
        for b in LIDAR_BANDS:
            a = s.read(b).astype(np.float32)
            a[~valid] = np.nan
            arr[:, col] = a.ravel()[idx]
            col += 1
        theta = (np.maximum(s.read(11).astype(np.float32) - 1, 0) / 254) * np.pi
        for a in (np.cos(2 * theta), np.sin(2 * theta)):
            a[~valid] = np.nan
            arr[:, col] = a.ravel()[idx]
            col += 1
    dem = stored["det_elev"]
    dv = np.isfinite(dem)
    # Nearest valid fill affects only label-free transform neighborhoods; missing
    # input pixels themselves remain NaN. No label-based imputation.
    from scipy.ndimage import distance_transform_edt

    inds = distance_transform_edt(~dv, return_distances=False, return_indices=True)
    dem_fill = dem[tuple(inds)]
    del inds
    local_relief = dem_fill - gaussian_filter(dem_fill, 5)
    gy, gx = np.gradient(gaussian_filter(dem_fill, 1), 100)
    for a in (local_relief, np.hypot(gx, gy)):
        a[~dv] = np.nan
        arr[:, col] = a.ravel()[idx]
        col += 1
    ar = arcs.arc_rim_support(stored["rtp"], np.isfinite(stored["rtp"]))
    ad = arcs.arc_rim_support(dem, dv)
    # Agreement is a descriptor, not a declaration of statistical independence.
    aa = np.sqrt(np.maximum(ar, 0) * np.maximum(ad, 0))
    for a in (ar, ad, aa):
        arr[:, col] = a.ravel()[idx]
        col += 1
    if col != len(names):
        raise SystemExit("Feature column accounting error")
    arr.flush()
    del arr
    dest.with_name("features.partial.npy").replace(dest)
    metadata = {
        "names": names,
        "base_count": len(names) - 3,
        "shape": [len(idx), len(names)],
        "arc_radii_px": list(arcs.RADII_PX),
        "sha256": sha256_file(dest),
        "inputs": {_input_key(p): sha256_file(p) for p in (template, source, lidar)},
        "note": "Band names follow owner bridge order. Ambiguous tc/earthquake description aliases are deliberately excluded. Features are not calibrated fault probabilities.",
    }
    meta_path.write_text(json.dumps(metadata, indent=2) + "\n")
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
