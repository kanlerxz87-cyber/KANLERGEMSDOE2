#!/usr/bin/env python3
"""Finalize lane KANLER-EXT-CORROB: honest paired baselines, TIF, run card.

Leakage discipline (IR-EXT-01): for the supervised MCSUP surface the
global-model callable hide-recover (0.1598) and final-mask SGMC (0.3288) in
experiments_ext.json are CONTAMINATED (global model trained on the evaluated
labels/SGMC) and are excluded from every gate/estimate here. Only fold-local
OOF numbers gate MCSUP. For label-free CORROB all evaluations are clean.
"""
import json, pathlib, subprocess, sys
import numpy as np, rasterio
from scipy.ndimage import distance_transform_edt, binary_dilation, binary_erosion

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA, CACHE, EV = ROOT / "data", ROOT / ".cache", ROOT / "evidence"
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
from gems import metric
from run_experiments import quadrants
from promotion_gate import check as gate_check

ALPHA, BETA = 0.2, 0.8

def pooled(cells):
    tp = sum(c[0] for c in cells); fp = sum(c[1] for c in cells); n = sum(c[2] for c in cells)
    return float(tp / (tp + ALPHA * fp + BETA * (n - tp) + 1e-12))

def main():
    exp = json.loads((EV / "experiments_ext.json").read_text())
    with rasterio.open(DATA / "sample_submission.tif") as ds: foot = np.isfinite(ds.read(1))
    with rasterio.open(DATA / "labels.tif") as ds: labels = (ds.read(1) > 0) & foot
    with rasterio.open(DATA / "external/derived_sgmc_faults_100m_u8.tif") as ds: sgm = ds.read(1) > 0
    near = binary_dilation(labels, iterations=3)
    sgmc_off = sgm & ~labels & ~near & foot
    with rasterio.open(DATA / "registry/g32_champion.tif") as ds: champ = (ds.read(1) > 0) & foot

    # Champion scored inside the same OOF domains (fold-visible B=2 gate re-applied)
    q = quadrants(foot); cells_cat, cells_sg, champ_dots_in = [], [], 0
    for f in range(4):
        domain = binary_erosion(q == f, iterations=12) & foot
        collar = binary_dilation(q == f, iterations=15) & foot
        visible = labels & (foot & ~collar)
        d_vis = distance_transform_edt(~visible)
        dots = champ & domain & (d_vis > 2); champ_dots_in += int(dots.sum())
        for truth, acc in [(labels & domain, cells_cat), (sgmc_off & domain, cells_sg)]:
            r = metric.dti_binary(dots & ~visible, truth); acc.append((r["tp"], r["fp"], r["n_truth"]))
    rng = np.random.default_rng(11)
    def ci(cells):
        b = [pooled([cells[i] for i in rng.integers(0, len(cells), len(cells))]) for _ in range(2000)]
        return [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]
    champ_dom = {"label": "HOLDOUT-DTI (champion fixed dots restricted to OOF domains; diagnostic pairing only — champion dots were placed with full-catalogue knowledge, so catalogue value is pessimistic by the B-gate artefact)",
                 "catalogue_pooled": pooled(cells_cat), "catalogue_ci95": ci(cells_cat),
                 "sgmc_pooled": pooled(cells_sg), "sgmc_ci95": ci(cells_sg),
                 "sgmc_n": int(sum(c[2] for c in cells_sg)), "dots_in_domains": champ_dots_in}
    print("champion in-domain:", {k: (round(v, 5) if isinstance(v, float) else v) for k, v in champ_dom.items() if k != "label"})

    e3 = exp["EXP3_EMIT"]; oof = e3["oof"]
    e1_oof, e1_est = 0.12524379452733242, 0.218
    est_a = e1_est * (oof["pooled_dti"] / e1_oof)
    estimates = {
        "label": "MODEL ESTIMATE (projection — never a score; no organizer receipt exists for any new file)",
        "headline_anchorA_catalogueOOF_via_E1": {"value": est_a,
            "method": "0.218 (E1 SGMC-anchored estimate) x EXP3 OOF / E1 OOF; EXP3 and E1 catalogue OOF are statistically indistinguishable"},
        "anchorB_SGMC_ratio_REJECTED_for_MCSUP": {
            "value_if_used": 0.2778 * (oof["sgmc_oof_pooled_dti"] / champ_dom["sgmc_pooled"]),
            "why_rejected": "MCSUP trains on SGMC appearance; SGMC-ratio anchoring assumes cross-family proportionality falsified by direct SGMC emission (live 0.0512/0.0492 despite trivially maxing SGMC-DTI)"},
        "exp1_corrob_anchorB_clean": {"value": 0.2778 * (exp["EXP1_CORROB"]["sgmc_paired_vs_champion"]["candidate_sgmc_raw"] / 0.09606004283619353),
            "paired_diff_ci95": exp["EXP1_CORROB"]["sgmc_paired_vs_champion"]["diff_ci95"],
            "note": "CORROB never trains on SGMC so its SGMC anchor is admissible, but its catalogue OOF (0.0792) and callable hide-recover (0.0499) trail badly; split decision -> negative"},
        "headline_range": [round(est_a * 0.8, 3), round(est_a * 1.2, 3)],
    }

    # ---- write the unique TIF via the shared writer (fixes [0,1] portal error) ----
    note = "EXT MCSUP cat+SGMC HGB 44090d B2 | OOF 0.1264 =E1 | unique; NEGATIVE verdict, experiment only"
    assert len(note) <= 140, len(note)
    out = subprocess.run([sys.executable, "scripts/submission_writer.py", "--mask", ".cache/dots_EXP3_EMIT.npy",
                          "--slug", "ext-mcsup-44090d", "--note", note],
                         cwd=ROOT, capture_output=True, text=True)
    print(out.stdout[-1500:]); print(out.stderr[-500:], file=sys.stderr)
    receipt = json.loads(out.stdout[out.stdout.index("{"):])

    uniq = e3["uniqueness"]
    card = {
        "lane": "KANLER-EXT-CORROB (Exp3 EMIT = MCSUP surface @44,090 dots)",
        "hypothesis": "Multi-catalogue supervision (catalogue + off-catalogue SGMC positives, fold-local) plus holdout-tuned emission budget recovers blind faults better than catalogue-only supervision (E1) and the H19-5 champion lineage.",
        "mechanism": "HistGradientBoosting on the 47-ch label-free stack; positives = USGS/INGENIOUS catalogue UNION SGMC off-catalogue faults; spacing>=3px dotted emission matches the 300m DTI kernel; B=2 prune removes sub-bar near-catalogue dots (known faults are masked in scoring — DrivenData staff, community post 11516); budget 44,090 beat 37,654/25,000 on quadrant OOF.",
        "non_fault_mimic": "SGMC lithologic contacts and bedrock structures that are not Quaternary geothermal faults; mag/gravity lithology edges; roads/mine benches and terrace risers in LiDAR.",
        "named_non_fault_mimic": "SGMC lithologic contacts / inactive bedrock faults; lithologic mag-gravity edges; roads, mine benches, paleo-shoreline risers.",
        "holdout_dti": {
            "primary_oof": {"label": "HOLDOUT-DTI", "evaluator": oof["evaluator"], "value": oof["pooled_dti"],
                            "ci95": oof["ci95_foldbootstrap"], "n_withheld_positives": oof["n_withheld_positives"],
                            "E1_same_evaluator": e1_oof, "E1_ci95": [0.09675, 0.15658]},
            "sgmc_oof_foldlocal": {"label": "HOLDOUT-DTI", "value": oof["sgmc_oof_pooled_dti"], "ci95": oof["sgmc_oof_ci95"],
                                   "n_withheld_positives": oof["sgmc_oof_n"], "champion_in_domain_sgmc": champ_dom["sgmc_pooled"]},
            "exp1_corrob_clean": {"oof": exp["EXP1_CORROB"]["oof"]["pooled_dti"],
                                  "callable_visible_gated": exp["EXP1_CORROB"]["visible_gated_callable"]["dti"],
                                  "sgmc_final_clean": exp["EXP1_CORROB"]["sgmc_paired_vs_champion"]["candidate_sgmc_raw"],
                                  "champion_surface_proxy_visible_gated": 0.09920, "champion_sgmc": 0.09606},
            "contaminated_excluded_IR_EXT_01": {"EXP3_callable_global": e3["visible_gated_callable"]["dti"],
                                                "EXP3_sgmc_final_trained_on_sgmc": e3["sgmc_paired_vs_champion"]["candidate_sgmc_raw"]},
        },
        "leakage_canary": {"max_single_feature_abs_AUC": exp["meta"]["canary_max_auc"], "threshold": 0.90, "pass": True,
                           "detail": "evidence/canaries_ext.json (47 features, sampled AUC vs catalogue)"},
        "correlation_overlap_vs_registry": {"max_abs_surface_spearman": uniq["max_abs_surface_spearman"],
            "max_dot_overlap_3px_frac": uniq["max_dot_overlap_3px"], "vs_champion_dot_overlap_3px":
            next(r["dot_overlap_3px_euclidean"] for r in uniq["rows"] if "g32" in r["registry"]),
            "thresholds": {"spearman": 0.90, "dot_overlap": 0.70}, "pass": bool(uniq["pass"]),
            "registry": "9 focus-site bests + quarantined E1 mask (10 rasters); NOT the full ~100-site prompt registry — flagged IR-EXT-02",
            "surface_checked_before_placement": True},
        "estimated_live_score": estimates,
        "champion_in_domain_diagnostic": champ_dom,
        "raster_sha256": receipt["sha256"],
        "validator_output": receipt,
        "submission_name": receipt["unique_name"],
        "submission_note": note, "note_chars": len(note),
        "verdict": "negative",
        "verdict_plain": "DOWNLOAD: YES (unique, format-valid research file). SUBMIT AS EXPECTED IMPROVEMENT OVER 0.2778: NO — catalogue OOF ties E1 (0.1264 vs 0.1252, CIs overlap), headline MODEL ESTIMATE ~0.22 < 0.2778, and the flattering SGMC numbers for MCSUP are training-contaminated or population-shifted. Spend zero weekly slots today; promotion remains a separate selector step.",
        "ok_to_download_and_submit": False,
        "ok_to_download": True, "experiments_used": 3,
        "integration_review": {"prior_blindbasin_authorization": "withdrawn",
                               "reason": "Preserved from prior card: synthetic inputs/placeholder canary in concurrent-main blind-basin lane; originals under research/quarantine. This EXT lane supersedes it as a second, independently negative deliverable."},
        "irregularities": [
            "IR-EXT-01: EXP2/EXP3 callable hide-recover and final-mask SGMC use a globally trained surface -> contaminated; excluded from gates (fold-local OOF used instead).",
            "IR-EXT-02: uniqueness registry = 10 rasters (9 focus bests + E1), not every raster on the ~100 prompt sites; no full-registry certificate claimed.",
            "IR-EXT-03: sample_submission.tif ones sit exactly on catalogue faults (60,988 px), contradicting the problem page's 'total fault absence' wording; file used as grid/footprint template only.",
            "IR-EXT-04: training_features band-6 file description ('tilt angle or total curvature') conflicts with upstream forensic IR-32-BAND-02 (radiometric total count); bands consumed by index exactly as E1 lane, descriptions not trusted.",
            "IR-EXT-05: scripts/build_site_e1_xg_hgb.py and docs/lane-e1-xg-hgb.html contained committed merge-conflict markers; resolved this session (E1 side kept; stale builder quarantined).",
            "IR-EXT-06: GitHub contents API 403 (invalid GH_TOKEN + rate limit); data restored by anonymous git sparse clone, every sha256 pin verified. gh-based PR merge may need re-auth.",
        ],
        "blockers": ["No candidate beat the frozen holdout best (E1 OOF) with a positive paired CI",
                     "Full ~100-site registry not byte-restored for uniqueness certification",
                     "No organizer receipt for any new file; all historical scores OWNER-REPORTED",
                     "USGS FDSN/other external fetches blocked from sandbox bash egress"],
    }
    (EV / "run_card_ext.json").write_text(json.dumps(card, indent=2) + "\n")

    gate_in = {"lane": card["lane"], "registry_complete": False,
               "surface": {"max_abs_rank_correlation": uniq["max_abs_surface_spearman"], "max_overlap_3px": uniq["max_dot_overlap_3px"]},
               "dots": {"max_abs_rank_correlation": uniq["max_abs_surface_spearman"], "max_overlap_3px": uniq["max_dot_overlap_3px"]},
               "max_feature_alone_auc": exp["meta"]["canary_max_auc"],
               "holdout": {"label": "HOLDOUT-DTI", "evaluator_version": oof["evaluator"],
                           "withheld_positives": int(oof["n_withheld_positives"]), "dti": float(oof["pooled_dti"]),
                           "ci95": [float(x) for x in oof["ci95_foldbootstrap"]], "fold_local_features": True,
                           "baseline_id": "E1-XG-HGB quadrant OOF 0.12524 (evidence/experiments_oof.json)",
                           "paired_improvement_ci95": [float(oof["ci95_foldbootstrap"][0] - 0.15658), float(oof["ci95_foldbootstrap"][1] - 0.09675)]},
               "validator": {"no_nan_inside_footprint": bool(receipt["checks"]["no_nan_anywhere"]),
                             "range_0_1": bool(receipt["checks"]["values_in_0_1_everywhere"]),
                             "crs_match": bool(receipt["checks"]["crs_match"]), "shape_match": bool(receipt["checks"]["shape_match"]),
                             "transform_match": bool(receipt["checks"]["transform_match"]), "single_band": bool(receipt["checks"]["single_band"])},
               "raster_sha256": receipt["sha256"], "submission_name": receipt["unique_name"], "note": note}
    gate = gate_check(gate_in)
    sel = {"lane": card["lane"], "gate_input_summary": "paired_improvement_ci95 uses independent-CI bound (conservative); true paired fold diff also crosses zero (E1 >= EXP3 in 3 of 4 folds)",
           **gate, "ok_to_submit": False, "slot_approved": False,
           "reason": "Fail-closed selector: no positive paired improvement vs frozen holdout best and registry scope incomplete. Format validity is insufficient."}
    (EV / "selector_decision_ext.json").write_text(json.dumps(sel, indent=2) + "\n")
    # canonical run-card locations read by tests/site (verdict negative preserved)
    (ROOT / "research/run_card.json").write_text(json.dumps(card, indent=2) + "\n")
    (EV / "run_card.json").write_text(json.dumps(card, indent=2) + "\n")
    print(json.dumps({"tif": receipt["file"], "sha": receipt["sha256"][:16], "dots": receipt["dots"],
                      "gate_verdict": gate["verdict"], "gate_errors": gate["errors"],
                      "estimate_headline": est_a}, indent=2))

if __name__ == "__main__":
    main()
