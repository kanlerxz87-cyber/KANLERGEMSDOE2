#!/usr/bin/env python3
"""Check actual data placement; never manufacture a synthetic fallback."""
import json
from pathlib import Path
import rasterio

def main():
    root=Path(__file__).resolve().parents[1]; data=root/'data'
    required=['training_features.tif','existing_faults.tif','sample_submission.tif']
    missing=[name for name in required if not (data/name).is_file()]
    report={'ready':False,'missing':missing,'provenance':'Mirrors are not organizer-authenticated; origin requires independent verification.'}
    if not missing:
        with rasterio.open(data/'sample_submission.tif') as template:
            checks={}
            for name in required:
                with rasterio.open(data/name) as src:
                    checks[name]=src.shape==template.shape and src.crs is not None and src.crs==template.crs and src.transform==template.transform
            report['grid_checks']=checks
            report['ready']=all(checks.values())
    data.mkdir(exist_ok=True)
    (data/'prepared_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    raise SystemExit(0 if report['ready'] else 1)
if __name__=='__main__':main()
