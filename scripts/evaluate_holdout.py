#!/usr/bin/env python3
"""Canonical spatially blocked holdout evaluator entrypoint.

Normal usage is `python scripts/evaluate_holdout.py CANDIDATE.tif` (or `.npy`/`.npz`)
and delegates to `evaluate_htcads_holdout.py`. This entrypoint never launches MTR1 or
any other experiment. The legacy `--verify-kg2` switch is retained only as a safe,
read-only artifact-integrity check for the archived KG2 lane.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if "--verify-kg2" in sys.argv[1:]:
        if sys.argv[1:] != ["--verify-kg2"]:
            raise SystemExit("--verify-kg2 is a read-only verification mode and cannot be combined with evaluator arguments")
        sys.path.insert(0, str(ROOT / "scripts"))
        from run_kg2_lane import verify_recorded

        result = verify_recorded()
        # Be defensive if an older archived card still carries an authorization-like
        # field: verification can never turn into approval to submit.
        result.pop("ok_to_submit", None)
        result["authorized_to_submit"] = False
        result["live_slot_selected"] = False
        result["live_submission_performed"] = False
        result["verification_scope"] = "Read-only integrity verification of archived artifacts; no experiment or upload was run."
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0 if result.get("verified") is True else 1

    sys.path.insert(0, str(ROOT / "scripts"))
    from evaluate_htcads_holdout import main as evaluate_main

    return evaluate_main()


if __name__ == "__main__":
    raise SystemExit(main())
