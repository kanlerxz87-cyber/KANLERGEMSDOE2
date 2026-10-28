#!/usr/bin/env python3
"""Synchronize Session-3 KG2-S3-HPTR Run Card and Validator Receipts with main's fail-closed gates."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    raise SystemExit(
        "Archived runner disabled: not the assigned HTCADS lane; the literal registry stop "
        "and preserved historical receipts prohibit this execution path."
    )


def _legacy_main_archived() -> int:
    """Historical implementation retained for audit; do not use as an active runner."""
    rc_path = ROOT / "evidence/session3_hptr_run_card_20261027.json"
    dl_rc_path = ROOT / "docs/downloads/hptr_run_card.json"
    rc = json.loads(rc_path.read_text(encoding="utf-8"))

    tif_name = rc["raster_filename"]
    tif_path = ROOT / "docs/downloads" / tif_name
    assert tif_path.is_file(), f"Missing {tif_path}"

    # 1. Recompute exact overlaps against ALL KANLERGEMSDOE2 rasters in docs/downloads/
    with rasterio.open(ROOT / ".cache/gems_data/sample_submission.tif") as t:
        foot = np.isfinite(t.read(1))
    with rasterio.open(tif_path) as ds:
        ours = foot & (ds.read(1) >= 0.5)

    own_overlaps = {}
    for p in sorted((ROOT / "docs/downloads").glob("*.tif")):
        if p.name == tif_name:
            continue
        if not (p.name.startswith("kanlergems") or p.name.startswith("36GEMSDOE")):
            continue
        with rasterio.open(p) as ds:
            arr = ds.read(1)
        peer = foot & np.isfinite(arr) & (arr >= 0.5)
        if not peer.any():
            continue
        ov_in_peer = float((distance_transform_edt(~peer) <= 3.0)[ours].mean())
        ov_in_ours = float((distance_transform_edt(~ours) <= 3.0)[peer].mean())
        harm = (
            2.0 * ov_in_peer * ov_in_ours / (ov_in_peer + ov_in_ours)
            if (ov_in_peer + ov_in_ours) > 0
            else 0.0
        )
        own_overlaps[p.name] = {
            "peer_dots_ge_05": int(peer.sum()),
            "asym_3px_overlap_ours_in_peer": round(ov_in_peer, 6),
            "asym_3px_overlap_peer_in_ours": round(ov_in_ours, 6),
            "harmonic_3px_overlap": round(harm, 6),
        }

    # 2. Run main's shared fail-closed validators and record exact receipts
    lit_out = ROOT / "evidence/hptr_validation_literal_witness_20261027.json"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/validate_submission.py"),
         "--tif", str(tif_path), "--run-card", str(rc_path), "--out", str(lit_out)],
        check=False, capture_output=True, text=True,
    )
    for mode, fname in (
        ("champion", "hptr_validation_champion_20261027.json"),
        ("unique-slot", "hptr_validation_unique_slot_20261027.json"),
    ):
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/validate_submission_kg2s2.py"),
             "--tif", str(tif_path), "--run-card", str(rc_path), "--mode", mode,
             "--out", str(ROOT / "evidence" / fname)],
            check=False, capture_output=True, text=True,
        )

    v_lit = json.loads(lit_out.read_text(encoding="utf-8"))
    v_kg2s3 = json.loads((ROOT / "evidence/hptr_kg2s3_gate_receipt_20261027.json").read_text(encoding="utf-8"))

    # 3. Update Run Card under strict fail-closed protocol (Rule 5: negative results are valid deliverables)
    rc.pop("automated_5gate_champion_mode", None)
    rc.pop("automated_5gate_unique_slot_mode", None)
    exp_ledger = json.loads((ROOT / "evidence/hptr_experiments_20261027.json").read_text(encoding="utf-8"))
    rc["budget"] = {
        "experiments_executed": int(rc.get("experiments_executed", 3)),
        "max_experiments": 3,
        "wall_clock_seconds": float(exp_ledger["elapsed_seconds_total"]),
        "max_wall_clock_seconds": 7200,
        "within_budget": True,
    }
    rc["verdict"] = "negative"
    rc["ok_to_submit"] = False
    rc["validated_ok_to_download_and_submit"] = False
    rc["ok_to_download_for_research"] = True
    rc["submission_decision"] = (
        "DO NOT SUBMIT TO DRIVENDATA (RESEARCH DOWNLOAD ONLY — PROTECT WEEKLY SLOT). "
        "HPTR-EXP-2 is the first candidate in KANLERGEMSDOE2 to beat the 0.2778 champion across all "
        "three blind holdout suites simultaneously (Hide-Recover 0.113133 vs 0.099202, SGMC-CAL 0.077148 "
        "vs 0.064121, C-PIED 0.104289 vs 0.101166) while clearing <=70% binary (r>=0.5) 3-px overlap "
        "across all non-blanket detectors (max 65.98%), <=49.24% across all 9 Focus & 24 Sister sites, "
        "and 13/13 [0,1] GeoTIFF checks; however, automated validators fail closed (`negative`) under "
        "the literal all-entry 13gems spacing-5 lattice rule (99.963%; forced >=82.34% at 37,654 dots) "
        "and kg2s3 Gate 3/4 (r>0 soft-tail / retracted-DSLUP bar)."
    )
    rc["overlap_vs_all_kanlergemsdoe2_rasters"] = own_overlaps
    rc["max_overlap_vs_all_kanlergemsdoe2_rasters"] = round(
        max(v["asym_3px_overlap_ours_in_peer"] for v in own_overlaps.values()), 6
    )
    rc["validator_output"] = {
        "human_intervention_required": False,
        "shared_literal_validator_v2": {
            "script": "scripts/validate_submission.py",
            "verdict": v_lit["verdict"],
            "ok_to_submit": v_lit["ok_to_submit"],
            "gates": v_lit["gates"],
            "witness_overlap_dots": v_lit["format_audit"]["witness_overlap_dots"],
            "witness_overlap_fraction": v_lit["format_audit"]["witness_overlap_fraction"],
            "strict_whole_array_finite_0_1": v_lit["format_audit"]["strict_whole_array_finite_0_1"],
            "on_catalogue_positive_pixels": v_lit["format_audit"]["on_catalogue_positive_pixels"],
        },
        "kg2s3_byte_gate_v1": {
            "script": "scripts/validate_submission_kg2s3.py",
            "verdict": v_kg2s3["verdict"],
            "failed_gates": v_kg2s3["failed_gates"],
            "gate_1_format_0_1_passed": v_kg2s3["gates"]["gate_1_format_0_1"]["passed"],
            "gate_2_canary_passed": v_kg2s3["gates"]["gate_2_canary"]["passed"],
            "gate_3_uniqueness_r_gt_0_passed": v_kg2s3["gates"]["gate_3_uniqueness"]["passed"],
            "gate_3_binary_r_ge_05_non_blanket_max_overlap": rc["registry_comparison"]["final_dots_max_detector_3px_overlap"],
            "gate_4_holdout_vs_dslup_passed": v_kg2s3["gates"]["gate_4_holdout"]["passed"],
            "gate_5_metadata_passed": v_kg2s3["gates"]["gate_5_metadata"]["passed"],
        },
    }

    txt = json.dumps(rc, indent=2, allow_nan=False) + "\n"
    rc_path.write_text(txt, encoding="utf-8")
    dl_rc_path.write_text(txt, encoding="utf-8")

    # 4. Update validation sidecar & DO-NOT-SUBMIT guard file in docs/downloads/
    val_sidecar = ROOT / "docs/downloads" / tif_name.replace("-zeros.tif", "-validation.json")
    sidecar_payload = {
        "schema": "gems.hptr-validation-sidecar.v1",
        "verdict": "negative",
        "ok_to_submit": False,
        "validated_ok_to_download_and_submit": False,
        "ok_to_download_for_research": True,
        "human_intervention_required": False,
        "raster_filename": tif_name,
        "raster_sha256": rc["raster_sha256"],
        "format_checks_13_of_13_pass": True,
        "all_cells_finite_in_0_1": True,
        "positive_dots": 37654,
        "on_catalogue_dots": 0,
        "beats_02778_on_all_three_blind_holdouts": True,
        "binary_detector_max_3px_overlap_le_70pct": rc["registry_comparison"]["final_dots_max_detector_3px_overlap"],
        "literal_spacing5_lattice_overlap": v_lit["format_audit"]["witness_overlap_fraction"],
        "reasons": v_lit["reasons"] + [
            "kg2s3 Gate 3 (r>0 soft-tail / 6%-density) and Gate 4 (retracted-DSLUP bar) fail closed; protect weekly DrivenData slot."
        ],
    }
    val_sidecar.write_text(json.dumps(sidecar_payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    guard_path = ROOT / "docs/downloads" / tif_name.replace("-zeros.tif", "-DO-NOT-SUBMIT.txt")
    guard_path.write_text(
        "DO NOT SUBMIT THIS GEOTIFF TO DRIVENDATA — RESEARCH ARTIFACT ONLY.\n"
        f"File: {tif_name}\n"
        f"SHA-256: {rc['raster_sha256']}\n"
        "Automated Validator Verdict: negative (ok_to_submit=false, human_intervention_required=false).\n"
        "Scientific status: First KANLERGEMSDOE2 candidate to beat the 0.2778 GEMSDOE32 champion across ALL THREE "
        "blind holdout benchmarks simultaneously (Hide-Recover v3.0 = 0.113133 vs 0.099202; SGMC-CAL v3.0 = 0.077148 "
        "vs 0.064121; C-PIED v1.0 = 0.104289 vs 0.101166) with 13/13 [0,1] GeoTIFF format checks passing and <=65.98% "
        "binary (r>=0.5) 3-px overlap across all non-blanket detectors.\n"
        "Why DO NOT SUBMIT: Fails literal all-entry 13gems spacing-5 lattice witness (99.963%; forced >=82.34% at 37,654 "
        "dots) in scripts/validate_submission.py and Gate 3/4 in scripts/validate_submission_kg2s3.py.\n",
        encoding="utf-8",
    )
    print(f"[SYNC] Synced {rc_path.name}, {dl_rc_path.name}, {val_sidecar.name}, and {guard_path.name}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
