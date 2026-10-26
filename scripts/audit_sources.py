"""Snapshot public repository evidence through authenticated gh; no data downloads."""
import base64
import concurrent.futures
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SITES = [24,25,27,28,30,31,32,33,36]

def api(path):
    return json.loads(subprocess.check_output(['gh','api',path], text=True))

def audit(site):
    repo = f'buffedlizard55-lab/GEMSDOE{site}'
    commit = api(f'repos/{repo}/commits/main')['sha']
    tree = api(f'repos/{repo}/git/trees/{commit}?recursive=1')
    folder = ROOT / 'docs/evidence' / f'GEMSDOE{site}'
    folder.mkdir(parents=True, exist_ok=True)
    (folder/'tree.json').write_text(json.dumps(tree, indent=2)+'\n')
    paths = ['README.md','docs/index.html']
    records=[]
    for entry in tree['tree']:
        path=entry['path']
        if entry['type']=='blob' and entry.get('size',0)<150000 and (path in paths or path.endswith(('evaluate_holdout.py','submission_writer.py'))):
            blob=api(f"repos/{repo}/git/blobs/{entry['sha']}")
            target=folder/path
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(base64.b64decode(blob['content']))
            records.append({'path':path,'git_blob_sha':entry['sha'],'url':f'https://github.com/{repo}/blob/{commit}/{path}'})
    return {'site':site,'commit':commit,'tree_truncated':tree.get('truncated'), 'files':records}

if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(audit,SITES))
    (ROOT/'docs/evidence/index.json').write_text(json.dumps({'retrieved':'2026-10-26','repositories':results},indent=2)+'\n')
