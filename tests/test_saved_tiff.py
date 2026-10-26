import numpy as np
import rasterio
from rasterio.transform import from_origin
from scripts.validate_saved_tiff import audit


def write(path, a, *, transform=None, dtype='float32'):
    with rasterio.open(path, 'w', driver='GTiff', height=a.shape[0], width=a.shape[1], count=1,
                       dtype=dtype, crs='EPSG:32611', transform=transform or from_origin(500, 1000, 100, 100)) as dst:
        dst.write(a.astype(dtype), 1)
    return path


def files(tmp_path, values, *, dtype='float32', transform=None):
    footprint = np.array([[0, 1, 0], [0, np.nan, np.nan]], dtype='float32')
    template = write(tmp_path / 'template.tif', footprint)
    candidate = write(tmp_path / 'candidate.tif', np.array(values), transform=transform, dtype=dtype)
    return candidate, template


def test_nan_outside_valid_but_never_authorized(tmp_path):
    c, t = files(tmp_path, [[0, 1, 0.5], [0, np.nan, np.nan]])
    r = audit(c, t, 'nan')
    assert r['local_format_pass'] and not r['whole_array_finite']
    assert r['portal_acceptance'] is None and r['ok_to_submit'] is False
    assert len(r['sha256']) == 64


def test_zero_outside_valid_only_as_local_profile(tmp_path):
    c, t = files(tmp_path, [[0, 1, .1], [0, 0, 0]])
    r = audit(c, t, 'zero')
    assert r['local_format_pass'] and r['whole_array_finite']
    assert not audit(c, t, 'nan')['local_format_pass']


def test_invalid_inside_and_outside_are_not_silently_clipped(tmp_path):
    c, t = files(tmp_path, [[0, 1.01, np.nan], [-0.1, 0, np.inf]])
    r = audit(c, t, 'zero')
    assert not r['local_format_pass']
    assert not r['checks']['finite_inside_footprint']
    assert not r['checks']['zero_outside']
    assert not r['checks']['whole_array_finite_in_0_1']


def test_grid_and_dtype_must_match(tmp_path):
    c, t = files(tmp_path, [[0, 1, 0], [0, 0, 0]], dtype='float64',
                 transform=from_origin(501, 1000, 100, 100))
    r = audit(c, t, 'zero')
    assert not r['checks']['float32']
    assert not r['checks']['matching_crs_shape_transform']
    assert not r['local_format_pass']


def test_template_must_expose_nonfinite_exterior(tmp_path):
    c, t = files(tmp_path, [[0, 1, 0], [0, 0, 0]])
    write(t, np.zeros((2, 3), dtype='float32'))
    import pytest
    with pytest.raises(ValueError, match='finite interior'):
        audit(c, t, 'zero')


def test_wrong_crs_and_multiple_bands_fail(tmp_path):
    c, t = files(tmp_path, [[0, 1, 0], [0, 0, 0]])
    a = np.zeros((2, 3), dtype='float32')
    with rasterio.open(c, 'w', driver='GTiff', height=2, width=3, count=2,
                       dtype='float32', crs='EPSG:4326', transform=from_origin(500, 1000, 100, 100)) as dst:
        dst.write(a, 1)
        dst.write(a, 2)
    r = audit(c, t, 'zero')
    assert not r['checks']['single_band']
    assert not r['checks']['epsg_32611']
    assert not r['checks']['matching_crs_shape_transform']
    assert not r['local_format_pass']


def test_finite_nodata_sentinel_cannot_mask_interior(tmp_path):
    from scripts.validate_raster import validate
    c, t = files(tmp_path, [[0, 0, 0], [0, 0, 0]])
    values = np.zeros((2, 3), dtype='float32')
    with rasterio.open(c, 'w', driver='GTiff', height=2, width=3, count=1,
                       dtype='float32', crs='EPSG:32611', nodata=0,
                       transform=from_origin(500, 1000, 100, 100)) as dst:
        dst.write(values, 1)
    for result in (audit(c, t, 'zero'), validate(c, t)):
        assert result['inside_masked_count'] == 4
        assert not result['checks']['unmasked_inside_footprint']
        assert not result.get('local_format_pass', result.get('format_valid'))
        assert not result['ok_to_submit']


def test_external_mask_sidecars_cannot_be_part_of_a_single_tiff(tmp_path):
    from scripts.validate_raster import validate
    c, t = files(tmp_path, [[0, 1, 0], [0, 0, 0]])
    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=False):
        with rasterio.open(c, 'r+') as dst:
            dst.write_mask(np.full((2, 3), 255, dtype='uint8'))
    for result in (audit(c, t, 'zero'), validate(c, t)):
        assert result['candidate_external_dependencies']
        assert not result['checks']['no_external_candidate_dependencies']
        assert not result.get('local_format_pass', result.get('format_valid'))


def test_template_external_mask_is_not_part_of_the_hashed_tiff(tmp_path):
    from scripts.validate_raster import validate
    c, t = files(tmp_path, [[0, 1, 0], [0, 0, 0]])
    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=False):
        with rasterio.open(t, 'r+') as dst:
            dst.write_mask(np.full((2, 3), 255, dtype='uint8'))
    for result in (audit(c, t, 'zero'), validate(c, t)):
        assert result['template_external_dependencies']
        assert not result['checks']['no_external_template_dependencies']
        assert not result.get('local_format_pass', result.get('format_valid'))


def test_internal_masked_pixel_rejected(tmp_path):
    from scripts.validate_raster import validate
    c, t = files(tmp_path, [[0, 1, 0], [0, 0, 0]])
    mask = np.full((2, 3), 255, dtype='uint8'); mask[0, 1] = 0
    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):
        with rasterio.open(c, 'r+') as dst:
            dst.write_mask(mask)
    for result in (audit(c, t, 'zero'), validate(c, t)):
        assert result['inside_masked_count'] == 1
        assert not result.get('local_format_pass', result.get('format_valid'))


def test_template_masked_finite_pixels_do_not_define_a_safe_footprint(tmp_path):
    import pytest
    from scripts.validate_raster import validate
    c, t = files(tmp_path, [[0, 1, 0], [0, 0, 0]])
    # A finite nodata sentinel makes this template ambiguous, even if its raw
    # bytes otherwise look like valid predictions.
    with rasterio.open(t, 'r+') as dst:
        dst.nodata = 0
    with pytest.raises(ValueError, match='footprint is ambiguous'):
        audit(c, t, 'zero')
    result = validate(c, t)
    assert not result['checks']['template_footprint_unambiguous']
    assert not result['format_valid']


def test_changed_file_hash_during_audit_fails_closed(tmp_path, monkeypatch):
    import scripts.validate_saved_tiff as strict
    import scripts.validate_raster as whole_grid
    c, t = files(tmp_path, [[0, 1, 0], [0, 0, 0]])
    for module, func, name in ((strict, lambda: strict.audit(c, t, 'zero'), 'sha256'),
                               (whole_grid, lambda: whole_grid.validate(c, t), 'digest')):
        real = getattr(module, name)
        calls = {}
        def changing_digest(path, *, _real=real):
            key = str(path)
            calls[key] = calls.get(key, 0) + 1
            return _real(path) if key != str(c) or calls[key] == 1 else 'changed'
        with monkeypatch.context() as patch:
            patch.setattr(module, name, changing_digest)
            result = func()
        assert not result['checks']['candidate_unchanged_during_audit']
        assert not result.get('local_format_pass', result.get('format_valid'))
