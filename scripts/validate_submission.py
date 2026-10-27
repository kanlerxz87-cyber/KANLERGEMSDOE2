#!/usr/bin/env python3
"""Fail-closed, byte-bound GeoTIFF and recorded-evidence screening.

The format check is not portal acceptance, a new holdout replay, an exhaustive
registry comparison, or weekly-slot authorization. No upload is performed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems import submission  # noqa: E402
from gems.preflight import LATTICE_NAME, TEMPLATE_SHA256, measure_candidate, pinned_witness  # noqa: E402
from gems.validator import sha256_file  # noqa: E402
from gems32.paths import data_dir  # noqa: E402


def validate_all_gates(tif_path: Path, run_card_path: Path, ddir: Path | None = None) -> dict:
    """Reopen exact bytes and return a negative decision if evidence is missing.

    The recorded numbers in an old card are not independently reproduced merely
    by reading them. There is intentionally no positive slot-authorization path
    until the complete replay and current-account selector are implemented.
    """
    ddir = Path(ddir) if ddir is not None else data_dir()
    tif_path, run_card_path = Path(tif_path), Path(run_card_path)
    template = ddir / "sample_submission.tif"
    issues: list[str] = []
    checks = None
    witness = None
    card: dict = {}
    sha = None
    note_ok = False
    identity_ok = False
    template_ok = False
    format_ok = False
    witness_ok = False
    try:
        card = json.loads(run_card_path.read_text(encoding="utf-8"))
        if not isinstance(card, dict):
            raise ValueError("run card must be an object")
        note = card.get("note", card.get("submission_note"))
        note_ok = isinstance(note, str) and 0 < len(note) <= 140 and bool(card.get("submission_name"))
    except (OSError, ValueError) as exc:
        issues.append(f"run card unavailable or malformed: {exc}")
    try:
        sha = sha256_file(tif_path)
        identity_ok = sha == card.get("raster_sha256")
        if not identity_ok:
            issues.append("artifact SHA-256 does not match the recorded run card")
    except OSError as exc:
        issues.append(f"artifact unavailable: {exc}")
    try:
        template_ok = sha256_file(template) == TEMPLATE_SHA256
        if not template_ok:
            raise ValueError("template does not match the pinned owner mirror")
        checks = submission.check_variants(tif_path, template)
        strict = checks["checks"]["variant_strict_whole_array_no_nan_allowed"]["pass"]
        format_ok = bool(checks["format_valid"] and strict)
        if not format_ok:
            issues.append("reopened file failed a local grid/range check")
    except (OSError, ValueError, KeyError, rasterio.errors.RasterioError) as exc:
        issues.append(f"local format check unavailable or failed: {exc}")
    if format_ok:
        try:
            # Derive K from the actual raster before measuring the registered
            # witness. This is not a claim that the rest of the registry passed.
            with rasterio.open(template) as ds:
                fp = np.isfinite(ds.read(1))
            with rasterio.open(tif_path) as ds:
                k = int((ds.read(1)[fp] > 0).sum())
            proof, fp, halo = pinned_witness(
                template, ddir / "scored" / LATTICE_NAME,
                ROOT / "registry/comparison_registry.json", k,
            )
            witness = {**measure_candidate(tif_path, template, fp, halo),
                       "forced_minimum_overlap": proof["minimum_possible_directional_overlap"]}
            witness_ok = not witness["literal_duplicate"]
            if not witness_ok:
                issues.append("literal registry duplicate: more than 70% of candidate dots are within 3 px of the registered lattice")
        except (OSError, ValueError, KeyError, rasterio.errors.RasterioError) as exc:
            issues.append(f"literal registry witness unavailable or invalid: {exc}")
    # Recorded booleans, sampled correlations, and a format pass are not a
    # replay certificate. Fail closed until these integrations really exist.
    gates = {
        "artifact_sha_matches_card": identity_ok,
        "pinned_owner_mirror_template": template_ok,
        "local_grid_and_whole_array_range": format_ok,
        "literal_registered_lattice_overlap": witness_ok,
        "complete_registry_surface_and_final_replayed": False,
        "all_feature_canaries_independently_replayed": False,
        "same_evaluator_current_best_paired_holdout_replayed": False,
        "note_at_most_140_characters": note_ok,
        "separate_account_quota_selector_verified": False,
    }
    issues.extend([
        "complete registry/surface and final-dot replay is not implemented",
        "feature-canary and current-best paired holdout replays are not attached to this exact artifact",
        "current-account weekly allowance and separate selector are not verified",
    ])
    return {
        "schema": "gems.validator.fail-closed.v2",
        "raster_filename": tif_path.name,
        "raster_sha256": sha,
        "format_audit": checks,
        "local_format_valid": format_ok,
        "literal_lattice_witness": witness,
        "gates": gates,
        "validated_ok_to_download_and_submit": False,
        "ok_to_submit": False,
        "verdict": "negative",
        "automated_screen_only": True,
        "portal_acceptance": "unknown",
        "reasons": issues,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tif", type=Path, required=True)
    ap.add_argument("--run-card", type=Path, default=ROOT / "evidence/run_card.json")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    result = validate_all_gates(args.tif, args.run_card)
    text = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["ok_to_submit"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
