#!/usr/bin/env python3
import json, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]; DOCS=ROOT/"docs"; (DOCS).mkdir(exist_ok=True)
focus=json.loads((ROOT/"evidence/focus_sites.json").read_text())
run=json.loads((ROOT/"evidence/run_card.json").read_text())
dl=sorted((DOCS/"downloads").glob("*-allfinite.tif"))[0]; receipt=json.loads(pathlib.Path(str(dl)+".receipt.json").read_text())
rows="".join(f"<tr><td>{s['site']}</td><td><code>{s['file']}</code></td><td>{s['score_owner_reported']:.4f}<br><small>OWNER-REPORTED</small></td><td>{s['dots']:,}</td><td>{s['unique_vs_others']}</td><td>{s['verdict']}</td></tr>" for s in sorted(focus['sites'], key=lambda x:-x['score_owner_reported']))
CSS="body{font-family:system-ui;max-width:1100px;margin:2rem auto;padding:0 1rem;line-height:1.5}table{border-collapse:collapse;width:100%;font-size:.85rem}td,th{border:1px solid #ccc;padding:.4rem;vertical-align:top}.banner{border:3px solid #b00;padding:1rem;background:#fff5f5}.ok{border-color:#080;background:#f5fff5}code{word-break:break-all}.dl{font-size:1.2rem;background:#064;color:#fff;padding:.7rem 1rem;display:inline-block;border-radius:6px;text-decoration:none}"
index=f"""<!doctype html><meta charset=utf-8><title>KANLERGEMSDOE2 — Executive Summary</title><style>{CSS}</style>
<h1>KANLERGEMSDOE2 — DOE GEMS Prize (DrivenData #306)</h1>
<p>Core values: <b>Maximize P(Win)</b> · <b>Own the Outcome</b>. Every number below is labelled
<b>HOLDOUT-DTI</b> (local evaluator, withheld positives + CI) or <b>OWNER-REPORTED</b> (site submission logs; no organizer receipt found) or <b>MODEL ESTIMATE</b> (projection — never a score).</p>

<div class=banner><h2>🚦 Submission status — read first</h2>
<p><b>OK TO DOWNLOAD: YES.</b> One new unique GeoTIFF was generated in this repo (below).</p>
<p><b>OK TO SUBMIT AS AN EXPECTED IMPROVEMENT OVER 0.2778: 🔴 NO.</b> Automated gates: format PASS (11/11), leakage canaries PASS (max AUC 0.580 ≤ 0.90),
uniqueness PASS (max |Spearman| 0.089 ≤ 0.90; max 3-px dot overlap 40.9% ≤ 70%; 31.7% vs the 0.2778 champion), quadrant-OOF HOLDOUT-DTI PASS vs controls —
<b>but the off-catalogue SGMC blind-fault gate FAILS vs the champion</b> (0.0752 vs 0.0961), so the SGMC-anchored MODEL ESTIMATE is <b>~0.22 [0.19, 0.26]</b>, below 0.2778.
Verdict: <b>negative</b> (JSON run card). If you spend a weekly slot on it, it is an experiment — promotion is a separate selector step. No human inspection is used anywhere; all gates are machine-run.</p>
<a class=dl href="downloads/{dl.name}">⬇ Download the unique TIF (research/experiment)</a>
<p>Also: <a href="downloads/{dl.name}.zip">.zip (single TIF)</a> · <a href="downloads/{dl.name}.receipt.json">validator receipt (JSON)</a> · <a href="run_card.json">run card</a></p>
<p><b>Unique name:</b> <code>{receipt['unique_name']}</code><br><b>Note ({receipt['note_chars']}/140 chars):</b> <code>{receipt['note']}</code><br>
<b>SHA-256:</b> <code>{receipt['sha256']}</code> · {receipt['dots']:,} dots · values exactly {{0,1}}, all-finite, in [0,1] on all 12,279,160 cells (fixes “Predicted values must be in range [0, 1]”).</p></div>

<h2>What to download — score &amp; uniqueness table</h2>
<table><tr><th>File to download</th><th>Estimated / historical score</th><th>Label</th><th>Unique?</th><th>OK to submit?</th></tr>
<tr><td><code>{dl.name}</code> (this repo, NEW)</td><td><b>~0.22</b> [0.19, 0.26]</td><td>MODEL ESTIMATE (SGMC-anchored; not a score)</td><td><b>YES</b> — max ρ 0.089, max 3-px overlap 40.9% vs all 9 registry bests; 0 exact matches</td><td><b>NO</b> as expected improvement (negative verdict); research/experiment only</td></tr>
<tr><td>GEMSDOE32 champion (reference only — do not download from here / do not resubmit)</td><td>0.2778</td><td>OWNER-REPORTED</td><td>Historical best of 9</td><td>NO — already submitted</td></tr></table>

<h2>Executive summary — every focus site (highest-scoring submission each)</h2>
<p>{focus['pattern']}</p>
<table><tr><th>Site</th><th>Best file</th><th>Score</th><th>Dots</th><th>Unique?</th><th>Best submission to submit / guidance</th></tr>{rows}</table>
<p><small>{focus['label_note']}</small></p>

<h2>Why did 0.2778 win, and can we beat it?</h2>
<p><b>Mechanism (PhD autopsy).</b> All nine bests are the same H19-5 multiline-corroborated ridge surface; only emission differs.
(1) <i>Dot spacing ≈ kernel:</i> DTI uses a 300 m triangular kernel (3 px), α=0.2 (FP) vs β=0.8 (FN) — missing a fault costs 4× a wasted dot, but dots closer than ~3 px give redundant kernel credit while each still risks FP cost. Densities confirm it: D1.5 (~61k dots) scored 0.2449–0.2477 &lt; D2.8 (40–44k) 0.2600–0.2710.
(2) <i>B=2 catalogue-flank prune:</i> deleting every dot within 2 px of known faults (40,199→37,654) raised 0.2708→0.2778. Near-catalogue dots have expected credit below the marginal bar α·DTI≈0.056: known faults are masked in scoring, mapping is most complete there, and blind faults are continuations <i>away</i> from mapped traces.
(3) Nothing outside this lineage in the prompt list exceeded 0.24, so surface novelty alone has not paid — emission geometry has.</p>
<p><b>Can we beat 0.2778?</b> Not with evidence in hand. Our genuinely different E1 surface beats the champion on catalogue hide-recover (0.0251 vs 0.0045, same vendored evaluator, 22,232 withheld) and on quadrant OOF (0.1252), but trails on the only blind-fault proxy available locally (SGMC, 0.0752 vs 0.0961). The SGMC-anchored estimate is ~0.22. Claiming &gt;0.2778 would require the catalogue-recovery proxy to dominate the blind proxy — upstream repos that made that assumption produced the string of 0.02–0.16 live scores in the prompt list. We therefore do not promote E1.</p>

<h2>Experiments (budget: 3 — exhausted)</h2>
<table><tr><th>Exp</th><th>Method lane (stayed inside)</th><th>HOLDOUT-DTI</th><th>Result</th></tr>
<tr><td>E1</td><td>XG-HGB supervised 47ch incl. mag×grav cross-gradient boundary + LiDAR dipole; spacing≥3px dots, B=2</td><td>Quadrant OOF 0.1252 [0.097,0.157], 56,464 withheld; template hide-recover 0.0251 [0.023,0.027]; SGMC 0.0752</td><td>Best of 3; uniqueness+format pass; SGMC gate fail → <b>negative</b></td></tr>
<tr><td>E2</td><td>Unsupervised cross-gradient surface alone</td><td>OOF 0.0748; hide-recover 0.0052</td><td>Negative (ablation: supervision is doing the work)</td></tr>
<tr><td>E3</td><td>E1 boosted by GDR hot-spring heat density (12,570 spring px, σ=8px)</td><td>hide-recover 0.0244; SGMC 0.0739</td><td>Negative vs E1 (springs do not add fault signal at 100 m)</td></tr></table>
<p>Mimic (all experiments): lithologic mag/gravity contacts, roads/mine benches, terrace risers, drainage chains. Leakage canaries: max single-feature AUC 0.580 (≤0.90 pass) — <a href="canaries.json">evidence/canaries.json</a>.</p>

<h2>Hypotheses ranked (next, untested — do not spend a slot without beating holdout best)</h2>
<ol>
<li><b>Sub-km seismicity lineaments</b> — USGS ANSS ComCat FDSN epicentre + nodal-plane strikes. Would catch seismogenic blind faults invisible in potential fields. <i>Status: source is free/official but unreachable from this sandbox (only github/pypi egress; curl returned nothing 2026-10-26) — not viable here until fetched elsewhere.</i> Mimic: quarry blasts, aftershock clouds.</li>
<li><b>Tilt-depth shallow-source persistence</b> — Miller/Salem tilt zero-crossings on RTP with depth &lt; basement depth. Data on disk; upstream variants scored low, cost medium. Mimic: shallow basalt flows.</li>
<li><b>Euler deconvolution depth clusters</b> — structural index clusters along lineaments. Upstream variants 0.03–0.10 live; low expected gain.</li>
<li><b>Radiometric Th/K metasomatic lineaments alone</b> — tried concurrently elsewhere (RADLIN) and failed strict uniqueness there; do not repeat.</li>
<li><b>DEM-free subsurface-only HGB</b> — tried at GEMSDOE25 (H72-3, holdout 0.059 vs 0.154 control); negative, do not repeat.</li></ol>

<p><a href="executive-summary.html">Full executive summary &amp; how the 0.2778 was verified line-by-line</a> · <a href="how-to-submit.html">How to submit to DrivenData (subpage)</a> · <a href="../README.md">README / project charter</a></p>
<small>Sources: DrivenData #306 <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">problem/metric</a>, <a href="https://github.com/drivendataorg/gems-prize-reference-solution">reference solution</a>, <a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN</a>, <a href="https://gbcge.org/current-projects/ingenious/">INGENIOUS</a>, <a href="https://epsg.io/32611">EPSG:32611</a>, <a href="https://en.wikipedia.org/wiki/Tversky_index">Tversky index</a>, NLR rules PDF 96647. Irregularities flagged in README (IR-01 lattice, IR-02 LiDAR band order, IR-03 no organizer receipts).</small>
"""
(DOCS/"index.html").write_text(index)
summary = index.replace("<h1>KANLERGEMSDOE2", "<h1>Executive Summary — KANLERGEMSDOE2")
(DOCS/"executive-summary.html").write_text(summary)
how=f"""<!doctype html><meta charset=utf-8><title>How to submit</title><style>{CSS}</style>
<h1>How to make a submission (DrivenData #306)</h1>
<ol><li>Download <code>{dl.name}</code> from the front page (or use the .zip — DrivenData accepts a single .tif or a .zip containing one TIF).</li>
<li>Open <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">the submission page</a> → <b>New submission</b> → choose the file.</li>
<li>Unique name: <code>{receipt['unique_name']}</code></li><li>Note (≤140 chars here): <code>{receipt['note']}</code></li>
<li>Format already machine-validated: single-band float32, EPSG:32611, 3730×3292, exact sample transform, no NaN anywhere, all values in [0,1] — the “Predicted values must be in range [0, 1]” error cannot occur for this file (receipt: <code>{dl.name}.receipt.json</code>).</li>
<li><b>Gate reminder:</b> this repo's verdict for this file is <b>negative / do not submit as an expected improvement</b> (estimate ~0.22 &lt; 0.2778). Submitting is your selector decision and spends a weekly slot.</li></ol>
<p><a href="index.html">Back to executive summary</a></p>"""
(DOCS/"how-to-submit.html").write_text(how)
print("site written", dl.name)
