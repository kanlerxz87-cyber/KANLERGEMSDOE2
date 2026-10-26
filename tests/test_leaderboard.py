import pytest
from scripts.update_leaderboard import parse

HTML = '''<html><table><tr><th>Rank</th><th>Team members</th><th>Participant</th><th>Best<br>public<br>DW-Tversky</th><th>Shared work</th></tr>
<tr><td>#1</td><td></td><td><a>xiaofanhu</a><br>18h 23min ago <span>⸱</span> 31 submissions</td><td>0.4437</td><td></td></tr>
<tr><td>#2</td><td></td><td>second</td><td>0.3916</td><td></td></tr></table></html>'''

def test_parse_official_shaped_table():
    assert parse(HTML) == {"rank": 1, "participant": "xiaofanhu", "score": 0.4437}

def test_reject_login_page():
    with pytest.raises(ValueError): parse('<h1>Login</h1>')

def test_reject_nonfinite_or_wrong_score():
    with pytest.raises(ValueError): parse(HTML.replace('0.4437','NaN'))
    with pytest.raises(ValueError): parse(HTML.replace('0.4437','1.2'))

def test_reject_missing_and_duplicate_rank_one():
    with pytest.raises(ValueError): parse(HTML.replace('#1','#3'))
    with pytest.raises(ValueError): parse(HTML.replace('#2','#1'))


def test_does_not_parse_unrelated_ranked_table():
    with pytest.raises(ValueError):
        parse(HTML.replace('public<br>DW-Tversky', 'private<br>Other metric'))


def test_preserves_team_name_with_spaces():
    assert parse(HTML.replace('xiaofanhu', 'A Scientific Team'))['participant'] == 'A Scientific Team'


def test_failed_refresh_preserves_dated_snapshot(tmp_path, monkeypatch):
    import sys
    from scripts import update_leaderboard as updater
    out = tmp_path / 'snapshot.json'
    before = '{"observed_utc":"2026-10-26T21:37:00Z","score":0.4437}\n'
    out.write_text(before)
    def fail(_):
        raise ValueError('simulated network or format failure')
    monkeypatch.setattr(updater, 'refresh', fail)
    monkeypatch.setattr(sys, 'argv', ['update_leaderboard.py', '--out', str(out), '--allow-stale'])
    assert updater.main() == 0
    assert out.read_text() == before
