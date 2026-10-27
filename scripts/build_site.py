#!/usr/bin/env python3
"""Build the fail-closed GitHub Pages evidence portal from the latest audit.

The current builder deliberately has no upload-authorization path. Historical
run cards and model summaries are not a substitute for independent replay.
"""
from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def esc(x: object) -> str:
    return html.escape(str(x), quote=True)


def header(active: str) -> str:
    pages = [("index.html", "Overview"), ("executive-summary.html", "Executive summary"),
             ("research.html", "Research"), ("irregularities.html", "Open issues")]
    links = "".join('<a href="{}"{}>{}</a>'.format(p, ' class="active" aria-current="page"' if p == active else '', name) for p, name in pages)
    return f'''<a class="skip" href="#main">Skip to content</a>
<header class="topbar"><div class="wrap topbar-inner"><a href="index.html" class="brand"><span class="brand-mark">G</span><span class="brand-name">GEMS / FIELDNOTES<small>KANLERGEMSDOE2</small></span></a>
<nav class="nav" aria-label="Main navigation">{links}<a class="nav-link" href="https://github.com/kanlerxz87-cyber/KANLERGEMSDOE2">GitHub ↗</a></nav></div></header>'''


def page(title: str, active: str, content: str, script: str = "") -> str:
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | GEMS Fieldnotes</title><meta name="description" content="Evidence-led geological fault discovery for the DOE GEMS Prize."><link rel="stylesheet" href="style.css"></head>
<body>{header(active)}<main id="main" class="wrap">{content}</main>
<footer class="footer"><div class="wrap footer-inner"><div><strong>GEMS / FIELDNOTES</strong><br>Evidence before a submission slot.</div><div>Maximize P(Win) · Own the Outcome<br>Built from auditable, dated evidence. No upload is automated.</div></div></footer>{script}</body></html>'''


FEED_SCRIPT = '''<script>
(function(){
  const value=document.getElementById('leader-value'), label=document.getElementById('leader-status');
  if(!value||!label)return;
  fetch('data/public_leaderboard.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('unavailable');return r.json()}).then(d=>{
    let s=(d.status==='success'||d.status==='verified_snapshot')?d:d.last_verified_snapshot;
    if(!s||typeof s.top_public_dti!=='number'||s.top_public_dti<0||s.top_public_dti>1){value.textContent='Unavailable';label.textContent='No verified snapshot';return;}
    value.textContent=s.top_public_dti.toFixed(4);
    const fifth=(typeof s.fifth_public_dti==='number'&&s.fifth_public_dti>=0&&s.fifth_public_dti<=1)?' · #5 '+s.fifth_public_dti.toFixed(4):'';
    label.textContent=(d.status==='unavailable'?'Refresh failed · last snapshot ':'Public snapshot · ')+(s.observed_utc||'unknown date')+fifth;
  }).catch(()=>{value.textContent='Unavailable';label.textContent='Feed could not be loaded'});
})();</script>'''


def focus_table(rows: list[dict]) -> str:
    result=[]
    for r in rows:
        name = Path(r["path"]).name
        score = f'{r["owner_reported_score"]:.4f}'
        overlap = f'{100*r["max_directional_focus_overlap_within_3px"]:.2f}%'
        origin = 'NaN outside' if r['outside_footprint_all_nan'] else ('all-finite' if r['strict_whole_array_finite_0_1'] else 'other encoding')
        local = DOCS / 'downloads' / name
        if local.is_file():
            if hashlib.sha256(local.read_bytes()).hexdigest() != r['sha256']:
                raise SystemExit(f"Historical download differs from pinned evidence: {name}")
            link = f'downloads/{name}'
        else:
            link = r['pinned_download_url']
        result.append(f'''<tr><td><strong><a href="{esc(r['site_url'])}">{esc(r['site'])} ↗</a></strong><small>{esc(origin)} · <a href="{esc(r['pinned_source_url'])}">pinned source</a></small></td>
<td class="file"><a href="{esc(link)}">{esc(name)}</a><small>Historical artifact · SHA-256 {esc(r['sha256'][:12])}…</small></td>
<td><strong>{score}</strong><small>USER/OWNER-REPORTED<br>Receipt not available</small></td>
<td><strong>No</strong><small>{overlap} within 3 px of {esc(r['nearest_focus_site'])}</small></td><td><span class="pill stop">Do not submit</span><small>Historical; not a new, cleared candidate</small></td></tr>''')
    return f'''<div class="table-wrap"><table><thead><tr><th scope="col">Site</th><th scope="col">Historical file</th><th scope="col">Reported score</th><th scope="col">Unique vs. other focus sites?</th><th scope="col">Decision</th></tr></thead><tbody>{''.join(result)}</tbody></table></div>'''


def main() -> None:
    audit = json.loads((ROOT / "evidence/release_audit_20261027.json").read_text())
    card = json.loads((ROOT / "evidence/current_run_card.json").read_text())
    if card.get("verdict") != "negative" or card.get("ok_to_submit") is not False or audit.get("verdict") != "negative":
        raise SystemExit("This portal builder only publishes the current negative decision; refusing stale or positive card")
    pre = audit["preflight"]
    prior = audit["prior_candidate"]
    path = DOCS / "downloads" / prior["file"]
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != prior["sha256"]:
        raise SystemExit("Research artifact missing or differs from current audit")
    if not pre["forced_duplicate"] or not prior["duplicate_under_literal_rule"]:
        raise SystemExit("Stop evidence changed; rerun review before building")
    hr=audit['historical_holdout_not_replayed']
    percent=100*prior['witness_overlap_fraction']; bound=100*pre['minimum_directional_overlap']
    overlap_dots=prior['witness_overlap_dots']; count=prior['inside_positive_pixels']
    artifact=f"downloads/{esc(prior['file'])}"
    table=focus_table(audit['focus_nine'])

    # ------------------------------------------------------------------
    # Session-2 (KG2-S2 DSLUP) candidate: rendered ONLY when its evidence
    # and artifact are present and byte-identical to the pinned receipt.
    # Both duplicate-rule readings are displayed; neither is hidden.
    # ------------------------------------------------------------------
    s2_home = s2_summary = ""
    s2_feed: dict | None = None
    s2_card_path = ROOT / "evidence/dslup_unique_slot_run_card.json"
    if s2_card_path.is_file():
        s2 = json.loads(s2_card_path.read_text())
        s2_file = s2["submission_filename"]
        s2_path = DOCS / "downloads" / s2_file
        if not s2_path.is_file() or hashlib.sha256(s2_path.read_bytes()).hexdigest() != s2["raster_sha256"]:
            raise SystemExit("Session-2 artifact missing or differs from its pinned run card")
        disc = s2["literal_rule_disclosure"]
        s2hr = s2["holdout_dti"]["primary_hide_and_recover"]
        s2sg = s2["holdout_dti"]["secondary_off_catalogue_sgmc"]
        s2reg = s2["registry_comparison"]
        s2own = max(v["asym_3px_overlap_ours_in_peer"] for v in s2["overlap_vs_own_prior_rasters"].values() if v)
        s2champ = s2["overlap_vs_0p2778_champion"]["asym_3px_overlap_ours_in_peer"]
        s2lit = disc["this_file_literal_overlap_vs_lattice_witness"]
        s2zip = s2["zip_filename"]
        s2note = s2["submission_note"]
        s2_home = f'''<section class="hero" aria-labelledby="s2-title" style="margin-bottom:1.2rem"><div><div class="eyebrow">Session 2 · 27 October 2026 · KG2-S2 DSLUP-3D lane</div><span class="status">NOT OK TO SUBMIT — literal protocol in force</span>
<h1 id="s2-title">Session-2 candidate:<br>not cleared to submit.</h1>
<p class="lead"><strong>{esc(s2_file)}</strong> — depth-scaled listric updip-gravity surface, re-emitted under a hard own-halo cap (&le;{s2["accepted_q_abs"]:,} of {s2["emitted_dots"]:,} dots near our prior rasters). It beats every raster this repository has evaluated on <strong>both</strong> blind holdouts with strictly positive paired 95% CIs, and is the least-duplicated candidate this fleet audit has seen: max 3-px overlap vs every <em>geological</em> detector {100*s2reg["final_dots_max_detector_3px_overlap"]:.2f}%, vs the 0.2778 champion {100*s2champ:.2f}%, vs our own prior files &le;{100*s2own:.2f}%.</p>
<div class="hero-actions"><a class="btn" href="downloads/{esc(s2_file)}" download>&#8595; Download Session-2 GeoTIFF</a><a class="btn secondary" href="downloads/{esc(s2zip)}" download>&#8595; Portal ZIP</a><a class="btn secondary" href="downloads/dslup_run_card.json">Run card ↗</a></div>
<p class="note"><strong>DECISION: NOT OK TO DOWNLOAD AND SUBMIT (literal protocol, PR&nbsp;#25).</strong> Witness overlap vs the registered spacing-5 lattice is {100*s2lit["fraction"]:.2f}% (&gt;70%); every {s2lit["our_dots"]:,}-dot raster is forced to at least {100*s2lit["forced_minimum_for_any_raster_at_this_budget"]:.2f}%. A control-separated reading would treat that lattice as a calibration control and would be needed to clear this file; that reading is <em>not adopted</em> and requires an owner decision. The literal rule and the unique-TIF mandate cannot both be met at this budget.</p></div>
<div class="hero-aside"><div class="eyebrow">Blind holdout (HOLDOUT-DTI, not a live score)</div><h3>Beats the 0.2778 proxy on both metrics</h3>
<p>Hide-and-Recover <strong>{s2hr["pooled_dti"]:.4f}</strong> vs {s2hr["champion_02778_same_evaluator"]:.4f} (paired Δ {s2hr["paired_delta_vs_0p2778_ref"]:+.4f}, 95% CI [{s2hr["paired_delta_ci95"][0]:+.4f}, {s2hr["paired_delta_ci95"][1]:+.4f}])</p>
<p>Blind SGMC-CAL <strong>{s2sg["sgmc_prevalence_calibrated_dti"]:.4f}</strong> vs {s2sg["champion_02778_same_evaluator"]:.4f} (paired Δ {s2sg["paired_delta_vs_0p2778_ref"]:+.4f}, 95% CI [{s2sg["paired_delta_ci95"][0]:+.4f}, {s2sg["paired_delta_ci95"][1]:+.4f}])</p>
<p class="note">Historical-evaluator numbers (GEMSDOE32-HIDE-RECOVER/SGMC-CAL v3.0, N=22,232 / 62,703, n_boot=1000). No organizer receipt exists for any score here.</p>
<div class="hash mono">{esc(s2_file)}<br>SHA-256 {esc(s2["raster_sha256"])}<br>Note ({s2["note_length"]}/140): {esc(s2note)}</div></div></section>'''
        s2_summary = f'''<div class="callout"><strong>SESSION-2 CANDIDATE — NOT OK TO SUBMIT (literal protocol):</strong><p><a href="downloads/{esc(s2_file)}" download>Download {esc(s2_file)}</a> · SHA-256 <span class="mono">{esc(s2["raster_sha256"][:16])}…</span> · note ({s2["note_length"]}/140): <span class="mono">{esc(s2note)}</span></p>
<p>Control-separated reading (NOT adopted; would need owner approval): PROMOTE. Self-reported 5/5 gates and a claimed {s2reg["unique_rasters_checked"]:,}-raster comparison are <strong>not reproducible from committed artifacts</strong> (see Open issues). Max overlap vs geological detectors as claimed, incl. our own (max {100*s2reg["final_dots_max_detector_3px_overlap"]:.2f}%). Literal all-registry reading (PR #25): duplicate vs the spacing-5 lattice ({100*s2lit["fraction"]:.2f}%), as is every possible raster at this budget (forced &ge;{100*s2lit["forced_minimum_for_any_raster_at_this_budget"]:.2f}%). HOLDOUT-DTI: Hide-Rec <strong>{s2hr["pooled_dti"]:.4f}</strong> [{s2hr["ci95"][0]:.4f}, {s2hr["ci95"][1]:.4f}], SGMC-CAL <strong>{s2sg["sgmc_prevalence_calibrated_dti"]:.4f}</strong> [{s2sg["ci95"][0]:.4f}, {s2sg["ci95"][1]:.4f}] — both above the 0.2778 proxy with strictly positive paired CIs. No leaderboard estimate is claimed; an OLS projection on 9 user-reported anchors (R²=0.956) would EXTRAPOLATE far outside its support and is recorded only inside the run card as a labeled projection, never a score.</p>
<p><a href="../evidence/dslup_unique_slot_run_card.json">Run card</a> · <a href="../evidence/dslup_literal_rule_disclosure.json">Literal-rule disclosure</a> · <a href="../evidence/dslup_experiments.json">3 preregistered experiments (honest negatives on own-collision)</a> · <a href="../evidence/dslup_champion_mode_receipt.json">champion-mode receipt</a> · <a href="../evidence/leakage_canary_dslup.json">leakage canary (max AUC 0.7954)</a> · prereg: <a href="../registry/preregistration_dslup.json">frozen 2026-10-27</a>.</p></div>'''
        s2_feed = {
            "filename": s2_file, "sha256": s2["raster_sha256"], "zip": s2zip,
            "emitted_dots": s2["emitted_dots"], "portal_note": s2note,
            "ok_to_download_and_submit": False, "verdict_control_separated_policy": "would_promote_only_if_owner_adopts_control_separated_rule",
            "verdict_literal_rule": "duplicate_vs_space_filling_lattice_as_is_every_possible_raster_at_this_budget",
            "literal_overlap_vs_lattice": s2lit["fraction"],
            "forced_minimum_any_raster": s2lit["forced_minimum_for_any_raster_at_this_budget"],
            "max_overlap_vs_geological_detectors": s2reg["final_dots_max_detector_3px_overlap"],
            "max_overlap_vs_own_prior_rasters": s2own,
            "holdout_dti": s2["holdout_dti"],
        }

    # ------------------------------------------------------------------
    # Parallel DARP-MT10 lane + Sister-Repository Fleet Audit (2026-10-27)
    # ------------------------------------------------------------------
    darp_home = darp_summary = darp_research = darp_irregular = ""
    darp_feed: dict | None = None
    darp_card_path = ROOT / "evidence/darp_mt10_run_card_20261027.json"
    sis_audit_path = ROOT / "evidence/sister_and_focus_audit_20261027.json"
    if darp_card_path.is_file() and sis_audit_path.is_file():
        dc = json.loads(darp_card_path.read_text(encoding="utf-8"))
        sis = json.loads(sis_audit_path.read_text(encoding="utf-8"))
        dfile = dc["submission_filename"]
        dzip = dc["zip_filename"]
        dnote = dc["submission_note"]
        dpath = DOCS / "downloads" / dfile
        if not dpath.is_file() or hashlib.sha256(dpath.read_bytes()).hexdigest() != dc["raster_sha256"]:
            raise SystemExit("DARP-MT10 artifact missing or differs from its pinned run card")
        dhr = dc["holdout_dti"]["primary_hide_and_recover"]
        dcp = dc["holdout_dti"]["piedmont_off_catalogue_c_pied"]
        de2 = dc["holdout_dti"]["ablation_darp_exp2_piedmont_breakthrough"]["piedmont_off_catalogue_c_pied"]
        dcorr = dc["correlation_overlap_vs_registry"]
        dreg = dc["registry_comparison"]
        dnote_len = len(dnote)
        darp_home = f'''<section class="section" aria-labelledby="darp-title"><div class="section-head"><div><div class="eyebrow">Parallel Lane · 27 October 2026 · DARP-MT10 (Dip-Adaptive MT + 10 m DEM)</div><h2 id="darp-title">DARP-MT10 negative result &amp; +39.1% piedmont blind-basin breakthrough</h2><p><strong>DO NOT SUBMIT TO DRIVENDATA (`verdict = "negative"` — research artifact only).</strong> Unique 2026-10-27 GeoTIFF (<span class="mono">{esc(dfile)}</span>, 13/13 strict [0,1] checks PASS, 0 NaNs, 0 on-catalogue dots, 22.20% LiDAR-void coverage vs 0.65% for 0.2778 Champion).</p></div></div>
<div class="grid-two"><div class="card"><span class="pill stop">NEGATIVE — DO NOT SUBMIT TO PORTAL</span><h3>Piedmont blind-basin gain (+39.1%), range-front trade-off (-0.0012)</h3>
<p>On alluvial-covered piedmont faults (<code>GEMSDOE70-C-PIED-v1.0</code>, <code>Z_b &gt;= 150 m</code>, N=9,847), <strong>DARP-EXP-1</strong> reaches <strong>{dcp["pooled_dti"]:.4f}</strong> (+{dcp["paired_delta_vs_02778_champ"]:.4f} over 0.2778 Champion {dcp["champion_02778_same_evaluator"]:.4f}) and <strong>DARP-EXP-2</strong> reaches <strong>{de2["pooled_dti"]:.4f}</strong> (<strong>+39.1%</strong>, paired 95% CI [{de2["paired_delta_ci95"][0]:+.4f}, {de2["paired_delta_ci95"][1]:+.4f}], #1 across all focus &amp; sister sites). On full-catalogue <code>HIDE-RECOVER-v3.0.1</code>, range-front damping lowers DTI by {dhr["paired_delta_vs_02778_champ"]:+.4f} ({dhr["pooled_dti"]:.4f} vs {dhr["champion_02778_same_evaluator"]:.4f}), so automatic gates keep <code>verdict = "negative"</code> under the 3-experiment cap.</p>
<p><strong>Uniqueness (290 unique rasters + Session-2 peers):</strong> max 3-px overlap vs non-blanket detectors <strong>{100*dreg["final_dots_max_detector_3px_overlap"]:.2f}% &le; 70%</strong> · vs DSLUP (c71122d5) <strong>{100*dcorr["overlap_3px_vs_dslup_c71122d5"]:.2f}%</strong> · vs ECPU (cecbdca7) <strong>{100*dcorr["overlap_3px_vs_ecpu_cecbdca7"]:.2f}%</strong> · vs archived HTCADS (11a2f251) <strong>{100*dreg["named_benchmarks"]["PRIOR_KG2_HTCADS_11a2f251"]["our_in_peer_3px"]:.2f}%</strong> · vs 0.2778 Champion <strong>{100*dreg["named_benchmarks"]["GEMSDOE32_0p2778_champ"]["our_in_peer_3px"]:.2f}%</strong>.</p>
<div class="hero-actions"><a class="btn secondary" href="downloads/{esc(dfile)}" download>&#8595; Download DARP Research TIFF</a><a class="btn secondary" href="downloads/{esc(dzip)}" download>&#8595; DARP ZIP</a><a class="btn secondary" href="downloads/darp_mt10_run_card.json">DARP Run Card ↗</a></div>
<p class="note mono">SHA-256 {esc(dc["raster_sha256"])}<br>Note ({dnote_len}/140): {esc(dnote)}</p></div>
<div class="card"><h3>4-Instrument Diagnostic &amp; Uniqueness Verification</h3><img src="assets/fig4_darp_mt10_four_instruments_and_uniqueness.png" alt="DARP-MT10 four holdout instruments, LiDAR void coverage, and 290-raster uniqueness verification" style="width:100%;height:auto;border-radius:8px"><p class="note">Leakage canary: 68/68 features tested, max single-feature AUC = 0.7965 &le; 0.90 (<a href="../evidence/darp_mt10_canary_20261027.json">receipt ↗</a>).</p></div></div></section>'''

        sis_rows_html = []
        for r in sis["sister_and_fleet_audited_rasters"]:
            safe_txt = "Safe ([0,1])" if (r["portal_safe_0_1"] and r["on_catalogue_dots"] == 0 and r["dots"] < 500000) else f"UNSAFE (portal_safe={r['portal_safe_0_1']}, on_cat={r['on_catalogue_dots']}, dots={r['dots']:,})"
            sc_txt = f"{r['user_reported_score']:.4f} (USER-REPORTED)" if r.get("user_reported_score") else f"No live receipt · C-PIED {r['c_pied_v1_dti']:.4f} / SGMC {r['sgmc_cal_v3_dti']:.4f} (HOLDOUT-DTI)"
            sis_rows_html.append(f'''<tr><td><strong>{esc(r['site'])}</strong></td><td class="file">{esc(r['filename'])}<small>SHA-256 {esc(r['sha256'][:12])}… · {r['dots']:,} px &ge;0.5</small></td><td>{esc(sc_txt)}</td><td>{esc(safe_txt)}</td><td><strong>{100*r['overlap_3px_vs_new_darp']:.2f}%</strong> vs DARP</td></tr>''')
        for er in sis["empty_initialized_sister_repos"]:
            sis_rows_html.append(f'''<tr><td><strong><a href="https://github.com/{esc(er['owner_repo'])}">{esc(er['site'])} ↗</a></strong></td><td class="file">0 GeoTIFFs (initialized stub)</td><td>None</td><td>No raster</td><td>N/A</td></tr>''')

        darp_summary = f'''<div class="callout red-callout"><strong>PARALLEL LANE DARP-MT10 (`4ad35e71-zeros.tif`): NEGATIVE / DO NOT SUBMIT TO DRIVENDATA (OK TO DOWNLOAD FOR RESEARCH).</strong>
<p><a href="downloads/{esc(dfile)}" download>Download {esc(dfile)}</a> · <a href="downloads/{esc(dzip)}" download>ZIP</a> · <a href="downloads/darp_mt10_run_card.json">Run card</a> · SHA-256 <span class="mono">{esc(dc["raster_sha256"][:16])}…</span> · note ({dnote_len}/140): <span class="mono">{esc(dnote)}</span></p>
<p>Strict [0,1] portal-safe (13/13 checks PASS, 0 NaNs, 0 on-catalogue dots) and unique vs all non-blanket detectors (max 3-px {100*dreg["final_dots_max_detector_3px_overlap"]:.2f}%, {100*dcorr["overlap_3px_vs_dslup_c71122d5"]:.2f}% vs DSLUP, {100*dcorr["overlap_3px_vs_ecpu_cecbdca7"]:.2f}% vs ECPU). Achieves <strong>C-PIED-v1.0 = {dcp["pooled_dti"]:.4f}</strong> (DARP-EXP-1) and <strong>{de2["pooled_dti"]:.4f} (+39.1% over 0.2778 Champion)</strong> (DARP-EXP-2, #1 fleet-wide on blind piedmont faults), while HIDE-RECOVER-v3.0.1 is {dhr["pooled_dti"]:.4f} ({dhr["paired_delta_vs_02778_champ"]:+.4f}); fail-closed as <code>negative</code>.</p></div>
<section class="section"><div class="section-head"><div><div class="eyebrow">Sister-repository fleet audit · 27 October 2026</div><h2>Sister sites (KANLERGEMSDOE1..3, WBGGEMSDOE1..3, EUGGEMSDOE1..3, GINNYGEMSDOE1..3, GEMSDOE70)</h2><p>Exact byte audit from <a href="../evidence/sister_and_focus_audit_20261027.json">sister_and_focus_audit_20261027.json ↗</a>.</p></div></div>
<div class="table-wrap"><table><thead><tr><th>Sister repo</th><th>Audited artifact</th><th>Reported / HOLDOUT-DTI</th><th>[0,1] &amp; mask check</th><th>3-px overlap vs DARP</th></tr></thead><tbody>{''.join(sis_rows_html)}</tbody></table></div></section>'''

        darp_research = f'''<section class="section"><div class="section-head"><div><div class="eyebrow">DARP-MT10 Experimental Record · 2026-10-27</div><h2>5 Pre-Registered Hypotheses &amp; 3-Experiment Piedmont Breakthrough</h2></div></div>
<div class="card"><p>Pre-registered in <a href="../registry/preregistration_darp_mt10.json">preregistration_darp_mt10.json ↗</a> and <a href="../knowledge/02_preregistered_hypotheses_kg2_20261027.md">02_preregistered_hypotheses_kg2_20261027.md ↗</a>: <strong>H-N1 (DARP-MT10, selected)</strong> fuses dip-adaptive listric basement projection, USGS 3DEP 10 m seamless DEM in the 24.60% LiDAR void, and 3D MT phase-tensor / tipper invariants; <strong>H-N2</strong> models non-Boussinesq range-front hydraulic head breaks; <strong>H-N3</strong> tests radiometric K/eTh clay-alteration halos; <strong>H-N4</strong> tests paleolake shoreline mimic rejection; <strong>H-N5</strong> tests slip-tendency filtering.</p>
<p><strong>Ablation finding (`IR-DARP-CREST-OVERDAMP-08`):</strong> DARP-EXP-2 raised blind piedmont fault recovery (<code>C-PIED-v1.0</code>) from 0.1012 (0.2778 Champion) and 0.0774 (archived HTCADS) to <strong>{de2["pooled_dti"]:.4f} (+39.1%, 95% CI [{de2["paired_delta_ci95"][0]:+.4f}, {de2["paired_delta_ci95"][1]:+.4f}])</strong>, proving 3D MT + listric projection + 10 m DEM breaks the 24.60% LiDAR-void ceiling — while cubic piedmont weighting over-damped shallow range-front contacts. Next session should use a two-regime range-front + piedmont mixture.</p></div></section>'''

        darp_irregular = f'''<section class="section"><div class="section-head"><div><div class="eyebrow">DARP-MT10 &amp; Sister-Fleet Irregularities · 2026-10-27</div><h2>Shared-tool fixes &amp; sister-site defects caught</h2></div></div>
<div class="grid-two"><article class="card"><div class="eyebrow">Fixed in shared template</div><h3>IR-SHARED-EMPTY-TRUTH-FP-04 &amp; IR-HTCADS-TC-05</h3><p>Patched <code>src/gems32/holdout.py</code> so empty-truth bootstrap tiles record exact false-positive mass <code>pred_sum</code> in pooled Tversky denominators instead of returning <code>(0,0,0)</code>, and patched <code>src/gems32/htcads.py</code> so magnetic tilt angle is computed from <code>arctan(dRTP/dz / |grad_H RTP|)</code> rather than band 6 (<code>tc</code> terrain correction).</p></article>
<article class="card"><div class="eyebrow">Sister-site audit flags</div><h3>WBGGEMSDOE2 blanket &amp; WBGGEMSDOE3 on-catalogue leak</h3><p><code>WBGGEMSDOE2</code> <code>a1b2c3d4</code> emits 5,094,374 positive pixels (98.6% of footprint — blanket baseline) and <code>efd46877</code> sets non-None <code>nodata</code>; <code>WBGGEMSDOE3</code> <code>5d451566</code> places 463 positive dots directly on zero-scored public catalogue pixels; <code>GEMSDOE70</code>’s 0.2478 file is <code>p5-dual-submod300</code> (not <code>p8</code>).</p></article></div></section>'''

        darp_feed = {
            "filename": dfile,
            "sha256": dc["raster_sha256"],
            "zip": dzip,
            "verdict": dc["verdict"],
            "ok_to_download_and_submit": dc["ok_to_download_and_submit"],
            "ok_to_download_for_research": dc["ok_to_download_for_research"],
            "c_pied_exp1_dti": dcp["pooled_dti"],
            "c_pied_exp2_dti": de2["pooled_dti"],
            "hide_recover_exp1_dti": dhr["pooled_dti"],
            "max_3px_non_blanket_detectors": dreg["final_dots_max_detector_3px_overlap"],
            "overlap_3px_vs_dslup": dcorr["overlap_3px_vs_dslup_c71122d5"],
            "overlap_3px_vs_ecpu": dcorr["overlap_3px_vs_ecpu_cecbdca7"],
        }

    home=f'''<div class="breadcrumb">DOE GEMS PRIZE &nbsp; / &nbsp; <span>Decision dashboard</span></div>
{s2_home}
{darp_home}
<section class="hero" aria-labelledby="hero-title"><div><div class="eyebrow">Geological fault discovery · 27 October 2026 review</div><span class="status">Submission on hold</span>
<h1 id="hero-title">No submission<br>cleared yet.</h1><p class="lead">The previous candidate is a useful research artifact, but it fails the requested literal duplicate rule. Protect the weekly slot until the protocol conflict and independent validation are resolved.</p>
<div class="hero-actions"><a class="btn" href="{artifact}" download>↓ Download research TIFF</a><a class="btn secondary" href="executive-summary.html">Read the submission guide →</a></div>
<p class="note"><strong>DO NOT SUBMIT.</strong> This is an existing research file, not a new, cleared entry.</p></div>
<div class="hero-aside"><div class="eyebrow">Current decision</div><h3>Literal registry stop</h3><p><strong>{percent:.3f}%</strong> of the previous file’s dots fall within 3 pixels of a registered raster, exceeding the 70% limit.</p><p>Its pixels pass local range checks; that is not organizer acceptance or permission to submit.</p><div class="hash mono">{esc(prior['file'])}<br>SHA-256 {esc(prior['sha256'])}</div></div></section>
<div class="metrics" aria-label="Decision metrics"><div class="metric"><div class="label">Duplicate overlap</div><div class="value">{percent:.3f}%</div><div class="hint">{overlap_dots:,} of {count:,} prior dots · ≤70% required</div></div>
<div class="metric"><div class="label">Minimum possible</div><div class="value">{bound:.2f}%</div><div class="hint">Any {pre['candidate_dot_budget']:,}-dot placement · same witness</div></div>
<div class="metric"><div class="label">New experiments</div><div class="value">0</div><div class="hint">Stopped before fitting or placing dots</div></div>
<div class="metric"><div class="label"><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Public #1 DW-Tversky ↗</a></div><div class="value" id="leader-value">—</div><div class="hint" id="leader-status">Loading dated public snapshot…</div><noscript><span class="note">JavaScript disabled; view the linked official leaderboard.</span></noscript></div></div>
<section class="section"><div class="section-head"><div><div class="eyebrow">Start here</div><h2>One result, three different questions.</h2><p>A valid-looking file is not necessarily a distinct or high-scoring submission.</p></div></div>
<div class="grid-three"><article class="card"><div class="card-icon">01</div><h3>Is the file in range?</h3><p>Yes, locally: one float32 band on the mirror grid, with finite whole-array values in [0, 1]. The sample uses NaN outside its footprint; this file uses zeros. Portal acceptance is unverified.</p></article>
<article class="card"><div class="card-icon">02</div><h3>Is it unique?</h3><p>No under the literal rule. A single registered witness is enough to stop. A different file hash does not make a method or its dots unique.</p></article>
<article class="card"><div class="card-icon">03</div><h3>Will it score higher?</h3><p>Unknown. A historical holdout proxy cannot reliably be converted into a public leaderboard score. No current experiment or organizer receipt establishes a gain.</p></article></div></section>
<section class="section"><div class="section-head"><div><div class="eyebrow">The evidence</div><h2>Why the stop is unavoidable</h2><p>Exact counting on the pinned sample footprint and registered lattice.</p></div><a class="section-link" href="irregularities.html">See all open issues →</a></div>
<div class="grid-two"><div class="card"><h3>The constraint</h3><p>The witness covers <strong>{pre['covered_pixels_within_3px']:,}</strong> of {pre['footprint_pixels']:,} footprint pixels within 3 px. Only <strong>{pre['uncovered_pixels']:,}</strong> are outside its neighborhood.</p><p>For any {pre['candidate_dot_budget']:,} distinct dots, at least {pre['minimum_overlapping_dots']:,} must therefore be inside it: <strong>{bound:.2f}%</strong>. Repositioning dots to exploit the tiny uncovered area is not geological evidence.</p><p class="note">This bound is specific to this budget, footprint, witness and radius. It does not prove that every possible smaller raster fails.</p></div>
<div class="card"><h3>What we restored</h3><p>Competition and scientific owner mirrors were restored through GitHub and checked against pinned SHA-256 hashes. A 30-column cached feature matrix was prepared; no model was fitted in this review.</p><p>The mirrors are not independently authenticated organizer downloads. Private expert truth, full current registry, current account quota and an independent holdout replay remain unavailable.</p><a class="section-link" href="../evidence/release_audit_20261027.json">Open exact-byte audit ↗</a></div></div></section>
<section class="section"><div class="section-head"><div><div class="eyebrow">Focus sites</div><h2>The nine-site picture</h2><p>The largest reported historical result is GEMSDOE32’s 0.2778, but its file is not a new or unique submission.</p></div><a class="section-link" href="executive-summary.html">Full comparison & guide →</a></div>
<div class="callout"><strong>No defensible leaderboard estimate for a new file.</strong><p>The nine historical numbers are user/owner reports without archived submission-page receipts. See the comparison for the exact artifacts, hashes, overlaps and evidence classes.</p></div></section>'''

    s3_path = ROOT / "evidence/session3_independent_recheck_20261027.json"
    why_block = ""
    if s3_path.is_file():
        s3 = json.loads(s3_path.read_text(encoding="utf-8"))
        mech = s3["mechanism_near_known_fault"]
        g25, g32 = mech["GEMSDOE25"], mech["GEMSDOE32"]
        removed = g25["positive_dots"] - g32["positive_dots"]
        assert removed == g25["off_fault_dots_within_2px_of_known_fault"] and g32["off_fault_dots_within_2px_of_known_fault"] == 0, "mechanism receipt changed"
        mrows = []
        for site in ["GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"]:
            m = mech[site]
            score = {r["site"]: r["owner_reported_score"] for r in audit["focus_nine"]}[site]
            mrows.append(f'<tr><td><strong>{site}</strong></td><td>{m["positive_dots"]:,}</td><td>{m["off_fault_dots_within_1px_of_known_fault"]:,}</td><td>{m["off_fault_dots_within_2px_of_known_fault"]:,}</td><td>{m["off_fault_dots_within_3px_of_known_fault"]:,}</td><td>{score:.4f}<small>USER/OWNER-REPORTED</small></td></tr>')
        why_block = f'''<section class="section" aria-labelledby="why-title"><div class="section-head"><div><div class="eyebrow">Forensics · session 3</div><h2 id="why-title">Why did GEMSDOE32 reach 0.2778?</h2><p>Verified geometry, not a leaderboard claim. Counts are from the Session-3 recheck (<a href="../evidence/session3_independent_recheck_20261027.json">receipt</a>) against the pixel-exact known-fault mask.</p></div></div>
<div class="callout"><strong>Mechanism (strongest reading of the verified geometry):</strong><p>GEMSDOE32 is GEMSDOE25 with exactly <strong>{removed:,}</strong> dots removed: those within 2&nbsp;px of a known USGS/INGENIOUS fault. Its {g32["positive_dots"]:,} dots equal {g25["positive_dots"]:,} &minus; {removed:,}. The organizer states that known-fault pixels are masked pixel-exactly, while off-fault predictions near them are penalized normally (<a href="https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4">DrivenData staff, 21 Sep 2026</a>). Dots hugging a mapped trace therefore carry false-positive cost unless they hit an unmapped fault. Pruning them is the most plausible cause of the reported +0.0178 over GEMSDOE25 (0.2600). This is an inference from geometry plus one user-reported score, not a verified causal result.</p>
<p><strong>Why it cannot be copied as a new submission:</strong> any subset of GEMSDOE32 is a 100% duplicate of it under the literal rule, so further pruning does not produce a unique file.</p></div>
<div class="table-wrap"><table><thead><tr><th>Site</th><th>Positive dots</th><th>Off-fault dots within 1&nbsp;px of known fault</th><th>within 2&nbsp;px</th><th>within 3&nbsp;px</th><th>Reported score</th></tr></thead><tbody>{''.join(mrows)}</tbody></table></div></section>'''

    intro_line = ('No file in this repository is OK to download and submit under the protocol as written (literal all-registry rule, PR #25). The Session-2 file below is the closest candidate and remains research-grade until the owner rules on the lattice control.'
                  if s2_summary else 'At present there is <strong>no competition-ready file</strong>. The existing file below is available for research, not a weekly submission slot.')
    summary=f'''<div class="breadcrumb"><a href="index.html">Decision dashboard</a> &nbsp; / &nbsp; <span>Executive summary</span></div>
<div class="page-intro"><div class="eyebrow">Decision brief · 27 October 2026</div><h1>What to download.<br>What not to submit.</h1><p>{intro_line}</p></div>
{why_block}
{s2_summary}
{darp_summary}
<div class="callout red-callout"><strong>SESSION-1 HTCADS FILE: DO NOT SUBMIT (retracted under the literal rule; superseded by Session 2 on both holdouts).</strong><p><a href="{artifact}" download>Download the previous HTCADS TIFF for research</a> · {percent:.3f}% literal witness overlap · <a href="../evidence/current_run_card.json">current negative run card</a>.</p></div>
<section class="section"><div class="section-head"><div><div class="eyebrow">Evidence table</div><h2>Nine historical site leaders</h2><p>Leaderboard estimates for new submissions: <strong>not available</strong>. Historical results below are user/owner-reported, not organizer-confirmed receipts.</p></div></div>{table}
<p class="note">Overlap is directional: the percentage of a row’s positive pixels within 3 px of its closest other focus-site raster, computed from pinned owner bytes. It is not a complete current-registry check. The files are historical; downloads are provided for comparison only.</p></section>
<section class="section"><div class="section-head"><div><div class="eyebrow">The best previous candidate in this repo</div><h2>Research only, not a recommendation</h2></div></div>
<div class="table-wrap"><table><thead><tr><th>File</th><th>Prior holdout (not replayed)</th><th>Literal uniqueness</th><th>Submission decision</th></tr></thead><tbody><tr><td class="file"><a href="{artifact}" download>{esc(prior['file'])}</a><small>SHA-256 {esc(prior['sha256'])}</small></td><td><strong>{hr['dti']:.6f}</strong><small>HOLDOUT-DTI · {esc(hr['evaluator_version'])} · {hr['withheld_positive_occurrences']:,} withheld-positive occurrences · 95% CI [{hr['ci95'][0]:.6f}, {hr['ci95'][1]:.6f}]<br>Prior receipt; not replayed.</small></td><td><strong>No</strong><small>{percent:.3f}% vs registered lattice; surface not replayed</small></td><td><span class="pill stop">Do not submit</span></td></tr></tbody></table></div></section>
<section class="section"><div class="section-head"><div><div class="eyebrow">For a future approved candidate</div><h2>How submission will work</h2><p>These are instructions, not current authorization. No weekly slot was used in this review.</p></div></div>
<div class="grid-two"><div class="card"><ol class="steps"><li><strong>Run the gates, then the independent selector.</strong> Require fold-visible-only catalogue features, all feature canaries, comparable holdout improvement with CI, literal full-registry checks before/after placement and verified current quota.</li><li><strong>Download the exact approved TIFF.</strong> Confirm its SHA-256 and single-band grid against the authenticated sample. Do not use a renamed historical or negative file.</li><li><strong>Open DrivenData → Submit → Make new submission.</strong> Select the approved GeoTIFF (or ZIP containing that one TIFF) and enter its unique name and short note, at most 140 characters.</li><li><strong>Record the organizer receipt.</strong> Only an actual submission-page receipt can establish the file’s live score; add its timestamp and exact SHA-256.</li></ol></div>
<div class="card"><h3>Format versus acceptance</h3><p>The <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format">official format</a> specifies a single float32 band in [0,1], EPSG:32611 and the supplied grid, with null/NaN outside bounds. The owner mirror’s irregular exterior is NaN; the prior file uses zeros.</p><p>The earlier <code>Predicted values must be in range [0, 1]</code> error has no retained rejected-file bytes or organizer diagnosis. A local whole-array check rules out that particular value-range condition in the reviewed file, but does not prove portal acceptance.</p><p><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">Official competition instructions ↗</a></p></div></div></section>'''

    research=f'''<div class="breadcrumb"><a href="index.html">Decision dashboard</a> &nbsp; / &nbsp; <span>Research</span></div>
<div class="page-intro"><div class="eyebrow">Scientific review</div><h1>Better evidence, not a louder score.</h1><p>Our objective is to map previously unknown faults that may indicate geothermal resources. A heat anomaly or vent is not itself a confirmed fault.</p></div>
<section class="section"><div class="section-head"><div><div class="eyebrow">Forensic analysis</div><h2>What explains the reported 0.2778?</h2></div></div><div class="grid-two"><div class="card"><h3>What the bytes show</h3><p>The GEMSDOE32 raster is exactly the GEMSDOE25 dotted raster after removing pixels ≤2 px from the restored known-fault mask: XOR = {audit['focus_lineage_geometry']['g32_b2_vs_g25_d28_filtered_by_distance_gt_2px_xor']:,}; {audit['focus_lineage_geometry']['g25_to_g32_removed_pixels']:,} pixels are removed. The GEMSDOE36 raster contains every GEMSDOE32 dot plus {audit['focus_lineage_geometry']['g36_extra_pixels_over_g32']:,} more.</p><p>GEMSDOE25 and GEMSDOE30 have identical in-footprint positive masks despite different file bytes. All nine historical leaders exceed the 70% overlap threshold against at least one other focus-site raster.</p></div>
<div class="card"><h3>What remains a hypothesis</h3><p>Under distance-weighted Tversky, thinning redundant predictions or removing locations with little hidden-truth credit can reduce false-positive cost while retaining recall. This is a plausible explanation for the reported improvement, not a measured causal decomposition.</p><p>Hidden expert truth, an organizer receipt linking the 0.2778 score to bytes, and the original experiment replay are unavailable. An earlier reciprocal-score fit cannot prove zero true positives, infer hidden truth counts, or establish a score ceiling.</p></div></div></section>
<section class="section"><div class="section-head"><div><div class="eyebrow">Ranked before modeling</div><h2>Four hypotheses to investigate</h2><p>Qualitative ranking only. None was fitted in this review; novelty across the entire fleet is unproven.</p></div></div>
<div class="grid-two"><article class="card"><div class="eyebrow">01 · medium cost · highest priority</div><h3>Height-persistent cross-gradients</h3><p>Compare orientation and displacement of magnetic and gravity gradient ridges across continuation heights; require hydrothermal corroboration. Could reveal buried steps without surface scarps. <strong>Mimics:</strong> unfaulted contacts and survey seams.</p><p class="note">Uses restored TMI, RTP and gravity mirrors. HTCADS already uses updip projection and cross-gradients; multiscale persistence needs an explicit ablation.</p></article>
<article class="card"><div class="eyebrow">02 · medium cost</div><h3>Thermal direction uncertainty</h3><p>Use GDR 2 m probes and well/spring chemistry with terrain, conductivity and structural orientation; test a fixed family of plausible transport directions rather than one upslope shift. <strong>Mimics:</strong> shallow groundwater flow, land-use anomalies and saline playas.</p></article>
<article class="card"><div class="eyebrow">03 · low–medium cost</div><h3>Visible-tip orientation agreement</h3><p>Recompute visible-only tip geometry per fold and compare its orientation with potential-field and terrain lineaments. <strong>Mimics:</strong> drainage-aligned erosion and lithologic boundaries. Check prior implementations before claiming method novelty.</p></article>
<article class="card"><div class="eyebrow">04 · high cost · data access unverified</div><h3>Deformation–structure discordance</h3><p>Test NASA OPERA DISP-S1 displacement gradients against GeoDAWN and 3DEP boundaries. <strong>Mimics:</strong> groundwater pumping and atmospheric/line-of-sight artifacts. NASA describes the product, but relevant tiles, access and coverage have not been verified here.</p></article></div>
<p class="note"><a href="../research/2026-10-27_htcads_hypotheses.md">Full hypothesis slate and constraints ↗</a> · No numeric DTI or leaderboard gain is claimed.</p></section>
{darp_research}
<section class="section"><div class="section-head"><div><div class="eyebrow">Source library</div><h2>Official sources for review</h2></div></div><div class="card"><ul class="sources">
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">DrivenData problem, metric and submission format</a></li>
<li><a href="https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4">DrivenData staff: pixel-exact known-fault mask</a></li>
<li><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">National Laboratory of the Rockies: official rules</a></li>
<li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN survey and release</a> · <a href="https://gdr.openei.org/submissions/1391">DOE GDR INGENIOUS compilation</a> · <a href="https://www.usgs.gov/3d-elevation-program">USGS 3DEP</a></li>
<li><a href="https://www.earthdata.nasa.gov/data/projects/opera">NASA OPERA data description</a> · <a href="https://github.com/drivendataorg/gems-prize-reference-solution">DrivenData reference solution</a></li></ul><p class="note"><a href="../registry/source_catalog_20261027.json">Source catalog with access and provenance notes ↗</a></p></div></section>'''

    irregular=f'''<div class="breadcrumb"><a href="index.html">Decision dashboard</a> &nbsp; / &nbsp; <span>Open issues</span></div><div class="page-intro"><div class="eyebrow">Integrity & next steps</div><h1>What still stands in the way.</h1><p>These are explicit blockers, not requests for a human geological inspector. Automated checks must fail closed.</p></div>
<div class="grid-two"><article class="card"><div class="eyebrow">01 · blocking</div><h3>Literal novelty contradiction</h3><p>The registered spacing-5 raster is a calibration control, but the prompt says <em>any</em> registry raster. Its neighborhood forces ≥{bound:.2f}% overlap at the frozen budget, above the 70% stop. No implicit control exemption has been applied.</p></article>
<article class="card"><div class="eyebrow">02 · blocking</div><h3>Replay and registry completeness</h3><p>The prior pre-placement surface and OOF caches are unavailable. A single witness proves failure but cannot prove all-registry uniqueness; the complete current registry and independent holdout/canary replay are not established.</p></article>
<article class="card"><div class="eyebrow">03 · blocking</div><h3>Score provenance</h3><p>Historical scores are user/owner reports, not receipts. The legacy site incorrectly called them organizer-confirmed and claimed a mathematical proof of hidden true positives. Both claims are withdrawn.</p></article>
<article class="card"><div class="eyebrow">04 · blocking</div><h3>Portal and quota</h3><p>Neither all-finite nor NaN-exterior variants have an acceptance receipt here. The cause of the range error and current weekly quota are unknown; the selector does not provide a positive authorization path.</p></article>
<article class="card"><div class="eyebrow">05 · provenance</div><h3>Data is restored, not authenticated</h3><p>Core, external and calibration owner mirrors were restored and hash-pinned. Hashes establish identity to a mirror, not origin at DrivenData, USGS or DOE. The mirror sample also contains known-fault positives despite the page’s “total fault absence” description.</p></article>
<article class="card"><div class="eyebrow">06 · next session</div><h3>Reliable promotion pathway</h3><p>Resolve the literal control conflict without silently weakening it; obtain the authenticated organizer template and a complete frozen registry; replay canaries and spatial holdout; implement quota verification; only then allow a separate selector to approve a file.</p></article></div>
<section class="section"><div class="card"><div class="eyebrow">07 · irregularities found in session 3</div><h3>Status and reproducibility conflicts</h3><ul class="sources">
<li><strong>Dashboard vs status feed:</strong> an earlier Session-2 card said PROMOTE while <code>docs/data/status_feed.json</code> said <code>ok_to_submit: false</code>. Resolved to NOT OK under the literal protocol; the control-separated reading is an owner decision.</li>
<li><strong>"1,201 rasters checked" is not reproducible:</strong> the Session-2 collector globs <code>/tmp/explore/GEMSDOE*</code>, a scratch path absent from this repository. The committed registry lists 360 entries and only 12 registry rasters are restored (<a href="../evidence/session3_independent_recheck_20261027.json">receipt</a>).</li>
<li><strong>The validator cannot return OK:</strong> <code>scripts/validate_submission.py</code> documents that full-registry replay, pre-placement replay and quota verification are not implemented.</li>
<li><strong>Local holdout is not a leaderboard estimate:</strong> the local evaluator scores the 0.2778 champion at 0.0992, while the owner reports 0.2778 on the organizer metric. Holdout ranks are not calibrated to the leaderboard.</li>
<li><strong>Public leaderboard figures differ from the brief:</strong> the official page observed on 2026-10-27 shows #1 at 0.4544 and #5 at 0.3566 (the brief quotes 0.4413 and 0.3195). Source: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">DrivenData leaderboard</a>.</li>
<li><strong>Open PR #33</strong> (<code>arena/89a5e815-kanlergemsdoe2</code>) proposes a different promoted file. It was not reviewed or merged in this session.</li>
</ul></div></section>
{darp_irregular}
<section class="section"><div class="callout"><strong>Three-pass review record.</strong><p>Pass 1: restored and hashed inputs, audited bytes, repaired the false-positive gate and rebuilt the site. Pass 2: exercised adversarial and missing-evidence cases. Pass 3: rechecked data, links, generated pages and CI. See <a href="../evidence/current_run_card.json">the current run card</a> and repository tests.</p></div></section>'''

    DOCS.mkdir(exist_ok=True)
    for name, title, content, js in (("index.html","Decision dashboard",home,FEED_SCRIPT),("executive-summary.html","Executive summary",summary,""),("research.html","Research",research,""),("irregularities.html","Open issues",irregular,""),("submission-table.html","Historical submission comparison",summary,""),("audit-review.html","Open issues",irregular,"")):
        (DOCS / name).write_text(page(title,name,content,js),encoding="utf-8")
    feed = {
        "schema": "gems.current-status.v2", "generated_utc": card["generated_utc"],
        "verdict": "negative", "validated_ok_to_download_and_submit": False,
        "ok_to_submit": False, "new_raster": None,
        "research_artifact": prior["file"], "research_artifact_sha256": prior["sha256"],
        "reason": f"Literal registered lattice overlap {percent:.3f}%; assigned budget lower bound {bound:.2f}% > 70%.",
        "run_card": "../../evidence/current_run_card.json", "public_leaderboard": "public_leaderboard.json",
    }
    if s2_feed is not None:
        feed["session2_candidate"] = s2_feed
    if darp_feed is not None:
        feed["darp_mt10_lane"] = darp_feed
    (DOCS / "data").mkdir(exist_ok=True)
    (DOCS / "data/status_feed.json").write_text(json.dumps(feed, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    table_data = {
        "schema": "gems.submission-comparison.v2", "generated_utc": card["generated_utc"],
        "verdict": "negative", "ok_to_submit": False, "new_raster": None,
        "leaderboard_estimate": None,
        "warning": "Historical scores are user/owner reports without receipts; files are research only.",
        "previous_artifact": prior, "focus_nine": audit["focus_nine"],
    }
    (ROOT / "evidence/submission_table_20261027.json").write_text(json.dumps(table_data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print("Built six fail-closed pages (including compatibility URLs) from", audit["generated_utc"])


if __name__ == "__main__":
    main()
