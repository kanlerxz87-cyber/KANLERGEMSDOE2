"""Current evidence and static-site regression checks: no historical auto-promotion."""
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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_metric_soft_and_binary_agree_without_dropping_soft_scores() -> None:
    truth = np.zeros((25, 25), dtype=bool)
    truth[12, 5:20] = True
    pred = np.zeros((25, 25), dtype=np.float32)
    pred[12, 6:18:3] = 1.0
    assert abs(metric.dti_exact(pred, truth)["dti"] - metric.dti_binary(pred > 0.5, truth)["dti"]) < 1e-9
    assert metric.dti_exact(pred * 0.25, truth)["dti"] > 0.05


def test_current_card_is_negative_and_references_the_exact_historical_bytes() -> None:
    card = json.loads((ROOT / "run_card.json").read_text())
    assert card == json.loads((ROOT / "docs/data/run_card.json").read_text())
    assert card == json.loads((ROOT / "docs/downloads/htcads_run_card.json").read_text())
    assert card["verdict"] == "negative" and card["ok_to_submit"] is False
    assert card["new_experiments_this_session"] == 0 and card["submission_slots_used"] == 0
    assert card["new_raster_generated_this_session"] is False
    assert 0 < len(card["note"]) <= 140
    hold = card["holdout_dti"]
    assert hold["label"] == "HOLDOUT-DTI" and hold["replayed_this_session"] is False
    assert hold["evaluator_version"] and hold["n_withheld_positive_pixels"] == 22232
    assert len(hold["ci95"]) == 2 and hold["is_leaderboard_prediction"] is False
    assert card["estimated_organizer_score"] is None
    nov = card["correlation_overlap_vs_registry"]
    assert nov["duplicate_stop_triggered"] and nov["final_3px_lattice_overlap_fraction"] > 0.70
    assert nov["all_registry_entries_replayed"] is False
    assert nov["pre_placement_surface_replayed"] is False

    tif = ROOT / "docs/downloads" / card["submission_name"]
    assert sha256(tif) == card["raster_sha256"]
    with rasterio.open(tif) as ds:
        assert ds.count == 1 and ds.dtypes == ("float32",)
        assert (ds.height, ds.width) == (3730, 3292)
        assert ds.crs.to_epsg() == 32611
        assert tuple(ds.transform)[:6] == (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
        arr = ds.read(1)
    assert np.isfinite(arr).all() and ((arr >= 0) & (arr <= 1)).all()
    assert int((arr > 0).sum()) == 37654
    assert card["validator_output"]["all_cells_in_0_1"]
    assert card["validator_output"]["nonfinite_inside_footprint"] == 0
    with zipfile.ZipFile(tif.with_suffix(".zip")) as zf:
        assert zf.namelist() == [tif.name]
        assert hashlib.sha256(zf.read(tif.name)).hexdigest() == card["raster_sha256"]


def test_superseded_public_approvals_are_negative() -> None:
    for rel in ("evidence/run_card.json", "evidence/kg2_run_card_20261026.json",
                "evidence/validator_receipt.json", "docs/downloads/htcads_run_card.json"):
        data = json.loads((ROOT / rel).read_text())
        assert data["verdict"] == "negative", rel
        assert data.get("ok_to_submit", data.get("ok_to_download_and_submit", data.get("validated_ok_to_download_and_submit"))) is False
    reasons = json.loads((ROOT / "evidence/validator_receipt.json").read_text())["reasons"]
    assert any("literal registry duplicate" in r for r in reasons)
    assert any("quota" in r for r in reasons)


def test_nine_site_reaudit_and_lattice_bound() -> None:
    audit = json.loads((ROOT / "evidence/focus_reaudit_20261027.json").read_text())
    assert not audit["missing_focus_sites"] and len(audit["focus_sites"]) == 9
    for row in audit["focus_sites"]:
        assert len(row["file_audit"]["sha256"]) == 64
        assert row["focus_site_comparisons"][0]["fraction_candidate_dots_within_3px"] > .70
        assert "user/owner report" in row["value_provenance"]
        assert row["organizer_receipt_verified"] is False
    lattice = audit["registry_lattice"]
    assert lattice["footprint_pixels"] == 5_167_373
    assert lattice["covered_within_3px"] == 5_160_724
    assert lattice["uncovered_within_3px"] == 6_649
    assert len(audit["previous_local_candidates"]) == 3
    for row in audit["previous_local_candidates"]:
        assert row["lattice_overlap_fraction"] > .995
        assert row["pigeonhole_min_overlap_fraction"] > .70
    rows = {r["site"]: r for r in audit["focus_sites"]}
    same = next(x for x in rows["GEMSDOE25"]["focus_site_comparisons"] if x["site"] == "GEMSDOE30")
    assert same["same_footprint_pixels"]


def test_pages_and_links_are_explicitly_fail_closed() -> None:
    docs = ROOT / "docs"
    for page in ("index.html", "executive-summary.html", "research.html", "irregularities.html"):
        text = (docs / page).read_text()
        assert 'name="viewport"' in text and 'lang="en"' in text
        assert "Own the Outcome" in text
        for match in re.finditer(r'(?:href|src)="([^"#?]+)"', text):
            ref = match.group(1)
            if ref.startswith(("https://", "http://", "mailto:")):
                continue
            assert (docs / ref).exists(), f"broken local link {ref} on {page}"
    front = (docs / "index.html").read_text()
    summary = (docs / "executive-summary.html").read_text()
    assert "DO NOT SUBMIT" in front and "audit only" in front
    assert "USER/OWNER REPORT" in summary and "DO NOT SUBMIT" in summary
    for site in (24, 25, 27, 28, 30, 31, 32, 33, 36):
        assert f"GEMSDOE{site}" in summary
    assert not re.search(r"0\.2778.{0,40}ORGANIZER.CONFIRMED", summary, re.IGNORECASE)
    readme = (ROOT / "README.md").read_text()
    assert "Maximize P(Win)" in readme and "Own the Outcome" in readme
    assert "PARALLEL-RUN PROTOCOL" in readme and "DO NOT SUBMIT" in readme


def test_negative_verification_without_restored_inputs(tmp_path: Path) -> None:
    card = json.loads((ROOT / "run_card.json").read_text())
    proc = subprocess.run([
        sys.executable, str(ROOT / "scripts/validate_submission.py"), "--tif",
        str(ROOT / "docs/downloads" / card["submission_name"]), "--run-card", str(ROOT / "run_card.json"),
        "--data-dir", str(tmp_path),
    ], text=True, capture_output=True)
    assert proc.returncode == 1
    result = json.loads(proc.stdout)
    assert result["verdict"] == "negative" and result["validated_ok_to_download_and_submit"] is False
    assert "could not be completed" in result["reasons"][0]


def test_leaderboard_parser_fails_closed_on_bad_or_ambiguous_source() -> None:
    from scripts.refresh_leaderboard import parse_leaderboard
    import pytest
    sample = """<table><tr><th>Rank</th><th>Name</th><th>Score</th></tr>
      <tr><td>#1</td><td>one</td><td>0.4544</td></tr>
      <tr><td>#5</td><td>five</td><td>0.3566</td></tr></table>"""
    assert parse_leaderboard(sample) == {1: .4544, 5: .3566}
    for text in ("please log in", sample.replace("0.3566", "???"),
                 sample.replace("0.4544", "0.1000"), sample.replace("</td></tr>", "</td><td>0.1234</td></tr>", 1)):
        with pytest.raises(ValueError):
            parse_leaderboard(text)
