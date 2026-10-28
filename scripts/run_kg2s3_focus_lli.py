#!/usr/bin/env python3
"""KG2-S3: leave-site-out LLI predictions for the nine focus files (selected design), for the executive
summary.  Live scores are USER-REPORTED; model numbers are PROJECTIONS (leave-site-out = the focus site's
own rasters were excluded from the fit that predicts them)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import run_kg2s3_lli_cv as cv  # noqa: E402
from gems32 import ledger_inversion as li  # noqa: E402
from gems32 import lope  # noqa: E402

FOCUS = {"GEMSDOE24": "h25-1-dotted-h19-5-d1-5", "GEMSDOE25": "dotted-h19-5-d2-8-20261002", "GEMSDOE27": "topo-gap-closure-t-v2",
         "GEMSDOE28": "h36-1-rung30-blind-r1", "GEMSDOE30": "d28-poisson300m-offcat-44090", "GEMSDOE31": "h27-4-solo-d28",
         "GEMSDOE32": "h33-h33-2-b2", "GEMSDOE33": "h33d-analog-tip-stepover", "GEMSDOE36": "anderson-geothermal-pinn"}


def main() -> int:
    raise SystemExit(
        "Archived runner disabled: not the assigned HTCADS lane; the literal registry stop "
        "and preserved historical receipts prohibit this execution path."
    )


def _legacy_main_archived() -> int:
    """Historical implementation retained for audit; do not use as an active runner."""
    sel = json.loads((ROOT / "evidence/kg2s3_lli_design_cv.json").read_text())["selected"]
    z, fm, meta, active = cv.load()
    full = lope.full_spec(fm, active)
    fac = cv.DESIGNS[sel["design"]]
    sp = cv.design_spec(fm, active, fac)
    A, B = cv.collapse(z["A"], full, fac), cv.collapse(z["B"], full, fac)
    N, S = z["N"], z["S"]
    groups = np.array([m["site"] for m in meta])
    lso = li.loo(A, B, N, S, sp, groups=groups, ridge=sel["ridge"])["pred"]
    fit = li.fit(A, B, N, S, sp, ridge=sel["ridge"])["pred"]
    rows = []
    for site, key in FOCUS.items():
        for i, m in enumerate(meta):
            names = [m["submission"]] + m["aliases"]
            if m["site"] == site and any(key in n for n in names):
                rows.append({"site": site, "submission": m["submission"], "live_user_reported": m["score"],
                             "lli_in_sample_fit": float(fit[i]), "lli_leave_site_out_projection": float(lso[i]),
                             "dots": m["dots"]})
                break
    out = {"schema": "kg2s3.focus_lli.v1", "design": sel["design"], "ridge": sel["ridge"],
           "labels": {"live_user_reported": "USER-REPORTED", "lli_*": "PROJECTION"}, "rows": rows}
    (ROOT / "evidence/kg2s3_focus_site_lli.json").write_text(json.dumps(out, indent=1) + "\n")
    for r in rows:
        print(f"{r['site']:10s} live {r['live_user_reported']:.4f} fit {r['lli_in_sample_fit']:.4f} LSO {r['lli_leave_site_out_projection']:.4f}  {r['submission'][:60]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
