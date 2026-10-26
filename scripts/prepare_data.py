#!/usr/bin/env python3
"""Verify pinned mirror placement, grid, band metadata and coverage; never synthesize inputs."""
import argparse
import json
from pathlib import Path
import numpy as np
import rasterio

from restore_core_data import MANIFEST, ROOT, digest, safe_destination, valid_existing

BAND_NAMES = [
    'mag_anom', 'rtp', 'tmi_hg', 'geod_2ndinv', 'iso_grav_anom_slope', 'tc',
    'geod_shearrate', 'geod_dilaterate', 'tmi_vg', 'deq_n100a15', 'iso_grav_anom_vg',
    'det_elev', 'iso_grav_anom', 'tmi', 'depth_to_base_surf', 'ieq_n100a15',
    'cond_surf', 'iso_grav_anom_hg', 'det_elev_slope',
]


def inspect(data_dir):
    manifest = json.loads(MANIFEST.read_text())
    core = [f for f in manifest['files'] if f['group'] == 'core']
    report = {'ready': False, 'training_authorized': False,
              'provenance': 'SHA256-pinned peer mirror, NOT organizer-authenticated.',
              'manifest_sha256': digest(MANIFEST), 'missing': [], 'files': [], 'errors': []}
    for entry in core:
        path = safe_destination(data_dir, entry['dest'])
        if not path.is_file():
            report['missing'].append(entry['dest'])
        elif not valid_existing(path, entry):
            report['errors'].append('Pin mismatch: ' + entry['dest'])
    if report['missing'] or report['errors']:
        return report
    with rasterio.open(data_dir / 'sample_submission.tif') as template:
        sample = template.read(1, masked=True)
        footprint = ~np.ma.getmaskarray(sample) & np.isfinite(sample.data)
        report['footprint_pixels'] = int(footprint.sum())
        if (template.count != 1 or template.dtypes != ('float32',) or template.crs is None
                or template.crs.to_epsg() != 32611 or not footprint.any() or len(template.files) != 1):
            report['errors'].append('Sample must be a self-contained, nonempty, single-band EPSG:32611 float32 grid')
        for entry in manifest['files']:
            if entry['group'] not in ('core', 'external'):
                continue
            path = safe_destination(data_dir, entry['dest'])
            if not path.is_file():
                continue
            record = {'id': entry['id'], 'path': entry['dest'], 'sha256': digest(path),
                      'hash_matches_pin': valid_existing(path, entry)}
            if path.suffix == '.tif':
                with rasterio.open(path) as src:
                    record.update(shape=list(src.shape), crs=str(src.crs), transform=list(src.transform)[:6],
                                  bands=src.count, descriptions=list(src.descriptions), dtypes=list(src.dtypes),
                                  nodata_repr=str(src.nodata), color_interpretations=[c.name for c in src.colorinterp],
                                  mask_flags=[[f.name for f in flags] for flags in src.mask_flag_enums])
                    record['grid_matches'] = src.shape == template.shape and src.crs is not None and src.crs == template.crs and src.transform == template.transform
                    record['valid_inside_footprint_by_band'] = []
                    if record['grid_matches']:
                        for band in range(1, src.count + 1):
                            a = src.read(band, masked=True)
                            valid = ~np.ma.getmaskarray(a) & np.isfinite(a.data)
                            record['valid_inside_footprint_by_band'].append(int((valid & footprint).sum()))
                    else:
                        report['errors'].append('Grid mismatch: ' + entry['dest'])
                    expected = 19 if entry['id'] == 'training_features' else 1 if entry['group'] == 'core' else src.count
                    if src.count != expected:
                        report['errors'].append('Band count mismatch: ' + entry['dest'])
                    if len(src.files) != 1:
                        report['errors'].append('Unexpected external raster sidecar: ' + entry['dest'])
                    if entry['id'] == 'training_features':
                        band_names = [src.tags(i).get('band_name') for i in range(1, src.count + 1)]
                        record['band_names'] = band_names
                        record['band_names_match_expected'] = band_names == BAND_NAMES
                        if band_names != BAND_NAMES or src.dtypes != ('float32',) * len(BAND_NAMES):
                            report['errors'].append('19-band names/order/dtypes do not match the pinned contract')
            if not record['hash_matches_pin']:
                report['errors'].append('Pin mismatch: ' + entry['dest'])
            report['files'].append(record)
    report['labels_are_existing_faults_not_hidden_truth'] = digest(data_dir / 'labels.tif') == digest(data_dir / 'existing_faults.tif')
    with rasterio.open(data_dir / 'labels.tif') as labels:
        label_values = labels.read(1)
        if label_values.shape == footprint.shape:
            report['sample_ones_equal_known_faults'] = bool(np.array_equal((sample.data == 1) & footprint, (label_values > 0) & footprint))
            if np.any((label_values > 0) & ~footprint):
                report['errors'].append('Known-fault positives extend beyond the template footprint')
        else:
            report['errors'].append('Label shape does not match the sample')
    report['ready'] = not report['errors'] and report['footprint_pixels'] > 0
    report['limitations'] = [
        'Data placement is not training authorization: assigned lane, full registry and frozen baseline remain required.',
        'Coverage counts are data-audit measurements, not HOLDOUT-DTI or leaderboard scores.',
        'Sample values must NEVER enter features or serve as independent hidden-fault truth.',
        'Masked/nodata input cells must be handled explicitly in fold-local feature construction.',
        'External provenance and band descriptions are mirror claims, not independent official-source authentication.',
        'Radiometric four-band TIFFs tag their last quantitative channel as alpha; nodata overrides that display flag. Coverage uses rasterio nodata masks, not rendered opacity.',
        'Core band tc has an ambiguous mirror description (tilt angle or total curvature); do not assign a physical meaning without source verification.',
    ]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=ROOT / 'data')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    report = inspect(args.data_dir)
    out = args.out or args.data_dir / 'prepared_manifest.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps(report, indent=2, allow_nan=False))
    raise SystemExit(0 if report['ready'] else 1)


if __name__ == '__main__':
    main()
