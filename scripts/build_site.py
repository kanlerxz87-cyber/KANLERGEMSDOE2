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

    home=f'''<div class="breadcrumb">DOE GEMS PRIZE &nbsp; / &nbsp; <span>Decision dashboard</span></div>
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

    summary=f'''<div class="breadcrumb"><a href="index.html">Decision dashboard</a> &nbsp; / &nbsp; <span>Executive summary</span></div>
<div class="page-intro"><div class="eyebrow">Decision brief · 27 October 2026</div><h1>What to download.<br>What not to submit.</h1><p>At present there is <strong>no competition-ready file</strong>. The existing file below is available for research, not a weekly submission slot.</p></div>
<div class="callout red-callout"><strong>SUBMISSION STATUS: NO — DO NOT SUBMIT.</strong><p><a href="{artifact}" download>Download the previous HTCADS TIFF for research</a> · {percent:.3f}% literal witness overlap · <a href="../evidence/current_run_card.json">current negative run card</a>.</p></div>
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
