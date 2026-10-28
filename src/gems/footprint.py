"""Load the scored footprint from the committed run-length payload (docs/data/footprint.bin)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine

from .paths import SITE_DATA_DIR

WIDTH, HEIGHT = 3292, 3730
CRS = "EPSG:32611"
TRANSFORM = Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)


def decode_runs(payload: bytes, total: int = WIDTH * HEIGHT) -> np.ndarray:
    if not isinstance(total, int) or isinstance(total, bool) or total <= 0:
        raise ValueError("footprint size must be a positive integer")
    mask = np.zeros(total, dtype=bool)
    pos = n = 0
    val = False
    while pos < len(payload):
        v = shift = 0
        while True:
            if pos >= len(payload) or shift >= 64:
                raise ValueError("truncated or oversized footprint run")
            b = payload[pos]
            pos += 1
            v |= (b & 0x7F) << shift
            shift += 7
            if not b & 0x80:
                break
        if n + v > total:
            raise ValueError("footprint run exceeds expected size")
        if val:
            mask[n : n + v] = True
        n += v
        val = not val
    if n != total:
        raise ValueError(f"footprint payload covers {n} pixels, expected {total}")
    return mask


def load_footprint(path: Path | None = None) -> np.ndarray:
    path = Path(path or SITE_DATA_DIR / "footprint.bin")
    payload = path.read_bytes()
    metadata = meta()
    if (len(payload) != metadata["payload_bytes"] or
            hashlib.sha256(payload).hexdigest() != metadata["payload_sha256"]):
        raise ValueError("footprint payload does not match the committed mirror checksum")
    return decode_runs(payload).reshape(HEIGHT, WIDTH)


def write_template(path: Path | str, fill_value: float = 0.0) -> Path:
    fp = load_footprint()
    arr = np.where(fp, np.float32(fill_value), np.float32(np.nan)).astype(np.float32)
    profile = dict(
        driver="GTiff",
        dtype="float32",
        count=1,
        width=WIDTH,
        height=HEIGHT,
        crs=CRS,
        transform=TRANSFORM,
        nodata=np.nan,
        compress="lzw",
        tiled=False,
        blockysize=1,
        interleave="band",
    )
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(arr, 1)
        dst.update_tags(AREA_OR_POINT="Area")
    return Path(path)


def meta() -> dict:
    return json.loads((SITE_DATA_DIR / "footprint.json").read_text())


def load_band(path, band: int = 1) -> "np.ndarray":
    """Read one band of a GeoTIFF as float32, NaN outside the file's nodata.
    Grid-agnostic helper for research scripts (assumes footprint grid; verify
    CRS/shape at the call site when the file is not ours)."""
    import numpy as _np
    import rasterio as _rio

    with _rio.open(str(path)) as d:
        a = d.read(band).astype("float32")
        if d.nodata is not None:
            a = _np.where(_np.isclose(a, d.nodata), _np.nan, a)
    return a
