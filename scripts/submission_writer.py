#!/usr/bin/env python3
"""Write all-finite [0,1] single-band GeoTIFF matching sample_submission CRS/shape/transform exactly.
Fixes DrivenData error 'Predicted values must be in range [0, 1]': no NaN/Inf/sentinel anywhere,
values clipped to [0,1], 0 outside footprint (nodata=None), 0 on catalogue. Automated validator included.
Template-derived from GEMSDOE32 submission.py checks (see src/gems/PROVENANCE.md); filename prefix is this repo's.
"""
import argparse, hashlib, json, pathlib, zipfile
import numpy as np, rasterio

ROOT=pathlib.Path(__file__).resolve().parents[1]

def validate(tif, sample, labels_path):
    with rasterio.open(sample) as ds: foot=np.isfinite(ds.read(1)); prof=ds.profile; crs, shape, tr = ds.crs, ds.shape, ds.transform
    with rasterio.open(labels_path) as ds: labels=ds.read(1)>0
    with rasterio.open(tif) as ds:
        a=ds.read(1); checks={
          "single_band": ds.count==1, "dtype_float32": ds.dtypes[0]=="float32",
          "crs_match": ds.crs==crs, "shape_match": ds.shape==shape, "transform_match": ds.transform==tr,
          "no_nan_anywhere": bool(not np.isnan(a).any()), "no_inf_anywhere": bool(np.isfinite(a).all()),
          "values_in_0_1_everywhere": bool(((a>=0)&(a<=1)).all()),
          "zero_outside_footprint": bool((a[~foot]==0).all()),
          "zero_on_catalogue": bool((a[labels]<=0).all()),
          "nodata_none": ds.nodata is None}
        return {"file":tif.name,"sha256":hashlib.sha256(tif.read_bytes()).hexdigest(),"bytes":tif.stat().st_size,
                "dots":int((a>0).sum()),"min":float(a.min()),"max":float(a.max()),"checks":checks,"all_pass":all(checks.values())}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--mask", type=pathlib.Path, required=True); ap.add_argument("--slug", required=True); ap.add_argument("--note", required=True); ap.add_argument("--out-dir", type=pathlib.Path, default=ROOT/"docs/downloads")
    a=ap.parse_args(); assert len(a.note)<=140, f"note {len(a.note)}>140"
    with rasterio.open(ROOT/"data/sample_submission.tif") as ds: foot=np.isfinite(ds.read(1)); prof=ds.profile.copy()
    with rasterio.open(ROOT/"data/labels.tif") as ds: labels=ds.read(1)>0
    mask=np.load(a.mask)>0; arr=np.where(foot & mask & ~labels, 1.0, 0.0).astype(np.float32)
    digest=hashlib.sha256(np.packbits(arr>0)).hexdigest()[:10]
    from datetime import datetime, timezone; ts=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name=f"kanler-{a.slug}-{ts}-{digest}-allfinite.tif"; out=a.out_dir/name; a.out_dir.mkdir(parents=True,exist_ok=True)
    prof.update(driver="GTiff", dtype="float32", count=1, compress="deflate", predictor=3, zlevel=9, tiled=True, blockxsize=256, blockysize=256, nodata=None)
    with rasterio.open(out,"w",**prof) as ds: ds.write(arr,1)
    receipt=validate(out, ROOT/"data/sample_submission.tif", ROOT/"data/labels.tif")
    receipt.update({"unique_name":f"KANLER-{a.slug.upper()}-{digest.upper()}","note":a.note,"note_chars":len(a.note)})
    (a.out_dir/f"{name}.receipt.json").write_text(json.dumps(receipt,indent=2))
    with zipfile.ZipFile(out.with_suffix(".zip"),"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z: z.write(out, arcname=name)
    print(json.dumps(receipt,indent=2))
if __name__=="__main__": main()
