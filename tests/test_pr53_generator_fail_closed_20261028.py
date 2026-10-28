from __future__ import annotations

from pathlib import Path
from runpy import run_path

ROOT = Path(__file__).resolve().parents[1]


def test_concurrent_pr53_generator_keeps_frozen_budget_and_stops_at_lattice() -> None:
    module = run_path(str(ROOT / "scripts/generate_unique_submission_tif.py"), run_name="_archived_pr53_generator")
    assert module["DOT_BUDGET"] == 37_654
    forced_overlap = module["lattice_forced_overlap"](37_654, 6_649)
    assert forced_overlap == (37_654 - 6_649) / 37_654
    assert forced_overlap > 0.70


def test_concurrent_pr53_renderer_is_disabled() -> None:
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_executive_summary.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
    assert "Disabled" in proc.stderr
    assert "frozen 37,654-dot lattice stop" in proc.stderr
