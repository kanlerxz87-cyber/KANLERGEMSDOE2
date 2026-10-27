#!/usr/bin/env python3
"""Restore the focus-site submission GeoTIFFs that the executive summary links to.

Why: docs/executive-summary.html and README link 12 focus-site GeoTIFFs under docs/downloads/
that were never committed (broken links). This script resolves each listed submission stem
against the owner repo tree (buffedlizard55-lab/GEMSDOE<NN>, via the GitHub API with gh),
downloads the exact file, and writes SHA-256 + size + provenance to
evidence/focus_site_files.json. Nothing is trusted from the page text: every byte is hashed.

Scores are USER-REPORTED (copied from the task prompt listing); they are NOT organizer receipts.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "downloads"  # flat, matching the existing download links
EVIDENCE = ROOT / "evidence" / "focus_site_files.json"

# (site, repo, submission stem as listed in the prompt, user-reported score, listing order)
# Only the top-scoring listed submissions per site are fetched, plus the top file's -zeros sibling
# if one exists, so each site has a concrete downloadable file.
CANDIDATES = [
    ("GEMSDOE24", "GEMSDOE24", "h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan", 0.2477),
    ("GEMSDOE25", "GEMSDOE25", "dotted-h19-5-d2-8-20261002-e56ea318af89-nan", 0.2600),
    ("GEMSDOE27", "GEMSDOE27", "topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan", 0.2449),
    ("GEMSDOE28", "GEMSDOE28", "h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan", 0.2710),
    ("GEMSDOE30", "GEMSDOE30", "d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca", 0.2600),
    ("GEMSDOE31", "GEMSDOE31", "h27-4-solo-d28-20261004-8acb75e1-nan", 0.2708),
    ("GEMSDOE32", "GEMSDOE32", "h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros", 0.2778),
    ("GEMSDOE33", "GEMSDOE33", "h33d-analog-tip-stepover-r30-20261004-cb490425926e", 0.2632),
    ("GEMSDOE36", "GEMSDOE36", "anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros", 0.2750),
]

# Latest-run alternates that the executive summary already links (not top-scoring listings).
# Score None = no user-reported score in the prompt listing for this exact file.
ALTERNATES = [
    ("GEMSDOE24", "GEMSDOE24", "gems24-dprf1-stitched-oof-tworegime-20261026-81849d67c8bf-zeros", None),
    ("GEMSDOE27", "GEMSDOE27", "gems27-h31-drcg-wl-celf28-20261026-cf8e1bbef244-allfinite", 0.2250),
    ("GEMSDOE31", "GEMSDOE31", "gemsdoe31-h31x-piedmont-junction-37654-20261026-5a956da9-zeros", None),
]


def gh_json(path: str) -> dict:
    out = subprocess.run(["gh", "api", path], check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def tree_paths(repo: str) -> list[dict]:
    # Owner repos are on the default branch; use the branch tree so the lookup is ref-stable.
    t = gh_json(f"repos/buffedlizard55-lab/{repo}/git/trees/HEAD?recursive=1")
    return [e for e in t.get("tree", []) if e.get("type") == "blob"]


def find_sibling(entries: list[dict], nan_name: str) -> dict | None:
    """Portal-safe sibling of a '-nan.tif' file: same stem with '-zeros' or '-allfinite' instead."""
    base = nan_name[: -len("-nan.tif")]
    for suffix in ("-zeros.tif", "-allfinite.tif"):
        hits = [e for e in entries if Path(e["path"]).name.lower() == (base + suffix).lower()]
        if len(hits) == 1:
            return hits[0]
    return None


def find_tif(entries: list[dict], stem: str) -> dict | None:
    """Exact-suffix match: the listed stem must end the filename right before '.tif'.

    Repo filenames may carry a site prefix (e.g. 'GEMSDOE33-' or 'gemsdoe30-'), so we match the
    suffix, not the start. '-nanoutside' variants do not end with the stem, so they cannot collide.
    """
    target = (stem + ".tif").lower()
    hits = [e for e in entries if Path(e["path"]).name.lower().endswith(target)]
    return hits[0] if len(hits) == 1 else None


def download_raw(repo: str, path: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as f:
        subprocess.run(
            ["gh", "api", f"repos/buffedlizard55-lab/{repo}/contents/{path}", "-H", "Accept: application/vnd.github.raw"],
            stdout=f, check=True,
        )


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    sys.path.insert(0, str(ROOT / "src"))
    from gems.protocol import retired_legacy_pipeline

    retired_legacy_pipeline("fetch_focus_submissions (unpinned HEAD; use the pinned re-audit)")
    records = []
    cache: dict[str, list[dict]] = {}
    jobs = [(s_, r_, st, sc, "listed") for s_, r_, st, sc in CANDIDATES]
    jobs += [(s_, r_, st, sc, "alternate") for s_, r_, st, sc in ALTERNATES]
    for site, repo, stem, score, role in jobs:
        if repo not in cache:
            cache[repo] = tree_paths(repo)
        ent = find_tif(cache[repo], stem)
        if ent is None:
            print(f"UNRESOLVED {site}: {stem}", file=sys.stderr)
            records.append({"site": site, "listed_stem": stem, "status": "unresolved"})
            continue
        name = Path(ent["path"]).name
        dest = OUT_DIR / name
        download_raw(repo, ent["path"], dest)
        if role == "listed" and name.lower().endswith("-nan.tif"):
            sib = find_sibling(cache[repo], name)
            if sib is not None:
                sib_dest = OUT_DIR / Path(sib["path"]).name
                download_raw(repo, sib["path"], sib_dest)
                records.append({
                    "site": site, "role": "portal-safe sibling of " + name,
                    "listed_stem": stem, "user_reported_score": None,
                    "score_label": "NO SCORE LISTED (same stem as the -nan file; check dot identity in audit)",
                    "source_repo": f"https://github.com/buffedlizard55-lab/{repo}",
                    "source_path": sib["path"], "local_path": sib_dest.relative_to(ROOT).as_posix(),
                    "bytes": sib_dest.stat().st_size, "sha256": sha256(sib_dest), "status": "downloaded",
                })
                print(f"{site}: sibling {Path(sib['path']).name} sha256={records[-1]['sha256'][:12]}")
        size = dest.stat().st_size
        if size != ent.get("size", size):
            print(f"SIZE MISMATCH {site} {name}: {size} != {ent.get('size')}", file=sys.stderr)
            return 2
        rec = {
            "site": site,
            "role": role,
            "listed_stem": stem,
            "user_reported_score": score,
            "score_label": "USER-REPORTED (prompt listing; not organizer-confirmed)",
            "source_repo": f"https://github.com/buffedlizard55-lab/{repo}",
            "source_path": ent["path"],
            "local_path": dest.relative_to(ROOT).as_posix(),
            "bytes": size,
            "sha256": sha256(dest),
            "status": "downloaded",
        }
        records.append(rec)
        print(f"{site}: {name} {size} B sha256={rec['sha256'][:12]}")

    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps({"schema": "kanlergemsdoe2.focus_site_files.v1", "records": records}, indent=2) + "\n")
    return 0 if all(r["status"] == "downloaded" for r in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
