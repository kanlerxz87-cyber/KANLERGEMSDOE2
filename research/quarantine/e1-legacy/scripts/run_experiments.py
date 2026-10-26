#!/usr/bin/env python3
"""3 preregistered experiments, quadrant-blocked OOF + upstream hide-recover comparison.
E1 XG-HGB: supervised HGB on label-free multi-physics stack (incl. mag-grav cross-gradient).
E2 XG-UNSUP: unsupervised cross-gradient boundary surface alone.
E3 SPRING-BLEND: E1 global surface anisotropically boosted by GDR spring heat density.
Emission: greedy spacing>=3px, catalogue gate d>2px (visible-only in OOF, full in final), budget 37654.
"""
import json, pathlib, sys, hashlib, csv
import numpy as np, rasterio
from scipy.ndimage import distance_transform_edt, binary_dilation, binary_erosion, gaussian_filter, label as cc_label
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ROOT = pathlib.Path(__file__).resolve().parents[1]; DATA=ROOT/"data"; CACHE=ROOT/".cache"; EV=ROOT/"evidence"; EV.mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT/"src"))
from gems import metric

BUDGET=37654; ALPHA=0.2; BETA=0.8

def load_grid():
    with rasterio.open(DATA/"sample_submission.tif") as ds: foot=np.isfinite(ds.read(1))
    with rasterio.open(DATA/"labels.tif") as ds: labels=(ds.read(1)>0)&foot
    return foot, labels

def quadrants(foot):
    yy,xx=np.nonzero(foot); ym,xm=int(np.median(yy)),int(np.median(xx))
    H,W=foot.shape; gy,gx=np.ogrid[:H,:W]; q=np.full((H,W),-1,np.int8)
    q[(gy<ym)&(gx<xm)&foot]=0; q[(gy<ym)&(gx>=xm)&foot]=1; q[(gy>=ym)&(gx<xm)&foot]=2; q[(gy>=ym)&(gx>=xm)&foot]=3
    return q

def greedy_dots(score, allowed, budget, spacing=3):
    """Select top-scoring pixels subject to Euclidean min-spacing (disk radius spacing-1 blocked)."""
    cand = np.argwhere(allowed)
    if len(cand)==0: return np.zeros_like(allowed)
    vals = score[allowed]
    order = np.argsort(-vals, kind="stable")
    cand = cand[order]
    blocked=np.zeros(allowed.shape,bool); chosen=np.zeros(allowed.shape,bool)
    r=spacing-1
    yy,xx=np.ogrid[-r:r+1,-r:r+1]; disk=(yy*yy+xx*xx)<spacing*spacing
    n=0; H,W=allowed.shape
    for (y,x) in cand:
        if blocked[y,x]: continue
        chosen[y,x]=True; n+=1
        y0,y1=max(0,y-r),min(H,y+r+1); x0,x1=max(0,x-r),min(W,x+r+1)
        d=disk[y0-(y-r):disk.shape[0]-(y+r+1-y1) if y+r+1-y1>0 else disk.shape[0], x0-(x-r):disk.shape[1]-(x+r+1-x1) if x+r+1-x1>0 else disk.shape[1]]
        blocked[y0:y1,x0:x1]|=d
        if n>=budget: break
    return chosen

def dti_binary(pred, truth):
    return metric.dti_binary(pred, truth)

def robust_unit(a, foot):
    v=a[foot]; lo,hi=np.percentile(v,[1,99.5]); return np.clip((a-lo)/max(hi-lo,1e-9),0,1).astype(np.float32)

def main():
    foot, labels = load_grid(); H,W=foot.shape
    stack=np.load(CACHE/"feature_stack.npy", mmap_mode="r")
    feats=json.loads((CACHE/"feature_stack.json").read_text())["features"]; nf=len(feats)
    rng=np.random.default_rng(20261026)
    # ---------- Leakage canaries: each feature alone vs catalogue (sampled) ----------
    pos_idx=np.argwhere(labels); neg_pool=np.argwhere(foot & (distance_transform_edt(~labels)>3))
    neg_idx=neg_pool[rng.choice(len(neg_pool), size=min(200000,len(neg_pool)), replace=False)]
    sample_idx=np.vstack([pos_idx, neg_idx]); y=np.r_[np.ones(len(pos_idx)), np.zeros(len(neg_idx))]
    Xcan=np.empty((len(sample_idx), nf), np.float32)
    for j in range(nf): Xcan[:,j]=stack[j][sample_idx[:,0], sample_idx[:,1]]
    canaries=[]
    for j,name in enumerate(feats):
        v=Xcan[:,j]; 
        if np.nanstd(v)<1e-12: auc=0.5
        else:
            a=roc_auc_score(y, v); auc=float(max(a,1-a))
        canaries.append({"feature":name,"auc_abs":auc,"leakage_flag":bool(auc>0.90)})
    (EV/"canaries.json").write_text(json.dumps(canaries,indent=2))
    print("max canary AUC", max(c['auc_abs'] for c in canaries), [c for c in canaries if c['auc_abs']>0.75])

    def sample_xy(mask_pos, mask_neg, n_pos=60000, n_neg=120000):
        pi=np.argwhere(mask_pos); ni=np.argwhere(mask_neg)
        pi=pi[rng.choice(len(pi), size=min(n_pos,len(pi)), replace=False)]
        ni=ni[rng.choice(len(ni), size=min(n_neg,len(ni)), replace=False)]
        idx=np.vstack([pi,ni]); yy=np.r_[np.ones(len(pi)),np.zeros(len(ni))]
        X=np.empty((len(idx),nf),np.float32)
        for j in range(nf): X[:,j]=stack[j][idx[:,0],idx[:,1]]
        return X,yy

    def train_model(train_mask):
        visible = labels & train_mask
        negmask = train_mask & foot & (distance_transform_edt(~labels)>3)
        X,y = sample_xy(visible, negmask)
        m=HistGradientBoostingClassifier(max_iter=300, learning_rate=0.06, max_leaf_nodes=31, min_samples_leaf=40, l2_regularization=1.0, random_state=7)
        m.fit(X,y); return m

    def predict(m, region):
        idx=np.argwhere(region); out=np.zeros(foot.shape,np.float32)
        for s in range(0,len(idx),200000):
            chunk=idx[s:s+200000]; X=np.empty((len(chunk),nf),np.float32)
            for j in range(nf): X[:,j]=stack[j][chunk[:,0],chunk[:,1]]
            out[chunk[:,0],chunk[:,1]]=m.predict_proba(X)[:,1]
        return out

    q=quadrants(foot)
    # ---------- E2 unsupervised surface ----------
    idx_x = feats.index("xgrad_mag_grav"); idx_l1=feats.index("line_rtp"); idx_l2=feats.index("line_grav")
    surf_e2 = robust_unit(np.asarray(stack[idx_x],np.float32), foot)  # pure cross-gradient, preregistered

    # spring density for E3
    spring=np.zeros(foot.shape,np.float32)
    with open(DATA/"external/gdr_wellspring_in_footprint.csv") as f:
        r=list(csv.DictReader(f))
    seen=set()
    for row in r:
        try: rr,cc=int(row["row"]),int(row["col"]); t=float(row["temp_c"]) if row["temp_c"] else 20.0
        except Exception: continue
        if (rr,cc) in seen: continue
        seen.add((rr,cc))
        if 0<=rr<H and 0<=cc<W: spring[rr,cc]=max(spring[rr,cc], min(t,100)/100.0)
    spring_smooth=gaussian_filter(spring, sigma=8)
    spring_unit=robust_unit(spring_smooth, foot)
    (EV/"spring_points.json").write_text(json.dumps({"unique_spring_pixels":len(seen)}))
    print("spring pixels", len(seen))

    results={}
    # ---------- OOF for E1 and E2 ----------
    for exp in ["E1","E2"]:
        pooled_tp=pooled_fp=pooled_n=0; per_fold={}
        total_domain=int(sum((binary_erosion(q==f, iterations=12)&foot).sum() for f in range(4)))
        for f in range(4):
            foldmask=(q==f); domain=binary_erosion(foldmask, iterations=12)&foot
            collar=binary_dilation(foldmask, iterations=15)&foot
            train_mask=foot & ~collar
            visible=labels & train_mask
            d_vis=distance_transform_edt(~visible)
            budget_f=int(round(BUDGET*domain.sum()/foot.sum()))
            if exp=="E1":
                model=train_model(train_mask); score=predict(model, domain)
            else:
                score=surf_e2
            allowed=domain & (d_vis>2)
            dots=greedy_dots(score, allowed, budget_f)
            truth=labels & domain
            res=dti_binary(dots & ~visible, truth)  # visible masked pixel-exact via domain? truth excludes visible outside domain anyway
            per_fold[f"fold{f}"]={"dti":res["dti"],"tp":res["tp"],"fp":res["fp"],"n_truth":res["n_truth"],"emitted":int(dots.sum()),"budget":budget_f}
            pooled_tp+=res["tp"]; pooled_fp+=res["fp"]; pooled_n+=res["n_truth"]
            print(exp, f, res, flush=True)
        pooled=float(pooled_tp/(pooled_tp+ALPHA*pooled_fp+BETA*(pooled_n-pooled_tp)+1e-12))
        # block bootstrap CI over 4 folds (coarse, labelled as such)
        cells=[(v["tp"],v["fp"],v["n_truth"]) for v in per_fold.values()]; boots=[]
        brng=np.random.default_rng(11)
        for _ in range(2000):
            pick=[cells[i] for i in brng.integers(0,len(cells),len(cells))]
            tp=sum(c[0] for c in pick); fp=sum(c[1] for c in pick); n=sum(c[2] for c in pick)
            boots.append(tp/(tp+ALPHA*fp+BETA*(n-tp)+1e-12))
        results[exp]={"evidence":"HOLDOUT-DTI","evaluator":"KANLER quadrant-blocked OOF v1 (whole-quadrant holdout, 15px collar, 12px domain erosion, visible-only B=2 gate, alpha0.2 beta0.8 300m triangular)","pooled_dti":pooled,"ci95_foldbootstrap":[float(np.percentile(boots,2.5)),float(np.percentile(boots,97.5))],"n_withheld_positives":int(pooled_n),"per_fold":per_fold}
    # ---------- Final global E1 + E3 ----------
    print("training global E1")
    model=train_model(foot)
    score_e1=predict(model, foot)
    np.save(CACHE/"score_e1.npy", score_e1)
    surf_e3 = score_e1*(0.65+0.70*spring_unit)  # preregistered blend: max ~2x boost at hot springs
    surf_e3 = robust_unit(surf_e3, foot)
    np.save(CACHE/"score_e3.npy", surf_e3); np.save(CACHE/"surf_e2.npy", surf_e2)
    d_full=distance_transform_edt(~labels)
    for exp,score in [("E1",score_e1),("E2",surf_e2),("E3",surf_e3)]:
        dots=greedy_dots(score, foot & (d_full>2), BUDGET)
        np.save(CACHE/f"dots_{exp}.npy", dots)
        print(exp, "dots", int(dots.sum()))
    (EV/"experiments_oof.json").write_text(json.dumps(results,indent=2))
    print(json.dumps(results,indent=2))

if __name__=="__main__": main()
