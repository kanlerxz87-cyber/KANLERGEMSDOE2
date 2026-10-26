"""Small synthetic fixtures exercise safety gates, not competition performance."""
from pathlib import Path
import hashlib
import json

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

import audit_uniqueness
import submission_writer
from validate_raster import sha256_file, validate


def save_tif(path, array, *, nodata=None, crs="EPSG:32611", count=1, dtype="float32"):
    array = np.asarray(array)
    with rasterio.open(path, "w", driver="GTiff", height=array.shape[0], width=array.shape[1],
                       count=count, dtype=dtype, crs=crs, nodata=nodata,
                       transform=from_origin(1000, 2000, 100, 100)) as dst:
        for band in range(1, count + 1):
            dst.write(array.astype(dtype), band)
    return path


@pytest.fixture
def scene(tmp_path):
    shape = (32, 32)
    template_array = np.zeros(shape, dtype=np.float32)
    template_array[0, :] = np.nan
    template = save_tif(tmp_path / "template.tif", template_array, nodata=np.nan)
    fp = np.isfinite(template_array)
    reference = np.zeros(shape, dtype=np.float32)
    reference[2, 2] = 1
    ref_path = save_tif(tmp_path / "reference.tif", reference)
    entry = {"id": "reference", "file": "reference.tif", "cache_path": "reference.tif",
             "sha256": sha256_file(ref_path),
             "footprint_sha256": hashlib.sha256(np.asarray(reference[fp], dtype="<f4").tobytes()).hexdigest()}
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({"scope": "synthetic and deliberately incomplete", "entries": [entry]}))
    surface = np.random.default_rng(7).random(shape).astype(np.float32)
    surface_path = tmp_path / "surface.npy"
    np.save(surface_path, surface)
    return tmp_path, template, registry, surface_path


def test_outside_footprint_policies_are_distinct(scene):
    root, template, _, _ = scene
    official = np.zeros((32, 32), np.float32)
    official[0] = np.nan
    candidate = save_tif(root / "null-outside.tif", official, nodata=np.nan)
    report = validate(candidate, template)
    assert report["format_valid"] and not report["strict_whole_grid_range_and_grid_valid"]
    assert not report["ok_to_submit"]
    whole_grid = save_tif(root / "zero-outside.tif", np.zeros((32, 32), np.float32))
    report = validate(whole_grid, template)
    assert not report["format_valid"] and report["strict_whole_grid_range_and_grid_valid"]
    assert report["portal_acceptance"].startswith("unknown")


def test_inside_masked_nodata_or_nonfinite_fails(scene):
    root, template, _, _ = scene
    for value in (np.nan, np.inf, -np.inf, -9999.0, -0.01, 1.01):
        arr = np.zeros((32, 32), np.float32)
        arr[0] = np.nan
        arr[5, 5] = value
        path = save_tif(root / "invalid.tif", arr, nodata=-9999.0 if value == -9999.0 else np.nan)
        assert not validate(path, template)["format_valid"]
    arr = np.zeros((32, 32), np.float32)
    arr[0] = np.inf
    assert not validate(save_tif(root / "exterior-infinity.tif", arr), template)["format_valid"]


def test_template_or_dtype_invalid_fails(scene):
    root, template, _, _ = scene
    arr = np.zeros((32, 32), np.float32)
    assert not validate(save_tif(root / "int.tif", arr, dtype="uint8"), template)["format_valid"]
    empty = save_tif(root / "empty.tif", np.full((32, 32), np.nan, np.float32), nodata=np.nan)
    result = validate(save_tif(root / "empty-candidate.tif", arr), empty)
    assert not result["format_valid"] and not result["strict_whole_grid_range_and_grid_valid"]
    assert not validate(save_tif(root / "multiband.tif", arr, count=2), template)["format_valid"]


def surface_receipt(scene):
    root, template, registry, surface = scene
    report = audit_uniqueness.audit(surface, template, registry, root=root)
    assert report["stage"] == "surface_before_placement" and report["technical_passed"]
    assert not report["registry_completeness_independently_verified"]
    path = root / "preplacement.json"
    path.write_text(json.dumps(report))
    return path


def test_novelty_uses_exact_euclidean_overlap_and_full_scope(scene):
    root, template, registry, surface = scene
    prior = surface_receipt(scene)
    dots = np.zeros((32, 32), np.float32)
    dots[25, 25] = 1
    path = root / "dots.npy"
    np.save(path, dots)
    final = audit_uniqueness.audit(surface, template, registry, dots_path=path, previous_report=prior, root=root)
    assert final["technical_passed"] and not final["eligible_for_selector"]
    assert final["comparison"]["rows"][0]["candidate_dot_overlap_within_3px"] == 0
    dots[:] = 0
    dots[4, 4] = 1  # sqrt(2² + 2²) < 3 (Manhattan would wrongly miss it)
    np.save(path, dots)
    final = audit_uniqueness.audit(surface, template, registry, dots_path=path, previous_report=prior, root=root)
    assert not final["technical_passed"]
    assert final["comparison"]["rows"][0]["candidate_dot_overlap_within_3px"] == 1


def test_no_empty_scope_undefined_rank_or_mutated_reference(scene):
    root, template, registry, surface = scene
    scope = json.loads(registry.read_text())
    registry.write_text(json.dumps({"entries": []}))
    with pytest.raises(ValueError, match="nonempty"):
        audit_uniqueness.audit(surface, template, registry, root=root)
    registry.write_text(json.dumps(scope))
    np.save(surface, np.zeros((32, 32), np.float32))
    out = audit_uniqueness.audit(surface, template, registry, root=root)
    assert not out["technical_passed"] and out["undefined_full_footprint_ranks"] == ["reference"]
    (root / "reference.tif").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="registry bytes"):
        audit_uniqueness.audit(surface, template, registry, root=root)


def test_final_audit_binds_surface_template_registry_and_footprint(scene):
    root, template, registry, surface = scene
    prior = surface_receipt(scene)
    dots = np.zeros((32, 32), np.float32)
    dots[25, 25] = 1
    path = root / "dots.npy"
    np.save(path, dots)
    other_template = save_tif(root / "other-template.tif", np.zeros((32, 32), np.float32))
    with pytest.raises(ValueError, match="mismatched pre-placement"):
        audit_uniqueness.audit(surface, other_template, registry, dots_path=path, previous_report=prior, root=root)
    dots[0, 10] = 1
    np.save(path, dots)
    with pytest.raises(ValueError, match="outside the footprint"):
        audit_uniqueness.audit(surface, template, registry, dots_path=path, previous_report=prior, root=root)
    np.save(surface, np.random.default_rng(8).random((32, 32)))
    with pytest.raises(ValueError, match="mismatched pre-placement"):
        audit_uniqueness.audit(surface, template, registry, dots_path=path, previous_report=prior, root=root)


def test_writer_stops_before_output_when_registry_incomplete(scene, monkeypatch):
    root, template, registry, surface = scene
    prior = surface_receipt(scene)
    dots = np.zeros((32, 32), np.float32)
    dots[25, 25] = 1
    path = root / "dots.npy"
    np.save(path, dots)
    real_audit = audit_uniqueness.audit
    monkeypatch.setattr(submission_writer, "ROOT", root)
    monkeypatch.setattr(submission_writer, "audit", lambda *args, **kwargs: real_audit(*args, **kwargs, root=root))
    out = root / ".cache/candidate-exports"
    with pytest.raises(ValueError, match="Full registry coverage is unverified"):
        submission_writer.write_research(surface=surface, dots=path, template=template, registry=registry,
                                         preplacement=prior, slug="fixture", note="synthetic", output_dir=out)
    assert not list(root.rglob("*RESEARCH-ONLY.tif"))


def test_writer_can_only_emit_negative_research_fixture_with_verified_stub(scene, monkeypatch):
    root, template, registry, surface = scene
    prior = surface_receipt(scene)
    dots = np.zeros((32, 32), np.float32)
    dots[25, 25] = 1
    path = root / "dots.npy"
    np.save(path, dots)
    real_audit = audit_uniqueness.audit
    def verified_stub(*args, **kwargs):
        result = real_audit(*args, **kwargs, root=root)
        result["registry_completeness_independently_verified"] = True  # synthetic test stub ONLY
        return result
    monkeypatch.setattr(submission_writer, "ROOT", root)
    monkeypatch.setattr(submission_writer, "audit", verified_stub)
    out = root / ".cache/candidate-exports"
    receipt = submission_writer.write_research(surface=surface, dots=path, template=template, registry=registry,
                                                preplacement=prior, slug="fixture", note="synthetic", output_dir=out)
    assert receipt["verdict"] == "negative" and not receipt["ok_to_submit"]
    assert receipt["format"]["format_valid"] and "RESEARCH-ONLY" in receipt["file"]
    with pytest.raises(FileExistsError):
        submission_writer.write_research(surface=surface, dots=path, template=template, registry=registry,
                                         preplacement=prior, slug="fixture", note="synthetic", output_dir=out)
