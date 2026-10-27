"""Single source of truth for repository and data locations.

Large rasters are never committed. Point ``GEMS_DATA_DIR`` at the folder that holds
``training_features.tif``, ``labels.tif`` and ``sample_submission.tif`` (created by
``scripts/download_competition_data.sh``). ``GEMS_GROUP_DIR`` is a cache for the group's
historic submission GeoTIFFs fetched from GitHub by ``scripts/forensic_audit.py``.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT: Path = Path(__file__).resolve().parents[2]
DATA_DIR: Path = Path(os.environ.get("GEMS_DATA_DIR", ROOT / "data"))
GROUP_DIR: Path = Path(os.environ.get("GEMS_GROUP_DIR", DATA_DIR / "group_subs"))
EVIDENCE_DIR: Path = ROOT / "evidence"
DOCS_DIR: Path = ROOT / "docs"
DOWNLOADS_DIR: Path = DOCS_DIR / "downloads"
SITE_DATA_DIR: Path = DOCS_DIR / "data"
SUBMISSIONS_DIR: Path = ROOT / "submissions"
REGISTRY_DIR: Path = ROOT / "registry"
REGISTRY_PATH: Path = REGISTRY_DIR / "submissions.json"
AUDIT_CLONES: Path = Path(os.environ.get("GEMS_AUDIT_DIR", "/tmp/audit"))

def core_path(name: str) -> Path:
    """Locate a restored core input, accepting the older ``bridge/`` layout.

    The manifest restores core files at the data-directory root. Older
    workspaces stored the small template and labels in ``bridge/``. Prefer
    the restored root file and do not silently select an unrelated directory.
    """
    if Path(name).name != name:
        raise ValueError("core input must be a filename, not a path")
    direct = DATA_DIR / name
    legacy = DATA_DIR / "bridge" / name
    return direct if direct.is_file() or not legacy.is_file() else legacy


TEMPLATE_PATH: Path = core_path("sample_submission.tif")
LABELS_PATH: Path = core_path("labels.tif")
FEATURES_PATH: Path = core_path("training_features.tif")
