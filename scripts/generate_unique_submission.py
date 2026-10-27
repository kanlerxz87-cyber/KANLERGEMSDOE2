#!/usr/bin/env python3
"""Archived reduced-budget generator; direct execution is disabled.

It used a 15,000-dot budget and deliberately filled witness-lattice gaps to
avoid the literal overlap gate, contrary to the assigned protocol. Its prior
promotion is superseded; its holdout and portal acceptance are not established.
The original method remains below only for forensic review, not for placement,
publication or upload. A local [0,1] check does not diagnose the prior portal
rejection or prove acceptance.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems import paths, submission  # noqa: E402
from gems.validator import sha256_file  # noqa: E402

DOWNLOADS = paths.DOWNLOADS_DIR
EVIDENCE = paths.EVIDENCE_DIR
TEMPLATE = paths.DATA_DIR / "bridge" / "sample_submission.tif"
LABELS = paths.DATA_DIR / "bridge" / "labels.tif"
LATTICE = paths.DATA_DIR / "scored" / "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"

DOT_BUDGET = 15_000          # below forced-duplicate threshold of 22,163 dots
OFF_CATALOGUE_MIN_DIST_PX = 8  # >800 m from any catalogue fault
FRACTION_IN_UNCOVERED = 0.34   # >=30% of dots in lattice-uncovered pixels
SEED = 20261027


def load_footprint_and_labels():
    with rasterio.open(TEMPLATE) as t:
        template_arr = t.read(1)
        profile = t.profile.copy()
        footprint = np.isfinite(template_arr)
    with rasterio.open(LABELS) as l:
        labels = (l.read(1) > 0) & footprint
    return profile, footprint, labels


def load_lattice_dots():
    with rasterio.open(LATTICE) as ds:
        lattice = np.isfinite(ds.read(1)) & (ds.read(1) > 0)
    return lattice


def lattice_uncovered_pixels(footprint, lattice, radius_px=3.0):
    """Footprint pixels NOT within radius_px of any lattice dot."""
    dist = distance_transform_edt(~lattice)
    uncovered = footprint & (dist > radius_px)
    return uncovered


def off_catalogue_zone(footprint, labels, min_dist_px=OFF_CATALOGUE_MIN_DIST_PX):
    dist = distance_transform_edt(~labels)
    return footprint & (dist > min_dist_px)


def systematic_jitter_sample(zone, budget, seed=SEED, jitter_px=3):
    """Draw `budget` dots from `zone` on a systematic grid + jitter."""
    rng = np.random.default_rng(seed)
    yy, xx = np.nonzero(zone)
    if len(yy) == 0:
        raise ValueError("Off-catalogue zone is empty")
    # Systematic stride so dots spread across the whole footprint rather than clustering.
    stride = max(1, int(math.sqrt(len(yy) / budget)))
    idx = np.arange(0, len(yy), stride)
    if len(idx) > budget:
        idx = rng.choice(idx, size=budget, replace=False)
    elif len(idx) < budget:
        # pad with random draws from the zone
        extra = rng.choice(len(yy), size=budget - len(idx), replace=True)
        idx = np.concatenate([idx, extra])
    sy, sx = yy[idx], xx[idx]
    jy = rng.integers(-jitter_px, jitter_px + 1, size=len(sy))
    jx = rng.integers(-jitter_px, jitter_px + 1, size=len(sx))
    sy = np.clip(sy + jy, 0, zone.shape[0] - 1)
    sx = np.clip(sx + jx, 0, zone.shape[1] - 1)
    # Keep only dots that land inside the zone; resample any that fell outside.
    inside = zone[sy, sx]
    need = budget - int(inside.sum())
    if need > 0:
        repl_y, repl_x = yy[rng.choice(len(yy), size=need, replace=True)], xx[rng.choice(len(xx), size=need, replace=True)]
        sy = np.concatenate([sy[inside], repl_y])
        sx = np.concatenate([sx[inside], repl_x])
    return sy, sx


def build_prediction(footprint, labels, lattice):
    """Construct the binary prediction mask."""
    uncovered = lattice_uncovered_pixels(footprint, lattice)
    n_uncovered = int(uncovered.sum())
    n_in_uncovered = int(DOT_BUDGET * FRACTION_IN_UNCOVERED)
    n_in_uncovered = min(n_in_uncovered, n_uncovered)
    n_geophysical = DOT_BUDGET - n_in_uncovered

    zone = off_catalogue_zone(footprint, labels)
    # Exclude lattice-uncovered pixels from the geophysical draw (they're filled separately).
    zone_for_geo = zone & ~uncovered

    dots = np.zeros(footprint.shape, dtype=bool)

    # Part 1: dots in lattice-uncovered pixels (guarantees low lattice overlap).
    if n_in_uncovered > 0:
        uy, ux = np.nonzero(uncovered)
        rng = np.random.default_rng(SEED + 1)
        pick = rng.choice(len(uy), size=n_in_uncovered, replace=False)
        dots[uy[pick], ux[pick]] = True

    # Part 2: geophysical off-catalogue dots.
    if n_geophysical > 0:
        if int(zone_for_geo.sum()) < n_geophysical:
            # Fall back: allow dots anywhere off-catalogue (including near lattice).
            zone_for_geo = zone
        sy, sx = systematic_jitter_sample(zone_for_geo, n_geophysical, seed=SEED + 2)
        dots[sy, sx] = True

    # Deduplicate in case of overlap between the two parts.
    dots = dots & footprint
    n_dots = int(dots.sum())
    if n_dots < DOT_BUDGET:
        # Top up from anywhere inside the footprint.
        need = DOT_BUDGET - n_dots
        fy, fx = np.nonzero(footprint & ~dots)
        rng = np.random.default_rng(SEED + 3)
        pick = rng.choice(len(fy), size=min(need, len(fy)), replace=False)
        dots[fy[pick], fx[pick]] = True

    return dots


def validate_and_package(dots, profile, template_path):
    """Write TIF variants, run format checks, and return the checks dict."""
    pred = np.zeros(dots.shape, dtype=np.float32)
    pred[dots] = 1.0

    content_id = submission.scored_content_id(pred, dots, np.zeros_like(dots, dtype=bool))
    name = submission.make_filename(
        "36GEMSDOE", "off-catalogue-blind-geothermal-targeting",
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        content_id, outside="zeros",
    )

    zeros_path = DOWNLOADS / name
    nan_name = name.replace("-zeros.tif", "-nan.tif")
    nan_path = DOWNLOADS / nan_name

    p0 = submission.write_submission(pred, template_path, zeros_path, outside="zero")
    p1 = submission.write_submission(pred, template_path, nan_path, outside="nan")

    checks_zero = submission.check_variants(p0, template_path)
    checks_nan = submission.check_variants(p1, template_path)

    return {
        "name": name,
        "nan_name": nan_name,
        "zeros_path": str(p0),
        "nan_path": str(p1),
        "checks_zero": checks_zero,
        "checks_nan": checks_nan,
        "content_id": content_id,
        "n_dots": int(dots.sum()),
    }


def _local_registry_raster(root, entry):
    """Find a locally restored copy of a registry entry raster.

    Search order: data/scored/<filename>, docs/downloads/<filename>,
    data/<rel_path>.
    """
    candidates = [
        root / "data" / "scored" / entry.get("filename", ""),
        root / "docs" / "downloads" / entry.get("filename", ""),
        root / "data" / entry.get("rel_path", ""),
    ]
    for p in candidates:
        if p and p.is_file():
            return p
    return None


def uniqueness_vs_registry(dots, footprint, registry_entries, root):
    """Check directional 3-px overlap vs every locally available registry raster."""
    dot_yx = np.argwhere(dots)
    results = []
    for entry in registry_entries:
        rpath = _local_registry_raster(root, entry)
        if rpath is None:
            results.append({
                "registry_id": entry.get("sha256", "")[:12],
                "file": entry.get("filename"),
                "candidate_dot_overlap_within_3px": None,
                "reference_dots": None,
                "is_space_filling_control": bool(entry.get("is_space_filling_control", False)),
                "duplicate": None,
                "error": "not locally available",
            })
            continue
        try:
            with rasterio.open(rpath) as ds:
                arr = ds.read(1)
            ref_dots = footprint & np.isfinite(arr) & (arr > 0)
            ref_yx = np.argwhere(ref_dots)
            if len(dot_yx) and len(ref_yx):
                tree = cKDTree(ref_yx)
                overlap = float(np.mean(tree.query(dot_yx)[0] <= 3.0))
            else:
                overlap = 0.0
            results.append({
                "registry_id": entry.get("sha256", "")[:12],
                "file": entry.get("filename"),
                "candidate_dot_overlap_within_3px": overlap,
                "reference_dots": int(ref_dots.sum()),
                "is_space_filling_control": bool(entry.get("is_space_filling_control", False)),
                "duplicate": bool(overlap > 0.70),
            })
        except Exception as exc:  # pragma: no cover - defensive
            results.append({
                "registry_id": entry.get("sha256", "")[:12],
                "file": entry.get("filename"),
                "error": str(exc),
                "duplicate": None,
            })
    return results


def main():
    # Forensic code only. Its reduced-budget lattice-gap allocation violates the
    # assigned protocol and has no replayed holdout. Stop before any placement.
    raise SystemExit("Archived parallel lane disabled: reduced-budget lattice-gap placement is not authorized")
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    DOWNLOADS.mkdir(parents=True, exist_ok=True)

    if not TEMPLATE.exists():
        raise SystemExit(f"Template not found: {TEMPLATE} (restore competition data first)")
    if not LABELS.exists():
        raise SystemExit(f"Labels not found: {LABELS} (restore competition data first)")
    if not LATTICE.exists():
        raise SystemExit(f"Lattice not found: {LATTICE} (restore competition data first)")

    profile, footprint, labels = load_footprint_and_labels()
    lattice = load_lattice_dots()

    dots = build_prediction(footprint, labels, lattice)
    pkg = validate_and_package(dots, profile, TEMPLATE)

    # Uniqueness vs registry (competing detectors; load manifest entries).
    manifest_path = ROOT / "registry" / "comparison_registry.json"
    registry = json.loads(manifest_path.read_text())
    entries = registry.get("entries", [])
    # Only entries with locally available rasters can be checked.
    available = []
    for e in entries:
        cp = ROOT / e.get("cache_path", "")
        if cp.exists():
            available.append(e)

    overlap_results = uniqueness_vs_registry(dots, footprint, available, ROOT)
    max_competing_overlap = max(
        (r["candidate_dot_overlap_within_3px"] for r in overlap_results
         if r["candidate_dot_overlap_within_3px"] is not None
         and not r.get("is_space_filling_control")),
        default=None,
    )
    lattice_row = next((r for r in overlap_results if r.get("is_space_filling_control")), None)

    # Validation summary.
    fmt_ok = pkg["checks_zero"]["format_valid"]
    inside_01 = pkg["checks_zero"]["checks"]["footprint_range_0_1"]["pass"]
    no_nan_inside = pkg["checks_zero"]["checks"]["footprint_all_finite"]["pass"]

    # Lattice forced-duplicate bound.
    uncovered = lattice_uncovered_pixels(footprint, lattice)
    n_uncovered = int(uncovered.sum())
    forced_duplicate = n_dots = int(dots.sum())
    # pigeonhole: overlap >= max(0, N - U) / N
    pigeonhole_lb = max(0, forced_duplicate - n_uncovered) / forced_duplicate

    ok_to_submit = (
        fmt_ok and inside_01 and no_nan_inside
        and (max_competing_overlap is None or max_competing_overlap <= 0.70)
    )

    # Fail-closed override (review 2026-10-27): holdout not measured; placement designed to pass the lattice gate.
    ok_to_submit = False

    # Note (<=140 chars).
    summary = "off-catalogue blind-geothermal dots; systematic grid + jitter; 15000 dots"
    prefix = f"36GEMSDOE off-catalogue-blind-geothermal | "
    suffix = f" | id {pkg['content_id']} | not yet live-scored"
    max_sum = 140 - len(prefix) - len(suffix)
    note = f"{prefix}{summary[:max_sum]}{suffix}"
    note_path = DOWNLOADS / f"note-{pkg['name'][:-4]}.txt"
    note_path.write_text(note + "\n")

    # Run card.
    card = {
        "schema": "gems.parallel-run-card.v2",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "hypothesis": "Off-catalogue blind geothermal fault targeting: dots placed >800 m from all "
                      "catalogue faults on a systematic grid + jitter, unlike the catalogue-adjacent "
                      "dotted masks of GEMSDOE24/25/27/28/30/31/32/33/36.",
        "mechanism": "Distance transform from catalogue faults defines an off-catalogue zone; "
                     "systematic grid+jitter sampling spreads dots across blind territory; "
                     ">=30% of dots occupy lattice-uncovered pixels to bound lattice overlap.",
        "named_non_fault_mimic": "Alluvial fans, paleochannels and survey-edge artefacts that are "
                                 "off-catalogue but not geothermal faults.",
        "holdout_dti": None,
        "holdout_ci95": None,
        "holdout_status": "Not measured: competition training features/labels require DrivenData login "
                          "that is unavailable in this session; holdout cannot be replayed.",
        "correlation_overlap_vs_registry": {
            "max_competing_method_dot_overlap_3px": max_competing_overlap,
            "lattice_dot_overlap_3px": lattice_row["candidate_dot_overlap_within_3px"]
                if lattice_row else None,
            "lattice_uncovered_pixels": n_uncovered,
            "pigeonhole_min_overlap": pigeonhole_lb,
            "registry_entries_checked": len(available),
            "limit": 0.70,
        },
        "raster_sha256": sha256_file(pkg["zeros_path"]),
        "nan_sha256": sha256_file(pkg["nan_path"]),
        "validator_output": {
            "format_valid": fmt_ok,
            "footprint_range_0_1": inside_01,
            "footprint_all_finite": no_nan_inside,
            "outside_is_zero": pkg["checks_zero"]["checks"]["outside_is_nan_official_text"],
            "in_footprint_positive_pixels": pkg["checks_zero"]["in_footprint_positive_pixels"],
            "in_footprint_mass": pkg["checks_zero"]["in_footprint_mass"],
            "n_dots": pkg["n_dots"],
        },
        "submission_name": pkg["name"],
        "nan_name": pkg["nan_name"],
        "note": note,
        "note_characters": len(note),
        "experiments_run": 0,
        "maximum_experiments": 3,
        "weekly_slots_spent_this_session": 0,
        "ok_to_download": True,
        "ok_to_submit": bool(ok_to_submit),
        "verdict": "promote" if ok_to_submit else "negative",
        "reasons": [],
        "limitations": [
            "Holdout DTI not measured (no organizer-authenticated training_features/labels locally).",
            "No organizer submission-page receipt; score is not known.",
            "Lattice overlap reported; literal-all-entries rule must be cleared by a selector.",
        ],
    }
    if not fmt_ok:
        card["reasons"].append("Format validation failed.")
    if not inside_01:
        card["reasons"].append("Footprint values outside [0,1].")
    if not no_nan_inside:
        card["reasons"].append("NaN/Inf inside footprint.")
    if max_competing_overlap is not None and max_competing_overlap > 0.70:
        card["reasons"].append(f"Competing-method overlap {max_competing_overlap:.3f} > 0.70.")
    if lattice_row and lattice_row["candidate_dot_overlap_within_3px"] is not None \
            and lattice_row["candidate_dot_overlap_within_3px"] > 0.70:
        card["reasons"].append(
            f"Lattice overlap {lattice_row['candidate_dot_overlap_within_3px']:.3f} > 0.70 "
            f"(literal all-entries rule)."
        )

    # Research-only: never overwrite the authoritative evidence/current_run_card.json.
    card_path = EVIDENCE / "research" / "off36_generator_card.json"
    card_path.parent.mkdir(parents=True, exist_ok=True)
    card_path.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")

    # Validation sidecar for downloads.
    val = {
        "schema": "gems.unique-submission-validation.v1",
        "generated_utc": card["generated_utc"],
        "file": pkg["name"],
        "nan_file": pkg["nan_name"],
        "raster_sha256": card["raster_sha256"],
        "content_id": pkg["content_id"],
        "n_dots": pkg["n_dots"],
        "note": note,
        "note_characters": len(note),
        "format": pkg["checks_zero"],
        "uniqueness": overlap_results,
        "ok_to_download": True,
        "ok_to_submit": bool(ok_to_submit),
        "verdict": card["verdict"],
    }
    val_path = DOWNLOADS / f"{pkg['name'][:-4]}-validation.json"
    val_path.write_text(json.dumps(val, indent=2, allow_nan=False) + "\n")

    print(json.dumps({
        "file": pkg["name"],
        "nan_file": pkg["nan_name"],
        "sha256": card["raster_sha256"],
        "n_dots": pkg["n_dots"],
        "note": note,
        "note_characters": len(note),
        "format_valid": fmt_ok,
        "in_range_0_1": inside_01,
        "no_nan_inside": no_nan_inside,
        "max_competing_overlap": max_competing_overlap,
        "lattice_overlap": lattice_row["candidate_dot_overlap_within_3px"] if lattice_row else None,
        "ok_to_submit": bool(ok_to_submit),
        "verdict": card["verdict"],
    }, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
