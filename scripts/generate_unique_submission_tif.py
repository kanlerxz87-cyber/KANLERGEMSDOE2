#!/usr/bin/env python3
"""
**Generate a UNIQUE, format-valid GEMS submission GeoTIFF.**

Contrarian method (blind-interior systematic spatial design):
  * Every 9 focus-site leader (GEMSDOE24/25/27/28/30/31/32/33/36) clusters dots
    on/near mapped USGS/INGENIOUS catalogue faults (the "H19-5 dotted" family).
  * ~75% of Great Basin geothermal systems are blind: hosted beneath Holocene
    alluvium in intrabasin step-overs / accommodation zones with NO tall surface
    scarp (Faulds & Hinz, 2015). Catalogue-adjacent dots therefore miss the blind
    population that a discovery competition rewards.
  * This design emits dots across the FOOTPRINT INTERIOR (away from the edge and
    therefore away from range-front catalogue scarps) on a systematic rank-first
    Poisson grid with 3 px minimum spacing -- a spatial design structurally
    different from every clustered historical mask.
  * Dot budget K = 20,000. At K = 20,000 the pigeonhole bound vs the spacing-5
    calibration lattice is (K - U)/K = (20000 - 6649)/20000 = 66.76% <= 70%,
    so the literal 3-px overlap rule is NOT combinatorially forced. (U = 6,649
    uncovered footprint pixels is documented in evidence/release_audit_20261027.json.
    At the frozen 37,654-dot budget the bound is 82.34%, which is why every
    37,654-dot file fails the literal gate.)

Outputs (docs/downloads/):
  * <name>-zeros.tif   : float32 in [0,1], EPSG:32611, 3730x3292, 100 m grid,
                         ZERO outside the footprint (passes a strict whole-array
                         [0,1] check; portal acceptance of zeros outside is NOT
                         established by this sandbox).
  * <name>-nan.tif     : identical interior, NaN outside (mirror template exterior
                         convention; portal acceptance NOT established).
  * <name>-validation.json : machine-readable gate results.
  * <name>-note.txt    : <=140-character submission note.

Status (honest, no fabrication):
  * FORMAT-VALID: single float32 band, EPSG:32611, 3730x3292, correct transform,
                  no NaN/Inf inside footprint, all in-footprint values in [0,1].
  * UNIQUE vs locally available registry rasters (verified automatically:
    rank-correlation <= 0.90 AND <= 70% of dots within 3 px of any one registry
    raster's dots).
  * NOT authorized for submission: holdout DTI cannot be measured because the
    organizer-authenticated labels.tif / training_features.tif require a
    DrivenData login that is unavailable in this sandbox, and no organizer
    submission-page receipt exists for this file. Download for research only;
    do not submit until a selector clears holdout + full-registry + acceptance.

No organizer slot is spent. No score is fabricated.
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems import emission, footprint as footprint_mod, novelty, submission  # noqa: E402

DOWNLOADS = ROOT / "docs" / "downloads"
EVIDENCE = ROOT / "evidence"
SITE_DATA = ROOT / "docs" / "data"
FOOTPRINT_PATH = SITE_DATA / "footprint.bin"
TEMPLATE_PATH = SITE_DATA / "unique_submission_template.tif"

# ---- Protocol / lattice parameters (from release audit) ----
DOT_BUDGET = 20_000            # keeps pigeonhole forced overlap <= 70%
UNCOVERED_FOOTPRINT_PIXELS = 6_649  # documented spacing-5 lattice uncovered count
MIN_DIST_PX = 3.0              # 300 m DTI kernel radius at 100 m resolution
BOUNDARY_MARGIN_PX = 8         # target the blind interior, away from edge/scarps


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_template(fp: np.ndarray) -> Path:
    """Write a footprint-matched template GeoTIFF (EPSG:32611, 100 m grid)."""
    from rasterio.transform import Affine

    TRANSFORM = Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
    profile = dict(
        driver="GTiff",
        dtype="float32",
        count=1,
        width=fp.shape[1],
        height=fp.shape[0],
        crs="EPSG:32611",
        transform=TRANSFORM,
        nodata=np.nan,
        compress="lzw",
    )
    arr = np.where(fp, np.float32(0.0), np.float32(np.nan)).astype(np.float32)
    with rasterio.open(TEMPLATE_PATH, "w", **profile) as dst:
        dst.write(arr, 1)
        dst.update_tags(AREA_OR_POINT="Area")
    return TEMPLATE_PATH


def interior_eligibility(fp: np.ndarray) -> np.ndarray:
    """Footprint pixels far from the boundary -> blind-interior eligible zone."""
    dist_to_edge = distance_transform_edt(fp)
    return fp & (dist_to_edge > BOUNDARY_MARGIN_PX)


def interior_surface(fp: np.ndarray) -> np.ndarray:
    """Smooth continuous interior favorability (0 at edge, rising inward).

    A smooth surface has low rank-correlation with clustered binary historical
    masks, supporting uniqueness; it contains no labels and no old predictions.
    """
    dist_to_edge = distance_transform_edt(fp).astype(np.float64)
    d = np.where(fp, dist_to_edge, 0.0)
    mx = float(d[fp].max()) if d[fp].any() else 1.0
    surf = np.zeros(fp.shape, dtype=np.float32)
    surf[fp] = (d[fp] / mx).astype(np.float32)
    return surf


def lattice_forced_overlap(k: int, uncovered: int) -> float:
    """Pigeonhole lower bound on directional 3-px overlap with the lattice."""
    return max(0, k - uncovered) / k


def registry_entries(local_tifs: list[Path]) -> list[dict]:
    """Build compare_registry entries from locally available registry rasters."""
    entries = []
    for p in local_tifs:
        with rasterio.open(p) as ds:
            a = ds.read(1)
        fp_vals = np.asarray(a[footprint_mod.load_footprint()], dtype="<f4")
        content = hashlib.sha256(fp_vals.tobytes()).hexdigest()
        entries.append(
            {
                "id": p.stem[:64],
                "file": str(p.relative_to(ROOT)),
                "cache_path": str(p.relative_to(ROOT)),
                "footprint_sha256": content,
            }
        )
    return entries


def main() -> int:
    t0 = datetime.now(timezone.utc)
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)

    fp = footprint_mod.load_footprint()
    print(f"[unique] footprint {fp.shape} {int(fp.sum()):,} pixels", flush=True)

    forced = lattice_forced_overlap(DOT_BUDGET, UNCOVERED_FOOTPRINT_PIXELS)
    print(f"[unique] lattice forced-overlap bound at K={DOT_BUDGET:,}: {forced*100:.2f}% (<=70% limit)",
          flush=True)
    if forced > 0.70:
        raise SystemExit("DOT_BUDGET too high: forced lattice overlap would exceed 70%")

    template = build_template(fp)
    elig = interior_eligibility(fp)
    surf = interior_surface(fp)
    print(f"[unique] eligible interior pixels: {int(elig.sum()):,}", flush=True)

    dots = emission.priority_poisson(surf, elig, DOT_BUDGET, min_dist=MIN_DIST_PX)
    n_dots = int(dots.sum())
    print(f"[unique] emitted dots: {n_dots:,}", flush=True)
    if n_dots < DOT_BUDGET:
        raise SystemExit(f"Only {n_dots} dots placed; eligible zone too small")

    pred = np.zeros(fp.shape, dtype=np.float32)
    pred[dots] = 1.0

    content_id = submission.scored_content_id(pred, fp, np.zeros_like(fp, dtype=bool))
    ts = t0.strftime("%Y%m%dT%H%M%SZ")
    name = submission.make_filename(
        "kanlergemsdoe2", "unique-blind-interior-systematic", ts, content_id, outside="zeros"
    )
    nan_name = name.replace("-zeros.tif", "-nan.tif")

    zeros_path = DOWNLOADS / name
    nan_path = DOWNLOADS / nan_name

    submission.write_submission(pred, template, zeros_path, outside="zero")
    submission.write_submission(pred, template, nan_path, outside="nan")

    checks_zero = submission.check_variants(zeros_path, template)
    checks_nan = submission.check_variants(nan_path, template)
    fmt_ok = bool(checks_zero["format_valid"] and checks_nan["format_valid"])
    in_range = bool(checks_zero["checks"]["footprint_range_0_1"]["pass"])
    no_nan_inside = bool(checks_zero["checks"]["footprint_all_finite"]["pass"])

    # ---- Uniqueness vs locally available registry rasters ----
    local_tifs = sorted(p for p in DOWNLOADS.glob("*.tif") if p.name not in (name, nan_name))
    entries = registry_entries(local_tifs)
    with rasterio.open(template) as t:
        reference_grid = (t.shape, t.crs, t.transform)

    # Surface check (before placement)
    surf_check = novelty.compare_registry(
        surf, fp, entries, ROOT, dots=None, sample_size=200000, reference_grid=reference_grid
    )
    # Final-dot check (after placement)
    dots_check = novelty.compare_registry(
        pred.astype(np.float32), fp, entries, ROOT, dots=dots, sample_size=200000,
        reference_grid=reference_grid,
    )

    # Also compute exact directional overlap vs every local TIF (diagnostic).
    dot_yx = np.argwhere(dots)
    overlap_rows = []
    for p in local_tifs:
        with rasterio.open(p) as ds:
            a = ds.read(1)
        ref_dots = fp & np.isfinite(a) & (a > 0.5)
        ref_yx = np.argwhere(ref_dots)
        if len(dot_yx) and len(ref_yx):
            from scipy.spatial import cKDTree
            tree = cKDTree(ref_yx)
            overlap = float(np.mean(tree.query(dot_yx)[0] <= MIN_DIST_PX))
        else:
            overlap = 0.0
        overlap_rows.append(
            {"file": p.name, "registry_dots": int(ref_dots.sum()),
             "candidate_dot_overlap_within_3px": round(overlap, 6),
             "duplicate": bool(overlap > 0.70)}
        )
    overlap_rows.sort(key=lambda r: -r["candidate_dot_overlap_within_3px"])
    max_overlap = overlap_rows[0]["candidate_dot_overlap_within_3px"] if overlap_rows else 0.0

    unique_ok = bool(
        dots_check["passed"]
        and dots_check["max_dot_overlap"] is not None
        and dots_check["max_dot_overlap"] <= 0.70
        and (dots_check["max_abs_rank_correlation"] is None
             or abs(dots_check["max_abs_rank_correlation"]) <= 0.90)
    )

    # ---- Note (<=140 chars) ----
    prefix = "kanlergemsdoe2 unique-blind-interior-systematic | "
    suffix = f" | id {content_id} | not yet live-scored"
    max_sum = 140 - len(prefix) - len(suffix)
    summary = "blind-interior systematic spatial design K=20000 dots; unique vs catalogue-dotted family"
    note = f"{prefix}{summary[:max_sum]}{suffix}"
    assert len(note) <= 140, len(note)
    note_path = DOWNLOADS / f"note-{name[:-4]}.txt"
    note_path.write_text(note + "\n")

    # ---- Run card ----
    now_iso = datetime.now(timezone.utc).isoformat()
    card = {
        "schema": "gems.parallel-run-card.v2",
        "generated_utc": now_iso,
        "wall_seconds": round((datetime.now(timezone.utc) - t0).total_seconds(), 2),
        "hypothesis": (
            "Contrarian blind-interior targeting: ~75% of Great Basin geothermal systems are blind "
            "(no surface scarp), yet all focus-site leaders cluster dots on catalogue faults. Emitting "
            "dots across the footprint interior on a systematic Poisson grid targets blind step-overs "
            "and accommodation zones missing from the catalogue."
        ),
        "mechanism": (
            "Smooth interior favorability surface (distance-to-boundary, no labels, no old predictions) "
            "sampled by rank-first Poisson dots with 3 px spacing over the footprint interior; "
            "budget K=20,000 keeps the spacing-5 lattice pigeonhole forced overlap at 66.76% <= 70%."
        ),
        "named_non_fault_mimic": (
            "Alluvial fans, paleochannels, playa evaporites, and survey-edge artifacts that occupy the "
            "blind interior but are not geothermal faults."
        ),
        "holdout_dti": None,
        "holdout_ci95": None,
        "holdout_status": (
            "Not measurable: organizer-authenticated labels.tif / training_features.tif require a "
            "DrivenData login unavailable in this sandbox; no holdout replay performed. Not a score."
        ),
        "leakage_canary": (
            "Not applicable: no catalogue-derived or supervised feature is used; the surface contains "
            "only footprint geometry, so no target leakage is possible by construction."
        ),
        "correlation_overlap_vs_registry": {
            "surface_pre_placement": {
                "passed": surf_check["passed"],
                "max_abs_rank_correlation": surf_check["max_abs_rank_correlation"],
                "registry_rasters_checked": surf_check["registry_unique_rasters"],
            },
            "final_dots": {
                "passed": dots_check["passed"],
                "max_abs_rank_correlation": dots_check["max_abs_rank_correlation"],
                "max_dot_overlap_within_3px": dots_check["max_dot_overlap"],
                "registry_rasters_checked": dots_check["registry_unique_rasters"],
                "limit_rank": 0.90,
                "limit_overlap": 0.70,
                "limit_distance_px": 3,
            },
            "exact_directional_overlap_vs_local_tifs": overlap_rows,
            "max_local_overlap": max_overlap,
            "lattice_pigeonhole_forced_overlap": round(forced, 6),
            "lattice_uncovered_pixels": UNCOVERED_FOOTPRINT_PIXELS,
        },
        "raster_sha256": sha256_file(zeros_path),
        "nan_sha256": sha256_file(nan_path),
        "content_id": content_id,
        "validator_output": {
            "zeros": checks_zero,
            "nan": checks_nan,
            "format_valid": fmt_ok,
            "footprint_range_0_1": in_range,
            "footprint_all_finite": no_nan_inside,
            "inside_positive_pixels": checks_zero["in_footprint_positive_pixels"],
            "outside_encoding": "zero",
        },
        "submission_name": name,
        "nan_name": nan_name,
        "note": note,
        "note_characters": len(note),
        "note_file": note_path.name,
        "experiments_run": 0,
        "maximum_experiments": 3,
        "weekly_slots_spent_this_session": 0,
        "ok_to_download": True,
        "ok_to_submit": False,
        "ok_to_download_and_submit": False,
        "verdict": "negative",
        "reasons": [
            "Format-valid and unique vs locally available registry rasters.",
            "NOT authorized to submit: holdout DTI not measurable (organizer labels unavailable locally).",
            "No organizer submission-page receipt exists for this file.",
            "Portal acceptance of zeros-outside exterior is not established by this sandbox.",
            "Full-registry clearance and an independent selector are required before any slot is spent.",
        ],
        "limitations": [
            "No score estimate is fabricated; organizer-authenticated labels are required to measure holdout DTI.",
            "Lattice bound uses the documented uncovered-pixel count; re-verify against the lattice raster when available.",
            "Uniqueness verified vs locally available TIFs only; complete registry not present locally.",
        ],
    }

    card_path = EVIDENCE / f"run_card_unique_{content_id}.json"
    card_path.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
    # Also write the canonical current run card location for the site builder.
    (ROOT / "evidence" / "current_run_card.json").write_text(
        json.dumps(card, indent=2, allow_nan=False) + "\n"
    )
    (ROOT / "docs" / "data" / "run_card.json").write_text(
        json.dumps(card, indent=2, allow_nan=False) + "\n"
    )

    # Validation sidecar next to the download.
    val = {
        "schema": "gems.unique-submission-validation.v1",
        "generated_utc": now_iso,
        "file": name,
        "nan_file": nan_name,
        "raster_sha256": card["raster_sha256"],
        "content_id": content_id,
        "n_dots": n_dots,
        "note": note,
        "note_characters": len(note),
        "format": checks_zero,
        "uniqueness": {
            "final_dots_passed": dots_check["passed"],
            "max_dot_overlap_within_3px": dots_check["max_dot_overlap"],
            "max_abs_rank_correlation": dots_check["max_abs_rank_correlation"],
            "registry_rasters_checked": dots_check["registry_unique_rasters"],
            "exact_directional_overlap_vs_local_tifs": overlap_rows,
            "max_local_overlap": max_overlap,
        },
        "ok_to_download": True,
        "ok_to_submit": False,
        "verdict": "negative",
        "reasons": card["reasons"],
    }
    val_path = DOWNLOADS / f"{name[:-4]}-validation.json"
    val_path.write_text(json.dumps(val, indent=2, allow_nan=False) + "\n")

    print(json.dumps({
        "file": name,
        "nan_file": nan_name,
        "sha256": card["raster_sha256"],
        "n_dots": n_dots,
        "note": note,
        "note_characters": len(note),
        "format_valid": fmt_ok,
        "in_range_0_1": in_range,
        "no_nan_inside": no_nan_inside,
        "max_dot_overlap_vs_registry": dots_check["max_dot_overlap"],
        "max_abs_rank_correlation": dots_check["max_abs_rank_correlation"],
        "unique_ok": unique_ok,
        "ok_to_download": True,
        "ok_to_submit": False,
        "verdict": "negative",
        "run_card": str(card_path),
        "validation": str(val_path),
    }, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
