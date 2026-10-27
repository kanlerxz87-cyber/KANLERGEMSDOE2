"""A prepared matrix cannot be reused after inputs or implementation change."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prepare_data", ROOT / "scripts/prepare_data.py")
assert spec and spec.loader
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


def test_cached_matrix_binds_hash_inputs_and_pipeline(tmp_path: Path) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"input")
    dest = tmp_path / "features.npy"
    np.save(dest, np.zeros((3, 2), dtype=np.float32))
    meta = tmp_path / "features.json"
    payload = {"names": ["a", "b"], "shape": [3, 2], "sha256": prepare.sha256_file(dest),
               "inputs": {prepare._input_key(source): prepare.sha256_file(source)},
               "pipeline_signature": prepare.pipeline_signature()}
    meta.write_text(json.dumps(payload))
    assert prepare.verify_cached_preparation(dest, meta, (source,), (3, 2), ["a", "b"]) == payload
    old = payload["pipeline_signature"]
    payload["pipeline_signature"] = {"code_sha256": {}, "versions": {}}
    meta.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="implementation or library"):
        prepare.verify_cached_preparation(dest, meta, (source,), (3, 2), ["a", "b"])
    payload["pipeline_signature"] = old
    meta.write_text(json.dumps(payload))
    source.write_bytes(b"modified")
    with pytest.raises(ValueError, match="inputs changed"):
        prepare.verify_cached_preparation(dest, meta, (source,), (3, 2), ["a", "b"])
