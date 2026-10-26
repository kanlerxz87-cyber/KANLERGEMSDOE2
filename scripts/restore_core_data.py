#!/usr/bin/env python3
"""Restore the existing pinned peer mirror, never synthetic or authenticated data.

Uses pinned codeload.github.com archives by default, or raw api.github.com blobs.
Verifies assembled SHA256/size (plus Git SHA1 for API transport) and atomically
installs verified bytes under ignored data/.
A valid existing file is reused; an invalid existing file is never trusted.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import tarfile
import shutil
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'research/snapshots/GEMSDOE32/registry/data_manifest.json'


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def request(url, raw=False):
    if urllib.parse.urlparse(url).hostname != 'api.github.com':
        raise ValueError('Only the GitHub API is permitted')
    return urllib.request.urlopen(urllib.request.Request(url, headers={
        'User-Agent': 'KANLERGEMS-pinned-data',
        'Accept': 'application/vnd.github.raw+json' if raw else 'application/vnd.github+json',
    }), timeout=120)


def valid_existing(path, entry):
    return path.is_file() and path.stat().st_size == entry['bytes'] and digest(path) == entry['sha256']


def safe_destination(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Manifest destination escapes data directory')
    return path


def restore(entry, data_dir):
    dest = safe_destination(data_dir, entry['dest'])
    if valid_existing(dest, entry):
        return {'id': entry['id'], 'status': 'verified-existing', 'sha256': entry['sha256'], 'bytes': entry['bytes']}
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=dest.name + '.', suffix='.partial', dir=dest.parent)
    tmp = Path(temporary)
    sources = []
    try:
        with os.fdopen(fd, 'wb') as out:
            for part in entry.get('parts', [entry.get('path')]):
                url = f'https://api.github.com/repos/{entry["repo"]}/contents/{urllib.parse.quote(part, safe="/")}?ref={entry["ref"]}'
                with request(url) as response:
                    metadata = json.load(response)
                size = metadata['size']
                git_hash = hashlib.sha1(f'blob {size}\0'.encode())
                received = 0
                with request(metadata['git_url'], raw=True) as response:
                    if 'json' in response.headers.get('Content-Type', ''):
                        raise ValueError('Expected raw Git blob; refusing JSON as raster bytes')
                    while chunk := response.read(1024 * 1024):
                        received += len(chunk)
                        if received > size:
                            raise ValueError('Git blob exceeds declared size')
                        git_hash.update(chunk)
                        out.write(chunk)
                if received != size or git_hash.hexdigest() != metadata['sha']:
                    raise ValueError('Git blob checksum/size mismatch: ' + part)
                sources.append({'url': url, 'blob_sha1': metadata['sha'], 'bytes': size})
                print('Verified mirror part:', part, received, flush=True)
        if not valid_existing(tmp, entry):
            raise ValueError('Assembled SHA256/size mismatch: ' + entry['id'])
        tmp.replace(dest)
    finally:
        tmp.unlink(missing_ok=True)
    return {'id': entry['id'], 'status': 'restored-verified', 'sha256': entry['sha256'], 'bytes': entry['bytes'], 'sources': sources}


def restore_archive_group(entries, data_dir):
    """Rate-limit-independent pinned codeload transport. Extract selected files only.

    No tar paths are extracted directly. Each selected member goes into a private
    temporary directory and must pass the full manifest SHA256 before install.
    """
    repo, ref = entries[0]['repo'], entries[0]['ref']
    if any((f['repo'], f['ref']) != (repo, ref) for f in entries):
        raise ValueError('Archive entries must share a repository and commit')
    needed = {p for e in entries for p in e.get('parts', [e.get('path')])}
    url = f'https://codeload.github.com/{repo}/tar.gz/{ref}'
    data_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='mirror-', dir=data_dir) as work:
        work = Path(work)
        members = {}
        total = 0
        with urllib.request.urlopen(url, timeout=120) as response, tarfile.open(fileobj=response, mode='r|gz') as archive:
            for member in archive:
                total += member.size
                if total > 8 * 1024**3:
                    raise ValueError('Archive exceeds safety budget')
                relative = member.name.partition('/')[2]
                if relative not in needed:
                    continue
                if not member.isfile() or relative in members or member.size > 512 * 1024**2:
                    raise ValueError('Invalid or duplicate archive member')
                local = work / str(len(members))
                with archive.extractfile(member) as src, local.open('wb') as dest:
                    shutil.copyfileobj(src, dest, 1024 * 1024)
                members[relative] = local
                print('Retrieved archive member:', relative, member.size, flush=True)
                if len(members) == len(needed):
                    break
        if set(members) != needed:
            raise ValueError('Pinned archive missing selected files: ' + str(needed - set(members)))
        results = []
        # Verify ALL assembled files before replacing any final path.
        assembled = []
        for i, entry in enumerate(entries):
            temporary = work / f'assembled-{i}'
            with temporary.open('wb') as dest:
                for part in entry.get('parts', [entry.get('path')]):
                    with members[part].open('rb') as src:
                        shutil.copyfileobj(src, dest, 1024 * 1024)
            if not valid_existing(temporary, entry):
                raise ValueError('Archive assembled SHA256/size mismatch: ' + entry['id'])
            assembled.append((entry, temporary))
        for entry, temporary in assembled:
            dest = safe_destination(data_dir, entry['dest'])
            dest.parent.mkdir(parents=True, exist_ok=True)
            temporary.replace(dest)
            results.append({'id': entry['id'], 'status': 'restored-verified', 'transport': 'pinned-codeload',
                            'source': url, 'sha256': entry['sha256'], 'bytes': entry['bytes']})
        return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=ROOT / 'data')
    parser.add_argument('--include-external', action='store_true')
    parser.add_argument('--transport', choices=('api', 'archive'), default='archive')
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    groups = {'core', 'external'} if args.include_external else {'core'}
    report = {'provenance': 'Peer mirror integrity only; NOT organizer-authenticated.',
              'manifest_sha256': digest(MANIFEST), 'files': [], 'ready': False}
    pending = {}
    for entry in manifest['files']:
        if entry.get('group') not in groups:
            continue
        if args.transport == 'api' or valid_existing(safe_destination(args.data_dir, entry['dest']), entry):
            try:
                result = restore(entry, args.data_dir)
            except Exception as exc:
                result = {'id': entry['id'], 'status': 'failed', 'error': str(exc)}
            report['files'].append(result)
        else:
            pending.setdefault((entry['repo'], entry['ref']), []).append(entry)
    for entries in pending.values():
        try:
            report['files'].extend(restore_archive_group(entries, args.data_dir))
        except Exception as exc:
            report['files'].extend({'id': e['id'], 'status': 'failed', 'error': str(exc)} for e in entries)
    report['ready'] = bool(report['files']) and all(f['status'] != 'failed' for f in report['files'])
    args.data_dir.mkdir(parents=True, exist_ok=True)
    (args.data_dir / 'restore_manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['ready'] else 1)


if __name__ == '__main__':
    main()
