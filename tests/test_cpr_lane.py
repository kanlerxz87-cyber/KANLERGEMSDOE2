"""KG2-CPR lane: CELF order nestedness, negative-verdict receipts, promoted file untouched."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems32.htcads import emit_submodular_celf  # noqa: E402


def test_celf_return_order_backward_compatible_and_nested() -> None:
    rng = np.random.default_rng(0)
    pi = rng.random((60, 50), dtype=np.float32)
    elig = np.ones((60, 50), dtype=bool)
    m120 = emit_submodular_celf(pi, elig, max_dots=120)
    m120b, order = emit_submodular_celf(pi, elig, max_dots=120, return_order=True)
    m50 = emit_submodular_celf(pi, elig, max_dots=50)
    prefix = np.zeros_like(m120)
    prefix.ravel()[order[:50]] = True
    assert np.array_equal(m120, m120b), "return_order must not change the emission"
    assert order.size == 120 and len(np.unique(order)) == 120
    assert np.array_equal(prefix, m50), "greedy prefixes must equal smaller-budget runs"


def test_cpr_negative_verdict_and_gate_failure_recorded() -> None:
    exps = json.loads((ROOT / "evidence" / "cpr_experiments.json").read_text(encoding="utf-8"))
    assert exps["verdict"] == "negative"
    assert exps["selected_experiment"] is None
    assert exps["within_protocol_budget"]["experiments_run"] <= 3
    cpr1 = [e for e in exps["experiments"] if e["experiment_id"] == "CPR-1"][0]
    # The trap, on record: strong hide-recover, failed uniqueness, weak blind SGMC.
    assert cpr1["holdout_hide_recover"]["pooled_dti"] > 0.112353
    assert cpr1["uniqueness_audit"]["passed"] is False
    assert cpr1["uniqueness_audit"]["final_dots_max_detector_3px_overlap"] > 0.70
    assert cpr1["holdout_sgmc_offcat"]["sgmc_prevalence_calibrated_dti"] < 0.064121
    # Crest snapping falsified with strictly-negative paired CI.
    snap = [s for s in exps["crest_snap_ablation_hide_recover"] if s["budget"] == 37654][0]
    assert snap["paired_delta_vs_unsnapped_ci95"][1] < 0.0


def test_no_cpr_tif_offered_and_promoted_file_unchanged() -> None:
    downloads = ROOT / "docs" / "downloads"
    assert not list(downloads.glob("*cpr*.tif")), "negative lane must not ship a submittable TIF"
    assert (downloads / "cpr_run_card.json").exists()
    promoted = downloads / "kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif"
    assert hashlib.sha256(promoted.read_bytes()).hexdigest() == (
        "f482d3bad4b390470be06363b60867c8e42942101271caf4fa82ae3c3975abeb"
    )
    feed = json.loads((ROOT / "docs" / "data" / "status_feed.json").read_text(encoding="utf-8"))
    assert feed["validated_ok_to_download_and_submit"] is True
    assert feed["cpr_lane_20261027"]["verdict"] == "negative"
    assert feed["promoted_submission"]["sha256"] == hashlib.sha256(promoted.read_bytes()).hexdigest()


def test_ledger_recomputation_receipt() -> None:
    led = json.loads((ROOT / "evidence" / "ledger_recomputation_20261027.json").read_text(encoding="utf-8"))
    rec = led["recomputed"]
    # Exact OLS on the collar chain must reproduce inside the receipt's own rounding.
    n = np.array([44090.0, 40199.0, 37654.0])
    inv = 1.0 / np.array([0.2600, 0.2708, 0.2778])
    slope, intercept = np.polyfit(n, inv, 1)
    assert abs(0.2 / slope - rec["tp_w_px"]) < 0.2
    assert abs(intercept * (0.2 / slope) / 0.8 - rec["k_hidden_px"]) < 0.2
    assert rec["r_squared"] > 0.999
