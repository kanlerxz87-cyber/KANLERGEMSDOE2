#!/usr/bin/env python3
"""Exercise the unmodified, hash-pinned shared evaluator on synthetic inputs only."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from lattice_feasibility import sha256

PINS = {
    'evaluate_holdout.py': '51dd3aa1315b5fd195c2c5301b6bd65826d07390372eae991408367b92fcb099',
    'src/gems33/__init__.py': 'e63b4d4ce4ba3f605e6a9d27de87623aac2fa94b9e05729d6ac75a752f73e04f',
    'src/gems33/grid.py': '7ad984dbfd894b609af56bc0e2c1b7d6c31a3239a9980d217a9b855455bc4463',
    'src/gems33/metric.py': '575524d5c9357cdd22a43301a4dfe847fdd6506f48761b8713ce51057b4cdcfe',
}


def reproduce(shared: Path) -> dict:
    shared = shared.resolve()
    for name, expected in PINS.items():
        path = shared / name
        if not path.is_file() or sha256(path) != expected:
            raise ValueError(f'pinned shared input missing or modified: {name}')

    # Import the shared code as-is; this is a reproducer, not an evaluator fork.
    module_name = 'pinned_shared_evaluator_synthetic_reproduction'
    spec = importlib.util.spec_from_file_location(module_name, shared / 'evaluate_holdout.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    footprint = np.ones((5, 5), dtype=bool)
    catalogue = np.zeros((5, 5), dtype=bool)
    catalogue[0, 0] = catalogue[0, 4] = catalogue[4, 0] = catalogue[4, 4] = True
    empty = module.leakage_canary_auc(np.zeros((5, 5)), [])
    folds = module.build_hide_and_recover_folds(catalogue, footprint, system_buffer_px=0, collar_px=4, n_folds=4)
    fold_counts = [{'withheld': int(f.withheld_pos.sum()), 'visible': int(f.visible_faults.sum()),
                    'known_for_scoring': int(f.known_mask_for_scoring.sum())} for f in folds]
    with tempfile.TemporaryDirectory() as temp:
        missing = Path(temp) / 'missing_registry.tif'
        dots = np.zeros((5, 5), bool); dots[2, 2] = True
        screening = module.screen_against_registry(np.arange(25).reshape(5, 5), dots, footprint,
                                                    {'missing': missing})
    flags = {
        'empty_canary_returns_unflagged_half_auc': empty.get('canary_auc') == 0.5
            and empty.get('leakage_flag') is False and not empty.get('fold_aucs'),
        'collar_removed_faults_still_masked': any(row['visible'] == 0 and row['known_for_scoring'] > 0
                                                   for row in fold_counts),
        'missing_registry_silently_skipped': screening['n_registry_rasters_checked'] == 0
            and screening['duplicate_triggered'] is False,
    }
    if not all(flags.values()):
        raise RuntimeError('the pinned evaluator did not reproduce every recorded defect')
    return {
        'checked_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'synthetic evaluator regression only; not a feature canary, holdout, candidate or slot approval',
        'shared_commit': '1d99d73fe14d9a87126ffca2db52c69336d6099b',
        'evaluator_version': module.EVALUATOR_VERSION,
        'input_sha256': PINS,
        'empty_fold_canary_output': empty,
        'synthetic_fold_counts': fold_counts,
        'missing_registry_expected': 1,
        'missing_registry_checked': screening['n_registry_rasters_checked'],
        'missing_registry_duplicate_triggered': screening['duplicate_triggered'],
        'defects_reproduced': flags,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--shared', type=Path, default=Path('.cache/GEMSDOE33'))
    p.add_argument('--out', type=Path)
    args = p.parse_args()
    result = reproduce(args.shared)
    text = json.dumps(result, indent=2, allow_nan=False) + '\n'
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
