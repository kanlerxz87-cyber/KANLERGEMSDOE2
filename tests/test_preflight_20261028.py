"""Reporting regressions: old proxies must not become new score claims."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_preflight_evidence_count_and_card():
    r = json.loads((ROOT / 'evidence/preflight_replay_20261028.json').read_text())
    p = r['preflight']
    assert p['candidate_dot_budget'] - p['uncovered_pixels'] == p['minimum_overlapping_dots']
    assert p['minimum_overlapping_dots'] / p['candidate_dot_budget'] == p['minimum_directional_overlap']
    assert p['minimum_directional_overlap'] > p['limit'] and p['forced_duplicate']
    assert len(r['focus_nine']) == 9 and all(x['duplicate_vs_focus'] for x in r['focus_nine'])
    assert r['forensics']['g25_g30_positive_mask_xor'] == 0
    assert r['forensics']['g32_vs_g25_with_gt_2px_catalogue_collar_xor'] == 0
    c = json.loads((ROOT / 'evidence/run_card_20261028_preflight.json').read_text())
    assert c['verdict'] == 'negative' and not c['ok_to_submit']
    assert c['raster_sha256'] is c['holdout_dti'] is c['submission_name'] is None
    assert len(c['note']) <= 140


def test_public_page_does_not_treat_projections_as_scores():
    for name in ('index.html', 'executive-summary.html', 'research.html', 'irregularities.html'):
        page = (ROOT / 'docs' / name).read_text()
        assert 'DO NOT SUBMIT' in page
        assert 'not HOLDOUT-DTI or leaderboard estimates' in page
        assert 'pure-false-positive dots' not in page
        assert 'beat 0.2778 across ALL THREE blind holdouts' not in page
    feed = json.loads((ROOT / 'docs/data/status_feed.json').read_text())['kg2s3_hptr_lane']
    assert feed['beats_02778_leaderboard_score'] is None
    assert 'sgmc_cal_v3_dti' not in feed

    trbvc = json.loads((ROOT / 'docs/data/status_feed.json').read_text())['kg2s3_trbvc_lane']
    assert 'sgmc_cal_v3_dti' not in trbvc
    assert 'hide_recover_v3_dti' not in trbvc
