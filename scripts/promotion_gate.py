"""Fail-closed schema gate. It cannot authenticate a card or authorize a slot."""
import math


def _object(value):
    return value if isinstance(value, dict) else {}


def _number(value, lo, hi):
    return type(value) in (int, float) and math.isfinite(value) and lo <= value <= hi


def check(card):
    card = _object(card)
    errors = []
    if not isinstance(card.get('lane'), str) or not card['lane'].strip():
        errors.append('Missing assigned method lane')
    if card.get('registry_complete') is not True:
        errors.append('Registry coverage unverified')
    for stage in ('surface', 'dots'):
        values = _object(card.get(stage))
        for name, limit in [('max_abs_rank_correlation', .90), ('max_overlap_3px', .70)]:
            if not _number(values.get(name), 0, limit):
                errors.append(f'{stage}.{name}: missing, invalid, or duplicate')
    if not _number(card.get('max_feature_alone_auc'), .50, .90):
        errors.append('Leakage canary absent, not polarity-normalized, or failed')
    h = _object(card.get('holdout'))
    count = h.get('withheld_positives')
    if h.get('label') != 'HOLDOUT-DTI' or not isinstance(h.get('evaluator_version'), str) or not h['evaluator_version'].strip() or type(count) is not int or count <= 0:
        errors.append('Missing versioned holdout evidence')
    score, interval = h.get('dti'), h.get('ci95')
    if not _number(score, 0, 1):
        errors.append('Missing or invalid HOLDOUT-DTI')
    if not isinstance(interval, list) or len(interval) != 2 or not all(_number(v, 0, 1) for v in interval) or interval[0] > interval[1] or (_number(score, 0, 1) and not interval[0] <= score <= interval[1]):
        errors.append('Missing or invalid holdout 95% CI')
    if h.get('fold_local_features') is not True or not isinstance(h.get('baseline_id'), str) or not h['baseline_id'].strip():
        errors.append('Missing fold-local feature evidence or baseline identity')
    ci = h.get('paired_improvement_ci95')
    if not isinstance(ci, list) or len(ci) != 2 or not all(_number(v, -1, 1) for v in ci) or not 0 < ci[0] <= ci[1]:
        errors.append('No positive paired 95% CI against current holdout best')
    validator = _object(card.get('validator'))
    for key in ('no_nan_inside_footprint', 'range_0_1', 'crs_match', 'shape_match', 'transform_match', 'single_band', 'dtype_float32',
                'unmasked_inside_footprint', 'no_external_dependencies', 'candidate_unchanged_during_audit', 'template_unchanged_during_audit'):
        if validator.get(key) is not True:
            errors.append('Validator missing/failed: ' + key)
    sha = card.get('raster_sha256', '')
    if not isinstance(sha, str) or len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
        errors.append('Missing raster SHA256')
    name, note = card.get('submission_name'), card.get('note')
    if not isinstance(name, str) or not name.strip() or not isinstance(note, str) or not note.strip() or len(note) > 140:
        errors.append('Invalid name/note')
    return {'verdict': 'negative' if errors else 'promote', 'eligible_for_selector': not errors,
            'authorized_to_submit': False, 'errors': errors,
            'scope': 'Schema/declared values only; caller must authenticate evidence and run registry guard.'}
