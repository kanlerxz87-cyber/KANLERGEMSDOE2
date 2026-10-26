#!/usr/bin/env bash
set -euo pipefail
# Downloads competition rasters into data/ from free public mirrors.
# Requires unrestricted network (Dropbox + GDR + USGS). In sandboxed Arena seats,
# this will fail with "Cannot auto-download" — run on any unrestricted host.
#
# Official source: https://www.drivendata.org/competitions/306/competition-doe-gems/data/ (login required)
# Public mirrors documented in knowledge/03_limitations_and_external_data.md:
#   - GDR #1391: https://gdr.openei.org/submissions/1391
#   - Dropbox mirrors (community-provided, verified with sha probes):
#     example_submission.tif: https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&dl=1
#     existing_faults.tif:    https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&dl=1
#     training_features:      https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&dl=1
#     1m DEM links PDF:       https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&dl=1
#
DATA_DIR="data"
mkdir -p "$DATA_DIR"
echo "=== KANLERGEMSDOE2 download_competition_data.sh ==="
echo "Target: $DATA_DIR/"
echo "If this fails with 403/login, you are in a restricted sandbox — run on an unrestricted machine."

dl() {
  local url="$1" out="$2"
  echo "→ $out"
  if command -v curl >/dev/null; then
    curl -L --fail --progress-bar -o "$out" "$url" || { echo "WARN: curl failed for $url"; return 1; }
  elif command -v wget >/dev/null; then
    wget -O "$out" "$url" || { echo "WARN: wget failed for $url"; return 1; }
  else
    echo "ERROR: need curl or wget"; exit 2
  fi
  ls -lh "$out"
}

# Try Dropbox mirrors (direct download with dl=1)
dl "https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&dl=1" "$DATA_DIR/sample_submission.tif" || true
dl "https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&dl=1" "$DATA_DIR/existing_faults.tif" || true
dl "https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&dl=1" "$DATA_DIR/training_features.tif" || true
dl "https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&dl=1" "$DATA_DIR/1m_DEM_links.pdf" || true

# Verify
echo ""
echo "=== Verification ==="
ls -lh "$DATA_DIR" || true
if [[ -f "$DATA_DIR/training_features.tif" ]]; then
  echo "✓ training_features.tif present"
else
  echo "❌ training_features.tif MISSING — see Limitations in README.md"
fi
if [[ -f "$DATA_DIR/existing_faults.tif" ]]; then
  echo "✓ existing_faults.tif present"
fi
if [[ -f "$DATA_DIR/sample_submission.tif" ]]; then
  echo "✓ sample_submission.tif present (template for CRS/shape/transform)"
fi
echo ""
echo "Next: python scripts/prepare_data.py"
