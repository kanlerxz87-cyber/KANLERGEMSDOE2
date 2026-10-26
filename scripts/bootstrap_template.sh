#!/usr/bin/env bash
# Restore the pinned shared tools and hash-verified owner mirrors. No uploads.
set -euo pipefail
cd "$(dirname "$0")/.."
COMMIT=07806249f4ed3efe70b4fbf866183c32392b7853
ARCHIVE_SHA=74421783a733593d61893de323c3dfd6f4a2cf4a2af2d07bdd872e17bc3df12d
mkdir -p .cache/audit
if [[ ! -f .cache/template32/.arena-template-commit ]]; then
  if [[ -d .cache/template32 && -n "$(ls -A .cache/template32)" ]]; then
    echo 'Unpinned template cache exists; move it aside or use a clean workspace.' >&2; exit 1
  fi
  mkdir -p .cache/template32
  curl --fail --location --retry 2 --connect-timeout 10 \
    "https://codeload.github.com/buffedlizard55-lab/GEMSDOE32/tar.gz/$COMMIT" \
    -o .cache/template32.tar.gz.partial
  echo "$ARCHIVE_SHA  .cache/template32.tar.gz.partial" | sha256sum --check --status || { echo 'Template archive hash mismatch' >&2; exit 1; }
  tar -xzf .cache/template32.tar.gz.partial --strip-components=1 -C .cache/template32
  mv .cache/template32.tar.gz.partial .cache/template32.tar.gz
  printf '%s\n' "$COMMIT" > .cache/template32/.arena-template-commit
fi
[[ "$(cat .cache/template32/.arena-template-commit)" == "$COMMIT" ]] || { echo 'Wrong template revision' >&2; exit 1; }
if [[ ! -x .venv/bin/python ]]; then python -m venv .venv; fi
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python .cache/template32/scripts/restore_data.py --group core --target-dir .cache/audit/core
.venv/bin/python .cache/template32/scripts/restore_data.py --group external --target-dir .cache/audit/core
gh api -H 'Accept: application/vnd.github.raw+json' \
  repos/buffedlizard55-lab/13GEMSDOE/git/blobs/81c802618e6d46c6d62289d856ae74439439bbc6 \
  > .cache/audit/lattice.tif.partial
printf '%s  %s\n' b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2 .cache/audit/lattice.tif.partial | sha256sum --check --status || { echo 'Lattice hash mismatch' >&2; exit 1; }
mv .cache/audit/lattice.tif.partial .cache/audit/lattice.tif
.venv/bin/python .cache/template32/scripts/fetch_focus_registry.py --jobs 6
.venv/bin/python scripts/verify_registry_snapshot.py --manifest data/registry-lock.json
.venv/bin/python scripts/audit_priority.py
if [[ "${1:-}" == "--build-stack" ]]; then
  .venv/bin/python scripts/prepare_data.py
elif [[ $# -ne 0 ]]; then
  echo 'Use no arguments or --build-stack.' >&2; exit 2
fi
printf '\nRestored pinned public owner mirrors. These hashes do NOT authenticate organizer inputs.\n'
printf 'The H1 lane is already stopped; no TIFF or competition submission was generated.\n'
