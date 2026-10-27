"""Single source of truth for repository and data locations.

Large rasters are never committed. Point ``GEMS_DATA_DIR`` at the folder that holds
``training_features.tif``, ``labels.tif`` and ``sample_submission.tif`` (created by
``scripts/download_competition_data.sh``). ``GEMS_GROUP_DIR`` is a cache for the group's
historic submission GeoTIFFs fetched from GitHub by ``scripts/forensic_audit.py``.
"""

from __future__ import annotations

import os
from pathlib import Path

def _resolve_default_data_dir() -> Path:
    env = os.environ.get("GEMS_DATA_DIR")
    if env:
        return Path(env).expanduser()
    cache = ROOT / ".cache" / "gems_data"
    if (cache / "sample_submission.tif").exists() or (cache / "training_features.tif").exists():
        return cache
    return ROOT / "data"


ROOT: Path = Path(__file__).resolve().parents[2]
# Use the same resolver as restore_data.py, including legacy /core layouts.
from gems32.paths import data_dir as _data_dir

DATA_DIR: Path = _data_dir()
GROUP_DIR: Path = Path(os.environ.get("GEMS_GROUP_DIR", DATA_DIR / "group_subs"))
EVIDENCE_DIR: Path = ROOT / "evidence"
DOCS_DIR: Path = ROOT / "docs"
DOWNLOADS_DIR: Path = DOCS_DIR / "downloads"
SITE_DATA_DIR: Path = DOCS_DIR / "data"
SUBMISSIONS_DIR: Path = ROOT / "submissions"
REGISTRY_DIR: Path = ROOT / "registry"
REGISTRY_PATH: Path = REGISTRY_DIR / "submissions.json"
AUDIT_CLONES: Path = Path(os.environ.get("GEMS_AUDIT_DIR", "/tmp/audit"))

TEMPLATE_PATH: Path = DATA_DIR / "sample_submission.tif"
LABELS_PATH: Path = DATA_DIR / "labels.tif"
FEATURES_PATH: Path = DATA_DIR / "training_features.tif"
