#!/usr/bin/env python3
"""Build leak-free, EDT-border-repaired 60-channel physical & geothermal feature stack (`KG2-H1`).

Memory & speed engineered for 2 vCPUs / 3.8 GiB RAM (0 swap):
  - Feature-major memmap `(60, 5_167_373)` `float32` (`.cache/fvca_stack_fp.npy`) so each channel
    writes one contiguous 20.7 MB block without pinning 1.24 GB in page cache.
  - Precomputes EDT nearest-neighbor index maps ONCE (`~foot` and competition sentinel mask)
    instead of 27 separate full-grid EDT passes.
  - Uses `4x4` normal equations (`X^T X \\ X^T y`) instead of `5.17M x 4` LAPACK SVD (`lstsq`).
  - Zero catalogue/label leakage: NEVER reads `labels.tif`, `existing_faults.tif`,
    `gdr_qfaults_traces.csv`, `dist_known_fault_px`, or `derived_sgmc_faults_100m_u8.tif`.
"""
from __future__ import annotations

import csv
import gc
import io
import json
import resource
import struct
import time
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import transform as rio_transform
from scipy.ndimage import distance_transform_edt, gaussian_filter

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EXT = DATA / "external"
CACHE = ROOT / ".cache"

COMP_NAMES = [
    "b01_curie_depth",
    "b02_rtp",
    "b03_tmi_hg",
    "b04_geod_2ndinv",
    "b05_iso_grav_slope",
    "b06_rad_tc",          # Verified: GeoDAWN Radiometric Total Count (Spearman 0.99995 with rad TC)
    "b07_geod_shearrate",
    "b08_geod_dilaterate",
    "b09_tmi_vg",
    "b10_deq_n100a15",
    "b11_iso_grav_vg",
    "b12_det_elev",
    "b13_iso_grav_anom",
    "b14_tmi",
    "b15_depth_to_base",
    "b16_ieq_n100a15",
    "b17_cond_surf",
    "b18_iso_grav_hg",
    "b19_det_elev_slope",
]

STRUCT_DERIVED_NAMES = [
    "elev_ridge_s10",
    "elev_ridge_s25",
    "elev_ridge_s50",
    "grav_ridge_s15",
    "grav_ridge_s40",
    "rtp_ridge_s15",
    "elev_st_coh_s25",
    "grav_st_coh_s30",
    "xgrad_mag_grav",
    "xgrad_grav_elev",
    "xstrike_align_elev_grav",
    "tmi_vcont_resid150",
    "mag_basement_depth_disc",
    "rad_K",
    "rad_Th",
    "rad_U",
    "ext_ThK",
    "ext_UK",
    "ext_UTh",
    "lid_ex",
    "lid_step",
    "lid_lap",
    "lid_coh",
    "road_dist_log",
    "lid_scarp_tectonic",
]

FVCA_GEOTHERM_NAMES = [
    "probe2m_dab_s4",
    "probe2m_dab_s12",
    "probe2m_t2m_s8",
    "paleo_sinter_s5",
    "paleo_sinter_s15",
    "spring_chem_s4",
    "spring_chem_s12",
    "volc_vent_s15",
    "fvca_upslope_600m",
    "fvca_upslope_1800m",
    "potassic_mag_low",
    "cond_playa_resid",
    "cond_seal_grad",
    "coulomb_dilatancy_frac",
    "seismo_strain_coupling",
    "fvca_joint_conduit",
]

ALL_FEATURE_NAMES = COMP_NAMES + STRUCT_DERIVED_NAMES + FVCA_GEOTHERM_NAMES
assert len(ALL_FEATURE_NAMES) == 60


def apply_edt_indices(arr: np.ndarray, bad: np.ndarray, idx_map: np.ndarray) -> np.ndarray:
    x = np.asarray(arr, dtype=np.float32).copy()
    if bad.any():
        x[bad] = x[idx_map[0, bad], idx_map[1, bad]]
    # Handle any isolated extra non-finite pixels (e.g. 12 extra cells in B06) via local median/neighbor
    rem = (~np.isfinite(x)) | (x < -1e30) | (x > 1e30)
    if rem.any():
        _, idx2 = distance_transform_edt(rem, return_indices=True)
        x[rem] = x[idx2[0, rem], idx2[1, rem]]
    return x


def zscore_fp(arr: np.ndarray, foot: np.ndarray) -> np.ndarray:
    v = arr[foot]
    mu = float(np.mean(v, dtype=np.float64))
    sd = float(np.std(v, dtype=np.float64)) + 1e-6
    return ((arr - mu) / sd).astype(np.float32)


def hessian_ridge_pos(arr: np.ndarray, sigma: float) -> np.ndarray:
    gxx = gaussian_filter(arr, sigma=sigma, order=(0, 2), mode="nearest")
    gyy = gaussian_filter(arr, sigma=sigma, order=(2, 0), mode="nearest")
    gxy = gaussian_filter(arr, sigma=sigma, order=(1, 1), mode="nearest")
    tr = 0.5 * (gxx + gyy)
    rad = np.sqrt(np.maximum(0.25 * (gxx - gyy) ** 2 + gxy * gxy, 0.0))
    lam_min = tr - rad
    return (np.maximum(-lam_min, 0.0) * (sigma * sigma)).astype(np.float32)


def structure_tensor_coherence(arr: np.ndarray, grad_sigma: float, win_sigma: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    gx = gaussian_filter(arr, sigma=grad_sigma, order=(0, 1), mode="nearest")
    gy = gaussian_filter(arr, sigma=grad_sigma, order=(1, 0), mode="nearest")
    jxx = gaussian_filter(gx * gx, sigma=win_sigma, mode="nearest")
    jyy = gaussian_filter(gy * gy, sigma=win_sigma, mode="nearest")
    jxy = gaussian_filter(gx * gy, sigma=win_sigma, mode="nearest")
    coh = np.sqrt(np.maximum((jxx - jyy) ** 2 + 4.0 * jxy * jxy, 0.0)) / (jxx + jyy + 1e-6)
    return coh.astype(np.float32), gx.astype(np.float32), gy.astype(np.float32)


def _parse_2m_probes(foot: np.ndarray, tr: rasterio.Affine) -> tuple[np.ndarray, np.ndarray]:
    H, W = foot.shape
    dab_grid = np.zeros((H, W), dtype=np.float32)
    t2m_grid = np.zeros((H, W), dtype=np.float32)
    zpath = EXT / "2m_temperature_probe_INGENIOUS_regional_data.zip"
    with zipfile.ZipFile(zpath) as z:
        shp = z.read("2m_temperature_probe_INGENIOUS_regional_data/2m_temperature_probe_n83geo/2m_temperature_probe_n83geo.shp")
        dbf = z.read("2m_temperature_probe_INGENIOUS_regional_data/2m_temperature_probe_n83geo/2m_temperature_probe_n83geo.dbf")

    num_rec, hdr_len, rec_len = struct.unpack("<IHH", dbf[4:12])
    fields = []
    pos = 32
    while pos < hdr_len - 1 and dbf[pos] != 0x0D:
        fname = dbf[pos : pos + 11].split(b"\x00")[0].decode("ascii", errors="replace")
        fields.append((fname, dbf[pos + 16]))
        pos += 32

    pts = []
    s_pos = 100
    while s_pos < len(shp):
        _, content_len = struct.unpack(">II", shp[s_pos : s_pos + 8])
        s_pos += 8
        stype = struct.unpack("<I", shp[s_pos : s_pos + 4])[0]
        if stype in (1, 11, 21):
            pts.append(struct.unpack("<dd", shp[s_pos + 4 : s_pos + 20]))
        else:
            pts.append((np.nan, np.nan))
        s_pos += content_len * 2

    xs, ys = rio_transform("EPSG:4269", "EPSG:32611", [p[0] for p in pts], [p[1] for p in pts])
    cols = np.floor((np.asarray(xs) - tr.c) / tr.a).astype(np.int32)
    rows = np.floor((np.asarray(ys) - tr.f) / tr.e).astype(np.int32)

    r_pos = hdr_len
    for i in range(min(num_rec, len(pts))):
        rec = dbf[r_pos : r_pos + rec_len]
        r_pos += rec_len
        r, c = int(rows[i]), int(cols[i])
        if not (0 <= r < H and 0 <= c < W and foot[r, c]):
            continue
        d = {}
        off = 1
        for fname, flen in fields:
            d[fname] = rec[off : off + flen].decode("utf-8", errors="replace").strip()
            off += flen
        try:
            dab = float(d["F2mDAB"]) if d.get("F2mDAB") else 0.0
        except ValueError:
            dab = 0.0
        try:
            t2m = float(d["T2m"]) if d.get("T2m") else 0.0
        except ValueError:
            t2m = 0.0
        if np.isfinite(dab) and dab > 0.25:
            dab_grid[r, c] = max(dab_grid[r, c], min(float(dab), 20.0))
        if np.isfinite(t2m) and t2m > 18.0:
            t2m_grid[r, c] = max(t2m_grid[r, c], min(float(t2m - 18.0), 40.0))
    return dab_grid, t2m_grid


def _parse_paleo_geothermal(foot: np.ndarray, tr: rasterio.Affine) -> np.ndarray:
    H, W = foot.shape
    grid = np.zeros((H, W), dtype=np.float32)
    with zipfile.ZipFile(EXT / "paleo_geothermal_regional.zip") as z:
        txt = z.read("Paleo_geothermal_final.csv").decode("utf-8", errors="replace")
    lons, lats, weights = [], [], []
    for row in csv.DictReader(io.StringIO(txt)):
        try:
            lon = float(row["Long_deg_NAD83"])
            lat = float(row["Lat_deg_NAD83"])
        except (KeyError, TypeError, ValueError):
            continue
        dtype = (row.get("Deposit_type") or "").lower()
        w = 1.5 if ("sinter" in dtype or "silic" in dtype or "opal" in dtype) else 1.0
        lons.append(lon)
        lats.append(lat)
        weights.append(w)
    if lons:
        xs, ys = rio_transform("EPSG:4269", "EPSG:32611", lons, lats)
        cols = np.floor((np.asarray(xs) - tr.c) / tr.a).astype(np.int32)
        rows = np.floor((np.asarray(ys) - tr.f) / tr.e).astype(np.int32)
        for r, c, w in zip(rows, cols, weights):
            if 0 <= r < H and 0 <= c < W and foot[r, c]:
                grid[r, c] += float(w)
    return np.minimum(grid, 6.0)


def _parse_springs_and_vents(foot: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    H, W = foot.shape
    spring_grid = np.zeros((H, W), dtype=np.float32)
    with (EXT / "gdr_wellspring_in_footprint.csv").open() as f:
        for row in csv.DictReader(f):
            r, c = int(row["row"]), int(row["col"])
            if not (0 <= r < H and 0 <= c < W and foot[r, c]):
                continue
            vals = []
            for key, mult in (
                ("temp_c", 1.0),
                ("geothermquartz_c", 0.45),
                ("geothermchalc_c", 0.45),
                ("geothermcat_c", 0.40),
            ):
                s = (row.get(key) or "").strip()
                if s:
                    try:
                        v = float(s)
                        if np.isfinite(v) and 0.0 < v < 350.0:
                            vals.append(v * mult)
                    except ValueError:
                        pass
            if vals:
                eff_t = max(vals)
                if eff_t > 25.0:
                    spring_grid[r, c] = max(spring_grid[r, c], min((eff_t - 25.0) / 50.0, 3.0))

    vent_grid = np.zeros((H, W), dtype=np.float32)
    with (EXT / "gdr_volcanic_vents_in_footprint.csv").open() as f:
        for row in csv.DictReader(f):
            r, c = int(row["row"]), int(row["col"])
            if 0 <= r < H and 0 <= c < W and foot[r, c]:
                vent_grid[r, c] = 1.0
    return spring_grid, vent_grid


def _upslope_backproject(q_source: np.ndarray, uy: np.ndarray, ux: np.ndarray, foot: np.ndarray, steps_px: list[int], smooth_sigma: float) -> np.ndarray:
    H, W = foot.shape
    ys, xs = np.nonzero((q_source > 0.0) & foot)
    vals = q_source[ys, xs].astype(np.float32)
    acc = np.zeros((H, W), dtype=np.float32)
    if ys.size == 0:
        return acc
    ry = ys.astype(np.float32).copy()
    rx = xs.astype(np.float32).copy()
    max_step = int(max(steps_px))
    target_set = set(steps_px)
    if 0 in target_set:
        np.add.at(acc, (ys, xs), vals * 0.5)
    for step in range(1, max_step + 1):
        iy = np.clip(np.round(ry).astype(np.int32), 0, H - 1)
        ix = np.clip(np.round(rx).astype(np.int32), 0, W - 1)
        ry = np.clip(ry + uy[iy, ix], 0.0, H - 1.001)
        rx = np.clip(rx + ux[iy, ix], 0.0, W - 1.001)
        if step in target_set:
            ty = np.round(ry).astype(np.int32)
            tx = np.round(rx).astype(np.int32)
            ok = foot[ty, tx]
            np.add.at(acc, (ty[ok], tx[ok]), vals[ok])
    return gaussian_filter(np.log1p(acc), sigma=smooth_sigma, mode="nearest").astype(np.float32)


def build(force: bool = False) -> dict:
    t0 = time.time()
    CACHE.mkdir(parents=True, exist_ok=True)
    mmap_path = CACHE / "fvca_stack_fp.npy"
    meta_path = CACHE / "fvca_stack_meta.json"

    with rasterio.open(DATA / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
        tr = ds.transform
        H, W = ds.shape

    n_fp = int(foot.sum())
    if mmap_path.exists() and meta_path.exists() and not force:
        meta = json.loads(meta_path.read_text())
        if meta.get("n_fp") == n_fp and meta.get("feature_names") == ALL_FEATURE_NAMES and meta.get("layout") == "feature_major":
            return meta

    # Feature-major (60, n_fp) so each write is a single sequential 20.7 MB slice
    fp_mm = np.lib.format.open_memmap(
        mmap_path, mode="w+", dtype=np.float32, shape=(len(ALL_FEATURE_NAMES), n_fp)
    )

    def write_ch(idx: int, name: str, arr2d: np.ndarray) -> None:
        assert ALL_FEATURE_NAMES[idx] == name, (idx, name, ALL_FEATURE_NAMES[idx])
        v = np.asarray(arr2d[foot], dtype=np.float32)
        np.nan_to_num(v, copy=False, nan=0.0, posinf=0.0, neginf=0.0)
        fp_mm[idx] = v

    # Compute the TWO shared EDT nearest-neighbor index maps ONCE
    bad_foot = ~foot
    _, idx_foot = distance_transform_edt(bad_foot, return_indices=True)

    keep = {}
    with rasterio.open(DATA / "training_features.tif") as ds:
        b1_raw = ds.read(1)
        bad_comp = (~foot) | (~np.isfinite(b1_raw)) | (b1_raw < -1e30)
        _, idx_comp = distance_transform_edt(bad_comp, return_indices=True)
        c1 = apply_edt_indices(b1_raw, bad_comp, idx_comp)
        write_ch(0, COMP_NAMES[0], c1)
        del b1_raw, c1
        for b in range(2, 20):
            raw = ds.read(b)
            cleaned = apply_edt_indices(raw, bad_comp, idx_comp)
            write_ch(b - 1, COMP_NAMES[b - 1], cleaned)
            if b in (2, 3, 4, 5, 7, 8, 9, 12, 13, 14, 15, 16, 17, 19):
                keep[b] = cleaned
            del raw

    del bad_comp, idx_comp
    gc.collect()

    # Group A: Multi-scale ridges & structure-tensor coherence (19..29)
    write_ch(19, "elev_ridge_s10", hessian_ridge_pos(keep[12], 1.0))
    write_ch(20, "elev_ridge_s25", hessian_ridge_pos(keep[12], 2.5))
    write_ch(21, "elev_ridge_s50", hessian_ridge_pos(keep[12], 5.0))
    write_ch(22, "grav_ridge_s15", hessian_ridge_pos(keep[13], 1.5) + hessian_ridge_pos(-keep[13], 1.5))
    write_ch(23, "grav_ridge_s40", hessian_ridge_pos(keep[13], 4.0) + hessian_ridge_pos(-keep[13], 4.0))
    write_ch(24, "rtp_ridge_s15", hessian_ridge_pos(keep[2], 1.5) + hessian_ridge_pos(-keep[2], 1.5))

    coh_elev, ex_gx, ex_gy = structure_tensor_coherence(keep[12], 1.2, 2.5)
    coh_grav, gr_gx, gr_gy = structure_tensor_coherence(keep[13], 1.5, 3.0)
    _, mg_gx, mg_gy = structure_tensor_coherence(keep[2], 1.5, 3.0)
    del keep[13]

    write_ch(25, "elev_st_coh_s25", coh_elev)
    write_ch(26, "grav_st_coh_s30", coh_grav)

    gm_elev = np.hypot(ex_gx, ex_gy) + 1e-6
    gm_grav = np.hypot(gr_gx, gr_gy) + 1e-6
    gm_mag = np.hypot(mg_gx, mg_gy) + 1e-6
    del mg_gx, mg_gy

    z_g_elev = np.maximum(zscore_fp(gm_elev, foot), 0.0)
    z_g_grav = np.maximum(zscore_fp(gm_grav, foot), 0.0)
    z_g_mag = np.maximum(zscore_fp(gm_mag, foot), 0.0)
    write_ch(27, "xgrad_mag_grav", np.sqrt(z_g_mag * z_g_grav))
    write_ch(28, "xgrad_grav_elev", np.sqrt(z_g_grav * z_g_elev))
    cos_eg = np.abs(ex_gx * gr_gx + ex_gy * gr_gy) / (gm_elev * gm_grav)
    write_ch(29, "xstrike_align_elev_grav", cos_eg * coh_elev * coh_grav)
    del gr_gx, gr_gy, gm_elev, gm_grav, gm_mag, z_g_elev, z_g_grav, z_g_mag, cos_eg, coh_elev, coh_grav
    gc.collect()

    # KG2-H3: Shallow volcanic vertical-continuation residual & depth discordance (30..31)
    with rasterio.open(EXT / "geodawn_extensions_u8.tif") as ds:
        ext_thk = apply_edt_indices(ds.read(1).astype(np.float32) / 255.0, bad_foot, idx_foot)
        ext_uk = apply_edt_indices(ds.read(2).astype(np.float32) / 255.0, bad_foot, idx_foot)
        ext_uth = apply_edt_indices(ds.read(3).astype(np.float32) / 255.0, bad_foot, idx_foot)
        ext_tmi_up150 = apply_edt_indices(ds.read(4).astype(np.float32) / 255.0, bad_foot, idx_foot)

    tmi_vcont = np.abs(zscore_fp(keep[14], foot) - zscore_fp(ext_tmi_up150, foot))
    del keep[14], ext_tmi_up150
    write_ch(30, "tmi_vcont_resid150", tmi_vcont)
    z_mag_est = np.clip(keep[3] / (np.abs(keep[9]) + 0.05), 0.0, 5000.0)
    del keep[3], keep[9]
    depth_pos = np.maximum(keep[15], 0.0)
    del keep[15]
    write_ch(31, "mag_basement_depth_disc", np.log1p(depth_pos) - np.log1p(z_mag_est))
    del z_mag_est

    # GeoDAWN Radiometrics (32..37)
    with rasterio.open(EXT / "geodawn_rad_u8.tif") as ds:
        rad_k = apply_edt_indices(ds.read(1).astype(np.float32) / 255.0, bad_foot, idx_foot)
        rad_th = apply_edt_indices(ds.read(2).astype(np.float32) / 255.0, bad_foot, idx_foot)
        rad_u = apply_edt_indices(ds.read(3).astype(np.float32) / 255.0, bad_foot, idx_foot)

    write_ch(32, "rad_K", rad_k)
    write_ch(33, "rad_Th", rad_th)
    write_ch(34, "rad_U", rad_u)
    write_ch(35, "ext_ThK", ext_thk)
    write_ch(36, "ext_UK", ext_uk)
    write_ch(37, "ext_UTh", ext_uth)
    del rad_u, ext_thk, ext_uk, ext_uth

    # Road- & Lahontan-shoreline-deconfounded 1m 3DEP LiDAR scarps (38..43)
    with rasterio.open(EXT / "lidar_scarp_features_u8.tif") as ds:
        lid_valid = (ds.read(12) > 0) & foot
        lid_ex = np.where(lid_valid, ds.read(1).astype(np.float32) / 255.0, 0.0)
        lid_step = np.where(lid_valid, ds.read(3).astype(np.float32) / 255.0, 0.0)
        lid_lap = np.where(lid_valid, np.maximum(ds.read(4), ds.read(5)).astype(np.float32) / 255.0, 0.0)
        lid_coh = np.where(lid_valid, ds.read(10).astype(np.float32) / 255.0, 0.0)
        lid_strike_rad = (ds.read(11).astype(np.float32) / 255.0) * np.pi

    with rasterio.open(EXT / "tiger_road_distance_m.tif") as ds:
        d_road_m = np.maximum(apply_edt_indices(ds.read(1), bad_foot, idx_foot), 0.0)

    road_clearance = (1.0 - 0.65 * np.exp(-d_road_m / 150.0)).astype(np.float32)
    theta_contour = np.arctan2(-ex_gx, ex_gy)
    del ex_gx, ex_gy
    contour_factor = (0.35 + 0.65 * (np.sin(lid_strike_rad - theta_contour) ** 2)).astype(np.float32)
    lid_scarp_tectonic = (lid_step * (0.4 + 0.6 * lid_coh) * road_clearance * contour_factor).astype(np.float32)

    write_ch(38, "lid_ex", lid_ex)
    write_ch(39, "lid_step", lid_step)
    write_ch(40, "lid_lap", lid_lap)
    write_ch(41, "lid_coh", lid_coh)
    write_ch(42, "road_dist_log", np.log1p(d_road_m).astype(np.float32))
    write_ch(43, "lid_scarp_tectonic", lid_scarp_tectonic)
    del lid_valid, lid_ex, lid_step, lid_lap, lid_coh, lid_strike_rad, d_road_m, road_clearance, theta_contour, contour_factor, lid_scarp_tectonic
    gc.collect()

    # Group B: Fault-Valve Geothermal Vent Back-Projection & Coulomb Dilatancy (44..59)
    dab_grid, t2m_grid = _parse_2m_probes(foot, tr)
    paleo_grid = _parse_paleo_geothermal(foot, tr)
    spring_grid, vent_grid = _parse_springs_and_vents(foot)

    write_ch(44, "probe2m_dab_s4", gaussian_filter(dab_grid, sigma=4.0, mode="nearest"))
    write_ch(45, "probe2m_dab_s12", gaussian_filter(dab_grid, sigma=12.0, mode="nearest"))
    write_ch(46, "probe2m_t2m_s8", gaussian_filter(t2m_grid, sigma=8.0, mode="nearest"))
    write_ch(47, "paleo_sinter_s5", gaussian_filter(paleo_grid, sigma=5.0, mode="nearest"))
    write_ch(48, "paleo_sinter_s15", gaussian_filter(paleo_grid, sigma=15.0, mode="nearest"))
    write_ch(49, "spring_chem_s4", gaussian_filter(spring_grid, sigma=4.0, mode="nearest"))
    write_ch(50, "spring_chem_s12", gaussian_filter(spring_grid, sigma=12.0, mode="nearest"))
    write_ch(51, "volc_vent_s15", gaussian_filter(vent_grid, sigma=15.0, mode="nearest"))

    elev_s3_gy = gaussian_filter(keep[12], sigma=3.0, order=(1, 0), mode="nearest")
    elev_s3_gx = gaussian_filter(keep[12], sigma=3.0, order=(0, 1), mode="nearest")
    elev_s3_gn = np.hypot(elev_s3_gy, elev_s3_gx) + 1e-5
    uy = (elev_s3_gy / elev_s3_gn).astype(np.float32)
    ux = (elev_s3_gx / elev_s3_gn).astype(np.float32)
    del elev_s3_gy, elev_s3_gx, elev_s3_gn

    q_total_vent = (0.35 * (dab_grid / 5.0) + 0.80 * paleo_grid + 0.65 * spring_grid + 1.00 * vent_grid).astype(np.float32)
    fvca_up600 = _upslope_backproject(q_total_vent, uy, ux, foot, [0, 2, 4, 6], smooth_sigma=3.5)
    fvca_up1800 = _upslope_backproject(q_total_vent, uy, ux, foot, [6, 10, 14, 18], smooth_sigma=5.0)
    del uy, ux, q_total_vent
    write_ch(52, "fvca_upslope_600m", fvca_up600)
    write_ch(53, "fvca_upslope_1800m", fvca_up1800)

    # Potassic alteration K-on-Th OLS residual + high-pass RTP magnetite destruction trough
    kf = rad_k[foot].astype(np.float64)
    thf = rad_th[foot].astype(np.float64)
    mk, mth = float(kf.mean()), float(thf.mean())
    slope_k_th = float(np.dot(kf - mk, thf - mth) / (np.dot(thf - mth, thf - mth) + 1e-8))
    inter_k_th = mk - slope_k_th * mth
    del kf, thf
    k_resid = np.maximum(rad_k - (inter_k_th + slope_k_th * rad_th), 0.0)
    del rad_k, rad_th
    rtp_hp_low = np.maximum(-(keep[2] - gaussian_filter(keep[2], sigma=10.0, mode="nearest")), 0.0)
    del keep[2]
    potassic_mag_low = (
        zscore_fp(k_resid, foot).clip(0.0, 6.0) * (0.5 + 0.5 * zscore_fp(rtp_hp_low, foot).clip(0.0, 6.0))
    ).astype(np.float32)
    del k_resid, rtp_hp_low
    write_ch(54, "potassic_mag_low", potassic_mag_low)
    del potassic_mag_low

    # Playa-deconfounded MT clay-cap residual via 4x4 normal equations (zero SVD RAM!)
    y_cond = np.log1p(np.maximum(keep[17][foot], 0.0)).astype(np.float64)
    del keep[17]
    X_cols = [
        np.ones(n_fp, dtype=np.float64),
        keep[12][foot].astype(np.float64),
        np.log1p(depth_pos[foot]).astype(np.float64),
        keep[19][foot].astype(np.float64),
    ]
    del keep[12], keep[19], depth_pos
    xtx = np.array([[float(np.dot(a, b)) for b in X_cols] for a in X_cols], dtype=np.float64)
    xty = np.array([float(np.dot(a, y_cond)) for a in X_cols], dtype=np.float64)
    beta_playa = np.linalg.solve(xtx + 1e-8 * np.eye(4), xty)
    pred_cond = sum(b * col for b, col in zip(beta_playa, X_cols))
    cond_resid = np.zeros((H, W), dtype=np.float32)
    cond_resid[foot] = (y_cond - pred_cond).astype(np.float32)
    del y_cond, X_cols, pred_cond
    cond_resid = apply_edt_indices(cond_resid, bad_foot, idx_foot)
    c_gx = gaussian_filter(cond_resid, sigma=2.0, order=(0, 1), mode="nearest")
    c_gy = gaussian_filter(cond_resid, sigma=2.0, order=(1, 0), mode="nearest")
    cond_seal_grad = np.hypot(c_gx, c_gy).astype(np.float32)
    del c_gx, c_gy
    write_ch(55, "cond_playa_resid", cond_resid)
    write_ch(56, "cond_seal_grad", cond_seal_grad)
    del cond_resid

    # KG2-H2: Active Coulomb dilatancy fraction, seismogenic strain coupling, and joint fault-valve conduit
    dilat_frac = (np.maximum(keep[8], 0.0) / (np.abs(keep[4]) + 1e-4)).astype(np.float32)
    seismo_strain = (
        np.log1p(np.maximum(keep[16], 0.0)) * np.maximum(zscore_fp(keep[7], foot) + 1.5, 0.0)
    ).astype(np.float32)
    struct_step = np.maximum(zscore_fp(keep[5], foot), 0.0) + np.maximum(zscore_fp(tmi_vcont, foot), 0.0)
    fvca_joint = (
        (0.6 * zscore_fp(fvca_up600, foot).clip(0.0, 8.0) + 0.4 * zscore_fp(fvca_up1800, foot).clip(0.0, 8.0))
        * (0.5 + 0.5 * struct_step.clip(0.0, 6.0))
        * (0.5 + 0.5 * zscore_fp(cond_seal_grad, foot).clip(0.0, 6.0))
    ).astype(np.float32)
    write_ch(57, "coulomb_dilatancy_frac", dilat_frac)
    write_ch(58, "seismo_strain_coupling", seismo_strain)
    write_ch(59, "fvca_joint_conduit", fvca_joint)

    fp_mm.flush()
    rss_mb = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1)
    meta = {
        "schema": "KANLERGEMSDOE2-FVCA-STACK-v2.0",
        "layout": "feature_major",
        "shape_memmap": [len(ALL_FEATURE_NAMES), n_fp],
        "shape_2d": [H, W],
        "n_fp": n_fp,
        "n_features": len(ALL_FEATURE_NAMES),
        "struct_indices": list(range(44)),
        "fvca_indices": list(range(60)),
        "feature_names": ALL_FEATURE_NAMES,
        "edt_border_repaired": True,
        "uses_labels_or_existing_faults": False,
        "geothermal_counts_in_footprint": {
            "2m_temp_probe_anomalous_px": int((dab_grid > 0).sum()),
            "paleo_geothermal_px": int((paleo_grid > 0).sum()),
            "wellspring_thermal_px": int((spring_grid > 0).sum()),
            "volcanic_vent_px": int((vent_grid > 0).sum()),
        },
        "peak_rss_mb": rss_mb,
        "elapsed_s": round(time.time() - t0, 2),
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    return meta


def main() -> int:
    meta = build(force=True)
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
