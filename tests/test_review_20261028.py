"""Independent review must not confuse byte integrity with authorization."""
import importlib.util
from pathlib import Path
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("review_published", ROOT / "scripts/review_published_artifact.py")
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)

@pytest.mark.parametrize("value,valid", [(0.0, True), (1.0, True), (-0.1, False), (1.01, False), (float("nan"), False), (float("inf"), False)])
def test_numeric_checks_and_unknown_provenance(tmp_path, value, valid):
    path = tmp_path / "candidate.tif"
    with rasterio.open(path, "w", driver="GTiff", width=2, height=2, count=1,
                       dtype="float32", crs="EPSG:32611", transform=from_origin(1000, 2000, 100, 100)) as ds:
        ds.write(np.full((2, 2), value, dtype=np.float32), 1)
    result = review.inspect(path, "not-the-hash")
    assert result["all_cells_in_0_1"] is valid
    assert result["hash_matches_sidecar"] is False
    assert result["official_template_match"] is None
    assert result["organizer_acceptance_verified"] is False


def test_review_notice_precedes_historical_claims_on_all_pages():
    for name in ["index.html", "executive-summary.html", "submission-table.html", "submission-howto.html", "research.html", "irregularities.html", "audit-review.html"]:
        page = (ROOT / "docs" / name).read_text()
        assert 'aria-label="Current evidence correction"' in page
        assert '<main id="main" class="wrap"><section class="callout" role="note" aria-label="Current evidence correction">' in page
        assert "No validated leaderboard estimate is available" in page
