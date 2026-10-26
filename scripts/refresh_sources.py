#!/usr/bin/env python3
"""Record public GitHub commit heads only; never query the DrivenData portal."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def observe(manifest: dict) -> dict:
    rows = []
    for item in manifest['sites']:
        try:
            proc = subprocess.run(['gh', 'api', f"repos/{item['repository']}/commits/main", '--jq', '.sha'],
                                  text=True, capture_output=True, check=True, timeout=25)
            ref = proc.stdout.strip()
            if len(ref) != 40 or any(c not in '0123456789abcdef' for c in ref):
                raise ValueError('invalid commit response')
            rows.append({'site': item['site'], 'repository': item['repository'], 'observed_head': ref,
                         'status': 'observed'})
        except (subprocess.SubprocessError, ValueError) as exc:
            rows.append({'site': item['site'], 'repository': item['repository'], 'observed_head': None,
                         'status': 'unavailable', 'reason': type(exc).__name__})
    return {'checked_utc': datetime.now(timezone.utc).isoformat(), 'all_heads_observed': all(r['observed_head'] for r in rows),
            'scope': 'GitHub repository heads only; not an audit, leaderboard, live score or slot decision', 'sites': rows}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, default=ROOT / 'registry/focus-sites.json')
    p.add_argument('--out', type=Path, default=ROOT / 'docs/data/source-heads.json')
    args = p.parse_args()
    result = observe(json.loads(args.manifest.read_text()))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=args.out.parent, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w') as out:
            json.dump(result, out, indent=2, allow_nan=False)
            out.write('\n')
        Path(temp).replace(args.out)
    finally:
        Path(temp).unlink(missing_ok=True)
    print(json.dumps(result, indent=2))
    return 0 if result['all_heads_observed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
