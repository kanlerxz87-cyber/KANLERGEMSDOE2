"""Restore historical rasters for EDUCATION ONLY and byte-identical shared tools."""
import base64, concurrent.futures, hashlib, json, pathlib, urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
TERMS={24:'989f595',25:'e56ea318',27:'5512495',28:'b531dae',30:'91eae1ca',31:'h27-4-solo-d28',32:'e5eb6e7e',33:'cb490425',36:'9b9ea4e6'}

def request(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'KANLERGEMS-audit'}),timeout=60) as r:return json.load(r)
def fetch(task):
    url,dest,sha=task
    obj=request(url)
    if obj.get('encoding') == 'none' and obj.get('git_url'):
        obj=request(obj['git_url'])
    b=base64.b64decode(obj['content'])
    if not b:
        raise ValueError('Empty GitHub payload: '+url)
    if sha and hashlib.sha256(b).hexdigest()!=sha:raise ValueError('Checksum mismatch: '+str(dest))
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
    return hashlib.sha256(b).hexdigest()
def main():
    tasks=[]; records=[]
    for n,term in TERMS.items():
        repo=f'GEMSDOE{n}'; tree=json.loads((ROOT/f'research/snapshots/{repo}-tree.json').read_text())
        nodes=[x for x in tree['tree'] if term in x['path'] and x['path'].endswith('.tif') and not any(t in x['path'] for t in ['-nan','nanoutside'])]
        if len(nodes)!=1:raise ValueError((repo,nodes))
        node=nodes[0]; dest=ROOT/'data/registry'/f'{repo}.tif'
        tasks.append((node['url'],dest,None)); records.append({'site':repo,'path':node['path'],'tree_revision':tree['sha'],'blob':node['sha'],'url':f'https://github.com/buffedlizard55-lab/{repo}/blob/{tree["sha"]}/{node["path"]}','local':str(dest.relative_to(ROOT)),'purpose':'historical reference only; not a new submission'})
    manifest=json.loads((ROOT/'research/snapshots/GEMSDOE32/registry/data_manifest.json').read_text())
    for f in manifest['files']:
        if f['id'] in ['sample_submission','existing_faults']:
            tasks.append((f'https://api.github.com/repos/{f["repo"]}/contents/{f["path"]}?ref={f["ref"]}',ROOT/'data'/f['dest'],f['sha256']))
    pins=json.loads((ROOT/'research/snapshots/GEMSDOE36/registry/template_pins.json').read_text())
    for p in pins['files']:
        tasks.append((f'https://api.github.com/repos/{p["upstream_repo"]}/contents/{p["upstream_path"]}?ref={p["upstream_commit"]}',ROOT/'vendor/template'/p['local'],p['sha256']))
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex: hashes=list(ex.map(fetch,tasks))
    for record,sha in zip(records,hashes):record['sha256']=sha
    (ROOT/'research/raster_manifest.json').write_text(json.dumps(records,indent=2)+'\n')
    (ROOT/'vendor/template/pins.json').write_text(json.dumps(pins,indent=2)+'\n')
    print('Restored',len(tasks),'files; historical rasters excluded from Git')
if __name__=='__main__':main()
