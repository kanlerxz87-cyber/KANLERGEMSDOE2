# KANLERGEMSDOE2 — DOE GEMS Prize (DrivenData #306)

**Read this file at the start of every session.** It is the project charter (the prompt that created this repo, condensed without changing its requirements), the current verified state, and the only place promotion decisions are recorded.

## Core Values
- **Maximize P(Win)** — every weekly submission slot is an experiment, not a lottery ticket; weigh tradeoffs and choose the path that maximizes the probability of winning.
- **Own the Outcome** — own results end to end; when a gate fails, publish the negative result rather than quietly dropping it.

## Charter / prompt (operative requirements, verbatim in substance)
1. Focus on the highest-scoring submissions from **GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36**. Produce an executive summary per site making obvious which is the best submission to submit for a high leaderboard score. It must be unique and not an exact duplicate of any previous submission.
2. We should be able to estimate the score for a submission. The executive summary must contain a table listing clearly: what file to download, what the estimated score is, and whether it is a unique submission unlike any other GEMSDOE site listed.
3. **HIGHEST URGENCY: MUST GENERATE A UNIQUE TIF SUBMISSION. DO NOT COPY A PREVIOUS SUBMISSION EXCEPT FOR LEARNING/EDUCATION. IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT THE GENERATED TIF.**
4. Inspection/validation must be automated through the project, without human intervention (no manual inspector).
5. PARALLEL-RUN PROTOCOL: (a) stay in one method lane — rank-correlation ≲0.90 and ≲70% of dots within 3 px of any one registry raster, checked on the surface before placement AND on final dots; drift = log as duplicate and stop. (b) Reuse the template's cached feature stack, `evaluate_holdout.py`, `submission_writer.py`; holdout = hide-and-recover (withhold whole fault segments with a buffer, catalogue features only from visible faults, visible faults masked pixel-exactly, pooled DTI α=0.2, β=0.8, 300 m triangular kernel); fix shared tools once, never keep a private fork. (c) Label every number **HOLDOUT-DTI** (evaluator version, withheld positives, 95% CI) or **ORGANIZER-CONFIRMED** (submission-page receipt); a projection is never written as a score. (d) Leakage canary: each feature alone on holdout, AUC >0.90 = leakage until proven otherwise. (e) Run card: one JSON with hypothesis, mechanism, named non-fault mimic, holdout DTI+CI, correlation/overlap vs registry, raster sha256, validator output, submission name + ≤140-char note, verdict promote/negative. Negative results are deliverables. (f) Budget: 3 experiments or 2 hours; promotion to a real slot is a separate selector step within the weekly cap.
6. Study the highest score from GEMSDOE32 (`h33-h33-2-b2…-zeros`, reported 0.2778): why/how did it score highest, can we generate higher? Answer with PhD-level judgement, then generate a unique TIF. Leaderboard top cited in the prompt: 0.4413 (and 0.3195 in an earlier paragraph of the same prompt — see IR-04).
7. Before implementing, generate 3–5 candidate geological hypotheses not yet tried here, each naming the layer(s), the physical signature/transform, why it should catch a fault missing from the USGS/INGENIOUS catalogue, and how it differs from anything in this repo; rank by expected DTI improvement and cost. Validate the top candidate on a spatially blocked holdout before touching a weekly slot. If a candidate needs new external data, name the specific free official source and check obtainability first.
8. Work line by line from official verified trusted sources, provide links for manual review, no manual input, flag irregularities, **no hallucinations**.
9. The site must make submission obvious: easy one-click download TIF at the top, unique name + short note (fixes the user's DrivenData error *"Predicted values must be in range [0, 1]"*), plus an executive-summary subpage explaining exactly how to submit.
10. Passes 1–3 (implement / bug-review / re-check), then PR → merge to main, with remaining work + limitations stated.

## 🚦 Current status (2026-10-26) — machine-gated, no human inspection
**Download: YES · Submit as an expected improvement over 0.2778: NO (verdict `negative`).**
New unique file: `docs/downloads/kanler-e1-xg-hgb-37654d-20261026T214616Z-7ab68c3efd-allfinite.tif`
(SHA-256 `8e35f810f2426f6e70e68f1075439352b363ba1059b40d6237ed306275f5b154`, 37,654 dots, validator 11/11 PASS).
It passes format, leakage-canary, surface+dot uniqueness, and catalogue holdout gates, but **fails the SGMC blind-fault gate vs the champion** (0.0752 vs 0.0961); SGMC-anchored **MODEL ESTIMATE ≈ 0.22 [0.19, 0.26]** (< 0.2778). Full reasoning, nine-site table, and one-click download: **[docs/index.html](docs/index.html)** (GitHub Pages: enable Pages → `/docs`) · [how to submit](docs/how-to-submit.html) · [run card](evidence/run_card.json).

## Nine focus sites — best file each (all OWNER-REPORTED, none ORGANIZER-CONFIRMED, all already submitted — do not resubmit)
| Site | Best file | Score | Dots |
|---|---|---:|---:|
| GEMSDOE32 | h33-h33-2-b2…-e5eb6e7e-zeros | **0.2778** | 37,654 |
| GEMSDOE36 | anderson-geothermal-pinn-38854…-9b9ea4e6-zeros | 0.2750 | 38,854 |
| GEMSDOE28 | h36-1-rung30-blind-r1…-b531dae0a36f | 0.2710 | 37,660 |
| GEMSDOE31 | h27-4-solo-d28…-8acb75e1 | 0.2708 | 40,199 |
| GEMSDOE33 | h33d-analog-tip-stepover-r30…-cb490425926e | 0.2632 | 41,865 |
| GEMSDOE25 | dotted-h19-5-d2-8…-e56ea318af89-zeros | 0.2600 | 44,090 |
| GEMSDOE30 | d28-poisson300m-offcat-44090…-91eae1ca | 0.2600 | 44,090 |
| GEMSDOE24 | h25-1-dotted-h19-5-d1-5…-989f59505db1 | 0.2477 | 60,069 |
| GEMSDOE27 | topo-gap-closure-t-v2-on-d1-5…-5512495c6bd1 | 0.2449 | 61,328 |

**Pattern (verified):** every best is the same H19-5 ridge surface; only dot spacing/pruning differs. D1.5 (~61k) < D2.8 (40–44k) < D2.8+B2-prune (37,654). Why 0.2778 won and why our different surface is *not* expected to beat it: see docs/index.html §"Why did 0.2778 win".

## Experiments run here (budget exhausted: 3/3)
| Exp | Lane | HOLDOUT-DTI | Verdict |
|---|---|---|---|
| E1 XG-HGB | 47-ch supervised HGB incl. mag×grav cross-gradient boundary, LiDAR dipole (correct band indices); spacing≥3 px dots, B=2 gate | Quadrant OOF **0.1252** [0.097,0.157] (56,464 withheld); template hide-recover 0.0251 [0.023,0.027] vs champion 0.0045 same evaluator (22,232 withheld); SGMC raw 0.0752 [0.065,0.089] vs champion 0.0961 (62,703) | Best of 3, but SGMC gate fail → **negative** |
| E2 XG-UNSUP | Cross-gradient surface alone | OOF 0.0748; hide-recover 0.0052 | Negative |
| E3 SPRING-BLEND | E1 × GDR hot-spring heat density (12,570 spring px) | hide-recover 0.0244; SGMC 0.0739 | Negative vs E1 |

Leakage canaries: max single-feature |AUC| = **0.580** (lid_dipole) ≤ 0.90 PASS (`evidence/canaries.json`).
Uniqueness (E1): surface max |Spearman| **0.089** ≤ 0.90; final-dot 3-px overlap max **40.9%** ≤ 70% (31.7% vs champion) vs the 9 sha-verified registry bests (`evidence/uniqueness_E1.json`).

## Hypotheses ranked (next work — none may spend a slot without beating the holdout best)
1. Sub-km seismicity lineaments — USGS ANSS ComCat FDSN (https://earthquake.usgs.gov/fdsnws/event/1/), free/official, **not obtainable from this sandbox** (egress limited to github/pypi; curl returned nothing 2026-10-26). Highest expected gain, blocked.
2. Tilt-depth shallow-source persistence (RTP tilt zero-crossings, depth<basement) — data on disk, medium cost, upstream variants weak.
3. Euler depth clusters — upstream live 0.03–0.10; low gain.
4–5. Th/K lineaments alone; DEM-free subsurface HGB — both already negative in sibling repos; do not repeat.

## Reproduce
```bash
python3 -m venv /tmp/venv && /tmp/venv/bin/pip install numpy scipy rasterio scikit-learn
# data/ is gitignored: restore sha-pinned mirrors (training_features sha256 4371c82e… from buffedlizard55-lab/GEMSDOE parts; labels/sample/external from GEMSDOE24 — see registry/data_manifest in GEMSDOE32)
/tmp/venv/bin/python scripts/build_features.py      # .cache/feature_stack.npy (47 ch)
/tmp/venv/bin/python scripts/run_experiments.py     # canaries + OOF + final dots
/tmp/venv/bin/python scripts/evaluate_holdout.py .cache/dots_E1.npy .cache/dots_E2.npy .cache/dots_E3.npy data/registry/g32_champion.tif --out evidence/holdout_template.json
/tmp/venv/bin/python scripts/audit_uniqueness.py --surface .cache/score_e1.npy --dots .cache/dots_E1.npy --out evidence/uniqueness_E1.json
/tmp/venv/bin/python scripts/submission_writer.py --mask .cache/dots_E1.npy --slug e1-xg-hgb-37654d --note "…≤140 chars…"
/tmp/venv/bin/python scripts/build_site.py
```
Template reuse: `src/gems/metric.py` + `holdout.py` are vendored verbatim from GEMSDOE32 (this repo started empty — see `src/gems/PROVENANCE.md`); `scripts/evaluate_holdout.py`/`submission_writer.py` delegate to them / implement their 11–13 checks. No private evaluator fork.

## Irregularities flagged (review, do not silently fix history)
- **IR-01 Lattice gate:** a spacing-5 calibration lattice makes *any* dense dot map >70% within-3-px by geometry (max distance to lattice = 3.54 px). Registry here = 9 genuine scored bests only; lattice probes excluded and disclosed (upstream IR-42-UNIQ-01 concurs).
- **IR-02 LiDAR band order:** file GDAL descriptions are (ex_max, ex_mean, step_max, lapneg, lappos, downface, upface, cross, relief, coh100, strike, valid); several upstream scripts assumed different indices (e.g. band 5 = coherence). We index from descriptions.
- **IR-03 No organizer receipts:** all 9 historical scores are OWNER-REPORTED; no DrivenData receipt binds sha256→score in any audited repo. Our file's 0.22 is a MODEL ESTIMATE, never a score.
- **IR-04 Prompt inconsistency:** the creating prompt cites both 0.3195 and 0.4413 as "current leaderboard top" in different paragraphs; neither re-verified here (leaderboard requires login from this sandbox).
- **IR-05 Band 6 label:** `training_features.tif` describes band 6 as tilt/total-curvature; upstream byte-correlation (IR-32-REDUND-01) identifies it as radiometric total count. We use it only as a raw channel, never as a tilt transform.

## Limitations / what is still needed
- No DrivenData auth → cannot download organizer data directly or obtain ORGANIZER-CONFIRMED scores; mirrors are owner-supplied, sha-pinned, not organizer-authenticated (419 MB `training_features.tif` restored here and hash-verified, but that verifies bytes, not provenance).
- No GPU needed/used (HGB is CPU); ComCat seismicity (hypothesis 1) unreachable from this sandbox — fetch on an unrestricted machine and drop into `data/external/` with sha256 logged.
- GitHub Pages must be enabled (Settings → Pages → `/docs`) for the site/download links to go live; files are ready in `docs/`.
- SGMC is an imperfect blind proxy (pre-Quaternary geologic-map faults ≠ hidden INGENIOUS population); a promoted candidate ultimately needs either a better blind validation set or a selector-approved experimental slot.

## Sources (manual review)
DrivenData #306 [overview/problem/metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) · [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) · [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) · [NLR rules PDF 96647](https://docs.nlr.gov/docs/fy26osti/96647.pdf) · [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · [INGENIOUS](https://gbcge.org/current-projects/ingenious/) · [GDR 1391](https://gdr.openei.org/submissions/1391) · [EPSG:32611](https://epsg.io/32611) · [Tversky index](https://en.wikipedia.org/wiki/Tversky_index) · focus sites: GEMSDOE[24](https://buffedlizard55-lab.github.io/GEMSDOE24/), [25](https://buffedlizard55-lab.github.io/GEMSDOE25/), [27](https://buffedlizard55-lab.github.io/GEMSDOE27/), [28](https://buffedlizard55-lab.github.io/GEMSDOE28/), [30](https://buffedlizard55-lab.github.io/GEMSDOE30/), [31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/), [32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html), [33](https://buffedlizard55-lab.github.io/GEMSDOE33/), [36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/)
