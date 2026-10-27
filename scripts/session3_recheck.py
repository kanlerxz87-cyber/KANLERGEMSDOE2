#!/usr/bin/env python3
"""Independent recheck of the focus-site and candidate GeoTIFFs (Session 3, 2026-10-27).

Recomputes, from committed files plus restored owner mirrors only:
  1. Format audit of each candidate (CRS, shape, transform, dtype, finite/[0,1], NaN, outside values).
  2. Literal lattice-witness overlap (dots within 3 px of witness dots) and Spearman rho.
  3. Pairwise directional 3-px overlap among the nine focus-site files, the three
     KANLERGEMS2 candidates and every restored registry raster that is present.
  4. Near-catalogue dot counts (the mechanism behind the 0.2778 raster's pruning).

Every number is HOLDOUT-free: these are geometry/format facts, not scores.
Output: evidence/session3_independent_recheck_20261027.json
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems.release_audit import WITNESS_NAME, assess_file, load_reference  # noqa: E402
from gems32.paths import data_dir  # noqa: E402

OUT = ROOT / "evidence" / "session3_independent_recheck_20261027.json"
DOWNLOADS = ROOT / "docs" / "downloads"

FOCUS_NINE = {
    "GEMSDOE24": "gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif",
    "GEMSDOE25": "gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
    "GEMSDOE27": "gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif",
    "GEMSDOE28": "gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif",
    "GEMSDOE30": "gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif",
    "GEMSDOE31": "gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif",
    "GEMSDOE32": "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
    "GEMSDOE33": "gemsdoe33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif",
    "GEMSDOE36": "gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
}
# Note: docs/downloads uses the GEMSDOE33 file name with its own casing; resolved below.
CANDIDATES = {
    "KG2-DSLUP-session2": "kanlergems2-dslup-uniq-q15k-37654dots-20261027T181253Z-c71122d5-zeros.tif",
    "KG2-DARP-EXP1-session3-lane": "kanlergems2-darp-exp-1-37654dots-20261027T181633Z-4ad35e71-zeros.tif",
    "KG2-HTCADS-session1": "kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif",
    "KG2-HYP1-binary-PR34": "kanlergemsdoe2-unique-hypothesis1-binary-20261027.tif",
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_download(name: str) -> Path:
    p = DOWNLOADS / name
    if p.is_file():
        return p
    matches = [q for q in DOWNLOADS.glob("*.tif") if q.name.lower() == name.lower()]
    if len(matches) != 1:
        raise FileNotFoundError(name)
    return matches[0]


def circle(r: int) -> np.ndarray:
    y, x = np.mgrid[-r:r + 1, -r:r + 1]
    return y * y + x * x <= r * r


def main() -> int:
    ddir = data_dir()
    ref = load_reference(ROOT, ddir)
    foot = ref["foot"]
    cat = ref["catalogue"]
    grid = ref["grid"]

    # Candidate files: format + witness audit.
    cand_rows: dict[str, dict] = {}
    rasters: dict[str, Path] = {}
    for label, name in {**FOCUS_NINE, **CANDIDATES}.items():
        p = find_download(name)
        rasters[label] = p
    for label, p in rasters.items():
        if label in CANDIDATES:
            audit = assess_file(p, ref)
            cand_rows[label] = {k: audit[k] for k in (
                "file", "sha256", "size_bytes", "shape", "crs", "transform", "dtype", "nodata",
                "grid_matches_pinned_owner_template", "no_nan_inside_footprint", "no_inf_inside_footprint",
                "inside_range_0_1", "strict_whole_array_finite_0_1", "outside_footprint_all_nan",
                "outside_footprint_all_zero", "inside_positive_pixels", "outside_positive_pixels",
                "on_catalogue_positive_pixels", "witness_overlap_dots", "witness_overlap_fraction",
                "witness_final_dots_spearman", "duplicate_under_literal_rule")}

    # Dot sets and near-masks for pairwise overlap (dots = in-footprint, finite, > 0).
    dots: dict[str, np.ndarray] = {}
    values_stats: dict[str, dict] = {}
    for label, p in rasters.items():
        with rasterio.open(p) as ds:
            assert (ds.height, ds.width) == grid[0] and ds.count == 1
            arr = ds.read(1)
        inside = arr[foot]
        dots[label] = foot & np.isfinite(arr) & (arr > 0)
        values_stats[label] = {
            "inside_min": float(np.nanmin(inside)), "inside_max": float(np.nanmax(inside)),
            "inside_distinct_values": int(np.unique(inside).size),
            "inside_fraction_exactly_one": float((inside == 1).mean()),
        }

    # Registry rasters present on disk (restored owner mirrors, already hash-pinned).
    scored_dir = ddir / "scored"
    for p in sorted(scored_dir.glob("*.tif")):
        label = f"REG:{p.name}"
        with rasterio.open(p) as ds:
            if (ds.height, ds.width) != grid[0]:
                continue
            arr = ds.read(1)
        rasters[label] = p
        dots[label] = foot & np.isfinite(arr) & (arr > 0)

    near3 = {k: binary_dilation(v, structure=circle(3)) for k, v in dots.items()}
    labels = list(dots)
    pair = {}
    for a in labels:
        n_a = int(dots[a].sum())
        row = {}
        for b in labels:
            if a == b or n_a == 0:
                continue
            row[b] = float((dots[a] & near3[b]).sum() / n_a)
        pair[a] = row

    focus_pairs = {a: {b: pair[a][b] for b in FOCUS_NINE if b != a and b in pair[a]} for a in FOCUS_NINE}
    focus_nearest = {a: max(focus_pairs[a].items(), key=lambda kv: kv[1]) for a in FOCUS_NINE}

    # Mechanism: where do focus-site dots sit relative to the pixel-exact known-fault mask?
    near_cat = {r: binary_dilation(cat, structure=circle(r)) for r in (1, 2, 3)}
    mechanism = {}
    for label in FOCUS_NINE:
        d = dots[label]
        mechanism[label] = {
            "positive_dots": int(d.sum()),
            "on_known_fault_pixels_masked_by_organizer": int((d & cat).sum()),
            "off_fault_dots_within_1px_of_known_fault": int((d & ~cat & near_cat[1]).sum()),
            "off_fault_dots_within_2px_of_known_fault": int((d & ~cat & near_cat[2]).sum()),
            "off_fault_dots_within_3px_of_known_fault": int((d & ~cat & near_cat[3]).sum()),
            "value_stats": values_stats[label],
        }

    # Exact lineage check: GEMSDOE32 should be GEMSDOE25 minus its dots within 2 px of known faults.
    g25, g32 = dots["GEMSDOE25"], dots["GEMSDOE32"]
    removed = g25 & ~g32
    lineage = {
        "gemsdoe32_subset_of_gemsdoe25": bool(not (g32 & ~g25).any()),
        "removed_dots_from_gemsdoe25": int(removed.sum()),
        "removed_dots_all_within_2px_of_known_fault": bool(not (removed & ~near_cat[2]).any()),
        "removed_dots_on_known_fault_pixels": int((removed & cat).sum()),
        "gemsdoe25_off_fault_dots_within_2px": int((g25 & ~cat & near_cat[2]).sum()),
        "gemsdoe25_minus_gemsdoe32_equals_within_2px_count": bool(int(removed.sum()) == int((g25 & ~cat & near_cat[2]).sum())),
    }

    receipt = {
        "schema": "gems.session3-independent-recheck.v1",
        "lineage_gemsdoe32_from_gemsdoe25": lineage,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "data_dir": str(ddir.relative_to(ROOT)) if ddir.is_relative_to(ROOT) else str(ddir),
        "witness": {"filename": WITNESS_NAME, "sha256": sha256(ddir / "scored" / WITNESS_NAME),
                    "uncovered_footprint_pixels": ref["uncovered"]},
        "footprint_pixels": int(foot.sum()),
        "catalogue_positive_pixels": int(cat.sum()),
        "restored_registry_rasters_on_disk": len(list(scored_dir.glob("*.tif"))),
        "registry_entries_declared": len(json.loads((ROOT / "registry/comparison_registry.json").read_text())["entries"]),
        "candidates_format_and_witness": cand_rows,
        "focus_nine_files": {k: {"file": v, "sha256": sha256(rasters[k])} for k, v in FOCUS_NINE.items()},
        "focus_nine_nearest_other_focus_site": {
            k: {"site": v[0], "directional_3px_overlap": v[1]} for k, v in focus_nearest.items()},
        "pairwise_directional_3px_overlap_focus_and_candidates": {
            k: pair[k] for k in list(FOCUS_NINE) + list(CANDIDATES)},
        "mechanism_near_known_fault": mechanism,
        "method": [
            "dots = in-footprint, finite, value > 0 (same definition as release_audit.assess_file)",
            "directional overlap A->B = fraction of A's dots within a radius-3 disk of any B dot (300 m at 100 m)",
            "known-fault mask = labels.tif > 0 inside footprint (DrivenData staff, 2026-09-21: pixel-exact)",
            "No DTI, holdout or leaderboard score is computed here.",
        ],
    }
    OUT.write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    for k, v in focus_nearest.items():
        print(f"{k}: nearest {v[0]} directional overlap {v[1]:.4f}")
    for k, v in cand_rows.items():
        print(f"{k}: sha256={v['sha256'][:12]} inside_0_1={v['inside_range_0_1']} "
              f"witness_overlap={v['witness_overlap_fraction']:.4f} rho={v['witness_final_dots_spearman']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
