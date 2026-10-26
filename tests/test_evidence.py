import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / name).read_text())


def test_run_card_does_not_invent_a_candidate_or_holdout():
    card = load('evidence/run-card.json')
    geom = load('evidence/lattice-feasibility-20261026.json')
    assert card['verdict'] == 'negative' and not card['ok_to_submit']
    assert card['raster_sha256'] is None and card['submission_name'] is None
    assert card['holdout_dti']['score'] is None and card['holdout_dti']['ci95'] is None
    assert card['validator_output']['no_nan_inside_footprint'] is None
    assert card['correlation_and_overlap_vs_registry']['minimum_possible_fraction_within_3px_of_pinned_lattice'] == geom['minimum_fraction_inside_halo']
    assert geom['strict_more_than_70_percent_unavoidable']
    assert len(card['note']) <= 140


def test_historical_claims_are_not_scores_or_slot_approvals():
    manifest = load('registry/focus-sites.json')
    audit = load('evidence/focus-audit-20261026.json')
    assert len(manifest['sites']) == len(audit['sites']) == 9
    assert {r['site'] for r in manifest['sites']} == {r['site'] for r in audit['sites']}
    for row in audit['sites']:
        assert row['claim_status'].startswith('unverified owner claim')
        assert row['score_estimate'] is None and row['ok_to_submit'] is False
        assert row['raster_sha256_verified'] == row['sha256']
        assert row['maximum_directed_3px_overlap_with_other_focus_champions'] > 0.70
    lineage = audit['lineage']
    assert lineage['b1_distance_prune_matches_gemsdoe31_exactly']
    assert lineage['b2_distance_prune_matches_gemsdoe32_exactly']
    assert lineage['gemsdoe36_contains_every_b2_dot']


def test_shared_template_defects_are_synthetic_not_holdout_evidence():
    result = load('evidence/template-defects-20261026.json')
    assert all(result['defects_reproduced'].values())
    assert result['missing_registry_expected'] == 1 and result['missing_registry_checked'] == 0
    assert result['missing_registry_duplicate_triggered'] is False
    assert all(row == {'withheld': 1, 'visible': 0, 'known_for_scoring': 3}
               for row in result['synthetic_fold_counts'])
    assert 'not a feature canary, holdout, candidate or slot approval' in result['scope']


def test_defect_reproducer_refuses_unpinned_template(tmp_path):
    import subprocess
    import sys
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/reproduce_template_defects.py'),
                             '--shared', str(tmp_path)], capture_output=True, text=True)
    assert result.returncode != 0
    assert 'pinned shared input missing or modified' in result.stderr


def test_parallel_archived_e1_is_not_promoted():
    result = load('evidence/parallel-e1-lattice-audit-20261026.json')
    assert result['candidate_dots'] == 37654
    assert result['candidate_dots_within_3px'] == 37395
    assert result['actual_directed_fraction_within_3px'] == 37395 / 37654
    assert result['strict_more_than_70_percent'] is True
    assert result['verdict'] == 'duplicate-stop' and result['ok_to_submit'] is False
