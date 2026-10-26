"""Fail-closed evidence gate. Format validity alone never authorizes submission."""
import math

def check(card):
    errors=[]
    if not card.get('lane'): errors.append('Missing assigned method lane')
    if card.get('registry_complete') is not True: errors.append('Registry coverage unverified')
    for stage in ('surface','dots'):
        values=card.get(stage,{})
        for name,limit in [('max_abs_rank_correlation',.90),('max_overlap_3px',.70)]:
            value=values.get(name)
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=limit:
                errors.append(f'{stage}.{name}: missing, invalid, or duplicate')
    auc=card.get('max_feature_alone_auc')
    if isinstance(auc,bool) or not isinstance(auc,(int,float)) or not math.isfinite(auc) or not 0<=auc<=.90:
        errors.append('Leakage canary absent or failed')
    h=card.get('holdout',{})
    if h.get('label')!='HOLDOUT-DTI' or not h.get('evaluator_version') or not isinstance(h.get('withheld_positives'),int) or h.get('withheld_positives',0)<=0:
        errors.append('Missing versioned holdout evidence')
    score=h.get('dti')
    interval=h.get('ci95')
    if type(score) not in (int,float) or not math.isfinite(score) or not 0<=score<=1:
        errors.append('Missing or invalid HOLDOUT-DTI')
    if not isinstance(interval,list) or len(interval)!=2 or not all(type(v) in (int,float) and math.isfinite(v) and 0<=v<=1 for v in interval) or interval[0]>interval[1] or (type(score) in (int,float) and not interval[0]<=score<=interval[1]):
        errors.append('Missing or invalid holdout 95% CI')
    if h.get('fold_local_features') is not True or not h.get('baseline_id'):
        errors.append('Missing fold-local feature evidence or baseline identity')
    ci=h.get('paired_improvement_ci95')
    if not isinstance(ci,list) or len(ci)!=2 or not all(type(v) in (int,float) and math.isfinite(v) for v in ci) or not 0<ci[0]<=ci[1]:
        errors.append('No positive paired 95% CI against current holdout best')
    for key in ('no_nan_inside_footprint','range_0_1','crs_match','shape_match','transform_match','single_band'):
        if card.get('validator',{}).get(key) is not True: errors.append('Validator missing/failed: '+key)
    sha=card.get('raster_sha256','')
    if not isinstance(sha,str) or len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha): errors.append('Missing raster SHA256')
    if not card.get('submission_name') or not isinstance(card.get('note'),str) or len(card.get('note',''))>140: errors.append('Invalid name/note')
    return {'verdict':'negative' if errors else 'promote','eligible_for_selector':not errors,'authorized_to_submit':False,'errors':errors}
