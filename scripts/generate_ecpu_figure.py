#!/usr/bin/env python3
"""Figure 4: KG2-ECPU negative-result holdout comparison (from measured receipts only)."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
exps = json.loads((ROOT / "evidence" / "ecpu_experiments_20261027.json").read_text())

labels = ["B2 champ\n(procedural)", "HTCADS EXP-2\n(recorded OOF)", "C0 twin\n(unweighted)",
          "ECPU EXP-1\n(weighted)", "ECPU EXP-2\n(+strata)", "ECPU EXP-3\n(+ridge gate)"]
hr = [exps["references"]["REF-B2-HR-procedural"]["pooled_dti"], 0.112353,
      exps["experiments"]["C0-twin"]["holdout_hide_recover_oof"]["pooled_dti"],
      exps["experiments"]["EXP-1"]["holdout_hide_recover_oof"]["pooled_dti"],
      exps["experiments"]["EXP-2"]["holdout_hide_recover_oof"]["pooled_dti"],
      exps["experiments"]["EXP-3"]["holdout_hide_recover_oof"]["pooled_dti"]]
hr_ci = [exps["references"]["REF-B2-HR-procedural"]["ci95"], [0.098995, 0.125743],
         exps["experiments"]["C0-twin"]["holdout_hide_recover_oof"]["ci95"],
         exps["experiments"]["EXP-1"]["holdout_hide_recover_oof"]["ci95"],
         exps["experiments"]["EXP-2"]["holdout_hide_recover_oof"]["ci95"],
         exps["experiments"]["EXP-3"]["holdout_hide_recover_oof"]["ci95"]]
sg = [exps["references"]["REF-B2-SGMC-static"]["sgmc_prevalence_calibrated_dti"],
      exps["references"]["REF-HTCADS-SGMC-static"]["sgmc_prevalence_calibrated_dti"],
      exps["experiments"]["C0-twin"]["holdout_sgmc_static_live"]["sgmc_prevalence_calibrated_dti"],
      exps["experiments"]["EXP-1"]["holdout_sgmc_static_live"]["sgmc_prevalence_calibrated_dti"],
      exps["experiments"]["EXP-2"]["holdout_sgmc_static_live"]["sgmc_prevalence_calibrated_dti"],
      exps["experiments"]["EXP-3"]["holdout_sgmc_static_live"]["sgmc_prevalence_calibrated_dti"]]
sg_ci = [exps["references"]["REF-B2-SGMC-static"]["ci95"],
         exps["references"]["REF-HTCADS-SGMC-static"]["ci95"],
         exps["experiments"]["C0-twin"]["holdout_sgmc_static_live"]["ci95"],
         exps["experiments"]["EXP-1"]["holdout_sgmc_static_live"]["ci95"],
         exps["experiments"]["EXP-2"]["holdout_sgmc_static_live"]["ci95"],
         exps["experiments"]["EXP-3"]["holdout_sgmc_static_live"]["ci95"]]
colors = ["#f59e0b", "#34d399", "#94a3b8", "#f87171", "#f87171", "#f87171"]

fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
for ax, vals, cis, title in (
    (axes[0], hr, hr_ci, "HOLDOUT-DTI GEMSDOE32-HIDE-RECOVER-v3.0 (OOF, N=22,232)"),
    (axes[1], sg, sg_ci, "HOLDOUT-DTI GEMSDOE32-SGMC-CAL-v3.0 (static, N=62,703)"),
):
    x = np.arange(len(labels))
    err = np.array([[v - c[0] for v, c in zip(vals, cis)], [c[1] - v for v, c in zip(vals, cis)]])
    ax.bar(x, vals, color=colors, edgecolor="k", linewidth=0.5)
    ax.errorbar(x, vals, yerr=err, fmt="none", ecolor="k", capsize=3, linewidth=1)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.004, f"{v:.4f}", ha="center", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8)
    ax.set_title(title, fontsize=10); ax.set_ylabel("DTI"); ax.grid(axis="y", alpha=0.3)
    ax.set_ylim(0, max(vals) * 1.25)
fig.suptitle("KG2-ECPU (2026-10-27): NEGATIVE RESULT — all 3 preregistered experiments lose to both benchmarks (fail-closed, DO NOT SUBMIT)", fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.92])
out = ROOT / "docs" / "assets" / "fig4_ecpu_negative_result.png"
fig.savefig(out, dpi=160)
print(f"wrote {out}")
