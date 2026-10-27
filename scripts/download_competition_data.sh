#!/usr/bin/env bash
# Autonomous, SHA-256-pinned competition & external geothermal data restoration.
# Uses standard Git protocol over https://github.com (no DrivenData login, no REST API rate limit).
# Stores large rasters in .cache/gems_data/ (excluded from snapshots/Git) and symlinks into data/.
set -euo pipefail
cd "$(dirname "$0")/.."

CACHE_DATA=".cache/gems_data"
TMP_REPOS="/tmp/gems_repos"
mkdir -p "$CACHE_DATA" "$TMP_REPOS" data/external

if [[ ! -s "$CACHE_DATA/training_features.tif" ]]; then
  if [[ ! -d "$TMP_REPOS/GEMSDOE" ]]; then
    git clone --depth 1 --filter=blob:none --no-checkout https://github.com/buffedlizard55-lab/GEMSDOE.git "$TMP_REPOS/GEMSDOE"
    git -C "$TMP_REPOS/GEMSDOE" sparse-checkout init --no-cone
    git -C "$TMP_REPOS/GEMSDOE" sparse-checkout set "data/bridge/gems-geodawn-numerical-features.tif.part-*"
    git -C "$TMP_REPOS/GEMSDOE" checkout
  fi
  cat "$TMP_REPOS/GEMSDOE"/data/bridge/gems-geodawn-numerical-features.tif.part-* > "$CACHE_DATA/training_features.tif"
fi

if [[ ! -s "$CACHE_DATA/sample_submission.tif" || ! -s "$CACHE_DATA/2m_temperature_probe_INGENIOUS_regional_data.zip" ]]; then
  if [[ ! -d "$TMP_REPOS/GEMSDOE24" ]]; then
    git clone --depth 1 --filter=blob:none --no-checkout https://github.com/buffedlizard55-lab/GEMSDOE24.git "$TMP_REPOS/GEMSDOE24"
    git -C "$TMP_REPOS/GEMSDOE24" sparse-checkout init --no-cone
    git -C "$TMP_REPOS/GEMSDOE24" sparse-checkout set \
      "data/bridge/*" \
      "data/external/*" \
      "data/external/audit_sources/tiger_road_distance_m.tif" \
      "inputs/*" \
      "inputs/calibration/*"
    git -C "$TMP_REPOS/GEMSDOE24" checkout
  fi
  cp -f "$TMP_REPOS/GEMSDOE24/data/bridge/existing_faults.tif" "$CACHE_DATA/existing_faults.tif"
  cp -f "$TMP_REPOS/GEMSDOE24/data/bridge/labels.tif" "$CACHE_DATA/labels.tif"
  cp -f "$TMP_REPOS/GEMSDOE24/data/bridge/sample_submission.tif" "$CACHE_DATA/sample_submission.tif"
  cp -f "$TMP_REPOS/GEMSDOE24/data/external/2m_temperature_probe_INGENIOUS_regional_data.zip" "$CACHE_DATA/2m_temperature_probe_INGENIOUS_regional_data.zip"
  cp -f "$TMP_REPOS/GEMSDOE24/data/external/paleo_geothermal_regional.zip" "$CACHE_DATA/paleo_geothermal_regional.zip"
  cp -f "$TMP_REPOS/GEMSDOE24/data/external/audit_sources/tiger_road_distance_m.tif" "$CACHE_DATA/tiger_road_distance_m.tif"
  for extf in lidar_scarp_features_u8.tif geodawn_rad_u8.tif geodawn_extensions_u8.tif derived_sgmc_faults_100m_u8.tif gdr_wellspring_in_footprint.csv gdr_qfaults_traces.csv gdr_volcanic_vents_in_footprint.csv; do
    if [[ ! -s "data/external/$extf" ]]; then
      if [[ ! -s "$CACHE_DATA/$extf" && -s "$TMP_REPOS/GEMSDOE24/data/external/$extf" ]]; then
        cp -f "$TMP_REPOS/GEMSDOE24/data/external/$extf" "$CACHE_DATA/$extf"
      fi
      if [[ -s "$CACHE_DATA/$extf" ]]; then
        ln -sf "../../$CACHE_DATA/$extf" "data/external/$extf"
      fi
    fi
  done
fi

ln -sf "../$CACHE_DATA/training_features.tif" data/training_features.tif
ln -sf "../$CACHE_DATA/existing_faults.tif" data/existing_faults.tif
ln -sf "../$CACHE_DATA/labels.tif" data/labels.tif
ln -sf "../$CACHE_DATA/sample_submission.tif" data/sample_submission.tif
ln -sf "../../$CACHE_DATA/2m_temperature_probe_INGENIOUS_regional_data.zip" data/external/2m_temperature_probe_INGENIOUS_regional_data.zip
ln -sf "../../$CACHE_DATA/paleo_geothermal_regional.zip" data/external/paleo_geothermal_regional.zip
ln -sf "../../$CACHE_DATA/tiger_road_distance_m.tif" data/external/tiger_road_distance_m.tif

PY="${PYTHON:-python3}"
if [[ -x ".venv/bin/python" ]]; then PY=".venv/bin/python"; fi

"$PY" - << 'EOF'
import hashlib, json, pathlib
root = pathlib.Path(".")
manifest = json.loads((root / "research/snapshots/GEMSDOE32/registry/data_manifest.json").read_text())
verified = []
for f in manifest["files"]:
    if f["group"] in ("core", "external"):
        p = root / "data" / f["dest"]
        if not p.exists():
            raise SystemExit(f"MISSING required file: {p}")
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        if sha != f["sha256"]:
            raise SystemExit(f"SHA-256 MISMATCH for {f['id']}: {sha} != {f['sha256']}")
        verified.append({"id": f["id"], "dest": f["dest"], "bytes": p.stat().st_size, "sha256": sha})
print(f"Verified SHA-256 checksums for all {len(verified)} core + external files (owner-mirrored pins; not organizer-authenticated).")
EOF
