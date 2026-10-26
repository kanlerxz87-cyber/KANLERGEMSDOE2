#!/usr/bin/env python3
"""Write a *research-only* GeoTIFF with the pinned shared writer, after novelty checks.

This does not train a detector, approve a weekly slot, or publish to Pages. The
continuous surface must have been audited before dots were placed. The final-dot
check is rerun here; on a duplicate this program stops before writing a TIFF.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor/template/src"))
from gems.submission import write_submission, zip_single  # noqa: E402
from audit_uniqueness import audit  # noqa: E402
from validate_raster import sha256_file, validate  # noqa: E402


def write_research(*, surface: Path, dots: Path, template: Path, registry: Path,
                   preplacement: Path, slug: str, note: str, output_dir: Path,
                   make_zip: bool = False) -> dict:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", slug):
        raise ValueError("Slug must contain only lowercase letters, digits and hyphens")
    if not isinstance(note, str) or not note.strip() or len(note) > 140:
        raise ValueError("A nonempty note of at most 140 characters is required")
    allowed = (ROOT / ".cache/candidate-exports").resolve()
    output_dir = output_dir.resolve()
    if output_dir != allowed and allowed not in output_dir.parents:
        raise ValueError("Research outputs must remain under .cache/candidate-exports; no direct Pages publication")
    if dots.suffix.lower() != ".npy":
        raise ValueError("Dots must be a newly constructed binary .npy, not a previously submitted TIFF")
    # Audit already-placed dots against the same registry as the pre-placement
    # surface. The adapter fails on missing hashes, wrong grids, or a prior stop.
    final = audit(surface, template, registry, dots_path=dots, previous_report=preplacement)
    if final["technical_passed"] is not True:
        raise ValueError("Literal duplicate/undefined novelty check: stop before writing a raster")
    if final.get("registry_completeness_independently_verified") is not True:
        raise ValueError("Full registry coverage is unverified: stop before writing even a research raster")
    arr = np.load(dots, allow_pickle=False)
    digest = sha256_file(dots)
    if digest != final.get("dots_sha256"):
        raise ValueError("Dot array changed after novelty audit")
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / f"kanler-{slug}-{digest[:12]}-RESEARCH-ONLY.tif"
    if out.exists() or out.with_suffix(".zip").exists() or out.with_suffix(".receipt.json").exists():
        raise FileExistsError("Refusing to overwrite an existing candidate or receipt")
    try:
        # Published format calls for null/NaN outside the footprint; do not clip.
        write_submission(arr, template, out, outside="nan")
        format_result = validate(out, template)
        if not format_result["format_valid"]:
            raise ValueError("Saved raster did not pass the published-format checks")
        receipt = {
            "file": out.name, "raster_sha256": sha256_file(out), "source_dots_sha256": digest,
            "submission_name": f"KANLER-{slug.upper()}-{digest[:12].upper()}", "note": note,
            "format": format_result, "novelty": final,
            "verdict": "negative", "ok_to_submit": False,
            "reason": "Research-only artifact. Registry completeness, scientific gates, authenticated template and separate slot selector are not established by this writer.",
        }
        if make_zip:
            receipt["zip"] = zip_single(out).name
        out.with_suffix(".receipt.json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
        return receipt
    except Exception:
        out.unlink(missing_ok=True)
        out.with_suffix(".zip").unlink(missing_ok=True)
        out.with_suffix(".receipt.json").unlink(missing_ok=True)
        raise


def write_candidate(predictions, template, output, *, name, note):
    """Legacy format-only API: disabled because it bypassed registry prerequisites."""
    raise ValueError("BLOCKED: format-only staging bypasses pre-placement, final-dot and complete-registry checks; no raster written")


# Keep the old importable name, but never permit a registry-bypassing artifact.
stage = write_candidate


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--research-only", action="store_true", required=True)
    p.add_argument("--surface", type=Path, required=True)
    p.add_argument("--dots", type=Path, required=True)
    p.add_argument("--template", type=Path, default=ROOT / "data/sample_submission.tif")
    p.add_argument("--registry", type=Path, required=True)
    p.add_argument("--preplacement-report", type=Path, required=True)
    p.add_argument("--slug", required=True)
    p.add_argument("--note", required=True)
    p.add_argument("--out-dir", type=Path, default=ROOT / ".cache/candidate-exports")
    p.add_argument("--zip", action="store_true")
    a = p.parse_args()
    result = write_research(surface=a.surface, dots=a.dots, template=a.template, registry=a.registry,
                            preplacement=a.preplacement_report, slug=a.slug, note=a.note,
                            output_dir=a.out_dir, make_zip=a.zip)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
