#!/usr/bin/env python3
"""Stage a fleet-wide TIF registry for KG2-S3-GMV Rule 1 checks (prep, not an experiment).

Fetches small (<=8 MB) prediction rasters from GEMSDOE-family repositories into
$GEMS_REGISTRY_DIR (default /tmp/gmv_reg) with collision-proof names, plus a JSON
manifest. Failures are skipped and logged; the experiment proceeds with whatever
staged plus docs/downloads + ddir/scored. Caps: 12 files/repo, 600 files total.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/gmv_reg")
OUT.mkdir(parents=True, exist_ok=True)

SISTERS = [
    "kanlerxz87-cyber/KANLERGEMSDOE1",
    "kanlerxz87-cyber/KANLERGEMSDOE3",
    "eugboogieman123-ops/EUGGEMSDOE1",
    "eugboogieman123-ops/EUGGEMSDOE2",
    "eugboogieman123-ops/EUGGEMSDOE3",
    "wingbangboozle1-lang/WBGGEMSDOE1",
    "wingbangboozle1-lang/WBGGEMSDOE2",
    "wingbangboozle1-lang/WBGGEMSDOE3",
    "ginnymcfiner23-ux/GINNYGEMSDOE1",
    "ginnymcfiner23-ux/GINNYGEMSDOE2",
    "ginnymcfiner23-ux/GINNYGEMSDOE3",
    "karagemop466-tech/GEMSDOEkarage1",
    "karagemop466-tech/GEMSDOEkarage2",
    "karagemop466-tech/GEMSDOEkarage3",
    "apartanish22-droid/ApartGEMSDOE1",
    "apartanish22-droid/ApartGEMSDOE2",
    "apartanish22-droid/ApartGEMSDOE3",
    "sassnarep3-star/GEMSDOESASS1",
    "sassnarep3-star/GEMSDOESASS2",
    "sassnarep3-star/GEMSDOESASS3",
]

MAX_BYTES = 8_000_000
MAX_PER_REPO = 12
MAX_TOTAL = 600


def _gh_api(args: list[str], timeout: int = 60) -> bytes:
    return subprocess.run(
        ["gh", "api", *args], capture_output=True, check=True, timeout=timeout
    ).stdout


def _repo_list(owner: str) -> list[dict]:
    out = _gh_api([f"repos/{owner}/repos", "--paginate", "-q", ".[].name"])
    return [n for n in out.decode().splitlines() if n.strip()]


def main() -> int:
    t0 = time.time()
    repos: list[str] = []
    try:
        names = subprocess.run(
            ["gh", "repo", "list", "buffedlizard55-lab", "--limit", "300",
             "--json", "name", "-q", ".[].name"],
            capture_output=True, check=True, timeout=120,
        ).stdout.decode().splitlines()
        for n in names:
            nl = n.strip().lower()
            if "gemsdoe" in nl or "gems" in nl:
                repos.append(f"buffedlizard55-lab/{n.strip()}")
    except Exception as exc:  # noqa: BLE001 - staging must never block experiments
        print(f"[stage] owner listing failed: {exc}", flush=True)
    repos += SISTERS
    print(f"[stage] {len(repos)} candidate repos", flush=True)

    manifest: list[dict] = []
    seen_sha: set[str] = set()
    n_skip = 0
    for repo in sorted(set(repos)):
        if len(manifest) >= MAX_TOTAL:
            break
        try:
            info = json.loads(_gh_api([f"repos/{repo}", "-q", "{sha: .default_branch}"]))
            branch = info.get("sha") or "main"
        except Exception:
            n_skip += 1
            continue
        try:
            tree = json.loads(
                _gh_api([f"repos/{repo}/git/trees/{branch}?recursive=1"], timeout=90)
            )
        except Exception:
            n_skip += 1
            continue
        cands = [
            t for t in tree.get("tree", [])
            if t.get("type") == "blob"
            and t.get("path", "").lower().endswith(".tif")
            and ("/docs/downloads/" in ("/" + t["path"]) or "/submissions/" in ("/" + t["path"]))
            and int(t.get("size") or 0) <= MAX_BYTES
        ][:MAX_PER_REPO]
        for t in cands:
            if len(manifest) >= MAX_TOTAL:
                break
            dest = OUT / f"{repo.replace('/', '_')}__{Path(t['path']).name}"
            if dest.exists():
                continue
            try:
                raw = _gh_api(
                    [f"repos/{repo}/contents/{t['path']}?ref={branch}",
                     "-H", "Accept: application/vnd.github.raw"],
                    timeout=180,
                )
            except Exception:
                n_skip += 1
                continue
            sha = hashlib.sha256(raw).hexdigest()
            if sha in seen_sha:
                continue
            seen_sha.add(sha)
            dest.write_bytes(raw)
            manifest.append({"repo": repo, "ref": branch, "path": t["path"],
                             "file": dest.name, "bytes": len(raw), "sha256": sha})
    man_path = ROOT / "evidence" / "gmv_registry_manifest.json"
    man_path.write_text(json.dumps(
        {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
         "out_dir": str(OUT), "n_files": len(manifest),
         "repos_attempted": len(repos), "skipped": n_skip,
         "elapsed_s": round(time.time() - t0, 1), "files": manifest},
        indent=1) + "\n", encoding="utf-8")
    print(f"[stage] staged {len(manifest)} files in {time.time()-t0:.0f}s "
          f"(skipped {n_skip}) -> {man_path.name}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
