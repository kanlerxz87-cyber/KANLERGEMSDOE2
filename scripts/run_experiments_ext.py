#!/usr/bin/env python3
"""Lane KANLER-EXT-CORROB: 3 pre-registered experiments (see
research/preregistration-ext-corrob.md, written before any run).

Exp1 CORROB: label-free geometric-mean corroboration (mag/grav line responses,
cross-gradient, tilt-zero, LiDAR step/dipole, LiDAR-coverage routed).
Exp2 MCSUP: HistGradientBoosting, positives = catalogue UNION off-cat SGMC
(fold-local), 47-ch stack (scripts/build_features.py, reused unchanged).
Exp3 EMIT: budget sweep {25000, 44090} on the Exp1/Exp2 OOF winner.

Evaluation (all HOLDOUT-DTI, alpha 0.2 beta 0.8 300m triangular):
 - primary: KANLER quadrant-blocked OOF v1 (fold-local emission, visible-only
   B=2 gate), as in scripts/run_experiments.py (E1 lane, reused pattern);
 - callable GEMSDOE32-HOLDOUT-v3-visible-gated (fold-local re-emission);
 - SGMC off-catalogue raw on final masks, paired 16-tile bootstrap vs champion.
Uniqueness: sampled surface Spearman + exact Euclidean 3px dot overlap vs
9 registry bests + quarantined E1 mask, BEFORE placement (surface) and after.
"""
import json, pathlib, sys, time
import numpy as np, rasterio
from scipy.ndimage import distance_transform_edt, binary_dilation, binary_erosion
from scipy.spatial import cKDTree
from scipy.stats import spearmanr
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA, CACHE, EV = ROOT / "data", ROOT / ".cache", ROOT / "evidence"
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
from gems import metric, holdout
from run_experiments import greedy_dots, robust_unit, quadrants

ALPHA, BETA, BUDGET = 0.2, 0.8, 37654
E1_TIF = ROOT / "research/quarantine/prior-docs/downloads/kanler-e1-xg-hgb-37654d-20261026T214616Z-7ab68c3efd-allfinite.tif"

def load_mask(p, foot):
    with rasterio.open(p) as ds: a = ds.read(1)
    return np.isfinite(a) & (a > 0) & foot

def pooled(cells):
    tp = sum(c[0] for c in cells); fp = sum(c[1] for c in cells); n = sum(c[2] for c in cells)
    return float(tp / (tp + ALPHA * fp + BETA * (n - tp) + 1e-12))

def boot_ci(cells, seed=11, n=2000):
    rng = np.random.default_rng(seed)
    boots = [pooled([cells[i] for i in rng.integers(0, len(cells), len(cells))]) for _ in range(n)]
    return [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]

def uniqueness(surface, dots, foot, refs):
    rng = np.random.default_rng(3); idx = np.argwhere(foot)
    sel = idx[rng.choice(len(idx), 200000, replace=False)]
    sv = surface[sel[:, 0], sel[:, 1]]; dpts = np.argwhere(dots); rows = []
    for name, reg in refs:
        rv = reg[sel[:, 0], sel[:, 1]].astype(float)
        rho = float(spearmanr(sv, rv).statistic) if np.std(rv) > 0 else 0.0
        ov = float(np.mean(cKDTree(np.argwhere(reg)).query(dpts)[0] <= 3.0)) if len(dpts) else 0.0
        rows.append({"registry": name, "surface_spearman_sampled200k": rho,
                     "dot_overlap_3px_euclidean": ov,
                     "duplicate": bool(abs(rho) > 0.90 or ov > 0.70)})
    return {"max_abs_surface_spearman": max(abs(r["surface_spearman_sampled200k"]) for r in rows),
            "max_dot_overlap_3px": max(r["dot_overlap_3px_euclidean"] for r in rows),
            "pass": all(not r["duplicate"] for r in rows), "rows": rows}

def main():
    t0 = time.time()
    with rasterio.open(DATA / "sample_submission.tif") as ds: foot = np.isfinite(ds.read(1))
    with rasterio.open(DATA / "labels.tif") as ds: labels = (ds.read(1) > 0) & foot
    stack = np.load(CACHE / "feature_stack.npy", mmap_mode="r")
    feats = json.loads((CACHE / "feature_stack.json").read_text())["features"]; nf = len(feats)
    fi = {n: i for i, n in enumerate(feats)}
    ctx = holdout.load_holdout_context(DATA)
    sgmc_off = ctx.sgmc_off
    print(f"foot {foot.sum()} labels {labels.sum()} sgmc_off {sgmc_off.sum()} ctx cells {len(ctx.cells)} [{time.time()-t0:.0f}s]", flush=True)

    # ---------- leakage canaries (each feature alone vs catalogue) ----------
    rng = np.random.default_rng(20261026)
    pos_idx = np.argwhere(labels)
    neg_pool = np.argwhere(foot & (distance_transform_edt(~labels) > 3))
    neg_idx = neg_pool[rng.choice(len(neg_pool), size=min(200000, len(neg_pool)), replace=False)]
    sidx = np.vstack([pos_idx, neg_idx]); y = np.r_[np.ones(len(pos_idx)), np.zeros(len(neg_idx))]
    can = []
    for j, name in enumerate(feats):
        v = np.asarray(stack[j][sidx[:, 0], sidx[:, 1]], float)
        auc = 0.5 if np.nanstd(v) < 1e-12 else float(max(roc_auc_score(y, v), 1 - roc_auc_score(y, v)))
        can.append({"feature": name, "auc_abs": auc, "leakage_flag": bool(auc > 0.90)})
    (EV / "canaries_ext.json").write_text(json.dumps(can, indent=2))
    print("canary max AUC", max(c["auc_abs"] for c in can), flush=True)

    # ---------- Exp1 CORROB surface (label-free) ----------
    def ru(name): return robust_unit(np.asarray(stack[fi[name]], np.float32), foot)
    base = [ru("xgrad_mag_grav"), ru("line_rtp"), ru("line_grav"), ru("tilt_zero")]
    lid = [ru("lid_step"), ru("lid_dipole")]
    valid = np.asarray(stack[fi["lid_valid"]], np.float32) > 0.5
    eps = 0.02
    logsum = sum(np.log(c + eps) for c in base); ncomp = np.full(foot.shape, float(len(base)))
    for c in lid:
        logsum = np.where(valid, logsum + np.log(c + eps), logsum); ncomp = np.where(valid, ncomp + 1, ncomp)
    surf1 = np.where(foot, np.exp(logsum / ncomp), 0).astype(np.float32)
    np.save(CACHE / "score_corrob.npy", surf1)
    print(f"Exp1 surface done [{time.time()-t0:.0f}s]", flush=True)

    # ---------- Exp2 MCSUP helpers ----------
    union_pos = labels | sgmc_off
    d_union = distance_transform_edt(~union_pos)
    def sample_xy(pos_mask, neg_mask):
        pi = np.argwhere(pos_mask); ni = np.argwhere(neg_mask)
        pi = pi[rng.choice(len(pi), size=min(60000, len(pi)), replace=False)]
        ni = ni[rng.choice(len(ni), size=min(120000, len(ni)), replace=False)]
        idx = np.vstack([pi, ni]); yy = np.r_[np.ones(len(pi)), np.zeros(len(ni))]
        X = np.empty((len(idx), nf), np.float32)
        for j in range(nf): X[:, j] = stack[j][idx[:, 0], idx[:, 1]]
        return X, yy
    def train(train_mask):
        X, yy = sample_xy(union_pos & train_mask, train_mask & foot & (d_union > 3))
        m = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.06, max_leaf_nodes=31,
                                           min_samples_leaf=40, l2_regularization=1.0, random_state=7)
        m.fit(X, yy); return m
    def predict(m, region):
        idx = np.argwhere(region); out = np.zeros(foot.shape, np.float32)
        for s in range(0, len(idx), 200000):
            ch = idx[s:s + 200000]; X = np.empty((len(ch), nf), np.float32)
            for j in range(nf): X[:, j] = stack[j][ch[:, 0], ch[:, 1]]
            out[ch[:, 0], ch[:, 1]] = m.predict_proba(X)[:, 1]
        return out

    q = quadrants(foot)
    fold_frac, fold_domains = {}, {}
    for f in range(4):
        fold_domains[f] = binary_erosion(q == f, iterations=12) & foot
        fold_frac[f] = float(fold_domains[f].sum() / foot.sum())

    def oof_eval(exp, budget=BUDGET, surface=None):
        per, cells, cells_sg = {}, [], []
        for f in range(4):
            domain = fold_domains[f]
            collar = binary_dilation(q == f, iterations=15) & foot
            train_mask = foot & ~collar
            visible = labels & train_mask
            d_vis = distance_transform_edt(~visible)
            bf = int(round(budget * fold_frac[f]))
            score = predict(train(train_mask), domain) if exp == "MCSUP" else surface
            dots = greedy_dots(score, domain & (d_vis > 2), bf)
            for truth, acc in [(labels & domain, cells), (sgmc_off & domain, cells_sg)]:
                r = metric.dti_binary(dots & ~visible, truth); acc.append((r["tp"], r["fp"], r["n_truth"]))
            r0 = metric.dti_binary(dots & ~visible, labels & domain)
            per[f"fold{f}"] = {"dti": r0["dti"], "tp": r0["tp"], "fp": r0["fp"],
                               "n_truth": r0["n_truth"], "emitted": int(dots.sum()), "budget": bf}
            print(exp, "budget", budget, "fold", f, {k: round(v, 4) if isinstance(v, float) else v for k, v in per[f"fold{f}"].items()}, flush=True)
        return {"label": "HOLDOUT-DTI",
                "evaluator": "KANLER quadrant-blocked OOF v1 (whole-quadrant holdout, 15px collar, 12px domain erosion, visible-only B=2 gate, alpha0.2 beta0.8 300m triangular)",
                "budget": budget, "pooled_dti": pooled(cells), "ci95_foldbootstrap": boot_ci(cells),
                "n_withheld_positives": int(sum(c[2] for c in cells)),
                "sgmc_oof_pooled_dti": pooled(cells_sg), "sgmc_oof_ci95": boot_ci(cells_sg),
                "sgmc_oof_n": int(sum(c[2] for c in cells_sg)), "per_fold": per}

    results = {}
    # registry refs (9 bests + E1)
    refs = [(p.name, load_mask(p, foot)) for p in sorted((DATA / "registry").glob("*.tif"))]
    refs.append(("kanler_e1_quarantined.tif", load_mask(E1_TIF, foot)))
    champ = dict(refs)["g32_champion.tif"]
    d_full = distance_transform_edt(~labels)

    def full_eval(exp_name, surface, budget):
        dots = greedy_dots(surface, foot & (d_full > 2), budget)
        np.save(CACHE / f"dots_{exp_name}.npy", dots)
        uniq = uniqueness(surface, dots, foot, refs)
        def emit(cell):
            sl = cell.bbox
            return greedy_dots(surface[sl], cell.active_sub & (cell.d_visible_sub > 2),
                               int(round(budget * fold_frac[cell.fold])))
        vg = holdout.evaluate_visible_gated_holdout(emit, ctx, b_gate_px=2.0,
                                                    full_map_mask=dots, name=exp_name)
        vg = {k: v for k, v in vg.items() if k != "cells"}
        # paired SGMC bootstrap vs champion (16 tiles, same tiling as holdout.py)
        def sgmc_tiles(mask):
            ev = mask & (d_full > 2) & foot & ~labels
            dp = distance_transform_edt(~ev); k = metric.kernel(dp[ctx.sgmc_truth_coords])
            fpv = 1.0 - ctx.sgmc_k_dg[ev]
            ty = np.clip((ctx.sgmc_truth_coords[0] * 4) // foot.shape[0], 0, 3)
            tx = np.clip((ctx.sgmc_truth_coords[1] * 4) // foot.shape[1], 0, 3); tb = ty * 4 + tx
            ey, ex = np.nonzero(ev)
            eb = np.clip((ey * 4) // foot.shape[0], 0, 3) * 4 + np.clip((ex * 4) // foot.shape[1], 0, 3)
            return [(float(k[tb == b].sum()), float(fpv[eb == b].sum()), int((tb == b).sum())) for b in range(16)]
        tc, th = sgmc_tiles(dots), sgmc_tiles(champ)
        brng = np.random.default_rng(7); diffs = []
        for _ in range(2000):
            pick = brng.integers(0, 16, 16)
            diffs.append(pooled([tc[i] for i in pick]) - pooled([th[i] for i in pick]))
        paired = {"diff_ci95": [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))],
                  "champion_sgmc_raw": pooled(th), "candidate_sgmc_raw": pooled(tc)}
        print(exp_name, "dots", int(dots.sum()), "uniq max|rho|", round(uniq["max_abs_surface_spearman"], 4),
              "maxOv", round(uniq["max_dot_overlap_3px"], 4), "VG", round(vg["dti"], 5),
              "SGMC", round(paired["candidate_sgmc_raw"], 5), "vs champ", round(paired["champion_sgmc_raw"], 5), flush=True)
        return {"dots": int(dots.sum()), "uniqueness": uniq, "visible_gated_callable": vg,
                "sgmc_paired_vs_champion": paired}

    results["EXP1_CORROB"] = {"oof": oof_eval("CORROB", surface=surf1), **full_eval("EXP1_CORROB", surf1, BUDGET)}
    print(f"Exp1 done [{time.time()-t0:.0f}s]", flush=True)

    results["EXP2_MCSUP"] = {"oof": oof_eval("MCSUP")}
    surf2 = predict(train(foot), foot); np.save(CACHE / "score_mcsup.npy", surf2)
    results["EXP2_MCSUP"].update(full_eval("EXP2_MCSUP", surf2, BUDGET))
    print(f"Exp2 done [{time.time()-t0:.0f}s]", flush=True)

    # ---------- Exp3 EMIT: budget sweep on OOF winner ----------
    w = "EXP1_CORROB" if results["EXP1_CORROB"]["oof"]["pooled_dti"] >= results["EXP2_MCSUP"]["oof"]["pooled_dti"] else "EXP2_MCSUP"
    wsurf = surf1 if w == "EXP1_CORROB" else surf2
    sweep = {str(BUDGET): results[w]["oof"]["pooled_dti"]}
    for b in (25000, 44090):
        r = oof_eval("MCSUP" if w == "EXP2_MCSUP" else "CORROB", budget=b, surface=wsurf if w == "EXP1_CORROB" else None) \
            if w == "EXP1_CORROB" else oof_eval("MCSUP", budget=b)
        sweep[str(b)] = r["pooled_dti"]; results.setdefault("EXP3_EMIT", {})[f"oof_{b}"] = r
    best_b = int(max(sweep, key=sweep.get))
    results["EXP3_EMIT"].update({"winner_surface": w, "sweep_pooled_dti": sweep, "best_budget": best_b})
    if best_b != BUDGET:
        results["EXP3_EMIT"].update(full_eval("EXP3_EMIT", wsurf, best_b))
        results["EXP3_EMIT"]["oof"] = results[w]["oof"] if False else results["EXP3_EMIT"].get(f"oof_{best_b}")
    else:
        results["EXP3_EMIT"].update({k: results[w][k] for k in ("dots", "uniqueness", "visible_gated_callable", "sgmc_paired_vs_champion")})
        results["EXP3_EMIT"]["oof"] = results[w]["oof"]
        np.save(CACHE / "dots_EXP3_EMIT.npy", np.load(CACHE / f"dots_{w}.npy"))
    results["meta"] = {"seconds": time.time() - t0, "canary_max_auc": max(c["auc_abs"] for c in can),
                       "features": feats}
    (EV / "experiments_ext.json").write_text(json.dumps(results, indent=2, default=float))
    print(json.dumps({k: {"oof": round(v["oof"]["pooled_dti"], 5),
                          "vg": round(v["visible_gated_callable"]["dti"], 5),
                          "sgmc": round(v["sgmc_paired_vs_champion"]["candidate_sgmc_raw"], 5)}
                      for k, v in results.items() if k.startswith("EXP")}, indent=2))
    print("champion SGMC paired-base", results["EXP1_CORROB"]["sgmc_paired_vs_champion"]["champion_sgmc_raw"])

if __name__ == "__main__":
    main()
