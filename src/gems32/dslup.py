"""KG2-S2 DSLUP-3D: Depth-Scaled Listric Updip Continuation projector.

Implements preregistered hypotheses KG2-S2-H1 (depth-scaled listric updip continuation) and
KG2-S2-H3 (multi-height strike-coherence gate) from
``knowledge/02_preregistered_hypotheses_dslup_20261027.md``.

Physics
-------
Basin & Range normal faults are listric: dip ~60-65 deg at the surface, shallowing with depth.
Over deep basin fill the isostatic-gravity horizontal-gradient crest sits basinward of the fault's
sub-alluvial emergence line by roughly the horizontal heave ``s = z / tan(dip_eff(z))`` of the
basement offset at depth ``z``. The promoted HTCADS EXP-2 lane migrated crests by a FIXED 3.5 px
(400 m continuation); here the migration distance is scaled per pixel by ``depth_to_base_surf``:

    dip_eff(z) = 62 deg - 24 deg * min(z / 2500 m, 1)        (listric shallowing)
    s_px(z)    = clip( z / tan(dip_eff(z)) / 100 m , 1.5 , 11.0 )

The migration *direction* is the (negated, i.e. updip/rangeward) gradient of the smoothed
difference between deep (800 m) upward-continued and surface horizontal-gradient magnitude —
the same robust direction estimator as the template, but anchored at the deepest height so the
regional footwall direction is stable over deep basins.

KG2-S2-H3 gate: basement-rooted faults keep their strike across continuation heights, shallow
alluvial noise does not. We weight the migrated ridge by ``0.5 + 0.5 * cos(2 * (strike_150 -
strike_800))`` computed from Hessian ridge strikes of the 150 m and 800 m continued fields.

All computations are label-free (no ``labels.tif``, no SGMC, no Quaternary trace coordinates).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import gaussian_filter

from .htcads import (
    _fft_upward_continue,
    _fill_outside_with_inds,
    _grad_yx_f32,
    _hessian_ridge_and_strike,
    _pos_norm_2d,
)

GRAV_BAND = 13        # iso_grav_anom  (1-indexed rasterio band, matches htcads.build_static_feature_stack)
DEPTH_BAND = 15       # depth_to_base_surf
PX_M = 100.0          # grid spacing in metres
DIP_SURF_DEG = 62.0   # surface dip of Basin & Range normal faults
DIP_DEEP_DEG = 38.0   # effective dip at >= DEPTH_FULL_M (listric sole-out trend)
DEPTH_FULL_M = 2500.0
S_MIN_PX = 1.5
S_MAX_PX = 11.0
HEIGHTS_M = (150.0, 400.0, 800.0)


def _read_filled(ddir: Path, band: int, foot: np.ndarray) -> np.ndarray:
    with rasterio.open(ddir / "training_features.tif") as src:
        a = src.read(band).astype(np.float32)
    valid = foot & np.isfinite(a) & (a > -1e30)
    filled, _ = _fill_outside_with_inds(a, valid, None)
    return filled


def build_dslup_fields(ddir: Path, foot: np.ndarray) -> dict:
    """Return the DSLUP ridge channel plus basin-depth context fields (all float32, full grid)."""
    iso_grav = _read_filled(ddir, GRAV_BAND, foot)
    depth = _read_filled(ddir, DEPTH_BAND, foot)
    depth = np.clip(depth, 0.0, None).astype(np.float32)

    g0 = gaussian_filter(iso_grav, sigma=1.2, mode="nearest")
    del iso_grav
    gy0, gx0 = _grad_yx_f32(g0)
    hg0 = np.hypot(gy0, gx0).astype(np.float32)
    del gy0, gx0

    # Multi-height continuation horizontal-gradient magnitudes
    hg_by_z: dict[float, np.ndarray] = {}
    for z in HEIGHTS_M:
        g_up = _fft_upward_continue(g0, dz_m=z, dx_m=PX_M)
        gyu, gxu = _grad_yx_f32(g_up)
        hg_by_z[z] = np.hypot(gyu, gxu).astype(np.float32)
        del g_up, gyu, gxu
    del g0

    # Migration (updip) direction anchored at the deepest continuation height (800 m)
    hg0_s = gaussian_filter(hg0, sigma=3.0, mode="nearest")
    hgu = hg_by_z[HEIGHTS_M[-1]]
    scale = float(np.mean(hg0_s[foot])) / (float(np.mean(hgu[foot])) + 1e-6)
    hgu_s = gaussian_filter(hgu * scale, sigma=3.0, mode="nearest")
    diff = gaussian_filter(hgu_s - hg0_s, sigma=4.0, mode="nearest")
    del hg0_s, hgu_s
    my, mx = _grad_yx_f32(diff)
    del diff
    mnorm = np.hypot(my, mx).astype(np.float32) + 1e-6
    uy = (-my / mnorm).astype(np.float32)
    ux = (-mx / mnorm).astype(np.float32)
    del my, mx, mnorm

    # KG2-S2-H1: per-pixel listric depth-scaled updip offset (in pixels)
    frac = np.clip(depth / DEPTH_FULL_M, 0.0, 1.0)
    dip_eff = np.deg2rad(DIP_SURF_DEG - (DIP_SURF_DEG - DIP_DEEP_DEG) * frac).astype(np.float32)
    s_px = np.clip(depth / np.tan(dip_eff) / PX_M, S_MIN_PX, S_MAX_PX).astype(np.float32)
    del frac, dip_eff

    H, W = foot.shape
    rows = np.arange(H, dtype=np.float32)[:, None]
    cols = np.arange(W, dtype=np.float32)[None, :]
    sy = np.clip(np.round(rows - s_px * uy).astype(np.int32), 0, H - 1)
    sx = np.clip(np.round(cols - s_px * ux).astype(np.int32), 0, W - 1)
    del rows, cols, uy, ux
    shifted = hg0[sy, sx]
    del hg0, sy, sx

    ridge_mig, _strike_mig = _hessian_ridge_and_strike(shifted, sigma=1.2, foot=foot)
    del shifted

    # KG2-S2-H3: strike coherence between shallow (150 m) and deep (800 m) continuation ridges
    _r150, st150 = _hessian_ridge_and_strike(hg_by_z[HEIGHTS_M[0]], sigma=1.2, foot=foot)
    _r800, st800 = _hessian_ridge_and_strike(hg_by_z[HEIGHTS_M[-1]], sigma=1.2, foot=foot)
    del _r150, _r800, hg_by_z
    coh = (0.5 + 0.5 * np.cos(2.0 * (st150 - st800))).astype(np.float32)
    del st150, st800

    dslup = _pos_norm_2d(ridge_mig * (0.60 + 0.40 * coh), foot)
    del ridge_mig, coh

    depth_fp = depth[foot]
    deep_thresh = float(np.quantile(depth_fp[depth_fp > 0.0], 0.60)) if np.any(depth_fp > 0.0) else 0.0
    return {
        "dslup_ridge": dslup.astype(np.float32),
        "depth_m": depth,
        "deep_basin_threshold_m": deep_thresh,
        "s_px_stats": {
            "min": float(s_px[foot].min()),
            "median": float(np.median(s_px[foot])),
            "p90": float(np.quantile(s_px[foot], 0.90)),
            "max": float(s_px[foot].max()),
        },
    }
