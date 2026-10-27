#!/usr/bin/env python3
"""Automated fail-closed weekly-slot submission selector (`Maximize P(Win)`)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.promotion_gate import check  # noqa: E402

PORTFOLIO_LIVE_BENCHMARK_DTI = 0.2778


def evaluate_card(card: dict) -> dict:
    decision = check(card)
    gate_passed = bool(decision["verdict"] == "promote" and decision["eligible_for_selector"])
    lli_proj = (card.get("lli_s3_projection") or {}).get("projected_dti")
    beats_live_champion = isinstance(lli_proj, (int, float)) and float(lli_proj) > PORTFOLIO_LIVE_BENCHMARK_DTI

    ok_to_submit = bool(gate_passed and beats_live_champion)
    reasons = list(decision["errors"])
    if not beats_live_champion:
        reasons.append(
            f"Calibrated LLI-S3 projection ({lli_proj}) does not exceed active portfolio champion ({PORTFOLIO_LIVE_BENCHMARK_DTI})"
        )

    out = {
        **decision,
        "ok_to_submit": ok_to_submit,
        "slot_approved": ok_to_submit,
        "portfolio_live_benchmark_dti": PORTFOLIO_LIVE_BENCHMARK_DTI,
        "lli_s3_projected_dti": lli_proj,
        "selector_reasons": reasons,
        "reason": (
            "Approved for DrivenData weekly slot."
            if ok_to_submit
            else "HOLD / DO NOT SUBMIT TO PORTAL: " + "; ".join(reasons)
        ),
    }
    return out


def main() -> int:
    card = json.loads((ROOT / "research" / "run_card.json").read_text())
    out = evaluate_card(card)
    (ROOT / "evidence" / "selector_decision.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
