#!/usr/bin/env python3
"""Pretraining diagnostics using the pinned template, not a detector experiment.

Tests raw physical cache channels only. No catalogue distance, labels, sample
values, SGMC faults or historic submission enters the feature dictionary.
Missing data use a fixed zero sentinel; separate validity masks are also tested.
No canary pass proves feature independence or authorizes model training.
"""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor/template/src'))
from gems.holdout import SegmentHoldout, MTR_EVALUATOR_VERSION
from restore_core_data import digest
from prepare_data import inspect

FILES = ['training_features.tif', 'external/geodawn_rad_u8.tif',
         'external/geodawn_extensions_u8.tif', 'external/lidar_scarp_features_u8.tif']


def mask_hash(a):
    return hashlib.sha256(np.packbits(a).tobytes()).hexdigest()


def main():
    data = ROOT / 'data'
    if not inspect(data)['ready']:
        raise SystemExit('Run verified data preparation first')
    with rasterio.open(data / 'sample_submission.tif') as src:
        footprint = np.isfinite(src.read(1)) & (src.read_masks(1) > 0)
    with rasterio.open(data / 'existing_faults.tif') as src:
        truth = (src.read(1) > 0) & footprint & (src.read_masks(1) > 0)
    context = SegmentHoldout(footprint, truth, buffer_px=15)
    fold_manifest = {'evaluator_version': MTR_EVALUATOR_VERSION, 'buffer_px': 15,
                     'mask_hash_encoding': 'SHA256 of C-order np.packbits bool raster; shape specified below',
                     'shape': list(footprint.shape), 'folds': [],
                     'template_pins_sha256': digest(ROOT / 'vendor/template/pins.json'),
                     'input_sha256': {name: digest(data / name) for name in ['sample_submission.tif', 'existing_faults.tif']},
                     'frozen_best_available': False, 'hypothesis_experiments_used': 0}
    cache = ROOT / '.cache/segment-folds'
    cache.mkdir(parents=True, exist_ok=True)
    for fold in context.folds:
        arrays = {k: fold[k] for k in ['valid', 'train', 'visible', 'truth']}
        np.savez_compressed(cache / f"fold-{fold['id']}.npz", **arrays)
        fold_manifest['folds'].append({'id': fold['id'], 'name': fold['name'],
            'n_withheld_positives': int(fold['truth'].sum()),
            'hidden_component_count': int(len(fold['hidden_component_ids'])),
            'n_training_pixels': int(fold['train'].sum()),
            'masks': {k: mask_hash(v) for k, v in arrays.items()}})
    (ROOT / 'evidence/segment_folds.json').write_text(json.dumps(fold_manifest, indent=2) + '\n')
    result = {'diagnostic': 'LEAKAGE-CANARY AUC, not HOLDOUT-DTI or organizer score',
              'evaluator_version': MTR_EVALUATOR_VERSION, 'feature_groups': [],
              'limitations': ['Raw channels only; all future transforms and fold-local features need their own canaries.',
                             'Low AUC does not establish absence of leakage, official origin, or useful fault prediction.',
                             'This context freezes masks, not a comparable current-best model.',
                             'A fixed zero sentinel and validity mask reveal missingness sensitivity; no learned imputation.'],
              'hypothesis_experiments_used': 0, 'authorized_to_submit': False}
    for name in FILES:
        features = {}
        with rasterio.open(data / name) as src:
            for band, description in enumerate(src.descriptions, start=1):
                a = src.read(band, masked=True)
                valid = ~np.ma.getmaskarray(a) & np.isfinite(a.data) & footprint
                feature = f'{band}:{description or "unnamed"}'
                features[feature] = np.where(valid, a.data, 0).astype(np.float32)
                features[feature + ':validity'] = valid
        report = context.canary(features)
        result['feature_groups'].append({'path': name, 'sha256': digest(data / name), **report})
        del features
        print(name, 'passed=', report['passed'], flush=True)
        # Persist diagnostics even if a later group fails; consumers must check complete.
        result['complete'] = len(result['feature_groups']) == len(FILES)
        result['passed'] = result['complete'] and all(g['passed'] for g in result['feature_groups'])
        (ROOT / 'evidence/raw_feature_canaries.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print('Raw-feature canary audit complete; no model or submission generated', flush=True)


if __name__ == '__main__':
    main()
