#!/usr/bin/env python3
"""Execute the 3 pre-registered H-N1 DARP-MT10 experiments (DARP-EXP-1..3), 4-instrument holdout
evaluation, 410+-raster pre/post-placement uniqueness audit, and portal-safe GeoTIFF + ZIP emission.

Strictly obeys Parallel-Run Protocol Rules 1-6:
  - Rule 1 (LANE & UNIQUENESS): Stays inside pre-registered `H-N1 (DARP-MT10)` frozen in
    `knowledge/02_preregistered_hypotheses_kg2_20261027.md`. Checks continuous surface BEFORE
    placement (`|Spearman| <= 0.90`) AND final dots AFTER placement (`|Spearman| <= 0.90` and
    `<= 70%` 3-px dot overlap) against all competing detector rasters across the 360-entry archive
    registry, all 9 focus sites, fleet benchmarks, sister sites (`KANLERGEMSDOE1/3`, `WBGGEMSDOE1..3`),
    and all 3 prior `KANLERGEMSDOE2` submissions (`11a2f251`, `f5a469e94b14`, `cab53e1b`), while
    transparently logging the literal `13gems` 5-px calibration lattice (`U = 6,649` uncovered edge px).
  - Rule 2 (REUSE, DON'T REBUILD): Reuses repaired `src/gems32/holdout.py` (`HIDE-RECOVER-v3.1` &
    `SGMC-CAL-v3.0`), `src/gems/holdout.py` (`gems-segment-pooled-v1`), `C-PIED-v1.0`, and cached stacks.
  - Rule 3 (LABEL EVERY NUMBER): Every metric carries `HOLDOUT-DTI` (evaluator version, withheld N,
    95% CI) or `USER-REPORTED` / `ORGANIZER-CONFIRMED`. Never writes a projection as a score.
  - Rule 4 (LEAKAGE CANARY): Requires 68/68 single-feature AUCs <= 0.90 before fitting any model.
  - Rule 5-6 (RUN CARD & BUDGET): Exactly 3 experiments within < 2 hours, 0 live DrivenData slots spent.
"""
from __future__ import annotations

import gc
import glob
import hashlib
import json
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import lightgbm as lgb
import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt, gaussian_filter
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems.holdout import SegmentHoldout  # noqa: E402
from gems32 import darp_mt10, holdout, htcads, submission  # noqa: E402
from gems32.paths import data_dir, downloads_dir, evidence_dir, work_dir  # noqa: E402

_D3_OFFS: list[tuple[int, int]] = [
    (dy, dx) for dy in range(-3, 4) for dx in range(-3, 4) if dy * dy + dx * dx <= 9
]

# Smooth >15-km regional fields excluded from local centerline tree splits (fixes IR-KG2-BUG-02)
_SUB_REGIONAL_BLOB_COLS = {20, 21, 22, 24, 25, 26, 27, 33, 35}


def _git_branch() -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, cwd=ROOT, check=True)
        return r.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _extract_ci95(ci_obj) -> list[float]:
    if isinstance(ci_obj, dict):
        return [round(float(x), 6) for x in ci_obj["interval"]]
    return [round(float(x), 6) for x in ci_obj]


def _logit(p: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    pc = np.clip(p, eps, 1.0 - eps)
    return np.log(pc / (1.0 - pc)).astype(np.float32)


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return (1.0 / (1.0 + np.exp(-np.clip(x, -20.0, 20.0)))).astype(np.float32)


def _unit_rank_vec(v: np.ndarray) -> np.ndarray | None:
    r = rankdata(v, method="average").astype(np.float64)
    r -= r.mean()
    nrm = float(np.linalg.norm(r))
    return (r / nrm).astype(np.float32) if nrm >= 1e-12 else None


def _predict_chunked_concat(
    model: lgb.LGBMClassifier,
    X_sub: np.ndarray,
    sub_cols: list[int],
    X_darp: np.ndarray,
    darp_cols: list[int],
    chunk: int = 1_050_000,
) -> np.ndarray:
    n = X_sub.shape[0]
    out = np.empty(n, dtype=np.float32)
    for s in range(0, n, chunk):
        e = min(s + chunk, n)
        blk = np.hstack([
            np.asarray(X_sub[s:e, sub_cols], dtype=np.float32),
            np.asarray(X_darp[s:e, darp_cols], dtype=np.float32),
        ])
        out[s:e] = model.predict_proba(blk)[:, 1].astype(np.float32)
    return out


def _predict_chunked_single(model: lgb.LGBMClassifier, X: np.ndarray, chunk: int = 1_050_000) -> np.ndarray:
    n = X.shape[0]
    out = np.empty(n, dtype=np.float32)
    for s in range(0, n, chunk):
        e = min(s + chunk, n)
        out[s:e] = model.predict_proba(np.asarray(X[s:e], dtype=np.float32))[:, 1].astype(np.float32)
    return out


def _build_darp_physical_priors(
    X_sub: np.ndarray,
    X_lid: np.ndarray,
    X_darp: np.ndarray,
    lidar_valid_fp: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """First-principles label-free Multi-Physics Conduit priors for DARP-EXP-1 (scarp-blind) and DARP-EXP-2/3.

    Crucially weights piedmont/basin-margin extensional habitat (`piedmont_habitat_prior`) + depth-adaptive
    updip basement emergence + asymmetric MT clay-cap baffles + stress-aligned ComCat/heat-flow conduits,
    suppressing bare-rock Mesozoic range-crest thrusts (prevents 10GEMSDOE scarp convergence while maximizing
    concealed piedmont & basin-margin fault discovery).
    """
    n = X_sub.shape[0]
    p1 = np.empty(n, dtype=np.float32)
    p2 = np.empty(n, dtype=np.float32)
    chunk = 1_050_000

    lid_raw = 0.60 * np.asarray(X_lid[:, 8], dtype=np.float32) + 0.40 * np.asarray(X_lid[:, 9], dtype=np.float32)
    lid_mean = float(np.mean(lid_raw[lidar_valid_fp]))
    lid_zm = np.where(lidar_valid_fp, lid_raw - lid_mean, 0.0).astype(np.float32)
    del lid_raw

    for s in range(0, n, chunk):
        e = min(s + chunk, n)
        bs = np.asarray(X_sub[s:e], dtype=np.float32)
        bd = np.asarray(X_darp[s:e], dtype=np.float32)

        pied_hab = bd[:, 12]  # [0.10, 1.0] alluvial-piedmont / basin-margin structural habitat

        # Updip multi-horizon potential-field & true tilt contact wavenumber (H-N1a + H-N2)
        updip_struct = (
            0.34 * bd[:, 0]      # darp_grav_updip_zb
            + 0.22 * bd[:, 1]    # darp_rtp_updip_zb
            + 0.20 * bd[:, 2]    # darp_grav_tilt_k
            + 0.24 * bd[:, 3]    # darp_updip_converge
            + 0.18 * np.maximum.reduce([bs[:, 1], bs[:, 3], bs[:, 8], bs[:, 10]])
        )

        # Asymmetric MT clay-cap baffle + K/Th + magnetite-destruction + heat-flow/GDR conduit (H-N1b)
        hydro_baffle = (
            0.35 * bd[:, 4]      # darp_mt_baffle_asym
            + 0.28 * bd[:, 5]    # darp_mt_baffle_worm
            + 0.37 * bd[:, 7]    # darp_clay_alter_conduit
            + 0.16 * np.maximum.reduce([bs[:, 14], bs[:, 15], bs[:, 17], bs[:, 23]])
        )

        # Regional stress dilation tendency x shallow ComCat microseismicity + conductive heat-flow (H-N1d)
        reg_tect_therm = 1.0 + 0.24 * np.tanh(
            0.40 * bd[:, 6]      # darp_usgs_hf_resid_up
            + 0.35 * bd[:, 15]   # comcat_shallow_seismicity
            + 0.35 * bd[:, 16]   # comcat_stress_ridge
            + 0.30 * bs[:, 20]   # gdr_probe_2m_upgrad
            + 0.25 * bs[:, 21]   # gdr_geotherm_upgrad
            + 0.25 * bs[:, 24]   # gps_strain_2ndinv
        )

        # Meso-piedmont toe concavity (100m DEM, allowed in EXP-1 because non-LiDAR/non-fine-scarp)
        meso_toe = (0.30 * bs[:, 30] + 0.22 * bs[:, 29] + 0.18 * bs[:, 31]) * (0.55 + 0.45 * pied_hab)

        # EXP-1: Pure subsurface updip + asymmetric MT + stress/seismic/thermal + meso-piedmont toe
        raw_1 = (0.42 * updip_struct + 0.32 * hydro_baffle + 0.26 * meso_toe) * (0.60 + 0.40 * pied_hab) * reg_tect_therm

        # EXP-2/3: Adds seamless 10m + 3m + 1m contour-orthogonal piedmont scarp stack bridging 100% of 24.6% void
        pied_scarp_10_3_1 = (
            0.36 * bd[:, 13]     # multiscale_piedmont_scarp (seamless 1m+3m+10m)
            + 0.26 * bd[:, 10]   # dem10_piedmont_worm
            + 0.20 * bd[:, 11]   # scarp3m_piedmont_gate
            + 0.18 * bd[:, 8]    # dem10_scarp_onesided_clean
            + 0.06 * np.maximum(lid_zm[s:e], 0.0)
        ) * (0.62 + 0.38 * pied_hab)

        raw_2 = (0.46 * pied_scarp_10_3_1 + 0.26 * updip_struct + 0.18 * hydro_baffle + 0.10 * bd[:, 17]) * reg_tect_therm

        p1[s:e] = np.clip(raw_1, 0.0, 2.0).astype(np.float32)
        p2[s:e] = np.clip(raw_2, 0.0, 2.0).astype(np.float32)

    p1 *= 0.045 / (float(np.percentile(p1, 99.2)) + 1e-6)
    p2 *= 0.045 / (float(np.percentile(p2, 99.2)) + 1e-6)
    return np.clip(p1, 0.0, 0.12), np.clip(p2, 0.0, 0.12)


def _collect_all_comparison_rasters(foot: np.ndarray) -> tuple[list[dict], np.ndarray, set[str], dict]:
    """Load and deduplicate ALL comparison rasters across archive, focus, fleet, sister, and prior KG2."""
    ddir = data_dir()
    cand_paths = sorted(set(
        glob.glob(str(ddir / "scored" / "*.tif"))
        + glob.glob(str(ddir / "scored_extra" / "*.tif"))
        + glob.glob(str(ROOT / "docs" / "downloads" / "*.tif"))
    ))
    # Exclude any previously emitted darp-mt10 artifact if script is re-run idempotently
    cand_paths = [p for p in cand_paths if "darp-mt10" not in Path(p).name]

    H, W = foot.shape
    n_fp = int(foot.sum())
    seen_fp_hash: dict[str, dict] = {}
    all_file_shas: set[str] = set()
    records: list[dict] = []

    rng = np.random.default_rng(20261027)
    sample_idx = rng.choice(n_fp, size=80_000, replace=False)
    sample_idx.sort()

    scratch_pad = np.zeros((H + 6, W + 6), dtype=bool)
    fy_all, fx_all = np.nonzero(foot)
    fy_cov = fy_all[sample_idx] + 3
    fx_cov = fx_all[sample_idx] + 3

    exact_lattice_info = {}

    for p_str in cand_paths:
        p = Path(p_str)
        try:
            fsha = submission.sha256_file(p)
            all_file_shas.add(fsha)
            with rasterio.open(p) as ds:
                if (ds.height, ds.width) != (H, W):
                    continue
                arr = ds.read(1)
        except Exception:
            continue

        af = np.where(np.isfinite(arr[foot]), arr[foot], 0.0).astype(np.float32)
        h_fp = hashlib.sha256(np.round(af, 5).tobytes()).hexdigest()[:16]
        if h_fp in seen_fp_hash:
            seen_fp_hash[h_fp]["aliases"].append(p.name)
            continue

        n_frac = int(np.sum((af > 1e-5) & (af < 1.0 - 1e-5)))
        is_cont = n_frac > 1000
        m_dots = foot & np.isfinite(arr) & (arr >= 0.5)
        ry, rx = np.nonzero(m_dots)
        n_dots = int(ry.size)
        if n_dots == 0 and not is_cont:
            continue

        cov3_fp = 0.0
        if n_dots > 0:
            scratch_pad[ry + 3, rx + 3] = True
            hit_cov = np.zeros(sample_idx.size, dtype=bool)
            for dy, dx in _D3_OFFS:
                hit_cov |= scratch_pad[fy_cov + dy, fx_cov + dx]
            cov3_fp = float(hit_cov.mean())
            scratch_pad[ry + 3, rx + 3] = False

        is_lattice = bool(cov3_fp > 0.50 or "lattice-s5" in p.name)
        if is_lattice and not exact_lattice_info:
            d_lat = distance_transform_edt(~m_dots)
            within3_exact = int((foot & (d_lat <= 3.0 + 1e-6)).sum())
            u_exact = int(n_fp - within3_exact)
            exact_lattice_info = {
                "name": p.name,
                "sha256": fsha,
                "n_dots_in_footprint": n_dots,
                "footprint_pixels": n_fp,
                "within_3px_pixels": within3_exact,
                "exact_uncovered_pixels_U": u_exact,
                "exact_footprint_3px_coverage": round(within3_exact / n_fp, 8),
            }

        rec = {
            "name": p.name,
            "aliases": [p.name],
            "path": str(p),
            "sha256": fsha,
            "is_continuous": is_cont,
            "is_calibration_lattice": is_lattice,
            "n_dots": n_dots,
            "cov3_of_footprint": round(cov3_fp, 5),
            "unit_rank": _unit_rank_vec(af[sample_idx]),
            "ry": ry.astype(np.int16) if n_dots > 0 else None,
            "rx": rx.astype(np.int16) if n_dots > 0 else None,
        }
        seen_fp_hash[h_fp] = rec
        records.append(rec)

    del fy_all, fx_all
    return records, sample_idx, all_file_shas, exact_lattice_info


def _audit_uniqueness(
    pi_full_2d: np.ndarray,
    dots_2d: np.ndarray,
    foot: np.ndarray,
    registry: list[dict],
    sample_idx: np.ndarray,
    exact_lattice_info: dict,
) -> dict:
    """Protocol Rule 1: Pre-placement continuous surface AND post-placement final dots uniqueness check."""
    H, W = foot.shape
    u_pi = _unit_rank_vec(pi_full_2d[foot][sample_idx])
    u_dots = _unit_rank_vec(dots_2d[foot][sample_idx].astype(np.float32))

    oy, ox = np.nonzero(dots_2d)
    n_our = int(oy.size)
    oy_p = oy + 3
    ox_p = ox + 3
    our_d3 = distance_transform_edt(~dots_2d) <= 3.0
    scratch_pad = np.zeros((H + 6, W + 6), dtype=bool)

    max_cont_spearman = -1.0
    max_cont_peer = ""
    max_dots_spearman = -1.0
    max_dots_spearman_peer = ""
    max_asym_3px_detector = -1.0
    max_asym_3px_peer = ""
    max_bidir_3px_detector = -1.0
    max_bidir_3px_peer = ""
    max_sym_3px_all = -1.0
    max_sym_3px_peer = ""
    max_literal_all = -1.0
    max_literal_all_peer = ""

    calibration_probes = []
    named_benchmarks = {}
    top_peers = []

    key_tags = {
        "GEMSDOE32_0p2778_champ": "e5eb6e7e",
        "PRIOR_KG2_HTCADS_11a2f251": "11a2f251",
        "PRIOR_KG2_MGHV_f5a469e94b14": "f5a469e94b14",
        "PRIOR_KG2_FVCA_cab53e1b": "cab53e1b",
        "GEMSDOE36_0p2750": "9b9ea4e6",
        "GEMSDOE28_0p2710": "b531dae0a36f",
        "GEMSDOE31_0p2708": "8acb75e1",
        "GEMSDOE33_0p2632": "cb490425926e",
        "GEMSDOE25_0p2600": "e56ea318af89",
        "GEMSDOE24_0p2477": "989f59505db1",
        "GEMSDOE27_0p2449": "5512495c6bd1",
        "GEMSDOE70_0p2478": "p8-oof38k",
        "KANLERGEMSDOE1": "kanlergemsdoe1",
        "KANLERGEMSDOE3": "kanlergemsdoe3",
        "WBGGEMSDOE1": "wbggemsdoe1",
        "WBGGEMSDOE2": "wbg2-h1",
        "WBGGEMSDOE3": "wb-gems-doe-3-stepover",
    }

    for rec in registry:
        ur = rec["unit_rank"]
        if ur is not None and u_pi is not None and u_dots is not None:
            rc_cont = abs(float(np.dot(u_pi, ur)))
            rc_dots = abs(float(np.dot(u_dots, ur)))
        else:
            rc_cont, rc_dots = 0.0, 0.0

        if rc_cont > max_cont_spearman:
            max_cont_spearman = rc_cont
            max_cont_peer = rec["name"]
        if rc_dots > max_dots_spearman:
            max_dots_spearman = rc_dots
            max_dots_spearman_peer = rec["name"]

        if rec["ry"] is not None and rec["n_dots"] > 0:
            ry = rec["ry"].astype(np.int32)
            rx = rec["rx"].astype(np.int32)
            scratch_pad[ry + 3, rx + 3] = True
            hit = np.zeros(n_our, dtype=bool)
            for dy, dx in _D3_OFFS:
                hit |= scratch_pad[oy_p + dy, ox_p + dx]
            scratch_pad[ry + 3, rx + 3] = False

            ov_our_in_reg = float(hit.sum()) / max(n_our, 1)
            ov_reg_in_our = float(our_d3[ry, rx].sum()) / max(rec["n_dots"], 1)
            bidir_ov = max(ov_our_in_reg, ov_reg_in_our)
            sym_ov = (
                2.0 * ov_our_in_reg * ov_reg_in_our / (ov_our_in_reg + ov_reg_in_our)
                if (ov_our_in_reg + ov_reg_in_our) > 0
                else 0.0
            )
            if ov_our_in_reg > max_literal_all:
                max_literal_all = ov_our_in_reg
                max_literal_all_peer = rec["name"]
            if sym_ov > max_sym_3px_all:
                max_sym_3px_all = sym_ov
                max_sym_3px_peer = rec["name"]

            joined_names = " ".join(rec["aliases"]).lower()
            for bkey, sub_tag in key_tags.items():
                if sub_tag.lower() in joined_names and bkey not in named_benchmarks:
                    named_benchmarks[bkey] = {
                        "peer": rec["name"],
                        "peer_dots": rec["n_dots"],
                        "our_in_peer_3px": round(ov_our_in_reg, 6),
                        "peer_in_our_3px": round(ov_reg_in_our, 6),
                        "harmonic_3px": round(sym_ov, 6),
                        "continuous_spearman": round(rc_cont, 6),
                        "dots_spearman": round(rc_dots, 6),
                    }

            if rec["is_calibration_lattice"]:
                u_uncov = exact_lattice_info.get("exact_uncovered_pixels_U", 6649)
                pigeonhole_lb = max(0, n_our - u_uncov) / max(n_our, 1)
                calibration_probes.append({
                    "name": rec["name"],
                    "n_dots": rec["n_dots"],
                    "footprint_3px_coverage": exact_lattice_info.get("exact_footprint_3px_coverage", rec["cov3_of_footprint"]),
                    "exact_uncovered_pixels_U": u_uncov,
                    "pigeonhole_min_3px_overlap_at_K": round(pigeonhole_lb, 6),
                    "asym_frac_in_3px": round(ov_our_in_reg, 6),
                    "reverse_frac_reg_in_our_3px": round(ov_reg_in_our, 6),
                    "harmonic_3px_overlap": round(sym_ov, 6),
                    "continuous_spearman": round(rc_cont, 6),
                    "final_dots_spearman": round(rc_dots, 6),
                    "note": (
                        f"Uniform 5-px calibration lattice covering {exact_lattice_info.get('within_3px_pixels', 5160724):,}/"
                        f"{exact_lattice_info.get('footprint_pixels', 5167373):,} footprint px (U={u_uncov:,} edge px >3px); "
                        f"Pigeonhole lower bound at K={n_our:,} is {pigeonhole_lb:.4%}."
                    ),
                })
            else:
                if ov_our_in_reg > max_asym_3px_detector:
                    max_asym_3px_detector = ov_our_in_reg
                    max_asym_3px_peer = rec["name"]
                if bidir_ov > max_bidir_3px_detector:
                    max_bidir_3px_detector = bidir_ov
                    max_bidir_3px_peer = rec["name"]
                top_peers.append({
                    "peer": rec["name"],
                    "peer_dots": rec["n_dots"],
                    "asym_3px_overlap": round(ov_our_in_reg, 6),
                    "bidir_max_3px_overlap": round(bidir_ov, 6),
                    "harmonic_3px_overlap": round(sym_ov, 6),
                    "continuous_spearman": round(rc_cont, 6),
                    "final_dots_spearman": round(rc_dots, 6),
                })

    top_peers.sort(key=lambda d: d["asym_3px_overlap"], reverse=True)
    n_detectors = sum(1 for r in registry if not r["is_calibration_lattice"])
    detector_passed = bool(
        max_cont_spearman < 0.90
        and max_dots_spearman < 0.90
        and max_asym_3px_detector <= 0.70
        and max_sym_3px_all <= 0.70
    )
    literal_all_passed = bool(detector_passed and max_literal_all <= 0.70)
    return {
        "passed": detector_passed,
        "detector_protocol_passed": detector_passed,
        "literal_including_5px_calibration_lattice_passed": literal_all_passed,
        "unique_rasters_checked": len(registry),
        "competing_detectors_checked": n_detectors,
        "calibration_lattices_checked": len(registry) - n_detectors,
        "pre_placement_surface_max_abs_spearman": round(max_cont_spearman, 6),
        "pre_placement_closest_peer": max_cont_peer,
        "final_dots_max_abs_spearman": round(max_dots_spearman, 6),
        "final_dots_closest_spearman_peer": max_dots_spearman_peer,
        "final_dots_max_detector_3px_overlap": round(max_asym_3px_detector, 6),
        "final_dots_closest_3px_detector_peer": max_asym_3px_peer,
        "final_dots_max_detector_bidir_3px_overlap": round(max_bidir_3px_detector, 6),
        "final_dots_closest_bidir_detector_peer": max_bidir_3px_peer,
        "final_dots_max_harmonic_3px_overlap_all": round(max_sym_3px_all, 6),
        "final_dots_closest_harmonic_peer": max_sym_3px_peer,
        "literal_all_registry_max_3px_overlap": round(max_literal_all, 6),
        "literal_all_registry_closest_peer": max_literal_all_peer,
        "calibration_lattice_probes_logged": calibration_probes,
        "named_benchmarks": named_benchmarks,
        "top_12_closest_detector_peers": top_peers[:12],
    }


def main() -> int:
    t_start = time.time()
    ddir, wdir, edir, dldir = data_dir(), work_dir(), evidence_dir(), downloads_dir()

    canary_path = edir / "darp_mt10_canary_20261027.json"
    if not canary_path.exists():
        raise SystemExit("Missing evidence/darp_mt10_canary_20261027.json — run single-feature canary first.")
    canary = json.loads(canary_path.read_text(encoding="utf-8"))
    if not canary.get("passed"):
        raise SystemExit("Rule 4 Leakage Canary failed; aborting experiments.")
    print(f"[DARP-MT10] Verified 68/68 Rule 4 Leakage Canary PASSED (max single-feature AUC = {canary['max_single_feature_auc']:.6f} <= 0.90).", flush=True)

    dstack = darp_mt10.build_darp_feature_stack(ddir, wdir)
    foot = dstack["foot"]
    lidar_valid_fp = dstack["lidar_valid_fp"]
    X_sub = dstack["X_sub"]
    X_lid = dstack["X_lid"]
    X_darp = dstack["X_darp"]
    n_fp = int(foot.sum())

    ctx = holdout.load_holdout_context(ddir)
    cp_ctx = darp_mt10.prepare_c_pied_truth(ddir, ctx)
    seg_holdout = SegmentHoldout(foot, ctx.labels, buffer_px=15)

    fp_idx_2d = np.full(foot.shape, -1, dtype=np.int32)
    fp_idx_2d[foot] = np.arange(n_fp, dtype=np.int32)

    # ------------------------------------------------------------------
    # Score Reference Baselines across all instruments:
    #   (A) GEMSDOE32 B=2 (0.2778 USER-REPORTED champion)
    #   (B) Prior KANLERGEMSDOE2 HTCADS EXP-2 (11a2f251)
    # ------------------------------------------------------------------
    with rasterio.open(ddir / "scored" / "GEMSDOE25__gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif") as ds:
        a_d28 = ds.read(1)
        d28_mask = foot & np.isfinite(a_d28) & (a_d28 >= 0.5)
        del a_d28
    with rasterio.open(ddir / "scored" / "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif") as ds:
        a_b2 = ds.read(1)
        b2_static_mask = foot & np.isfinite(a_b2) & (a_b2 >= 0.5)
        del a_b2

    ref_hr = holdout.evaluate_hide_and_recover(d28_mask, ctx, b_visible_px=2.0, n_boot=1000, seed=20261027, name="GEMSDOE32_B2_0p2778_ref")
    ref_sg = holdout.evaluate_sgmc_with_ci(b2_static_mask, ctx, n_boot=1000, seed=20261027, name="GEMSDOE32_B2_0p2778_ref")
    ref_cp = darp_mt10.evaluate_c_pied_with_ci(b2_static_mask, ctx, cp_ctx, n_boot=1000, seed=20261027, name="GEMSDOE32_B2_0p2778_ref")

    # Fold-honest D2.8 vis-B2 baseline on SegmentHoldout (N=60,988)
    seg_ref_preds = []
    for f_obj in seg_holdout.folds:
        d_v = distance_transform_edt(~f_obj["visible"])
        seg_ref_preds.append((d28_mask & (d_v > 2.0)).astype(np.uint8))
    ref_seg = seg_holdout.summarize(seg_ref_preds, ci_draws=1000)
    del d28_mask, b2_static_mask

    prior_htcads_path = dldir / "kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif"
    prior_htcads_sg = None
    prior_htcads_cp = None
    if prior_htcads_path.exists():
        with rasterio.open(prior_htcads_path) as ds:
            arr_ht = ds.read(1)
            m_ht = foot & np.isfinite(arr_ht) & (arr_ht >= 0.5)
            del arr_ht
        prior_htcads_sg = holdout.evaluate_sgmc_with_ci(m_ht, ctx, n_boot=1000, seed=20261027, name="PRIOR_HTCADS_EXP2_11a2f251")
        prior_htcads_cp = darp_mt10.evaluate_c_pied_with_ci(m_ht, ctx, cp_ctx, n_boot=1000, seed=20261027, name="PRIOR_HTCADS_EXP2_11a2f251")
        del m_ht

    print(
        f"[DARP-MT10] Reference 0.2778 Champion:\n"
        f"  HIDE-RECOVER-v3.1 = {ref_hr['pooled_dti']:.6f} {ref_hr['ci95_cluster_bootstrap']}\n"
        f"  gems-segment-v1   = {ref_seg['dti']:.6f} {ref_seg['ci95']}\n"
        f"  SGMC-CAL-v3.0     = {ref_sg['sgmc_prevalence_calibrated_dti']:.6f} {ref_sg['sgmc_calibrated_ci95']}\n"
        f"  C-PIED-v1.0       = {ref_cp['pooled_dti']:.6f} {ref_cp['ci95_cluster_bootstrap']}",
        flush=True,
    )

    # ------------------------------------------------------------------
    # Load expanded 410+-raster comparison registry BEFORE placement
    # ------------------------------------------------------------------
    t_reg = time.time()
    registry, reg_sample_idx, all_file_shas, exact_lattice_info = _collect_all_comparison_rasters(foot)
    print(
        f"[DARP-MT10] Loaded {len(registry)} footprint-distinct comparison rasters "
        f"({len(all_file_shas)} total .tif files; exact 13gems U={exact_lattice_info.get('exact_uncovered_pixels_U')}) in {time.time()-t_reg:.1f}s.",
        flush=True,
    )

    # ------------------------------------------------------------------
    # Scale-separated sharp feature columns (excludes >15-km regional blobs)
    # ------------------------------------------------------------------
    sub_cols_exp1 = [i for i in range(len(htcads.SUBSURF_FEATURE_NAMES)) if i not in _SUB_REGIONAL_BLOB_COLS and i != 4]
    sub_cols_exp2 = [i for i in range(len(htcads.SUBSURF_FEATURE_NAMES)) if i not in _SUB_REGIONAL_BLOB_COLS]
    darp_cols_exp1 = [i for i in range(len(darp_mt10.DARP_FEATURE_NAMES)) if i not in darp_mt10.DARP_REGIONAL_COLS and i not in darp_mt10.DARP_TOPO_SCARP_COLS]
    darp_cols_exp2 = [i for i in range(len(darp_mt10.DARP_FEATURE_NAMES)) if i not in darp_mt10.DARP_REGIONAL_COLS]

    phys_exp1_fp, phys_exp2_fp = _build_darp_physical_priors(X_sub, X_lid, X_darp, lidar_valid_fp)

    # ------------------------------------------------------------------
    # Train 4 Out-of-Quadrant Specialists strictly on seg_holdout.folds[f]["train"]
    # (purges BOTH test quadrant + 1.5 km collar AND cross-quadrant fault segments!)
    # ------------------------------------------------------------------
    rng = np.random.default_rng(20261027)
    labels_dil3 = binary_dilation(ctx.labels, structure=np.ones((3, 3), bool), iterations=3)

    gbdt_exp1_oof = np.zeros(n_fp, dtype=np.float32)
    gbdt_exp1_full = np.zeros(n_fp, dtype=np.float32)
    gbdt_exp2_oof = np.zeros(n_fp, dtype=np.float32)
    gbdt_exp2_full = np.zeros(n_fp, dtype=np.float32)
    lid_resid_oof = np.zeros(n_fp, dtype=np.float32)
    lid_resid_full = np.zeros(n_fp, dtype=np.float32)

    exp2_feature_names = [htcads.SUBSURF_FEATURE_NAMES[i] for i in sub_cols_exp2] + [darp_mt10.DARP_FEATURE_NAMES[i] for i in darp_cols_exp2]
    exp2_importances = np.zeros(len(exp2_feature_names), dtype=np.float64)

    for fold in holdout.FOLDS:
        t0 = time.time()
        f_seg = seg_holdout.folds[fold]
        q_mask = f_seg["valid"]
        q_fp = fp_idx_2d[q_mask]
        tdom = f_seg["train"]  # Strictly purged of test quadrant + hidden cross-boundary segments + 15-px collar!

        pos_2d = binary_dilation(f_seg["visible"] & tdom, structure=np.ones((3, 3), bool), iterations=1) & tdom
        neg_2d = tdom & ~labels_dil3
        pos_idx = fp_idx_2d[pos_2d]
        neg_idx = fp_idx_2d[neg_2d]

        if pos_idx.size > 40_000:
            pos_idx = rng.choice(pos_idx, size=40_000, replace=False)
        neg_sub = rng.choice(neg_idx, size=min(neg_idx.size, pos_idx.size * 4), replace=False)
        tr_idx = np.concatenate([pos_idx, neg_sub])
        y_tr = np.concatenate([np.ones(pos_idx.size, dtype=np.int8), np.zeros(neg_sub.size, dtype=np.int8)])

        # Piedmont-aware sample weight: upweights basin-margin/piedmont training faults (Z_b >= 150m)
        # so GBDT learns subtle alluvial/updip signatures rather than memorizing steep mountain scarps
        pied_tr = np.asarray(X_darp[tr_idx, 12], dtype=np.float32)
        sw_tr = np.where(y_tr == 1, 0.70 + 0.65 * pied_tr, 1.0).astype(np.float32)

        X_tr_e1 = np.hstack([
            np.asarray(X_sub[tr_idx][:, sub_cols_exp1], dtype=np.float32),
            np.asarray(X_darp[tr_idx][:, darp_cols_exp1], dtype=np.float32),
        ])
        clf_b1 = lgb.LGBMClassifier(
            n_estimators=135,
            learning_rate=0.06,
            num_leaves=31,
            min_child_samples=100,
            subsample=0.80,
            subsample_freq=1,
            colsample_bytree=0.75,
            reg_alpha=2.5,
            reg_lambda=9.0,
            random_state=1100 + fold,
            n_jobs=2,
            verbose=-1,
        )
        clf_b1.fit(X_tr_e1, y_tr, sample_weight=sw_tr)
        del X_tr_e1
        pred_b1 = _predict_chunked_concat(clf_b1, X_sub, sub_cols_exp1, X_darp, darp_cols_exp1)
        gbdt_exp1_oof[q_fp] = pred_b1[q_fp]
        gbdt_exp1_full += 0.25 * pred_b1
        del clf_b1, pred_b1

        X_tr_e2 = np.hstack([
            np.asarray(X_sub[tr_idx][:, sub_cols_exp2], dtype=np.float32),
            np.asarray(X_darp[tr_idx][:, darp_cols_exp2], dtype=np.float32),
        ])
        clf_b2 = lgb.LGBMClassifier(
            n_estimators=150,
            learning_rate=0.06,
            num_leaves=31,
            min_child_samples=100,
            subsample=0.80,
            subsample_freq=1,
            colsample_bytree=0.72,
            reg_alpha=2.5,
            reg_lambda=9.0,
            random_state=1200 + fold,
            n_jobs=2,
            verbose=-1,
        )
        clf_b2.fit(X_tr_e2, y_tr, sample_weight=sw_tr)
        exp2_importances += 0.25 * clf_b2.booster_.feature_importance(importance_type="gain")
        del X_tr_e2
        pred_b2 = _predict_chunked_concat(clf_b2, X_sub, sub_cols_exp2, X_darp, darp_cols_exp2)
        gbdt_exp2_oof[q_fp] = pred_b2[q_fp]
        gbdt_exp2_full += 0.25 * pred_b2
        del clf_b2, pred_b2
        gc.collect()

        # 1 m LiDAR zero-mean log-odds specialist (active inside 75.4% LiDAR valid zone; 10m/3m seamlessly covers 100%)
        pos_lid = pos_idx[lidar_valid_fp[pos_idx]]
        neg_lid_pool = neg_idx[lidar_valid_fp[neg_idx]]
        neg_lid = rng.choice(neg_lid_pool, size=min(neg_lid_pool.size, pos_lid.size * 4), replace=False)
        tr_lid = np.concatenate([pos_lid, neg_lid])
        y_lid = np.concatenate([np.ones(pos_lid.size, dtype=np.int8), np.zeros(neg_lid.size, dtype=np.int8)])
        clf_lid = lgb.LGBMClassifier(
            n_estimators=115,
            learning_rate=0.06,
            num_leaves=23,
            min_child_samples=100,
            subsample=0.80,
            subsample_freq=1,
            colsample_bytree=0.85,
            reg_alpha=2.5,
            reg_lambda=8.0,
            random_state=1300 + fold,
            n_jobs=2,
            verbose=-1,
        )
        clf_lid.fit(np.asarray(X_lid[tr_lid], dtype=np.float32), y_lid)
        raw_lid = _predict_chunked_single(clf_lid, X_lid)
        log_lid = _logit(raw_lid)
        mean_log_lid = float(np.mean(log_lid[lidar_valid_fp]))
        # Complemented inside ~lidar_valid_fp by zero-mean 10m+3m multiscale piedmont scarp log-odds!
        ms10_fp = np.asarray(X_darp[:, 13], dtype=np.float32)
        ms10_void_centered = ms10_fp - float(np.mean(ms10_fp[~lidar_valid_fp]))
        resid = np.where(lidar_valid_fp, log_lid - mean_log_lid, 2.1 * ms10_void_centered).astype(np.float32)
        lid_resid_oof[q_fp] = resid[q_fp]
        lid_resid_full += 0.25 * resid
        del clf_lid, raw_lid, log_lid, ms10_fp, ms10_void_centered, resid
        gc.collect()
        print(f"[DARP-MT10] Quadrant {fold} ({f_seg['name']}) specialists trained in {time.time()-t0:.1f}s", flush=True)

    pied_hab_all = np.asarray(X_darp[:, 12], dtype=np.float32)

    def _blend_blind_piedmont(p_gbdt: np.ndarray, phys_fp: np.ndarray, resid: np.ndarray | None) -> np.ndarray:
        p_g = _sigmoid(_logit(p_gbdt) + 0.45 * resid) if resid is not None else p_gbdt
        # Weight GBDT by piedmont habitat envelope so bare-rock range-crest scarps don't monopolize budget
        p_g_hab = p_g * (0.68 + 0.32 * pied_hab_all)
        p_g_norm = np.clip(p_g_hab * (0.045 / (float(np.percentile(p_g_hab, 99.2)) + 1e-6)), 0.0, 0.12)
        return (0.46 * p_g_norm + 0.54 * phys_fp).astype(np.float32)

    pi_blind_e1_oof = _blend_blind_piedmont(gbdt_exp1_oof, phys_exp1_fp, resid=None)
    pi_blind_e1_full = _blend_blind_piedmont(gbdt_exp1_full, phys_exp1_fp, resid=None)
    pi_blind_e2_oof = _blend_blind_piedmont(gbdt_exp2_oof, phys_exp2_fp, resid=lid_resid_oof)
    pi_blind_e2_full = _blend_blind_piedmont(gbdt_exp2_full, phys_exp2_fp, resid=lid_resid_full)
    del gbdt_exp1_oof, gbdt_exp1_full, gbdt_exp2_oof, gbdt_exp2_full, phys_exp1_fp, phys_exp2_fp, pied_hab_all
    gc.collect()

    def _to_2d(vec_fp: np.ndarray) -> np.ndarray:
        g = np.zeros(foot.shape, dtype=np.float32)
        g[foot] = vec_fp
        return g

    def _axial_smooth(pi_2d: np.ndarray) -> np.ndarray:
        sm = gaussian_filter(pi_2d, sigma=0.50, mode="nearest")
        out = (0.86 * pi_2d + 0.14 * sm).astype(np.float32)
        out[~foot] = 0.0
        return out

    # ------------------------------------------------------------------
    # Full-catalogue directional tip/relay features for live deployment
    # ------------------------------------------------------------------
    vis_cols_dir = [1, 2]
    X_vis_full, aux_full = htcads.compute_visible_catalogue_features(ctx.labels, foot)
    X_vis_full_dir = X_vis_full[:, vis_cols_dir].copy()
    tip_env_full = (np.clip(np.maximum(X_vis_full_dir[:, 0], X_vis_full_dir[:, 1]), 0.0, 1.0) ** 0.65).astype(np.float32)
    del X_vis_full

    d_full_2d = aux_full["d_vis"]
    elig_b2_live = foot & (d_full_2d > 2.0)
    elig_tipcone_live = foot & np.where(
        (aux_full["tip_cone_2d"] >= 0.52) | (aux_full["relay_2d"] >= 0.42),
        d_full_2d > 1.65,
        d_full_2d > 2.10,
    )
    del aux_full
    gc.collect()

    # ------------------------------------------------------------------
    # Fold-honest directional Tip/Relay models + OOF emission across all 8 Hide-Recover cells
    # AND all 4 SegmentHoldout folds
    # ------------------------------------------------------------------
    cell_em_by_exp: dict[str, dict[str, np.ndarray]] = {"DARP-EXP-1": {}, "DARP-EXP-2": {}, "DARP-EXP-3": {}}
    seg_preds_by_exp: dict[str, list[np.ndarray]] = {"DARP-EXP-1": [], "DARP-EXP-2": [], "DARP-EXP-3": []}
    p_tip_e1_live = np.zeros(n_fp, dtype=np.float32)
    p_tip_e2_live = np.zeros(n_fp, dtype=np.float32)

    for idx_c, cell in enumerate(ctx.cells):
        t0 = time.time()
        collar = binary_dilation(ctx.quad == cell.fold, structure=np.ones((3, 3), bool), iterations=holdout.COLLAR_PX) & foot
        tdom = foot & ~collar

        X_vis_c, aux_c = htcads.compute_visible_catalogue_features(cell.visible_full, foot)
        X_vis_c_dir = X_vis_c[:, vis_cols_dir].copy()
        tip_env_c = (np.clip(np.maximum(X_vis_c_dir[:, 0], X_vis_c_dir[:, 1]), 0.0, 1.0) ** 0.65).astype(np.float32)
        del X_vis_c

        d_vis_c = aux_c["d_vis"]
        elig_b2_c = foot & (d_vis_c > 2.0)
        elig_tip_c = foot & np.where(
            (aux_c["tip_cone_2d"] >= 0.52) | (aux_c["relay_2d"] >= 0.42),
            d_vis_c > 1.65,
            d_vis_c > 2.10,
        )
        del aux_c

        active_tip_fp = tip_env_c > 0.02
        active_tip_2d = np.zeros(foot.shape, dtype=bool)
        active_tip_2d[foot] = active_tip_fp

        hid_train_core = (ctx.labels & tdom) & ~cell.visible_full
        hid_pos_2d = binary_dilation(hid_train_core, structure=np.ones((3, 3), bool), iterations=1) & tdom & (d_vis_c > 1.4) & active_tip_2d
        neg_tip_2d = tdom & ~labels_dil3 & (d_vis_c > 1.4) & active_tip_2d
        pos_fp = fp_idx_2d[hid_pos_2d]
        neg_cand_fp = fp_idx_2d[neg_tip_2d]
        del d_vis_c, hid_train_core, hid_pos_2d, neg_tip_2d, active_tip_2d

        neg_fp = rng.choice(neg_cand_fp, size=min(neg_cand_fp.size, pos_fp.size * 5), replace=False)
        tr_fp = np.concatenate([pos_fp, neg_fp])
        y_tr = np.concatenate([np.ones(pos_fp.size, dtype=np.int8), np.zeros(neg_fp.size, dtype=np.int8)])
        X_vis_tr = X_vis_c_dir[tr_fp]

        do_live = cell.seed == 20
        nz_c = np.flatnonzero(active_tip_fp)
        nz_lv = np.flatnonzero(tip_env_full > 0.02) if do_live else None

        # EXP-1 Tip specialist
        clf_t1 = lgb.LGBMClassifier(
            n_estimators=115, learning_rate=0.06, num_leaves=23, min_child_samples=60,
            subsample=0.80, subsample_freq=1, colsample_bytree=0.80,
            reg_alpha=2.0, reg_lambda=8.0, random_state=1400 + idx_c, n_jobs=2, verbose=-1,
        )
        clf_t1.fit(np.hstack([
            np.asarray(X_sub[tr_fp][:, sub_cols_exp1], dtype=np.float32),
            np.asarray(X_darp[tr_fp][:, darp_cols_exp1], dtype=np.float32),
            X_vis_tr,
        ]), y_tr)
        pi_t1_c = np.zeros(n_fp, dtype=np.float32)
        raw_t1 = clf_t1.predict_proba(np.hstack([
            np.asarray(X_sub[nz_c][:, sub_cols_exp1], dtype=np.float32),
            np.asarray(X_darp[nz_c][:, darp_cols_exp1], dtype=np.float32),
            X_vis_c_dir[nz_c],
        ]))[:, 1].astype(np.float32)
        pi_t1_c[nz_c] = np.clip(0.029 * raw_t1 * tip_env_c[nz_c], 0.0, 0.038)
        if do_live and nz_lv is not None:
            raw_t1_lv = clf_t1.predict_proba(np.hstack([
                np.asarray(X_sub[nz_lv][:, sub_cols_exp1], dtype=np.float32),
                np.asarray(X_darp[nz_lv][:, darp_cols_exp1], dtype=np.float32),
                X_vis_full_dir[nz_lv],
            ]))[:, 1].astype(np.float32)
            p_tip_e1_live[nz_lv] += 0.25 * np.clip(0.029 * raw_t1_lv * tip_env_full[nz_lv], 0.0, 0.038)

        # Score SegmentHoldout fold for EXP-1 (using seg_holdout.folds[cell.fold]["visible"] strictly!)
        if do_live:
            f_seg1 = seg_holdout.folds[cell.fold]
            X_vis_s1, aux_s1 = htcads.compute_visible_catalogue_features(f_seg1["visible"], foot)
            X_vis_s1_dir = X_vis_s1[:, vis_cols_dir].copy()
            tip_env_s1 = (np.clip(np.maximum(X_vis_s1_dir[:, 0], X_vis_s1_dir[:, 1]), 0.0, 1.0) ** 0.65).astype(np.float32)
            nz_s1 = np.flatnonzero(tip_env_s1 > 0.02)
            pi_ts1 = np.zeros(n_fp, dtype=np.float32)
            raw_ts1 = clf_t1.predict_proba(np.hstack([
                np.asarray(X_sub[nz_s1][:, sub_cols_exp1], dtype=np.float32),
                np.asarray(X_darp[nz_s1][:, darp_cols_exp1], dtype=np.float32),
                X_vis_s1_dir[nz_s1],
            ]))[:, 1].astype(np.float32)
            pi_ts1[nz_s1] = np.clip(0.029 * raw_ts1 * tip_env_s1[nz_s1], 0.0, 0.038)
            el_s1 = foot & (aux_s1["d_vis"] > 2.0)
            pi_se1 = _axial_smooth(_to_2d(1.0 - (1.0 - pi_ts1) * (1.0 - pi_blind_e1_oof)))
            seg_preds_by_exp["DARP-EXP-1"].append(htcads.emit_submodular_celf(pi_se1, el_s1, max_dots=37654).astype(np.uint8))
            del X_vis_s1, aux_s1, X_vis_s1_dir, tip_env_s1, pi_ts1, raw_ts1, el_s1, pi_se1

        del clf_t1, raw_t1

        pi_e1_2d = _axial_smooth(_to_2d(1.0 - (1.0 - pi_t1_c) * (1.0 - pi_blind_e1_oof)))
        del pi_t1_c
        em1 = htcads.emit_submodular_celf(pi_e1_2d, elig_b2_c, max_dots=37654, marginal_bar=0.0)
        cell_em_by_exp["DARP-EXP-1"][cell.key] = em1[cell.bbox].copy()
        del pi_e1_2d, em1

        # EXP-2/3 Tip specialist
        clf_t2 = lgb.LGBMClassifier(
            n_estimators=120, learning_rate=0.06, num_leaves=23, min_child_samples=60,
            subsample=0.80, subsample_freq=1, colsample_bytree=0.80,
            reg_alpha=2.0, reg_lambda=8.0, random_state=1500 + idx_c, n_jobs=2, verbose=-1,
        )
        clf_t2.fit(np.hstack([
            np.asarray(X_sub[tr_fp][:, sub_cols_exp2], dtype=np.float32),
            np.asarray(X_darp[tr_fp][:, darp_cols_exp2], dtype=np.float32),
            X_vis_tr,
        ]), y_tr)
        pi_t2_c = np.zeros(n_fp, dtype=np.float32)
        raw_t2 = clf_t2.predict_proba(np.hstack([
            np.asarray(X_sub[nz_c][:, sub_cols_exp2], dtype=np.float32),
            np.asarray(X_darp[nz_c][:, darp_cols_exp2], dtype=np.float32),
            X_vis_c_dir[nz_c],
        ]))[:, 1].astype(np.float32)
        pi_t2_c[nz_c] = np.clip(0.029 * raw_t2 * tip_env_c[nz_c], 0.0, 0.038)
        if do_live and nz_lv is not None:
            raw_t2_lv = clf_t2.predict_proba(np.hstack([
                np.asarray(X_sub[nz_lv][:, sub_cols_exp2], dtype=np.float32),
                np.asarray(X_darp[nz_lv][:, darp_cols_exp2], dtype=np.float32),
                X_vis_full_dir[nz_lv],
            ]))[:, 1].astype(np.float32)
            p_tip_e2_live[nz_lv] += 0.25 * np.clip(0.029 * raw_t2_lv * tip_env_full[nz_lv], 0.0, 0.038)

        # Also score SegmentHoldout fold (using seg_holdout.folds[cell.fold]["visible"] strictly!)
        if do_live:
            f_seg = seg_holdout.folds[cell.fold]
            X_vis_s, aux_s = htcads.compute_visible_catalogue_features(f_seg["visible"], foot)
            X_vis_s_dir = X_vis_s[:, vis_cols_dir].copy()
            tip_env_s = (np.clip(np.maximum(X_vis_s_dir[:, 0], X_vis_s_dir[:, 1]), 0.0, 1.0) ** 0.65).astype(np.float32)
            nz_s = np.flatnonzero(tip_env_s > 0.02)
            pi_ts = np.zeros(n_fp, dtype=np.float32)
            raw_ts = clf_t2.predict_proba(np.hstack([
                np.asarray(X_sub[nz_s][:, sub_cols_exp2], dtype=np.float32),
                np.asarray(X_darp[nz_s][:, darp_cols_exp2], dtype=np.float32),
                X_vis_s_dir[nz_s],
            ]))[:, 1].astype(np.float32)
            pi_ts[nz_s] = np.clip(0.029 * raw_ts * tip_env_s[nz_s], 0.0, 0.038)
            d_vs = aux_s["d_vis"]
            el_s2 = foot & (d_vs > 2.0)
            el_s3 = foot & np.where(
                (aux_s["tip_cone_2d"] >= 0.52) | (aux_s["relay_2d"] >= 0.42),
                d_vs > 1.65,
                d_vs > 2.10,
            )
            pi_se2 = _axial_smooth(_to_2d(1.0 - (1.0 - pi_ts) * (1.0 - pi_blind_e2_oof)))
            seg_preds_by_exp["DARP-EXP-2"].append(htcads.emit_submodular_celf(pi_se2, el_s2, max_dots=37654).astype(np.uint8))
            em_s3, _ = darp_mt10.emit_submodular_celf_with_trace(
                pi_se2, el_s3, max_dots=40500, expected_total_truth=12691.0, dinkelbach_stop=True, min_dots=33500
            )
            seg_preds_by_exp["DARP-EXP-3"].append(em_s3.astype(np.uint8))
            del X_vis_s, aux_s, X_vis_s_dir, tip_env_s, pi_ts, raw_ts, d_vs, el_s2, el_s3, pi_se2, em_s3

        del clf_t2, raw_t2, X_vis_c_dir, tip_env_c

        pi_e2_2d = _axial_smooth(_to_2d(1.0 - (1.0 - pi_t2_c) * (1.0 - pi_blind_e2_oof)))
        del pi_t2_c
        em2 = htcads.emit_submodular_celf(pi_e2_2d, elig_b2_c, max_dots=37654, marginal_bar=0.0)
        cell_em_by_exp["DARP-EXP-2"][cell.key] = em2[cell.bbox].copy()
        del em2

        em3, _ = darp_mt10.emit_submodular_celf_with_trace(
            pi_e2_2d, elig_tip_c, max_dots=40500, expected_total_truth=12691.0, dinkelbach_stop=True, min_dots=33500
        )
        cell_em_by_exp["DARP-EXP-3"][cell.key] = em3[cell.bbox].copy()
        del pi_e2_2d, em3
        gc.collect()
        print(f"[DARP-MT10] Emitted OOF masks for {cell.key} in {time.time()-t0:.1f}s", flush=True)

    # ------------------------------------------------------------------
    # Full-Footprint Live Candidate Surfaces + Rule 1 Pre/Post Uniqueness
    # ------------------------------------------------------------------
    pi_live_e1 = _axial_smooth(_to_2d(1.0 - (1.0 - p_tip_e1_live) * (1.0 - pi_blind_e1_full)))
    pi_live_e2 = _axial_smooth(_to_2d(1.0 - (1.0 - p_tip_e2_live) * (1.0 - pi_blind_e2_full)))

    em_live_e1, tr_e1 = darp_mt10.emit_submodular_celf_with_trace(pi_live_e1, elig_b2_live, max_dots=37654, dinkelbach_stop=False)
    em_live_e2, tr_e2 = darp_mt10.emit_submodular_celf_with_trace(pi_live_e2, elig_b2_live, max_dots=37654, dinkelbach_stop=False)
    em_live_e3, tr_e3 = darp_mt10.emit_submodular_celf_with_trace(
        pi_live_e2, elig_tipcone_live, max_dots=40500, expected_total_truth=12691.0, dinkelbach_stop=True, min_dots=33500
    )

    live_specs = [
        ("DARP-EXP-1", "DARP-SubsurfUpdip-MT-SeismoThermal (0% topo scarp, B=2.0)", pi_live_e1, em_live_e1, tr_e1),
        ("DARP-EXP-2", "DARP-MT10-SeamlessPiedmont-TriRegime (10m+3m+1m fusion, B=2.0)", pi_live_e2, em_live_e2, tr_e2),
        ("DARP-EXP-3", "DARP-MT10-Dinkelbach-TipCone (Fractional-programming budget + tip collar)", pi_live_e2, em_live_e3, tr_e3),
    ]

    exp_records = []
    for exp_id, desc, pi_lv, em_lv, celf_tr in live_specs:
        hr_res = holdout.evaluate_hide_and_recover(cell_em_by_exp[exp_id], ctx, b_visible_px=0.0, n_boot=1000, seed=20261027, name=exp_id)
        hr_del = holdout.paired_bootstrap_delta(hr_res, ref_hr, boot_key="_boots")

        sg_res = holdout.evaluate_sgmc_with_ci(em_lv, ctx, n_boot=1000, seed=20261027, name=exp_id)
        sg_del = holdout.paired_bootstrap_delta(sg_res, ref_sg, boot_key="_cal_boots")

        cp_res = darp_mt10.evaluate_c_pied_with_ci(em_lv, ctx, cp_ctx, n_boot=1000, seed=20261027, name=exp_id)
        cp_del = holdout.paired_bootstrap_delta(cp_res, ref_cp, boot_key="_boots")

        seg_res = seg_holdout.summarize(seg_preds_by_exp[exp_id], ci_draws=1000)
        seg_del = seg_holdout.compare_paired(seg_preds_by_exp[exp_id], seg_ref_preds, ci_draws=1000, seed=20261027)

        uniq_res = _audit_uniqueness(pi_lv, em_lv, foot, registry, reg_sample_idx, exact_lattice_info)

        # LiDAR-void coverage balance diagnostic
        dots_in_void = int((em_lv & foot & ~_to_2d(lidar_valid_fp.astype(np.float32)).astype(bool)).sum())
        n_dots = int(em_lv.sum())
        void_share = dots_in_void / max(n_dots, 1)

        rec = {
            "id": exp_id,
            "description": desc,
            "emitted_dots": n_dots,
            "lidar_void_dot_share": round(void_share, 5),
            "footprint_void_share": round(float((~lidar_valid_fp).mean()), 5),
            "celf_trace": celf_tr,
            "hide_and_recover": {
                "score_label": "HOLDOUT-DTI",
                "evaluator_version": holdout.HIDE_RECOVER_EVALUATOR_VERSION + ".1-fp-conserved",
                "n_withheld_positives": hr_res["n_withheld_positives"],
                "pooled_dti": round(hr_res["pooled_dti"], 6),
                "ci95": [round(x, 6) for x in hr_res["ci95_cluster_bootstrap"]],
                "per_quadrant_dti": {k: round(v, 6) for k, v in hr_res["per_quadrant_dti"].items()},
                "paired_delta_vs_02778_champ": round(hr_del["delta"], 6),
                "paired_delta_ci95": [round(x, 6) for x in hr_del["ci95"]],
                "win_prob_vs_02778_champ": round(hr_del["win_prob"], 4),
                "beats_02778_strictly": bool(hr_del["ci95_strictly_positive"]),
            },
            "gems_segment_pooled_v1": {
                "score_label": "HOLDOUT-DTI",
                "evaluator_version": seg_res["evaluator_version"],
                "n_withheld_positives": seg_res["n_withheld_positive_pixels"],
                "pooled_dti": round(float(seg_res["dti"]), 6),
                "ci95": _extract_ci95(seg_res["ci95"]),
                "paired_delta_vs_d28_b2": round(float(seg_del["paired_delta_dti"]), 6),
                "paired_delta_ci95": _extract_ci95(seg_del["paired_delta_ci95"]),
                "fold_wins": seg_del["fold_wins"],
            },
            "sgmc_off_catalogue": {
                "score_label": "HOLDOUT-DTI",
                "evaluator_version": holdout.SGMC_EVALUATOR_VERSION,
                "n_withheld_positives": sg_res["n_withheld_positives"],
                "raw_pooled_dti": round(sg_res["sgmc_raw_pooled_dti"], 6),
                "raw_ci95": [round(x, 6) for x in sg_res["sgmc_raw_ci95"]],
                "prevalence_calibrated_dti": round(sg_res["sgmc_prevalence_calibrated_dti"], 6),
                "calibrated_ci95": [round(x, 6) for x in sg_res["sgmc_calibrated_ci95"]],
                "paired_delta_vs_02778_champ": round(sg_del["delta"], 6),
                "paired_delta_ci95": [round(x, 6) for x in sg_del["ci95"]],
                "beats_02778_strictly": bool(sg_del["ci95_strictly_positive"]),
            },
            "c_pied_piedmont_off_catalogue": {
                "score_label": "HOLDOUT-DTI",
                "evaluator_version": darp_mt10.C_PIED_EVALUATOR_VERSION,
                "n_withheld_positives": cp_res["n_withheld_positives"],
                "pooled_dti": round(cp_res["pooled_dti"], 6),
                "ci95": [round(x, 6) for x in cp_res["ci95_cluster_bootstrap"]],
                "paired_delta_vs_02778_champ": round(cp_del["delta"], 6),
                "paired_delta_ci95": [round(x, 6) for x in cp_del["ci95"]],
                "beats_02778_strictly": bool(cp_del["ci95_strictly_positive"]),
            },
            "uniqueness": uniq_res,
            "_mask": em_lv,
        }
        exp_records.append(rec)
        print(
            f"\n[{exp_id}] dots={n_dots:,} void_share={void_share:.2%} (fp_void=24.60%)\n"
            f"  HIDE-RECOVER-v3.1 : {hr_res['pooled_dti']:.6f} (Δ vs 0.2778 = {hr_del['delta']:+.6f}, CI {hr_del['ci95']}, win={hr_del['win_prob']:.1%})\n"
            f"  gems-segment-v1   : {seg_res['dti']:.6f} (Δ vs D2.8-B2 = {seg_del['paired_delta_dti']:+.6f}, folds={seg_del['fold_wins']}/4)\n"
            f"  SGMC-CAL-v3.0     : {sg_res['sgmc_prevalence_calibrated_dti']:.6f} (Δ vs 0.2778 = {sg_del['delta']:+.6f}, CI {sg_del['ci95']})\n"
            f"  C-PIED-v1.0       : {cp_res['pooled_dti']:.6f} (Δ vs 0.2778 = {cp_del['delta']:+.6f}, CI {cp_del['ci95']})\n"
            f"  Uniqueness (det)  : pass={uniq_res['detector_protocol_passed']} max_3px_det={uniq_res['final_dots_max_detector_3px_overlap']:.4%} "
            f"({uniq_res['final_dots_closest_3px_detector_peer']}) | vs 11a2f251={uniq_res['named_benchmarks'].get('PRIOR_KG2_HTCADS_11a2f251', {}).get('our_in_peer_3px', -1):.4%} "
            f"| max_|rho|_surf={uniq_res['pre_placement_surface_max_abs_spearman']:.4f}",
            flush=True,
        )

    # Select winning gate-passing experiment (or best diagnostic experiment if none passes)
    passing = [
        r for r in exp_records
        if r["uniqueness"]["detector_protocol_passed"]
        and r["hide_and_recover"]["beats_02778_strictly"]
        and r["sgmc_off_catalogue"]["beats_02778_strictly"]
        and r["c_pied_piedmont_off_catalogue"]["beats_02778_strictly"]
    ]
    chosen = max(passing, key=lambda r: r["hide_and_recover"]["pooled_dti"]) if passing else max(exp_records, key=lambda r: r["hide_and_recover"]["pooled_dti"])
    chosen_mask = chosen["_mask"]

    # Write brand-new unique portal-safe GeoTIFF (-zeros.tif) + single-TIFF .zip
    ts_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    mask_hash8 = hashlib.sha256(np.packbits(chosen_mask.ravel()).tobytes()).hexdigest()[:8]
    exp_slug = chosen["id"].lower()
    sub_stem = f"kanlergems2-{exp_slug}-{chosen['emitted_dots']}dots-{ts_str}-{mask_hash8}-zeros"
    tif_name = f"{sub_stem}.tif"
    zip_name = f"{sub_stem}.zip"
    tif_path = dldir / tif_name
    zip_path = dldir / zip_name

    arr_out = np.where(foot & chosen_mask, 1.0, 0.0).astype(np.float32)
    with rasterio.open(ddir / "sample_submission.tif") as tmpl:
        prof = tmpl.profile.copy()
    prof.update(dtype="float32", count=1, nodata=None, compress="deflate", predictor=3)
    with rasterio.open(tif_path, "w", **prof) as dst:
        dst.write(arr_out, 1)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(tif_path, arcname=tif_name)

    tif_sha = submission.sha256_file(tif_path)
    zip_sha = submission.sha256_file(zip_path)
    assert tif_sha not in all_file_shas, "Generated GeoTIFF SHA-256 collided with existing file!"

    fmt_audit = submission.audit_geotiff(
        tif_path, foot=foot, labels=ctx.labels, mode="zeros", template_tif=ddir / "sample_submission.tif"
    )
    assert fmt_audit["all_checks_passed"], f"Format audit failed: {fmt_audit}"

    wall_s = time.time() - t_start
    verdict = "promote" if (passing and fmt_audit["all_checks_passed"] and wall_s <= 7200.0) else "negative"

    for r in exp_records:
        r.pop("_mask", None)

    top_imp = sorted(zip(exp2_feature_names, exp2_importances.tolist()), key=lambda x: x[1], reverse=True)

    summary = {
        "lane_id": "KANLERGEMSDOE2-DARP-MT10-20261027",
        "branch": _git_branch(),
        "generated_at_utc": ts_str,
        "wall_seconds": round(wall_s, 2),
        "wall_hours": round(wall_s / 3600.0, 4),
        "within_protocol_budget": {
            "experiments_run": len(exp_records),
            "max_experiments": 3,
            "wall_hours": round(wall_s / 3600.0, 4),
            "max_wall_hours": 2.0,
            "live_drivendata_slots_spent": 0,
            "passed": bool(len(exp_records) <= 3 and wall_s <= 7200.0),
        },
        "reference_benchmarks": {
            "GEMSDOE32_B2_0p2778_champ": {
                "user_reported_live_score": 0.2778,
                "hide_recover_v3_1_dti": round(ref_hr["pooled_dti"], 6),
                "hide_recover_ci95": [round(x, 6) for x in ref_hr["ci95_cluster_bootstrap"]],
                "gems_segment_v1_dti": round(float(ref_seg["dti"]), 6),
                "gems_segment_v1_ci95": _extract_ci95(ref_seg["ci95"]),
                "sgmc_cal_v3_0_dti": round(ref_sg["sgmc_prevalence_calibrated_dti"], 6),
                "sgmc_cal_ci95": [round(x, 6) for x in ref_sg["sgmc_calibrated_ci95"]],
                "c_pied_v1_0_dti": round(ref_cp["pooled_dti"], 6),
                "c_pied_ci95": [round(x, 6) for x in ref_cp["ci95_cluster_bootstrap"]],
            },
            "PRIOR_HTCADS_EXP2_11a2f251": {
                "sgmc_cal_v3_0_dti": round(prior_htcads_sg["sgmc_prevalence_calibrated_dti"], 6) if prior_htcads_sg else None,
                "c_pied_v1_0_dti": round(prior_htcads_cp["pooled_dti"], 6) if prior_htcads_cp else None,
            },
        },
        "exact_13gems_lattice_pigeonhole": exact_lattice_info,
        "experiments": exp_records,
        "selected_experiment_id": chosen["id"],
        "verdict": verdict,
        "submission_artifact": {
            "submission_name": sub_stem,
            "submission_filename": tif_name,
            "zip_filename": zip_name,
            "raster_sha256": tif_sha,
            "zip_sha256": zip_sha,
            "bytes": tif_path.stat().st_size,
            "zip_bytes": zip_path.stat().st_size,
            "emitted_dots": chosen["emitted_dots"],
            "format_audit": fmt_audit,
        },
        "top_20_feature_gain": [{"feature": f, "gain": round(g, 2)} for f, g in top_imp[:20]],
    }
    out_json = edir / "darp_mt10_experiments_20261027.json"
    out_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"\n[DARP-MT10] Completed all 3 pre-registered experiments in {wall_s:.1f}s -> verdict={verdict}", flush=True)
    print(f"[DARP-MT10] Emitted: docs/downloads/{tif_name} (sha256={tif_sha[:16]}...)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
