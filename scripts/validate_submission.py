#!/usr/bin/env python3
"""Run the shared format and fail-closed selector screens; never upload.

A valid GeoTIFF is not necessarily a unique or worthwhile submission. Historical
cards with detector-only lattice exceptions are NOT authorization certificates.
No account-quota or complete independent replay verifier is currently wired in.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems import selector, submission  # noqa: E402
from gems32.paths import data_dir  # noqa: E402


def validate_all_gates(tif_path: Path, run_card_path: Path, ddir: Path | None = None) -> dict:
    ddir = Path(ddir) if ddir is not None else data_dir()
    template = ddir / "sample_submission.tif"
    if not template.is_file():
        template = ddir / "bridge/sample_submission.tif"
    try:
        card = json.loads(run_card_path.read_text(encoding="utf-8"))
        if not isinstance(card, dict):
            raise ValueError("run card must be a JSON object")
        fmt = submission.check_variants(tif_path, template)
        decision = selector.verify_selector(tif_path, template, card)
        return {
            "validated_ok_to_download_and_submit": decision["ok_to_submit"],
            "human_inspection_used": False,
            "verdict": "promote" if decision["ok_to_submit"] else "negative",
            "raster_filename": tif_path.name,
            "raster_sha256": fmt["sha256"],
            "format_audit": fmt,
            "gates": decision["gates"],
            "reasons": decision["reasons"],
            "selector_version": decision["selector_version"],
            "scope": decision["scope"],
        }
    except (OSError, ValueError, TypeError, KeyError) as exc:
        return {
            "validated_ok_to_download_and_submit": False,
            "human_inspection_used": False,
            "verdict": "negative",
            "raster_filename": tif_path.name,
            "raster_sha256": None,
            "gates": {"validation_completed": False},
            "reasons": [f"validation could not be completed: {type(exc).__name__}: {exc}"],
        }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tif", type=Path, required=True)
    ap.add_argument("--run-card", type=Path, default=ROOT / "run_card.json")
    ap.add_argument("--data-dir", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    result = validate_all_gates(args.tif, args.run_card, args.data_dir)
    text = json.dumps(result, indent=2, allow_nan=False)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result["validated_ok_to_download_and_submit"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
