#!/usr/bin/env python3
"""Read-only priority-repository HEAD monitor. Does NOT refresh scores or audit pins."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def observe(record):
    repo = 'buffedlizard55-lab/' + record['site']
    result = {'site': record['site'], 'repository': 'https://github.com/' + repo,
              'audited_tree_revision': record['tree_revision'],
              'historical_evidence_refreshed': False, 'organizer_scores_checked': False}
    try:
        process = subprocess.run(['git', 'ls-remote', result['repository'] + '.git', 'HEAD'],
                                 text=True, capture_output=True, timeout=45, check=True)
        sha, ref = process.stdout.strip().split()
        if not re.fullmatch(r'[0-9a-f]{40}', sha) or ref != 'HEAD':
            raise ValueError('Invalid remote HEAD response')
        result.update(status='observed', head_commit=sha)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        result.update(status='unavailable', error=str(exc), head_commit=None)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'evidence/source_freshness.json')
    args = parser.parse_args()
    records = json.loads((ROOT / 'research/raster_manifest.json').read_text())
    with ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(observe, records))
    previous = {}
    if args.out.exists():
        previous = {r['site']: r.get('head_commit') for r in json.loads(args.out.read_text()).get('repositories', [])}
    for row in rows:
        old = previous.get(row['site'])
        row['changed_since_previous_observation'] = None if not old or not row['head_commit'] else old != row['head_commit']
    result = {'checked_utc': datetime.now(timezone.utc).isoformat(), 'method': 'git ls-remote HEAD; read-only',
              'scope': 'Repository revision monitor, NOT live competition scores, complete registry, or refreshed scientific evidence.',
              'repositories': rows, 'all_reachable': all(r['status'] == 'observed' for r in rows)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    # Unavailability is published, never hidden by reusing an old successful receipt.
    raise SystemExit(0 if result['all_reachable'] else 1)


if __name__ == '__main__':
    main()
