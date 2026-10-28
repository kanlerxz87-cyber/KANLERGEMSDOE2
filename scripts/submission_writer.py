#!/usr/bin/env python3
"""Shared CLI for the existing strict writer; never authorizes a weekly slot."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems import paths  # noqa: E402
from gems.submission import check_variants, write_submission  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("prediction", type=Path, help="2D .npy or aligned single-band .tif")
    ap.add_argument("output", type=Path)
    default_template = paths.DATA_DIR / "sample_submission.tif"
    if not default_template.exists():
        default_template = paths.DATA_DIR / "bridge/sample_submission.tif"  # legacy layout
    ap.add_argument("--template", type=Path, default=default_template)
    ap.add_argument(
        "--outside",
        choices=("nan", "zero"),
        default="zero",
        help="exterior encoding; zero passes a strict whole-array check, but portal acceptance is unverified",
    )
    args = ap.parse_args()
    if args.prediction.suffix == ".npy":
        a = np.load(args.prediction, allow_pickle=False)
    else:
        with rasterio.open(args.prediction) as s, rasterio.open(args.template) as t:
            if (s.shape, s.crs, s.transform, s.count) != (t.shape, t.crs, t.transform, 1):
                raise SystemExit("Prediction must match the template grid and be single-band")
            a = s.read(1)
    if args.output.suffix.lower() != ".tif":
        raise SystemExit("Output must have a .tif extension")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Never leave a newly generated invalid file, and never destroy an existing
    # output on failure. Validate the exact saved bytes before atomic replacement.
    fd, tmp_name = tempfile.mkstemp(prefix=".gems-writer-", suffix=".tif", dir=args.output.parent)
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        write_submission(a, args.template, tmp, outside=args.outside)
        checks = check_variants(tmp, args.template)
        if not checks["format_valid"]:
            print(json.dumps(checks, indent=2))
            raise SystemExit("Written file failed pinned-mirror grid/format validation")
        tmp.replace(args.output)
        checks["file"] = args.output.name
        print(json.dumps(checks, indent=2))
    finally:
        tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
