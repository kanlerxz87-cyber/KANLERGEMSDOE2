"""Synthetic lineage geometry, plus consistency with the checked-in audit receipt."""
import json
from pathlib import Path

import numpy as np
import pytest

from audit_h33_lineage import compare_lineage

ROOT = Path(__file__).resolve().parents[1]


def test_two_pixel_prune_is_euclidean_and_exact():
    fp = np.ones((20, 20), bool)
    known = np.zeros_like(fp); known[8, 8] = 1
    base = np.zeros_like(fp, dtype=np.float32)
    base[9, 9] = base[8, 10] = base[11, 11] = 1
    champ = np.zeros_like(base); champ[11, 11] = 1
    result = compare_lineage(base, champ, known, fp)
    assert result["removed_pixels"] == 2 and result["added_pixels"] == 0
    assert result["removed_at_sqrt_2px"] == 1 and result["removed_at_2px"] == 1
    assert result["equals_exact_2px_pruned_base"]
    champ[15, 15] = 1
    assert not compare_lineage(base, champ, known, fp)["equals_exact_2px_pruned_base"]


def test_lineage_rejects_invalid_inputs():
    z = np.zeros((8, 8))
    with pytest.raises(ValueError, match="nonempty known"):
        compare_lineage(z, z, z, np.ones_like(z))
    with pytest.raises(ValueError, match="aligned"):
        compare_lineage(z, z[:3], z, np.ones_like(z))


def test_historical_receipt_reports_raster_relationship_not_score_confirmation():
    audit = json.loads((ROOT / "evidence/h33_lineage_20261026.json").read_text())
    comp = audit["comparison"]
    assert comp["base_positive_pixels"] == 40199 and comp["champion_positive_pixels"] == 37654
    assert comp["removed_pixels"] == 2545 and comp["added_pixels"] == 0
    assert comp["equals_exact_2px_pruned_base"] and comp["difference_from_exact_2px_catalogue_prune"] == 0
    assert "Unverified" in audit["reported_scores"]["label"] and not audit["ok_to_submit"]
