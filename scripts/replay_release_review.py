#!/usr/bin/env python3
"""Replay one pinned lattice witness and the focus-nine geometry; never authorize upload.

Requires the hash-pinned owner mirrors restored with restore_data.py and
restore_focus_sites.py. The mirrors are not organizer-authenticated. This is a
negative-witness audit, not a full registry, holdout, or model replay.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from audit_release import audit_focus  # noqa: E402
from gems.release_audit import assess_file, forced_budget_result, load_reference  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    reference = load_reference(ROOT, args.data_dir)
    preflight = forced_budget_result(reference, 37654)
    focus, geometry = audit_focus(reference, args.data_dir)
    historic = json.loads((ROOT / "evidence/release_audit_20261027.json").read_text())
    if preflight != historic["preflight"] or geometry != historic["focus_lineage_geometry"]:
        raise SystemExit("Historical preflight or lineage mismatch; investigate before publication")
    card = json.loads((ROOT / "evidence/session3_hptr_run_card_20261027.json").read_text())
    path = ROOT / "docs/downloads" / card["raster_filename"]
    hptr = assess_file(path, reference)
    if hptr["sha256"] != card["raster_sha256"]:
        raise SystemExit("HPTR byte hash does not match historical card")
    result = {
        "schema": "gems.independent-replay.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Hash-pinned owner mirror template, labels, lattice, nine focus rasters, and HPTR exact bytes. No organizer authentication, full registry, holdout or surface replay.",
        "preflight": preflight,
        "hptr_exact_bytes": hptr,
        "focus_nine": focus,
        "geometry": geometry,
        "historical_preflight_and_geometry_match": True,
        "verdict": "negative",
        "ok_to_submit": False,
    }
    # A changed duplicate result requires a new decision, not silent publication.
    if not preflight["forced_duplicate"] or not hptr["duplicate_under_literal_rule"]:
        raise SystemExit("Witness stop changed; investigate before publication")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(args.out), "preflight": preflight, "hptr": hptr}, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
