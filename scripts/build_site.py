#!/usr/bin/env python3
"""Build the evidence portal; the only supported current decision is negative.

This builder does not grant upload approval. It checks the current card and
recorded byte audits before publishing; historical run-card claims cannot
create an alternative promotion path.
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
    pages = [("index.html", "Overview"), ("executive-summary.html", "Comparison"),
             ("research.html", "Research"), ("irregularities.html", "Open issues")]
    links = "".join('<a href="{}"{}>{}</a>'.format(
        p, ' class="active" aria-current="page"' if p == active else '', name)
        for p, name in pages)
    return f'''<a class="skip" href="#main">Skip to content</a>
<header class="topbar"><div class="wrap topbar-inner"><a href="index.html" class="brand"><span class="brand-mark">G</span><span class="brand-name">GEMS / FIELDNOTES<small>KANLERGEMSDOE2</small></span></a>
<nav class="nav" aria-label="Main navigation">{links}<a class="nav-link" href="https://github.com/kanlerxz87-cyber/KANLERGEMSDOE2">GitHub ↗</a></nav></div></header>'''


def page(title: str, active: str, content: str, script: str = "") -> str:
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | GEMS Fieldnotes</title><meta name="description" content="Evidence-led geological fault discovery for the DOE GEMS Prize."><link rel="stylesheet" href="style.css"></head>
<body>{header(active)}<main id="main" class="wrap">{content}</main>
<footer class="footer"><div class="wrap footer-inner"><div><strong>GEMS / FIELDNOTES</strong><br>Evidence before a submission slot.</div><div>Maximize P(Win) · Own the Outcome<br>Dated evidence; no upload is automated.</div></div></footer>{script}</body></html>'''


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


def checked_artifact(audit: dict) -> str:
    name = audit["file"]
    path = DOCS / "downloads" / name
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != audit["sha256"]:
        raise SystemExit(f"Research artifact missing or differs from recorded bytes: {name}")
    if not audit.get("duplicate_under_literal_rule"):
        raise SystemExit(f"Stop evidence changed for {name}; rerun independent review")
    return name


def focus_table(rows: list[dict]) -> str:
    result = []
    for r in rows:
        name = Path(r["path"]).name
        local = DOCS / "downloads" / name
        if local.is_file():
            if hashlib.sha256(local.read_bytes()).hexdigest() != r["sha256"]:
                raise SystemExit(f"Historical download differs from pinned evidence: {name}")
            link = f"downloads/{name}"
        else:
            link = r["pinned_download_url"]
        overlap = 100 * r["max_directional_focus_overlap_within_3px"]
        origin = "NaN outside" if r["outside_footprint_all_nan"] else (
            "all-finite" if r["strict_whole_array_finite_0_1"] else "other exterior")
        result.append(f'''<tr><td><strong><a href="{esc(r['site_url'])}">{esc(r['site'])} ↗</a></strong><small>{esc(origin)} · <a href="{esc(r['pinned_source_url'])}">pinned source</a></small></td>
<td class="file"><a href="{esc(link)}">{esc(name)}</a><small>SHA-256 {esc(r['sha256'][:12])}… · research only</small></td>
<td><strong>{r['owner_reported_score']:.4f}</strong><small>USER/OWNER-REPORTED<br>Receipt unavailable</small></td>
<td><strong>No</strong><small>{overlap:.2f}% of this row's dots within 3 px of {esc(r['nearest_focus_site'])}</small></td>
<td><span class="pill stop">Do not submit</span><small>Historical duplicate; not a new cleared candidate</small></td></tr>''')
    return f'''<div class="table-wrap"><table><thead><tr><th scope="col">Site</th><th scope="col">Exact historical file</th><th scope="col">Reported score</th><th scope="col">Unique vs focus nine?</th><th scope="col">Verdict</th></tr></thead><tbody>{''.join(result)}</tbody></table></div>'''


def main() -> None:
    audit = json.loads((ROOT / "evidence/release_audit_20261027.json").read_text())
    card = json.loads((ROOT / "evidence/current_run_card.json").read_text())
    if (card.get("verdict") != "negative" or card.get("ok_to_submit") is not False
            or card.get("raster_sha256") is not None or audit.get("verdict") != "negative"):
        raise SystemExit("This portal builder is refusing stale or positive card")
    pre, prior = audit["preflight"], audit["prior_candidate"]
    prior_file = checked_artifact(prior)
    dsl = json.loads((ROOT / "evidence/dslup_literal_validation_20261027.json").read_text())
    parallel = json.loads((ROOT / "evidence/parallel_hypothesis1_literal_audit_20261027.json").read_text())
    availability = json.loads((ROOT / "evidence/data_availability_20261027.json").read_text())
    if (not pre["forced_duplicate"] or dsl.get("ok_to_submit") is not False
            or parallel.get("ok_to_submit") is not False):
        raise SystemExit("Refusing to publish: the current negative decision/evidence changed")
    dsl_audit = dsl["format_audit"]
    dsl_file = checked_artifact(dsl_audit)
    parallel_audit = parallel["audit"]
    parallel_file = checked_artifact(parallel_audit)
    off36 = json.loads((ROOT / "evidence/off36_independent_check_20261027.json").read_text())
    off36_validator = json.loads((ROOT / "evidence/off36_literal_validation_20261027.json").read_text())
    off36_file = Path(off36["file"]).name
    off36_path = DOCS / "downloads" / off36_file
    if (not off36_path.is_file() or hashlib.sha256(off36_path.read_bytes()).hexdigest() != off36["sha256"]
            or off36_validator.get("ok_to_submit") is not False
            or off36_validator.get("raster_sha256") != off36["sha256"]):
        raise SystemExit("Refusing to publish: off36 byte identity or negative receipt changed")
    hr = audit["historical_holdout_not_replayed"]
    bound = 100 * pre["minimum_directional_overlap"]
    table = focus_table(audit["focus_nine"])
    dsl_pct = 100 * dsl_audit["witness_overlap_fraction"]
    parallel_pct = 100 * parallel_audit["witness_overlap_fraction"]
    prior_pct = 100 * prior["witness_overlap_fraction"]
    verified, unavailable = availability["external"]["verified"], availability["external"]["unavailable"]
    observed = esc(audit["generated_utc"])

    home = f'''<div class="breadcrumb">KANLERGEMSDOE2 &nbsp; / &nbsp; <span>Current decision</span></div>
<section class="hero" aria-labelledby="hero-title"><div><div class="eyebrow">Decision dashboard · audited {observed}</div><span class="status">Negative · do not submit</span>
<h1 id="hero-title">No TIFF is cleared<br>for a live slot.</h1>
<p class="lead">The fixed 37,654-dot lane cannot meet the literal all-registry novelty rule. This lane stopped before a new model or raster; no slot was selected or spent. Parallel artifacts are research only.</p>
<div class="hero-actions"><a class="btn" href="executive-summary.html">See the comparison table →</a><a class="btn secondary" href="../evidence/current_run_card.json">Current JSON run card ↗</a></div></div>
<aside class="hero-aside"><div class="eyebrow">The blocking witness</div><h3>At least {bound:.2f}% must overlap</h3><p>The registered spacing-5 lattice leaves only {pre['uncovered_pixels']:,} footprint pixels farther than 3 px away. At this fixed budget, at least {pre['minimum_overlapping_dots']:,} dots must overlap it: more than the 70% limit.</p><p class="note">This is an exact lower bound for this budget, not a proof about every smaller raster. No control exemption is authorized.</p></aside></section>
<div class="metrics"><div class="metric"><div class="label">Best historical report</div><div class="value">0.2778</div><div class="hint">GEMSDOE32 · user/owner reported; no receipt</div></div>
<div class="metric"><div class="label">Minimum overlap</div><div class="value">{bound:.2f}%</div><div class="hint">At the frozen 37,654-dot budget</div></div>
<div class="metric"><div class="label">New holdout</div><div class="value">Not run</div><div class="hint">Stopped before training or placement</div></div>
<div class="metric"><div class="label">Public #1</div><div class="value" id="leader-value">—</div><div class="hint" id="leader-status">Loading dated feed…</div></div></div>
<section class="section"><div class="section-head"><div><div class="eyebrow">What changed</div><h2>One rule, one decision.</h2></div></div><div class="grid-two"><div class="card"><h3>Two archived files were rechecked</h3><p>The prior HTCADS file overlaps the lattice at <strong>{prior_pct:.3f}%</strong>; DSLUP overlaps at <strong>{dsl_pct:.3f}%</strong>. Both fail the literal rule, regardless of old control-exempt promotion claims.</p><a href="executive-summary.html">View artifacts and evidence →</a></div>
<div class="card"><h3>Parallel-file corrections</h3><p>The hypothesis-1 TIFF overlaps the lattice at <strong>{parallel_pct:.4f}%</strong> and has <strong>{parallel_audit['on_catalogue_positive_pixels']}</strong> on-catalogue positives. A separate 15,000-dot file deliberately targeted lattice gaps and lacks a holdout; its promotion is also retracted.</p><a href="executive-summary.html">Exact-byte audits ↗</a></div></div></section>
<section class="section"><div class="callout"><strong>About the reported range error.</strong><p>The rejected bytes and portal diagnostic are unavailable, so its cause is unknown. Current local checks reopen the exact file and inspect inside-footprint NaN/Inf, [0,1], grid, and exterior. The official description says null/NaN outside bounds; the old all-zero exterior passes a whole-array range test but is not proven accepted. <a href="irregularities.html">Details and remaining checks →</a></p></div></section>'''

    summary = f'''<div class="breadcrumb"><a href="index.html">Decision dashboard</a> &nbsp; / &nbsp; <span>Comparison</span></div>
<div class="page-intro"><div class="eyebrow">Executive decision · {observed}</div><h1>Research downloads.<br>Not submission candidates.</h1><p>There is no approved new TIFF, no current holdout score, and no numerical leaderboard estimate. Do not upload any file on this page.</p></div>
<div class="callout red-callout"><strong>NEGATIVE / DO NOT SUBMIT</strong><p>The 37,654-dot assignment is mathematically incompatible with the literal &gt;70% overlap stop. Lattice controls count; treating them as exempt was not authorized. The original promotion and 5/5 claims are withdrawn.</p></div>
<section class="section"><div class="section-head"><div><div class="eyebrow">Prioritized sites</div><h2>Nine reported leaders</h2><p>Scores are user/owner reports, not organizer receipts. None establishes what a new file will score.</p></div></div>{table}
<p class="note">For each row, overlap is the fraction of its dots within Euclidean 3 px of its nearest of the other eight. This limited comparison is not a complete current-registry audit. The broader historical registry is <a href="../registry/comparison_registry.json">available for review</a>; remaining sites and scores are not independently verified in this pass.</p></section>
<section class="section"><div class="section-head"><div><div class="eyebrow">Exact-byte witness</div><h2>Local research artifacts</h2></div></div>
<div class="table-wrap"><table><thead><tr><th>File / hash</th><th>What is known</th><th>Witness</th><th>Verdict</th></tr></thead><tbody>
<tr><td class="file"><a href="downloads/{esc(prior_file)}">{esc(prior_file)}</a><small>SHA-256 {esc(prior['sha256'])}</small></td><td>HOLDOUT-DTI {hr['dti']:.6f}, {esc(hr['evaluator_version'])}, N={hr['withheld_positive_occurrences']:,} withheld-positive occurrences, 95% CI [{hr['ci95'][0]:.6f}, {hr['ci95'][1]:.6f}]. Historical receipt, not replayed.</td><td>{prior['witness_overlap_dots']:,} / {prior['inside_positive_pixels']:,} · {prior_pct:.3f}%</td><td><span class="pill stop">Do not submit</span></td></tr>
<tr><td class="file"><a href="downloads/{esc(dsl_file)}">{esc(dsl_file)}</a><small>SHA-256 {esc(dsl_audit['sha256'])}</small></td><td>Prior holdout and control-separated reports are archived but not independently replayed. <a href="../evidence/dslup_literal_validation_20261027.json">Current validator receipt</a>.</td><td>{dsl_audit['witness_overlap_dots']:,} / {dsl_audit['inside_positive_pixels']:,} · {dsl_pct:.4f}%</td><td><span class="pill stop">Do not submit</span></td></tr>
<tr><td class="file"><a href="downloads/{esc(parallel_file)}">{esc(parallel_file)}</a><small>SHA-256 {esc(parallel_audit['sha256'])}</small></td><td>Added by a parallel session; {parallel_audit['on_catalogue_positive_pixels']} on-catalogue positives; no independent holdout or surface replay. <a href="../evidence/parallel_hypothesis1_literal_audit_20261027.json">Corrected byte audit</a>.</td><td>{parallel_audit['witness_overlap_dots']:,} / {parallel_audit['inside_positive_pixels']:,} · {parallel_pct:.4f}%</td><td><span class="pill stop">Do not submit</span></td></tr>
<tr><td class="file"><a href="downloads/{esc(off36_file)}">{esc(off36_file)}</a><small>SHA-256 {esc(off36['sha256'])}</small></td><td>Parallel 15,000-dot artifact; {off36['dots_in_lattice_gap_pixels']:,} dots deliberately placed in lattice gaps, {off36['on_catalogue_positive_pixels']} on catalogue, no independent holdout. The changed budget and gap targeting violate the lane. <a href="../evidence/off36_independent_check_20261027.json">Recheck</a> · <a href="../evidence/off36_literal_validation_20261027.json">negative validator</a>.</td><td>{off36['lattice_overlap_3px']*100:.2f}% to lattice; other registry and surface incomplete</td><td><span class="pill stop">Do not submit</span></td></tr>
</tbody></table></div></section>
<section class="section"><div class="section-head"><div><div class="eyebrow">When a future candidate is cleared</div><h2>Submission instructions</h2></div></div><div class="grid-two"><div class="card"><ol class="steps"><li><strong>Resolve and preregister the protocol.</strong> Do not silently exempt the lattice or adjust this budget to escape the gate.</li><li><strong>Replay automated checks.</strong> Check the pre-placement surface and final dots against every current registry raster; test every feature for leakage and use visible-only, buffered whole-segment spatial holdout with pooled DTI and paired CIs.</li><li><strong>Run the separate selector.</strong> It must verify exact file identity, official format, current account quota and all gates. This repository has no positive upload path today.</li></ol></div><div class="card"><h3>Only after approval</h3><p>On the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">official competition page</a>, choose Submit, upload the exact approved TIFF or a ZIP containing only that TIFF, enter its unique name and note of at most 140 characters, then save the actual receipt.</p><p>Check the current account-specific limit on the submission page; staff say it takes precedence over the rules' older weekly parenthetical. No quota was checked or slot spent here.</p></div></div></section>'''

    research = f'''<div class="breadcrumb"><a href="index.html">Decision dashboard</a> &nbsp; / &nbsp; <span>Research</span></div>
<div class="page-intro"><div class="eyebrow">Mechanism before metric</div><h1>What might be missing?</h1><p>Four ranked hypotheses, not fitted in this review. Relative priority and costs are qualitative, not scores. A new lane requires proper preregistration and protocol resolution.</p></div>
<section class="section"><div class="section-head"><div><div class="eyebrow">Forensic analysis</div><h2>Why the reported 0.2778?</h2></div></div><div class="grid-two"><div class="card"><h3>Measured geometry</h3><p>GEMSDOE32 equals GEMSDOE25's positive mask after removing 6,436 pixels within 2 px of the restored known-fault catalogue. GEMSDOE25 and 30 have identical positive masks; GEMSDOE36 contains all GEMSDOE32 dots plus 1,200.</p></div><div class="card"><h3>A plausible, unproven explanation</h3><p>Pruning may reduce false positives while retaining useful coverage under DTI, but the hidden expert truth and submission receipts are unavailable. Neither causal contribution nor a score ceiling is established. A higher score is possible in principle, but not demonstrated for a new candidate.</p></div></div></section>
<section class="section"><div class="section-head"><div><div class="eyebrow">Ranked hypotheses</div><h2>Converging lines of evidence</h2></div></div><div class="grid-two">
<article class="card"><div class="eyebrow">01 · medium cost · owner mirrors available</div><h3>Height-persistent cross-gradients</h3><p>Use magnetic RTP/TMI and isostatic-gravity gradients at multiple continuation heights, plus independent hydrothermal support. Persistent aligned offsets may reveal a buried fault step where a scarp is absent. <strong>Mimics:</strong> unfaulted contacts and survey seams.</p><p class="note">HTCADS already combines cross-gradients and updip projection; multi-height stability needs an explicit ablation and fleet novelty review.</p></article>
<article class="card"><div class="eyebrow">02 · medium cost · GDR mirror available</div><h3>Thermal direction uncertainty</h3><p>Test a fixed family of plausible transport directions using 2 m thermal probes, spring/well chemistry, conductivity, terrain and structural ridges. Offset anomalies could indicate a blind feeder. <strong>Mimics:</strong> shallow groundwater, seasonal heating and saline playas.</p><p class="note">Prior HTCADS uses an upslope shift; direction sensitivity is untested. DOE source is public, but mirrored bytes are not authenticated to the official download.</p></article>
<article class="card"><div class="eyebrow">03 · low–medium cost · owner mirrors available</div><h3>Visible-tip orientation agreement</h3><p>Recompute fold-visible tip direction and intersect it with potential-field and terrain lineaments. A consistent orientation could trace an unmapped continuation. <strong>Mimics:</strong> drainage-aligned erosion and lithologic contacts.</p><p class="note">Tip cones/relay priors already exist; the proposed cross-layer orientation comparison needs an implementation audit.</p></article>
<article class="card"><div class="eyebrow">04 · high cost · tiles not verified</div><h3>Deformation–structure discordance</h3><p>Compare NASA OPERA DISP-S1 displacement gradients across time with GeoDAWN and 3DEP boundaries. Repeated discontinuities might indicate concealed structure. <strong>Mimics:</strong> pumping subsidence, atmospheric effects and radar line-of-sight artifacts.</p><p class="note">NASA describes open U.S. coverage, but relevant tiles, access, dates and local usability remain unverified. Not executable here.</p></article></div>
<p class="note"><a href="../research/2026-10-27_htcads_hypotheses.md">Full ranked slate, layers, costs and controls ↗</a> · <a href="../research/2026-10-27_new_hypotheses.md">Parallel slate with corrected TIFF claims ↗</a></p></section>
<section class="section"><div class="section-head"><div><div class="eyebrow">Source library</div><h2>Official resources</h2></div></div><div class="card"><ul class="sources">
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">DrivenData problem, metric and format</a> · <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">public leaderboard</a></li>
<li><a href="https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4">DrivenData staff: exact-pixel known-fault mask</a> · <a href="https://community.drivendata.org/t/submission-amount-question/11553">submission-limit clarification</a></li>
<li><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">National Laboratory of the Rockies official rules</a> · <a href="https://github.com/drivendataorg/gems-prize-reference-solution">DrivenData reference solution</a></li>
<li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN</a> · <a href="https://gdr.openei.org/submissions/1391">DOE INGENIOUS GDR 1391</a> · <a href="https://www.usgs.gov/3d-elevation-program">USGS 3DEP</a></li>
<li><a href="https://www.usgs.gov/publications/structural-discontinuities-and-their-control-hydrothermal-systems-great-basin-usa">USGS stepover/termination research</a> · <a href="https://www.usgs.gov/publications/influence-pre-existing-structures-geothermal-springs-inferences-potential-field">USGS dike/contact mimic example</a></li>
<li><a href="https://www.earthdata.nasa.gov/data/catalog/asf-opera-l3-disp-s1-v1-1">NASA OPERA DISP-S1 product</a> · <a href="../registry/source_catalog_20261027.json">source catalog and access notes</a></li></ul>
<p class="note">Metadata pages support the scientific context and access descriptions, not model efficacy or mirror authenticity.</p></div></section>'''

    irregular = f'''<div class="breadcrumb"><a href="index.html">Decision dashboard</a> &nbsp; / &nbsp; <span>Open issues</span></div><div class="page-intro"><div class="eyebrow">Integrity & next steps</div><h1>What still stands in the way.</h1><p>These are explicit blockers. Automated validation must fail closed; no manual geological inspector is assumed.</p></div>
<div class="grid-two"><article class="card"><div class="eyebrow">01 · blocking</div><h3>Literal novelty contradiction</h3><p>The registered lattice forces at least {bound:.2f}% overlap at the assigned budget, above the 70% stop. It is a calibration control, but the protocol says <em>any</em> registry raster. No exemption is authorized.</p></article>
<article class="card"><div class="eyebrow">02 · blocking</div><h3>Independent replay</h3><p>A single witness proves failure, not complete novelty. The current full registry, pre-placement surfaces, per-feature canary and spatial holdout were not independently replayed. A past run card cannot approve itself.</p></article>
<article class="card"><div class="eyebrow">03 · blocking</div><h3>Score provenance</h3><p>The nine scores are user/owner reports without receipts. Past claims of organizer confirmation, hidden-truth inference and control-exempt promotion are superseded.</p></article>
<article class="card"><div class="eyebrow">04 · blocking</div><h3>Portal error and quota</h3><p>No rejected bytes or acceptance receipt was available. NaN exterior matches the mirror; zeros pass a strict whole-array check but differ from it. Neither establishes acceptance. The live quota is unknown.</p></article>
<article class="card"><div class="eyebrow">05 · provenance</div><h3>External restore is partial</h3><p>Core and scored mirrors and nine focus TIFFs passed hashes. Of 30 external entries, {verified} verified and {unavailable} returned 404, including 13 derived 10 m DEM channels, their manifest, and one heat-flow mirror. A pinned hash authenticates mirror identity, not official origin. <a href="../evidence/data_availability_20261027.json">Availability receipt ↗</a></p></article>
<article class="card"><div class="eyebrow">06 · safeguards</div><h3>Legacy paths disabled</h3><p>The old KG2-S2 validator accepted self-attested promotion and ignored the lattice; both modes now delegate to the fail-closed validator. Legacy parallel experiment entry points stop before training or emission. Invalid predictions are rejected rather than silently clipped.</p></article>
<article class="card"><div class="eyebrow">07 · deployment</div><h3>Pages refresh may race</h3><p>Pages currently uses legacy main-root publishing while an Actions deployment also runs. Switching the source to Actions returned HTTP 403 for the integration. The feed is dated; automatic live delivery is not guaranteed. <a href="../evidence/pages_deployment_20261027.json">Deployment audit ↗</a></p></article></div>
<section class="section"><div class="callout"><strong>Verification record.</strong><p>Reproduced the counting bound and audited exact bytes, reviewed and corrected shared gates and presentation, and added adversarial checks. See <a href="../evidence/current_run_card.json">the current run card</a>, <a href="../evidence/release_audit_20261027.json">full audit</a> and repository tests.</p></div></section>'''

    DOCS.mkdir(exist_ok=True)
    for name, title, content, js in (
        ("index.html", "Decision dashboard", home, FEED_SCRIPT),
        ("executive-summary.html", "Executive summary", summary, ""),
        ("research.html", "Research", research, ""),
        ("irregularities.html", "Open issues", irregular, ""),
        ("submission-table.html", "Historical submission comparison", summary, ""),
        ("audit-review.html", "Open issues", irregular, ""),
    ):
        (DOCS / name).write_text(page(title, name, content, js), encoding="utf-8")
    feed = {
        "schema": "gems.current-status.v3", "generated_utc": card["generated_utc"],
        "verdict": "negative", "validated_ok_to_download_and_submit": False,
        "ok_to_submit": False, "new_raster": None,
        "research_artifact": prior_file, "research_artifact_sha256": prior["sha256"],
        "reason": f"Literal lattice overlap {prior_pct:.3f}%; fixed-budget lower bound {bound:.2f}% > 70%.",
        "dslup": {"filename": dsl_file, "sha256": dsl_audit["sha256"],
                  "witness_overlap": dsl_audit["witness_overlap_fraction"], "ok_to_submit": False},
        "parallel_hypothesis1": {"filename": parallel_file, "sha256": parallel_audit["sha256"],
                                 "witness_overlap": parallel_audit["witness_overlap_fraction"],
                                 "on_catalogue_positives": parallel_audit["on_catalogue_positive_pixels"],
                                 "ok_to_submit": False},
        "parallel_off36": {"filename": off36_file, "sha256": off36["sha256"],
                           "witness_overlap": off36["lattice_overlap_3px"],
                           "on_catalogue_positives": off36["on_catalogue_positive_pixels"],
                           "ok_to_submit": False},
        "run_card": "../../evidence/current_run_card.json", "public_leaderboard": "public_leaderboard.json",
    }
    howto = f'''<div class="breadcrumb"><a href="index.html">Decision dashboard</a> / Submission instructions</div><div class="page-intro"><div class="eyebrow">Not cleared</div><h1>How to submit, when cleared.</h1><p>No candidate is approved today. Follow the automated checks, separate selector, account-page quota and receipt instructions on the <a href="executive-summary.html">comparison page</a>.</p></div>'''
    (DOCS / "submission-howto.html").write_text(page("How to submit", "submission-howto.html", howto, ""), encoding="utf-8")
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
    print("Built seven fail-closed pages from", audit["generated_utc"])


if __name__ == "__main__":
    main()
