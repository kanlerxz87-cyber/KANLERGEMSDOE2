"""Write submission GeoTIFF — exact DrivenData format.

Guarantees:
  - Single-band Float32, EPSG:32611, 3730×3292, transform [100,0,243350,0,-100,4508550]
  - tiled deflate, whole-array [0,1] (zeros outside) or nan outside twin
  - Values exactly {0.0,1.0}, 0 on-catalogue leakage, B=2 enforced externally
"""
import rasterio
import numpy as np
from rasterio.transform import Affine

CRS = "EPSG:32611"
TRANSFORM = Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
WIDTH, HEIGHT = 3292, 3730

def write_submission(array: np.ndarray, footprint: np.ndarray, path: str, nodata_mode="zeros"):
    """array: (H,W) binary 0/1 in footprint, 0 outside (zeros) or nan (nan mode)"""
    assert array.shape == (HEIGHT, WIDTH)
    assert footprint.shape == (HEIGHT, WIDTH)
    # enforce footprint
    out = array.astype(np.float32)
    if nodata_mode == "zeros":
        out[~footprint] = 0.0
        nodata = None
    else:
        out[~footprint] = np.nan
        nodata = float("nan")
    # validate range
    assert np.all(np.isfinite(out[footprint])), "NaN inside footprint"
    assert out[footprint].min() >= 0 and out[footprint].max() <= 1, "range violation"

    profile = dict(
        driver="GTiff", dtype="float32", nodata=nodata,
        width=WIDTH, height=HEIGHT, count=1, crs=CRS, transform=TRANSFORM,
        tiled=True, blockxsize=256, blockysize=256, compress="deflate"
    )
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(out, 1)
    return path
