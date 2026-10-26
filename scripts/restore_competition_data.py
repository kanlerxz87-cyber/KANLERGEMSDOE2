#!/usr/bin/env python3
"""Restore integrity-pinned, public peer mirrors; they are NOT organizer-authenticated.

Downloads GitHub codeload archives (not the rate-limited contents API), extracts
only explicitly named regular files, verifies SHA-256 and size before atomic
installation, and never extracts arbitrary archive paths. No synthetic fallback.
Large inputs stay in ignored data/ and are not committed by this script.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tarfile
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research/snapshots/GEMSDOE32/registry/data_manifest.json"
CORE = ("training_features", "labels", "existing_faults", "sample_submission")
EXTRA = (
    {
        "id": "continuous_witness",
        "repo": "buffedlizard55-lab/GEMSDOE48",
        "ref": "268ec599f51c517cc3485da077c24d83af5be81d",
        "path": "docs/downloads/gemsdoe48-h58-continuous-pignistic-20261008T175914Z-e58.tif",
        "dest": "registry/blockers/gemsdoe48-h58-continuous-pignistic-20261008T175914Z-e58.tif",
        "sha256": "59ef8e7d8374e228bc1e41376f03fc67dd5b8a5e6804885a1ae802f399140b89",
        "bytes": 1399672,
    },
    {
        "id": "lattice_witness",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "path": "inputs/calibration/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif",
        "dest": "registry/blockers/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif",
        "sha256": "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2",
        "bytes": 1706456,
    },
)


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verified(path, row):
    path = Path(path)
    return path.is_file() and path.stat().st_size == row["bytes"] and sha256_file(path) == row["sha256"]


def extract_selected(archive, archive_root, wanted, tempdir):
    """Stream selected files to temp paths, rejecting duplicate/missing/non-file entries."""
    paths = {}
    with tarfile.open(fileobj=archive, mode="r|gz") as tar:
        for member in tar:
            prefix = archive_root + "/"
            if not member.name.startswith(prefix):
                continue
            rel = member.name[len(prefix):]
            if rel not in wanted:
                continue
            if rel in paths or not member.isfile() or member.size < 1:
                raise ValueError(f"Invalid or duplicate archive member: {rel}")
            # No member name is used as an output path: archive traversal is impossible.
            path = Path(tempdir) / f"part-{len(paths):04d}"
            source = tar.extractfile(member)
            if source is None:
                raise ValueError(f"Cannot read archive member: {rel}")
            with source, path.open("wb") as out:
                shutil.copyfileobj(source, out, length=1024 * 1024)
            paths[rel] = path
    missing = set(wanted) - set(paths)
    if missing:
        raise ValueError(f"Pinned archive lacks requested members: {sorted(missing)}")
    return paths


def restore(rows, data_dir):
    data_dir = Path(data_dir).resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    destinations = set()
    for row in rows:
        dest = (data_dir / row["dest"]).resolve()
        if not dest.is_relative_to(data_dir) or dest == data_dir or dest in destinations:
            raise ValueError(f"Unsafe or duplicate restore destination: {row['dest']}")
        destinations.add(dest)
    pending = [row for row in rows if not verified(data_dir / row["dest"], row)]
    groups = {}
    for row in pending:
        groups.setdefault((row["repo"], row["ref"]), []).append(row)
    for (repo, ref), group in groups.items():
        wanted = {part for row in group for part in row.get("parts", [row.get("path")])}
        if None in wanted:
            raise ValueError(f"Missing pinned source path for {repo}")
        url = f"https://codeload.github.com/{repo}/tar.gz/{ref}"
        archive_root = repo.split("/")[-1] + "-" + ref
        print(f"Restoring {len(group)} pinned item(s) from {repo}@{ref[:8]}...", flush=True)
        with tempfile.TemporaryDirectory(prefix=".restore-", dir=data_dir) as tmp:
            request = urllib.request.Request(url, headers={"User-Agent": "KANLERGEMS-data-restorer"})
            with urllib.request.urlopen(request, timeout=120) as response:
                parts = extract_selected(response, archive_root, wanted, tmp)
            # Verify every reconstructed output before replacing any of this group's files.
            ready = []
            for index, row in enumerate(group):
                assembled = Path(tmp) / f"output-{index:04d}"
                with assembled.open("wb") as out:
                    for name in row.get("parts", [row.get("path")]):
                        with parts[name].open("rb") as src:
                            shutil.copyfileobj(src, out, length=1024 * 1024)
                if not verified(assembled, row):
                    raise ValueError(f"Integrity check failed for {row['id']}; destination not replaced")
                ready.append((assembled, data_dir / row["dest"]))
            for source, dest in ready:
                dest.parent.mkdir(parents=True, exist_ok=True)
                source.replace(dest)
                print(f"Verified {dest.relative_to(data_dir)}", flush=True)
    return {row["id"]: verified(data_dir / row["dest"], row) for row in rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data",
                        help="ignored destination directory for pinned mirrors")
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    by_id = {row["id"]: row for row in manifest["files"]}
    rows = [by_id[name] for name in CORE] + list(EXTRA)
    checks = restore(rows, args.data_dir)
    print(json.dumps({"integrity_checks": checks, "organizer_authenticated": False,
                      "provenance": "public peer mirror; compare with organizer data when available"}, indent=2))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
