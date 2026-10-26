"""A single-file upload must not rely on external GDAL masks or sidecars."""
import numpy as np
import rasterio
from rasterio.transform import from_origin

import validate_raster
from validate_raster import validate


def save(path, array):
    with rasterio.open(path, "w", driver="GTiff", height=array.shape[0], width=array.shape[1], count=1,
                       dtype="float32", crs="EPSG:32611", transform=from_origin(0, 300, 100, 100)) as ds:
        ds.write(array.astype("float32"), 1)


def external_mask(path, mask):
    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=False):
        with rasterio.open(path, "r+") as ds:
            ds.write_mask(mask)


def test_candidate_external_mask_fails_closed(tmp_path):
    template = tmp_path / "template.tif"
    values = np.zeros((3, 3), np.float32); values[0, 0] = np.nan
    save(template, values)
    candidate = tmp_path / "candidate.tif"; save(candidate, np.zeros_like(values))
    mask = np.full((3, 3), 255, np.uint8); mask[0, 0] = 0
    external_mask(candidate, mask)
    report = validate(candidate, template)
    assert report["checks"]["outside_footprint_null_or_nan"]
    assert report["candidate_external_dependencies"] and not report["format_valid"]
    assert not report["ok_to_submit"]


def test_template_external_mask_fails_closed(tmp_path):
    template = tmp_path / "template.tif"; save(template, np.zeros((3, 3), np.float32))
    candidate = tmp_path / "candidate.tif"; save(candidate, np.zeros((3, 3), np.float32))
    external_mask(template, np.full((3, 3), 255, np.uint8))
    report = validate(candidate, template)
    assert report["template_external_dependencies"] and not report["format_valid"]


def test_masked_finite_template_is_ambiguous(tmp_path):
    template = tmp_path / 'template.tif'
    with rasterio.open(template, 'w', driver='GTiff', height=3, width=3, count=1,
                       dtype='float32', crs='EPSG:32611', transform=from_origin(0, 300, 100, 100), nodata=-9999) as ds:
        arr = np.zeros((3, 3), np.float32); arr[0, 0] = -9999
        ds.write(arr, 1)
    candidate = tmp_path / 'candidate.tif'; save(candidate, np.zeros((3, 3), np.float32))
    report = validate(candidate, template)
    assert not report['checks']['template_footprint_unambiguous'] and not report['format_valid']


def test_changed_candidate_during_validation_fails_closed(tmp_path, monkeypatch):
    template = tmp_path / 'template.tif'; save(template, np.zeros((3, 3), np.float32))
    candidate = tmp_path / 'candidate.tif'; save(candidate, np.zeros((3, 3), np.float32))
    real_hash = validate_raster.sha256_file
    counts = {}
    def changing_hash(path):
        path = str(path); counts[path] = counts.get(path, 0) + 1
        result = real_hash(path)
        return ('f' * 64) if path == str(candidate) and counts[path] > 1 else result
    monkeypatch.setattr(validate_raster, 'sha256_file', changing_hash)
    report = validate(candidate, template)
    assert not report['checks']['candidate_unchanged_during_audit'] and not report['format_valid']
