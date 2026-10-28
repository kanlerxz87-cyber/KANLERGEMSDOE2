#!/usr/bin/env python3
"""Fetch all 360 comparison-registry rasters (``registry/comparison_registry.json``), SHA-256 verified.

Needed by the automated uniqueness gate (``scripts/validate_submission_kg2s3.py``): overlap and rank
correlation are recomputed from bytes, never copied from a run card.  Files go to
``$GEMS_DATA_DIR/registry/<sha16>/<filename>`` (ignored by git).  Rasters already present in the
ledger cache are hard-linked instead of re-downloaded.  Unavailable files are reported and make the
receipt incomplete; the validator fails closed if any registry raster is missing.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems32.paths import data_dir  # noqa: E402

OWNER = "buffedlizard55-lab"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def local_index(root: Path) -> dict[str, Path]:
    idx = {}
    for sub in ("ledger", "ledger_add", "scored", "scored_extra", "focus_sites", "focus_20261027"):
        d = root / sub
        if d.exists():
            for p in d.rglob("*.tif"):
                try:
                    idx.setdefault(sha256_file(p), p)
                except OSError:
                    pass
    return idx


def main() -> int:
    reg = json.loads((ROOT / "registry/comparison_registry.json").read_text())["entries"]
    root = data_dir()
    out_dir = root / "registry"
    have = local_index(root)

    def one(e):
        dest = out_dir / e["sha256"][:16] / e["filename"]
        if dest.exists() and sha256_file(dest) == e["sha256"]:
            return dict(sha256=e["sha256"], local=str(dest), status="present")
        dest.parent.mkdir(parents=True, exist_ok=True)
        if e["sha256"] in have:
            try:
                os.link(have[e["sha256"]], dest)
            except OSError:
                dest.write_bytes(have[e["sha256"]].read_bytes())
            return dict(sha256=e["sha256"], local=str(dest), status="linked")
        cands = [f"{e['primary_repo']}:{e['rel_path']}"] + list(e.get("also_in") or [])
        for c in cands:
            repo, path = c.split(":", 1)
            tmp = dest.with_suffix(".partial")
            try:
                with tmp.open("wb") as f:
                    subprocess.run(["gh", "api", f"repos/{OWNER}/{repo}/contents/{path}",
                                    "-H", "Accept: application/vnd.github.raw"], stdout=f, check=True,
                                   stderr=subprocess.DEVNULL, timeout=600)
                if sha256_file(tmp) == e["sha256"]:
                    tmp.replace(dest)
                    return dict(sha256=e["sha256"], local=str(dest), status="restored", source=c)
            except Exception:  # noqa: BLE001
                pass
            tmp.unlink(missing_ok=True)
        return dict(sha256=e["sha256"], local=None, status="unavailable")

    with ThreadPoolExecutor(max_workers=6) as pool:
        res = list(pool.map(one, reg))
    ok = [r for r in res if r["status"] != "unavailable"]
    rec = {"schema": "kg2.registry_fetch.v1", "n_entries": len(reg), "n_verified": len(ok), "rows": res}
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data/registry_fetch_receipt.json").write_text(json.dumps(rec, indent=1) + "\n")
    print(f"verified {len(ok)}/{len(reg)} registry rasters into {out_dir}")
    for r in res:
        if r["status"] == "unavailable":
            print("UNAVAILABLE", r["sha256"][:16])
    return 0 if len(ok) == len(reg) else 1


if __name__ == "__main__":
    raise SystemExit(main())
