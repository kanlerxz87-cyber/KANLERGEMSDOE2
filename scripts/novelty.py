"""Literal surface/dot uniqueness against a verified, finite registry snapshot.

This module checks novelty only; the upstream template supplies the evaluator and
GeoTIFF writer. It never changes thresholds for dense baselines or treats a hash
change as scientific novelty. The snapshot cannot cover private/future rasters.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from scipy.stats import rankdata


def _rank_summary(values: np.ndarray) -> tuple[float, np.ndarray, float]:
    """Centered midranks for sparse, nonnegative values (zero is the common tie)."""
    values = np.asarray(values)
    if values.ndim != 1 or not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Candidate must be finite and nonnegative")
    n = values.size
    pos = values > 0
    k = int(pos.sum())
    x0 = -k / 2.0
    xp = (n - k + rankdata(values[pos], method="average")) - (n + 1) / 2.0
    xvar = float((n - k) * x0 * x0 + np.dot(xp, xp))
    return x0, xp, xvar


def spearman_sparse(candidate: np.ndarray, peer: np.ndarray) -> float | None:
    """Exact tie-aware Spearman rho, avoiding a full candidate rank array.

    Inputs must be finite 1-D arrays over identical pixels. Both zeros and
    positive values in the registry count. Undefined constant correlations are
    returned as None, never misreported as a numerical pass.
    """
    x = np.asarray(candidate)
    y = np.asarray(peer)
    if x.ndim != 1 or y.shape != x.shape or not np.isfinite(y).all():
        raise ValueError("Expected same-length finite vectors")
    x0, xp, xvar = _rank_summary(x)
    if not xvar or not len(y):
        return None
    pos = x > 0
    n = y.size
    if np.all((y == 0) | (y == 1)):
        ones = int((y == 1).sum())
        yvar = n * ones * (n - ones) / 4.0
        if not yvar:
            return None
        cross = n / 2.0 * (ones * x0 + float(np.dot(xp - x0, y[pos])))
    else:
        yr = rankdata(y, method="average") - (n + 1) / 2.0
        yvar = float(np.dot(yr, yr))
        if not yvar:
            return None
        # Centered peer ranks sum to zero, so only candidate positive deltas matter.
        cross = float(np.dot(xp - x0, yr[pos]))
    rho = cross / float(np.sqrt(xvar * yvar))
    return float(np.clip(rho, -1.0, 1.0))


def dot_overlap(mine: np.ndarray, theirs: np.ndarray, radius_px: int = 3) -> float:
    """Forward fraction of my positive cells within a Euclidean radius of theirs."""
    if mine.ndim != 2 or mine.shape != theirs.shape or radius_px < 0:
        raise ValueError("Expected matching 2-D grids and nonnegative radius")
    ys, xs = np.nonzero(np.isfinite(mine) & (mine > 0))
    if not len(ys):
        raise ValueError("An empty candidate cannot establish uniqueness")
    support = np.isfinite(theirs) & (theirs > 0)
    near = np.zeros(len(ys), dtype=bool)
    height, width = mine.shape
    for dy in range(-radius_px, radius_px + 1):
        for dx in range(-radius_px, radius_px + 1):
            if dy * dy + dx * dx > radius_px * radius_px:
                continue
            iy, ix = ys + dy, xs + dx
            inside = (iy >= 0) & (iy < height) & (ix >= 0) & (ix < width)
            near[inside] |= support[iy[inside], ix[inside]]
    return float(near.mean())


def _sha256(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def compare(candidate: np.ndarray, footprint: np.ndarray, template_file: Path,
            registry: dict, template_root: Path, *, stage: str) -> dict:
    """Check the literal rule against all verified byte-distinct snapshot rasters.

    Returns immediately after a violation. Nonmatching test grids are warped by
    nearest neighbor solely for comparison and explicitly reported; completeness
    is limited to the snapshot and cannot be asserted for later/private files.
    """
    a = np.asarray(candidate, np.float32)
    foot = np.asarray(footprint, bool)
    if a.shape != foot.shape or a.ndim != 2 or not foot.any():
        raise ValueError("Candidate/footprint mismatch")
    if not np.isfinite(a).all() or (a < 0).any() or (a > 1).any() or (a[~foot] != 0).any():
        raise ValueError("Candidate must be finite [0,1], zero outside the footprint")
    if not (a > 0).any():
        raise ValueError("Empty candidate support")
    with rasterio.open(template_file) as tmpl:
        grid = (tmpl.shape, tmpl.crs, tmpl.transform)
    if grid[0] != a.shape:
        raise ValueError("Template grid and candidate shape differ")
    entries = registry["rasters"]
    if not entries:
        raise ValueError("An empty registry cannot establish uniqueness")
    seen, rows = set(), []
    for ent in entries:
        if ent["sha256"] in seen:
            continue
        seen.add(ent["sha256"])
        path = (template_root / ent["local"]).resolve()
        if not path.is_relative_to(template_root.resolve()) or not path.is_file() or _sha256(path) != ent["sha256"]:
            raise ValueError(f"Missing or corrupt registry file: {ent['path']}")
        with rasterio.open(path) as src:
            if src.count != 1:
                raise ValueError(f"Registry file is not single-band: {ent['path']}")
            aligned = (src.shape, src.crs, src.transform) == grid
            if aligned:
                b = src.read(1).astype(np.float32, copy=False)
            else:
                if src.crs is None:
                    raise ValueError(f"Registry file has no CRS: {ent['path']}")
                b = np.zeros(grid[0], dtype=np.float32)
                reproject(source=rasterio.band(src, 1), destination=b,
                          src_transform=src.transform, src_crs=src.crs,
                          src_nodata=src.nodata, dst_transform=grid[2],
                          dst_crs=grid[1], dst_nodata=0, resampling=Resampling.nearest)
        common = foot & np.isfinite(b)
        if not common.any():
            raise ValueError(f"No finite common footprint: {ent['path']}")
        rho = spearman_sparse(a[common], b[common])
        overlap = dot_overlap(a, b)
        row = {"repo": ent["repo"], "path": ent["path"], "sha256": ent["sha256"],
               "rho": rho, "my_dots_within_3px": overlap,
               "inside_footprint_nonfinite": int((foot & ~np.isfinite(b)).sum()),
               "inside_footprint_out_of_range": int((foot & np.isfinite(b) & ((b < 0) | (b > 1))).sum()),
               "warped_nearest_to_template": not aligned}
        rows.append(row)
        if (rho is not None and abs(rho) > 0.90) or overlap > 0.70:
            return {"stage": stage, "passed": False, "stop_reason": "DUPLICATE_LANE",
                    "trigger": row, "checked_unique_byte_rasters": len(rows),
                    "snapshot_entries": len(entries), "refs": registry["refs"], "rows": rows}
    incomplete = [r for r in rows if r["rho"] is None or r["inside_footprint_nonfinite"]
                  or r["inside_footprint_out_of_range"] or r["warped_nearest_to_template"]]
    return {"stage": stage, "passed": not incomplete,
            "stop_reason": "INCOMPLETE_REGISTRY_COMPARISON" if incomplete else None,
            "incomplete_count": len(incomplete),
            "checked_unique_byte_rasters": len(rows), "snapshot_entries": len(entries),
            "refs": registry["refs"],
            "max_abs_spearman": max((abs(r["rho"]) for r in rows if r["rho"] is not None), default=None),
            "max_overlap": max(r["my_dots_within_3px"] for r in rows),
            "undefined_rank_count": sum(r["rho"] is None for r in rows),
            "warped_count": sum(r["warped_nearest_to_template"] for r in rows),
            "rows": rows}
