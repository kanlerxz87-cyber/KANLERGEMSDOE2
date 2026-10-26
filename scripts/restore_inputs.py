#!/usr/bin/env python3
"""Restore hash-pinned peer-mirrored inputs using Git, without authenticating them.

The competition originals still require DrivenData access. This tool never commits
raster bytes and never replaces an existing mismatched file. Git objects and temporary
files are cached under ignored workspace directories, not the repository's .git.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PINS = ROOT / "research/input_pins.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(path: Path, record: dict) -> bool:
    return path.is_file() and path.stat().st_size == record["bytes"] and sha256_file(path) == record["sha256"]


def git(*args: str, **kwargs) -> None:
    subprocess.run(["git", *args], check=True, **kwargs)


def restore(record: dict, *, root: Path = ROOT, verify_only: bool = False) -> str:
    dest = (root / record["destination"]).resolve()
    data = (root / "data").resolve()
    if data not in dest.parents:
        raise ValueError(f"Destination must remain under data/: {dest}")
    if dest.exists():
        if not verify(dest, record):
            raise ValueError(f"Existing file differs from pinned bytes; not overwritten: {dest}")
        return "verified-existing"
    if verify_only:
        raise FileNotFoundError(f"Missing pinned input: {dest}")

    repo = record["repository"]
    commit = record["commit"]
    if not repo.startswith("buffedlizard55-lab/") or len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("Invalid pinned mirror repository or commit")
    cache = root / ".cache" / "git-mirrors" / (repo.replace("/", "__") + ".git")
    cache.parent.mkdir(parents=True, exist_ok=True)
    if not cache.exists():
        git("init", "--quiet", "--bare", str(cache))
        git(f"--git-dir={cache}", "remote", "add", "origin", f"https://github.com/{repo}.git")
        git(f"--git-dir={cache}", "config", "remote.origin.promisor", "true")
        git(f"--git-dir={cache}", "config", "remote.origin.partialclonefilter", "blob:none")
    git(f"--git-dir={cache}", "-c", "gc.auto=0", "fetch", "--quiet", "--depth=1", "--filter=blob:none", "origin", commit)
    dest.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(prefix=dest.name + ".", suffix=".partial", dir=dest.parent, delete=False) as out:
            temp_path = Path(out.name)
            for part in record["paths"]:
                if not part or part.startswith("/") or ".." in Path(part).parts:
                    raise ValueError(f"Invalid pinned Git path: {part}")
                print(f"Restoring {record['id']}: {part}", flush=True)
                git(f"--git-dir={cache}", "-c", "gc.auto=0", "show", f"{commit}:{part}", stdout=out)
        if not verify(temp_path, record):
            raise ValueError(f"Restored bytes differ from pin: {record['id']}")
        # Do not clobber a file created while a long download was in progress.
        if dest.exists():
            raise FileExistsError(f"Destination appeared during restore; not overwritten: {dest}")
        temp_path.replace(dest)
        temp_path = None
        return "restored-and-verified"
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true", help="Do not access the network")
    parser.add_argument("--ids", nargs="*", help="Optional IDs to restore; default is all pinned inputs")
    args = parser.parse_args()
    records = json.loads(PINS.read_text())["records"]
    if args.ids:
        requested = set(args.ids)
        missing = requested - {row["id"] for row in records}
        if missing:
            raise SystemExit(f"Unknown input IDs: {sorted(missing)}")
        records = [row for row in records if row["id"] in requested]
    for row in records:
        print(row["id"], restore(row, verify_only=args.verify_only), flush=True)
    print("Mirror integrity verified. Organizer authentication, fold-local evaluation, uniqueness and upload approval remain separate.")


if __name__ == "__main__":
    main()
