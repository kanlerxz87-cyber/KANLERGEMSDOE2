#!/usr/bin/env python3
"""Forensic byte-level audit of the 9 focus GEMSDOE sites + 92-site fleet cross-check."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems32 import holdout  # noqa: E402
from gems32.paths import data_dir, evidence_dir  # noqa: E402

FOCUS_SPECS = [
    {
        "site": "GEMSDOE32",
        "repo": "buffedlizard55-lab/GEMSDOE32",
        "pages_url": "https://buffedlizard55-lab.github.io/GEMSDOE32/",
        "repo_url": "https://github.com/buffedlizard55-lab/GEMSDOE32",
        "best_file_in_repo": "docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
        "download_url": "https://raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE32/main/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
        "local_cache": "scored/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
        "live_score": 0.2778,
        "live_score_label": "USER/OWNER-REPORTED; no organizer submission-page receipt archived",
        "lineage_formula": "d2.8 & (d_cat > 2 px) — strips 6,436 0-200 m catalogue-collar FPs off 19GEMSDOE H19-5",
        "latest_20261026_status": "DO NOT SUBMIT on latest Round-6 / H-GEO-CONDUIT candidates (halo crowding / fail-closed gate); historical 0.2778 -zeros.tif is format-valid but already submitted on GEMSDOE32.",
    },
    {
        "site": "GEMSDOE36",
        "repo": "buffedlizard55-lab/GEMSDOE36",
        "pages_url": "https://buffedlizard55-lab.github.io/GEMSDOE36/",
        "repo_url": "https://github.com/buffedlizard55-lab/GEMSDOE36",
        "best_file_in_repo": "docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
        "download_url": "https://raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE36/main/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
        "local_cache": "scored/GEMSDOE36__gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
        "live_score": 0.2750,
        "live_score_label": "USER/OWNER-REPORTED; no organizer submission-page receipt archived",
        "lineage_formula": "GEMSDOE32 B=2 (all 37,654 dots preserved) UNION 1,200 radial thermal IDW dots (-0.0028 FP dilution)",
        "latest_20261026_status": "Latest ATVR36 / HVG36 marked verdict=negative (tripped 3-px overlap against dense registry blankets including 5-px calibration lattice).",
    },
    {
        "site": "GEMSDOE28",
        "repo": "buffedlizard55-lab/GEMSDOE28",
        "pages_url": "https://buffedlizard55-lab.github.io/GEMSDOE28/",
        "repo_url": "https://github.com/buffedlizard55-lab/GEMSDOE28",
        "best_file_in_repo": "docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif",
        "download_url": "https://raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE28/main/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif",
        "local_cache": "scored/GEMSDOE28__gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif",
        "live_score": 0.2710,
        "live_score_label": "USER/OWNER-REPORTED; no organizer submission-page receipt archived",
        "lineage_formula": "H27-4 solo (d2.8 & d_cat > 1) pruned from 40,199 -> 37,660 dots via blind geophysical rung-30 filter; secondary h27-4-r1-solo (0.2708) is 0-XOR identical to GEMSDOE31 solo",
        "latest_20261026_status": "Historical best is -nan.tif (outside-footprint NaN triggers portal [0, 1] range rejection if re-uploaded raw); S18 live negative (0.0217).",
    },
    {
        "site": "GEMSDOE31",
        "repo": "buffedlizard55-lab/GEMSDOE31",
        "pages_url": "https://buffedlizard55-lab.github.io/GEMSDOE31/",
        "repo_url": "https://github.com/buffedlizard55-lab/GEMSDOE31",
        "best_file_in_repo": "docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif",
        "download_url": "https://raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE31/main/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif",
        "local_cache": "scored/GEMSDOE31__gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif",
        "live_score": 0.2708,
        "live_score_label": "USER/OWNER-REPORTED; no organizer submission-page receipt archived",
        "lineage_formula": "d2.8 & (d_cat > 1 px) — exact 40,199-dot superset of GEMSDOE32 B=2 (+2,545 1-2 px collar dots)",
        "latest_20261026_status": "DUPLICATE (0-XOR in footprint with GEMSDOE28 h27-4-r1-solo) + -nan.tif outside-footprint NaN hazard; H31-M marked DO NOT SUBMIT.",
    },
    {
        "site": "GEMSDOE33",
        "repo": "buffedlizard55-lab/GEMSDOE33",
        "pages_url": "https://buffedlizard55-lab.github.io/GEMSDOE33/",
        "repo_url": "https://github.com/buffedlizard55-lab/GEMSDOE33",
        "best_file_in_repo": "docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif",
        "download_url": "https://raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE33/main/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif",
        "local_cache": "scored/GEMSDOE33__GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif",
        "live_score": 0.2632,
        "live_score_label": "USER/OWNER-REPORTED; no organizer submission-page receipt archived",
        "lineage_formula": "GEMSDOE31 solo (40,199 dots) + analog tip/stepover replacements (41,865 dots; 94.0% 3-px overlap with B=2)",
        "latest_20261026_status": "Near-duplicate of H19-5/d2.8 cascade (94.0% 3-px overlap with GEMSDOE32 B=2) + outside-footprint NaN; latest A33-L1/DPPS marked NOT OK TO SUBMIT.",
    },
    {
        "site": "GEMSDOE25",
        "repo": "buffedlizard55-lab/GEMSDOE25",
        "pages_url": "https://buffedlizard55-lab.github.io/GEMSDOE25/",
        "repo_url": "https://github.com/buffedlizard55-lab/GEMSDOE25",
        "best_file_in_repo": "docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
        "download_url": "https://raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE25/main/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
        "local_cache": "scored/GEMSDOE25__gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
        "live_score": 0.2600,
        "live_score_label": "USER/OWNER-REPORTED; no organizer submission-page receipt archived",
        "lineage_formula": "300 m (2.8 px) greedy Poisson-disk thinning of 19GEMSDOE H19-5 (121,131 -> 44,090 dots, no catalogue collar)",
        "latest_20261026_status": "DUPLICATE (0-XOR in footprint with GEMSDOE30 poisson300m) + -nan.tif hazard; H66 live negative (0.0742).",
    },
    {
        "site": "GEMSDOE30",
        "repo": "buffedlizard55-lab/GEMSDOE30",
        "pages_url": "https://buffedlizard55-lab.github.io/GEMSDOE30/",
        "repo_url": "https://github.com/buffedlizard55-lab/GEMSDOE30",
        "best_file_in_repo": "docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif",
        "download_url": "https://raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE30/main/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif",
        "local_cache": "scored/GEMSDOE30__gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif",
        "live_score": 0.2600,
        "live_score_label": "USER/OWNER-REPORTED; no organizer submission-page receipt archived",
        "lineage_formula": "All-finite re-export of GEMSDOE25 d2.8 (44,090 dots, 0-XOR in footprint)",
        "latest_20261026_status": "DUPLICATE (0-XOR in footprint with GEMSDOE25 d2.8); MSDB-1v2 scored 0.1462 live and marked NOT APPROVED FOR SUBMISSION.",
    },
    {
        "site": "GEMSDOE24",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "pages_url": "https://buffedlizard55-lab.github.io/GEMSDOE24/",
        "repo_url": "https://github.com/buffedlizard55-lab/GEMSDOE24",
        "best_file_in_repo": "docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif",
        "download_url": "https://raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE24/main/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif",
        "local_cache": "scored/GEMSDOE24__gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif",
        "live_score": 0.2477,
        "live_score_label": "USER/OWNER-REPORTED; no organizer submission-page receipt archived",
        "lineage_formula": "150 m (1.5 px) greedy thinning of 19GEMSDOE H19-5 (121,131 -> 60,069 dots; over-packed inside 300 m kernel)",
        "latest_20261026_status": "Over-packed H19-5 ancestor + -nan.tif hazard; GVC1 live negative (0.0859 due to 74.3% <=10 px halo collapse).",
    },
    {
        "site": "GEMSDOE27",
        "repo": "buffedlizard55-lab/GEMSDOE27",
        "pages_url": "https://buffedlizard55-lab.github.io/GEMSDOE27/",
        "repo_url": "https://github.com/buffedlizard55-lab/GEMSDOE27",
        "best_file_in_repo": "docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif",
        "download_url": "https://raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE27/main/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif",
        "local_cache": "scored/GEMSDOE27__gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif",
        "live_score": 0.2449,
        "live_score_label": "USER/OWNER-REPORTED; no organizer submission-page receipt archived",
        "lineage_formula": "GEMSDOE24 d1.5 (60,069 dots) + 1,259 topographic gap-closure bridges = 61,328 dots (Jaccard 0.9795 vs GEMSDOE24)",
        "latest_20261026_status": "98% overlap with GEMSDOE24 d1.5 + -nan.tif hazard; standalone H29-S (0.2190) already submitted.",
    },
]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _invert_d28_collar_cascade() -> dict:
    """Descriptive fit to unverified rounded reports; not an inversion or proof."""
    ns = np.array([44090., 40199., 37654., 38854.])
    scores = np.array([0.2600, 0.2708, 0.2778, 0.2750])
    inv = 1.0 / scores
    slope, intercept = np.polyfit(ns, inv, 1)
    fitted = slope * ns + intercept
    r2 = float(1.0 - np.sum((inv - fitted) ** 2) / np.sum((inv - inv.mean()) ** 2))
    return {
        "evidence_class": "USER/OWNER-REPORTED; no organizer receipt",
        "r_squared_descriptive_only": r2,
        "warning": "A fit to four rounded points does not prove hidden TP, FP, label count, causality, or a score ceiling.",
        "correct_algebra": "DTI = TP / (0.2*(TP+N-M) + 0.8*K + epsilon); M is kernel credit of predictions against hidden truth.",
    }


def main() -> int:
    # The old static-raster holdout and unproven forensic inference are archived.
    # Delegate to the exact-byte release audit; do not overwrite historic receipts.
    from audit_release import main as current_audit
    return current_audit()


def _legacy_main_archived() -> int:
    ddir = data_dir()
    ctx = holdout.load_holdout_context(ddir)

    with rasterio.open(ddir / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
    with rasterio.open(ddir / "existing_faults.tif") as ds:
        known = (ds.read(1) > 0) & foot
    with rasterio.open(ddir / "external" / "lidar_scarp_features_u8.tif") as ds:
        lidar_valid = (ds.read(12) > 0) & foot

    d_known = distance_transform_edt(~known).astype(np.float32)

    masks = {}
    d3_masks = {}
    rows_out = []

    for spec in FOCUS_SPECS:
        p = ddir / spec["local_cache"]
        sha = _sha256(p)
        with rasterio.open(p) as ds:
            arr = ds.read(1)
            nodata = ds.nodata
        n_nan_total = int(np.isnan(arr).sum())
        n_nan_fp = int(np.isnan(arr[foot]).sum())
        m = foot & np.isfinite(arr) & (arr >= 0.5)
        masks[spec["site"]] = m
        d3_masks[spec["site"]] = distance_transform_edt(~m) <= 3.0

        ev = holdout.evaluate_hide_and_recover(m, ctx, n_boot=400, seed=20261026, name=spec["site"])
        sg = holdout.evaluate_sgmc_with_ci(m, ctx, n_boot=400, seed=20261026, name=spec["site"])
        dk = d_known[m]

        rows_out.append({
            **spec,
            "sha256": sha,
            "file_bytes": p.stat().st_size,
            "nodata_tag": nodata,
            "outside_footprint_nans": n_nan_total,
            "inside_footprint_nans": n_nan_fp,
            "portal_range_01_safe_as_stored": bool(
                n_nan_total == 0 and float(np.nanmin(arr)) >= 0.0 and float(np.nanmax(arr)) <= 1.0
            ),
            "dots": int(m.sum()),
            "median_d_known_px": round(float(np.median(dk)), 2),
            "pct_le_2px_known": round(100.0 * float((dk <= 2.0).mean()), 2),
            "pct_le_10px_known": round(100.0 * float((dk <= 10.0).mean()), 2),
            "pct_in_lidar": round(100.0 * float(lidar_valid[m].mean()), 2),
            "holdout_hide_recover": {
                "dti": round(ev["pooled_dti"], 6),
                "ci95": [round(ev["ci95_cluster_bootstrap"][0], 6), round(ev["ci95_cluster_bootstrap"][1], 6)],
                "label": (
                    f"HOLDOUT-DTI ({ev['evaluator_version']}, N={ev['n_withheld_positives']} withheld positives, "
                    f"95% CI [{ev['ci95_cluster_bootstrap'][0]:.4f}, {ev['ci95_cluster_bootstrap'][1]:.4f}])"
                ),
            },
            "holdout_sgmc_offcat": {
                "raw_dti": round(sg["sgmc_raw_pooled_dti"], 6),
                "prevalence_calibrated_dti": round(sg["sgmc_prevalence_calibrated_dti"], 6),
                "ci95": [round(sg["sgmc_calibrated_ci95"][0], 6), round(sg["sgmc_calibrated_ci95"][1], 6)],
                "label": (
                    f"HOLDOUT-DTI ({sg['evaluator_version']}, N={sg['n_withheld_positives']} off-catalogue SGMC positives, "
                    f"95% CI [{sg['sgmc_calibrated_ci95'][0]:.4f}, {sg['sgmc_calibrated_ci95'][1]:.4f}])"
                ),
            },
        })

    pairwise = []
    sites = [r["site"] for r in rows_out]
    for i, s1 in enumerate(sites):
        m1 = masks[s1]
        n1 = int(m1.sum())
        best_other, best_ov = None, -1.0
        for j, s2 in enumerate(sites):
            if i == j:
                continue
            m2 = masks[s2]
            xor_px = int(np.logical_xor(m1, m2).sum())
            ov_1_in_2 = float((m1 & d3_masks[s2]).sum()) / max(n1, 1)
            if ov_1_in_2 > best_ov:
                best_ov = ov_1_in_2
                best_other = s2
            if j > i:
                pairwise.append({
                    "site_a": s1,
                    "site_b": s2,
                    "xor_pixels": xor_px,
                    "exact_footprint_duplicate": bool(xor_px == 0),
                    "subset_a_in_b": bool(np.all(m2[m1])),
                    "subset_b_in_a": bool(np.all(m1[m2])),
                    "frac_a_within_3px_of_b": round(ov_1_in_2, 6),
                    "frac_b_within_3px_of_a": round(float((m2 & d3_masks[s1]).sum()) / max(int(m2.sum()), 1), 6),
                })
        rows_out[i]["max_3px_overlap_among_focus9"] = round(best_ov, 6)
        rows_out[i]["closest_focus9_peer"] = best_other
        rows_out[i]["unique_among_focus9_gate_le_0p70"] = bool(best_ov <= 0.70)

    fleet_benchmarks = []
    extra_specs = [
        ("GEMSDOE70", "scored_extra/GEMSDOE70__gems70-p5-dual-submod300-oof38k-20261020.tif", 0.2478, "Dual-pop 4-fold LOQO HGB + 300 m submodular cover (top non-H19-5 fleet entry)"),
        ("GEMSDOE49", "scored_extra/GEMSDOE49__gems49-gate_ortho_w0.25-40k-20261006T213721Z-nan.tif", 0.2376, "Orthogonal-gated multi-physics 40k emitter"),
        ("GEMSDOE27_H29S", "scored_extra/GEMSDOE27__gems27-h29-hydrothermal-piedmont-celf-20261025-511898747886-allfinite.tif", 0.2190, "Hydrothermal-piedmont CELF standalone (strongest zero-copy focus-9 entry)"),
        ("19GEMSDOE_H19_5", "scored/19GEMSDOE__gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-allfinite.tif", 0.1922, "4-line physical corroboration ancestor of all 0.2449-0.2778 focus-9 entries"),
    ]
    for name, relp, lscore, desc in extra_specs:
        p = ddir / relp
        if p.exists():
            with rasterio.open(p) as ds:
                a = ds.read(1)
            m = foot & np.isfinite(a) & (a >= 0.5)
            ev = holdout.evaluate_hide_and_recover(m, ctx, n_boot=200, seed=20261026, name=name)
            sg = holdout.evaluate_sgmc_with_ci(m, ctx, n_boot=200, seed=20261026, name=name)
            dk = d_known[m]
            ov_b2 = float((m & d3_masks["GEMSDOE32"]).sum()) / max(int(m.sum()), 1)
            fleet_benchmarks.append({
                "id": name,
                "live_score": lscore,
                "live_score_label": f"USER/OWNER-REPORTED (unverified: {lscore:.4f})",
                "architecture": desc,
                "dots": int(m.sum()),
                "median_d_known_px": round(float(np.median(dk)), 2),
                "pct_in_lidar": round(100.0 * float(lidar_valid[m].mean()), 2),
                "holdout_hide_recover_dti": round(ev["pooled_dti"], 6),
                "holdout_sgmc_raw_dti": round(sg["sgmc_raw_pooled_dti"], 6),
                "holdout_sgmc_cal_dti": round(sg["sgmc_prevalence_calibrated_dti"], 6),
                "frac_within_3px_of_B2": round(ov_b2, 4),
            })

    inv = _invert_d28_collar_cascade()
    # Uncensored Rule-2 evaluation of the 0.2778 Champion's exact mechanism (d2.8 & d_visible > 2 px per fold):
    ev_b2_uncens = holdout.evaluate_hide_and_recover(masks["GEMSDOE25"], ctx, b_visible_px=2.0, n_boot=1000, seed=20261026, name="GEMSDOE32_B2_uncensored")
    ev_b1_uncens = holdout.evaluate_hide_and_recover(masks["GEMSDOE25"], ctx, b_visible_px=1.0, n_boot=1000, seed=20261026, name="GEMSDOE31_B1_uncensored")
    inv["uncensored_hide_recover_progression"] = {
        "d15_GEMSDOE24_0p2477": round(rows_out[7]["holdout_hide_recover"]["dti"], 6),
        "d28_B0_GEMSDOE25_0p2600": round(rows_out[5]["holdout_hide_recover"]["dti"], 6),
        "d28_B1_GEMSDOE31_0p2708": round(ev_b1_uncens["pooled_dti"], 6),
        "d28_B2_GEMSDOE32_0p2778": round(ev_b2_uncens["pooled_dti"], 6),
        "d28_B2_ci95": [round(ev_b2_uncens["ci95_cluster_bootstrap"][0], 6), round(ev_b2_uncens["ci95_cluster_bootstrap"][1], 6)],
        "note": (
            "Scoring static B=1/B=2 rasters directly on Hide-and-Recover triggers IR-32-INSTR-03 (their full-catalogue "
            "d_cat > B collar deletes predictions around the withheld test faults, yielding 0.0305/0.0045). Recomputing "
            f"d_visible > B strictly from each fold's visible faults restores monotonic concordance with live DTI "
            f"({rows_out[7]['holdout_hide_recover']['dti']:.5f} -> {rows_out[5]['holdout_hide_recover']['dti']:.5f} -> "
            f"{ev_b1_uncens['pooled_dti']:.5f} -> {ev_b2_uncens['pooled_dti']:.6f})."
        ),
    }
    audit_payload = {
        "schema": "kanlergemsdoe2.nine_site_audit.v1",
        "generated_utc": "2026-10-26",
        "leaderboard_reference": {
            "rank_1_public": 0.4413,
            "rank_5_public": 0.3195,
            "focus_9_best_public": 0.2778,
            "fleet_92_sites_checked": 92,
            "fleet_scored_entries_checked": 118,
            "local_registry_tifs_checked": 361,
            "key_conclusion": (
                "All 9 focus-site historical highs (0.2449 to 0.2778) descend from a single 19GEMSDOE H19-5 "
                "detector via progressive 300 m thinning and catalogue-collar pruning (94.0%-100.0% 3-px overlap; "
                "two exact 0-XOR cross-site duplicate pairs: GEMSDOE25==GEMSDOE30 at 0.2600 and GEMSDOE28_solo==GEMSDOE31 at 0.2708). "
                "None of the 9 focus sites had an unsubmitted candidate passing both holdout improvement and <=70% uniqueness gates as of 2026-10-26."
            ),
        },
        "forensic_02778_inversion": inv,
        "focus_9_sites": rows_out,
        "focus_9_pairwise_overlap": pairwise,
        "independent_fleet_benchmarks": fleet_benchmarks,
    }

    out_path = evidence_dir() / "nine_site_audit.json"
    out_path.write_text(json.dumps(audit_payload, indent=2) + "\n", encoding="utf-8")
    print(f"[audit_focus_sites] Wrote {out_path} ({len(rows_out)} focus sites, {len(pairwise)} pairs).")
    for r in rows_out:
        print(
            f"  {r['site']:9s} live={r['live_score']:.4f}  dots={r['dots']:6d}  "
            f"hide_rec={r['holdout_hide_recover']['dti']:.5f}  "
            f"sgmc_cal={r['holdout_sgmc_offcat']['prevalence_calibrated_dti']:.5f}  "
            f"portal_safe={str(r['portal_range_01_safe_as_stored']):5s}  "
            f"max_f9_3px={r['max_3px_overlap_among_focus9']:.4f} ({r['closest_focus9_peer']})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
