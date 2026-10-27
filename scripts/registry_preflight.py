#!/usr/bin/env python3
"""Audit a literal-registry witness; a non-stop is not a uniqueness pass."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems.preflight import LATTICE_NAME, measure_candidate, pinned_witness  # noqa: E402


def run(template: Path, lattice: Path, budget: int, candidates: list[Path]) -> dict:
    result, fp, halo = pinned_witness(template, lattice, ROOT / "registry/comparison_registry.json", budget)
    result["generated_utc"] = datetime.now(timezone.utc).isoformat()
    result["artifact_checks"] = [measure_candidate(p, template, fp, halo) for p in candidates]
    result["experiments_run"] = 0
    result["portal_slots_used"] = 0
    return result


def main() -> int:
    data = Path(os.environ.get("GEMS_DATA_DIR", ROOT / "data"))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, default=data / "sample_submission.tif")
    parser.add_argument("--lattice", type=Path, default=data / "scored" / LATTICE_NAME)
    parser.add_argument("--budget", type=int, default=37654)
    parser.add_argument("--candidate", type=Path, action="append", default=[])
    parser.add_argument("--out", type=Path)
    parser.add_argument("--expect-stop", action="store_true", help="exit successfully only if a forced stop is proven")
    args = parser.parse_args()
    try:
        result = run(args.template, args.lattice, args.budget, args.candidate)
    except (OSError, ValueError, KeyError) as exc:
        result = {"status": "BLOCKED_INPUTS", "reason": str(exc), "duplicate_forced": None}
    text = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    if args.expect_stop:
        return 0 if result.get("duplicate_forced") is True else 1
    return 0 if result.get("duplicate_forced") is False else 2


if __name__ == "__main__":
    raise SystemExit(main())
