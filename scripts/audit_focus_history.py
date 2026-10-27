#!/usr/bin/env python3
"""Independently audit existing focus rasters and the literal registry stop.

This is a forensic comparison of prior files, not a model experiment. The
reported historical values are user/owner claims, not organizer receipts. It
retrieves only public GitHub mirrors and never uploads or spends a slot.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems import footprint  # noqa: E402
from gems.validator import sha256_file  # noqa: E402

DATA = ROOT / "data"
LEDGER = ROOT / "evidence/nine_site_audit.json"
OUTPUT = ROOT / "evidence/focus_reaudit_20261027.json"
LATTICE = DATA / "scored/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"
LATTICE_SHA = "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2"
PRIOR_LOCAL_FILES = [
    "kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif",
    "kanlergemsdoe2-kg2-mghv-exp-1-37654-20261026-f5a469e94b14-zeros.tif",
    "kanlergemsdoe2-kg2h1-fvca-submod-20261026T235000Z-cab53e1b-zeros.tif",
]


def gh(*args: str) -> bytes:
    return subprocess.run(["gh", "api", *args], check=True, capture_output=True).stdout


def fetch(row: dict) -> dict:
    """Pin the default-branch commit and verify the retrieved file against the old ledger."""
    repo, rel = row["repo"], row["best_file_in_repo"]
    try:
        commit = json.loads(gh(f"repos/{repo}/commits/main"))["sha"]
        if len(commit) != 40 or any(x not in "0123456789abcdef" for x in commit):
            raise ValueError("GitHub did not return a full commit SHA")
        dest = DATA / "focus_history" / f"{row['site']}.tif"
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists() or sha256_file(dest) != row["sha256"]:
            content = gh(f"repos/{repo}/contents/{rel}?ref={commit}", "-H", "Accept: application/vnd.github.raw")
            if hashlib.sha256(content).hexdigest() != row["sha256"]:
                raise ValueError("upstream file differs from historical ledger SHA-256")
            tmp = dest.with_suffix(".partial")
            tmp.write_bytes(content)
            tmp.replace(dest)
        return {"ok": True, "commit": commit, "path": str(dest.relative_to(ROOT))}
    except (subprocess.CalledProcessError, OSError, ValueError, KeyError) as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def grid(ds: rasterio.io.DatasetReader):
    return ds.shape, ds.crs, ds.transform


def inspect(path: Path, template_grid, fp: np.ndarray) -> tuple[dict, np.ndarray]:
    with rasterio.open(path) as ds:
        matches = grid(ds) == template_grid
        if not matches or ds.count != 1:
            raise ValueError(f"Grid or band mismatch: {path}")
        a = ds.read(1)
        dtype, nodata = ds.dtypes[0], ds.nodata
    mask = fp & np.isfinite(a) & (a > 0)
    values = a[fp]
    return {
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "single_band": True,
        "grid_matches_mirrored_template": matches,
        "dtype": dtype,
        "nodata": "nan" if nodata is not None and np.isnan(nodata) else nodata,
        "inside_all_finite": bool(np.isfinite(values).all()),
        "inside_range_0_1": bool(np.isfinite(values).all() and ((values >= 0) & (values <= 1)).all()),
        "all_cells_finite_and_in_range": bool(np.isfinite(a).all() and ((a >= 0) & (a <= 1)).all()),
        "positive_pixels_inside": int(mask.sum()),
        "positive_pixels_outside": int((~fp & np.isfinite(a) & (a > 0)).sum()),
    }, mask


def main() -> int:
    history = json.loads(LEDGER.read_text())["focus_9_sites"]
    if len(history) != 9 or len({x["site"] for x in history}) != 9:
        raise SystemExit("Nine distinct focus rows required")
    template = DATA / "sample_submission.tif"
    with rasterio.open(template) as ds:
        template_grid = grid(ds)
        fp = np.isfinite(ds.read(1))
    if not np.array_equal(fp, footprint.load_footprint()):
        raise SystemExit("Restored template footprint differs from committed payload")
    if sha256_file(LATTICE) != LATTICE_SHA:
        raise SystemExit("Registry lattice is missing or has the wrong pinned SHA-256")
    with rasterio.open(LATTICE) as ds:
        if grid(ds) != template_grid or ds.count != 1:
            raise SystemExit("Registry lattice grid differs from template")
        a = ds.read(1)
    lattice = fp & np.isfinite(a) & (a > 0)
    distance = distance_transform_edt(~lattice)
    covered = fp & (distance <= 3.0)
    nfp = int(fp.sum())
    uncovered = int((fp & ~covered).sum())

    with ThreadPoolExecutor(max_workers=5) as executor:
        fetched = list(executor.map(fetch, history))
    rows, masks, missing = [], {}, []
    for rec, source in zip(history, fetched):
        row = {
            "site": rec["site"],
            "site_url": rec["pages_url"],
            "repo": rec["repo"],
            "file": Path(rec["best_file_in_repo"]).name,
            "reported_value": f"{rec['live_score']:.4f}",
            "value_provenance": "user/owner report; submission-page receipt linking value to hash not available",
            "organizer_receipt_verified": False,
            "source": source,
        }
        if source["ok"]:
            path = ROOT / source["path"]
            try:
                details, mask = inspect(path, template_grid, fp)
                if details["sha256"] != rec["sha256"]:
                    raise ValueError("SHA-256 mismatch")
                row["file_audit"] = details
                row["blob_url"] = f"https://github.com/{rec['repo']}/blob/{source['commit']}/{rec['best_file_in_repo']}"
                masks[rec["site"]] = mask
            except (OSError, ValueError) as exc:
                row["source"] = {"ok": False, "error": str(exc)}
                missing.append(rec["site"])
        else:
            missing.append(rec["site"])
        rows.append(row)

    trees = {name: cKDTree(np.argwhere(mask)) for name, mask in masks.items() if mask.any()}
    for row in rows:
        site = row["site"]
        if site not in masks:
            row["uniqueness_against_other_focus_sites"] = "unknown: file unavailable"
            continue
        m = masks[site]
        points = np.argwhere(m)
        comparisons = []
        for peer, peer_mask in masks.items():
            if peer == site or peer not in trees or not len(points):
                continue
            overlap = float(np.mean(trees[peer].query(points, workers=1)[0] <= 3.0))
            comparisons.append({"site": peer, "fraction_candidate_dots_within_3px": overlap,
                                "same_footprint_pixels": bool(np.array_equal(m, peer_mask))})
        comparisons.sort(key=lambda x: x["fraction_candidate_dots_within_3px"], reverse=True)
        row["focus_site_comparisons"] = comparisons
        # A single violating comparator proves failure even if another is missing.
        if any(x["fraction_candidate_dots_within_3px"] > 0.70 for x in comparisons):
            row["uniqueness_against_other_focus_sites"] = "no: exceeds literal 70% rule"
        elif missing or len(comparisons) != 8:
            row["uniqueness_against_other_focus_sites"] = "unknown: incomplete comparisons"
        else:
            row["uniqueness_against_other_focus_sites"] = "passes dot-overlap check only; surface check not available"

    previous = []
    for filename in PRIOR_LOCAL_FILES:
        path = ROOT / "docs/downloads" / filename
        details, m = inspect(path, template_grid, fp)
        k = int(m.sum())
        overlap = int((m & covered).sum())
        per_focus = []
        points = np.argwhere(m)
        for peer, tree in trees.items():
            per_focus.append({"site": peer, "fraction_candidate_dots_within_3px": float(np.mean(tree.query(points, workers=1)[0] <= 3))})
        previous.append({
            "file": filename, "file_audit": details,
            "lattice_overlap_pixels": overlap,
            "lattice_overlap_fraction": overlap / k if k else None,
            "pigeonhole_min_overlap_fraction": max(0, k - uncovered) / k if k else None,
            "focus_comparisons": per_focus,
            "surface_replayed": False,
            "literal_registry_gate": "FAIL" if k and overlap / k > 0.70 else "UNKNOWN: complete registry not replayed",
            "ok_to_submit": False,
        })

    result = {
        "schema": "kanlergems2.focus-reaudit.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Independent forensic audit of previously produced files; no new prediction or competition submission.",
        "score_provenance": "All historical values are user/owner reports, not verified submission-page receipts.",
        "template_sha256": sha256_file(template),
        "template_provenance": "pinned public owner mirror; not independently authenticated against DrivenData data download",
        "registry_lattice": {
            "file": LATTICE.name, "sha256": LATTICE_SHA,
            "source": "https://github.com/buffedlizard55-lab/GEMSDOE24/blob/07345ea0604953d7efb858d9cfbc21e20c7aca0b/inputs/calibration/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif",
            "footprint_pixels": nfp, "positive_pixels": int(lattice.sum()),
            "covered_within_3px": int(covered.sum()), "uncovered_within_3px": uncovered,
            "coverage_fraction": int(covered.sum()) / nfp,
            "scope": "This one comparator suffices to prove a literal failure; the full registry was not replayed.",
        },
        "missing_focus_sites": missing,
        "focus_sites": rows,
        "previous_local_candidates": previous,
        "new_experiments_run": 0,
        "competition_slots_spent": 0,
        "verdict": "negative",
    }
    OUTPUT.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(OUTPUT.relative_to(ROOT)), "sites_audited": len(masks),
                      "missing_sites": missing, "lattice_coverage": result["registry_lattice"]["coverage_fraction"],
                      "local_candidates": [{"file": x["file"], "overlap": x["lattice_overlap_fraction"], "verdict": x["literal_registry_gate"]} for x in previous]}, indent=2))
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
