#!/usr/bin/env python3
"""Generate publication-grade 3-panel diagnostic figure for Session-3 KG2-S3-HPTR."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems32.paths import data_dir, downloads_dir, evidence_dir  # noqa: E402


def main() -> int:
    edir = evidence_dir()
    dldir = downloads_dir()
    ddir = data_dir()

    s3 = json.loads((edir / "session3_hptr_run_card_20261027.json").read_text(encoding="utf-8"))
    fleet = json.loads((edir / "hptr_full_fleet_audit_20261027.json").read_text(encoding="utf-8"))

    fig, axes = plt.subplots(1, 3, figsize=(16.5, 5.2), dpi=160)
    fig.patch.set_facecolor("#fbfbf8")

    # Panel A: All 3 Independent Holdout Suites vs 0.2778 Champion & Prior Repo Candidates
    ax0 = axes[0]
    ax0.set_facecolor("#ffffff")
    models = [
        "0.2778 Champ\n(GEMSDOE32)",
        "HTCADS EXP-2\n(11a2f251)",
        "DSLUP Uniq\n(c71122d5)",
        "DARP EXP-1\n(4ad35e71)",
        "HPTR-EXP-2\n(675d0ff8 NEW)",
    ]
    hr_vals = [0.099202, 0.112353, 0.125925, 0.098049, s3["holdout_dti"]["primary_hide_and_recover"]["pooled_dti"]]
    sg_vals = [0.064121, 0.078913, 0.098140, 0.038048, s3["holdout_dti"]["secondary_off_catalogue_sgmc"]["sgmc_prevalence_calibrated_dti"]]
    cp_vals = [0.101166, 0.077405, 0.073458, 0.116858, s3["holdout_dti"]["tertiary_concealed_piedmont_c_pied"]["pooled_dti"]]

    x = np.arange(len(models))
    w = 0.25
    ax0.bar(x - w, hr_vals, width=w, label="Hide-Recover v3.0.1 (N=22,232)", color="#1d4ed8")
    ax0.bar(x, sg_vals, width=w, label="Blind SGMC-CAL v3.0 (N=62,703)", color="#0f766e")
    ax0.bar(x + w, cp_vals, width=w, label="Blind Piedmont C-PIED v1.0 (N=9,847)", color="#b45309")
    ax0.axhline(0.099202, color="#1d4ed8", ls="--", lw=0.9, alpha=0.55)
    ax0.axhline(0.064121, color="#0f766e", ls="--", lw=0.9, alpha=0.55)
    ax0.axhline(0.101166, color="#b45309", ls="--", lw=0.9, alpha=0.55)
    ax0.set_xticks(x)
    ax0.set_xticklabels(models, fontsize=7.6)
    ax0.set_ylim(0, 0.148)
    ax0.set_ylabel("HOLDOUT-DTI (alpha=0.2, beta=0.8, 300 m kernel)", fontsize=9)
    ax0.set_title("A. Only Candidate Beating 0.2778 on All 3 Suites", fontsize=10.5, fontweight="bold")
    ax0.legend(fontsize=7.5, loc="upper left")
    ax0.grid(axis="y", alpha=0.25)

    # Panel B: 3-px Overlap vs Own Prior Rasters (<=45% gate) & Fleet Detectors (<=70% gate)
    ax1 = axes[1]
    ax1.set_facecolor("#ffffff")
    peers = [
        ("Max Ext Detector (348)", 100.0 * s3["registry_comparison"]["final_dots_max_detector_3px_overlap"], "#475569"),
        ("Focus GEMSDOE27", 49.24, "#64748b"),
        ("Sister ApartGEMSDOE3", 45.69, "#64748b"),
        ("Own HTCADS (11a2f251)", 100.0 * s3["overlap_vs_own_prior_rasters"]["htcads_exp2_11a2f251"]["asym_3px_overlap_ours_in_peer"], "#0284c7"),
        ("Own DSLUP (c71122d5)", 100.0 * s3["overlap_vs_own_prior_rasters"]["dslup_uniq_c71122d5"]["asym_3px_overlap_ours_in_peer"], "#0284c7"),
        ("Own MGHV (f5a469e94b14)", 100.0 * s3["overlap_vs_own_prior_rasters"]["kg2_mghv_f5a469e94b14"]["asym_3px_overlap_ours_in_peer"], "#0284c7"),
        ("Sister WBGGEMSDOE1", 42.41, "#64748b"),
        ("Focus 0.2778 Champ", 100.0 * s3["correlation_overlap_vs_registry"]["overlap_vs_0p2778_champion"], "#0f766e"),
        ("Own DARP (4ad35e71)", 100.0 * s3["overlap_vs_own_prior_rasters"]["darp_exp1_4ad35e71"]["asym_3px_overlap_ours_in_peer"], "#0284c7"),
        ("Sister GEMSDOESASS3", 37.88, "#64748b"),
        ("Sister KANLERGEMSDOE3", 16.28, "#64748b"),
    ]
    py = np.arange(len(peers))[::-1]
    ax1.barh(py, [p[1] for p in peers], color=[p[2] for p in peers], height=0.68)
    ax1.axvline(70.0, color="#dc2626", ls="--", lw=1.3, label="70% External Detector Gate")
    ax1.axvline(45.0, color="#0284c7", ls=":", lw=1.3, label="45% Own-Prior Cap")
    ax1.set_yticks(py)
    ax1.set_yticklabels([p[0] for p in peers], fontsize=8.0)
    ax1.set_xlim(0, 82)
    ax1.set_xlabel("Asymmetric 3-px Dot Overlap (% of HPTR-EXP-2 dots)", fontsize=9)
    ax1.set_title("B. Uniqueness Audit Across 642 Fleet GeoTIFFs", fontsize=10.5, fontweight="bold")
    ax1.legend(fontsize=7.5, loc="lower right")
    ax1.grid(axis="x", alpha=0.25)

    # Panel C: Spatial Map of HPTR-EXP-2 (37,654 dots) vs 1 m LiDAR Void & Mapped Faults
    ax2 = axes[2]
    ax2.set_facecolor("#f1f5f9")
    with rasterio.open(ddir / "labels.tif") as s:
        raw_l = s.read(1)
        foot = np.isfinite(raw_l)
        cat = foot & (raw_l > 0)
    with rasterio.open(ddir / "external" / "lidar_scarp_features_u8.tif") as sl:
        lid_ok = foot & (sl.read(5) > 0)
    with rasterio.open(dldir / s3["raster_filename"]) as sh:
        dots = foot & (sh.read(1) >= 0.5)

    bg = np.full(foot.shape + (3,), 0.95, dtype=np.float32)
    bg[foot & lid_ok] = [0.89, 0.93, 0.90]
    bg[foot & (~lid_ok)] = [0.96, 0.91, 0.82]  # warm sand = 24.63% 1m LiDAR void
    ax2.imshow(bg[::4, ::4], interpolation="nearest")

    cy, cx = np.nonzero(cat)
    ax2.scatter(cx[::6] / 4.0, cy[::6] / 4.0, s=0.15, c="#64748b", alpha=0.45, label="Known labels (masked)")
    dy_in, dx_in = np.nonzero(dots & lid_ok)
    dy_vo, dx_vo = np.nonzero(dots & (~lid_ok))
    ax2.scatter(dx_in[::2] / 4.0, dy_in[::2] / 4.0, s=0.32, c="#1d4ed8", alpha=0.75, label="HPTR in 1m LiDAR (72.9%)")
    ax2.scatter(dx_vo[::2] / 4.0, dy_vo[::2] / 4.0, s=0.42, c="#d97706", alpha=0.85, label="HPTR in LiDAR Void (27.1%)")
    ax2.set_xticks([])
    ax2.set_yticks([])
    ax2.set_title("C. Seamless Footprint Coverage (37,654 dots)", fontsize=10.5, fontweight="bold")
    ax2.legend(fontsize=7.3, loc="lower left", markerscale=5.0)

    plt.tight_layout()
    out_img = ROOT / "docs" / "assets" / "fig5_hptr_three_benchmarks_and_uniqueness.png"
    out_img.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_img, dpi=160)
    plt.close(fig)
    print(f"[PLOT] Saved {out_img} ({out_img.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
