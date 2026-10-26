#!/usr/bin/env python3
"""Evaluate the run card and literal witness; never authorize or spend a slot."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.promotion_gate import check
from scripts.registry_guard import require_candidate_generation_allowed


def main():
    card = json.loads((ROOT / "research/run_card.json").read_text())
    decision = check(card)
    try:
        require_candidate_generation_allowed(ROOT / "data")
    except RuntimeError as exc:
        decision["errors"].append(str(exc))
        decision["verdict"] = "negative"
        decision["eligible_for_selector"] = False
    decision["ok_to_submit"] = False
    decision["slot_approved"] = False
    decision["reason"] = "Format checks and self-reported card fields cannot authorize a slot; the literal registry stop is enforced independently."
    path = ROOT / "evidence/selector_decision.json"
    path.write_text(json.dumps(decision, indent=2) + "\n")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
