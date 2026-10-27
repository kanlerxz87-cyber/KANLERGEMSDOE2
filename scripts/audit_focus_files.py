#!/usr/bin/env python3
"""Independent format + uniqueness audit of the 9 focus-site files and the promoted KANLERGEMS2 file.

Reads the files fetched by scripts/fetch_focus_submissions.py (docs/downloads/focus-sites/) and the
promoted GeoTIFF (docs/downloads/), plus the restored scored archive (.cache/gems_data/scored/)
as an extra uniqueness reference. Writes evidence/focus_site_audit_20261027.json.

Every number here is COMPUTED from bytes in this run. Scores are copied from the prompt listing
and labelled USER-REPORTED; nothing here is an organizer receipt.

Checks per file (mirrors scripts/validate_submission.py / src/gems32/submission.py):
  - CRS EPSG:32611, shape 3730x3292, transform 100 m origin (243350, 4508550), single band float32
  - NaN inside footprint = 0 ; values inside footprint in [0, 1]
  - outside-footprint handling: 'zeros' (all 0) or 'nan' (all NaN) or 'mixed'
  - NaN outside footprint  => portal-risk flag (organizer rules say outside bounds null or nan,
    but the portal rejected at least one -nan upload with '[0,1]' error per the user's report)
  - dots = count(value > 0) inside footprint; on-catalogue dots = dots on labels>0

Uniqueness: 3-px dot overlap (candidate dots within 3 px of reference dots) in both directions,
and footprint-only Spearman |rho| on the continuous surface. Thresholds from the Parallel-Run
Protocol: |rho| > 0.90 or overlap > 0.70 => duplicate.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems.novelty import dot_overlap, correlation  # noqa: E402
from gems32.paths import data_dir  # noqa: E402

FOCUS_RECORDS = ROOT / "evidence" / "focus_site_files.json"
NEW_DARP = ROOT / "docs" / "downloads" / "kanlergems2-darp-exp-1-37654dots-20261027T181633Z-4ad35e71-zeros.tif"
PROMOTED = ROOT / "docs" / "downloads" / "kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif"
EVIDENCE_OUT = ROOT / "evidence" / "focus_site_audit_20261027.json"
EXPECTED_CRS = "EPSG:32611"
EXPECTED_SHAPE = (3730, 3292)
EXPECTED_TRANSFORM = (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_footprint_and_labels(ddir: Path):
    with rasterio.open(ddir / "sample_submission.tif") as s:
        foot = np.isfinite(s.read(1))
    with rasterio.open(ddir / "labels.tif") as s:
        labels = (s.read(1) > 0) & foot
    return foot, labels


def audit_one(path: Path, foot: np.ndarray, labels: np.ndarray) -> dict:
    with rasterio.open(path) as s:
        arr = s.read(1)
        crs = str(s.crs)
        shape = s.shape
        transform = tuple(round(float(x), 6) for x in s.transform)[:6]
        count = s.count
        dtype = s.dtypes[0]
        nodata = "NaN" if (s.nodata is not None and np.isnan(s.nodata)) else s.nodata
    in_f = arr[foot]
    out_f = arr[~foot]
    nan_out = int(np.isnan(out_f).sum())
    zero_out = int((out_f == 0).sum())
    if nan_out == out_f.size:
        outside_mode = "nan"
    elif zero_out == out_f.size:
        outside_mode = "zeros"
    else:
        outside_mode = "mixed"
    in_nan = int(np.isnan(in_f).sum())
    in_finite = np.isfinite(in_f)
    in_range_ok = bool(in_finite.all() and np.all((in_f[in_finite] >= 0) & (in_f[in_finite] <= 1)))
    dots_mask = foot & (np.nan_to_num(arr, nan=0.0) > 0)
    dots = int(dots_mask.sum())
    on_cat = int((dots_mask & labels).sum())
    checks = {
        "crs_epsg_32611": crs.endswith("32611"),
        "shape_3730x3292": shape == EXPECTED_SHAPE,
        "transform_100m_origin": transform == EXPECTED_TRANSFORM,
        "single_band": count == 1,
        "dtype_float32": dtype == "float32",
        "in_footprint_zero_nan": in_nan == 0,
        "in_footprint_range_0_1": in_range_ok,
        "zero_on_catalogue_dots": on_cat == 0,
    }
    return {
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "crs": crs,
        "shape": list(shape),
        "transform": list(transform),
        "dtype": dtype,
        "nodata": nodata,
        "nan_inside_footprint": in_nan,
        "nan_outside_footprint": nan_out,
        "outside_footprint_mode": outside_mode,
        "portal_risk_nan_outside": nan_out > 0,
        "in_footprint_min": float(np.nanmin(in_f)) if in_f.size else None,
        "in_footprint_max": float(np.nanmax(in_f)) if in_f.size else None,
        "dots_gt0_in_footprint": dots,
        "dots_on_catalogue": on_cat,
        "checks": checks,
        "all_checks_passed": all(checks.values()),
    }


def dots_of(path: Path, foot: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as s:
        arr = s.read(1)
    return foot & (np.nan_to_num(arr, nan=0.0) > 0)


def surface_of(path: Path, foot: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as s:
        arr = s.read(1)
    return np.nan_to_num(arr[foot].astype(np.float64), nan=0.0)


def main() -> int:
    ddir = data_dir()
    foot, labels = load_footprint_and_labels(ddir)

    # 1) new DARP-MT10 file + archived HTCADS EXP-2 file, 2) every focus-site file fetched by fetch_focus_submissions.py
    targets = [
        ("KANLERGEMSDOE2 new DARP-MT10 EXP-1", "KANLERGEMSDOE2", NEW_DARP, "HOLDOUT-DTI (verdict=negative, research-only)", None),
        ("KANLERGEMSDOE2 promoted EXP-2", "KANLERGEMSDOE2", PROMOTED, "HOLDOUT-DTI (archived prior candidate)", None),
    ]
    recs = json.loads(FOCUS_RECORDS.read_text())["records"]
    for r in recs:
        if r.get("status") != "downloaded":
            raise SystemExit(f"focus file not downloaded: {r}")
        targets.append((Path(r["local_path"]).name, r["site"], ROOT / r["local_path"], r["score_label"], r["user_reported_score"]))
    # 3) scored archive (restored, not committed) used only as extra uniqueness references
    archive_refs = [("archive:" + p.name, "archive", p, "n/a (archive reference)", None)
                    for p in sorted((ddir / "scored").glob("*.tif"))]

    audits, dots_cache, surf_cache = [], {}, {}
    for label, site, path, score_label, user_score in targets + archive_refs:
        a = audit_one(path, foot, labels)
        a.update({"label": label, "site": site, "score_label": score_label, "user_reported_score": user_score,
                  "file": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)})
        audits.append(a)
        dots_cache[label] = dots_of(path, foot)
        if label in (targets[0][0], targets[1][0]):
            surf_cache[label] = surface_of(path, foot)

    new_lbl = targets[0][0]
    promo = targets[1][0]
    names = [t[0] for t in targets] + [t[0] for t in archive_refs]
    pairs = []
    for i, la in enumerate(names):
        for lb in names[i + 1:]:
            ov = dot_overlap(dots_cache[la], dots_cache[lb], radius_px=3.0)
            exact = bool(np.array_equal(dots_cache[la], dots_cache[lb]))
            pairs.append({
                "a": la, "b": lb,
                "a_within_3px_of_b": ov["candidate_within_3px_of_reference"],
                "b_within_3px_of_a": ov["reference_within_3px_of_candidate"],
                "exact_dot_identity": exact,
            })

    def _build_vs_all(anchor: str) -> list[dict]:
        rows = []
        for lb in names:
            if lb == anchor:
                continue
            ab = [p for p in pairs if {p["a"], p["b"]} == {anchor, lb}][0]
            cand_in_ref = ab["a_within_3px_of_b"] if ab["a"] == anchor else ab["b_within_3px_of_a"]
            ref_in_cand = ab["b_within_3px_of_a"] if ab["a"] == anchor else ab["a_within_3px_of_b"]
            ov_max = max(cand_in_ref or 0.0, ref_in_cand or 0.0)
            path = next(t[2] for t in targets + archive_refs if t[0] == lb)
            rho = correlation(surf_cache[anchor], surface_of(path, foot))
            rows.append({
                "against": lb,
                "promoted_dots_within_3px_of_against": round(float(cand_in_ref), 6) if cand_in_ref is not None else None,
                "against_dots_within_3px_of_promoted": round(float(ref_in_cand), 6) if ref_in_cand is not None else None,
                "overlap_3px_max_direction": round(ov_max, 6),
                "footprint_spearman_rho": None if rho is None else round(float(rho), 6),
                "exact_dot_identity": ab["exact_dot_identity"],
                "duplicate_by_protocol_overlap_gt_0p70": bool(ov_max > 0.70),
                "duplicate_by_protocol_abs_rho_gt_0p90": bool(rho is not None and abs(rho) > 0.90),
                "note": "space-filling calibration lattice (control, not a detector)" if "lattice" in lb else "",
            })
        return rows

    new_vs = _build_vs_all(new_lbl)
    promo_vs = _build_vs_all(promo)

    out = {
        "schema": "kanlergemsdoe2.focus_site_audit.v1",
        "audit_date_utc": "2026-10-27",
        "footprint_pixels": int(foot.sum()),
        "labelled_catalogue_pixels_in_footprint": int(labels.sum()),
        "duplicate_thresholds": {"abs_spearman_gt": 0.90, "overlap_3px_gt": 0.70},
        "files": audits,
        "pairwise_overlap": pairs,
        "new_darp_vs_all": new_vs,
        "promoted_vs_all": promo_vs,
        "notes": [
            "Scores in files[] are USER-REPORTED from the prompt listing, not organizer receipts.",
            "Pairwise overlap covers the 9 focus-site files, their portal-safe siblings, the 3 latest-run alternates, the promoted file and the restored scored archive.",
            "Footprint Spearman is computed only against the promoted file (footprint pixels only).",
            "archive:* files are restored from the owner data bridge for uniqueness reference only; they are not submissions in this repo.",
        ],
    }
    EVIDENCE_OUT.write_text(json.dumps(out, indent=2) + "\n")
    bad = [a["label"] for a in audits if not a["all_checks_passed"] and not a["label"].startswith("archive:")]
    print(f"audited {len(audits)} files; focus/promoted format failures: {bad or 'none'}")
    for p in sorted(promo_vs, key=lambda x: -x["overlap_3px_max_direction"]):
        print(f"  {p['overlap_3px_max_direction']:.4f}  rho={p['footprint_spearman_rho']}  identical={p['exact_dot_identity']}  {p['against']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
