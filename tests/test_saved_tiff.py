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
