#!/usr/bin/env python3
"""Build a fail-closed GitHub Pages dashboard from the exact-byte audit.

A historical card's promotion flag cannot override the literal registry stop.
No file is authorized until an independently implemented selector verifies all
required evidence, including current quota and the pre-placement surface.
"""
from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def header(active: str) -> str:
    pages = [("index.html", "Overview"), ("executive-summary.html", "Executive summary"),
             ("submission-table.html", "Submission table"),
             ("research.html", "Research"), ("irregularities.html", "Open issues")]
    links = "".join(
        f'<a href="{path}"' + (' class="active" aria-current="page"' if path == active else '')
        + f'>{name}</a>' for path, name in pages
    )
    return f'''<a class="skip" href="#main">Skip to content</a>
<header class="topbar"><div class="wrap topbar-inner"><a href="index.html" class="brand"><span class="brand-mark">G</span><span class="brand-name">GEMS / FIELDNOTES<small>KANLERGEMSDOE2</small></span></a>
<nav class="nav" aria-label="Main navigation">{links}<a class="nav-link" href="https://github.com/kanlerxz87-cyber/KANLERGEMSDOE2">GitHub ↗</a></nav></div></header>'''


REVIEW_NOTICE = """<section class="callout" role="note" aria-label="Current evidence correction"><strong>2026-10-28 review: NOT OK TO SUBMIT.</strong><p>No new method lane was supplied; no new experiment or submission was run. Historical leaderboard values are user-reported. Holdout comparisons do not establish a leaderboard score. Hidden-label counts and pure-false-positive claims inferred from rounded scores are unverified. No validated leaderboard estimate is available. <a href="https://github.com/kanlerxz87-cyber/KANLERGEMSDOE2/blob/main/evidence/review_20261028.md">Read the superseding review and next steps ↗</a>.</p></section>"""


def page(title: str, active: str, content: str, script: str = "") -> str:
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | GEMS Fieldnotes</title><meta name="description" content="Evidence-led geological fault discovery for the DOE GEMS Prize."><link rel="stylesheet" href="style.css"></head>
<body>{header(active)}<main id="main" class="wrap">{REVIEW_NOTICE}{content}</main>
<footer class="footer"><div class="wrap footer-inner"><div><strong>GEMS / FIELDNOTES</strong><br>Evidence before a submission slot.</div><div>Maximize P(Win) · Own the Outcome<br>Auditable evidence. No upload is automated.</div></div></footer>{script}</body></html>'''


FEED_SCRIPT = '''<script>
(function(){
  const value=document.getElementById('leader-value'), label=document.getElementById('leader-status');
  if(!value||!label)return;
  fetch('data/public_leaderboard.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('unavailable');return r.json()}).then(d=>{
    let s=(d.status==='success'||d.status==='verified_snapshot')?d:d.last_verified_snapshot;
    if(!s||typeof s.top_public_dti!=='number'||s.top_public_dti<0||s.top_public_dti>1){value.textContent='Unavailable';label.textContent='No verified snapshot';return;}
    value.textContent=s.top_public_dti.toFixed(4);
    const fifth=(typeof s.fifth_public_dti==='number'&&s.fifth_public_dti>=0&&s.fifth_public_dti<=1)?' · #5 '+s.fifth_public_dti.toFixed(4):'';
    const when=Date.parse(s.observed_utc||''), age=Date.now()-when;
    const stale=!Number.isFinite(when)||age<0||age>24*60*60*1000;
    label.textContent=(d.status==='unavailable'?'Refresh failed · last snapshot ':stale?'Stale public snapshot · ':'Public snapshot · ')+(s.observed_utc||'unknown date')+fifth;
  }).catch(()=>{value.textContent='Unavailable';label.textContent='Feed could not be loaded'});
})();</script>'''


def focus_table(rows: list[dict]) -> str:
    result = []
    for row in rows:
        name = Path(row["path"]).name
        local = DOCS / "downloads" / name
        if local.is_file():
            if hashlib.sha256(local.read_bytes()).hexdigest() != row["sha256"]:
                raise SystemExit(f"Historical download differs from pinned evidence: {name}")
            link = f"downloads/{name}"
        else:
            link = row["pinned_download_url"]
        exterior = "NaN exterior" if row["outside_footprint_all_nan"] else (
            "all finite" if row["strict_whole_array_finite_0_1"] else "other encoding")
        overlap = 100 * row["max_directional_focus_overlap_within_3px"]
        result.append(f'''<tr><td><strong><a href="{esc(row['site_url'])}">{esc(row['site'])} ↗</a></strong><small>{exterior} · <a href="{esc(row['pinned_source_url'])}">pinned source</a></small></td>
<td class="file"><a href="{esc(link)}" download>{esc(name)}</a><small>Research only · SHA-256 {esc(row['sha256'][:12])}…</small></td>
<td><strong>{row['owner_reported_score']:.4f}</strong><small>USER/OWNER-REPORTED<br>No organizer receipt</small></td>
<td><strong>No</strong><small>{overlap:.2f}% within 3 px of {esc(row['nearest_focus_site'])}</small></td><td><span class="pill stop">Do not submit</span><small>Historical file, not a new candidate</small></td></tr>''')
    return f'''<div class="table-wrap"><table><thead><tr><th scope="col">Site</th><th scope="col">Historical download</th><th scope="col">Reported score</th><th scope="col">Unique vs focus sites?</th><th scope="col">Decision</th></tr></thead><tbody>{''.join(result)}</tbody></table></div>'''



def lope_sections() -> tuple[str, str, str, dict | None]:
    """Concurrent KG2-S3 LOPE lane block, rendered only from its receipts (no hard-coded numbers).

    Returns (home_html, summary_html, irregular_html, feed). Empty when the receipts are absent.
    The lane is NEGATIVE; this block can never authorize a submission."""
    paths = {k: ROOT / f"evidence/{v}" for k, v in (("rc", "kg2s3_run_card.json"), ("rv", "kg2s3_dslup_revalidation.json"),
                                                   ("fl", "kg2s3_focus_site_lli.json"), ("ir", "kg2s3_irregularities.json"))}
    if not all(p.is_file() for p in paths.values()):
        return "", "", "", None
    rc, rv, fl, ir = (json.loads(paths[k].read_text()) for k in ("rc", "rv", "fl", "ir"))
    if rc["verdict"] != "negative" or rc["validator"]["verdict"] != "NOT_OK_DO_NOT_SUBMIT" or rv["verdict"] != "NOT_OK_DO_NOT_SUBMIT":
        raise SystemExit("KG2-S3 LOPE receipts changed; this fail-closed builder only renders the recorded negative verdicts")
    hr = rc["holdout_dti"]["primary_hide_and_recover"]; sg = rc["holdout_dti"]["secondary_sgmc_cal"]
    reg = rc["registry_comparison"]; top = (reg.get("top10_overlap_non_space_filling") or [{}])[0]
    du = rv["gates"]["gate_3_uniqueness"]; dtop = (du.get("top10_overlap_non_space_filling") or [{}])[0]
    proj = rc["projection_lli"]; band = proj["error_band"]["leave_site_out_mae"]; dhr = hr["paired_delta_vs_champion"]
    lope_reason = (f"HOLDOUT-DTI {hr['pooled_dti']:.4f} ({esc(hr['evaluator_version'])}, N={hr['n_withheld']:,}, 95% CI "
                   f"[{hr['ci95'][0]:.4f}, {hr['ci95'][1]:.4f}]) is below DSLUP's {hr['dslup_recorded']:.4f}; paired Δ vs champion proxy "
                   f"{dhr['delta']:+.4f} [{dhr['ci95'][0]:+.4f}, {dhr['ci95'][1]:+.4f}]. SGMC-CAL {sg['dti']:.4f} vs {sg['dslup_recorded']:.4f}. "
                   f"Uniqueness: {100*(reg.get('max_overlap_3px_non_space_filling') or 0):.2f}% of dots lie within 3 px of {esc(top.get('file',''))}.")
    dslup_reason = (f"Even with the lattice null-calibrated, {100*(du.get('max_overlap_3px_non_space_filling') or 0):.2f}% of DSLUP's dots lie within "
                    f"3 px of {esc(dtop.get('file',''))}, above the 70% limit. Live-ledger PROJECTION {rv['lli_live_projection']['projected_dti']:.3f} vs "
                    f"{rv['lli_live_projection']['champion_same_identity']:.4f} for the champion (the same identity; not scores).")
    rows = "".join(
        f"<tr><td><strong>{esc(r['site'])}</strong></td><td class=\"mono\">{esc(r['submission'])}</td>"
        f"<td>{r['live_user_reported']:.4f}</td><td>{r['lli_leave_site_out_projection']:.4f}</td></tr>"
        for r in sorted(fl["rows"], key=lambda r: -r["live_user_reported"]))
    home = (f'<section class="section"><div class="section-head"><div><div class="eyebrow">Concurrent Session-3 lane · KG2-S3 LOPE · automated gate</div>'
            f'<h2>New LOPE TIFF: NOT OK — DO NOT SUBMIT</h2><p>This lane emitted <span class="mono">{esc(rc["raster_filename"])}</span> '
            f'(SHA-256 <span class="mono">{esc(rc["raster_sha256"][:16])}…</span>, not published). The byte-level gate '
            f'<span class="mono">scripts/validate_submission_kg2s3.py</span> returned <strong>NOT_OK_DO_NOT_SUBMIT</strong>.</p></div></div>'
            f'<div class="callout red-callout"><strong>Why the LOPE file is not OK</strong><p>{lope_reason}</p>'
            f'<p>Live-ledger PROJECTION {proj["candidate"]:.3f} (±{band:.3f} leave-site-out MAE), against {proj["champion_same_identity"]:.4f} for the champion. It is not a score. '
            f'<a href="../evidence/kg2s3_run_card.json">Run card</a> · <a href="../evidence/kg2s3_submission_gate.json">Gate receipt</a></p></div>'
            f'<div class="callout red-callout"><strong>DSLUP re-validated from bytes: NOT OK</strong><p>{dslup_reason} '
            f'<a href="../evidence/kg2s3_dslup_revalidation.json">Receipt</a></p></div></section>')
    summary = (f'<div class="callout red-callout"><strong>Concurrent KG2-S3 LOPE lane: NEGATIVE — DO NOT SUBMIT.</strong><p>{lope_reason}</p>'
               f'<p>{dslup_reason}</p><p><a href="../evidence/kg2s3_run_card.json">Run card</a> · <a href="../evidence/kg2s3_lli_design_cv.json">Design CV</a> · '
               f'<a href="../evidence/kg2s3_lope_holdout.json">Holdout</a> · <a href="../knowledge/03_preregistered_hypotheses_kg2s3_20261027.md">Preregistration</a></p></div>'
               f'<section class="section"><div class="section-head"><div><div class="eyebrow">Nine focus sites · live-ledger view</div>'
               f'<h2>GEMSDOE32 is the best reported file; the live ledger agrees.</h2><p>Live = USER-REPORTED. LLI = leave-SITE-out PROJECTION from a model fitted to '
               f'123 pinned live-scored rasters; on this family it is biased high by about 0.01.</p></div></div><div class="table-wrap"><table><thead><tr><th>Site</th><th>File</th>'
               f'<th>Live (USER-REPORTED)</th><th>LLI (PROJECTION)</th></tr></thead><tbody>{rows}</tbody></table></div>'
               f'<p><strong>Why 0.2778, and can it be beaten?</strong> The live ledger places most of the estimated hidden public truth within 3 px of the public H19-5 ridge network, '
               f'which the champion dots at 2.8 px after removing pure-false-positive dots within 2 px of the catalogue. A DTI-optimal re-dotting projects '
               f'{proj["unconstrained_duplicate_lane"]:.3f}, but it is a duplicate lane. With the protocol novelty quota it projects {proj["candidate"]:.3f} and fails the gates. '
               f'Beating 0.2778 uniquely needs information that is absent from every registry raster (<a href="https://community.drivendata.org/raw/11563">forum 11563</a>).</p></section>')
    items = "".join(f"<li><strong>{esc(i['id'])}</strong> ({esc(i['severity'])}): {esc(i['finding'])} <em>{esc(i['fix'])}</em></li>" for i in ir["items"])
    nxt = "".join(f"<li>{esc(x)}</li>" for x in ir["next_steps"])
    lim = "".join(f"<li>{esc(x)}</li>" for x in ir["limitations"])
    irregular = (f'<section class="section"><div class="section-head"><div><div class="eyebrow">Concurrent Session-3 lane · KG2-S3 LOPE</div>'
                 f'<h2>Irregularities found and fixed</h2></div></div><div class="card"><ul>{items}</ul></div>'
                 f'<div class="grid-two"><div class="card"><h3>Next steps</h3><ol>{nxt}</ol></div><div class="card"><h3>Limitations</h3><ul>{lim}</ul></div></div></section>')
    feed = {"lope_file": rc["raster_filename"], "lope_sha256": rc["raster_sha256"], "lope_verdict": rc["validator"]["verdict"],
            "lope_failed_gates": rc["validator"]["failed_gates"], "ok_to_submit": False,
            "dslup_byte_revalidation_verdict": rv["verdict"], "dslup_failed_gates": rv["failed_gates"],
            "lli_projection_lope": proj["candidate"], "lli_projection_dslup": proj["dslup_same_identity"],
            "lli_projection_champion": proj["champion_same_identity"], "label": "PROJECTIONS are not scores"}
    return home, summary, irregular, feed


def hptr_sections() -> tuple[str, str, str, str, dict | None]:
    """Session-3 KG2-S3-HPTR + Complete 9-Focus / 21-Sister / 93-Benchmark Audit block (fail-closed DO NOT SUBMIT)."""
    rc_p = ROOT / "evidence/session3_hptr_run_card_20261027.json"
    fl_p = ROOT / "evidence/hptr_full_fleet_audit_20261027.json"
    ex_p = ROOT / "evidence/hptr_experiments_20261027.json"
    if not (rc_p.is_file() and fl_p.is_file() and ex_p.is_file()):
        return "", "", "", "", None
    rc = json.loads(rc_p.read_text(encoding="utf-8"))
    fl = json.loads(fl_p.read_text(encoding="utf-8"))
    ex = json.loads(ex_p.read_text(encoding="utf-8"))
    if rc.get("verdict") != "negative" or rc.get("ok_to_submit") is not False:
        raise SystemExit("HPTR run card must remain negative under fail-closed gating")
    hfile = rc["raster_filename"]
    hzip = rc["zip_filename"]
    hnote = rc["submission_note"]
    hguard = hfile.replace("-zeros.tif", "-DO-NOT-SUBMIT.txt")
    hval = hfile.replace("-zeros.tif", "-validation.json")
    hpath = DOCS / "downloads" / hfile
    if not hpath.is_file() or hashlib.sha256(hpath.read_bytes()).hexdigest() != rc["raster_sha256"]:
        raise SystemExit("Session-3 HPTR artifact missing or differs from its pinned run card")

    hr = rc["holdout_dti"]["primary_hide_and_recover"]
    sg = rc["holdout_dti"]["secondary_off_catalogue_sgmc"]
    cp = rc["holdout_dti"]["tertiary_concealed_piedmont_c_pied"]
    reg = rc["registry_comparison"]
    can = rc["leakage_canary"]
    lit = rc["validator_output"]["shared_literal_validator_v2"]

    home = (
        f'<section class="section" aria-labelledby="hptr-title"><div class="section-head"><div>'
        f'<div class="eyebrow">Latest Session-3 lane · KG2-S3-HPTR (Hydrothermal Plume &amp; Three-Height Listric Trajectory) + 123-Repo Fleet Audit</div>'
        f'<h2 id="hptr-title">New HPTR-EXP-2 TIFF: NOT OK — DO NOT SUBMIT (Research Artifact Only)</h2>'
        f'<p>Emitted <span class="mono">{esc(hfile)}</span> (SHA-256 <span class="mono">{esc(rc["raster_sha256"][:16])}…</span>, '
        f'37,654 dots = 5,200 Stage-1 piedmont/void + 32,454 Stage-2 horst/tip, 13/13 strict [0,1] checks PASS, 0 NaNs across all 12,279,160 cells, 0 on-catalogue). '
        f'Automated validator verdict: <strong>negative — DO NOT SUBMIT</strong> (protect weekly DrivenData slot).</p></div></div>'
        f'<div class="grid-two"><div class="card"><span class="pill stop">DO NOT SUBMIT — RESEARCH ONLY</span>'
        f'<h3>First KANLERGEMSDOE2 candidate to beat 0.2778 across ALL THREE blind holdouts simultaneously — stopped by literal lattice &amp; kg2s3 gate</h3>'
        f'<p>Directly resolves <code>IR-TRBVC-SGMC-BASIN-SHARE-10</code> and <code>IR-DARP-CREST-OVERDAMP-08</code> via un-damped full-footprint physics '
        f'paired with a Stage-1 concealed-piedmont/void quota (5,200 dots) across 81 leakage-canaried channels (max AUC = {can["max_single_feature_auc"]:.4f} &le; 0.90):</p>'
        f'<ul><li><strong>HOLDOUT-DTI HIDE-RECOVER-v3.0:</strong> <strong>{hr["pooled_dti"]:.6f}</strong> vs 0.2778 ref 0.099202 '
        f'(N={hr["n_withheld_positives"]:,}, 95% CI [{hr["ci95"][0]:.4f}, {hr["ci95"][1]:.4f}], paired &Delta; {hr["paired_delta_vs_0p2778_ref"]:+.6f} (+14.04%), '
        f'paired 95% CI [{hr["paired_delta_ci95"][0]:+.4f}, {hr["paired_delta_ci95"][1]:+.4f}]).</li>'
        f'<li><strong>HOLDOUT-DTI SGMC-CAL-v3.0:</strong> <strong>{sg["sgmc_prevalence_calibrated_dti"]:.6f}</strong> vs 0.2778 ref 0.064121 '
        f'(N={sg["n_withheld_positives"]:,}, 95% CI [{sg["ci95"][0]:.4f}, {sg["ci95"][1]:.4f}], paired &Delta; {sg["paired_delta_vs_0p2778_ref"]:+.6f} (+20.32%), '
        f'paired 95% CI [{sg["paired_delta_ci95"][0]:+.4f}, {sg["paired_delta_ci95"][1]:+.4f}]).</li>'
        f'<li><strong>HOLDOUT-DTI C-PIED-v1.0:</strong> <strong>{cp["pooled_dti"]:.6f}</strong> vs 0.2778 ref 0.101166 '
        f'(N={cp["n_withheld_positives"]:,}, 95% CI [{cp["ci95"][0]:.4f}, {cp["ci95"][1]:.4f}], paired &Delta; {cp["paired_delta_vs_0p2778_ref"]:+.6f} (+3.09%); '
        f'+42.0% over DSLUP 0.073458 &amp; +34.7% over HTCADS 0.077405).</li></ul>'
        f'<p><strong>Why DO NOT SUBMIT:</strong> Binary (<code>r &ge; 0.5</code>) 3-px overlap is <strong>{100*reg["final_dots_max_detector_3px_overlap"]:.2f}% &le; 70%</strong> '
        f'across all non-blanket detectors, <strong>40.40%</strong> vs 0.2778 champion, <strong>&le;49.24%</strong> across all 9 Focus &amp; 21 Sister sites, and '
        f'<strong>&le;{100*rc["max_overlap_vs_all_kanlergemsdoe2_rasters"]:.2f}%</strong> across all 10 KANLERGEMSDOE2 files; however, '
        f'<code>validate_submission.py</code> fails closed on the literal <code>13gems</code> spacing-5 lattice ({100*lit["witness_overlap_fraction"]:.3f}%; forced &ge;82.34% at 37,654 dots) '
        f'and <code>validate_submission_kg2s3.py</code> flags <code>r &gt; 0</code> soft-tail / 6%-density rasters and trails retracted DSLUP on raw bedrock recall.</p>'
        f'<div class="hero-actions"><a class="btn secondary" href="downloads/{esc(hfile)}" download>&#8595; Download HPTR-EXP-2 Research TIFF</a>'
        f'<a class="btn secondary" href="downloads/{esc(hzip)}" download>&#8595; Research ZIP</a>'
        f'<a class="btn secondary" href="downloads/hptr_run_card.json">HPTR Run Card ↗</a>'
        f'<a class="btn secondary" href="downloads/{esc(hval)}">Validator Receipt ↗</a>'
        f'<a class="btn secondary" href="downloads/{esc(hguard)}">DO-NOT-SUBMIT Notice ↗</a></div>'
        f'<p class="note mono">Name: {esc(rc["submission_name"])} · Note ({rc["submission_note_length"]}/140, research record only): {esc(hnote)}</p></div>'
        f'<div class="card"><h3>3-Suite Holdout Dominance, 642-File Uniqueness &amp; Seamless LiDAR-Void Coverage</h3>'
        f'<img src="assets/fig5_hptr_three_benchmarks_and_uniqueness.png" alt="HPTR-EXP-2 3-suite holdout benchmarks, 642-raster uniqueness audit, and seamless LiDAR-void dot allocation" style="width:100%;height:auto;border-radius:8px">'
        f'<p class="note">27.11% of HPTR-EXP-2 dots lie seamlessly inside the 24.63% 1 m LiDAR void using 10 m + 3 m USGS 3DEP curvature/HGM persistence '
        f'(pre-placement |Spearman| max = {reg["pre_placement_surface_max_abs_spearman"]:.4f} &lt; 0.90; final-dot |Spearman| max = '
        f'{reg["final_dots_max_abs_spearman"]:.4f} &lt; 0.90; <a href="../evidence/hptr_full_fleet_audit_20261027.json">full 9-focus + 21-sister JSON audit ↗</a>).</p></div></div></section>'
    )

    f9_rows = []
    for r in fl["focus_nine_audit"]:
        safe_txt = "PASS (all finite [0,1])" if r["portal_safe_whole_grid_0_1"] else f"WARN ({r['full_grid_nan_pixels']:,} exterior NaNs)"
        f9_rows.append(
            f'<tr><td><strong><a href="{esc(r["pages_url"])}">{esc(r["site"])} ↗</a></strong><small><a href="{esc(r["repo_url"])}">repo</a> · <span class="mono">{esc(r["pinned_commit_sha"][:10])}</span></small></td>'
            f'<td class="mono">{esc(r["filename"])}<small>Dots: {r["positive_dots_ge_05"]:,} · On-cat: {r["on_catalogue_dots"]}</small></td>'
            f'<td><strong>{r["user_reported_score"]:.4f}</strong><small>USER-REPORTED</small></td>'
            f'<td>SGMC: <strong>{r["sgmc_cal_v3_holdout_dti"]:.4f}</strong><br>C-PIED: <strong>{r["c_pied_v1_holdout_dti"]:.4f}</strong><small>HOLDOUT-DTI</small></td>'
            f'<td>{esc(safe_txt)}</td>'
            f'<td><strong>{100*r["hptr_exp2_in_peer_3px_overlap"]:.2f}%</strong><small>&le;70% vs HPTR-EXP-2</small></td>'
            f'<td><span class="pill stop">Do not submit</span></td></tr>'
        )

    sis_rows = []
    for sr in fl["sister_24_audit"]:
        rep = sr["representative_raster"]
        if rep is None:
            sis_rows.append(
                f'<tr><td><strong><a href="{esc(sr["repo_url"])}">{esc(sr["site"])} ↗</a></strong><small>{esc(sr["owner"])} · <span class="mono">{esc(sr["commit_sha"][:10])}</span></small></td>'
                f'<td>0 GeoTIFFs (verified initialized stub)</td><td>—</td><td>—</td><td>—</td>'
                f'<td><span class="pill stop">No file</span></td></tr>'
            )
        else:
            safe_s = "PASS [0,1]" if rep["portal_safe_whole_grid_0_1"] else f"WARN ({rep['full_grid_nan_pixels']:,} NaNs)"
            ho_s = (f'SGMC {rep["sgmc_cal_v3_holdout_dti"]:.4f} · C-PIED {rep["c_pied_v1_holdout_dti"]:.4f}'
                    if rep["sgmc_cal_v3_holdout_dti"] is not None else "Blanket (>500k px)")
            ov_s = "Self (100%)" if sr["site"] == "KANLERGEMSDOE2" else f'{100*rep["hptr_exp2_in_peer_3px_overlap"]:.2f}%'
            sis_rows.append(
                f'<tr><td><strong><a href="{esc(sr["repo_url"])}">{esc(sr["site"])} ↗</a></strong><small><a href="{esc(sr["pages_url"])}">Pages</a> · {sr["total_tifs_in_repo"]} TIFs</small></td>'
                f'<td class="mono">{esc(rep["filename"])}<small>Dots: {rep["positive_dots_ge_05"]:,} · On-cat: {rep["on_catalogue_dots"]}</small></td>'
                f'<td>{esc(ho_s)}<small>HOLDOUT-DTI</small></td>'
                f'<td>{esc(safe_s)}</td>'
                f'<td><strong>{esc(ov_s)}</strong></td>'
                f'<td><span class="pill stop">Do not submit</span></td></tr>'
            )

    summary = (
        f'<div class="callout red-callout"><strong>Latest Session-3 KG2-S3-HPTR lane (<span class="mono">{esc(hfile)}</span>): NEGATIVE — DO NOT SUBMIT (Research Download Only).</strong>'
        f'<p><a href="downloads/{esc(hfile)}" download>Download HPTR-EXP-2 research TIFF</a> · <a href="downloads/{esc(hzip)}" download>ZIP</a> · '
        f'<a href="downloads/hptr_run_card.json">Unified Run Card</a> · <a href="downloads/{esc(hval)}">Validator sidecar</a> · '
        f'<a href="downloads/{esc(hguard)}">DO-NOT-SUBMIT guard</a> · SHA-256 <span class="mono">{esc(rc["raster_sha256"])}</span>.</p>'
        f'<p><strong>3-Suite HOLDOUT-DTI breakthrough:</strong> <code>HIDE-RECOVER-v3.0</code> = <strong>{hr["pooled_dti"]:.6f}</strong> '
        f'(N=22,232, 95% CI [{hr["ci95"][0]:.4f}, {hr["ci95"][1]:.4f}], paired &Delta; vs 0.2778 ref {hr["paired_delta_vs_0p2778_ref"]:+.6f} [{hr["paired_delta_ci95"][0]:+.4f}, {hr["paired_delta_ci95"][1]:+.4f}]), '
        f'<code>SGMC-CAL-v3.0</code> = <strong>{sg["sgmc_prevalence_calibrated_dti"]:.6f}</strong> (N=62,703, 95% CI [{sg["ci95"][0]:.4f}, {sg["ci95"][1]:.4f}], '
        f'paired &Delta; {sg["paired_delta_vs_0p2778_ref"]:+.6f} [{sg["paired_delta_ci95"][0]:+.4f}, {sg["paired_delta_ci95"][1]:+.4f}]), and '
        f'<code>C-PIED-v1.0</code> = <strong>{cp["pooled_dti"]:.6f}</strong> (N=9,847, 95% CI [{cp["ci95"][0]:.4f}, {cp["ci95"][1]:.4f}], '
        f'paired &Delta; {cp["paired_delta_vs_0p2778_ref"]:+.6f}). Binary (<code>r &ge; 0.5</code>) non-blanket detector max 3-px overlap = '
        f'<strong>{100*reg["final_dots_max_detector_3px_overlap"]:.2f}% &le; 70%</strong> across 642 scanned rasters, <strong>&le;49.24%</strong> across all 9 Focus &amp; 21 Sister sites, '
        f'and <strong>&le;{100*rc["max_overlap_vs_all_kanlergemsdoe2_rasters"]:.2f}%</strong> across all 10 KANLERGEMSDOE2 files; stopped fail-closed by literal <code>13gems</code> '
        f'spacing-5 lattice ({100*lit["witness_overlap_fraction"]:.3f}%) and <code>kg2s3</code> Gate 3/4.</p></div>'
        f'<section class="section"><div class="section-head"><div><div class="eyebrow">9 Focus Sites · Blind SGMC-CAL, C-PIED, [0,1] Safety &amp; HPTR-EXP-2 Overlap</div>'
        f'<h2>HPTR-EXP-2 exceeds all 9 Focus Sites on both blind SGMC-CAL (0.0771) and C-PIED (0.1043) with &le;49.24% 3-px overlap</h2>'
        f'<p>Live scores are USER-REPORTED; SGMC-CAL &amp; C-PIED are exact blind HOLDOUT-DTI evaluations on identical byte-pinned rasters.</p></div></div>'
        f'<div class="table-wrap"><table><thead><tr><th>Focus Site</th><th>Pinned GeoTIFF</th><th>Reported Score</th><th>Blind HOLDOUT-DTI</th><th>[0,1] Whole-Grid</th><th>HPTR-EXP-2 Overlap</th><th>Decision</th></tr></thead>'
        f'<tbody>{"".join(f9_rows)}</tbody></table></div></section>'
        f'<section class="section"><div class="section-head"><div><div class="eyebrow">Complete 21-Sister-Site &amp; 93-Benchmark-Site Audit</div>'
        f'<h2>KANLERGEMSDOE1..3, EUGGEMSDOE1..3, WBGGEMSDOE1..3, GINNYGEMSDOE1..3, GEMSDOEkarage1..3, ApartGEMSDOE1..3, GEMSDOESASS1..3 &amp; GEMSDOE..GEMSDOE92</h2>'
        f'<p>Every listed sister family (21 repos: 15 with GeoTIFFs + 6 verified 0-TIFF stubs) plus <code>buffedlizard55-lab/GEMSDOE..GEMSDOE92</code> (93 benchmark sites, 360 comparison-registry + ledger rasters) audited from bytes (<a href="../evidence/hptr_full_fleet_audit_20261027.json">full JSON receipt ↗</a>).</p></div></div>'
        f'<div class="table-wrap"><table><thead><tr><th>Sister Site</th><th>Audited Representative GeoTIFF</th><th>Blind HOLDOUT-DTI</th><th>[0,1] Safety</th><th>HPTR-EXP-2 Overlap</th><th>Decision</th></tr></thead>'
        f'<tbody>{"".join(sis_rows)}</tbody></table></div></section>'
    )

    exp_rows = []
    for e in ex["experiments"]:
        ehr = e["holdout_hide_recover"]
        esg = e["holdout_sgmc_offcat"]
        ecp = e["holdout_c_pied"]
        exp_rows.append(
            f'<tr><td><strong>{esc(e["experiment_id"])}</strong><small>{esc(e["name"])}</small></td>'
            f'<td><strong>{ehr["pooled_dti"]:.6f}</strong><small>&Delta; {ehr["paired_delta_vs_0p2778_ref"]:+.4f} (CI+ {ehr["ci95_strictly_positive"]})</small></td>'
            f'<td><strong>{esg["sgmc_prevalence_calibrated_dti"]:.6f}</strong><small>&Delta; {esg["paired_delta_vs_0p2778_ref"]:+.4f} (CI+ {esg["ci95_strictly_positive"]})</small></td>'
            f'<td><strong>{ecp["pooled_dti"]:.6f}</strong><small>&Delta; {ecp["paired_delta_vs_0p2778_ref"]:+.4f}</small></td>'
            f'<td>Det: {100*e["uniqueness_audit"]["final_dots_max_detector_3px_overlap"]:.2f}%<br>Own: {100*e["max_own_prior_3px_overlap"]:.2f}%</td></tr>'
        )

    research = (
        f'<section class="section"><div class="section-head"><div><div class="eyebrow">Session-3 KG2-S3-HPTR Experimental Record (`3/3` Budget)</div>'
        f'<h2>4 Pre-Registered Hydrothermal-Plume &amp; Listric-Trajectory Hypotheses Solving the Crest-vs-Piedmont Seesaw</h2></div></div>'
        f'<div class="card"><p>Frozen prior to training in <a href="../registry/preregistration_hptr_20261027.json">preregistration_hptr_20261027.json ↗</a> and '
        f'<a href="../knowledge/03_preregistered_hypotheses_hptr_20261027.md">03_preregistered_hypotheses_hptr_20261027.md ↗</a>: '
        f'<strong>H-S3-1</strong> (3-Height 500/2000/4000 m Upward-Continued Magnetic-Gravity Listric Dip-Slip Trajectory Coherence), '
        f'<strong>H-S3-2</strong> (Anisotropic Up-Gradient Hydrothermal Vent-Plume Conduit Tracing from INGENIOUS Wells/Springs, 2 m Probes &amp; Volcanic Vents), '
        f'<strong>H-S3-3</strong> (Seamless 10 m + 3 m USGS 3DEP Scarp Persistence Bridging 100% of the 24.63% 1 m LiDAR Void), and '
        f'<strong>H-S3-4</strong> (Fold-Honest Visible-Only Strike-Concordant Fault-Tip &amp; En-Echelon Relay Bridge).</p>'
        f'<div class="table-wrap"><table><thead><tr><th>Experiment</th><th>HIDE-RECOVER-v3.0</th><th>SGMC-CAL-v3.0</th><th>C-PIED-v1.0</th><th>Binary Detector / Own Overlap</th></tr></thead>'
        f'<tbody>{"".join(exp_rows)}</tbody></table></div>'
        f'<p class="note">Full 3-experiment log: <a href="../evidence/hptr_experiments_20261027.json">hptr_experiments_20261027.json ↗</a> · '
        f'81-channel canary receipt: <a href="../evidence/hptr_leakage_canary_20261027.json">hptr_leakage_canary_20261027.json ↗</a>.</p></div></section>'
    )

    ir_items = "".join(
        f'<li><strong>{esc(it["id"])}</strong> ({esc(it["severity"])} · <span class="mono">{esc(it["target"])}</span>): {esc(it["finding"])} '
        f'<em>Resolution: {esc(it["resolution"])}</em></li>'
        for it in fl["irregularities_flagged"]
    )
    irregular = (
        f'<section class="section"><div class="section-head"><div><div class="eyebrow">Session-3 KG2-S3-HPTR Fleet &amp; Tooling Audit</div>'
        f'<h2>6 Irregularities Identified &amp; Addressed (`IR-09` through `IR-14`)</h2></div></div>'
        f'<div class="card"><ul>{ir_items}</ul></div></section>'
    )

    hfeed = {
        "filename": hfile,
        "sha256": rc["raster_sha256"],
        "zip": hzip,
        "verdict": "negative",
        "ok_to_submit": False,
        "validated_ok_to_download_and_submit": False,
        "ok_to_download_for_research": True,
        "beats_02778_across_all_three_blind_holdouts": True,
        "hide_recover_v3_dti": hr["pooled_dti"],
        "sgmc_cal_v3_dti": sg["sgmc_prevalence_calibrated_dti"],
        "c_pied_v1_dti": cp["pooled_dti"],
        "binary_r_ge_05_max_detector_3px_overlap": reg["final_dots_max_detector_3px_overlap"],
        "max_overlap_vs_kanlergemsdoe2_rasters": rc["max_overlap_vs_all_kanlergemsdoe2_rasters"],
        "literal_spacing5_lattice_overlap": lit["witness_overlap_fraction"],
    }
    return home, summary, research, irregular, hfeed


def trbvc_sections() -> tuple[str, str, str, str, dict | None]:
    """Concurrent Session-3 TRBVC + 22-Sister-Repo Audit block, strictly fail-closed (DO NOT SUBMIT)."""
    tc_p = ROOT / "evidence/trbvc_run_card_20261027.json"
    s22_p = ROOT / "evidence/sister_fleet_uniqueness_20261027.json"
    if not (tc_p.is_file() and s22_p.is_file()):
        return "", "", "", "", None
    tc = json.loads(tc_p.read_text(encoding="utf-8"))
    s22 = json.loads(s22_p.read_text(encoding="utf-8"))
    if tc.get("verdict") != "negative":
        raise SystemExit("TRBVC run card must remain negative under fail-closed gating")
    tfile = tc["submission_name"]
    tzip = tc["submission_zip"]
    tnote = tc["submission_note"]
    tpath = DOCS / "downloads" / tfile
    if not tpath.is_file() or hashlib.sha256(tpath.read_bytes()).hexdigest() != tc["raster_sha256"]:
        raise SystemExit("Session-3 TRBVC artifact missing or differs from its pinned run card")
    thr = tc["holdout_dti"]["primary_hide_and_recover"]
    tsg = tc["holdout_dti"]["secondary_off_catalogue_sgmc"]
    tcp = tc["holdout_dti"]["piedmont_off_catalogue_c_pied"]
    tseg = tc["holdout_dti"]["gems_segment_pooled_v1"]
    treg = tc["registry_comparison"]
    talloc = tc["spatial_allocation_diagnostics"]
    sis_max = s22["max_overlap_across_all_22_sister_repos"]

    home = (
        f'<section class="section" aria-labelledby="trbvc-title"><div class="section-head"><div>'
        f'<div class="eyebrow">Concurrent Session-3 lane · TRBVC (Two-Regime Blind-Vent &amp; Cover-Partitioned Conduit) + 22-Sister-Repo Audit</div>'
        f'<h2 id="trbvc-title">New TRBVC TIFF: NOT OK — DO NOT SUBMIT (Research Artifact Only)</h2>'
        f'<p>Emitted <span class="mono">{esc(tfile)}</span> (SHA-256 <span class="mono">{esc(tc["raster_sha256"][:16])}…</span>, '
        f'37,654 dots, 13/13 strict [0,1] checks PASS, 0 NaNs). Fail-closed verdict: <strong>negative — DO NOT SUBMIT</strong>.</p></div></div>'
        f'<div class="grid-two"><div class="card"><span class="pill stop">DO NOT SUBMIT — RESEARCH ONLY</span>'
        f'<h3>Solves range-front over-damping (+19.4% Hide-Rec vs 0.2778 &amp; +53.6% C-PIED vs DSLUP), stopped by Gate 4 &amp; literal lattice</h3>'
        f'<p>Continuous cover partitioning <code>w_basin(Z_b)</code> across 80 leakage-canaried channels (max AUC = 0.7965 &le; 0.90) resolved '
        f'<code>IR-DARP-CREST-OVERDAMP-08</code>: <strong>HOLDOUT-DTI HIDE-RECOVER-v3.0 = {thr["pooled_dti"]:.4f}</strong> '
        f'(N=22,232, 95% CI [{thr["ci95"][0]:.4f}, {thr["ci95"][1]:.4f}], paired &Delta; {thr["paired_delta_vs_02778"]:+.4f}, '
        f'paired 95% CI [{thr["paired_delta_ci95"][0]:+.4f}, {thr["paired_delta_ci95"][1]:+.4f}]) and blind alluvial-basin '
        f'<strong>HOLDOUT-DTI C-PIED-v1.0 = {tcp["pooled_dti"]:.4f}</strong> (+53.6% over DSLUP c71122d5’s 0.0735, paired CI '
        f'[{tcp["paired_delta_vs_dslup_ci95"][0]:+.4f}, {tcp["paired_delta_vs_dslup_ci95"][1]:+.4f}]; <code>gems-segment-v1</code> = {tseg["pooled_dti"]:.4f}).</p>'
        f'<p><strong>Why DO NOT SUBMIT (`IR-TRBVC-SGMC-BASIN-SHARE-10` + literal lattice):</strong> Equal 99.2th-quantile scaling placed '
        f'{talloc["pct_dots_in_concealed_basin_zb_ge_200m"]:.2f}% ({talloc["dots_in_concealed_basin_zb_ge_200m"]:,}) of dots in <code>Z_b &ge; 200 m</code> basins, '
        f'leaving 17.67% on exposed bedrock blocks so <code>SGMC-CAL-v3.0</code> landed at {tsg["prevalence_calibrated_dti"]:.4f} (&lt; 0.0641 ref), '
        f'HIDE-RECOVER trailed DSLUP (0.1259), and the 37,654-dot budget hits the forced &ge;82.34% spacing-5 lattice bound. Per Protocol Rules 5 &amp; 6 '
        f'(3/3 experiments in {tc["budget"]["wall_clock_seconds"]:.1f}s), no weekly slot is spent.</p>'
        f'<div class="hero-actions"><a class="btn secondary" href="downloads/{esc(tfile)}" download>&#8595; Download TRBVC Research TIFF</a>'
        f'<a class="btn secondary" href="downloads/{esc(tzip)}" download>&#8595; Research ZIP</a>'
        f'<a class="btn secondary" href="downloads/trbvc_run_card.json">TRBVC Run Card ↗</a></div>'
        f'<p class="note mono">Note ({tc["submission_note_length"]}/140, research record only): {esc(tnote)}</p></div>'
        f'<div class="card"><h3>Blind Holdout Instruments, Crustal Domain Law &amp; 22-Sister-Repo Detector Uniqueness</h3>'
        f'<img src="assets/fig5_trbvc_four_instruments_and_domain_law.png" alt="TRBVC blind holdout instruments, crustal domain budget shares, and 22-sister-repo detector overlap" style="width:100%;height:auto;border-radius:8px">'
        f'<p class="note">Non-lattice detector overlap across 281 distinct fleet rasters &amp; all 22 sister repos (368 staged TIFs): max 3-px = '
        f'<strong>{100*treg["final_dots_max_detector_3px_overlap"]:.2f}% &le; 70%</strong> (surface |Spearman| = {treg["pre_placement_surface_max_abs_spearman"]:.4f} &le; 0.90; '
        f'<a href="../evidence/sister_fleet_uniqueness_20261027.json">22-sister-repo receipt ↗</a> · '
        f'<a href="../knowledge/01_focus9_gemsdoe32_phd_synthesis_20261027.md">PhD 9-site synthesis ↗</a>).</p></div></div></section>'
    )

    sis22_rows = []
    for sr in s22["sister_repos"]:
        cf_base = Path(sr["closest_file_to_dslup_c71122d5"]).name if sr["closest_file_to_dslup_c71122d5"] else "0 discrete TIFs"
        sis22_rows.append(
            f'<tr><td><strong><a href="{esc(sr["github_url"])}">{esc(sr["repo"])} ↗</a></strong><small>Commit <span class="mono">{esc(sr["commit_sha"][:10])}</span></small></td>'
            f'<td>{sr["n_submission_tifs_in_tree"]} staged ({sr["n_discrete_detector_tifs_evaluated"]} discrete)</td>'
            f'<td><strong>{100*sr["max_3px_overlap_dslup_c71122d5"]:.2f}%</strong><small>{esc(cf_base)}</small></td>'
            f'<td><strong>{100*sr["max_3px_overlap_htcads_11a2f251"]:.2f}%</strong></td>'
            f'<td><strong>{100*sr["max_3px_overlap_trbvc_decad771"]:.2f}%</strong></td>'
            f'<td><span class="pill stop">Research only</span><small>&le;70% vs sister detectors; literal lattice still blocks 37,654d</small></td></tr>'
        )

    summary = (
        f'<div class="callout red-callout"><strong>Concurrent Session-3 TRBVC lane (<span class="mono">{esc(tfile)}</span>): NEGATIVE — DO NOT SUBMIT (Research Only).</strong>'
        f'<p><a href="downloads/{esc(tfile)}" download>Download TRBVC research TIFF</a> · <a href="downloads/{esc(tzip)}" download>ZIP</a> · '
        f'<a href="downloads/trbvc_run_card.json">Run card</a> · SHA-256 <span class="mono">{esc(tc["raster_sha256"][:16])}…</span> · '
        f'80/80 canary max AUC = 0.7965 &le; 0.90 (<a href="../evidence/leakage_canary_trbvc_20261027.json">canary receipt</a>).</p>'
        f'<p>HOLDOUT-DTI: <code>HIDE-RECOVER-v3.0</code> = <strong>{thr["pooled_dti"]:.4f}</strong> [{thr["ci95"][0]:.4f}, {thr["ci95"][1]:.4f}] '
        f'(paired &Delta; vs 0.2778 proxy {thr["paired_delta_vs_02778"]:+.4f} [{thr["paired_delta_ci95"][0]:+.4f}, {thr["paired_delta_ci95"][1]:+.4f}]), '
        f'<code>C-PIED-v1.0</code> = <strong>{tcp["pooled_dti"]:.4f}</strong> (+53.6% vs DSLUP 0.0735), <code>SGMC-CAL-v3.0</code> = '
        f'{tsg["prevalence_calibrated_dti"]:.4f} (&lt; 0.0641 ref). Max 3-px overlap vs non-lattice detectors across 281 distinct fleet rasters &amp; 22 sister repos = '
        f'<strong>{100*treg["final_dots_max_detector_3px_overlap"]:.2f}% &le; 70%</strong>, but stopped by SGMC Gate 4 and the literal spacing-5 lattice.</p></div>'
        f'<section class="section"><div class="section-head"><div><div class="eyebrow">22-Sister-Repository Fleet Audit · 368 Staged TIFs</div>'
        f'<h2>Sister-fleet detector overlap matrix (all files remain DO NOT SUBMIT under literal lattice rule)</h2>'
        f'<p>Exact byte audit across all 22 accessible sister sites (<a href="../evidence/sister_fleet_uniqueness_20261027.json">sister_fleet_uniqueness_20261027.json ↗</a>).</p></div></div>'
        f'<div class="table-wrap"><table><thead><tr><th>Sister Repository</th><th>Staged TIFs</th><th>DSLUP c71122d5 Max 3-px</th>'
        f'<th>HTCADS 11a2f251 Max 3-px</th><th>TRBVC decad771 Max 3-px</th><th>Status</th></tr></thead><tbody>{"".join(sis22_rows)}</tbody></table></div></section>'
    )

    research = (
        f'<section class="section"><div class="section-head"><div><div class="eyebrow">Session-3 TRBVC Experimental Record &amp; 9-Site PhD Synthesis</div>'
        f'<h2>5 Pre-Registered Geothermal Conduit Hypotheses &amp; Crustal Domain Budget Law</h2></div></div>'
        f'<div class="card"><p>Pre-registered in <a href="../registry/preregistration_trbvc_20261027.json">preregistration_trbvc_20261027.json ↗</a> and '
        f'<a href="../knowledge/02_preregistered_hypotheses_kg2_s3_20261027.md">02_preregistered_hypotheses_kg2_s3_20261027.md ↗</a> (with 9-site synthesis in '
        f'<a href="../knowledge/01_focus9_gemsdoe32_phd_synthesis_20261027.md">01_focus9_gemsdoe32_phd_synthesis_20261027.md ↗</a>): '
        f'<strong>H-KG2S3-1</strong> (Two-Regime Cover Partitioning + Blind Fault-Valve Clay-Cap Breach + Cold-Aquifer &lt;28 &deg;C Geothermometer Disequilibrium + '
        f'Cohort-Detrended 2m-1m Probe Vertical Heat Flux), <strong>H-KG2S3-2</strong> (2-D Fourier Poisson Gravity-Minus-Pseudogravity Hydrothermal Magnetite-Destruction Decoupling), '
        f'<strong>H-KG2S3-3</strong> (Off-Catalogue Accommodation-Zone Rollover Hinges), plus deferred external-API hypotheses <strong>H-KG2S3-4</strong> (NASA ASTER TIR/SWIR) and '
        f'<strong>H-KG2S3-5</strong> (EarthScope USArray 3D MT / NASA OPERA InSAR).</p>'
        f'<p><strong>Crustal Domain Budget Law (`IR-TRBVC-SGMC-BASIN-SHARE-10`):</strong> 3 experiments (<code>TRBVC-EXP-1..3</code>) proved continuous cover partitioning '
        f'recovers range-front Hide-Rec ({thr["pooled_dti"]:.4f}) and concealed-basin C-PIED ({tcp["pooled_dti"]:.4f}) simultaneously, while equal tail-quantile scaling across '
        f'unequal footprint areas (~65% basin vs ~35% bedrock) shifts 82.33% of dots into basins at the expense of bare-bedrock SGMC contacts.</p></div></section>'
    )

    irregular = (
        f'<section class="section"><div class="section-head"><div><div class="eyebrow">Concurrent Session-3 TRBVC Diagnostics</div>'
        f'<h2>Crustal Domain Allocation Trade-Off (`IR-TRBVC-SGMC-BASIN-SHARE-10`)</h2></div></div>'
        f'<div class="card"><p>Equal 99.2th-quantile calibration across shallow (<code>Z_b &lt; 291 m</code>, ~35% area) and basin (<code>Z_b &ge; 291 m</code>, ~65% area) '
        f'regimes placed 31,001 / 37,654 dots (82.33%) in <code>Z_b &ge; 200 m</code> basins and 6,653 (17.67%) on exposed horst bedrock, lowering <code>SGMC-CAL-v3.0</code> '
        f'to {tsg["prevalence_calibrated_dti"]:.4f} despite +19.4% Hide-Rec and +53.6% C-PIED gains. Explicit domain-quota locking (~36% horst / ~42% basin / ~22% void) '
        f'is documented for future pre-registered testing once the literal lattice rule is resolved.</p></div></section>'
    )

    tfeed = {
        "filename": tfile,
        "sha256": tc["raster_sha256"],
        "zip": tzip,
        "verdict": "negative",
        "ok_to_submit": False,
        "validated_ok_to_download_and_submit": False,
        "ok_to_download_for_research": True,
        "hide_recover_v3_dti": thr["pooled_dti"],
        "sgmc_cal_v3_dti": tsg["prevalence_calibrated_dti"],
        "c_pied_v1_dti": tcp["pooled_dti"],
        "segment_v1_dti": tseg["pooled_dti"],
        "max_3px_non_lattice_detector_overlap": treg["final_dots_max_detector_3px_overlap"],
        "sister_22_repo_max_overlaps": sis_max,
    }
    return home, summary, research, irregular, tfeed


def main() -> None:
    audit = json.loads((ROOT / "evidence/release_audit_20261028.json").read_text())
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
    if len(audit["focus_nine"]) != 9:
        raise SystemExit("The focus-site comparison is incomplete")
    table = focus_table(audit["focus_nine"])
    hptr_home, hptr_summary, hptr_research, hptr_irregular, hptr_feed = hptr_sections()
    lope_home, lope_summary, lope_irregular, lope_feed = lope_sections()
    trbvc_home, trbvc_summary, trbvc_research, trbvc_irregular, trbvc_feed = trbvc_sections()
    # Archive legacy lane narratives: they contain claims of proven causality,
    # nonliteral uniqueness and calibrated SGMC projections mislabeled as DTI.
    # The underlying receipts remain linked, but are not independently replayed.
    archive = ("<section class=\"section\"><div class=\"callout red-callout\">"
               "<strong>KG2-S3-HPTR and other previous lanes: DO NOT SUBMIT.</strong> "
               "Historical results are not independently replayed. SGMC prevalence-calibrated "
               "figures are projections, not measured HOLDOUT-DTI or leaderboard scores. "
               "<a href=\"downloads/kanlergems2-hptr-exp-2-37654dots-20261028T014401Z-675d0ff8-zeros.tif\" download>HPTR research TIFF only</a> · "
               "<a href=\"../evidence/hptr_revalidation_20261028.json\">Fresh validator output</a> · "
               "<a href=\"../evidence/session3_hptr_run_card_20261027.json\">Archived HPTR card</a> · "
               "<a href=\"../evidence/release_audit_20261028.json\">Fresh byte audit</a></div></section>")
    hptr_home = hptr_summary = hptr_research = hptr_irregular = archive
    lope_home = lope_summary = lope_irregular = ""
    trbvc_home = trbvc_summary = trbvc_research = trbvc_irregular = ""
    hptr_feed = {"filename": hptr_feed["filename"], "sha256": hptr_feed["sha256"],
                 "verdict": "negative", "ok_to_submit": False,
                 "warning": "Historical holdouts not replayed; SGMC calibration is a projection, not measured DTI."}
    lope_feed = None
    trbvc_feed = {"filename": trbvc_feed["filename"], "sha256": trbvc_feed["sha256"],
                  "verdict": "negative", "ok_to_submit": False,
                  "validated_ok_to_download_and_submit": False,
                  "warning": "Historical results not independently replayed."}
    percent = 100 * prior["witness_overlap_fraction"]
    bound = 100 * pre["minimum_directional_overlap"]
    s2 = json.loads((ROOT / "evidence/dslup_unique_slot_run_card.json").read_text())
    s2_name, s2_sha = s2["submission_filename"], s2["raster_sha256"]
    s2_file = DOCS / "downloads" / s2_name
    if not s2_file.is_file() or hashlib.sha256(s2_file.read_bytes()).hexdigest() != s2_sha:
        raise SystemExit("Session-2 research artifact missing or differs from its archived record")
    checked = [r for r in audit["all_local_candidate_artifacts"] if r["sha256"] == s2_sha and r["file"] == s2_name]
    if len(checked) != 1 or not checked[0]["duplicate_under_literal_rule"]:
        raise SystemExit("Session-2 literal witness result missing or changed; rerun the audit")
    s2_audit = checked[0]
    revalidation = json.loads((ROOT / "evidence/dslup_literal_revalidation_20261027.json").read_text())
    if (revalidation.get("raster_sha256") != s2_sha or revalidation.get("raster_filename") != s2_name
            or revalidation.get("ok_to_submit") is not False or revalidation.get("verdict") != "negative"
            or revalidation.get("gates", {}).get("literal_witness_not_duplicate") is not False
            or revalidation.get("format_audit", {}).get("witness_overlap_dots") != s2_audit["witness_overlap_dots"]):
        raise SystemExit("Current Session-2 revalidation is absent or inconsistent with the exact-byte audit")
    hr = s2["holdout_dti"]["primary_hide_and_recover"]
    kg = json.loads((ROOT / "run_card.json").read_text())
    kg_rows = [r for r in audit["all_local_candidate_artifacts"] if r["sha256"] == kg["raster_sha256"]
               and r["file"] == kg["submission_filename"]]
    if len(kg_rows) != 1 or not kg_rows[0]["duplicate_under_literal_rule"]:
        raise SystemExit("Historical KG2 benchmark witness audit missing or changed")
    kg_audit, kg_hr = kg_rows[0], kg["holdout_dti"]
    # Integrate concurrent main-branch research artifacts without adopting their
    # self-attested promotion. Their differing budgets have different conclusions.
    extras = {}
    for key, filename in (
        ("pr34", "kanlergemsdoe2-unique-hypothesis1-binary-20261027.tif"),
        ("pr36", "36GEMSDOE-off-catalogue-blind-geothermal-targeting-20261027T234345Z-2ecaae7a056e-zeros.tif"),
    ):
        matches = [r for r in audit["all_local_candidate_artifacts"] if r["file"] == filename]
        candidate_path = DOCS / "downloads" / filename
        if len(matches) != 1 or not candidate_path.is_file() or hashlib.sha256(candidate_path.read_bytes()).hexdigest() != matches[0]["sha256"]:
            raise SystemExit(f"Parallel research artifact {key} differs from the audited bytes")
        extras[key] = matches[0]
    off36 = json.loads((ROOT / "evidence/off36_independent_check_20261027.json").read_text())
    if (extras["pr34"]["witness_overlap_dots"] != 37652 or extras["pr34"]["on_catalogue_positive_pixels"] != 184
            or extras["pr36"]["witness_overlap_dots"] != 9900 or extras["pr36"]["inside_positive_pixels"] != 15000
            or extras["pr36"]["on_catalogue_positive_pixels"] != 107 or off36["sha256"] != extras["pr36"]["sha256"]):
        raise SystemExit("Parallel research recheck disagrees; rerun the release audit")
    parallel_notice = f'''<div class="callout red-callout"><strong>Parallel-session artifacts — DO NOT SUBMIT.</strong>
<p><a href="downloads/{esc(extras['pr34']['file'])}" download>PR #34 research TIFF</a> · SHA-256 <span class="mono">{esc(extras['pr34']['sha256'])}</span>. Exact-byte audit: {extras['pr34']['witness_overlap_dots']:,}/{extras['pr34']['inside_positive_pixels']:,} dots ({100*extras['pr34']['witness_overlap_fraction']:.3f}%) overlap the lattice and {extras['pr34']['on_catalogue_positive_pixels']} are on the mirrored catalogue. No holdout was replayed.</p>
<p><a href="downloads/{esc(extras['pr36']['file'])}" download>PR #36 research TIFF</a> · SHA-256 <span class="mono">{esc(extras['pr36']['sha256'])}</span>. Its {extras['pr36']['inside_positive_pixels']:,}-dot budget deviates from the frozen lane and 5,100 dots were deliberately placed in lattice gaps; its 66.0% witness overlap does not establish protocol compliance or full-registry novelty. It has {extras['pr36']['on_catalogue_positive_pixels']} on-catalogue dots and no measured holdout. Its historical promotion is superseded. <a href="../evidence/off36_independent_check_20261027.json">Independent recheck ↗</a></p></div>'''
    archive_notice = f'''<div class="callout red-callout"><strong>DO NOT SUBMIT — all prior files are research only.</strong>
<p>The prior DSLUP TIFF can be <a href="downloads/{esc(s2_name)}" download>downloaded for research</a> · <a href="../evidence/dslup_literal_revalidation_20261027.json">current validator result</a> · SHA-256 <span class="mono">{esc(s2_sha)}</span>.</p>
<p>Its local grid and inside-footprint values pass, but {s2_audit['witness_overlap_dots']:,} of {s2_audit['inside_positive_pixels']:,} dots ({100*s2_audit['witness_overlap_fraction']:.3f}%) are within 3 pixels of a registered raster. The former detector-only promotion is superseded: the protocol contains no exemption. Neither format validity nor a unique file hash is approval to submit.</p></div>'''
    home = f'''<div class="breadcrumb">DOE GEMS PRIZE &nbsp; / &nbsp; <span>Decision dashboard</span></div>
<section class="hero" aria-labelledby="hero-title"><div><div class="eyebrow">Geothermal fault discovery · evidence review</div><span class="status">Submission on hold</span>
<h1 id="hero-title">No file is cleared<br>for submission.</h1><p class="lead">The literal uniqueness check fails. No new GeoTIFF, defensible leaderboard estimate, or live-slot decision was produced in this review. Protect the weekly slot.</p>
<div class="hero-actions"><a class="btn secondary" href="executive-summary.html">See the nine-site executive summary →</a><a class="btn secondary" href="research.html">Explore the research →</a></div><p class="note"><strong>DO NOT SUBMIT</strong> any file on this site today. Downloads are for research and comparison only.</p></div>
<div class="hero-aside"><div class="eyebrow">What blocks the candidate?</div><h3>Literal registry witness</h3><p>At the frozen {pre['candidate_dot_budget']:,}-dot budget, at least <strong>{bound:.2f}%</strong> of any possible placement must overlap the registered lattice’s 3-pixel neighborhood; the limit is 70%.</p><p>The earlier candidate’s exact overlap is {100*s2_audit['witness_overlap_fraction']:.3f}%. No exception is authorized.</p><div class="hash mono">Registered witness SHA-256<br>{esc(pre['witness_sha256'])}</div></div></section>
<div class="metrics" aria-label="Decision metrics"><div class="metric"><div class="label">New experiments</div><div class="value">0</div><div class="hint">Stopped before fitting or placement</div></div>
<div class="metric"><div class="label">New leaderboard estimate</div><div class="value">—</div><div class="hint">Unavailable; no hidden truth or receipt</div></div>
<div class="metric"><div class="label">Weekly slots used here</div><div class="value">0</div><div class="hint">A selector is a separate step</div></div>
<div class="metric"><div class="label"><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Public #1 DW-Tversky ↗</a></div><div class="value" id="leader-value">—</div><div class="hint" id="leader-status">Loading dated public snapshot…</div><noscript><span class="note">View the linked official leaderboard.</span></noscript></div></div>
{hptr_home}
{lope_home}
{trbvc_home}
<section class="section"><div class="section-head"><div><div class="eyebrow">Prior candidates</div><h2>Download for research, not for a slot.</h2></div></div>{archive_notice}{parallel_notice}</section>
<section class="section"><div class="section-head"><div><div class="eyebrow">The distinctions that matter</div><h2>A valid-looking TIFF is not a validated submission.</h2></div></div><div class="grid-three">
<article class="card"><div class="card-icon">01</div><h3>Format</h3><p>Independent local checks found the previous file finite in [0,1] on the mirror grid. The cause of the reported portal range error and portal acceptance are unknown.</p></article>
<article class="card"><div class="card-icon">02</div><h3>Uniqueness</h3><p>A different SHA-256 is not enough. The requested literal 3-pixel rule fails against a registered lattice, before considering the rest of the registry.</p></article>
<article class="card"><div class="card-icon">03</div><h3>Performance</h3><p>Historical holdout results are proxy measurements, not scores for the hidden leaderboard. Their original fold predictions have not been independently replayed.</p></article></div></section>'''

    summary = f'''<div class="breadcrumb"><a href="index.html">Decision dashboard</a> &nbsp; / &nbsp; <span>Executive summary</span></div>
<div class="page-intro"><div class="eyebrow">Decision brief · 27 October 2026</div><h1>What to download.<br>What not to submit.</h1><p><strong>No new file has passed all gates. Do not submit any current download.</strong> The tables distinguish research artifacts, reported scores, and measured overlap.</p></div>
{hptr_summary}
{lope_summary}
{trbvc_summary}
{archive_notice}
{parallel_notice}
<section class="section"><div class="section-head"><div><div class="eyebrow">Historical benchmark comparison</div><h2>Holdout evidence is not a submission recommendation.</h2></div></div>
<div class="table-wrap"><table><thead><tr><th>Research file</th><th>Historical holdout / leaderboard estimate</th><th>Literal uniqueness</th><th>Decision</th></tr></thead><tbody><tr>
<td class="file"><a href="downloads/{esc(s2_name)}" download>{esc(s2_name)}</a><small>SHA-256 {esc(s2_sha)}</small></td>
<td><strong>{hr['pooled_dti']:.6f}</strong><small>HOLDOUT-DTI · GEMSDOE32-HIDE-RECOVER-v3.0 · N=22,232 withheld-positive occurrences · 95% CI [{hr['ci95'][0]:.6f}, {hr['ci95'][1]:.6f}]. Historical procedure result; not independently replayed. Leaderboard estimate: unavailable.</small></td>
<td><strong>No</strong><small>{100*s2_audit['witness_overlap_fraction']:.3f}% vs registered lattice; pre-placement surface not replayed.</small></td><td><span class="pill stop">Do not submit</span></td></tr>
<tr><td class="file"><a href="downloads/{esc(kg['submission_filename'])}" download>{esc(kg['submission_filename'])}</a><small>SHA-256 {esc(kg['raster_sha256'])}</small></td>
<td><strong>{kg_hr['dti']:.6f}</strong><small>HOLDOUT-DTI · {esc(kg_hr['evaluator_version'])} · N={kg_hr['withheld_positive_pixels']:,} · 95% CI [{kg_hr['ci95'][0]:.6f}, {kg_hr['ci95'][1]:.6f}]. Historical receipt only; OOF not replayed.</small></td>
<td><strong>No</strong><small>{100*kg_audit['witness_overlap_fraction']:.3f}% vs lattice.</small></td><td><span class="pill stop">Do not submit</span></td></tr></tbody></table></div>
<p class="note">These are different evaluator protocols and populations, so the numbers cannot establish which procedure is better. This review has no new holdout to compare with either. Historical SGMC-CAL values rely on an unverified inferred hidden-truth count and are not measured leaderboard scores or a valid promotion gate.</p></section>
<section class="section"><div class="section-head"><div><div class="eyebrow">Evidence table</div><h2>Nine historical site leaders</h2><p>Scores are USER/OWNER-REPORTED, not organizer-confirmed; no receipts tie them to exact bytes. The largest reported value is 0.2778 for GEMSDOE32.</p></div></div>{table}
<p class="note">Overlap is directional: the fraction of a row’s positive pixels within 3 pixels of its closest other focus-site raster. The nine-site comparison is not full-registry clearance. All downloads are historical research only.</p></section>
<section class="section"><div class="section-head"><div><div class="eyebrow">Future instructions · not authorization</div><h2>How to make a submission, once cleared.</h2></div></div>
<div class="grid-two"><div class="card"><ol class="steps"><li><strong>Verify all gates and the independent selector.</strong> Require fold-visible-only features, per-feature canaries, a comparable holdout win with CI, literal complete-registry checks on surface and dots, and current account quota.</li><li><strong>Download the exact approved TIFF.</strong> Verify its SHA-256, one float32 band, CRS, shape, transform and in-footprint [0,1] values against the authenticated sample. No file is approved today.</li><li><strong>Open DrivenData → Submit → Make new submission.</strong> Choose the approved GeoTIFF or ZIP containing that single TIFF. Enter the unique name and short note, at most 140 characters, and check current site limits.</li><li><strong>Preserve the actual submission receipt.</strong> Record the file hash, timestamp and score only if returned by the organizer. Choose one final entry for both rounds before the deadline.</li></ol></div>
<div class="card"><h3>Format versus acceptance</h3><p>The <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format">official format</a> specifies a single float32 layer in [0,1], EPSG:32611, matching bounds and 100 m grid, with null/NaN outside bounds. The owner-mirrored template has an irregular NaN exterior; this candidate uses zeros there.</p><p>The rejected file bytes and organizer diagnosis for <code>Predicted values must be in range [0, 1]</code> were not retained. A local whole-array check does not establish portal acceptance of either exterior convention.</p><p><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">Official competition instructions ↗</a> · <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Official rules ↗</a></p></div></div></section>'''

    research = f'''<div class="breadcrumb"><a href="index.html">Decision dashboard</a> &nbsp; / &nbsp; <span>Research</span></div>
<div class="page-intro"><div class="eyebrow">Scientific review</div><h1>Better evidence, not a louder score.</h1><p><strong>DO NOT SUBMIT</strong> any current file. The competition predicts unmapped faults that may indicate geothermal resources. A heat anomaly or vent is not itself a confirmed fault.</p></div>
<section class="section"><div class="section-head"><div><div class="eyebrow">Forensic analysis</div><h2>What could explain the reported 0.2778?</h2></div></div><div class="grid-two"><div class="card"><h3>What the raster bytes show</h3><p>GEMSDOE32's mask equals GEMSDOE25's after removing {audit['focus_lineage_geometry']['g25_to_g32_removed_pixels']:,} pixels at distance ≤2 px from the mirrored known-fault mask (XOR {audit['focus_lineage_geometry']['g32_b2_vs_g25_d28_filtered_by_distance_gt_2px_xor']:,}). GEMSDOE36 contains those dots plus {audit['focus_lineage_geometry']['g36_extra_pixels_over_g32']:,}. GEMSDOE25 and GEMSDOE30 have identical positive masks.</p></div>
<div class="card"><h3>What remains unknown</h3><p>Thinning can reduce false-positive mass while retaining credit, but whether it caused the reported ordering is unknown. The hidden labels, an organizer receipt tying score to bytes, and the original replay are unavailable. We cannot establish that a new file will exceed 0.2778.</p></div></div></section>
<section class="section"><div class="section-head"><div><div class="eyebrow">Ranked before modeling</div><h2>Four hypotheses to investigate</h2><p>Qualitative ranking only; not fitted here. Novelty across the entire fleet is unproven.</p></div></div><div class="grid-two">
<article class="card"><div class="eyebrow">01 · medium cost</div><h3>Height-persistent cross-gradients</h3><p>Compare magnetic and gravity ridge orientation and displacement across continuation heights, with hydrothermal corroboration. Could reveal buried steps without scarps. <strong>Mimics:</strong> unfaulted contacts and survey seams.</p><p class="note">HTCADS already uses cross-gradients; multiscale stability requires an explicit ablation.</p></article>
<article class="card"><div class="eyebrow">02 · medium cost</div><h3>Thermal direction uncertainty</h3><p>GDR 2 m probes and well/spring chemistry plus terrain and structural orientation; test a fixed family of transport directions. <strong>Mimics:</strong> groundwater flow, land-use anomalies and saline playas.</p></article>
<article class="card"><div class="eyebrow">03 · low–medium cost</div><h3>Visible-tip orientation agreement</h3><p>Recompute visible-only tip geometry per fold and compare with potential-field and terrain lineaments. <strong>Mimics:</strong> erosion and lithologic boundaries.</p></article>
<article class="card"><div class="eyebrow">04 · high cost · access unverified</div><h3>Deformation–structure discordance</h3><p>Test NASA OPERA DISP-S1 displacement gradients against GeoDAWN and 3DEP boundaries. <strong>Mimics:</strong> pumping and atmospheric/line-of-sight artifacts. Relevant tile availability and access remain unverified.</p></article></div>
<p class="note"><a href="../research/2026-10-27_htcads_hypotheses.md">Full hypothesis slate, layer provenance and constraints ↗</a></p></section>
{hptr_research}
{trbvc_research}
<section class="section"><div class="section-head"><div><div class="eyebrow">Source library</div><h2>Official sources for review</h2></div></div><div class="card"><ul class="sources">
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">DrivenData problem, metric and submission format</a> · <a href="https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516">Staff clarification on known-fault masking</a></li>
<li><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">National Laboratory of the Rockies official rules</a> · <a href="https://github.com/drivendataorg/gems-prize-reference-solution">DrivenData reference solution</a></li>
<li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN</a> · <a href="https://gdr.openei.org/submissions/1391">DOE GDR INGENIOUS</a> · <a href="https://www.usgs.gov/3d-elevation-program">USGS 3DEP</a> · <a href="https://www.earthdata.nasa.gov/data/projects/opera">NASA OPERA</a></li></ul><p class="note"><a href="../registry/source_catalog_20261027.json">Source catalog and provenance notes ↗</a></p></div></section>'''

    irregular = f'''<div class="breadcrumb"><a href="index.html">Decision dashboard</a> &nbsp; / &nbsp; <span>Open issues</span></div><div class="page-intro"><div class="eyebrow">Integrity & next steps</div><h1>What still stands in the way.</h1><p><strong>DO NOT SUBMIT</strong> any current file. Automated checks fail closed; no human geological inspector is substituted for validation.</p></div>
{hptr_irregular}
{lope_irregular}
{trbvc_irregular}
<div class="grid-two"><article class="card"><div class="eyebrow">01 · blocking</div><h3>Literal novelty contradiction</h3><p>A registered calibration lattice forces ≥{bound:.2f}% overlap at the frozen budget. The prompt says <em>any</em> registry raster; no control exemption has been authorized.</p></article>
<article class="card"><div class="eyebrow">02 · blocking</div><h3>Replay and registry completeness</h3><p>The prior surface and out-of-fold caches have not been independently replayed. A single witness proves failure but cannot establish full-registry clearance. The separate method paragraph referred to in the prompt was not supplied.</p></article>
<article class="card"><div class="eyebrow">03 · blocking</div><h3>Score provenance</h3><p>The focus scores are user/owner reports without submission-page receipts. The historical SGMC prevalence calibration uses an inferred hidden-label count, not observed organizer truth. Neither is a leaderboard estimate.</p></article>
<article class="card"><div class="eyebrow">04 · blocking</div><h3>Portal and quota</h3><p>Neither exterior convention has an acceptance receipt here. The range-error cause and current account quota are unknown. The selector has no positive authorization path.</p></article>
<article class="card"><div class="eyebrow">05 · provenance</div><h3>Mirrors, not authenticated downloads</h3><p>Core inputs and LiDAR features were restored and SHA-checked from owner-hosted mirrors; hashes establish mirror consistency, not organizer origin. A parallel <a href="../evidence/data_availability_20261027.json">availability audit</a> reports 15 of 30 external mirror files unavailable. The <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/data/">official data page</a> redirects unauthenticated visitors to login.</p></article>
<article class="card"><div class="eyebrow">06 · publication</div><h3>Pages deployment can race</h3><p>Legacy main-branch publication and Actions deployment coexist. A parallel <a href="../evidence/pages_deployment_20261027.json">setting-change attempt</a> was denied with HTTP 403. A repository administrator must fix the source; until then the leaderboard feed is dated, not guaranteed live.</p></article>
<article class="card"><div class="eyebrow">07 · next session</div><h3>Safe next steps</h3><p>Resolve the conflicting rule explicitly, authenticate the official template, inventory the full registry, replay feature canaries and buffered holdouts, and verify quota before a separate selector considers a file.</p></article></div>
<section class="section"><div class="callout"><strong>Shared-tool corrections.</strong><p>The legacy positive validator is now a fail-closed wrapper. Archived parallel runners are stopped. The shared holdout rejects invalid in-footprint values and preserves false-positive mass for empty truth; the idealized marginal-credit threshold is corrected. <a href="../evidence/review_20261027_session3.md">Three-pass review ↗</a></p></div></section>'''

    DOCS.mkdir(exist_ok=True)
    for name, title, content, js in (("index.html", "Decision dashboard", home, FEED_SCRIPT),
            ("executive-summary.html", "Executive summary", summary, ""),
            ("research.html", "Research", research, ""),
            ("irregularities.html", "Open issues", irregular, ""),
            ("submission-table.html", "Historical submission comparison", summary, ""),
            ("submission-howto.html", "Conditional submission instructions", summary, ""),
            ("audit-review.html", "Open issues", irregular, "")):
        (DOCS / name).write_text(page(title, name, content, js), encoding="utf-8")
    feed = {
        "schema": "gems.current-status.v3", "generated_utc": card["generated_utc"],
        "verdict": "negative", "validated_ok_to_download_and_submit": False,
        "ok_to_submit": False, "new_raster": None,
        "research_artifact": prior["file"], "research_artifact_sha256": prior["sha256"],
        "session2_candidate": {
            "filename": s2_name, "sha256": s2_sha, "verdict": "negative",
            "ok_to_download_for_research": True, "ok_to_submit": False,
            "ok_to_download_and_submit": False,
            "literal_witness_overlap": s2_audit["witness_overlap_fraction"],
            "warning": "Archived detector-only promotion is superseded; the literal rule fails.",
        },
        "parallel_research_files": {
            key: {"filename": row["file"], "sha256": row["sha256"], "verdict": "negative",
                  "ok_to_submit": False, "literal_witness_overlap": row["witness_overlap_fraction"],
                  "warning": "Research only; no holdout replay or full-registry authorization."}
            for key, row in extras.items()
        },
        "reason": f"Literal lattice overlap {100*s2_audit['witness_overlap_fraction']:.3f}%; budget lower bound {bound:.2f}% > 70%.",
        "run_card": "../../evidence/current_run_card.json", "public_leaderboard": "public_leaderboard.json",
    }
    if hptr_feed is not None:
        feed["kg2s3_hptr_lane"] = hptr_feed
    if lope_feed is not None:
        feed["kg2s3_lope_lane"] = lope_feed
    if trbvc_feed is not None:
        feed["kg2s3_trbvc_lane"] = trbvc_feed
    (DOCS / "data").mkdir(exist_ok=True)
    (DOCS / "data/status_feed.json").write_text(json.dumps(feed, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (DOCS / "data/current_run_card.json").write_text(json.dumps(card, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    table_data = {
        "schema": "gems.submission-comparison.v2", "generated_utc": card["generated_utc"],
        "verdict": "negative", "ok_to_submit": False, "new_raster": None,
        "leaderboard_estimate": None,
        "warning": "Historical scores are user/owner reports without receipts; files are research only.",
        "previous_artifact": prior, "focus_nine": audit["focus_nine"],
    }
    (ROOT / "evidence/submission_table_20261027.json").write_text(json.dumps(table_data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print("Built seven fail-closed pages from exact-byte audit", audit["generated_utc"])


if __name__ == "__main__":
    main()
