#!/usr/bin/env python3
"""Fetch every USER-REPORTED leaderboard-scored raster listed in the LB ledger(s) and SHA-256 verify it.

Ledger provenance: ``registry/lb_ledger_gemsdoe32_20261026.json`` is a byte copy of
``buffedlizard55-lab/GEMSDOE32/evidence/live_ledger_rasters.json`` (generated 2026-10-26T20:26:59Z),
which pins (repo, commit, path, sha256) for 118 owner-reported live-scored rasters.
``registry/lb_ledger_additions_20261027.json`` adds later USER-REPORTED scores from the standing
brief. Scores are USER-REPORTED, never ORGANIZER-CONFIRMED (no submission-page receipts exist).
Files are written under ``$GEMS_DATA_DIR/ledger`` (ignored by git).
"""
from __future__ import annotations

import hashlib
import json
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


def load_rows() -> list[dict]:
    rows = []
    base = json.loads((ROOT / "registry/lb_ledger_gemsdoe32_20261026.json").read_text())
    for r in base["rows"]:
        if r.get("status") == "ok":
            rows.append({"site": r["site"], "submission": r["submission"], "score": float(r["score"]),
                         "repo": r["repo"] if "/" in r["repo"] else f"{OWNER}/{r['repo']}",
                         "ref": r["ref"], "path": r["path"], "sha256": r["sha256"], "source": "GEMSDOE32-ledger"})
    add = ROOT / "registry/lb_ledger_additions_20261027.json"
    if add.exists():
        for r in json.loads(add.read_text())["rows"]:
            rows.append(dict(r, source="KG2-S3-additions"))
    return rows


def fetch(row: dict, dest: Path) -> str:
    if dest.exists() and sha256_file(dest) == row["sha256"]:
        return "present"
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".partial")
    with tmp.open("wb") as out:
        subprocess.run(["gh", "api", f"repos/{row['repo']}/contents/{row['path']}?ref={row['ref']}",
                        "-H", "Accept: application/vnd.github.raw"], stdout=out, check=True,
                       stderr=subprocess.DEVNULL)
    got = sha256_file(tmp)
    if got != row["sha256"]:
        tmp.unlink(missing_ok=True)
        return f"HASH-MISMATCH {got[:12]}"
    tmp.replace(dest)
    return "restored"


def main() -> int:
    rows = load_rows()
    out_dir = data_dir() / "ledger"

    def one(r):
        dest = out_dir / r["sha256"][:16] / Path(r["path"]).name
        try:
            st = fetch(r, dest)
        except Exception as exc:  # noqa: BLE001 - record and continue; summary fails closed below
            st = f"unavailable: {type(exc).__name__}"
        return dict(r, local=str(dest), status=st)

    with ThreadPoolExecutor(max_workers=6) as pool:
        res = list(pool.map(one, rows))
    ok = [r for r in res if r["status"] in ("present", "restored")]
    receipt = {"schema": "kg2.lb_ledger_fetch.v1", "n_rows": len(res), "n_verified": len(ok),
               "evidence_class_of_scores": "USER-REPORTED (no organizer receipts)", "rows": res}
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data/lb_ledger_fetch_receipt.json").write_text(json.dumps(receipt, indent=1) + "\n")
    for r in res:
        if r["status"] not in ("present", "restored"):
            print("WARN", r["site"], r["submission"], r["status"])
    print(f"verified {len(ok)}/{len(res)} ledger rasters into {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
