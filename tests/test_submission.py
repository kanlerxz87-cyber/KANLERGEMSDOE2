import json, pathlib, numpy as np, rasterio, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class ArchivedSubmissionTests(unittest.TestCase):
    def test_lane_tif_range_and_grid(self):
        tif=ROOT/"research/quarantine/prior-docs/downloads/kanler-e1-xg-hgb-37654d-20261026T214616Z-7ab68c3efd-allfinite.tif"
        assert tif.exists()
        with rasterio.open(tif) as d:
            a=d.read(1); assert d.count==1 and d.dtypes[0]=="float32" and str(d.crs)=="EPSG:32611" and d.shape==(3730,3292)
        assert np.isfinite(a).all() and a.min()>=0 and a.max()<=1
        assert (a>0).sum()==37654
        r=json.loads(pathlib.Path(str(tif)+".receipt.json").read_text()); assert r["all_pass"] and r["note_chars"]<=140
    def test_lane_run_card(self):
        r=json.loads((ROOT/"evidence/run_card_e1_xg_hgb.json").read_text())
        assert r["verdict"]=="negative" and len(r["submission_note"])<=140 and r["raster_sha256"]
