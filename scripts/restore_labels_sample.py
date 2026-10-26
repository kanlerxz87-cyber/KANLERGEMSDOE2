#!/usr/bin/env python3
"""Restore competition rasters from hash-pinned peer mirrors via git sparse clone.

Why git, not the GitHub contents API: on 2026-10-26 the sandbox GH token was
invalid and api.github.com returned 403 (rate limit). Anonymous git clone of
the public mirror repos works and every byte is verified against the pins in
research/snapshots/GEMSDOE32/registry/data_manifest.json (fails closed).

Mirrors (integrity-pinned, NOT organizer-authenticated; DrivenData data page
https://www.drivendata.org/competitions/306/competition-doe-gems/data/ is
login-walled):
  buffedlizard55-lab/GEMSDOE24  data/bridge/{labels,existing_faults,sample_submission}.tif
  buffedlizard55-lab/GEMSDOE    data/bridge/gems-geodawn-numerical-features.tif.part-000..004
                                -> data/training_features.tif (19 bands)
External stacks under data/external/ are already tracked in this repo.
"""
import hashlib, pathlib, shutil, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
PINS = {
    "sample_submission.tif": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
    "labels.tif": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "existing_faults.tif": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "training_features.tif": "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5",
}

def sha(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()

def sparse_clone(repo: str, dest: pathlib.Path):
    subprocess.run(["git", "clone", "--filter=blob:none", "--sparse", "--depth", "1",
                    f"https://github.com/{repo}.git", str(dest)], check=True,
                   env={"GIT_TERMINAL_PROMPT": "0", "PATH": "/usr/bin:/bin:/usr/local/bin"})
    subprocess.run(["git", "-C", str(dest), "sparse-checkout", "set", "data/bridge"], check=True)

def main():
    need = [k for k, v in PINS.items()
            if not (ROOT / "data" / k).exists() or sha(ROOT / "data" / k) != v]
    if not need:
        print("all competition rasters present, sha ok"); return
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        if any(k != "training_features.tif" for k in need):
            sparse_clone("buffedlizard55-lab/GEMSDOE24", td / "g24")
            for k in need:
                if k != "training_features.tif":
                    shutil.copyfile(td / "g24" / "data" / "bridge" / k, ROOT / "data" / k)
        if "training_features.tif" in need:
            sparse_clone("buffedlizard55-lab/GEMSDOE", td / "gdoe")
            parts = sorted((td / "gdoe" / "data" / "bridge").glob("*.part-*"))
            if len(parts) != 5:
                raise SystemExit(f"expected 5 parts, got {len(parts)}")
            with open(ROOT / "data" / "training_features.tif", "wb") as out:
                for p in parts:
                    out.write(p.read_bytes())
    for k, v in PINS.items():
        got = sha(ROOT / "data" / k)
        if got != v:
            raise SystemExit(f"SHA MISMATCH {k}: got {got} want {v}")
        print(k, "sha ok")

if __name__ == "__main__":
    main()
