#!/usr/bin/env python3
"""Compatibility wrapper for the shared fail-closed submission validator.

The former champion/unique-slot modes exempted registered calibration rasters
and trusted self-attested holdout/registry results. Both modes are retired: a
format pass or a historical run card cannot authorize a competition upload.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from validate_submission import ROOT, validate_all_gates as shared_validate


def validate_all_gates(
    tif_path: Path,
    run_card_path: Path,
    ddir: Path | None = None,
    mode: str = "champion",
) -> dict:
    if mode not in {"champion", "unique-slot"}:
        raise ValueError("Unknown legacy validation mode")
    result = shared_validate(tif_path, run_card_path, ddir)
    result["requested_legacy_mode"] = mode
    result["legacy_mode_ignored"] = mode  # compatibility: no mode relaxes the literal gate
    result["legacy_mode_status"] = (
        "Retired: no calibration-raster exemption or self-attested promotion; "
        "all modes use scripts/validate_submission.py."
    )
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tif", type=Path, required=True)
    ap.add_argument("--run-card", type=Path, default=ROOT / "evidence" / "run_card.json")
    ap.add_argument("--data-dir", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--mode", choices=["champion", "unique-slot"], default="champion")
    args = ap.parse_args()
    result = validate_all_gates(args.tif, args.run_card, args.data_dir, args.mode)
    text = json.dumps(result, indent=2, allow_nan=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result["validated_ok_to_download_and_submit"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
