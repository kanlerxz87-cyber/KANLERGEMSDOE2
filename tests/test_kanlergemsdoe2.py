"""Current negative decision, exact historical bytes, and public-report integrity."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio

from gems32 import metric

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_pooled_dti_retains_soft_predictions() -> None:
    truth = np.zeros((25, 25), dtype=bool)
    truth[12, 5:20] = True
    binary = np.zeros_like(truth, dtype=np.float32)
    binary[12, 6:18:3] = 1
    assert abs(metric.dti_exact(binary, truth)["dti"] - metric.dti_binary(binary > 0.5, truth)["dti"]) < 1e-9
    assert metric.dti_exact(binary * 0.25, truth)["dti"] > 0.05


def test_current_card_and_receipt_are_negative_and_consistent() -> None:
    cards = [json.loads((ROOT / p).read_text()) for p in
             ("run_card.json", "evidence/run_card.json", "docs/data/run_card.json", "docs/downloads/htcads_run_card.json")]
    assert all(card == cards[0] for card in cards)
    card = cards[0]
    assert {"hypothesis", "mechanism", "named_non_fault_mimic", "holdout_dti", "correlation_overlap_vs_registry",
            "raster_sha256", "validator_output", "submission_name", "note", "verdict"} <= card.keys()
    assert card["verdict"] == "negative" and card["ok_to_submit"] is False
    assert card["raster_sha256"] is None and card["submission_name"] is None
    assert card["new_raster_generated"] is False
    assert card["experiments_run"] == 0 and card["weekly_slots_used"] == 0
    assert len(card["note"]) <= 140 and "DO NOT SUBMIT" in card["note"]
    assert card["holdout_dti"]["value"] is None
    assert card["holdout_dti"]["prior_artifact_record_not_replayed"]["label"] == "HOLDOUT-DTI"
    old = card["existing_research_artifact"]
    assert old["ok_to_submit"] is False and old["new_this_session"] is False
    receipt = json.loads((ROOT / "evidence/validator_receipt.json").read_text())
    assert receipt["raster_sha256"] == old["sha256"] == sha(ROOT / old["path"])
    assert receipt["local_format_valid"] is True
    assert receipt["portal_acceptance"] == "unknown"
    assert receipt["format_audit"]["official_format_compliant"] is None
    assert receipt["literal_lattice_witness"]["within_3px_of_witness"] == 37_642
    assert receipt["gates"]["literal_registered_lattice_overlap"] is False
    assert receipt["gates"]["complete_registry_surface_and_final_replayed"] is False
    assert receipt["gates"]["separate_account_quota_selector_verified"] is False
    assert receipt["ok_to_submit"] is False


def test_historical_tiff_and_zip_are_research_bytes_not_authorization() -> None:
    card = json.loads((ROOT / "run_card.json").read_text())
    p = ROOT / card["existing_research_artifact"]["path"]
    z = p.with_suffix(".zip")
    with zipfile.ZipFile(z) as archive:
        assert archive.namelist() == [p.name]
        assert hashlib.sha256(archive.read(p.name)).hexdigest() == sha(p)
    with rasterio.open(p) as ds:
        assert ds.count == 1 and ds.dtypes == ("float32",)
        assert ds.shape == (3730, 3292) and ds.crs.to_epsg() == 32611
        assert list(ds.transform)[:6] == [100, 0, 243350, 0, -100, 4508550]
        a = ds.read(1)
    assert np.isfinite(a).all() and np.all((a >= 0) & (a <= 1))
    assert int((a > 0).sum()) == 37_654


def test_registry_witness_arithmetic_and_nine_site_provenance() -> None:
    pre = json.loads((ROOT / "evidence/registry_preflight_20261027.json").read_text())
    assert pre["duplicate_forced"] is True and pre["status"] == "DUPLICATE_STOP"
    assert pre["footprint_pixels"] == 5_167_373 and pre["covered_pixels"] == 5_160_724
    assert pre["uncovered_pixels"] == 6_649 and pre["candidate_budget"] == 37_654
    assert pre["at_least_overlapping_dots"] == 31_005
    assert pre["minimum_possible_directional_overlap"] == 31_005 / 37_654 > 0.7
    assert pre["first_budget_forced_to_exceed_limit"] == 22_164
    audit = json.loads((ROOT / "evidence/focus9_audit_20261027.json").read_text())
    refs = json.loads((ROOT / "registry/focus9_reference_20261027.json").read_text())["references"]
    assert len(audit["rows"]) == len(refs) == 9
    matrix = audit["directional_overlap_matrix"]
    for row in audit["rows"]:
        assert row["score_evidence"].startswith("USER_REPORTED_UNVERIFIED")
        assert re.fullmatch(r"[0-9a-f]{64}", row["sha256"])
        assert row["ref"] in row["download_url"] and row["filename"] in row["download_url"]
        assert row["portal_acceptance"].startswith("unknown")
        assert row["unique_vs_nine_rule"] is False
        assert row["max_directional_3px_overlap_vs_other_eight"] == max(
            value for peer, value in matrix[row["site"]].items() if peer != row["site"])
        assert row["max_directional_3px_overlap_vs_other_eight"] > 0.70
    assert next(r for r in audit["rows"] if r["site"] == "GEMSDOE25")["exact_mask_matches"] == ["GEMSDOE30"]
    assert sum(r["outside_nonfinite_pixels"] > 0 for r in audit["rows"]) == 5


def test_site_links_current_status_and_prompt_preservation() -> None:
    docs = ROOT / "docs"
    for page in ("index.html", "executive-summary.html", "research.html", "irregularities.html"):
        content = (docs / page).read_text()
        for ref in re.findall(r'(?:href|src)="([^"#?]+)', content):
            if ref.startswith(("https://", "http://", "mailto:", "javascript:")):
                continue
            assert (docs / ref).resolve().exists(), f"broken {page} link: {ref}"
    home = (docs / "index.html").read_text()
    assert "Do not submit." in home and "No new GeoTIFF was generated" in home
    assert "ORGANIZER-CONFIRMED" not in home
    assert "owner/user-reported" in home and "portal acceptance" in home.lower()
    readme = (ROOT / "README.md").read_text()
    assert "Maximize P(Win)" in readme and "Own the Outcome" in readme
    assert "f482d3bad4b390470be06363b60867c8e42942101271caf4fa82ae3c3975abeb" in readme
    prompt = (ROOT / "PROMPT.md").read_text().split("\n\n", 1)[1]
    assert prompt.strip() in readme
    feed = json.loads((docs / "data/status_feed.json").read_text())
    assert feed["verdict"] == "negative" and feed["ok_to_submit"] is False


def test_legacy_verification_does_not_reauthorize_kg2() -> None:
    proc = subprocess.run([sys.executable, str(ROOT / "scripts/evaluate_holdout.py"), "--verify-kg2"],
                          text=True, capture_output=True, check=True)
    out = json.loads(proc.stdout)
    assert out["verified"] is True and out["holdout_replayed"] is False
    assert out["holdout_label"].startswith("HOLDOUT-DTI")
    assert out["ok_to_submit"] is False and out["verdict"] == "negative"
