#!/usr/bin/env python3
"""Independent byte-level re-validation of the standing KG2-S2 DSLUP file with the KG2-S3 gate code.

Gates 1 (format), 3 (uniqueness vs all 360 registry rasters + 124 scored-ledger rasters, null-calibrated
for space-filling controls) and 5 (metadata) are recomputed from bytes.  Gates 2 (canary) and 4 (holdout)
come from the KG2-S2 evaluator receipt (evidence/dslup_unique_slot_run_card.json), accepted only if its
recorded raster sha256 equals the sha256 of the file on disk.  Gate 4 uses the bar under which the file
was promoted in KG2-S2 (unique-slot mode: HR point > champion proxy AND SGMC-CAL paired CI > 0).
The LLI live-score PROJECTION is attached for information only; it cannot promote or veto.
Output: evidence/kg2s3_dslup_revalidation.json; prints ONE verdict.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import validate_submission_kg2s3 as v  # noqa: E402
from gems32.paths import data_dir  # noqa: E402

TIF = ROOT / "docs/downloads/kanlergems2-dslup-uniq-q15k-37654dots-20261027T181253Z-c71122d5-zeros.tif"


def main() -> int:
    ddir = data_dir()
    card = json.loads((ROOT / "evidence/dslup_unique_slot_run_card.json").read_text())
    with rasterio.open(ddir / "sample_submission.tif") as t:
        foot = np.isfinite(t.read(1))
    sha = v.sha256_file(TIF)
    g1, dots = v.gate_format(TIF, ddir)
    bound = sha == card["raster_sha256"]
    can = card["leakage_canary"]
    hr = card["holdout_dti"]["primary_hide_and_recover"]
    sg = card["holdout_dti"]["secondary_off_catalogue_sgmc"]
    g2 = {"passed": bool(bound and can["passed"] and can["max_single_feature_auc"] <= 0.90),
          "receipt_bound_by_raster_sha256": bound, "max_auc": can["max_single_feature_auc"], "max_feature": can["max_feature_name"]}
    g3 = v.gate_uniqueness(sha, dots, foot, ddir, None) if dots is not None else {"passed": False}
    g4 = {"passed": bool(bound and hr["pooled_dti"] > hr["champion_02778_same_evaluator"] and sg["paired_delta_ci95"][0] > 0),
          "bar": "KG2-S2 unique-slot: HR point > champion proxy AND SGMC-CAL paired 95% CI > 0",
          "hr": hr["label"], "hr_pooled_dti": hr["pooled_dti"], "champion_proxy": hr["champion_02778_same_evaluator"],
          "sgmc_cal_dti": sg["sgmc_prevalence_calibrated_dti"], "sgmc_paired_ci95": sg["paired_delta_ci95"]}
    reg = json.loads((ROOT / "registry/comparison_registry.json").read_text())["entries"]
    stems = {Path(e["filename"]).stem for e in reg}
    name, note = card["submission_name"], card["submission_note"]
    g5 = {"passed": bool(name and name not in stems and 0 < len(note) <= 140), "name": name, "note": note, "note_chars": len(note)}
    gates = {"gate_1_format_0_1": g1, "gate_2_canary": g2, "gate_3_uniqueness": g3, "gate_4_holdout": g4, "gate_5_metadata": g5}
    ok = all(g.get("passed") for g in gates.values())
    emis = ROOT / "evidence/kg2s3_lope_emission.json"
    proj = json.loads(emis.read_text())["references_same_identity"].get("DSLUP_KG2S2") if emis.exists() else None
    out = {"schema": "kg2s3.dslup_revalidation.v1", "tif": TIF.name, "tif_sha256": sha, "human_intervention_required": False,
           "gates": gates, "verdict": "OK_TO_SUBMIT" if ok else "NOT_OK_DO_NOT_SUBMIT",
           "failed_gates": [k for k, g in gates.items() if not g.get("passed")],
           "lli_live_projection": {"label": "PROJECTION (not a score)", **(proj or {}),
                                   "champion_same_identity": json.loads(emis.read_text())["references_same_identity"]["champion_G32"]["projected_dti"] if emis.exists() else None,
                                   "error_band_leave_site_out_mae": json.loads(emis.read_text())["projection_error_band"]["leave_site_out_mae"] if emis.exists() else None}}
    (ROOT / "evidence/kg2s3_dslup_revalidation.json").write_text(json.dumps(out, indent=1, allow_nan=False) + "\n")
    print(json.dumps({k: out[k] for k in ("tif", "verdict", "failed_gates", "lli_live_projection")}, indent=1))
    print("max non-space-filling overlap:", g3.get("max_overlap_3px_non_space_filling"), "duplicates:", g3.get("duplicates"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
