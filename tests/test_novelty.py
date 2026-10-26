import numpy as np
import pytest
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr
from scripts.novelty import dot_overlap, spearman_sparse

@pytest.mark.parametrize("seed", range(8))
def test_sparse_spearman_matches_scipy_ties(seed):
    rng = np.random.default_rng(seed)
    x = rng.choice([0, 0, 0, 0.2, 0.7, 1], 600)
    for y in (rng.integers(0, 2, len(x)), rng.choice([0, 0, 0.3, 0.5], len(x))):
        assert spearman_sparse(x, y) == pytest.approx(spearmanr(x, y).statistic, abs=1e-12)

def test_undefined_not_false_pass():
    assert spearman_sparse(np.array([0., 1.]), np.array([0., 0.])) is None
    assert spearman_sparse(np.array([0., 0.]), np.array([0., 1.])) is None

def test_overlap_inclusive_radius_and_boundaries():
    mine = np.zeros((10, 10)); theirs = np.zeros_like(mine)
    mine[0, 0] = 1; mine[5, 5] = 1; mine[9, 9] = 1
    theirs[0, 3] = 1; theirs[8, 5] = 1
    expected = (distance_transform_edt(~(theirs > 0))[mine > 0] <= 3).mean()
    assert dot_overlap(mine, theirs) == expected
    assert dot_overlap(mine, theirs) == pytest.approx(2/3)

def test_empty_candidate_fails():
    with pytest.raises(ValueError): dot_overlap(np.zeros((3, 3)), np.zeros((3, 3)))


def test_no_overlap_with_empty_peer():
    mine = np.zeros((5, 5)); mine[0, 0] = 1
    assert dot_overlap(mine, np.zeros((5, 5))) == 0


def test_registry_comparison_fails_closed_on_undefined_rank(tmp_path):
    import hashlib
    import rasterio
    from rasterio.transform import from_origin
    from scripts.novelty import compare
    a = np.zeros((10, 10), np.float32); a[4, 4] = 1
    footprint = np.ones_like(a, dtype=bool)
    def write(path, values):
        with rasterio.open(path, 'w', driver='GTiff', count=1, height=10, width=10,
                           dtype='float32', crs='EPSG:32611', transform=from_origin(1, 1001, 100, 100)) as ds:
            ds.write(values, 1)
    template, peer = tmp_path / 'template.tif', tmp_path / 'peer.tif'
    write(template, a)
    write(peer, np.zeros_like(a))  # Constant peer: Spearman is undefined.
    registry = {'rasters': [{'sha256': hashlib.sha256(peer.read_bytes()).hexdigest(),
                             'repo': 'test', 'path': 'peer.tif', 'local': 'peer.tif'}], 'refs': {'test': 'pinned'}}
    result = compare(a, footprint, template, registry, tmp_path, stage='surface')
    assert not result['passed']
    assert result['stop_reason'] == 'INCOMPLETE_REGISTRY_COMPARISON'
    assert result['undefined_rank_count'] == 1


def test_empty_registry_is_not_a_pass(tmp_path):
    import rasterio
    from rasterio.transform import from_origin
    from scripts.novelty import compare
    a = np.zeros((3, 3), np.float32); a[1, 1] = 1
    template = tmp_path / 'template.tif'
    with rasterio.open(template, 'w', driver='GTiff', count=1, height=3, width=3,
                       dtype='float32', crs='EPSG:32611', transform=from_origin(1, 1001, 100, 100)) as ds:
        ds.write(a, 1)
    with pytest.raises(ValueError, match='empty registry'):
        compare(a, np.ones_like(a, dtype=bool), template, {'rasters': [], 'refs': {}}, tmp_path, stage='surface')
