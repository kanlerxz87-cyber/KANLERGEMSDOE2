#!/usr/bin/env python3
"""Restore nine pinned owner-hosted raster witnesses (no competition upload)."""
from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems32.paths import data_dir  # noqa: E402
from restore_data import fetch, sha256_file  # noqa: E402


def main() -> int:
    manifest = json.loads((ROOT / "registry/focus_sites_20261027.json").read_text())
    target = data_dir() / "focus_20261027"
    target.mkdir(parents=True, exist_ok=True)

    def one(row: dict) -> tuple[str, str]:
        dest = target / (row["site"] + "__" + Path(row["path"]).name)
        try:
            if not dest.exists() or sha256_file(dest) != row["sha256"]:
                fetch(row["repository"], row["ref"], row["path"], dest)
            actual = sha256_file(dest)
            if actual != row["sha256"]:
                dest.unlink(missing_ok=True)
                return row["site"], "HASH MISMATCH " + actual
            return row["site"], "sha256 verified " + actual
        except Exception as exc:
            return row["site"], f"unavailable: {type(exc).__name__}: {exc}"

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(one, manifest["sites"]))
    for site, status in results:
        print(site, status)
    return 0 if all(s.startswith("sha256 verified") for _, s in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
