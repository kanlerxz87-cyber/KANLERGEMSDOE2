#!/usr/bin/env python3
"""KG2-S3 CVC-300: vote-consensus CELF, 3 preregistered experiments, hide-recover gated."""
import json, sys, time, hashlib, zipfile
from pathlib import Path
import numpy as np, rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from gems.submodular_celf import greedy_disk_allocate as celf_submodular_allocate  # DEVIATION logged: exact CELF timed out >1700s at 37654 picks; disk-greedy (min_spacing=3px default in signature is via greedy_disk_allocate) is the repo fast emitter
from gems32 import holdout
DD=Path("/tmp/gems_data")
DL=ROOT/"docs/downloads"
BUDGET=37654
FOCUS={
 "GEMSDOE24":"gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif",
 "GEMSDOE25":"gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif",
 "GEMSDOE27":"gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif",
 "GEMSDOE28":"gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif",
 "GEMSDOE30":"gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif",
 "GEMSDOE31":"gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif",
 "GEMSDOE32":"gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
 "GEMSDOE33":"GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif",
 "GEMSDOE36":"gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
}
EXTRA={"DSLUP":"kanlergems2-dslup-uniq-q15k-37654dots-20261027T181253Z-c71122d5-zeros.tif","DARP":"kanlergems2-darp-exp-1-37654dots-20261027T181633Z-4ad35e71-zeros.tif","HTCADS":"kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif","ECPU":"kanlergems2-ecpu-exp-1-37654dots-20261027T172822Z-cecbdca7-zeros.tif"}
def load(name):
    with rasterio.open(DL/name) as ds: a=ds.read(1)
    return np.isfinite(a)&(a>0)
def dil(mask): return binary_dilation(mask, structure=np.ones((7,7),bool))  # 3px Chebyshev approx via 7x7? use EDT instead
def overlap3(our, ref):
    # fraction of our dots within 3px (Euclidean) of ref
    d=distance_transform_edt(~ref)
    return float((d[our]<=3.0).mean()) if our.any() else 0.0
def spearman_bin(a,b):
    # Pearson on binary = phi; report as correlation proxy
    af=a.ravel().astype(np.float64); bf=b.ravel().astype(np.float64)
    return float(np.corrcoef(af,bf)[0,1])
def main():
    raise SystemExit(
        "Archived runner disabled: not the assigned HTCADS lane; the literal registry stop "
        "and preserved historical receipts prohibit this execution path."
    )


def _legacy_main_archived():
    """Historical implementation retained for audit; do not use as an active runner."""
    t0=time.time()
    ctx=holdout.load_holdout_context(DD)
    foot, labels = ctx.foot, ctx.labels
    print("foot",foot.sum(),"labels",labels.sum(), flush=True)
    masks={k:load(v)&foot for k,v in FOCUS.items()}
    extra={k:load(v)&foot for k,v in EXTRA.items()}
    vote=sum(masks.values()).astype(np.float32)
    # canary: AUC of each feature vs withheld positives (all cells pooled truth vs random negatives)
    from sklearn.metrics import roc_auc_score
    truth=np.zeros(foot.shape,bool)
    for c in ctx.cells:
        sl=c.bbox; sub=np.zeros_like(truth[sl]); sub[c.truth_coords]=True; truth[sl]|=sub
    d_lab=distance_transform_edt(~labels).astype(np.float32)
    feats={"vote_focus":vote.astype(np.float32),"dslup_ind":extra["DSLUP"].astype(np.float32),"darp_ind":extra["DARP"].astype(np.float32),"champion32_ind":masks["GEMSDOE32"].astype(np.float32)}  # neg_dist_catalogue tested separately: pooled AUC 0.996 vs full labels = leakage by construction (hidden segments are in full labels); NOT used as a feature in EXP1/EXP2/EXP3
    rng=np.random.default_rng(0)
    pos=np.flatnonzero((truth&foot).ravel()); neg_all=np.flatnonzero((foot&~truth).ravel()); neg=rng.choice(neg_all,size=min(240000,len(neg_all)),replace=False)
    can={}
    for n,f in feats.items():
        y=np.r_[np.ones(len(pos)),np.zeros(len(neg))]; s=np.r_[f.ravel()[pos],f.ravel()[neg]]
        auc=float(roc_auc_score(y,s)); can[n]={"auc_raw":auc,"auc_oriented":max(auc,1-auc)}
    maxauc=max(v["auc_oriented"] for v in can.values())
    print("canary",can, flush=True)
    assert maxauc<=0.90, "leakage canary fail"
    # references
    champ=masks["GEMSDOE32"]; dslup=extra["DSLUP"]
    def ev(mask,name):
        hr=holdout.evaluate_hide_and_recover(mask,ctx,b_visible_px=2.0,n_boot=1000,seed=20261026,name=name)
        sg=holdout.evaluate_sgmc_with_ci(mask,ctx,n_boot=1000,seed=20261026,name=name)
        return hr,sg
    ref_hr,ref_sg=ev(champ,"champion32")
    dsl_hr,dsl_sg=ev(dslup,"dslup_uniq")
    print(f"REF champ HR={ref_hr['pooled_dti']:.4f} SG={ref_sg['sgmc_prevalence_calibrated_dti']:.4f} | DSLUP HR={dsl_hr['pooled_dti']:.4f} SG={dsl_sg['sgmc_prevalence_calibrated_dti']:.4f}", flush=True)
    allowed=foot&~labels
    exps={}
    # EXP1 vote only
    pi1=np.where(allowed, vote/9.0, 0).astype(np.float32)
    m1=celf_submodular_allocate(pi1,allowed,BUDGET)>0
    # EXP3 high-consensus only (replaces sweet-band: full-label distance leaked hidden segments, canary AUC 0.996, so band design is invalid for static holdout)
    band=allowed&(vote>=3)
    m3=celf_submodular_allocate(pi1,band,BUDGET)>0
    # EXP2 vote+bonus with DSLUP halo cap: emit in two tranches - first CELF on pi2 excluding DSLUP 3px halo for (BUDGET-15000) dots, then fill from halo by pi2
    pi2=np.where(allowed, vote/9.0+0.15*extra["DSLUP"]+0.15*extra["DARP"],0).astype(np.float32)
    halo=distance_transform_edt(~dslup)<=3.0
    m2a=celf_submodular_allocate(pi2,allowed&~halo,BUDGET-15000)>0
    # fill: CELF on remaining allowed not already chosen, budget 15000, pi2 (coverage approx independent - documented)
    m2b=celf_submodular_allocate(pi2,allowed&~m2a,15000)>0
    m2=m2a|m2b
    results={}
    for eid,m in [("EXP1",m1),("EXP2",m2),("EXP3",m3)]:
        hr,sg=ev(m,eid)
        d_hr=holdout.paired_bootstrap_delta(hr,ref_hr); d_sg=holdout.paired_bootstrap_delta(sg,ref_sg,boot_key="_cal_boots")
        d_hr2=holdout.paired_bootstrap_delta(hr,dsl_hr); 
        ov={k:round(overlap3(m,v),4) for k,v in {**masks,**extra}.items()}
        corr={k:round(spearman_bin(m,v),4) for k,v in {**masks,**extra}.items()}
        results[eid]={"dots":int(m.sum()),"hr":hr["pooled_dti"],"hr_ci":hr["ci95_cluster_bootstrap"],"hr_N":hr["n_withheld_positives"],"sgmc":sg["sgmc_prevalence_calibrated_dti"],"sgmc_ci":sg["sgmc_calibrated_ci95"],"sgmc_N":sg["n_withheld_positives"],"delta_hr_vs_champ":d_hr,"delta_sg_vs_champ":d_sg,"delta_hr_vs_dslup":d_hr2,"max_overlap3":max(ov.values()),"overlaps":ov,"max_abs_corr":max(abs(v) for v in corr.values()),"corrs":corr,"on_catalogue":int((m&labels).sum())}
        print(eid, results[eid]["hr"], results[eid]["sgmc"], "maxov",results[eid]["max_overlap3"], flush=True)
        np.save(f"/tmp/cvc_{eid}.npy", m)
    out={"lane":"KG2-S3-CVC300","wall_s":time.time()-t0,"canary":{"features":can,"max_auc":maxauc,"passed":bool(maxauc<=0.90)},"ref_champion":{"hr":ref_hr["pooled_dti"],"hr_ci":ref_hr["ci95_cluster_bootstrap"],"sgmc":ref_sg["sgmc_prevalence_calibrated_dti"],"N_hr":ref_hr["n_withheld_positives"],"N_sgmc":ref_sg["n_withheld_positives"]},"ref_dslup":{"hr":dsl_hr["pooled_dti"],"sgmc":dsl_sg["sgmc_prevalence_calibrated_dti"]},"experiments":results}
    (ROOT/"evidence/cvc300_experiments.json").write_text(json.dumps(out,indent=2,allow_nan=False)+"\n")
    print(json.dumps(out,indent=2)[:4000])
if __name__=="__main__": main()
