#!/usr/bin/env python3
"""Restore and SHA-256 verify all competition, external, and historical scored files in registry/data_manifest.json."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems32.paths import data_dir  # noqa: E402


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _staging_path(directory: Path, prefix: str, suffix: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=directory, prefix=prefix, suffix=suffix)
    os.close(fd)
    return Path(name)


def fetch(repo: str, ref: str, path: str, dest: Path) -> None:
    tmp = _staging_path(dest.parent, dest.name + ".", ".partial")
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
            # Standard-library fallback for public mirrors. GitHub API requests
            # may be rate-limited without gh authentication; failures are recorded.
            url = (f"https://api.github.com/repos/{quote(repo, safe='/')}/contents/"
                   f"{quote(path, safe='/')}?ref={quote(ref, safe='')}")
            request = Request(url, headers={"Accept": "application/vnd.github.raw",
                                            "User-Agent": "GEMS-owner-mirror-restore/1.0"})
            with urlopen(request, timeout=120) as response, tmp.open("wb") as out:
                shutil.copyfileobj(response, out, 1 << 20)
        tmp.replace(dest)
    finally:
        tmp.unlink(missing_ok=True)


def restore_entry(entry: dict, root: Path) -> dict:
    dest = root / entry["dest"]
    if dest.exists() and sha256_file(dest) == entry["sha256"]:
        return {
            "id": entry["id"],
            "dest": entry["dest"],
            "group": entry["group"],
            "status": "present",
            "bytes": dest.stat().st_size,
            "sha256": entry["sha256"],
        }
    # Publish to the destination only after *all* parts and the whole-file hash
    # are verified. A failed retry must not destroy a previously existing file.
    tmp = _staging_path(dest.parent, dest.name + ".", ".assembling")
    try:
        if "parts" in entry:
            with tmp.open("wb") as out:
                for part in entry["parts"]:
                    p = _staging_path(root / "raw_parts", Path(part).name + ".", ".part")
                    try:
                        fetch(entry["repo"], entry["ref"], part, p)
                        with p.open("rb") as src:
                            shutil.copyfileobj(src, out, 1 << 20)
                    finally:
                        p.unlink(missing_ok=True)
        else:
            fetch(entry["repo"], entry["ref"], entry["path"], tmp)
        got = sha256_file(tmp)
        if got != entry["sha256"]:
            raise ValueError(f"HASH MISMATCH for {entry['id']}: {got} != {entry['sha256']}")
        tmp.replace(dest)
    finally:
        tmp.unlink(missing_ok=True)
    return {
        "id": entry["id"],
        "dest": entry["dest"],
        "group": entry["group"],
        "status": "restored",
        "bytes": dest.stat().st_size,
        "sha256": entry["sha256"],
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--group", default="all", choices=["core", "external", "scored", "all"])
    ap.add_argument("--manifest", default=str(ROOT / "registry" / "data_manifest.json"))
    ap.add_argument("--target-dir", default=None, help="Override destination directory")
    args = ap.parse_args(argv)

    man = json.loads(Path(args.manifest).read_text())
    root = Path(args.target_dir) if args.target_dir else data_dir()
    root.mkdir(parents=True, exist_ok=True)

    results = []
    for e in man["files"]:
        if args.group not in ("all", e["group"]):
            continue
        try:
            r = restore_entry(e, root)
            print(f"{r['status']:>8}  {e['dest']:82s}  sha256={r['sha256'][:12]}…", flush=True)
        except (OSError, ValueError, subprocess.CalledProcessError) as exc:
            # Keep trying independent entries; failures remain failures and the
            # exit status is nonzero. Never turn a partial restore into success.
            r = {"id": e["id"], "dest": e["dest"], "group": e["group"],
                 "status": "failed", "repo": e["repo"], "ref": e["ref"],
                 "error": f"{type(exc).__name__}: {exc}"}
            print(f"  failed  {e['dest']}: {r['error']}", file=sys.stderr, flush=True)
        results.append(r)

    try:
        storage_root = root.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        storage_root = str(root)
    failed = sum(r["status"] == "failed" for r in results)
    receipt = {
        "schema_version": 2,
        "requested_group": args.group,
        "status": "failed" if not results else "partial" if failed else "complete",
        "verified_files_count": len(results) - failed,
        "failed_files_count": failed,
        "storage_root": storage_root,
        "provenance": "SHA-256 verifies owner-mirror identity, not organizer origin.",
        "files": results,
    }
    # Separate receipts avoid clobbering each other when groups run concurrently.
    receipts = ROOT / "data"
    receipts.mkdir(parents=True, exist_ok=True)
    output = receipts / f"restore_receipt_{args.group}.json"
    tmp = _staging_path(receipts, output.name + ".", ".tmp")
    try:
        tmp.write_text(json.dumps(receipt, indent=2) + "\n")
        tmp.replace(output)
    finally:
        tmp.unlink(missing_ok=True)
    if not results:
        print(f"No files in requested group {args.group!r}; refusing an empty success", file=sys.stderr)
    print(f"Verified {len(results) - failed}/{len(results)} files; {failed} failed; receipt: {output.relative_to(ROOT)}")
    return 1 if failed or not results else 0


if __name__ == "__main__":
    raise SystemExit(main())
