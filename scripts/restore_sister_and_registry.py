#!/usr/bin/env python3
"""Fetch and cache comparison GeoTIFFs across Focus, Archive, and Sister GEMSDOE repositories into .cache/gems_data/scored_extra/.

Covers:
  - All entries in registry/comparison_registry.json (9 focus sites: GEMSDOE24..36)
  - All active sister repositories in the 2026-10-27 prompt:
      KANLERGEMSDOE1..3, WBGGEMSDOE1..3, EUGGEMSDOE1..3, GINNYGEMSDOE1..3,
      GEMSDOEkarage1..3, ApartGEMSDOE1..3, GEMSDOESASS1..3
  - High-scoring non-H19-5 benchmark sites: GEMSDOE70, GEMSDOE73, GEMSDOE75, GEMSDOE76, GEMSDOE82, GEMSDOE91, GEMSDOE92

All bulk rasters are stored strictly inside ignored `.cache/gems_data/scored_extra/` (zero Git bloat).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems32.paths import data_dir  # noqa: E402

SISTER_REPOS: list[tuple[str, str]] = [
    ("KANLERGEMSDOE1", "kanlerxz87-cyber/KANLERGEMSDOE1"),
    ("KANLERGEMSDOE3", "kanlerxz87-cyber/KANLERGEMSDOE3"),
    ("EUGGEMSDOE1", "eugboogieman123-ops/EUGGEMSDOE1"),
    ("EUGGEMSDOE2", "eugboogieman123-ops/EUGGEMSDOE2"),
    ("EUGGEMSDOE3", "eugboogieman123-ops/EUGGEMSDOE3"),
    ("WBGGEMSDOE1", "wingbangboozle1-lang/WBGGEMSDOE1"),
    ("WBGGEMSDOE2", "wingbangboozle1-lang/WBGGEMSDOE2"),
    ("WBGGEMSDOE3", "wingbangboozle1-lang/WBGGEMSDOE3"),
    ("GINNYGEMSDOE1", "ginnymcfiner23-ux/GINNYGEMSDOE1"),
    ("GINNYGEMSDOE2", "ginnymcfiner23-ux/GINNYGEMSDOE2"),
    ("GINNYGEMSDOE3", "ginnymcfiner23-ux/GINNYGEMSDOE3"),
    ("GEMSDOEkarage1", "karagemop466-tech/GEMSDOEkarage1"),
    ("GEMSDOEkarage2", "karagemop466-tech/GEMSDOEkarage2"),
    ("GEMSDOEkarage3", "karagemop466-tech/GEMSDOEkarage3"),
    ("ApartGEMSDOE1", "apartanish22-droid/ApartGEMSDOE1"),
    ("ApartGEMSDOE2", "apartanish22-droid/ApartGEMSDOE2"),
    ("ApartGEMSDOE3", "apartanish22-droid/ApartGEMSDOE3"),
    ("GEMSDOESASS1", "sassnarep3-star/GEMSDOESASS1"),
    ("GEMSDOESASS2", "sassnarep3-star/GEMSDOESASS2"),
    ("GEMSDOESASS3", "sassnarep3-star/GEMSDOESASS3"),
    ("GEMSDOE70", "buffedlizard55-lab/GEMSDOE70"),
    ("GEMSDOE73", "buffedlizard55-lab/GEMSDOE73"),
    ("GEMSDOE75", "buffedlizard55-lab/GEMSDOE75"),
    ("GEMSDOE76", "buffedlizard55-lab/GEMSDOE76"),
    ("GEMSDOE82", "buffedlizard55-lab/GEMSDOE82"),
    ("GEMSDOE91", "buffedlizard55-lab/GEMSDOE91"),
    ("GEMSDOE92", "buffedlizard55-lab/GEMSDOE92"),
]

SKIP_SUBSTRINGS = (
    "bridge/",
    "external/",
    "inputs/",
    "data/official/",
    "data/scored/",
    "data/registry_rasters/",
    "template_grid",
    "parent_R0",
    "reference/",
    "training_features",
    "existing_faults",
    "sample_submission",
    "labels.tif",
)


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _gh_raw_download(owner_repo: str, ref: str, rel_path: str, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        with tmp.open("wb") as out:
            r = subprocess.run(
                [
                    "gh",
                    "api",
                    f"repos/{owner_repo}/contents/{rel_path}?ref={ref}",
                    "-H",
                    "Accept: application/vnd.github.raw",
                ],
                stdout=out,
                stderr=subprocess.DEVNULL,
                timeout=90,
                check=False,
            )
        if r.returncode == 0 and tmp.exists() and tmp.stat().st_size > 1024:
            tmp.replace(dest)
            return True
    except Exception:
        pass
    tmp.unlink(missing_ok=True)
    return False


def main() -> int:
    ddir = data_dir()
    extra = ddir / "scored_extra"
    extra.mkdir(parents=True, exist_ok=True)

    # Copy focus_20261027 witnesses into scored_extra if present
    fdir = ddir / "focus_20261027"
    if fdir.exists():
        for p in fdir.glob("*.tif"):
            dst = extra / p.name
            if not dst.exists():
                dst.write_bytes(p.read_bytes())

    tasks: list[tuple[str, str, str, Path, str | None]] = []

    # 1. Comparison registry entries (9 focus repos)
    comp_reg_path = ROOT / "registry" / "comparison_registry.json"
    if comp_reg_path.exists():
        comp = json.loads(comp_reg_path.read_text(encoding="utf-8"))
        for e in comp.get("entries", []):
            repo_short = e["primary_repo"]
            rel_path = e["rel_path"]
            fname = Path(rel_path).name
            dest = extra / f"REG__{repo_short}__{e['sha256'][:12]}__{fname}"
            if dest.exists() and _sha256(dest) == e["sha256"]:
                continue
            tasks.append((f"buffedlizard55-lab/{repo_short}", "main", rel_path, dest, e["sha256"]))

    # 2. Live tree discovery across all 27 sister & benchmark repos
    sister_inventory: list[dict] = []
    for label, owner_repo in SISTER_REPOS:
        p_sha = subprocess.run(
            ["gh", "api", f"repos/{owner_repo}/commits/main", "--jq", ".sha"],
            capture_output=True,
            text=True,
            check=False,
        )
        if p_sha.returncode != 0 or not p_sha.stdout.strip():
            sister_inventory.append({"site": label, "owner_repo": owner_repo, "commit_sha": None, "tif_count": 0, "paths": []})
            continue
        csha = p_sha.stdout.strip()
        p_tree = subprocess.run(
            ["gh", "api", f"repos/{owner_repo}/git/trees/{csha}?recursive=1"],
            capture_output=True,
            text=True,
            check=False,
        )
        if p_tree.returncode != 0:
            sister_inventory.append({"site": label, "owner_repo": owner_repo, "commit_sha": csha, "tif_count": 0, "paths": []})
            continue
        tree = json.loads(p_tree.stdout).get("tree", [])
        cand_tifs = [
            x["path"]
            for x in tree
            if x.get("type") == "blob"
            and x["path"].endswith(".tif")
            and x.get("size", 0) < 25_000_000
            and not any(k in x["path"] for k in SKIP_SUBSTRINGS)
        ]
        # Cap GEMSDOE91/92 archive sprawl to recent/downloads tifs while keeping 100% of sister repos
        if label in ("GEMSDOE91", "GEMSDOE92") and len(cand_tifs) > 25:
            prioritized = [p for p in cand_tifs if any(t in p for t in ("S18-UNIQUE", "lbmc1", "s17-lftg", "s17-cwpc", "s22-omtj", "listricdip"))]
            others = [p for p in cand_tifs if p not in prioritized]
            cand_tifs = prioritized + others[-20:]

        sister_inventory.append({
            "site": label,
            "owner_repo": owner_repo,
            "commit_sha": csha,
            "tif_count": len(cand_tifs),
            "paths": cand_tifs,
        })
        for rel in cand_tifs:
            fname = Path(rel).name
            path_tag = hashlib.sha256(rel.encode()).hexdigest()[:8]
            dest = extra / f"{label}__{path_tag}__{fname}"
            if dest.exists() and dest.stat().st_size > 1024:
                continue
            tasks.append((owner_repo, csha, rel, dest, None))

    print(f"Queued {len(tasks)} comparison GeoTIFF downloads into {extra}...", flush=True)

    ok_count = 0
    fail_count = 0

    def _worker(t: tuple[str, str, str, Path, str | None]) -> bool:
        owner_repo, ref, rel_path, dest, exp_sha = t
        ok = _gh_raw_download(owner_repo, ref, rel_path, dest)
        if not ok:
            return False
        if exp_sha is not None and _sha256(dest) != exp_sha:
            dest.unlink(missing_ok=True)
            return False
        return True

    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = [pool.submit(_worker, t) for t in tasks]
        for fut in as_completed(futs):
            if fut.result():
                ok_count += 1
            else:
                fail_count += 1

    inv_out = ddir / "sister_tree_inventory_20261027.json"
    inv_out.write_text(json.dumps(sister_inventory, indent=2) + "\n", encoding="utf-8")
    total_cached = len(list(extra.glob("*.tif")))
    print(f"Downloaded {ok_count} new rasters ({fail_count} unavailable/moved on main); total cached in scored_extra: {total_cached}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
