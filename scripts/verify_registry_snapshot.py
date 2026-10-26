#!/usr/bin/env python3
"""Validate the shared registry cache against immutable Git tree blob IDs.

The upstream registry refresher may reuse same-sized cached bytes. This is an
independent integrity check, not a fork of its evaluator or writer. It validates
complete trees, restores any stale blob at the pinned commit, and writes a
separate receipt. GitHub data inputs and private/unpublished submissions are not
claimed to be part of this public, nine-repository scope.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

PREFIXES = ("docs/", "inputs/", "archive/", "evidence/")
MAX_BYTES = 8_000_000
OWNER = "buffedlizard55-lab"
FOCUS = ("GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36")


def gh_json(endpoint: str) -> dict:
    return json.loads(subprocess.run(["gh", "api", endpoint], check=True, capture_output=True, text=True).stdout)


def digest(path: Path) -> tuple[str, str]:
    size = path.stat().st_size
    gh = hashlib.sha1(f"blob {size}\0".encode())
    sha = hashlib.sha256()
    with path.open("rb") as inp:
        for chunk in iter(lambda: inp.read(1 << 20), b""):
            gh.update(chunk)
            sha.update(chunk)
    return gh.hexdigest(), sha.hexdigest()


def verify(template: Path, manifest_path: Path, out: Path) -> dict:
    template = template.resolve()
    manifest = json.loads(manifest_path.read_text())
    if set(manifest.get("refs", {})) != set(FOCUS):
        raise ValueError("Registry must contain exactly the nine specified focus repos")
    if manifest.get("n_failed") != 0 or any(e.get("status") != "ok" for e in manifest["rasters"]):
        raise ValueError("Shared registry has failed or missing entries")
    by_repo = {repo: {} for repo in FOCUS}
    for entry in manifest["rasters"]:
        repo = entry["repo"]
        if repo not in by_repo or entry["ref"] != manifest["refs"][repo]:
            raise ValueError("Registry owner, repository or pinned revision mismatch")
        if entry["path"] in by_repo[repo]:
            raise ValueError("Duplicate path in registry")
        by_repo[repo][entry["path"]] = entry
    bad_size, refetches, outside = [], [], {}
    for repo in FOCUS:
        ref = manifest["refs"][repo]
        tree = gh_json(f"repos/{OWNER}/{repo}/git/trees/{ref}?recursive=1")
        if tree.get("truncated"):
            raise ValueError(f"GitHub tree is truncated for {repo}; registry completeness unknown")
        eligible = {}
        other = []
        for item in tree["tree"]:
            path = item["path"]
            if item.get("type") != "blob" or not path.lower().endswith((".tif", ".tiff")):
                continue
            if path.startswith(PREFIXES):
                if item.get("size", MAX_BYTES + 1) <= MAX_BYTES:
                    eligible[path] = item
                else:
                    bad_size.append(f"{repo}/{path}")
            else:
                other.append(path)
        outside[repo] = other
        if set(eligible) != set(by_repo[repo]):
            raise ValueError(f"Registry path inventory differs from pinned tree for {repo}")
        for path, blob in eligible.items():
            e = by_repo[repo][path]
            local = (template / e["local"]).resolve()
            if not local.is_relative_to(template):
                raise ValueError("Registry local path escapes pinned template cache")
            if not local.exists() or digest(local)[0] != blob["sha"]:
                # Network fetching is limited to the exact immutable GitHub blob.
                local.parent.mkdir(parents=True, exist_ok=True)
                part = local.with_suffix(local.suffix + ".verify-partial")
                try:
                    with part.open("wb") as fout:
                        subprocess.run(["gh", "api", f"repos/{OWNER}/{repo}/contents/{path}?ref={ref}", "-H", "Accept: application/vnd.github.raw"], stdout=fout, check=True)
                    if digest(part)[0] != blob["sha"]:
                        raise ValueError(f"Downloaded Git blob mismatch: {repo}/{path}")
                    part.replace(local)
                    refetches.append(f"{repo}/{path}")
                finally:
                    part.unlink(missing_ok=True)
            g, h = digest(local)
            if g != blob["sha"] or local.stat().st_size != blob["size"]:
                raise ValueError(f"Blob verification failed for {repo}/{path}")
            e["sha256"] = h
            e["bytes"] = blob["size"]
            e["git_blob_sha1"] = g
    if bad_size:
        raise ValueError(f"Potential omitted large rasters in registry prefixes: {bad_size}")
    result = {
        "scope": "Nine public repos, pinned trees; TIFFs under docs/, inputs/, archive/, evidence/ up to 8 MB; no private/unlinked/later files",
        "refs": manifest["refs"],
        "rasters_verified": len(manifest["rasters"]),
        "corrected_same_size_or_missing_cache_entries": refetches,
        "raster_paths_outside_scope": outside,
        "rasters": manifest["rasters"],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    tmp.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    tmp.replace(out)
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--template", type=Path, default=Path(".cache/template32"))
    ap.add_argument("--manifest", type=Path, default=Path(".cache/template32/registry/focus_registry_manifest.json"))
    ap.add_argument("--out", type=Path, default=Path(".cache/audit/verified-registry.json"))
    args = ap.parse_args()
    result = verify(args.template, args.manifest, args.out)
    print(json.dumps({k: v for k, v in result.items() if k != "rasters"}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
