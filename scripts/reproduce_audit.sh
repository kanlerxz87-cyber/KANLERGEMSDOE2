#!/usr/bin/env bash
# Restore public, hash-pinned mirrors and rerun the evidence-only audit.
# Does not build a candidate, authenticate to DrivenData, or spend a slot.
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$PWD"
REF=1d99d73fe14d9a87126ffca2db52c69336d6099b
CACHE_DIR="${GEMS_CACHE_DIR:-$ROOT/.cache}"
TEMPLATE="$CACHE_DIR/GEMSDOE33"
DATA="$CACHE_DIR/owner-data"
LATTICE="$CACHE_DIR/registry-lattice-nan.tif"
for tool in python gh curl tar sha256sum; do command -v "$tool" >/dev/null || { echo "Missing required tool: $tool" >&2; exit 1; }; done
python -c 'import numpy, scipy, rasterio, sklearn' || { echo 'Install requirements.txt first' >&2; exit 1; }
mkdir -p "$CACHE_DIR"
if [[ ! -e "$TEMPLATE" ]]; then
  stage="$(mktemp -d "$CACHE_DIR/template-stage.XXXXXXXX")"
  trap 'rm -rf "$stage"' EXIT
  curl -fsSL "https://codeload.github.com/buffedlizard55-lab/GEMSDOE33/tar.gz/$REF" -o "$stage/template.tar.gz"
  mkdir "$stage/tree"
  tar -xzf "$stage/template.tar.gz" -C "$stage/tree" --strip-components=1
  mv "$stage/tree" "$TEMPLATE"
fi
# Refuse a changed/partial template rather than silently replacing shared code.
(cd "$TEMPLATE" && sha256sum -c "$ROOT/registry/template-files.sha256")
python scripts/reproduce_template_defects.py --shared "$TEMPLATE" --out evidence/template-defects-20261026.json
python "$TEMPLATE/scripts/restore_data.py" --group all --data-dir "$DATA"
if [[ ! -f "$LATTICE" ]] || [[ "$(sha256sum "$LATTICE" | cut -d' ' -f1)" != "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2" ]]; then
  tmp="$(mktemp "$CACHE_DIR/lattice.XXXXXXXX")"
  trap 'rm -f "$tmp"; [[ -z "${stage:-}" ]] || rm -rf "$stage"' EXIT
  gh api 'repos/buffedlizard55-lab/GEMSDOE24/contents/inputs/calibration/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif?ref=07345ea0604953d7efb858d9cfbc21e20c7aca0b' -H 'Accept: application/vnd.github.raw' > "$tmp"
  [[ "$(sha256sum "$tmp" | cut -d' ' -f1)" == "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2" ]] || { echo 'Registry hash mismatch' >&2; exit 1; }
  mv "$tmp" "$LATTICE"
fi
python scripts/audit_focus.py --template "$DATA/sample_submission.tif" --labels "$DATA/labels.tif" --cache "$CACHE_DIR/focus" --out evidence/focus-audit-20261026.json
python scripts/lattice_feasibility.py --template "$DATA/sample_submission.tif" --registry "$LATTICE" --budget 37654 --out evidence/lattice-feasibility-20261026.json
python scripts/audit_archived_e1.py --template "$DATA/sample_submission.tif" --registry "$LATTICE" --out evidence/parallel-e1-lattice-audit-20261026.json
printf '\nEvidence refresh complete. No candidate generated and no slot spent.\n'
