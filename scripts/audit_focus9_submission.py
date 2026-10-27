#!/usr/bin/env python3
"""Re-audit the candidate GeoTIFF against the nine pinned focus-site rasters.

This is a provenance/format/duplicate audit, not an experiment and not a leaderboard
score estimator. It only fetches the pinned owner-mirror TIFs, verifies their SHA-256
hashes, compares final dot rasters, and writes a machine-readable receipt. It does not
train a model, evaluate hidden test labels, spend a submission slot, or authorize upload.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "focus9_site_registry.json"
CANDIDATE = ROOT / "docs" / "downloads" / "kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif"
RUN_CARD = ROOT / "evidence" / "run_card.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fetch_pinned(site: dict, cache_dir: Path) -> Path:
    """Download one binary GeoTIFF from GitHub's contents API at a pinned commit."""
    path = cache_dir / f"{site['site']}__{Path(site['file']).name}"
    if path.exists() and sha256(path) == site["sha256"]:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".partial")
    api_path = f"repos/{site['repo']}/contents/{site['file']}?ref={site['ref']}"
    try:
        with tmp.open("wb") as out:
            subprocess.run(
                ["gh", "api", api_path, "-H", "Accept: application/vnd.github.raw"],
                stdout=out,
                check=True,
            )
        got = sha256(tmp)
        if got != site["sha256"]:
            raise ValueError(f"SHA-256 mismatch for {site['site']}: {got} != {site['sha256']}")
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)
    return path


def read_grid(path: Path, template_meta: dict) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as ds:
        arr = ds.read(1)
        nodata = ds.nodata
        if nodata is not None and not np.isfinite(nodata):
            nodata = "NaN"
        meta = {
            "count": ds.count,
            "shape": list(ds.shape),
            "crs": str(ds.crs),
            "transform": list(ds.transform)[:6],
            "dtype": ds.dtypes[0],
            "nodata": nodata,
        }
    grid_ok = (
        meta["count"] == 1
        and meta["shape"] == template_meta["shape"]
        and meta["crs"] == template_meta["crs"]
        and meta["transform"] == template_meta["transform"]
        and meta["dtype"] == "float32"
    )
    meta["grid_matches_template"] = bool(grid_ok)
    return arr, meta


def run(candidate: Path, registry_path: Path, cache_dir: Path, out_path: Path) -> dict:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    run_card = json.loads(RUN_CARD.read_text(encoding="utf-8"))
    data_dir = ROOT / ".cache" / "gems_data"
    template_path = data_dir / "sample_submission.tif"
    label_path = data_dir / "labels.tif"
    if not template_path.exists() or not label_path.exists():
        raise FileNotFoundError("Restore the pinned core data first: .venv/bin/python scripts/restore_data.py --group core")

    with rasterio.open(template_path) as ds:
        template = ds.read(1)
        footprint = np.isfinite(template)
        template_meta = {
            "shape": list(ds.shape),
            "crs": str(ds.crs),
            "transform": list(ds.transform)[:6],
            "footprint_pixels": int(footprint.sum()),
        }
    with rasterio.open(label_path) as ds:
        labels = np.isfinite(ds.read(1)) & (ds.read(1) > 0) & footprint

    cand, cand_meta = read_grid(candidate, template_meta)
    cand_sha = sha256(candidate)
    if cand_sha != run_card["raster_sha256"]:
        raise ValueError("Candidate SHA-256 does not match the frozen HTCADS run card")
    cand_dots = footprint & np.isfinite(cand) & (cand >= 0.5)
    all_finite = bool(np.isfinite(cand).all())
    cand_format = {
        **cand_meta,
        "sha256": cand_sha,
        "bytes": candidate.stat().st_size,
        "finite_all_grid": all_finite,
        "nan_all_grid": int(np.isnan(cand).sum()),
        "inf_all_grid": int(np.isinf(cand).sum()),
        "min_all_grid": float(np.nanmin(cand)),
        "max_all_grid": float(np.nanmax(cand)),
        "all_values_in_0_1": bool(all_finite and float(np.min(cand)) >= 0.0 and float(np.max(cand)) <= 1.0),
        "positive_dots_in_footprint": int(cand_dots.sum()),
        "positive_pixels_on_known_catalogue": int((cand_dots & labels).sum()),
        "format_safe": bool(
            cand_meta["grid_matches_template"]
            and all_finite
            and float(np.min(cand)) >= 0.0
            and float(np.max(cand)) <= 1.0
            and int((cand_dots & labels).sum()) == 0
        ),
    }

    site_results = []
    peer_dots: dict[str, np.ndarray] = {}
    for site in registry["sites"]:
        peer_path = fetch_pinned(site, cache_dir)
        if sha256(peer_path) != site["sha256"]:
            raise ValueError(f"Cached source hash mismatch: {peer_path}")
        peer, peer_meta = read_grid(peer_path, template_meta)
        dots = footprint & np.isfinite(peer) & (peer >= 0.5)
        peer_dots[site["site"]] = dots
        distance = distance_transform_edt(~dots)
        within3 = float((cand_dots & (distance <= 3.0)).sum() / max(int(cand_dots.sum()), 1))
        rho = float(spearmanr(cand[footprint], np.nan_to_num(peer[footprint], nan=0.0)).statistic)
        xor = int(np.logical_xor(cand_dots, dots).sum())
        peer_finite = bool(np.isfinite(peer).all())
        site_results.append({
            "site": site["site"],
            "repo": site["repo"],
            "source_ref": site["ref"],
            "source_file": site["file"],
            "source_view_url": f"https://github.com/{site['repo']}/blob/{site['ref']}/{site['file']}",
            "source_download_url": f"https://github.com/{site['repo']}/raw/{site['ref']}/{site['file']}",
            "source_sha256_expected": site["sha256"],
            "source_sha256_verified": sha256(peer_path),
            "source_file_sha_matches_pinned_registry": sha256(peer_path) == site["sha256"],
            "reported_score": site["reported_score"],
            "reported_score_label": "USER/OWNER-REPORTED UNVERIFIED; not organizer-confirmed (no submission receipt stored)",
            "filename": Path(site["file"]).name,
            "positive_dots_in_footprint": int(dots.sum()),
            "raster_metadata": peer_meta,
            "all_grid_finite": peer_finite,
            "nan_pixels_all_grid": int(np.isnan(peer).sum()),
            "portal_range_0_1_safe_as_stored": bool(peer_finite and float(np.min(peer)) >= 0.0 and float(np.max(peer)) <= 1.0),
            "candidate_dots_within_3px_of_peer_fraction": round(within3, 8),
            "candidate_final_raster_spearman_vs_peer": round(rho, 8),
            "exact_sha_match_candidate": sha256(peer_path) == cand_sha,
            "candidate_peer_xor_pixels_in_footprint": xor,
        })

    exact_pairs = []
    for i, (site_a, dots_a) in enumerate(peer_dots.items()):
        for site_b, dots_b in list(peer_dots.items())[i + 1:]:
            xor = int(np.logical_xor(dots_a, dots_b).sum())
            if xor == 0:
                exact_pairs.append({"site_a": site_a, "site_b": site_b, "xor_pixels_in_footprint": 0})

    previous_reg = run_card["registry_comparison"]
    overlap_values = [r["candidate_dots_within_3px_of_peer_fraction"] for r in site_results]
    rho_values = [abs(r["candidate_final_raster_spearman_vs_peer"]) for r in site_results]
    max_overlap_row = max(site_results, key=lambda r: r["candidate_dots_within_3px_of_peer_fraction"])
    max_rho_row = max(site_results, key=lambda r: abs(r["candidate_final_raster_spearman_vs_peer"]))
    gates = {
        "candidate_format_safe": cand_format["format_safe"],
        "unique_sha_from_all_nine": all(not r["exact_sha_match_candidate"] for r in site_results),
        "final_dot_overlap_le_0_70_vs_each_focus_site": max(overlap_values, default=1.0) <= 0.70,
        "final_raster_spearman_le_0_90_vs_each_focus_site": max(rho_values, default=1.0) <= 0.90,
        "recorded_preplacement_surface_spearman_le_0_90": float(previous_reg["pre_placement_surface_max_abs_spearman"]) <= 0.90,
        "recorded_full_registry_final_dot_overlap_le_0_70": float(previous_reg["final_dots_max_detector_3px_overlap"]) <= 0.70,
    }
    out = {
        "schema": "kanlergemsdoe2.focus9_submission_audit.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "score_provenance": {
            "status": "USER_OR_OWNER_REPORTED_UNVERIFIED",
            "organizer_receipt_present": False,
            "note": "The nine historical values are provided in the user prompt and mirrored site records. No DrivenData receipt was available to this audit, so none is labeled ORGANIZER-CONFIRMED.",
        },
        "audit_scope": "One top historical TIF per focus site, from the pinned site-repository commit in the registry; candidate versus these nine final dot rasters.",
        "candidate": {
            "filename": candidate.name,
            "sha256": cand_sha,
            "format": cand_format,
            "live_organizer_score": None,
            "organizer_submission_receipt_present": False,
            "portal_slot_authorized": False,
            "submission_slot_spent": False,
            "holdout_dti_from_frozen_run_card": run_card["holdout_dti"],
            "preplacement_surface_check": {
                "status": "RECORDED_IN_PRIOR_RUN_CARD_NOT_RECOMPUTED_THIS_AUDIT",
                "unique_rasters_checked": previous_reg["unique_rasters_checked"],
                "max_abs_spearman": previous_reg["pre_placement_surface_max_abs_spearman"],
                "threshold": 0.90,
                "pass_recorded": float(previous_reg["pre_placement_surface_max_abs_spearman"]) <= 0.90,
                "limitation": "The pre-placement continuous surface array was not retained in this checkout; this session did not rebuild it or rerun experiments.",
            },
            "recorded_full_registry_final_dots_check": {
                "status": "RECORDED_IN_PRIOR_RUN_CARD_NOT_RECOMPUTED_THIS_AUDIT",
                "unique_rasters_checked": previous_reg["unique_rasters_checked"],
                "max_abs_spearman": previous_reg["final_dots_max_abs_spearman"],
                "max_detector_3px_overlap": previous_reg["final_dots_max_detector_3px_overlap"],
                "threshold_spearman": 0.90,
                "threshold_overlap": 0.70,
            },
            "focus9_final_dots_check": {
                "status": "INDEPENDENTLY_RECOMPUTED_FROM_PINNED_TIFS",
                "sites_checked": len(site_results),
                "max_candidate_dots_within_3px_fraction": max_overlap_row["candidate_dots_within_3px_of_peer_fraction"],
                "max_overlap_site": max_overlap_row["site"],
                "max_abs_final_raster_spearman": max_rho_row["candidate_final_raster_spearman_vs_peer"],
                "max_rho_site": max_rho_row["site"],
                "threshold_overlap": 0.70,
                "threshold_abs_spearman": 0.90,
            },
            "focus9_uniqueness_pass": bool(
                gates["unique_sha_from_all_nine"]
                and gates["final_dot_overlap_le_0_70_vs_each_focus_site"]
                and gates["final_raster_spearman_le_0_90_vs_each_focus_site"]
                and gates["recorded_preplacement_surface_spearman_le_0_90"]
            ),
        },
        "gates": gates,
        "focus_sites": site_results,
        "exact_duplicate_pairs_among_focus_site_top_tifs": exact_pairs,
        "notes": [
            "Candidate dot overlap is directed: fraction of candidate positive pixels within 3 grid pixels of the peer's positive pixels.",
            "Final-raster Spearman is computed over the sample-template footprint. It is not a substitute for the continuous pre-placement surface test.",
            "Scores in this receipt are owner/user-reported historic values, not current leaderboard standings.",
        ],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, default=CANDIDATE)
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--cache-dir", type=Path, default=ROOT / ".cache" / "gems_data" / "focus9")
    parser.add_argument("--out", type=Path, default=ROOT / "evidence" / "focus9_submission_audit_20261027.json")
    args = parser.parse_args()
    result = run(args.candidate, args.registry, args.cache_dir, args.out)
    print(json.dumps({
        "generated_utc": result["generated_utc"],
        "candidate": result["candidate"]["filename"],
        "candidate_sha256": result["candidate"]["sha256"],
        "format_safe": result["candidate"]["format"]["format_safe"],
        "focus9_unique": result["candidate"]["focus9_uniqueness_pass"],
        "max_3px_overlap": result["candidate"]["focus9_final_dots_check"]["max_candidate_dots_within_3px_fraction"],
        "max_rho": result["candidate"]["focus9_final_dots_check"]["max_abs_final_raster_spearman"],
        "exact_duplicate_pairs": result["exact_duplicate_pairs_among_focus_site_top_tifs"],
        "gates": result["gates"],
        "output": str(args.out),
    }, indent=2))
    return 0 if all(result["gates"].values()) and result["candidate"]["focus9_uniqueness_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
