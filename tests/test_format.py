from pathlib import Path
import sys

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import check_format
from lattice_feasibility import sha256


def write_tif(path, arr, *, nodata=np.nan):
    with rasterio.open(path, 'w', driver='GTiff', height=arr.shape[0], width=arr.shape[1],
                       count=1, dtype='float32', crs='EPSG:32611',
                       transform=from_origin(243350, 4508550, 100, 100), nodata=nodata) as ds:
        ds.write(arr.astype('float32'), 1)


@pytest.fixture
def files(tmp_path, monkeypatch):
    shared = tmp_path / 'shared'
    validator = shared / 'scripts/validate_submission.py'
    validator.parent.mkdir(parents=True)
    # Stub only the unchanged shared validator's result; local supplemental
    # mask/range checks and byte binding still use real Rasterio files.
    validator.write_text('''import hashlib,json,sys\np=sys.argv[sys.argv.index("--submission")+1]\nprint(json.dumps({"pass":True,"sha256":hashlib.sha256(open(p,"rb").read()).hexdigest()}))\n''')
    monkeypatch.setattr(check_format, 'SHARED_VALIDATOR_SHA', sha256(validator))
    template = tmp_path / 'template.tif'
    values = np.zeros((3, 3), dtype='float32')
    values[0, 0] = np.nan
    write_tif(template, values)
    return shared, template, tmp_path


def run(files, arr, *, nodata=np.nan):
    shared, template, tmp = files
    candidate = tmp / 'candidate.tif'
    write_tif(candidate, arr, nodata=nodata)
    return check_format.inspect(candidate, template, shared, verify_template_pin=False)


def test_valid_format_is_never_slot_approval(files):
    a = np.zeros((3, 3), dtype='float32'); a[0, 0] = np.nan; a[1, 1] = 0.9
    result = run(files, a)
    assert result['local_format_pass'] is True
    assert result['ok_to_submit'] is False
    assert result['weekly_slot_approved'] is False
    assert result['scientific_and_registry_gates_checked'] is False


@pytest.mark.parametrize('bad', [-0.01, 1.01, float('inf'), float('nan')])
def test_bad_inside_is_rejected(files, bad):
    a = np.zeros((3, 3), dtype='float32'); a[0, 0] = np.nan; a[1, 1] = bad
    assert run(files, a)['local_format_pass'] is False


def test_zero_outside_does_not_silently_become_sample_null(files):
    result = run(files, np.zeros((3, 3), dtype='float32'), nodata=None)
    assert result['whole_array_finite'] is True
    assert result['matches_sample_null_mask_outside'] is False
    assert result['local_format_pass'] is False


def test_nodata_zero_inside_is_rejected_even_when_numeric_values_are_in_range(files):
    result = run(files, np.zeros((3, 3), dtype='float32'), nodata=0)
    assert result['inside_masked_count'] > 0
    assert result['inside_out_of_range_count'] == 0
    assert result['local_format_pass'] is False


def test_mutated_shared_validator_fails_closed(files):
    shared, template, tmp = files
    candidate = tmp / 'candidate.tif'
    arr = np.zeros((3, 3), dtype='float32'); arr[0, 0] = np.nan
    write_tif(candidate, arr)
    (shared / 'scripts/validate_submission.py').write_text('print("tampered")')
    with pytest.raises(ValueError, match='missing or modified'):
        check_format.inspect(candidate, template, shared, verify_template_pin=False)


def test_external_gdal_mask_cannot_make_single_tif_appear_valid(files):
    shared, template, tmp = files
    candidate = tmp / 'candidate.tif'
    write_tif(candidate, np.zeros((3, 3), dtype='float32'), nodata=None)
    mask = np.full((3, 3), 255, dtype='uint8'); mask[0, 0] = 0
    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=False):
        with rasterio.open(candidate, 'r+') as ds:
            ds.write_mask(mask)
    result = check_format.inspect(candidate, template, shared, verify_template_pin=False)
    assert result['matches_sample_null_mask_outside'] is True
    assert result['candidate_external_dependencies']
    assert result['local_format_pass'] is False
    assert result['ok_to_submit'] is False


def test_template_external_sidecar_also_fails_closed(files):
    shared, template, tmp = files
    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=False):
        with rasterio.open(template, 'r+') as ds:
            ds.write_mask(np.full((3, 3), 255, dtype='uint8'))
    candidate = tmp / 'candidate.tif'
    values = np.zeros((3, 3), dtype='float32'); values[0, 0] = np.nan
    write_tif(candidate, values)
    result = check_format.inspect(candidate, template, shared, verify_template_pin=False)
    assert result['template_external_dependencies']
    assert result['local_format_pass'] is False
