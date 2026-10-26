from itertools import combinations

import numpy as np
import pytest
from scipy.ndimage import distance_transform_edt

from scripts.lattice_feasibility import lower_bound


def test_lower_bound_equals_bruteforce_optimum():
    foot = np.ones((3, 4), dtype=bool)
    registry = np.zeros_like(foot)
    registry[1, 1] = True
    n = 5
    result = lower_bound(foot, registry, n, radius_px=1.0)
    halo = distance_transform_edt(~registry) <= 1.0
    minimum = min(sum(halo.flat[i] for i in combination) for combination in combinations(range(foot.size), n))
    assert result['minimum_candidate_dots_inside_halo'] == minimum
    assert result['minimum_fraction_inside_halo'] == minimum / n


def test_seventy_percent_is_not_strictly_over_threshold():
    foot = np.ones((1, 10), dtype=bool)
    points = np.array([[1, 1, 1, 1, 1, 1, 1, 0, 0, 0]], dtype=bool)
    result = lower_bound(foot, points, 10, radius_px=0)
    assert result['minimum_fraction_inside_halo'] == 0.70
    assert result['strict_more_than_70_percent_unavoidable'] is False
    assert result['verdict'] == 'inconclusive-not-a-novelty-pass'


def test_above_seventy_stops_and_does_not_mutate_input():
    foot = np.array([[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0]], dtype=bool)
    points = np.array([[1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1]], dtype=bool)
    saved = points.copy()
    result = lower_bound(foot, points, 10, radius_px=0)
    assert np.array_equal(points, saved)
    assert result['minimum_fraction_inside_halo'] == 0.8
    assert result['verdict'] == 'duplicate-stop'


def test_empty_registry_is_inconclusive_not_pass():
    foot = np.ones((2, 2), dtype=bool)
    out = lower_bound(foot, np.zeros_like(foot), 4)
    assert out['minimum_fraction_inside_halo'] == 0
    assert out['verdict'] == 'inconclusive-not-a-novelty-pass'


@pytest.mark.parametrize('budget', [0, -1, 5, True])
def test_invalid_budget_fails_closed(budget):
    with pytest.raises(ValueError):
        lower_bound(np.ones((2, 2), bool), np.ones((2, 2), bool), budget)


def test_bad_grid_and_radius_fail():
    with pytest.raises(ValueError):
        lower_bound(np.ones((2, 2), bool), np.ones((2, 1), bool), 1)
    with pytest.raises(ValueError):
        lower_bound(np.ones((2, 2), bool), np.ones((2, 2), bool), 1, radius_px=float('nan'))
