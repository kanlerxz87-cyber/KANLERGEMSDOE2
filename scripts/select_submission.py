#!/usr/bin/env python3
"""Evaluate the current card; never hard-code authorization or spend a slot."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.promotion_gate import check

def main():
    root=Path(__file__).resolve().parents[1]
    card=json.loads((root/'research/run_card.json').read_text())
    decision=check(card)
    decision['ok_to_submit']=False
    decision['slot_approved']=False
    decision['reason']='Separate selector needs complete verifiable evidence; format validity is insufficient.'
    (root/'evidence/selector_decision.json').write_text(json.dumps(decision,indent=2)+'\n')
    print(json.dumps(decision,indent=2))
if __name__=='__main__':main()
