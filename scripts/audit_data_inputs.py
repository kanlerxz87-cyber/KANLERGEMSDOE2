#!/usr/bin/env python3
"""Audit local owner-mirrored inputs against their pinned manifest; never download.

A matching SHA-256 proves identity with a recorded mirror, not provenance from
DrivenData, USGS, or DOE. Missing and corrupted files produce a nonzero exit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit(manifest_path: Path, data_dir: Path, group: str = "all") -> dict:
    manifest_path, data_dir = Path(manifest_path), Path(data_dir).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = [e for e in manifest["files"] if group == "all" or e.get("group") == group]
    if not entries:
        raise ValueError(f"No inputs in requested group: {group}")
    ids, destinations = set(), set()
    result = []
    for entry in entries:
        identifier, dest = entry["id"], entry["dest"]
        if identifier in ids or dest in destinations:
            raise ValueError("Manifest contains duplicate input identifiers or destinations")
        ids.add(identifier)
        destinations.add(dest)
        path = (data_dir / dest).resolve()
        if not path.is_relative_to(data_dir) or path == data_dir:
            raise ValueError(f"Input destination escapes data root: {dest}")
        expected = entry["sha256"]
        if len(expected) != 64 or any(ch not in "0123456789abcdef" for ch in expected):
            raise ValueError(f"Invalid expected SHA-256: {identifier}")
        expected_size = entry.get("bytes")
        if expected_size is not None and (type(expected_size) is not int or expected_size < 0):
            raise ValueError(f"Invalid expected byte count: {identifier}")
        row = {"id": identifier, "group": entry["group"], "dest": dest,
               "expected_sha256": expected, "expected_bytes": expected_size}
        if not path.is_file():
            row.update(status="missing", actual_sha256=None, bytes=None)
        else:
            actual, size = sha256_file(path), path.stat().st_size
            status = "hash_mismatch" if actual != expected else (
                "size_mismatch" if expected_size is not None and size != expected_size else "verified"
            )
            row.update(status=status, actual_sha256=actual, bytes=size)
        result.append(row)
    groups = {}
    for name in sorted({r["group"] for r in result}):
        selected = [r for r in result if r["group"] == name]
        groups[name] = {"verified": sum(r["status"] == "verified" for r in selected),
                        "total": len(selected)}
    return {
        "schema": "gems.local-mirror-input-audit.v1",
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_sha256": sha256_file(manifest_path),
        "requested_group": group,
        "groups": groups,
        "complete": all(r["status"] == "verified" for r in result),
        "provenance": "Owner-hosted mirrors only. SHA-256 matching does not authenticate organizer or official-source provenance.",
        "files": result,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, default=ROOT / "registry/data_manifest.json")
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--group", choices=("core", "external", "scored", "all"), default="all")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args(argv)
    report = audit(args.manifest, args.data_dir, args.group)
    text = json.dumps(report, indent=2, allow_nan=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        # Write only the receipt, never the input files.
        receipt = args.out.resolve()
        tmp = args.out.with_suffix(args.out.suffix + ".tmp")
        # Even a group-limited audit must never overwrite an unselected input.
        all_entries = json.loads(args.manifest.read_text(encoding="utf-8"))["files"]
        root = args.data_dir.resolve()
        protected = {args.manifest.resolve()}
        for row in all_entries:
            target = (root / row["dest"]).resolve()
            if not target.is_relative_to(root) or target == root:
                raise ValueError(f"Input destination escapes data root: {row['dest']}")
            protected.add(target)
        if receipt in protected or tmp.resolve() in protected:
            raise ValueError("Receipt must not overwrite the manifest or an input")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(args.out)
    print(json.dumps({k: report[k] for k in ("schema", "checked_utc", "groups", "complete", "provenance")}, indent=2))
    return 0 if report["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
