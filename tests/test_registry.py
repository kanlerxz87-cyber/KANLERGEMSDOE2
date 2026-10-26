import hashlib
import json
import pytest
from scripts import verify_registry_snapshot as registry


def blob_id(data):
    return hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()


def fixture(tmp_path, monkeypatch, *, tree=None):
    monkeypatch.setattr(registry, 'FOCUS', ('GEMSDOE24',))
    expected = b'authentic raster bytes'
    local = tmp_path / 'template' / '.cache/registry/GEMSDOE24/docs/a.tif'
    local.parent.mkdir(parents=True)
    local.write_bytes(expected)
    manifest = {'refs': {'GEMSDOE24': 'deadbeef'}, 'n_failed': 0,
                'rasters': [{'repo': 'GEMSDOE24', 'ref': 'deadbeef', 'path': 'docs/a.tif',
                             'local': '.cache/registry/GEMSDOE24/docs/a.tif', 'status': 'ok'}]}
    path = tmp_path / 'lock.json'; path.write_text(json.dumps(manifest))
    default = {'truncated': False, 'tree': [{'type': 'blob', 'path': 'docs/a.tif', 'size': len(expected), 'sha': blob_id(expected)}]}
    monkeypatch.setattr(registry, 'gh_json', lambda _: default if tree is None else tree)
    return path, local, expected


def test_manifest_hash_matches_immutable_tree(tmp_path, monkeypatch):
    path, _, expected = fixture(tmp_path, monkeypatch)
    r = registry.verify(tmp_path / 'template', path, tmp_path / 'out.json')
    assert r['rasters_verified'] == 1
    assert r['rasters'][0]['git_blob_sha1'] == blob_id(expected)
    assert r['rasters'][0]['sha256'] == hashlib.sha256(expected).hexdigest()


def test_truncated_or_missing_inventory_fails_closed(tmp_path, monkeypatch):
    p, _, _ = fixture(tmp_path, monkeypatch, tree={'truncated': True, 'tree': []})
    with pytest.raises(ValueError, match='truncated'):
        registry.verify(tmp_path / 'template', p, tmp_path / 'out.json')
    monkeypatch.setattr(registry, 'gh_json', lambda _: {'truncated': False, 'tree': []})
    with pytest.raises(ValueError, match='inventory differs'):
        registry.verify(tmp_path / 'template', p, tmp_path / 'out.json')


def test_same_size_wrong_bytes_are_refetched(tmp_path, monkeypatch):
    p, local, expected = fixture(tmp_path, monkeypatch)
    local.write_bytes(b'x' * len(expected))
    def fake_run(cmd, *, stdout, check):
        stdout.write(expected)
    monkeypatch.setattr(registry.subprocess, 'run', fake_run)
    r = registry.verify(tmp_path / 'template', p, tmp_path / 'out.json')
    assert local.read_bytes() == expected
    assert r['corrected_same_size_or_missing_cache_entries'] == ['GEMSDOE24/docs/a.tif']


def test_escaping_local_path_is_rejected(tmp_path, monkeypatch):
    p, _, _ = fixture(tmp_path, monkeypatch)
    data = json.loads(p.read_text()); data['rasters'][0]['local'] = '../outside.tif'
    p.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='escapes'):
        registry.verify(tmp_path / 'template', p, tmp_path / 'out.json')
