#!/usr/bin/env python3
"""Restore and SHA-256 verify all competition, external, and historical scored files in registry/data_manifest.json."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems32.paths import data_dir  # noqa: E402


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(repo: str, ref: str, path: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".partial")
    try:
        if shutil.which("gh"):
            with tmp.open("wb") as out:
                subprocess.run(
                    [
                        "gh",
                        "api",
                        f"repos/{repo}/contents/{path}?ref={ref}",
                        "-H",
                        "Accept: application/vnd.github.raw",
                    ],
                    stdout=out,
                    check=True,
                )
        else:
            import requests

            url = f"https://raw.githubusercontent.com/{repo}/{ref}/{path}"
            with requests.get(url, stream=True, timeout=120) as r:
                r.raise_for_status()
                with tmp.open("wb") as out:
                    for chunk in r.iter_content(1 << 20):
                        out.write(chunk)
        tmp.replace(dest)
    finally:
        tmp.unlink(missing_ok=True)


def restore_entry(entry: dict, root: Path) -> dict:
    """Verify existing bytes or restore atomically without blessing a partial file."""
    dest = root / entry["dest"]
    if dest.exists() and sha256_file(dest) == entry["sha256"]:
        return {
            "id": entry["id"], "dest": entry["dest"], "group": entry["group"],
            "status": "present", "bytes": dest.stat().st_size, "sha256": entry["sha256"],
        }
    candidate = dest.with_name(dest.name + ".assembling")
    candidate.parent.mkdir(parents=True, exist_ok=True)
    try:
        if "parts" in entry:
            with candidate.open("wb") as out:
                for part in entry["parts"]:
                    part_path = root / "raw_parts" / Path(part).name
                    try:
                        fetch(entry["repo"], entry["ref"], part, part_path)
                        with part_path.open("rb") as src:
                            shutil.copyfileobj(src, out, 1 << 20)
                    finally:
                        part_path.unlink(missing_ok=True)
        else:
            fetch(entry["repo"], entry["ref"], entry["path"], candidate)
        got = sha256_file(candidate)
        if got != entry["sha256"]:
            raise ValueError(f"HASH MISMATCH for {entry['id']}: {got} != {entry['sha256']}")
        candidate.replace(dest)
    finally:
        candidate.unlink(missing_ok=True)
    return {
        "id": entry["id"], "dest": entry["dest"], "group": entry["group"],
        "status": "restored", "bytes": dest.stat().st_size, "sha256": entry["sha256"],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--group", default="all", choices=["core", "external", "scored", "all"])
    ap.add_argument("--manifest", default=str(ROOT / "registry" / "data_manifest.json"))
    ap.add_argument("--target-dir", default=None, help="Override destination directory")
    args = ap.parse_args()

    man = json.loads(Path(args.manifest).read_text())
    if not any(args.group in ("all", e.get("group")) for e in man.get("files", [])):
        raise SystemExit("No manifest entries matched the requested group; nothing verified")
    root = Path(args.target_dir) if args.target_dir else data_dir()
    root.mkdir(parents=True, exist_ok=True)

    results = []
    for e in man["files"]:
        if args.group in ("all", e["group"]):
            try:
                r = restore_entry(e, root)
            except (OSError, ValueError, subprocess.CalledProcessError) as exc:
                # Keep checking the rest of the manifest, but return nonzero and
                # publish a partial receipt; failure is never recorded as verified.
                r = {"id": e["id"], "dest": e["dest"], "group": e["group"],
                     "status": "failed", "error": f"{type(exc).__name__}: {exc}",
                     "repo": e.get("repo"), "ref": e.get("ref"), "path": e.get("path")}
            results.append(r)
            detail = f"sha256={r['sha256'][:12]}…" if "sha256" in r else r["error"]
            print(f"{r['status']:>8}  {e['dest']:82s}  {detail}", flush=True)

    try:
        storage_root = root.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        storage_root = str(root)
    receipt = {
        "schema_version": 1,
        "verified_files_count": sum(r["status"] in ("present", "restored") for r in results),
        "failed_files_count": sum(r["status"] == "failed" for r in results),
        "complete": all(r["status"] != "failed" for r in results),
        "storage_root": storage_root,
        "files": results,
    }
    # Separate receipts avoid clobbering each other when core/external/scored
    # restores run concurrently. Bulk inputs and receipts remain untracked.
    receipt["requested_group"] = args.group
    receipts = ROOT / "data"
    receipts.mkdir(parents=True, exist_ok=True)
    output = receipts / f"restore_receipt_{args.group}.json"
    tmp = output.with_suffix(".tmp")
    tmp.write_text(json.dumps(receipt, indent=2) + "\n")
    tmp.replace(output)
    print(f"Verified {receipt['verified_files_count']} files; {receipt['failed_files_count']} failed; receipt written to {output.relative_to(ROOT)}")
    return 0 if receipt["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
