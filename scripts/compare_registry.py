"""Measure historical rank correlation and directional dot overlap, never infer leaderboard performance."""
import json, pathlib
import numpy as np
import rasterio
from scipy.spatial import cKDTree
from scipy.stats import spearmanr
from validate_raster import validate
ROOT=pathlib.Path(__file__).resolve().parents[1]
def compare(a,b,mask):
    x,y=a[mask],b[mask]
    # Binary rasters: Spearman equals Pearson on the two-valued ranks, calculated exactly.
    if np.isin(x,[0,1]).all() and np.isin(y,[0,1]).all():
        xx=x.astype(np.float64); yy=y.astype(np.float64)
        rho=float(np.corrcoef(xx,yy)[0,1]) if xx.std()>0 and yy.std()>0 else None
    else:
        rho=float(spearmanr(x,y).statistic) if x.std()>0 and y.std()>0 else None
    da=np.argwhere((a>0)&mask); db=np.argwhere((b>0)&mask)
    overlap=float(np.mean(cKDTree(db).query(da,k=1)[0]<=3)) if len(da) and len(db) else None
    return {'spearman_rho':rho,'fraction_a_dots_within_3px_of_b':overlap,
            'duplicate_gate':rho is None or overlap is None or rho>0.90 or overlap>0.70,
            'decoded_pixels_equal_inside_footprint':bool(np.array_equal(x,y))}
def main():
    records=json.loads((ROOT/'research/raster_manifest.json').read_text()); arrays={};reports=[]
    with rasterio.open(ROOT/'data/sample_submission.tif') as src:mask=np.isfinite(src.read(1)) & (src.read_masks(1)>0)
    for r in records:
        path=ROOT/r['local']; reports.append({'site':r['site'],**validate(path,ROOT/'data/sample_submission.tif')})
        with rasterio.open(path) as src:arrays[r['site']]=src.read(1)
    pairs=[]
    for a in arrays:
        for b in arrays:
            if a!=b:pairs.append({'a':a,'b':b,**compare(arrays[a],arrays[b],mask)})
    out={'scope':'nine historical references only, not full registry; final dots only; no candidate surface tested',
         'footprint_pixels':int(mask.sum()),'format_reports':reports,'directed_pairs':pairs}
    (ROOT/'research/raster_audit.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    print('Validated',len(reports),'rasters;',len(pairs),'directed comparisons;',sum(p['duplicate_gate'] for p in pairs),'duplicate-gate hits')
if __name__=='__main__':main()
