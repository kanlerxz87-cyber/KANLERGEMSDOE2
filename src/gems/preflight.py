"""Literal-registry feasibility preflight, independent of a model or score.

A single hash-pinned registry witness can prove a duplicate stop. A non-stop is
only inconclusive: the rest of the registry, the surface, the final dots, and
the other scientific and selector gates still have to be checked.
"""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation

from .validator import sha256_file

LATTICE_NAME = "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"
LATTICE_SHA256 = "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2"
TEMPLATE_SHA256 = "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"


def coverage_witness(
    footprint: np.ndarray,
    reference: np.ndarray,
    budget: int,
    *,
    radius_px: int = 3,
    max_overlap: float = 0.70,
) -> tuple[dict[str, Any], np.ndarray]:
    """Prove a lower bound on directional overlap for every size-``budget`` set.

    At most U candidate pixels can fall outside the reference's radius-R halo.
    Thus at least max(0, K-U) of K distinct in-footprint dots must lie inside.
    Exactly 70% is not a stop; only strictly greater is, per the prompt.
    """
    fp_raw, ref_raw = np.asarray(footprint), np.asarray(reference)
    if (
        fp_raw.ndim != 2
        or fp_raw.shape != ref_raw.shape
        or not np.isin(fp_raw, (0, 1)).all()
        or not np.isin(ref_raw, (0, 1)).all()
    ):
        raise ValueError("aligned binary footprint and reference required")
    fp = fp_raw.astype(bool)
    ref = ref_raw.astype(bool) & fp
    total = int(fp.sum())
    if not total or not ref.any():
        raise ValueError("nonempty footprint and reference required")
    if type(budget) is not int or not 1 <= budget <= total:
        raise ValueError("budget must be a positive integer within the footprint")
    if type(radius_px) is not int or radius_px < 0:
        raise ValueError("radius must be a nonnegative integer")
    try:
        limit = Fraction(str(max_overlap))
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError("invalid overlap threshold") from exc
    if not 0 <= limit < 1:
        raise ValueError("overlap threshold must be in [0,1)")
    offsets = np.arange(-radius_px, radius_px + 1)
    disk = offsets[:, None] ** 2 + offsets[None, :] ** 2 <= radius_px**2
    halo = binary_dilation(ref, structure=disk) & fp
    covered = int(halo.sum())
    uncovered = total - covered
    min_overlapping = max(0, budget - uncovered)
    # Integer arithmetic avoids rounding a boundary exactly at the limit.
    forced_stop = min_overlapping * limit.denominator > budget * limit.numerator
    first_forced_budget = (uncovered * limit.denominator) // (limit.denominator - limit.numerator) + 1
    result = {
        "footprint_pixels": total,
        "reference_dots_in_footprint": int(ref.sum()),
        "radius_px": radius_px,
        "covered_pixels": covered,
        "uncovered_pixels": uncovered,
        "covered_fraction": covered / total,
        "candidate_budget": budget,
        "at_least_overlapping_dots": min_overlapping,
        "minimum_possible_directional_overlap": min_overlapping / budget,
        "overlap_limit": float(limit),
        "first_budget_forced_to_exceed_limit": first_forced_budget,
        "duplicate_forced": forced_stop,
        "status": "DUPLICATE_STOP" if forced_stop else "INCONCLUSIVE_NOT_A_PASS",
        "formula": "min_overlap = max(0, K - U) / K; stop only when > 0.70",
    }
    return result, halo


def pinned_witness(
    template_path: Path | str,
    lattice_path: Path | str,
    registry_path: Path | str,
    budget: int,
) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    """Verify file identities/alignment and evaluate the registered lattice.

    Pins prove consistency with the owner mirror, not organizer provenance.
    No arbitrary replacement template or missing comparator can silently pass.
    """
    template_path, lattice_path, registry_path = map(Path, (template_path, lattice_path, registry_path))
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    entries = [
        e for e in registry.get("entries", [])
        if e.get("filename") == LATTICE_NAME and e.get("sha256") == LATTICE_SHA256
    ]
    if len(entries) != 1:
        raise ValueError("expected exactly one registered, hash-pinned lattice witness")
    if sha256_file(template_path) != TEMPLATE_SHA256:
        raise ValueError("template does not match the pinned owner mirror")
    if sha256_file(lattice_path) != LATTICE_SHA256:
        raise ValueError("lattice does not match the registered bytes")
    with rasterio.open(template_path) as t, rasterio.open(lattice_path) as r:
        if (r.count, r.shape, r.crs, r.transform) != (1, t.shape, t.crs, t.transform):
            raise ValueError("lattice must be single-band and exactly template-aligned")
        if t.count != 1:
            raise ValueError("template must be single-band")
        footprint = np.isfinite(t.read(1))
        values = r.read(1)
    if not np.isfinite(values[footprint]).all() or not np.isin(values[footprint], (0, 1)).all():
        raise ValueError("witness must be finite and binary inside the footprint")
    result, halo = coverage_witness(footprint, values > 0, budget)
    result.update(
        witness_filename=LATTICE_NAME,
        witness_sha256=LATTICE_SHA256,
        template_sha256=TEMPLATE_SHA256,
        registry_path=str(registry_path),
        evidence_scope=(
            "One registered witness proves a stop, not an exhaustive registry comparison or "
            "organizer authentication. Surface was not fitted or inspected."
        ),
    )
    return result, footprint, halo


def require_safe_legacy_runner(data_dir: Path | str, repo_root: Path | str, budget: int) -> None:
    """Stop legacy runners before fit or placement until their ordering is fixed.

    They previously excluded controls from the gate and/or checked only after
    emission. Even an inconclusive one-witness result cannot authorize them.
    """
    data_dir, repo_root = Path(data_dir), Path(repo_root)
    try:
        result, _, _ = pinned_witness(
            data_dir / "sample_submission.tif",
            data_dir / "scored" / LATTICE_NAME,
            repo_root / "registry/comparison_registry.json",
            budget,
        )
    except (OSError, ValueError, KeyError) as exc:
        raise RuntimeError(f"BLOCKED: literal registry preflight unavailable: {exc}") from exc
    if result["duplicate_forced"]:
        raise RuntimeError(
            "DUPLICATE STOP before fitting/placement: registered lattice forces at least "
            f"{result['minimum_possible_directional_overlap']:.4%} overlap at K={budget}; "
            "limit is 70%. No submission generated."
        )
    raise RuntimeError(
        "BLOCKED: legacy runner lacks a verified all-entry surface check before placement "
        "and independent replay. A non-stop preflight is not a pass."
    )


def measure_candidate(
    path: Path | str,
    template_path: Path | str,
    footprint: np.ndarray,
    witness_halo: np.ndarray,
) -> dict[str, Any]:
    """Measure actual overlap of a saved candidate against this witness."""
    path = Path(path)
    with rasterio.open(template_path) as t, rasterio.open(path) as s:
        if (s.count, s.shape, s.crs, s.transform) != (1, t.shape, t.crs, t.transform):
            raise ValueError("candidate must be single-band and template-aligned")
        a = s.read(1)
    if not np.isfinite(a[footprint]).all() or np.any((a[footprint] < 0) | (a[footprint] > 1)):
        raise ValueError("candidate has invalid in-footprint values")
    dots = footprint & (a > 0)
    count = int(dots.sum())
    if not count:
        raise ValueError("empty candidate; novelty is undefined")
    hits = int((dots & witness_halo).sum())
    return {
        "filename": path.name,
        "sha256": sha256_file(path),
        "in_footprint_positive_pixels": count,
        "within_3px_of_witness": hits,
        "directional_overlap": hits / count,
        "literal_duplicate": hits * 10 > count * 7,
        "whole_array_finite_in_0_1": bool(np.isfinite(a).all() and ((a >= 0) & (a <= 1)).all()),
    }
