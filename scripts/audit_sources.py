"""Fetch pinned GitHub evidence; no leaderboard claims are inferred from peer files."""
import base64, concurrent.futures, datetime, hashlib, json, pathlib, urllib.request
ROOT = pathlib.Path(__file__).resolve().parents[1]

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'KANLERGEMS-audit'}), timeout=45) as r:
        return json.load(r)

def fetch(item):
    repo, node = item
    target = ROOT / 'research/snapshots' / repo / node['path']
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        data = base64.b64decode(get(node['url'])['content'])
        target.write_bytes(data)
        return {'repo':repo,'path':node['path'],'git_blob':node['sha'],'sha256':hashlib.sha256(data).hexdigest(),'source':f'https://github.com/{"drivendataorg" if repo == "gems-prize-reference-solution" else "buffedlizard55-lab"}/{repo}/blob/{node["sha"]}/{node["path"]}', 'blob_api':node['url'],'status':'retrieved'}
    except Exception as e:
        return {'repo':repo,'path':node['path'],'status':'failed','error':str(e)}

def main():
    tasks=[]
    for p in sorted((ROOT/'research/snapshots').glob('*-tree.json')):
        repo=p.name.removesuffix('-tree.json'); tree=json.loads(p.read_text())
        for n in tree['tree']:
            path=n['path']
            selected=path in ['README.md','registry/data_manifest.json','registry/live_scores.json','scripts/evaluate_holdout.py','evaluate_holdout.py','scripts/submission_writer.py','submission_writer.py','registry/template_pins.json']
            selected |= repo=='gems-prize-reference-solution' and n['type']=='blob'
            selected |= repo=='GEMSDOE32' and path in ['registry/submission_build.json','evidence/h33_holdout.json','evidence/h33_submission_bundles.json','registry/current_status.json']
            if selected and n['type']=='blob' and n.get('size',0)<300000: tasks.append((repo,n))
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex: results=list(ex.map(fetch,tasks))
    # Browser source URLs use the pinned tree revision, not a blob hash as a commit.
    for r in results:
        tree=json.loads((ROOT/'research/snapshots'/f'{r["repo"]}-tree.json').read_text())
        owner='drivendataorg' if r['repo']=='gems-prize-reference-solution' else 'buffedlizard55-lab'
        r['source']=f'https://github.com/{owner}/{r["repo"]}/blob/{tree["sha"]}/{r["path"]}'
    (ROOT/'research/source_manifest.json').write_text(json.dumps({'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':results},indent=2)+'\n')
    print('Retrieved',sum(r['status']=='retrieved' for r in results),'of',len(results))
if __name__=='__main__': main()
