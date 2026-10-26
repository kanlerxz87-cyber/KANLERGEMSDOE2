"""Fail closed on the independently verified literal registry counterexample."""
from pathlib import Path
import numpy as np
import rasterio

try:
    from .audit_registry_witness import REFERENCES, SAMPLE_SHA, sha256_file
except ImportError:
    from audit_registry_witness import REFERENCES, SAMPLE_SHA, sha256_file


def require_candidate_generation_allowed(data_dir: Path):
    """Stop before scoring or writing while the pinned witness blocks every dot.

    Missing/mismatched evidence is also a stop, not permission to continue. This
    guard alone never certifies complete registry coverage or scientific quality.
    """
    data_dir = Path(data_dir)
    sample = data_dir / "sample_submission.tif"
    entry = REFERENCES["continuous_gemsdoe48"]
    witness = data_dir / "registry" / "blockers" / entry["filename"]
    try:
        if sha256_file(sample) != SAMPLE_SHA or sha256_file(witness) != entry["sha256"]:
            raise ValueError("witness or sample checksum mismatch")
        with rasterio.open(sample) as s, rasterio.open(witness) as r:
            if s.count != 1 or r.count != 1 or s.crs is None or (s.shape, s.crs, s.transform) != (r.shape, r.crs, r.transform):
                raise ValueError("witness grid mismatch")
            footprint = np.isfinite(s.read(1))
            values = r.read(1)
            if not footprint.any() or not np.isfinite(values[footprint]).all():
                raise ValueError("empty or invalid witness footprint")
            if np.all(values[footprint] > 0):
                raise RuntimeError(
                    "DUPLICATE STOP: registered continuous support covers the full footprint; "
                    "every nonempty dot set overlaps it 100%. See evidence/registry_witness.json."
                )
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"Registry witness unavailable or invalid; fail closed: {exc}") from exc
    raise RuntimeError("No complete registry certificate is implemented; candidate generation remains blocked.")
