#!/usr/bin/env python3
"""Compatibility entry point for the shared, fail-closed submission validator.

The historical Session-2 validator exempted the lattice and trusted claimed
holdouts. Its champion/unique-slot modes must never authorize an upload. Both
modes now run exactly the same literal-witness screen as validate_submission.py.
Historical receipts are evidence of a superseded calculation, not permission.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from validate_submission import validate_all_gates as shared_validate_all_gates

ROOT = Path(__file__).resolve().parents[1]


def validate_all_gates(tif_path: Path, run_card_path: Path, ddir: Path | None = None,
                       mode: str = "champion") -> dict:
    if mode not in ("champion", "unique-slot"):
        raise ValueError("Unknown legacy mode")
    result = shared_validate_all_gates(tif_path, run_card_path, ddir)
    result["legacy_requested_mode"] = mode
    result["legacy_mode_ignored"] = True
    result["reasons"].append(
        "Legacy control-separated/unique-slot policies are superseded; the literal all-raster rule applies."
    )
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tif", type=Path, required=True)
    ap.add_argument("--run-card", type=Path, default=ROOT / "evidence/run_card.json")
    ap.add_argument("--data-dir", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--mode", choices=["champion", "unique-slot"], default="champion")
    args = ap.parse_args(argv)
    result = validate_all_gates(args.tif, args.run_card, args.data_dir, args.mode)
    text = json.dumps(result, indent=2, allow_nan=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result["ok_to_submit"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
