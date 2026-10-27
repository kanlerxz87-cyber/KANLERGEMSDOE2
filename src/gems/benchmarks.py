"""Inventory declared, comparable holdout records; never authorize a slot.

A recorded point estimate is a floor for screening, not proof that the run can
be replayed or that its features, split, or candidate are valid. The mandatory
records below are present in this checkout; missing/malformed records fail
closed instead of silently lowering the benchmark.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from .validator import sha256_file

EVALUATOR = "gems-segment-pooled-v1"
WITHHELD = 60988
# Explicit adapters are necessary: prior sessions used incompatible schemas.
REQUIRED_RECORDS = (
    ("KG2-MGHV-EXP-1", "evidence/kg2_holdout_20261026.json", "kg2"),
    ("FVCA-SUBMOD-EXP-2", "evidence/fvca_experiments.json", "fvca"),
)


def _normalize(result: dict) -> dict:
    label = result.get("label", result.get("metric_label"))
    count = result.get("n_withheld_positive_pixels", result.get("n_withheld_positives"))
    dti = result.get("dti")
    ci = result.get("ci95")
    interval = ci.get("interval") if isinstance(ci, dict) else ci
    if (
        label != "HOLDOUT-DTI"
        or result.get("evaluator_version") != EVALUATOR
        or type(count) is not int
        or count != WITHHELD
        or type(dti) not in (int, float)
        or not math.isfinite(dti)
        or not 0 <= dti <= 1
        or not isinstance(interval, list)
        or len(interval) != 2
        or any(type(x) not in (int, float) or not math.isfinite(x) for x in interval)
        or not 0 <= interval[0] <= interval[1] <= 1
    ):
        raise ValueError("Malformed or noncomparable recorded HOLDOUT-DTI")
    return {
        "label": "HOLDOUT-DTI",
        "evaluator_version": EVALUATOR,
        "n_withheld_positive_pixels": count,
        "dti": dti,
        "ci95": {"level": 0.95, "interval": interval, "scope": "Recorded CI; not independently replayed"},
    }


def recorded_points(root: Path) -> list[dict]:
    root = Path(root)
    rows = []
    for lane, source, adapter in REQUIRED_RECORDS:
        path = root / source
        if not path.is_file():
            raise ValueError(f"Required recorded benchmark missing: {source}")
        try:
            data = json.loads(path.read_text())
            if adapter == "kg2":
                result = data["arms"]["EXP-1_KG2_Core78_TwoRegime"]
            else:
                arms = [x for x in data["experiments"] if x["id"] == "EXP-2"]
                if len(arms) != 1:
                    raise ValueError("FVCA EXP-2 is not unique in the ledger")
                result = arms[0]["segment_holdout_v1"]
            holdout = _normalize(result)
        except (KeyError, TypeError, IndexError, json.JSONDecodeError) as exc:
            raise ValueError(f"Malformed required benchmark: {source}") from exc
        rows.append({
            "lane": lane, "source": source, "source_sha256": sha256_file(path),
            "holdout": holdout,
            "scope": "Recorded point estimate only; no independent replay, paired-gain or novelty certification",
        })
    # Admit future run cards only when they explicitly declare this evaluator
    # and positive count. Same-name metrics on different splits are not pooled.
    for path in sorted((root / "evidence").glob("*run_card*.json")):
        card = json.loads(path.read_text())
        if not isinstance(card, dict):
            continue
        result = card.get("holdout", card.get("holdout_dti"))
        if not isinstance(result, dict) or result.get("evaluator_version") != EVALUATOR:
            continue
        count = result.get("n_withheld_positive_pixels", result.get("n_withheld_positives"))
        if count != WITHHELD:
            continue
        holdout = _normalize(result)
        rows.append({
            "lane": path.stem, "source": path.relative_to(root).as_posix(),
            "source_sha256": sha256_file(path), "holdout": holdout,
            "scope": "Recorded point estimate only; no independent replay, paired-gain or novelty certification",
        })
    return sorted(rows, key=lambda row: row["holdout"]["dti"], reverse=True)


def recorded_point_best(root: Path) -> dict:
    rows = recorded_points(root)
    if not rows:
        raise ValueError("No required benchmark records")
    return rows[0]
