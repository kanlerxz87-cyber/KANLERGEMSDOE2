#!/usr/bin/env python3
"""Build label-free feature stack (memmap) from official competition bands + external GeoDAWN/3DEP layers.
No feature reads labels.tif except footprint masking. Spring density is built separately for E3.
Band-order irregularity: lidar descriptions in file are
 (ex_max, ex_mean, step_max, lapneg_max, lappos_max, downface_max, upface_max, cross_max, relief, coh100, strike, valid)
 — we read by index from GDAL descriptions, not by assumptions in older upstream scripts.
"""
import json, pathlib, numpy as np, rasterio
from scipy.ndimage import gaussian_filter

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"; CACHE = ROOT / ".cache"
SENTINEL = -1e30

FEATURES = (
 [f"raw_{n}" for n in ["mag_anom","rtp","tmi_hg","geod_2ndinv","iso_grav_anom_slope","tc","geod_shearrate","geod_dilaterate","tmi_vg","deq_n100a15","iso_grav_anom_vg","det_elev","iso_grav_anom","tmi","depth_to_base_surf","ieq_n100a15","cond_surf","iso_grav_anom_hg","det_elev_slope"]]
 + ["grad_rtp","grad_tmi","grad_grav","grad_elev","grad_cond","grad_depth",
    "line_rtp","line_grav","line_elev","xgrad_mag_grav","tilt_abs","tilt_zero",
    "rad_K","rad_Th","rad_U","rad_TC","ext_ThK","ext_UK","ext_UTh","ext_TMIup150",
    "lid_ex","lid_step","lid_dipole","lid_lap","lid_cross","lid_coh","lid_relief","lid_valid"]
)  # 19+28 = 47

def clean(a, foot):
    a = a.astype(np.float32)
    bad = ~np.isfinite(a) | (a < SENTINEL)
    med = float(np.median(a[foot & ~bad])) if (foot & ~bad).any() else 0.0
    a[bad] = med
    return a

def gradmag(a, sigma=1.0):
    return np.hypot(gaussian_filter(a, sigma, order=(1,0)), gaussian_filter(a, sigma, order=(0,1))).astype(np.float32)

def line_response(a, sigma=1.2):
    axx = gaussian_filter(a, sigma, order=(0,2)); ayy = gaussian_filter(a, sigma, order=(2,0)); axy = gaussian_filter(a, sigma, order=(1,1))
    tmp = np.sqrt(np.maximum(((axx-ayy)*0.5)**2 + axy**2, 0.0))
    l1 = (axx+ayy)*0.5 + tmp; l2 = (axx+ayy)*0.5 - tmp
    small = np.where(np.abs(l1) >= np.abs(l2), l2, l1)
    return (-small).astype(np.float32)

def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    out_path = CACHE / "feature_stack.npy"
    meta_path = CACHE / "feature_stack.json"
    with rasterio.open(DATA/"sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1)); shape = ds.shape
    if out_path.exists() and meta_path.exists() and json.loads(meta_path.read_text()).get("features")==FEATURES:
        print("cached feature stack present"); return
    stack = np.lib.format.open_memmap(out_path, mode="w+", dtype=np.float32, shape=(len(FEATURES),)+shape)
    bands = {}
    with rasterio.open(DATA/"training_features.tif") as ds:
        print("descriptions:", ds.descriptions)
        for i in range(19):
            a = clean(ds.read(i+1), foot); bands[i]=a; stack[i]=a
            print(f"raw {i} done", flush=True)
    # indices: rtp=1, tmi_hg=2, tmi_vg=8, det_elev=11, iso_grav=12, tmi=13, depth=14, cond=16, grav_hg=17
    def put(idx, arr): stack[idx]=np.where(foot, arr, 0).astype(np.float32); print(FEATURES[idx], "done", flush=True)
    gr = gradmag(bands[1]); gt = gradmag(bands[13]); gg = gradmag(bands[12])
    put(19, gr); put(20, gt); put(21, gg); put(22, gradmag(bands[11])); put(23, gradmag(bands[16])); put(24, gradmag(bands[14]))
    put(25, line_response(bands[1])); put(26, line_response(bands[12])); put(27, line_response(bands[11]))
    # cross-gradient magnetic-gravity boundary: sqrt(|g1||g2|)*(1-|sin theta|), sin = |g1 x g2|/(|g1||g2|)
    gx1 = gaussian_filter(bands[1],1.0,order=(0,1)); gy1 = gaussian_filter(bands[1],1.0,order=(1,0))
    gx2 = gaussian_filter(bands[12],1.0,order=(0,1)); gy2 = gaussian_filter(bands[12],1.0,order=(1,0))
    cross = np.abs(gx1*gy2-gy1*gx2); denom = (np.hypot(gx1,gy1)*np.hypot(gx2,gy2)+1e-9)
    sin_t = np.clip(cross/denom,0,1)
    put(28, (np.sqrt(np.hypot(gx1,gy1)*np.hypot(gx2,gy2))*(1-sin_t)).astype(np.float32))
    tilt = np.arctan2(bands[8], np.abs(bands[2])+1e-6)
    put(29, np.abs(tilt)); put(30, np.exp(-np.abs(tilt)/0.25))
    with rasterio.open(DATA/"external/geodawn_rad_u8.tif") as ds:
        for j in range(4): put(31+j, ds.read(j+1).astype(np.float32)/255.0)
    with rasterio.open(DATA/"external/geodawn_extensions_u8.tif") as ds:
        for j in range(4): put(35+j, ds.read(j+1).astype(np.float32)/255.0)
    with rasterio.open(DATA/"external/lidar_scarp_features_u8.tif") as ds:
        print("lidar descriptions:", ds.descriptions)
        b = [ds.read(i+1).astype(np.float32)/255.0 for i in range(12)]
        put(39, b[0]); put(40, b[2]); put(41, np.abs(b[5]-b[6])); put(42, b[3]+b[4]); put(43, b[7]); put(44, b[9]); put(45, b[8]); put(46, b[11])
    stack.flush()
    meta_path.write_text(json.dumps({"features":FEATURES,"shape":list(shape),"footprint_px":int(foot.sum())},indent=2))
    print("wrote", out_path)

if __name__=="__main__": main()
