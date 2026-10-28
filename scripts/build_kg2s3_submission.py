#!/usr/bin/env python3
"""KG2-S3: write the LOPE candidate with the SHARED writer, run the automated gate, emit the Run Card.

The TIFF is always written to the ignored work cache first.  It is copied to docs/downloads ONLY when
the automated gate (scripts/validate_submission_kg2s3.py) returns OK_TO_SUBMIT; otherwise the candidate
is a documented NEGATIVE and only its sha256 and Run Card are published.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems32.paths import data_dir, docs_dir, work_dir  # noqa: E402
from gems32.submission import write_submission_bundle  # noqa: E402


def main() -> int:
    ddir, wdir = data_dir(), work_dir() / "kg2s3"
    emis = json.loads((ROOT / "evidence/kg2s3_lope_emission.json").read_text())
    hold = json.loads((ROOT / "evidence/kg2s3_lope_holdout.json").read_text())
    cvsel = json.loads((ROOT / "evidence/kg2s3_lli_design_cv.json").read_text())
    z = np.load(wdir / "lope_dots.npz")
    dots = z["constrained"].astype(bool)
    np.save(wdir / "lope_surface.npy", z["lam"].astype(np.float32))
    with rasterio.open(ddir / "sample_submission.tif") as s:
        foot = np.isfinite(s.read(1))
    with rasterio.open(ddir / "labels.tif") as s:
        cat = (s.read(1) > 0) & foot
    tag = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    n = int(dots.sum())
    slug = f"s3-lope-q68-{n}dots"
    bundle = write_submission_bundle(dots.astype(np.float32), foot, cat, ddir / "sample_submission.tif", wdir / "out",
                                     slug, tag, {"lane": "KG2-S3 LOPE"}, prefix="kanlergems2")
    tif = Path(bundle["zeros_path"]) if "zeros_path" in bundle else sorted((wdir / "out").glob(f"*{slug}*-zeros.tif"))[-1]
    name = tif.stem
    hr = hold["hide_and_recover"]
    note = (f"KG2-S3 LOPE: live-ledger density (dcat x dH19-5 x scarp), DTI-greedy dots, 32% novelty quota; "
            f"HR {hr['pooled_dti']:.3f}")[:140]
    gate_out = ROOT / "evidence/kg2s3_submission_gate.json"
    cmd = [sys.executable, str(ROOT / "scripts/validate_submission_kg2s3.py"), "--tif", str(tif), "--name", name,
           "--note", note, "--surface-npy", str(wdir / "lope_surface.npy"), "--out", str(gate_out)]
    rc = subprocess.run(cmd, capture_output=True, text=True)
    gate = json.loads(gate_out.read_text())
    ok = gate["verdict"] == "OK_TO_SUBMIT"
    published = None
    if ok:
        dst = docs_dir() / "downloads" / tif.name
        shutil.copy2(tif, dst)
        published = str(dst.relative_to(ROOT))
    u = gate["gates"].get("gate_3_uniqueness", {})
    card = {
        "schema": "kg2s3.run_card.v1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hypothesis": "KG2-S3-H1 LOPE: hidden expert-fault density depends on distance to the public catalogue, "
                      "distance to the public H19-5 ridge network and label-free scarp evidence; a density fitted "
                      "to live scores, emitted by an exact DTI-greedy rule, maximises expected DTI.",
        "mechanism": "Live-Ledger Inversion (exact TP identity) on 123 USER-REPORTED pinned rasters; leave-site-out "
                     "selected design; two-phase emission (inside H19-5 halo DTI-greedy, outside halo forced novelty "
                     "quota 32%).",
        "named_non_fault_mimic": "Lake Lahontan wave-cut shorelines, stream-terrace risers and road cuts (one-sided "
                                 "scarps that inflate the scarp factor); the novelty-quota dots are most exposed.",
        "preregistration": "knowledge/03_preregistered_hypotheses_kg2s3_20261027.md",
        "experiment_budget": {"allowed": 3, "used": 2, "E1": "LLI design CV (leave-site-out)", "E2": "LOPE emission + holdouts",
                              "E3": "not run: E2 negative, and no remaining lane could pass both the uniqueness and holdout gates in budget"},
        "duplicate_lane_logged_and_stopped": {"lane": "LOPE unconstrained (100% of dots within 3 px of H19-5)",
                                              "action": "logged, not packaged (protocol rule 1)"},
        "design_selection": cvsel["selected"],
        "h1_physical_factor_supported": bool(
            cvsel["designs"]["C0_dcat_x_dH19"]["grid"][0]["leave_site_out_mae"] - cvsel["selected"]["leave_site_out_mae"] >= 0.001),
        "holdout_dti": {
            "primary_hide_and_recover": {
                "label": "HOLDOUT-DTI", "evaluator_version": hr["evaluator_version"],
                "n_withheld": hr["n_withheld_positives"], "pooled_dti": hr["pooled_dti"],
                "ci95": hr["ci95_cluster_bootstrap"],
                "champion_same_evaluator": hold["hide_and_recover_champion_same_evaluator"]["pooled_dti"],
                "paired_delta_vs_champion": hold["hide_and_recover_paired_delta_vs_champion"],
                "dslup_recorded": hold["dslup_recorded_reference"]["hr_pooled"]},
            "secondary_sgmc_cal": {
                "label": "HOLDOUT-DTI", "evaluator_version": hold["sgmc_cal"]["evaluator_version"],
                "n_withheld": hold["sgmc_cal"]["n_withheld_positives"],
                "dti": hold["sgmc_cal"]["sgmc_prevalence_calibrated_dti"], "ci95": hold["sgmc_cal"]["sgmc_calibrated_ci95"],
                "champion_same_evaluator": hold["sgmc_cal_champion_same_evaluator"]["sgmc_prevalence_calibrated_dti"],
                "paired_delta_vs_champion": hold["sgmc_cal_paired_delta_vs_champion"],
                "dslup_recorded": hold["dslup_recorded_reference"]["sgmc_cal"]},
        },
        "projection_lli": {"label": "PROJECTION (not a score)", "candidate": emis["constrained"]["projected_dti"],
                           "champion_same_identity": emis["references_same_identity"].get("champion_G32", {}).get("projected_dti"),
                           "dslup_same_identity": emis["references_same_identity"].get("DSLUP_KG2S2", {}).get("projected_dti"),
                           "unconstrained_duplicate_lane": emis["unconstrained"]["projected_dti"],
                           "error_band": emis["projection_error_band"]},
        "leakage_canary": hold["leakage_canary"],
        "registry_comparison": {k: u.get(k) for k in ("n_references_compared", "n_registry_missing", "exact_sha256_unique",
                                                      "max_overlap_3px_non_space_filling", "max_abs_final_dots_spearman",
                                                      "max_abs_surface_spearman", "space_filling_controls",
                                                      "top10_overlap_non_space_filling", "duplicates")},
        "raster_sha256": gate["tif_sha256"], "raster_filename": tif.name, "positive_dots": n,
        "validator": {"script": "scripts/validate_submission_kg2s3.py", "verdict": gate["verdict"],
                      "failed_gates": gate["failed_gates"], "receipt": "evidence/kg2s3_submission_gate.json",
                      "exit_code": rc.returncode},
        "submission_name": name, "submission_note": note, "submission_note_chars": len(note),
        "published_download": published,
        "verdict": "promote" if ok else "negative",
    }
    (ROOT / "evidence/kg2s3_run_card.json").write_text(json.dumps(card, indent=1, allow_nan=False) + "\n")
    print(json.dumps({k: card[k] for k in ("raster_filename", "raster_sha256", "verdict", "published_download")}, indent=1))
    print("failed gates:", gate["failed_gates"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
