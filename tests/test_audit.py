import hashlib
import json
import pathlib
import sys
import tempfile
import unittest

import numpy as np
import rasterio
from rasterio.transform import from_origin

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'vendor/template/src'))
from compare_registry import compare
from validate_raster import validate
from gems.submission import write_submission
from gems.holdout import SegmentHoldout

class FormatTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name)
        self.template=self.save('template.tif',np.zeros((8,8),np.float32))
    def tearDown(self): self.tmp.cleanup()
    def save(self,name,a,**changes):
        profile=dict(driver='GTiff',height=a.shape[0],width=a.shape[1],count=1,dtype='float32',crs='EPSG:32611',transform=from_origin(1000,2000,100,100))
        profile.update(changes);path=self.root/name
        with rasterio.open(path,'w',**profile) as dst:
            for b in range(1,profile['count']+1):dst.write(a.astype(np.float32),b)
        return path
    def test_valid_is_not_upload_approval(self):
        r=validate(self.template,self.template)
        self.assertTrue(r['format_valid']);self.assertFalse(r['ok_to_submit'])
    def test_nonfinite_and_out_of_range_rejected(self):
        for value in [np.nan,np.inf,-np.inf,-9999,-0.01,1.01]:
            with self.subTest(value=value):
                a=np.zeros((8,8));a[0,0]=value
                self.assertFalse(validate(self.save('bad.tif',a),self.template)['format_valid'])
    def test_grid_mismatches(self):
        for changes in [{'crs':'EPSG:4326'},{'transform':from_origin(1001,2000,100,100)},{'count':2}]:
            with self.subTest(changes=changes):
                self.assertFalse(validate(self.save('grid.tif',np.zeros((8,8)),**changes),self.template)['format_valid'])
        self.assertFalse(validate(self.save('shape.tif',np.zeros((4,4))),self.template)['format_valid'])
    def test_shared_writer_rejects_invalid_not_silent_clip(self):
        a=np.zeros((8,8));a[0,0]=2
        with self.assertRaises(ValueError):write_submission(a,self.template,self.root/'out.tif',outside='zero')
    def test_shared_writer_roundtrip(self):
        a=np.zeros((8,8));a[3,3]=1
        out=write_submission(a,self.template,self.root/'out.tif',outside='zero')
        self.assertTrue(validate(out,self.template)['format_valid'])

class NoveltyTests(unittest.TestCase):
    def test_identical_support(self):
        a=np.zeros((16,16));a[2,2]=1
        r=compare(a,a,np.ones_like(a,bool));self.assertTrue(r['duplicate_gate']);self.assertAlmostEqual(r['spearman_rho'],1)
    def test_shifted_duplicate(self):
        a=np.zeros((16,16));b=a.copy();a[2,2]=1;b[2,5]=1
        self.assertTrue(compare(a,b,np.ones_like(a,bool))['duplicate_gate'])
    def test_far_support(self):
        a=np.zeros((16,16));b=a.copy();a[2,2]=1;b[12,12]=1
        self.assertFalse(compare(a,b,np.ones_like(a,bool))['duplicate_gate'])
    def test_empty_fails_closed(self):
        a=np.zeros((16,16));self.assertTrue(compare(a,a,np.ones_like(a,bool))['duplicate_gate'])

class EvidenceTests(unittest.TestCase):
    def test_shared_tools_not_modified(self):
        pins=json.loads((ROOT/'vendor/template/pins.json').read_text())
        for f in pins['files']:
            self.assertEqual(hashlib.sha256((ROOT/'vendor/template'/f['local']).read_bytes()).hexdigest(),f['sha256'])
    def test_snapshot_hashes(self):
        manifest=json.loads((ROOT/'research/source_manifest.json').read_text())
        for f in manifest['files']:
            self.assertEqual(f['status'],'retrieved')
            b=(ROOT/'research/snapshots'/f['repo']/f['path']).read_bytes()
            self.assertEqual(hashlib.sha256(b).hexdigest(),f['sha256'])
    def test_negative_card_has_no_upload(self):
        c=json.loads((ROOT/'research/run_card.json').read_text())
        self.assertEqual(c['verdict'],'negative')
        self.assertFalse(c['ok_to_download_and_submit'])
        self.assertFalse(c['ok_to_submit'])
        self.assertRegex(c['raster_sha256'],r'^[0-9a-f]{64}$')
        tif_path=ROOT/c['raster_path']
        self.assertTrue(tif_path.exists())
        self.assertEqual(hashlib.sha256(tif_path.read_bytes()).hexdigest(),c['raster_sha256'])
        self.assertEqual(c['holdout']['label'],'HOLDOUT-DTI')
        self.assertGreater(c['holdout']['dti'],0.15)
        self.assertLessEqual(len(c['note']),140)
    def test_site_does_not_offer_fake_tiff(self):
        c=json.loads((ROOT/'research/run_card.json').read_text())
        tifs=sorted((ROOT/'docs').rglob('*.tif'))
        self.assertEqual(len(tifs),1)
        self.assertEqual(tifs[0],ROOT/c['raster_path'])
        self.assertIn('No new TIFF is approved for live portal submission',(ROOT/'docs/index.html').read_text())
    def test_audit_claim_matches_pair_records(self):
        d=json.loads((ROOT/'research/raster_audit.json').read_text())
        self.assertEqual(len(d['format_reports']),9)
        self.assertTrue(all(r['format_valid'] for r in d['format_reports']))
        self.assertEqual(len(d['directed_pairs']),72)
        self.assertTrue(all(p['duplicate_gate'] for p in d['directed_pairs']))

class SharedHoldoutContractTests(unittest.TestCase):
    def test_whole_components_hidden_and_disjoint(self):
        # SYNTHETIC contract fixture; never a competition HOLDOUT-DTI result.
        fp=np.ones((80,80),bool);truth=np.zeros_like(fp)
        for y,x in [(10,10),(10,60),(60,10),(60,60)]:truth[y:y+4,x]=1
        truth[39,5:70]=1
        h=SegmentHoldout(fp,truth,buffer_px=3)
        for f in h.folds:
            self.assertFalse((f['visible']&f['truth']).any())
            self.assertFalse((f['train']&f['valid']).any())
            for component in f['hidden_component_ids']:
                self.assertFalse(f['visible'][h.components==component].any())
    def test_too_small_buffer_rejected(self):
        fp=np.ones((8,8),bool)
        with self.assertRaises(ValueError):SegmentHoldout(fp,fp,buffer_px=2)

if __name__=='__main__':unittest.main()

class IntegrationSafetyTests(unittest.TestCase):
    def test_old_card_is_withdrawn(self):
        card=json.loads((ROOT/'evidence/run_card.json').read_text())
        self.assertEqual(card['integration_review']['prior_blindbasin_authorization'],'withdrawn')
        self.assertFalse(card['ok_to_download_and_submit'])
    def test_old_selector_cannot_approve(self):
        decision=json.loads((ROOT/'evidence/selector_decision.json').read_text())
        self.assertFalse(decision['ok_to_submit'])
        self.assertFalse(decision['slot_approved'])
    def test_archived_tiffs_not_published(self):
        quarantine_tifs=list((ROOT/'research/quarantine').rglob('*.tif'))
        self.assertTrue(quarantine_tifs)
        quarantine_hashes={hashlib.sha256(p.read_bytes()).hexdigest() for p in quarantine_tifs}
        for p in (ROOT/'docs').rglob('*.tif'):
            self.assertNotIn(hashlib.sha256(p.read_bytes()).hexdigest(),quarantine_hashes)
    def test_active_source_has_no_placeholder_canary(self):
        self.assertFalse((ROOT/'src/features.py').exists())
        self.assertTrue((ROOT/'vendor/template/src/gems/holdout.py').exists())
