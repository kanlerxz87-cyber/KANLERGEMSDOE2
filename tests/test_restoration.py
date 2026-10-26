"""Offline synthetic archive/fetch tests; no competition requests or uploads."""
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest import mock

from scripts.restore_competition_data import extract_selected, restore


def tar_bytes(members):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w:gz') as tar:
        for name, content, kind in members:
            info = tarfile.TarInfo(name)
            if kind == 'symlink':
                info.type = tarfile.SYMTYPE
                info.linkname = '/tmp/unsafe-target'
                info.size = 0
                tar.addfile(info)
            else:
                info.size = len(content)
                tar.addfile(info, io.BytesIO(content))
    return stream.getvalue()


class RestorationTests(unittest.TestCase):
    def test_extract_only_selected_no_archive_path_written(self):
        payload = tar_bytes([('Repo-ref/safe/file', b'abc', 'file'),
                             ('Repo-ref/../../escaped', b'bad', 'file')])
        with tempfile.TemporaryDirectory() as tmp:
            found = extract_selected(io.BytesIO(payload), 'Repo-ref', {'safe/file'}, tmp)
            self.assertEqual(found['safe/file'].read_bytes(), b'abc')
            self.assertFalse((Path(tmp).parent / 'escaped').exists())

    def test_missing_duplicate_and_symlink_are_rejected(self):
        for members, wanted in [([('Repo-ref/a', b'x', 'file')], {'missing'}),
                                 ([('Repo-ref/a', b'x', 'file'), ('Repo-ref/a', b'y', 'file')], {'a'}),
                                 ([('Repo-ref/a', b'', 'symlink')], {'a'})]:
            with self.subTest(members=members), tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(ValueError):
                    extract_selected(io.BytesIO(tar_bytes(members)), 'Repo-ref', wanted, tmp)

    def test_group_integrity_before_replacement_and_multipart(self):
        payload = tar_bytes([('Repo-ref/first', b'hello ', 'file'), ('Repo-ref/second', b'world', 'file'),
                             ('Repo-ref/other', b'new', 'file')])
        good = {'id': 'multi', 'repo': 'owner/Repo', 'ref': 'ref', 'parts': ['first', 'second'],
                'dest': 'multi.bin', 'sha256': hashlib.sha256(b'hello world').hexdigest(), 'bytes': 11}
        bad = {'id': 'bad', 'repo': 'owner/Repo', 'ref': 'ref', 'path': 'other', 'dest': 'bad.bin',
               'sha256': hashlib.sha256(b'not-the-archive').hexdigest(), 'bytes': 3}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / 'bad.bin').write_bytes(b'old')
            with mock.patch('scripts.restore_competition_data.urllib.request.urlopen', return_value=io.BytesIO(payload)):
                with self.assertRaisesRegex(ValueError, 'Integrity'):
                    restore([good, bad], root)
            self.assertFalse((root / 'multi.bin').exists())
            self.assertEqual((root / 'bad.bin').read_bytes(), b'old')
            with mock.patch('scripts.restore_competition_data.urllib.request.urlopen', return_value=io.BytesIO(payload)):
                self.assertTrue(restore([good], root)['multi'])
            self.assertEqual((root / 'multi.bin').read_bytes(), b'hello world')

    def test_destinations_cannot_escape_or_alias(self):
        base = {'id': 'x', 'repo': 'owner/Repo', 'ref': 'ref', 'path': 'a',
                'sha256': '0' * 64, 'bytes': 1}
        with tempfile.TemporaryDirectory() as tmp:
            for dest in ('../escape', '/tmp/escape'):
                with self.subTest(dest=dest), self.assertRaisesRegex(ValueError, 'Unsafe'):
                    restore([{**base, 'dest': dest}], Path(tmp))
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                restore([{**base, 'dest': 'a'}, {**base, 'dest': './a'}], Path(tmp))

