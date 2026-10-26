"""The three independent negative-status dashboards must survive site builds."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_all_three_dashboards_are_linked():
    root = (ROOT / 'index.html').read_text()
    assert 'docs/index.html' in root
    assert 'docs/h1-audit.html' in root
    assert 'Data audit' in root and 'H1 audit' in root
    assert 'No new TIFF is approved' in (ROOT / 'docs/index.html').read_text()
    assert 'No new TIFF is approved' in (ROOT / 'docs/h1-audit.html').read_text()


def test_data_site_build_does_not_overwrite_h1():
    from scripts.build_site import build
    h1 = ROOT / 'docs/h1-audit.html'
    before = h1.read_bytes()
    build()
    assert h1.read_bytes() == before


def test_scheduled_monitor_does_not_scrape_competition():
    workflow = (ROOT / '.github/workflows/pages.yml').read_text().lower()
    assert 'schedule:' in workflow
    assert 'check_source_freshness.py' in workflow
    assert 'drivendata' not in workflow
    assert 'update_leaderboard' not in workflow
