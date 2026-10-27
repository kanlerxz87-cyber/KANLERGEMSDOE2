#!/usr/bin/env python3
"""Re-open nine hash-pinned historical rasters and measure directional overlap.

These owner/user-reported scores are not organizer receipts. This audit never
uploads a raster and does not assert that the nine-file subset is exhaustive.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems.preflight import TEMPLATE_SHA256  # noqa: E402
from gems.validator import sha256_file  # noqa: E402

MANIFEST = ROOT / "registry/focus9_reference_20261027.json"


def restore(row: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".partial")
    try:
        with tmp.open("wb") as output:
            subprocess.run(
                ["gh", "api", f"repos/{row['repository']}/contents/{row['path']}?ref={row['ref']}",
                 "-H", "Accept: application/vnd.github.raw"],
                stdout=output, check=True,
            )
        if sha256_file(tmp) != row["sha256"]:
            raise ValueError(f"hash mismatch: {row['site']}")
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def audit(data: Path, *, allow_restore: bool = False) -> dict:
    refs = json.loads(MANIFEST.read_text(encoding="utf-8"))["references"]
    if len(refs) != 9 or len({r["site"] for r in refs}) != 9:
        raise ValueError("expected exactly nine distinct pinned reference sites")
    template = data / "sample_submission.tif"
    if sha256_file(template) != TEMPLATE_SHA256:
        raise ValueError("template does not match pinned owner mirror")
    with rasterio.open(template) as t:
        fp = np.isfinite(t.read(1))
        grid = (t.shape, t.crs, t.transform)
    masks, rows = [], []
    for row in refs:
        p = data / "focus9" / (row["site"] + "__" + row["filename"])
        if not p.exists() and allow_restore:
            restore(row, p)
        if sha256_file(p) != row["sha256"]:
            raise ValueError(f"hash mismatch for {row['site']}")
        with rasterio.open(p) as r:
            if (r.shape, r.crs, r.transform) != grid or r.count != 1:
                raise ValueError(f"grid mismatch for {row['site']}")
            a = r.read(1)
        inside = a[fp]
        if not np.isfinite(inside).all() or np.any((inside < 0) | (inside > 1)):
            raise ValueError(f"invalid in-footprint values for {row['site']}")
        mask = fp & (a > 0)
        if not mask.any():
            raise ValueError(f"empty reference: {row['site']}")
        masks.append(mask)
        rows.append({
            **row,
            "positive_pixels": int(mask.sum()),
            "whole_array_finite_in_0_1": bool(np.isfinite(a).all() and ((a >= 0) & (a <= 1)).all()),
            "outside_nonfinite_pixels": int((~np.isfinite(a[~fp])).sum()),
            "portal_acceptance": "unknown; no organizer acceptance receipt",
            "recommendation": "historical reference only; do not submit",
        })

    candidate_path = ROOT / "docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif"
    with rasterio.open(candidate_path) as ds:
        if (ds.shape, ds.crs, ds.transform) != grid or ds.count != 1:
            raise ValueError("historical HTC candidate grid mismatch")
        candidate = ds.read(1)
    if not np.isfinite(candidate[fp]).all() or np.any((candidate[fp] < 0) | (candidate[fp] > 1)):
        raise ValueError("invalid historical HTC candidate values")
    candidate_mask = fp & (candidate > 0)
    if not candidate_mask.any():
        raise ValueError("empty candidate")
    htc_overlaps: dict[str, float] = {}
    matrix = [[0.0] * len(rows) for _ in rows]
    offsets = np.arange(-3, 4)
    disk = offsets[:, None] ** 2 + offsets[None, :] ** 2 <= 9
    # Column j represents a peer's halo; row i is candidate->peer coverage.
    for j, ref_mask in enumerate(masks):
        halo = binary_dilation(ref_mask, structure=disk) & fp
        for i, candidate_i in enumerate(masks):
            matrix[i][j] = int((candidate_i & halo).sum()) / int(candidate_i.sum())
        htc_overlaps[rows[j]["site"]] = int((candidate_mask & halo).sum()) / int(candidate_mask.sum())
    for i, row in enumerate(rows):
        peers = [(matrix[i][j], rows[j]["site"]) for j in range(len(rows)) if j != i]
        overlap, peer = max(peers)
        row["max_directional_3px_overlap_vs_other_eight"] = overlap
        row["closest_site"] = peer
        row["unique_vs_nine_rule"] = overlap <= 0.70
        row["exact_mask_matches"] = [
            rows[j]["site"] for j in range(len(rows)) if j != i and np.array_equal(masks[i], masks[j])
        ]
    return {
        "schema": "gems.focus9.exact-audit.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Nine historical user-reported references only; no submission receipts, no exhaustive registry or leaderboard prediction.",
        "template_sha256": TEMPLATE_SHA256,
        "radius_px": 3,
        "criterion": "directional candidate pixels within inclusive 3 px of peer pixels; duplicate if > 0.70",
        "rows": rows,
        "directional_overlap_matrix": {
            rows[i]["site"]: {rows[j]["site"]: matrix[i][j] for j in range(len(rows))}
            for i in range(len(rows))
        },
        "historical_htcads_candidate": {
            "filename": candidate_path.name,
            "sha256": sha256_file(candidate_path),
            "overlap_vs_nine": htc_overlaps,
            "max_overlap_vs_nine": max(htc_overlaps.values()),
            "scope": "Only the nine named references; does not include the lattice or the complete registry.",
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", type=Path, default=Path(os.environ.get("GEMS_DATA_DIR", ROOT / "data")))
    ap.add_argument("--restore", action="store_true", help="fetch missing pinned owner-repo files using gh")
    ap.add_argument("--out", type=Path, default=ROOT / "evidence/focus9_audit_20261027.json")
    args = ap.parse_args()
    result = audit(args.data, allow_restore=args.restore)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(args.out), "files_checked": len(result["rows"]),
                      "max_candidate_overlap_vs_nine": result["historical_htcads_candidate"]["max_overlap_vs_nine"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
