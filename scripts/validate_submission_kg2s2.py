#!/usr/bin/env python3
"""Compatibility entry point for the shared, fail-closed submission validator.

The former KG2-S2 validator trusted self-reported gate results and exempted
registered lattice controls.  Neither behavior is authorized.  The historical
``--mode`` option is accepted for script compatibility but cannot relax any
gate; both modes use exactly the same literal-witness screening as
``validate_submission.py``.  Until complete independent replay is implemented,
no mode authorizes an upload.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from validate_submission import ROOT, validate_all_gates as _validate_shared


def validate_all_gates(tif_path: Path, run_card_path: Path, ddir: Path | None = None,
                       mode: str = "champion") -> dict:
    if mode not in {"champion", "unique-slot"}:
        raise ValueError("Unsupported historical validation mode")
    result = _validate_shared(tif_path, run_card_path, ddir)
    result["legacy_mode_ignored"] = mode
    result["reasons"].append(
        "The historical KG2-S2 mode does not exempt any registry raster or confer promotion."
    )
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tif", type=Path, required=True)
    ap.add_argument("--run-card", type=Path, default=ROOT / "evidence/run_card.json")
    ap.add_argument("--data-dir", type=Path, default=None)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--mode", choices=("champion", "unique-slot"), default="champion")
    args = ap.parse_args()
    result = validate_all_gates(args.tif, args.run_card, args.data_dir, args.mode)
    text = json.dumps(result, indent=2, allow_nan=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result["ok_to_submit"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
