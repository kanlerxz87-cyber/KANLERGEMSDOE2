"""Strict whole-array format validation. Format validity does NOT authorize submission."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import rasterio

def validate(path, template):
    with rasterio.open(template) as t, rasterio.open(path) as r:
        a=r.read(1)
        sample = t.read(1)
        checks={
            'template_single_band':t.count==1,
            'template_has_footprint':bool(np.isfinite(sample).any()),
            'single_band':r.count==1,
            'dtype_float32':r.dtypes == ('float32',),
            'crs_matches':r.crs is not None and r.crs==t.crs,
            'shape_matches':r.shape==t.shape,
            'transform_matches':r.transform==t.transform,
            'no_nan_or_inf_whole_grid':bool(np.isfinite(a).all()),
            'values_in_0_1_whole_grid':bool(np.isfinite(a).all() and ((a>=0)&(a<=1)).all()),
        }
        return {'path':str(path),'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                'checks':checks,'format_valid':all(checks.values()),'ok_to_submit':False,
                'authorization':'format only; holdout + novelty + selector still required',
                'crs':str(r.crs),'shape':list(r.shape),'transform':list(r.transform)[:6],
                'positive_pixels':int(np.count_nonzero(a>0)),
                'finite_min':float(a[np.isfinite(a)].min()) if np.isfinite(a).any() else None,
                'finite_max':float(a[np.isfinite(a)].max()) if np.isfinite(a).any() else None}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('raster');p.add_argument('template');args=p.parse_args()
    report=validate(args.raster,args.template);print(json.dumps(report,indent=2,allow_nan=False))
    raise SystemExit(0 if report['format_valid'] else 1)
if __name__=='__main__':main()
