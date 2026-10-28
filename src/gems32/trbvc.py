"""Session-3 TRBVC: Two-Regime Depth-Partitioned Blind-Vent Conduit & Fault-Valve Breach Stack.

Implements the pre-registered label-free geological hypotheses frozen in
`knowledge/02_preregistered_hypotheses_kg2_s3_20261027.md` and
`registry/preregistration_trbvc_20261027.json`:

  - H-KG2S3-1 (TRBVC-Valve):
      * Continuous sedimentary-cover partition weight `w_basin(Z_b) = clip((Z_b - 120)/380, 0, 1)`
        resolving `IR-DARP-CREST-OVERDAMP-08` (separating shallow range-front calibration from
        concealed alluvial-basin/piedmont calibration).
      * Un-damped seamless 1 m LiDAR + 3 m 3DEP + 10 m 3DEP geomorphic scarp & toe-concavity
        void-bridge across 100% of the 24.60% (1,271,226-pixel) 1 m LiDAR void.
      * Survey-cohort-detrended shallow 1 m-to-2 m vertical conductive probe flux
        `(T2m - T1m) - median_{Area,Date}(T2m - T1m)` across 3,800 INGENIOUS stations.
      * Cold-aquifer (< 28 C) cryptothermal silica/cation geothermometer disequilibrium
        `max(T_chalc, T_quartz, T_cat) - T_meas >= 45 C` (isolating concealed blind upflow
        masked by shallow cold groundwater, free of mapped hot-spring bias).
      * Quaternary silica-cemented alluvial sand, hydrothermal explosion-crater & opaline
        sinter fault-valve rupture corridor (`DOE GDR #1391`) + smectite clay-cap breach.
  - H-KG2S3-2 (PGBI):
      * Exact 2-D Fourier Baranov/Blakely Poisson gravity-minus-pseudogravity decoupling ridge
        isolating titanomagnetite-leached hydrothermal fault damage zones from fresh igneous contacts.
  - H-KG2S3-3 (ATSD):
      * Off-catalogue opposing-dip accommodation-zone strike-divergence & antithetic hanging-wall
        basement rollover hinge (`Faulds & Hinz, 2015`).

Strictly 100% label-free: never reads `labels.tif`, `existing_faults.tif`, `dist_known_fault_px`,
or `derived_sgmc_faults_100m_u8.tif`. All channels verified by Protocol Rule 4 Leakage Canary
(single-feature holdout AUC <= 0.90) prior to model fitting.
"""
from __future__ import annotations

import gc
import json
import struct
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from scipy.ndimage import convolve, gaussian_filter
from sklearn.metrics import roc_auc_score

from . import darp_mt10, dslup, holdout, htcads

TRBVC_FEATURE_NAMES: list[str] = [
    # Cover-regime partition & listric depth-scaled gravity emergence
    "trbvc_w_basin_cover",              # 0: clip((Z_b - 120m)/380m, 0, 1) continuous basin cover weight
    "trbvc_dslup_listric_ridge",        # 1: 62->38 deg listric depth-scaled updip gravity ridge + strike coherence
    # Un-damped 100%-coverage void-bridging geomorphic scarps (resolves IR-DARP-CREST-OVERDAMP-08)
    "trbvc_unhab_scarp_void_bridge",    # 2: un-damped seamless 1m + 3m + 10m contour-ortho scarp centerline
    "trbvc_dem10_toe_concav",           # 3: 10m 3DEP range-front/piedmont foot-of-scarp concavity inflection
    # H-KG2S3-1: Blind geothermal-vent vertical heat flux, cold cryptothermal & fault-valve clay-cap breach
    "trbvc_probe2m_vert_flux_up",       # 4: cohort-detrended (T2m - T1m) upward conductive flux (regional)
    "trbvc_cold_cryptotherm_up",        # 5: T_meas < 28C silica/cation disequilibrium >= 45C plume (regional)
    "trbvc_silica_sand_valve_field",    # 6: silica-cemented sand / explosion-crater / sinter field (regional)
    "trbvc_clay_cap_valve_breach",      # 7: sharp structural/MT clay-cap breach x demag x vent upflow
    # H-KG2S3-2: 2-D Fourier Poisson gravity-minus-pseudogravity hydrothermal leaching decoupling
    "trbvc_poisson_grav_mag_decouple",  # 8: updip gravity step decoupled from Fourier RTP pseudogravity step
    # H-KG2S3-3: Off-catalogue accommodation-zone strike-divergence & rollover hinge
    "trbvc_accomm_strike_div",          # 9: opposing-dip / conjugate strike dispersion V_theta (R=1.2 km)
    "trbvc_rollover_hinge",             # 10: hanging-wall basement rollover convexity x transtensional dilation
    # Label-free concealed blind-vent physical conduit composite
    "trbvc_blind_vent_conduit_synth",   # 11: label-free concealed fault-valve + Poisson + accommodation composite
]

# Smooth (> 600 m) regional plumes excluded from raw GBDT splits so trees cannot memorize sparse station coords
TRBVC_REGIONAL_COLS: set[int] = {4, 5, 6}

# Fine topographic scarp channels excluded from TRBVC-EXP-1 (100% scarp/LiDAR-blind baseline)
TRBVC_TOPO_SCARP_COLS: set[int] = {2, 3}


def _fourier_pseudogravity_hgm(rtp: np.ndarray, foot: np.ndarray, dx_m: float = 100.0) -> np.ndarray:
    """Compute stabilized 2-D FFT Baranov (1957) / Blakely (1995) pseudogravity horizontal gradient magnitude.

    Under Poisson's relation, vertical integration in wavenumber space multiplies F(RTP) by
    `1 / (2*pi*|k| + k0)` (with gentle `dz = 150 m` upward continuation to suppress Nyquist grid ringing
    and `k0 = 2*pi / 35 km` basin-scale taper), placing magnetic contacts onto the exact same physical
    wavenumber support (`1/r` potential) as isostatic gravity before taking horizontal gradients.
    """
    H, W = rtp.shape
    pad = 48
    rtp_zm = (rtp - float(np.mean(rtp[foot]))).astype(np.float32)
    padded = np.pad(rtp_zm, ((pad, pad), (pad, pad)), mode="edge")
    del rtp_zm
    ky = np.fft.fftfreq(padded.shape[0], d=dx_m).astype(np.float32)[:, None]
    kx = np.fft.rfftfreq(padded.shape[1], d=dx_m).astype(np.float32)[None, :]
    k_mag = np.sqrt(ky * ky + kx * kx).astype(np.float32)
    k0 = np.float32(1.0 / 35000.0)
    transfer = (np.exp(-2.0 * np.pi * k_mag * 150.0) / (2.0 * np.pi * (k_mag + k0))).astype(np.float32)
    transfer[0, 0] = 0.0
    spec = np.fft.rfft2(padded)
    spec *= transfer
    pgrav = np.fft.irfft2(spec, s=padded.shape).astype(np.float32)[pad : pad + H, pad : pad + W].copy()
    del padded, spec, transfer, k_mag
    py, px = htcads._grad_yx_f32(gaussian_filter(pgrav, sigma=1.2, mode="nearest"))
    del pgrav
    hgm = np.hypot(py, px).astype(np.float32)
    del py, px
    return htcads._pos_norm_2d(hgm, foot, q=99.3)


def _parse_2m_vertical_flux_seeds(
    zpath: Path,
    transform: rasterio.Affine,
    shape: tuple[int, int],
) -> np.ndarray:
    """Extract survey-cohort-detrended shallow 1 m -> 2 m vertical conductive flux excess from 3,800 probes.

    Each survey campaign `(Area, Date[:6])` shares an ambient seasonal solar soil-temperature wave;
    subtracting the campaign median of `(T2m - T1m)` isolates local upward conductive geothermal heat
    flux `dT/dz > 0` above concealed blind upflow faults (Coolbaugh et al., 2007; Sladek et al., 2009).
    """
    grid = np.zeros(shape, dtype=np.float32)
    if not zpath.exists():
        return grid
    with zipfile.ZipFile(zpath) as zf:
        dbf = zf.read(
            "2m_temperature_probe_INGENIOUS_regional_data/2m_temperature_probe_n83geo/2m_temperature_probe_n83geo.dbf"
        )
    nrec, header_len, rec_len = struct.unpack("<IHH", dbf[4:12])
    fields = []
    pos = 32
    while dbf[pos] != 0x0D:
        fname = dbf[pos : pos + 11].split(b"\x00")[0].decode("ascii", errors="ignore")
        flen = dbf[pos + 16]
        fields.append((fname, flen))
        pos += 32

    wanted = {"Area", "Date", "T1m", "T15m", "T2m", "F2mDAB", "LatDegreeN", "LongDegree"}
    rows_parsed: list[dict] = []
    offset = header_len
    for _ in range(nrec):
        if offset + rec_len > len(dbf):
            break
        rec = dbf[offset : offset + rec_len]
        offset += rec_len
        if rec[0] == 0x2A:
            continue
        p = 1
        vals: dict[str, str] = {}
        for fname, flen in fields:
            if fname in wanted:
                vals[fname] = rec[p : p + flen].decode("utf-8", errors="ignore").strip()
            p += flen
        try:
            lon = float(vals["LongDegree"]) if vals.get("LongDegree") else np.nan
            lat = float(vals["LatDegreeN"]) if vals.get("LatDegreeN") else np.nan
        except ValueError:
            continue
        if not (np.isfinite(lon) and np.isfinite(lat) and -125.0 < lon < -110.0 and 35.0 < lat < 45.0):
            continue

        def _f(k: str) -> float:
            s = vals.get(k, "")
            if not s:
                return float("nan")
            try:
                v = float(s)
                return v if -10.0 < v < 130.0 else float("nan")
            except ValueError:
                return float("nan")

        t1 = _f("T1m")
        t15 = _f("T15m")
        t2 = _f("T2m")
        f2m = _f("F2mDAB")
        # Vertical conductive gradient proxy (deg C / m): prefer T2m - T1m, fallback 2*(T2m - T15m)
        dt_dz = float("nan")
        if np.isfinite(t2) and np.isfinite(t1):
            dt_dz = t2 - t1
        elif np.isfinite(t2) and np.isfinite(t15):
            dt_dz = 2.0 * (t2 - t15)
        cohort = f"{vals.get('Area', 'unk')[:24]}|{vals.get('Date', '')[:6]}"
        rows_parsed.append({"lon": lon, "lat": lat, "cohort": cohort, "dt_dz": dt_dz, "f2m": f2m})

    if not rows_parsed:
        return grid
    df = pd.DataFrame(rows_parsed)
    # Detrend seasonal solar wave per (Area, YYYYMM) cohort when >= 5 stations exist, else global median
    glob_med = float(df["dt_dz"].dropna().median()) if df["dt_dz"].notna().any() else 0.0
    cohort_cnt = df.groupby("cohort")["dt_dz"].transform("count")
    cohort_med = df.groupby("cohort")["dt_dz"].transform("median")
    ref_med = np.where(cohort_cnt >= 5, cohort_med, glob_med)
    dt_excess = df["dt_dz"].to_numpy(dtype=np.float64) - ref_med

    tr = Transformer.from_crs("EPSG:4269", "EPSG:32611", always_xy=True)
    xs, ys = tr.transform(df["lon"].to_numpy(), df["lat"].to_numpy())
    cols = np.floor((xs - transform.c) / transform.a).astype(np.int32)
    r_idx = np.floor((ys - transform.f) / transform.e).astype(np.int32)
    f2m_arr = df["f2m"].to_numpy(dtype=np.float64)

    for r, c, dte, f2 in zip(r_idx, cols, dt_excess, f2m_arr):
        if 0 <= r < shape[0] and 0 <= c < shape[1]:
            w = 0.0
            if np.isfinite(dte) and dte > 0.35:
                w += min((float(dte) - 0.25) / 2.2, 2.8)
            if np.isfinite(f2) and f2 > 0.75:
                w = max(w, min(float(f2) / 5.5, 2.5))
            if w > grid[r, c]:
                grid[r, c] = float(w)
    return grid


def build_trbvc_feature_stack(ddir: Path, cache_dir: Path) -> dict:
    """Build or load cached 12-channel label-free TRBVC feature stack on top of HTCADS (46) + DARP (18)."""
    darp_stack = darp_mt10.build_darp_feature_stack(ddir, cache_dir)
    foot = darp_stack["foot"]
    n_fp = int(foot.sum())
    shape = foot.shape

    trbvc_mmap_path = cache_dir / "X_trbvc_fp_f32.npy"
    meta_path = cache_dir / "trbvc_stack_meta.json"
    if trbvc_mmap_path.exists() and meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if (
                meta.get("schema_version") == "trbvc_v1"
                and int(meta.get("n_fp", -1)) == n_fp
                and meta.get("trbvc_features") == TRBVC_FEATURE_NAMES
            ):
                X_trbvc_ro = np.memmap(
                    trbvc_mmap_path, dtype="float32", mode="r", shape=(n_fp, len(TRBVC_FEATURE_NAMES))
                )
                return {
                    **darp_stack,
                    "X_trbvc": X_trbvc_ro,
                }
        except Exception:
            pass

    X_trbvc = np.memmap(trbvc_mmap_path, dtype="float32", mode="w+", shape=(n_fp, len(TRBVC_FEATURE_NAMES)))

    with rasterio.open(ddir / "sample_submission.tif") as ds:
        transform = ds.transform

    core_inds = None

    def _read_core(src, idx: int) -> np.ndarray:
        nonlocal core_inds
        a = src.read(idx).astype(np.float32)
        valid = foot & np.isfinite(a) & (a > -1e30)
        filled, core_inds = htcads._fill_outside_with_inds(a, valid, core_inds)
        return filled

    def _load_dem10(fname: str) -> np.ndarray:
        arr = np.zeros(shape, dtype=np.float32)
        v = np.load(ddir / "dem10" / fname).astype(np.float32)
        arr[foot] = np.where(np.isfinite(v), v, 0.0)
        filled, _ = htcads._fill_outside_with_inds(arr, foot, None)
        return filled

    with rasterio.open(ddir / "training_features.tif") as src:
        rtp = _read_core(src, 2)
        det_elev = _read_core(src, 12)
        iso_grav = _read_core(src, 13)
        zb_raw = _read_core(src, 15)
    del core_inds

    zb = np.clip(zb_raw, 0.0, 5000.0).astype(np.float32)
    del zb_raw

    # Col 0: Continuous sedimentary cover weight w_basin(Z_b) = clip((Z_b - 120m)/380m, 0, 1)
    w_basin_2d = np.clip((zb - 120.0) / 380.0, 0.0, 1.0).astype(np.float32)
    X_trbvc[:, 0] = w_basin_2d[foot]

    # Col 1: DSLUP listric depth-scaled (62->38 deg) updip gravity ridge + multi-height strike coherence
    dsl = dslup.build_dslup_fields(ddir, foot)
    dslup_2d = dsl["dslup_ridge"].astype(np.float32)
    del dsl
    X_trbvc[:, 1] = dslup_2d[foot]

    # Cols 2..3: Un-damped 100%-coverage void-bridging geomorphic scarp & 10m break-in-slope curvature
    # (Fixes IR-DARP-CREST-OVERDAMP-08: preserves full range-front scarp strength across the 24.60% 1m LiDAR void)
    scarp10_2d = 0.60 * _load_dem10("dem10_onesided.f32.npy") + 0.40 * _load_dem10("dem10_onesided3.f32.npy")
    hgm10_2d = 0.55 * _load_dem10("dem10_hgm50_max.f32.npy") + 0.45 * _load_dem10("dem10_hgm20_max.f32.npy")
    slp10_2d = _load_dem10("dem10_slope_max.f32.npy")
    curv10_2d = _load_dem10("dem10_curv_absmax.f32.npy")

    with rasterio.open(ddir / "external" / "tiger_road_distance_m.tif") as s_rd:
        road_d = s_rd.read(1).astype(np.float32)
    road_w = np.where(foot & np.isfinite(road_d), np.clip((road_d - 60.0) / 140.0, 0.25, 1.0), 1.0).astype(np.float32)
    del road_d

    elev_macro = gaussian_filter(det_elev, sigma=8.0, mode="nearest")
    emy, emx = htcads._grad_yx_f32(elev_macro)
    del elev_macro
    contour_theta = np.arctan2(emy, emx) + (np.pi / 2.0)
    macro_slope = np.hypot(emy, emx).astype(np.float32)
    del emy, emx
    _, strike_s10 = htcads._hessian_ridge_and_strike(scarp10_2d, sigma=1.1, foot=foot)
    sin2_ortho = (np.sin(strike_s10 - contour_theta) ** 2).astype(np.float32)
    del contour_theta, strike_s10
    flat_basin = np.clip(1.0 - macro_slope / (float(np.percentile(macro_slope[foot], 55.0)) + 1e-5), 0.0, 1.0)
    del macro_slope
    # Suppress contour-parallel Pleistocene shoreline benches only inside flat basins where basement gravity is quiet
    darp_updip_fp = np.asarray(darp_stack["X_darp"][:, 0], dtype=np.float32)
    grav_quiet_2d = np.ones(shape, dtype=np.float32)
    grav_quiet_2d[foot] = np.clip(1.0 - 2.0 * np.maximum(dslup_2d[foot], darp_updip_fp), 0.0, 1.0)
    shoreline_keep = (1.0 - 0.65 * flat_basin * grav_quiet_2d * (1.0 - sin2_ortho)).astype(np.float32)
    del flat_basin, grav_quiet_2d, sin2_ortho

    s10_unhab = htcads._pos_norm_2d(np.maximum(scarp10_2d, 0.0) * road_w * shoreline_keep, foot, q=99.4)
    h10_unhab = htcads._pos_norm_2d(np.maximum(hgm10_2d, 0.0) * road_w * shoreline_keep, foot, q=99.4)
    del scarp10_2d, hgm10_2d
    w10_unhab = htcads._multi_azimuth_worm(0.65 * s10_unhab + 0.35 * h10_unhab, length_px=13, foot=foot)

    s3_unhab = s10_unhab.copy()
    p_s3 = ddir / "external" / "h52_scarp3m_100m.tif"
    if p_s3.exists():
        with rasterio.open(p_s3) as s3:
            h07 = s3.read(1).astype(np.float32)
            h12 = s3.read(2).astype(np.float32)
            facing = s3.read(5).astype(np.float32)
            cov3 = s3.read(7)
        valid3 = foot & (cov3 > 2000) & (h07 >= 0) & (h12 >= 0)
        del cov3
        face_w = np.clip(np.maximum(facing, 0.0) / 10000.0, 0.25, 1.0)
        raw3 = (0.58 * np.maximum(h07, 0.0) + 0.42 * np.maximum(h12, 0.0)) * face_w * road_w * shoreline_keep
        del h07, h12, facing, face_w
        if valid3.any():
            q3 = float(np.percentile(raw3[valid3], 99.4)) + 1e-6
            norm3 = np.clip(raw3 / q3, 0.0, 1.0).astype(np.float32)
            s3_unhab = np.where(valid3, 0.65 * norm3 + 0.35 * s10_unhab, s10_unhab).astype(np.float32)
            del norm3
        del raw3, valid3

    lid_valid_fp = darp_stack["lidar_valid_fp"]
    lid_scarp_fp = (
        0.60 * np.asarray(darp_stack["X_lid"][:, 8], dtype=np.float32)
        + 0.40 * np.asarray(darp_stack["X_lid"][:, 9], dtype=np.float32)
    )
    base_void_fp = 0.48 * s3_unhab[foot] + 0.32 * w10_unhab[foot] + 0.20 * h10_unhab[foot]
    del s10_unhab, h10_unhab, w10_unhab, s3_unhab
    # Exact mean/std domain alignment across the 75.4% / 24.6% 1m LiDAR boundary (zero tile seam)
    raw_in = 0.52 * base_void_fp[lid_valid_fp] + 0.48 * lid_scarp_fp[lid_valid_fp]
    mu_void = float(np.mean(base_void_fp[~lid_valid_fp]))
    sd_void = float(np.std(base_void_fp[~lid_valid_fp])) + 1e-6
    mu_in = float(np.mean(raw_in))
    sd_in = float(np.std(raw_in)) + 1e-6
    seamless_fp = base_void_fp.copy()
    seamless_fp[lid_valid_fp] = np.clip((raw_in - mu_in) * (sd_void / sd_in) + mu_void, 0.0, 1.2)
    q_sm = float(np.percentile(seamless_fp, 99.5)) + 1e-6
    X_trbvc[:, 2] = np.clip(seamless_fp / q_sm, 0.0, 1.0).astype(np.float32)
    del lid_scarp_fp, base_void_fp, raw_in, seamless_fp

    # Col 3: 10m range-front / piedmont break-in-slope curvature inflection (curv_absmax * slope_max ridge)
    slp_r, _ = htcads._hessian_ridge_and_strike(slp10_2d, sigma=1.2, foot=foot)
    curv_norm = htcads._pos_norm_2d(np.maximum(curv10_2d, 0.0) * road_w * shoreline_keep, foot, q=99.2)
    del slp10_2d, curv10_2d, road_w, shoreline_keep
    toe10_2d = htcads._pos_norm_2d(0.55 * curv_norm + 0.45 * (curv_norm * slp_r * 2.0), foot, q=99.4)
    del slp_r, curv_norm
    X_trbvc[:, 3] = toe10_2d[foot]
    del toe10_2d
    gc.collect()

    # Hydraulic up-gradient unit vector from smoothed det_elev for thermal/cryptothermal plume back-projection
    elev_sm12 = gaussian_filter(det_elev, sigma=12.0, mode="nearest")
    del det_elev
    egy12, egx12 = htcads._grad_yx_f32(elev_sm12)
    del elev_sm12
    egnorm = np.hypot(egy12, egx12).astype(np.float32) + 1e-4
    sgate = np.clip(egnorm / (float(np.percentile(egnorm[foot], 65.0)) + 1e-4), 0.0, 1.0).astype(np.float32)
    uy_hyd = (egy12 / egnorm) * sgate
    ux_hyd = (egx12 / egnorm) * sgate
    del egy12, egx12, egnorm, sgate

    # Col 4: Survey-cohort-detrended 1m-to-2m vertical probe conductive flux excess (H-KG2S3-1)
    vflux_seeds = _parse_2m_vertical_flux_seeds(
        ddir / "external" / "2m_temperature_probe_INGENIOUS_regional_data.zip", transform, shape
    )
    vflux_up_2d = htcads._advective_upgradient_plume(vflux_seeds, uy_hyd, ux_hyd, foot)
    del vflux_seeds
    X_trbvc[:, 4] = vflux_up_2d[foot]

    # Col 5: Cold-aquifer (< 28 C) cryptothermal silica/cation geothermometer disequilibrium >= 45 C (H-KG2S3-1)
    # Strictly ignores `dist_known_fault_px` and excludes >= 28 C mapped hot springs!
    ws_df = pd.read_csv(
        ddir / "external" / "gdr_wellspring_in_footprint.csv",
        usecols=["row", "col", "temp_c", "geothermquartz_c", "geothermchalc_c", "geothermcat_c"],
    )
    crypto_seeds = np.zeros(shape, dtype=np.float32)
    for row in ws_df.itertuples(index=False):
        r, c = int(row.row), int(row.col)
        if 0 <= r < shape[0] and 0 <= c < shape[1]:
            t_meas = float(row.temp_c) if pd.notna(row.temp_c) and row.temp_c > -5.0 else 15.0
            if t_meas >= 28.0:
                continue  # Exclude hot surface springs (already mapped along catalogued range-front faults)
            t_geo = max(
                float(row.geothermchalc_c) if pd.notna(row.geothermchalc_c) else 0.0,
                float(row.geothermquartz_c) if pd.notna(row.geothermquartz_c) else 0.0,
                float(row.geothermcat_c) if pd.notna(row.geothermcat_c) else 0.0,
            )
            diseq = t_geo - t_meas
            if t_geo >= 68.0 and diseq >= 45.0:
                w = min((diseq - 40.0) / 65.0, 3.0)
                if w > crypto_seeds[r, c]:
                    crypto_seeds[r, c] = float(w)
    del ws_df
    crypto_up_2d = htcads._advective_upgradient_plume(crypto_seeds, uy_hyd, ux_hyd, foot)
    del crypto_seeds, uy_hyd, ux_hyd
    X_trbvc[:, 5] = crypto_up_2d[foot]

    # Col 6: Quaternary silica-cemented alluvial sand, explosion crater & opaline sinter fault-valve field
    valve_seeds = np.zeros(shape, dtype=np.float32)
    with zipfile.ZipFile(ddir / "external" / "paleo_geothermal_regional.zip") as zf:
        pal_df = pd.read_csv(zf.open("Paleo_geothermal_final.csv"), encoding="latin-1")
    tr_nad83 = Transformer.from_crs("EPSG:4269", "EPSG:32611", always_xy=True)
    pxs, pys = tr_nad83.transform(pal_df["Long_deg_NAD83"].to_numpy(), pal_df["Lat_deg_NAD83"].to_numpy())
    pcols = np.floor((pxs - transform.c) / transform.a).astype(np.int32)
    prows = np.floor((pys - transform.f) / transform.e).astype(np.int32)
    for r, c, dtype_s in zip(prows, pcols, pal_df["Deposit_type"].fillna("").astype(str)):
        if 0 <= r < shape[0] and 0 <= c < shape[1]:
            dl = dtype_s.lower()
            if "cemented" in dl or "explosion" in dl or "sinter" in dl:
                w = 3.0  # Direct silica/boiling fault-valve rupture in alluvial cover
            elif "alteration" in dl or "sulfur" in dl or "sulfate" in dl:
                w = 2.0  # Steam-heated acid-sulfate / argillic fault leak
            elif "tufa" in dl:
                w = 0.08  # Lake Lahontan wave-zone tufa mimic strongly suppressed
            else:
                w = 0.85  # Travertine carbonate spring
            if w > valve_seeds[r, c]:
                valve_seeds[r, c] = float(w)
    del pal_df, pxs, pys, pcols, prows
    valve_field_2d = htcads._pos_norm_2d(
        0.65 * gaussian_filter(valve_seeds, sigma=4.5, mode="nearest")
        + 0.35 * gaussian_filter(valve_seeds, sigma=10.0, mode="nearest"),
        foot,
        q=99.5,
    )
    del valve_seeds
    X_trbvc[:, 6] = valve_field_2d[foot]

    # Col 8 (computed before Col 7 so Poisson decoupling also informs blind conduit synthesis):
    # Exact 2-D Fourier Poisson Gravity-minus-Pseudogravity Hydrothermal Decoupling Ridge (H-KG2S3-2)
    pgrav_hgm = _fourier_pseudogravity_hgm(rtp, foot)
    del rtp
    hydro_demag_fp = np.asarray(darp_stack["X_sub"][:, 14], dtype=np.float32)
    grav_crest_fp = np.maximum.reduce([
        dslup_2d[foot],
        darp_updip_fp,
        np.asarray(darp_stack["X_darp"][:, 2], dtype=np.float32),  # darp_grav_tilt_k
        np.asarray(darp_stack["X_sub"][:, 1], dtype=np.float32),   # grav_ridge_s12
    ])
    poisson_dec_fp = (
        grav_crest_fp
        * np.clip(1.15 - pgrav_hgm[foot], 0.15, 1.0)
        * (1.0 + 0.55 * hydro_demag_fp)
    ).astype(np.float32)
    del pgrav_hgm
    q_pd = float(np.percentile(poisson_dec_fp, 99.4)) + 1e-6
    poisson_dec_fp = np.clip(poisson_dec_fp / q_pd, 0.0, 1.0).astype(np.float32)
    X_trbvc[:, 8] = poisson_dec_fp

    # Col 7: Fault-Valve Smectite Clay-Cap Breach Conduit (H-KG2S3-1)
    mt_edge_fp = np.asarray(darp_stack["X_sub"][:, 18], dtype=np.float32)
    mt_asym_fp = np.asarray(darp_stack["X_darp"][:, 4], dtype=np.float32)
    k_meta_fp = np.asarray(darp_stack["X_sub"][:, 15], dtype=np.float32)
    uth_fp = np.asarray(darp_stack["X_sub"][:, 17], dtype=np.float32)
    vent_plume_fp = np.maximum.reduce([
        vflux_up_2d[foot],
        crypto_up_2d[foot],
        valve_field_2d[foot],
        np.asarray(darp_stack["X_darp"][:, 6], dtype=np.float32),  # usgs_hf_resid_up
    ])
    del vflux_up_2d, crypto_up_2d, valve_field_2d

    clay_breach_raw = (
        (0.52 * mt_asym_fp + 0.48 * mt_edge_fp)
        * (0.35 + 0.65 * (0.45 * hydro_demag_fp + 0.30 * k_meta_fp + 0.25 * uth_fp))
        * (0.40 + 0.60 * grav_crest_fp)
        * (1.0 + 0.70 * vent_plume_fp)
    )
    del mt_edge_fp, hydro_demag_fp, k_meta_fp, uth_fp
    q_cb = float(np.percentile(clay_breach_raw, 99.4)) + 1e-6
    clay_breach_fp = np.clip(clay_breach_raw / q_cb, 0.0, 1.0).astype(np.float32)
    del clay_breach_raw
    X_trbvc[:, 7] = clay_breach_fp

    # Cols 9..10: Off-Catalogue Accommodation-Zone Strike-Divergence & Rollover Hinge (H-KG2S3-3)
    grav_r_s2, strike_g = htcads._hessian_ridge_and_strike(iso_grav, sigma=2.0, foot=foot)
    del iso_grav
    w_str = np.clip(grav_r_s2 + 0.05, 0.05, 1.05).astype(np.float32)
    c2 = gaussian_filter((w_str * np.cos(2.0 * strike_g)).astype(np.float32), sigma=10.0, mode="nearest")
    s2 = gaussian_filter((w_str * np.sin(2.0 * strike_g)).astype(np.float32), sigma=10.0, mode="nearest")
    wn = gaussian_filter(w_str, sigma=10.0, mode="nearest") + 1e-6
    del strike_g, w_str
    r_coh = np.clip(np.hypot(c2, s2) / wn, 0.0, 1.0).astype(np.float32)
    del c2, s2, wn
    accomm_2d = ((1.0 - r_coh) * np.clip(grav_r_s2 * 1.8 + 0.15, 0.0, 1.0)).astype(np.float32)
    del r_coh, grav_r_s2
    accomm_worm = htcads._multi_azimuth_worm(htcads._pos_norm_2d(accomm_2d, foot, q=99.3), length_px=13, foot=foot)
    del accomm_2d
    X_trbvc[:, 9] = accomm_worm[foot]

    zb_sm = gaussian_filter(zb, sigma=2.5, mode="nearest")
    zb_lap_pos = np.maximum(
        convolve(zb_sm, np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32), mode="nearest"),
        0.0,
    )
    del zb_sm
    # Intermediate alluvial-basin depth envelope [100 m .. 1400 m] where hanging-wall antithetic rollover hinges root
    hinge_depth_gate = (
        np.clip((zb - 80.0) / 180.0, 0.0, 1.0) * np.clip((1800.0 - zb) / 900.0, 0.20, 1.0)
    ).astype(np.float32)
    del zb
    lap_norm = htcads._pos_norm_2d(zb_lap_pos * hinge_depth_gate, foot, q=99.3)
    del zb_lap_pos, hinge_depth_gate
    td_stress_fp = np.asarray(darp_stack["X_darp"][:, 14], dtype=np.float32)
    rollover_fp = (
        (0.55 * lap_norm[foot] + 0.45 * accomm_worm[foot])
        * (0.45 + 0.55 * td_stress_fp)
        * (0.35 + 0.65 * grav_crest_fp)
    )
    del lap_norm, accomm_worm
    q_ro = float(np.percentile(rollover_fp, 99.4)) + 1e-6
    rollover_fp = np.clip(rollover_fp / q_ro, 0.0, 1.0).astype(np.float32)
    X_trbvc[:, 10] = rollover_fp

    # Col 11: Label-free blind-vent + Poisson-decoupled + accommodation-hinge concealed conduit composite
    blind_vent_synth = (
        (
            0.26 * dslup_2d[foot]
            + 0.22 * poisson_dec_fp
            + 0.24 * clay_breach_fp
            + 0.16 * mt_asym_fp
            + 0.12 * rollover_fp
        )
        * (0.50 + 0.50 * w_basin_2d[foot])
        * (1.0 + 0.35 * vent_plume_fp + 0.25 * td_stress_fp)
    )
    q_bvs = float(np.percentile(blind_vent_synth, 99.5)) + 1e-6
    X_trbvc[:, 11] = np.clip(blind_vent_synth / q_bvs, 0.0, 1.0).astype(np.float32)
    del (
        w_basin_2d,
        dslup_2d,
        darp_updip_fp,
        grav_crest_fp,
        poisson_dec_fp,
        clay_breach_fp,
        mt_asym_fp,
        vent_plume_fp,
        td_stress_fp,
        rollover_fp,
        blind_vent_synth,
    )

    X_trbvc.flush()
    meta_path.write_text(
        json.dumps(
            {
                "schema_version": "trbvc_v1",
                "n_fp": n_fp,
                "trbvc_features": TRBVC_FEATURE_NAMES,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    X_trbvc_ro = np.memmap(trbvc_mmap_path, dtype="float32", mode="r", shape=(n_fp, len(TRBVC_FEATURE_NAMES)))
    gc.collect()
    return {
        **darp_stack,
        "X_trbvc": X_trbvc_ro,
    }


def run_full_trbvc_leakage_canary(trbvc_stack: dict, ctx: holdout.HoldoutContext, seed: int = 20261027) -> dict:
    """Protocol Rule 4: Single-feature holdout AUC <= 0.90 across ALL 80 channels (36 sub + 10 lid + 18 darp + 12 trbvc + 4 vis)."""
    darp_res = darp_mt10.run_full_darp_leakage_canary(trbvc_stack, ctx, seed=seed)
    foot = trbvc_stack["foot"]
    X_trbvc = trbvc_stack["X_trbvc"]

    fp_idx_2d = np.full(foot.shape, -1, dtype=np.int32)
    fp_idx_2d[foot] = np.arange(int(foot.sum()), dtype=np.int32)
    rng = np.random.default_rng(seed)

    pos_fp_list, neg_fp_list = [], []
    for cell in ctx.cells:
        if cell.seed != 20:
            continue
        sl = cell.bbox
        fp_sub = fp_idx_2d[sl]
        ty, tx = cell.truth_coords
        p_fp = fp_sub[ty, tx]
        p_fp = p_fp[p_fp >= 0]
        neg_mask = cell.active_sub & (cell.k_dg_sub == 0.0)
        ny, nx = np.nonzero(neg_mask)
        n_fp = fp_sub[ny, nx]
        n_fp = n_fp[n_fp >= 0]
        if n_fp.size > 60_000:
            n_fp = rng.choice(n_fp, size=60_000, replace=False)
        pos_fp_list.append(p_fp)
        neg_fp_list.append(n_fp)

    pos_idx = np.concatenate(pos_fp_list)
    neg_idx = np.concatenate(neg_fp_list)
    y_eval = np.concatenate([np.ones(pos_idx.size, dtype=np.int8), np.zeros(neg_idx.size, dtype=np.int8)])
    all_idx = np.concatenate([pos_idx, neg_idx])

    features = list(darp_res["features"])
    for j, name in enumerate(TRBVC_FEATURE_NAMES):
        vals = np.asarray(X_trbvc[all_idx, j], dtype=np.float32)
        assert np.isfinite(vals).all(), f"Non-finite values in TRBVC feature {name}"
        auc = float(roc_auc_score(y_eval, vals))
        sym_auc = max(auc, 1.0 - auc)
        features.append(
            {
                "feature": name,
                "group": "trbvc_s3_new",
                "raw_auc": round(auc, 6),
                "oriented_auc": round(sym_auc, 6),
            }
        )

    features.sort(key=lambda r: r["oriented_auc"], reverse=True)
    max_auc = float(features[0]["oriented_auc"])
    return {
        "protocol_rule": "Rule 4 Leakage Canary (single-feature holdout AUC <= 0.90)",
        "evaluator": "GEMSDOE32-HIDE-RECOVER-v3.0 (draw20 spatially-blocked withheld segments)",
        "threshold": 0.90,
        "total_features_tested": len(features),
        "n_withheld_positive_pixels_tested": int(pos_idx.size),
        "n_negative_pixels_tested": int(neg_idx.size),
        "max_single_feature_auc": round(max_auc, 6),
        "max_feature_name": features[0]["feature"],
        "passed": bool(max_auc <= 0.90),
        "features": features,
    }
