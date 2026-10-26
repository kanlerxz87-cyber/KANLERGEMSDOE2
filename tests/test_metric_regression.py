"""Independent numeric cross-checks of the pinned shared helpers."""
import numpy as np
import pytest
from scipy.stats import spearmanr

from compare_registry import compare
from gems.metric import dti_components_exact, dti_score_fast
from scripts.promotion_gate import check


def test_spearman_crosscheck_includes_nonbinary_tied_references():
    rng = np.random.default_rng(42)
    for binary_candidate in (True, False):
        a = rng.integers(0, 2 if binary_candidate else 5, size=(20, 20))
        b = rng.integers(0, 7, size=(20, 20))
        expected = spearmanr(a.ravel(), b.ravel()).statistic
        assert compare(a, b, np.ones_like(a, bool))["spearman_rho"] == pytest.approx(expected, abs=1e-12)


def test_shared_fast_binary_dti_matches_exact_with_visible_mask():
    rng = np.random.default_rng(23)
    pred = (rng.random((40, 40)) < .04).astype(np.uint8)
    truth = (rng.random((40, 40)) < .03).astype(np.uint8)
    valid = rng.random((40, 40)) > .1
    known = rng.random((40, 40)) < .08
    exact = dti_components_exact(pred, truth, valid_mask=valid, catalogue_mask=known)
    fast = dti_score_fast(pred, truth, valid_mask=valid, catalogue_mask=known)
    for key in ("TP_w", "FP_w", "FN_w", "dti"):
        assert fast[key] == pytest.approx(exact[key], abs=1e-10)


def test_structurally_invalid_cards_fail_closed_without_exceptions():
    for card in (None, [], {"lane": True}, {"surface": None, "holdout": None, "validator": None}):
        result = check(card)
        assert result["verdict"] == "negative" and not result["eligible_for_selector"]
