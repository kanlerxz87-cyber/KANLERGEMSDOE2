# KANLERGEMSDOE2 — DOE GEMS Prize Fault Discovery

> **Mission:** Generate a **unique, format-valid GeoTIFF** that predicts geological fault structures indicative of geothermal resources in the GeoDAWN region, with automated validation and no human inspection in the critical path.

**Competition:** [DOE GEMS Prize #306 on DrivenData](https://www.drivendata.org/competitions/306/competition-doe-gems/) — Total prize pool $300k (Initial Round $50k + Final Round $250k). Deadline 2026-12-03 UTC.

**Reference Solution:** [drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution) — U-Net + Monte-Carlo CV baseline using ~16 GeoDAWN channels at 100 m, EPSG:32611.

---

## Core Values — Own the Outcome

**Maximize P(Win):** Every decision weighs tradeoff, risk, and the path that maximizes probability of winning. Weekly submission slots are experiments, not lottery tickets — we don't spend a slot without paired, fold-local holdout evidence and uniqueness clearance.

**Own the Outcome:** We own results end-to-end. Failures are signals. Every claim carries an evidence class: `HOLDOUT-DTI` (evaluator version, withheld positives, 95% CI), `ORGANIZER-CONFIRMED` (submission-page receipt hash→score), or `PROJECTION` (model forecast, never a score).

**Verified Line-by-Line:** Every fact carries an official link for manual review. No hallucinations. Flag irregularities. If data is missing, say so — don't invent.

---

## The Problem in One Paragraph

Geological faults are fractures where rock blocks have displaced (normal = vertical, strike-slip = horizontal). Faults control geothermal fluid pathways but are often *hidden* — buried under alluvium, expressed only as subtle scarps, or absent from the USGS Quaternary Fault catalogue that is known to be incomplete. The GEMS Prize provides GeoDAWN airborne magnetics/radiometrics + lidar elevation over northwestern Great Basin (Walker Lane) and asks competitors to predict *new* expert-labeled faults not in the catalogue. Scoring uses a distance-weighted Tversky index (α=0.2, β=0.8, 300 m triangular kernel): false negatives penalized 4× more than false positives. The Final Round re-scores every submission against an expanded label set built from expert review of all submissions — so genuinely novel, geologically defensible predictions can outscore catalogue-clones.

**Official Sources:**
- Problem description: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- About/data: https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/
- Official Rules PDF: https://docs.nlr.gov/docs/fy26osti/96647.pdf (also Dropbox mirror: https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd)
- GeoDAWN: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- INGENIOUS: https://gbcge.org/current-projects/ingenious/
- CRS EPSG:32611: https://epsg.io/32611
- Tversky index: https://en.wikipedia.org/wiki/Tversky_index
- Metric weighting α=0.2/β=0.8/300m kernel documented on competition page and replicated in reference evaluator (see `src/metric.py`).

---

## TL;DR — What to Download and Submit

> **Status: 🟢 ONE UNIQUE TIF AUTHORIZED FOR UPLOAD — ALL AUTOMATED GATES PASS (see below).**

**If you do nothing else, read [docs/index.html](docs/index.html) → click the green download button → upload to DrivenData.**

| File | What it is | How to use |
|---|---|---|
| **`docs/downloads/kanlergemsdoe2-blindbasin-vent-gravity-20261026-2858780e-zeros.tif` + `.zip`** | **✅ AUTHORIZED — unique, all-finite [0,1], 37,654 dots, B=2-prune, EPSG:32611, 3730×3292, transform 100/243350/4508550, SHA256 `2858780e…`, validator 13/13 PASS** | **DOWNLOAD → DrivenData → New submission → choose .tif or .zip → paste note `KANLER HVG blind-basin vent-gravity 37654d B2 | HOLDOUT-DTI 0.1427 n=60988 | 2858780e` → Create** |
| `…-nan.tif` | Nan-outside twin for spec compliance (also authorized, same dots) | Use only if portal rejects zeros outside (historical edge case — zeros passes) |
| All other `*.tif` in `docs/downloads/` from sibling GEMSDOE sites (archived under `docs/evidence/`) | **Research/audit only — DO NOT SUBMIT** (duplicates, negatives, or already-submitted) | Download to study why they scored X, never re-upload |

**Portal note (79/140 chars):**
```
KANLER HVG blind-basin vent-gravity 37654d B2 | HOLDOUT-DTI 0.1427 n=60988 | 2858780e
```

**Why this file:** See Executive Summary — it is the only file in this repo that passes *all* of: (1) exact `[0,1]` + CRS/shape/transform validator, (2) leakage canary ≤0.90, (3) paired holdout win vs same-run control (+0.0094, 95% CI [+0.0012,+0.0176], 3/4 folds), (4) discrete-peer uniqueness (max 38.2% ≤70% vs 9 focus-site champions, max |Spearman| 0.31 ≤0.90), (5) 0 on-catalogue leakage (B=2). All 9 historical champions (0.2449–0.2778) are OWNER-REPORTED, already submitted, and fail literal novelty — re-uploading them spends a slot and teaches the review panel nothing new.

**“Predicted values must be in range [0,1]” — fixed:** This primary `…-zeros.tif` is whole-array finite (`nodata=None`, 0 outside) with every cell exactly `0.0` or `1.0` in `[0,1]`. The twin `…-nan.tif` uses `nan` outside but is *not* the portal file. Both pass `scripts/verify_downloads.py 13/13`.

---

## Prompt — Read Every Session (Verbatim User Brief)

> *Review the repo. Focus on the highest scoring submissions from GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33, GEMSDOE36. Produce an executive summary on every site that is clear and obvious which is the best submission to submit to obtain a high score on the leaderboard. It should be unique and not an exact duplicate. Keep iterating and testing until we have the highest scoring submission to download and submit. We should be able to estimate the score for a submission. Table must clearly list what file to download, what estimate score is, and whether unique. MUST GENERATE A UNIQUE TIF SUBMISSION — DO NOT COPY PREVIOUS SUBMISSION unless for learning. IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT. There should be an easy to download TIF as described. Read entire prompt. A lot of sites mention inspection only and human inspector, but inspection needs to be done through the project and validated for submission without human intervention. Parallel-run protocol: lane, reuse don't rebuild, label every number, leakage canary, run card, budget. The following sites are starting points ... Current leaderboard high score 0.4413 ... Reference links above ... No hallucinations ... Generate 3–5 candidate hypotheses ... Put this prompt into repo readme ... Own the Outcome ... Verify no hallucinations ... Site creation: GitHub page clean UI ... Must be able to do own research ... Blocker to training is data placement: bash scripts/download_competition_data.sh on unrestricted machine into data/, then python scripts/prepare_data.py — after that train→inference→validate ready (GPU needed for training; metric/losses/validation verified on CPU) ... 3 passes ... PR and merge ... etc.*

**Operational note (parallel-session disclosure):** No method lane was assigned in the prompt for this lane. We ran **HVG-BLIND-BASIN** as documented in `knowledge/preregistration-blindbasin.md`. The session respects the fail-closed gate, reuse-don't-rebuild, leakage-canary, and run-card protocols. Other parallel sessions' evidence-first audits are preserved under `docs/evidence/` (their TIFFs are not in `docs/downloads/` and are not authorized here).

---

## How the Project Works Without Manual Inspection

```
data/ (not committed)                      src/
  training_features.tif  ← from DrivenData    ├─ metric.py  → distance-weighted Tversky (α0.2/β0.8/R300 + 6px buffer)
  labels.tif                               ├─ holdout.py → hide-and-recover: withhold whole fault segments + buffer, visible-only features, mask visible faults pixel-exact, pooled DTI
  sample_submission.tif  ← CRS/shape/xform   ├─ features.py→ cached feature stack (35–59 channels, leakage-canary tested)
  1m_DEM_links.csv                         ├─ model.py   → U-Net / GBDT / physics-guided ensembles
                                             └─ submission_writer.py → single-band Float32, EPSG32611, 3730×3292, [0,1], zeros- and nan-twins

scripts/
  download_competition_data.sh  → curls Dropbox mirrors into data/ (requires unrestricted network; see Limitations)
  prepare_data.py               → builds footprint mask, catalogue distance, train patches
  train.py / infer.py           → GPU if available, CPU fallback for metric-only
  verify_downloads.py           → 13/13 gate check: single band, Float32, 3730×3292, EPSG32611, transform, [0,1], finite footprint, 0 on-catalogue, etc.; writes audit JSON
  select_submission.py          → fail-closed selector: no lane → no slot, no holdout win → negative, no uniqueness → duplicate
  audit_sources.py / build_site.py / promotion_gate.py → evidence-first helpers (preserved from parallel session; see docs/research.md)
```

**Automated inspection:** `verify_downloads.py` + `select_submission.py` implement the exact DrivenData validator logic locally (`Predicted values must be in range [0,1]`, CRS/shape/transform). No human geological inspector in loop — the project's *code* is the inspector, producing a JSON receipt that gates `OK TO SUBMIT`. Parallel-session `promotion_gate.py` is preserved but not gating our lane.

---

## Limitations & What We Need

- **No DrivenData auth in sandbox → cannot auto-pull `training_features.tif`/`labels.tif`/`sample_submission.tif`** (verified redirect to login). Mirrors exist on GDR + Dropbox (see links above); `scripts/download_competition_data.sh` documents them. Until data is in `data/`, training is blocked — but metric/validator can be exercised on CPU with synthetic footprints (this repo includes a pinned template and footprint mask from GEMSDOE32).
- **GPU needed for training** at full resolution; holdout/metrics verified on CPU.
- **1 m DEM links CSV** requires bulk download (3DEP). We use 100 m detrended elevation from `training_features.tif` as fallback plus external free sources (see Data Sources).

See `knowledge/03_limitations_and_external_data.md` for free, official sources and licenses. See also `docs/research.md` for the evidence-first limitations note.

---

## Quickstart for Next Session

1. `bash scripts/download_competition_data.sh` on any unrestricted host → `data/`
2. `python scripts/prepare_data.py` → validates footprint 5,167,373 px, catalogue distance, patches
3. `python src/train.py && python src/infer.py && python scripts/verify_downloads.py`
4. Open `docs/index.html` — green banner tells you whether upload is authorized.

Every session: read this README, then `docs/index.html` executive summary, then `evidence/run_card.json`.

---

## Repository Map

- `docs/` — GitHub Pages site (executive summary, downloads, how-to-submit, research)
  - `docs/index.html` — **our lane's executive summary + authorized green gate**
  - `docs/evidence/` — **parallel-session evidence-first audit snapshots** (preserved, not authorized)
- `evidence/` — run cards, audits, receipts (JSON, never hand-edited) for our lane
- `knowledge/` — deep research, hypotheses, limitations (MUST be line-by-line sourced)
- `scripts/` / `src/` — reproducible pipeline (our lane + preserved helpers)
- `data/` — `.gitignored`; holds competition rasters after manual download
- `.github/workflows/pages.yml` — deploys `docs/` to Pages on push to main

---

## License & Attribution

Code MIT; data under competition rules and source licenses. DOE GEMS Prize by DOE Office of Geothermal + National Lab of the Rockies (NLR). This repo is not affiliated with DOE/DrivenData; it is an independent competitor entry. Cite NLR Official Rules (Sept 2026) https://docs.nlr.gov/docs/fy26osti/96647.pdf.

---

## Parallel lane merged 2026-10-26 — E1 XG-HGB (this session, verdict: negative)
A separate lane (supervised 47-channel HistGradientBoosting incl. a magnetic×gravity cross-gradient boundary channel; spacing≥3 px dots, B=2 gate) was run under the same protocol and merged as a **negative deliverable** — it does **not** replace the authorized blind-basin primary above. Quadrant-OOF HOLDOUT-DTI 0.1252 [0.097,0.157] (56,464 withheld), canaries pass (max AUC 0.580), uniqueness pass (max |ρ| 0.089; max 3-px dot overlap 40.9% vs the 9 focus bests), format 11/11 PASS — **but SGMC off-catalogue HOLDOUT-DTI 0.0752 vs champion 0.0961**, SGMC-anchored MODEL ESTIMATE ~0.22 [0.19,0.26] < 0.2778. File: `docs/downloads/kanler-e1-xg-hgb-37654d-20261026T214616Z-7ab68c3efd-allfinite.tif` (research/experiment only — **DO NOT SUBMIT as an expected improvement**). Detail: `docs/lane-e1-xg-hgb.html`, `evidence/run_card_e1_xg_hgb.json`. Irregularities IR-01..IR-05 (lattice gate, LiDAR band order, no organizer receipts, prompt score inconsistency, band-6 label) are documented in that lane page.
