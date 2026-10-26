#!/usr/bin/env python3
"""Build the static GitHub Pages site from committed evidence only (CI-safe,
deterministic: no wall-clock, no data/ reads). Run cards are owned by
scripts/finalize_ext.py; this builder only renders/copies them.
Pages: index (decision desk), executive-summary, how-to-submit,
lane-ext-corrob, lane-e1-xg-hgb, submission (legacy redirect).
"""
import html, json, pathlib, shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS, EV, RES = ROOT / "docs", ROOT / "evidence", ROOT / "research"
DATE = "26 October 2026 UTC"

def page(title, content):
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{html.escape(title)} · KANLERGEMS</title><link rel="stylesheet" href="style.css"></head>'
            f'<body><main>{content}</main><footer>KANLERGEMS · Maximize P(Win) through reproducible '
            'evidence. Own the outcome, including negative results. · Snapshot ' + DATE + ' — not a live feed.</footer></body></html>\n')

def f4(x): return f"{x:.4f}"
def ci(c): return f"[{c[0]:.4f}, {c[1]:.4f}]"

def build():
    card = json.loads((EV / "run_card_ext.json").read_text())
    exp = json.loads((EV / "experiments_ext.json").read_text())
    focus = json.loads((EV / "focus_sites.json").read_text())
    fore = json.loads((EV / "champion_forensics.json").read_text())
    lb = json.loads((EV / "leaderboard_snapshot_20261026.json").read_text())
    uniq_ind = json.loads((EV / "uniqueness_EXT_independent.json").read_text())
    base = json.loads((EV / "baselines_visible_gated.json").read_text())
    receipt = card["validator_output"]; tif = receipt["file"]
    est = card["estimated_live_score"]; est_v = est["headline_anchorA_catalogueOOF_via_E1"]["value"]
    oof = card["holdout_dti"]["primary_oof"]; u = card["correlation_overlap_vs_registry"]
    sgoof = card["holdout_dti"]["sgmc_oof_foldlocal"]
    nav = ('<p><a href="index.html">Decision desk</a> · <a href="executive-summary.html">Executive summary</a> · '
           '<a href="how-to-submit.html">How to submit</a> · <a href="lane-ext-corrob.html">Lane EXT (this session)</a> · '
           '<a href="lane-e1-xg-hgb.html">Lane E1 (prior)</a></p>')

    banner = f'''<section class="alert"><span class="eyebrow">SUBMISSION STATUS — READ FIRST · {DATE}</span>
<h2>OK TO DOWNLOAD: YES. &nbsp; OK TO SUBMIT AS AN EXPECTED IMPROVEMENT OVER 0.2778: <span class="bad">NO</span>.</h2>
<p>One NEW, unique GeoTIFF was generated this session and is safe to download for research. Automated gates
(no human inspection anywhere): format PASS ({sum(receipt["checks"].values())}/{len(receipt["checks"])} checks, all 12,279,160 cells finite in [0,1] —
the “Predicted values must be in range [0, 1]” error cannot occur), leakage canary PASS
(max single-feature AUC {card["leakage_canary"]["max_single_feature_abs_AUC"]:.3f} ≤ 0.90), uniqueness PASS
(max |Spearman| {u["max_abs_surface_spearman"]:.3f} ≤ 0.90; max 3-px dot overlap {u["max_dot_overlap_3px_frac"]:.1%} ≤ 70%;
{u["vs_champion_dot_overlap_3px"]:.1%} vs the 0.2778 champion) — <b>but holdout superiority FAILS</b>:
catalogue OOF HOLDOUT-DTI {f4(oof["value"])} {ci(oof["ci95"])} ties the frozen best (E1 {f4(oof["E1_same_evaluator"])}),
so the headline MODEL ESTIMATE is <b>~{est_v:.2f} [{est["headline_range"][0]:.2f}, {est["headline_range"][1]:.2f}]</b>, below 0.2778.
Verdict: <b>negative</b>. Spend zero weekly slots today; promotion is a separate selector step on the authenticated page.</p>
<a class="button" href="downloads/{tif}" download>⬇ Download the unique TIF (research / experiment only)</a>
<a class="button secondary" href="downloads/{tif[:-4]}.zip">.zip (single TIF)</a>
<a class="button secondary" href="run_card.json" download>JSON run card</a>
<p class="mono">File: {tif}<br>Unique name: {receipt["unique_name"]} · Note ({len(card["submission_note"])}/140): “{html.escape(card["submission_note"])}”<br>
SHA-256: {receipt["sha256"]} · {receipt["dots"]:,} dots · single-band float32 · EPSG:32611 · 3730×3292 · 0 outside footprint · 0 on catalogue</p></section>'''

    dl_rows = f'''<tr><td><code>{tif}</code> (this repo, NEW)</td><td><b>~{est_v:.2f}</b> [{est["headline_range"][0]:.2f}, {est["headline_range"][1]:.2f}]</td>
<td>MODEL ESTIMATE (never a score)</td><td><b>YES</b> — max ρ {u["max_abs_surface_spearman"]:.3f}, max overlap {u["max_dot_overlap_3px_frac"]:.1%} vs 10 registry rasters; independent rerun max ρ {uniq_ind["max_abs_surface_spearman"]:.3f}</td>
<td><b class="bad">NO</b> as expected improvement (negative verdict)</td></tr>
<tr><td>E1 XG-HGB TIF (prior lane this repo, quarantined in git only)</td><td>~0.22 [0.19, 0.26]</td><td>MODEL ESTIMATE</td>
<td>YES (max ρ 0.089, overlap ≤40.9%)</td><td><b class="bad">NO</b> (negative verdict, SGMC gate failed)</td></tr>
<tr><td>GEMSDOE32 champion (reference — education only, do not resubmit)</td><td>0.2778</td><td>OWNER-REPORTED (no organizer receipt)</td>
<td>Best of the nine; subset-nested family</td><td><b class="bad">NO</b> — already submitted; copying fails the duplicate gate</td></tr>'''

    site_rows, site_cards = [], []
    fkey = {"GEMSDOE24": "g24_best", "GEMSDOE25": "g25_best", "GEMSDOE27": "g27_best", "GEMSDOE28": "g28_best",
            "GEMSDOE30": "g30_best", "GEMSDOE31": "g31_best", "GEMSDOE32": "g32_champion", "GEMSDOE33": "g33_best", "GEMSDOE36": "g36_best"}
    for s in sorted(focus["sites"], key=lambda x: -x["score_owner_reported"]):
        fr = fore["files"][fkey[s["site"]]]
        site_rows.append(f'<tr><th><a href="#{s["site"]}">{s["site"]}</a></th><td>{s["score_owner_reported"]:.4f}<small>OWNER-REPORTED</small></td>'
                         f'<td><code>{html.escape(s["file"])}</code><small>{s["dots"]:,} dots · sha {s["sha256_prefix"]}…</small></td>'
                         f'<td>{html.escape(s["unique_vs_others"])}</td><td>{html.escape(s["verdict"])}</td></tr>')
        site_cards.append(f'<article id="{s["site"]}"><h3>{s["site"]} — {s["score_owner_reported"]:.4f} OWNER-REPORTED</h3>'
            f'<p>Best file: <code>{html.escape(s["file"])}</code> ({s["dots"]:,} dots). RASTER-AUDIT (decoded here): '
            f'{fr["frac_d_le2"]:.1%} of dots within 2 px of catalogue; median nearest-neighbour spacing {fr["nn_spacing_px"]["median"]:.2f} px; '
            f'kernel redundancy {fr["kernel_redundancy_fraction"]:.1%}.</p><p><b>Unique?</b> {html.escape(s["unique_vs_others"])}</p>'
            f'<p><b>Decision:</b> {html.escape(s["verdict"])} <a href="{s["url"]}">Site ↗</a></p></article>')

    lb_rows = "".join(f'<tr><td>#{t["rank"]}</td><td>{html.escape(t["team"])}</td><td>{t["public_dti"]:.4f}</td><td>{t["submissions"]}</td></tr>' for t in lb["top"][:5])
    names = {"EXP1_CORROB": "CORROB (label-free corroboration)", "EXP2_MCSUP": "MCSUP @37,654", "EXP3_EMIT": "EMIT = MCSUP @44,090 (shipped file)"}
    exp_rows = ""
    for k in ["EXP1_CORROB", "EXP2_MCSUP", "EXP3_EMIT"]:
        v = exp[k]; o = v["oof"]
        exp_rows += (f'<tr><td>{names[k]}</td><td>{f4(o["pooled_dti"])} {ci(o["ci95_foldbootstrap"])}<small>{o["n_withheld_positives"]:,} withheld catalogue px</small></td>'
                     f'<td>{f4(o["sgmc_oof_pooled_dti"])} {ci(o["sgmc_oof_ci95"])}<small>{o["sgmc_oof_n"]:,} withheld SGMC px</small></td>'
                     f'<td>{v["dots"]:,}</td><td>ρ {v["uniqueness"]["max_abs_surface_spearman"]:.3f} / ov {v["uniqueness"]["max_dot_overlap_3px"]:.1%}</td></tr>')

    autopsy = f'''<section><h2>Why did 0.2778 win? — byte-level autopsy (verified this session)</h2>
<p><b>1. It is an emission optimum, not a new detection.</b> Decoded pixels prove exact nesting: the champion's {fore["files"]["g32_champion"]["dots"]:,}
dots are a 100% subset of GEMSDOE31's best (40,199), itself a subset of the D2.8 raster (44,090; GEMSDOE25 ≡ GEMSDOE30 pixel-identical).
GEMSDOE36 (0.2750) is the champion plus 1,200 dots. One H19-5 ridge surface; only dot placement differs.</p>
<p><b>2. Spacing ≈ kernel radius.</b> DTI credits each hidden fault pixel by the <i>maximum</i> kernel-weighted prediction within 300 m (3 px),
with α=0.2 (FP) vs β=0.8 (FN). Dots closer than ~3 px duplicate credit while each still risks FP cost. Median NN spacing measures
2.24 px on the D1.5 files (0.2449–0.2477 at ~61k dots) vs 3.0 px on D2.8 (0.2600–0.2710 at 40–44k).</p>
<p><b>3. B=2 catalogue-flank prune.</b> DrivenData staff confirm known-fault pixels are masked/excluded from scoring
(<a href="https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516">community post 11516, chrisk-dd</a>).
Dots 1–2 px off a known fault are still scored and almost surely FP (expected credit below the DTI marginal bar α·DTI ≈ 0.056 at 0.2778).
Measured near-catalogue dot share tracks the ladder exactly: 14.6% (0.2600) → 6.3% (0.2708) → 0.0% (0.2778; 2,545 dots deleted).</p>
<p><b>4. Holdout trap warning.</b> Scoring those FIXED masks on withheld catalogue segments anti-ranks the live ladder
({f4(base["g25_best.tif"]["dti"])} &gt; {f4(base["g31_best.tif"]["dti"])} &gt; {f4(base["g32_champion.tif"]["dti"])}, HOLDOUT-DTI v3, 22,232 withheld):
B-gated masks cannot hit segments they were gated away from. Any lane tuning final masks on that evaluator will un-learn B-pruning.
All gating here therefore uses fold-local emission.</p>
<p><b>Can we beat 0.2778 — and the board?</b> The public leaderboard read on {DATE} is led by {lb["top"][0]["public_dti"]:.4f}
(the prompt's 0.4413 and 0.3195 are older snapshots of a moving board; Initial Round prizes use a private set, Final Round an
expert-expanded set — <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">problem page</a>).
No evidence in this repo supports a &gt;0.2778 claim for a unique file: every independent lane tried here or upstream splits
(catalogue recovery vs blind-fault proxies disagree). Claiming otherwise would be fabrication; the honest deliverable is the
unique file + negative verdict + the ranked research queue below.</p></section>'''

    index = f'''<header><span class="eyebrow">KANLERGEMS · DOE GEMS PRIZE (DrivenData #306) · EVIDENCE FIRST</span>
<h1>Submission decision desk</h1><p class="lead">Nine focus sites autopsied byte-by-byte. One new unique TIF. One clear answer.</p>{nav}</header>
{banner}
<section><h2>What to download — estimate &amp; uniqueness table</h2><p>Every number is labelled:
<b>HOLDOUT-DTI</b> (local evaluator + withheld count + CI), <b>OWNER-REPORTED</b> (site logs; no organizer receipt found anywhere),
<b>MODEL ESTIMATE</b> (projection, never a score), or <b>ORGANIZER-PUBLISHED</b> (leaderboard read {DATE}).</p>
<div class="scroll"><table><thead><tr><th>File</th><th>Estimated / historical score</th><th>Label</th><th>Unique vs other sites?</th><th>OK to submit?</th></tr></thead><tbody>{dl_rows}</tbody></table></div></section>
<section><h2>Experiments this session (budget 3/3 — stopped per protocol)</h2>
<div class="scroll"><table><thead><tr><th>Experiment (lane KANLER-EXT-CORROB)</th><th>Catalogue OOF HOLDOUT-DTI</th><th>SGMC OOF HOLDOUT-DTI (fold-local)</th><th>Dots</th><th>Uniqueness</th></tr></thead><tbody>{exp_rows}</tbody></table></div>
<p>E1 (prior lane, same OOF evaluator): {f4(oof["E1_same_evaluator"])} {ci(oof["E1_ci95"])}. Champion SGMC (full mask, clean for champion):
{f4(base["g32_champion.tif"]["sgmc_off_catalogue"]["raw_pooled_dti"])}; CORROB clean SGMC {f4(exp["EXP1_CORROB"]["sgmc_paired_vs_champion"]["candidate_sgmc_raw"])}
(paired diff CI crosses zero). MCSUP's global-model SGMC/hide-recover numbers are training-contaminated (IR-EXT-01) and excluded — see lane page.
Non-fault mimic (all): {html.escape(card["named_non_fault_mimic"])} <a href="lane-ext-corrob.html">Full lane evidence →</a></p></section>
{autopsy}
<section><h2>Executive table — highest-scoring submission per focus site</h2><p>{html.escape(focus["pattern"])}</p>
<div class="scroll"><table><thead><tr><th>Site</th><th>Score</th><th>Best file</th><th>Unique?</th><th>Best submission to submit / guidance</th></tr></thead><tbody>{''.join(site_rows)}</tbody></table></div>
<p><small>{html.escape(focus["label_note"])}</small></p></section>
<section><h2>Site-by-site decisions</h2><div class="cards">{''.join(site_cards)}</div></section>
<section><h2>Leaderboard reality check (ORGANIZER-PUBLISHED, {DATE})</h2>
<div class="scroll"><table><thead><tr><th>Rank</th><th>Team</th><th>Public DTI</th><th>Submissions</th></tr></thead><tbody>{lb_rows}</tbody></table></div>
<p>{html.escape(lb["reconciliation"])} <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Live leaderboard ↗</a></p></section>
<section><h2>Ranked next hypotheses (untested — no slot without beating holdout best)</h2><ol>
<li><b>Full-footprint deep segmentation</b> (U-Net/SegFormer on 47–53 ch, Tversky loss, GPU): upstream roadmap H38-G4; fixes reference-solution tile-skip blind spots. Highest expected gain, needs GPU session.</li>
<li><b>Seismicity lineaments</b> — USGS ANSS ComCat FDSN (free, official: earthquake.usgs.gov/fdsnws) collinearity + focal strikes. Blocked from sandbox bash (verified empty response {DATE}); fetch on unrestricted machine first.</li>
<li><b>Radiometric texture displacement</b> across LiDAR scarps (patch registration, GeoDAWN K/Th/U): data local but uint8-quantised; medium/high cost.</li>
<li><b>Drainage-offset geodesy</b> from raw 3DEP DEM flow routing (usgs.gov/3d-elevation-program): raw tiles not local; blocked egress.</li></ol>
<p>Pre-registration + full hypothesis table: <code>research/preregistration-ext-corrob.md</code> in the repo.</p></section>
<section><h2>Sources (official first)</h2><ul>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Problem, metric, prize structure</a> · <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Leaderboard</a> · <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/data/">Data (login)</a> (all read {DATE})</li>
<li><a href="https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516">Staff: known faults masked in scoring</a> · <a href="https://github.com/drivendataorg/gems-prize-reference-solution">Reference solution</a> · <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">NLR rules PDF 96647</a></li>
<li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN (DOI 10.5066/P93LGLVQ)</a> · <a href="https://gdr.openei.org/submissions/1391">GDR 1391 INGENIOUS (CC BY 4.0)</a> · <a href="https://gbcge.org/current-projects/ingenious/">INGENIOUS</a> · <a href="https://epsg.io/32611">EPSG:32611</a> · <a href="https://en.wikipedia.org/wiki/Tversky_index">Tversky index</a></li>
<li>Mirror integrity: every restored competition raster sha256-verified against pinned manifests (<code>scripts/restore_labels_sample.py</code>); mirrors are NOT organizer-authenticated. Irregularities IR-EXT-01…06 are in the JSON run card.</li></ul></section>'''
    (DOCS / "index.html").write_text(page("Executive summary", index))
    (DOCS / "executive-summary.html").write_text(page("Executive summary (full)", index.replace("<h1>Submission decision desk</h1>", "<h1>Executive summary</h1>")))

    how = f'''<header><span class="eyebrow">KANLERGEMS · HOW TO SUBMIT</span><h1>How to make a submission (DrivenData #306)</h1>{nav}</header>
<section class="alert"><h2>Gate reminder first</h2><p>This repo's verdict for the current file is <b>negative — do not submit as an expected improvement</b>
(MODEL ESTIMATE ~{est_v:.2f} &lt; 0.2778). The steps below are exact for when a future file passes all gates
(<code>scripts/promotion_gate.py</code> + separate selector + weekly-cap check). Spending a slot is always the selector's decision; this project never auto-submits.</p></section>
<section><h2>Steps</h2><ol>
<li>Download the approved file from the <a href="index.html">decision desk</a> (current research file: <code>{tif}</code>, SHA-256 <code>{receipt["sha256"]}</code>). A .zip containing that single TIF is also accepted by the portal.</li>
<li>Verify locally (optional, automated): <code>python scripts/validate_raster.py {tif} data/sample_submission.tif</code> — single-band float32, EPSG:32611, 3730×3292, exact sample transform, every cell finite in [0,1], nodata=None.</li>
<li>Open the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">submission page</a> → <b>New submission</b> → choose the .tif (or .zip).</li>
<li>Unique name: <code>{receipt["unique_name"]}</code></li>
<li>Note (≤140 chars; this one is {len(card["submission_note"])}): <code>{html.escape(card["submission_note"])}</code></li>
<li>Confirm remaining weekly allowance on the page, submit, and save the organizer receipt. Only receipt results may be labelled ORGANIZER-CONFIRMED; everything on this site today is HOLDOUT-DTI / OWNER-REPORTED / MODEL ESTIMATE.</li></ol></section>
<section><h2>“Predicted values must be in range [0, 1]” — root cause &amp; fix</h2>
<p>Causes: NaN/Inf cells, the float32 nodata sentinel (−3.4e38, present even inside the footprint in <code>training_features.tif</code>) leaking into outputs,
or unbounded model values. Fix shipped here (<code>scripts/submission_writer.py</code>): binary {{0,1}} float32, 0 outside footprint and on catalogue,
nodata=None, then machine-validation of <b>all 12,279,160 cells</b> against the sample grid before release (receipt JSON beside the TIF). Never blindly clip to hide a bug — this writer only writes an already-binary mask.</p></section>'''
    (DOCS / "how-to-submit.html").write_text(page("How to submit", how))

    lane = f'''<header><span class="eyebrow">LANE KANLER-EXT-CORROB · {DATE}</span><h1>Lane evidence — EXT corroboration / multi-catalogue</h1>{nav}</header>
{banner}
<section><h2>Pre-registered method (single lane)</h2><p>{html.escape(card["mechanism"])}</p>
<p><b>Hypothesis:</b> {html.escape(card["hypothesis"])}</p><p><b>Named non-fault mimic:</b> {html.escape(card["named_non_fault_mimic"])}</p>
<p>Full pre-registration (5 ranked hypotheses, decision rule fixed before running): <code>research/preregistration-ext-corrob.md</code>.
Reproduce: <code>python scripts/restore_labels_sample.py &amp;&amp; python scripts/build_features.py &amp;&amp; python scripts/run_experiments_ext.py &amp;&amp; python scripts/finalize_ext.py &amp;&amp; python scripts/build_site.py</code></p></section>
<section><h2>Numbers (all HOLDOUT-DTI unless labelled)</h2>
<div class="scroll"><table><thead><tr><th>Result</th><th>Value</th><th>Evaluator / withheld</th></tr></thead><tbody>
<tr><td>EXP3 primary OOF (shipped file)</td><td>{f4(oof["value"])} {ci(oof["ci95"])}</td><td>KANLER quadrant OOF v1 · {oof["n_withheld_positives"]:,} px</td></tr>
<tr><td>E1 frozen best (same evaluator)</td><td>{f4(oof["E1_same_evaluator"])} {ci(oof["E1_ci95"])}</td><td>same · 56,464 px → tie, no superiority</td></tr>
<tr><td>EXP3 SGMC OOF (fold-local)</td><td>{f4(sgoof["value"])} {ci(sgoof["ci95"])}</td><td>quadrant OOF vs SGMC · {sgoof["n_withheld_positives"]:,} px; champion in-domain {f4(sgoof["champion_in_domain_sgmc"])}</td></tr>
<tr><td>EXP1 CORROB callable hide-recover (clean, label-free)</td><td>{f4(card["holdout_dti"]["exp1_corrob_clean"]["callable_visible_gated"])}</td><td>GEMSDOE32-HOLDOUT-v3-visible-gated · 22,232 px; champion-surface proxy {card["holdout_dti"]["exp1_corrob_clean"]["champion_surface_proxy_visible_gated"]:.4f}</td></tr>
<tr><td>Leakage canary</td><td>max AUC {card["leakage_canary"]["max_single_feature_abs_AUC"]:.3f} ≤ 0.90 PASS</td><td>47 features alone, sampled</td></tr>
<tr><td>Headline estimate</td><td>~{est_v:.2f} [{est["headline_range"][0]:.2f}, {est["headline_range"][1]:.2f}]</td><td>MODEL ESTIMATE (Anchor A); SGMC-ratio anchor ({est["anchorB_SGMC_ratio_REJECTED_for_MCSUP"]["value_if_used"]:.2f}) REJECTED for SGMC-trained models</td></tr>
</tbody></table></div>
<p><b>IR-EXT-01 (contamination quarantined):</b> EXP2/EXP3 global-surface callable hide-recover (0.1598) and final-mask SGMC (0.3288) evaluate a model on its own
training positives; they appear in <code>experiments_ext.json</code> for transparency and are excluded from every gate above. Direct SGMC emission scored only
0.0512/0.0492 live upstream — SGMC-DTI is gameable and never anchors an SGMC-trained model's estimate here.</p>
<p>Emission sweep (EXP3): 25,000 dots → OOF {f4(exp["EXP3_EMIT"]["sweep_pooled_dti"]["25000"])}; 37,654 → {f4(exp["EXP3_EMIT"]["sweep_pooled_dti"]["37654"])};
44,090 → {f4(exp["EXP3_EMIT"]["sweep_pooled_dti"]["44090"])} (winner). Unlike the champion lineage, this lower-precision supervised surface still gains from coverage at 44k.</p></section>
<section><h2>Downloads &amp; evidence files</h2><ul>
<li><a href="downloads/{tif}">TIF</a> · <a href="downloads/{tif[:-4]}.zip">ZIP</a> · <a href="downloads/{tif}.receipt.json">validator receipt</a></li>
<li><a href="run_card.json">run_card.json</a> · <a href="experiments_ext.json">experiments_ext.json</a> · <a href="canaries_ext.json">canaries_ext.json</a> · <a href="champion_forensics.json">champion_forensics.json</a> · <a href="baselines_visible_gated.json">baselines_visible_gated.json</a> · <a href="leaderboard_snapshot_20261026.json">leaderboard snapshot</a> · <a href="selector_decision_ext.json">selector decision</a></li></ul>
<p>Verdict: <b>negative</b> — a valid deliverable per protocol. No competition slot was used by this project.</p></section>'''
    (DOCS / "lane-ext-corrob.html").write_text(page("Lane EXT-CORROB", lane))

    e1 = json.loads((EV / "run_card_e1_xg_hgb.json").read_text())
    lane_e1 = f'''<header><span class="eyebrow">PRIOR LANE E1 XG-HGB · 2026-10-26</span><h1>Lane evidence — E1 cross-gradient HGB (superseded)</h1>{nav}</header>
<section class="alert"><h2>Verdict: negative (unchanged)</h2><p>{html.escape(e1["verdict_plain"][:600])}… Full card: <a href="run_card_e1_xg_hgb.json">run_card_e1_xg_hgb.json</a>.
Its TIF lives only in git quarantine (<code>research/quarantine/prior-docs/downloads/</code>) and must not be submitted as an expected improvement over 0.2778
(SGMC-anchored MODEL ESTIMATE ~0.22). This page was regenerated {DATE} after committed merge-conflict markers in the previous file were resolved (IR-EXT-05).</p></section>
<section><h2>Method &amp; key numbers</h2><p>{html.escape(e1["mechanism"])}</p>
<p>Quadrant OOF HOLDOUT-DTI {e1["holdout_dti"]["primary_quadrant_oof"]["E1"]:.4f} (56,464 withheld) — the frozen holdout best the EXT lane had to beat and only tied. SGMC raw {e1["holdout_dti"]["sgmc_off_catalogue"]["E1_raw"]:.4f} vs champion {e1["holdout_dti"]["sgmc_off_catalogue"]["champion_raw"]:.4f} (62,703 px) — the gate it failed. Canary max AUC {e1["leakage_canary"]["max_single_feature_abs_AUC"]:.3f}. Uniqueness max ρ {e1["correlation_overlap_vs_registry"]["max_abs_surface_spearman"]:.3f}.</p></section>'''
    (DOCS / "lane-e1-xg-hgb.html").write_text(page("Lane E1 XG-HGB", lane_e1))
    (DOCS / "submission.html").write_text(page("Moved", '<header><h1>How to submit has moved</h1></header><section><p>See <a href="how-to-submit.html">how-to-submit.html</a> and the <a href="index.html">decision desk</a>. Current verdict: no file is approved as an expected improvement.</p></section>'))

    for src, dst in [("run_card_ext.json", "run_card.json"), ("run_card_e1_xg_hgb.json", "run_card_e1_xg_hgb.json"),
                     ("experiments_ext.json", "experiments_ext.json"), ("experiments_oof.json", "experiments_oof.json"),
                     ("canaries_ext.json", "canaries_ext.json"), ("canaries.json", "canaries.json"),
                     ("champion_forensics.json", "champion_forensics.json"),
                     ("baselines_visible_gated.json", "baselines_visible_gated.json"),
                     ("leaderboard_snapshot_20261026.json", "leaderboard_snapshot_20261026.json"),
                     ("selector_decision_ext.json", "selector_decision_ext.json"),
                     ("uniqueness_EXT_independent.json", "uniqueness_EXT_independent.json"),
                     ("uniqueness_E1.json", "uniqueness_E1.json"), ("focus_sites.json", "focus_sites.json")]:
        p = EV / src
        if p.exists(): shutil.copyfile(p, DOCS / dst)
    for f in ["raster_audit.json", "raster_manifest.json", "source_manifest.json", "hypotheses.md"]:
        if (RES / f).exists(): shutil.copyfile(RES / f, DOCS / f)
    shutil.copyfile(RES / "run_card.json", DOCS / "run-card.json")
    print("site written:", tif)

if __name__ == "__main__":
    build()
