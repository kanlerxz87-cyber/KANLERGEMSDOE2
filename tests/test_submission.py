import json, pathlib, numpy as np, rasterio
ROOT=pathlib.Path(__file__).resolve().parents[1]
def test_tif_range_and_grid():
    tif=sorted((ROOT/"docs/downloads").glob("*-allfinite.tif"))[0]
    with rasterio.open(ROOT/"data/sample_submission.tif") as s: foot=np.isfinite(s.read(1)); crs,shape,tr=s.crs,s.shape,s.transform
    with rasterio.open(tif) as d:
        a=d.read(1); assert d.count==1 and d.dtypes[0]=="float32" and d.crs==crs and d.shape==shape and d.transform==tr
    assert np.isfinite(a).all() and a.min()>=0 and a.max()<=1 and (a[~foot]==0).all()
    assert (a>0).sum()==37654
    r=json.loads(pathlib.Path(str(tif)+".receipt.json").read_text()); assert r["all_pass"] and r["note_chars"]<=140
def test_run_card():
    r=json.loads((ROOT/"evidence/run_card.json").read_text())
    assert r["verdict"]=="negative" and len(r["submission_note"])<=140 and r["raster_sha256"]
