import unittest
from scripts.promotion_gate import check
class GateTests(unittest.TestCase):
    def valid(self):
        return dict(lane='assigned',registry_complete=True,surface=dict(max_abs_rank_correlation=.2,max_overlap_3px=.2),dots=dict(max_abs_rank_correlation=.2,max_overlap_3px=.2),max_feature_alone_auc=.7,holdout=dict(label='HOLDOUT-DTI',evaluator_version='test-only',withheld_positives=100,dti=.2,ci95=[.18,.22],fold_local_features=True,baseline_id='test-baseline',paired_improvement_ci95=[.001,.01]),validator={k:True for k in ['no_nan_inside_footprint','range_0_1','crs_match','shape_match','transform_match','single_band','dtype_float32']},raster_sha256='a'*64,submission_name='test',note='test')
    def test_empty(self): self.assertEqual(check({})['verdict'],'negative')
    def test_promotion_is_not_slot_authorization(self):
        r=check(self.valid());self.assertTrue(r['eligible_for_selector']);self.assertFalse(r['authorized_to_submit'])
    def test_duplicate_boundary(self):
        c=self.valid();c['dots']['max_overlap_3px']=.70001;self.assertEqual(check(c)['verdict'],'negative')
    def test_nan(self):
        c=self.valid();c['surface']['max_abs_rank_correlation']=float('nan');self.assertEqual(check(c)['verdict'],'negative')
    def test_leakage(self):
        c=self.valid();c['max_feature_alone_auc']=.91;self.assertEqual(check(c)['verdict'],'negative')
    def test_missing_validator(self):
        c=self.valid();c['validator']['range_0_1']=False;self.assertEqual(check(c)['verdict'],'negative')
    def test_no_improvement(self):
        c=self.valid();c['holdout']['paired_improvement_ci95']=[-.01,.03];self.assertEqual(check(c)['verdict'],'negative')

    def test_missing_dti(self):
        c=self.valid();del c['holdout']['dti'];self.assertEqual(check(c)['verdict'],'negative')
    def test_missing_fold_local(self):
        c=self.valid();del c['holdout']['fold_local_features'];self.assertEqual(check(c)['verdict'],'negative')
