#!/usr/bin/env python3
"""Build deterministic static GitHub Pages from the checked-in audit evidence."""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def external(url: str, text: str) -> str:
    return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(text)} ↗</a>'


def header(prefix: str, active: str) -> str:
    links = [('Overview', prefix + 'index.html', 'home'),
             ('Executive summary', prefix + 'docs/k2-executive-summary.html', 'executive'),
             ('How to submit', prefix + 'docs/k2-how-to-submit.html', 'guide'),
             ('Research', prefix + 'docs/k2-research.html', 'research')]
    nav = ''.join(f'<a href="{href}" class="{("active" if key == active else "")}"'
                  + (' aria-current="page"' if key == active else '') + f'>{label}</a>'
                  for label, href, key in links)
    return f'''<a class="skip" href="#main">Skip to content</a>
<header class="site-header"><div class="shell header-inner">
<a class="brand" href="{prefix}index.html" aria-label="GEMS Fault Lab home">
<span class="brand-mark" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none"><path d="M3 16c3-1 3-6 6-7s4 3 7 2 3-4 5-5M3 20c3-1 4-4 7-4s3 2 6 1 3-3 5-4" stroke="#c5dec0" stroke-width="1.7" stroke-linecap="round"/></svg></span>
<span class="brand-title">GEMS FAULT LAB<span class="brand-sub">KANLER · Research brief</span></span></a>
<nav class="main-nav" aria-label="Main navigation">{nav}<a class="nav-cta" href="https://www.drivendata.org/competitions/306/competition-doe-gems/" target="_blank" rel="noopener noreferrer">Competition ↗</a></nav>
</div></header>'''


def footer(prefix: str) -> str:
    return f'''<footer class="site-footer"><div class="shell footer-inner"><div><strong>GEMS FAULT LAB</strong><p>Evidence first. No automated competition uploads.</p></div><div class="footer-links">
<a href="{prefix}evidence/run-card.json">Run card</a><a href="{prefix}docs/research/irregularities.md">Irregularities</a>
<a href="https://github.com/kanlerxz87-cyber/KANLERGEMSDOE2">Repository ↗</a><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Official problem ↗</a></div></div></footer>'''


def page(title: str, description: str, prefix: str, active: str, body: str) -> str:
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{esc(description)}"><title>{esc(title)} · GEMS Fault Lab</title>
<link rel="stylesheet" href="{prefix}docs/assets/site.css"><script defer src="{prefix}docs/assets/site.js"></script></head>
<body>{header(prefix, active)}<main id="main">{body}</main>{footer(prefix)}</body></html>\n'''


def site_table(audit: dict, prefix: str) -> str:
    rows = sorted(audit['sites'], key=lambda r: float(r['owner_reported_claim']), reverse=True)
    trs = []
    for r in rows:
        file_name = Path(r['path']).name
        peer = r['maximum_overlap_peer'].replace('GEMSDOE', 'G')
        fraction = 100 * r['maximum_directed_3px_overlap_with_other_focus_champions']
        trs.append(f'''<tr><td><span class="site-id">{esc(r['site'])}</span></td>
<td><a class="file-link" href="{esc(r['source_url'] + '?raw=1')}" target="_blank" rel="noopener noreferrer">{esc(file_name)} ↗</a><span class="subtext">Reference download only</span></td>
<td><span class="owner-value">{esc(r['owner_reported_claim'])}</span><span class="subtext">Owner-reported · unverified</span></td>
<td>Not estimable<span class="subtext">No calibrated forecast</span></td>
<td><span class="fail">NO</span><span class="subtext">{fraction:.2f}% near {esc(peer)}</span></td>
<td><span class="small-pill">DO NOT SUBMIT</span></td></tr>''')
    return f'''<div class="card table-card"><div class="table-intro"><div><h3>Nine historical references</h3>
<p>The values are claims supplied by the owner, not organizer-confirmed submission receipts. The linked files are historical; they are <strong>not</strong> new submissions.</p></div><span class="tag tag-danger">No file approved</span></div>
<div class="table-scroll" role="region" aria-label="Nine historical references; scroll horizontally for all columns" tabindex="0"><table><thead><tr><th scope="col">Site</th><th scope="col">File · research only</th><th scope="col">Historical claim</th><th scope="col">Estimated leaderboard</th><th scope="col">Unique vs peers?</th><th scope="col">Submit?</th></tr></thead><tbody>{''.join(trs)}</tbody></table></div>
<div class="footnote">Uniqueness shown is the maximum directed fraction of that row's positive pixels within 3 pixels of one of the other eight historical focus files. &gt;70% fails. Surface correlation and the full changing registry were not audited here. <a href="{prefix}evidence/focus-audit-20261026.json">Full byte-level audit ↗</a></div></div>'''


def feed(heads: dict) -> str:
    items=[]
    for item in heads['sites']:
        observed = item.get('observed_head') or ''
        url='https://buffedlizard55-lab.github.io/' + item['site'] + '/'
        items.append(f'''<div class="feed-item" data-repo="{esc(item['repository'])}" data-head="{esc(observed)}"><a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(item['site'])} ↗</a><span data-state-text>Snapshot only</span></div>''')
    snapshot=esc(heads['checked_utc'].replace('T',' ')[:19] + ' UTC')
    return f'''<div class="card feed-panel" data-github-feed><div class="feed-header"><div><h3>Source activity</h3><p>Commit heads observed {snapshot}.</p></div><button class="btn btn-line refresh" type="button" data-refresh>Check GitHub heads <span class="arrow">↗</span></button></div>
<p class="feed-status" data-status aria-live="polite">A head change means re-audit is needed; it is not a score or approval.</p><div class="feed-list">{''.join(items)}</div></div>'''


def home(audit: dict, geom: dict, heads: dict) -> str:
    minimum = 100 * geom['minimum_fraction_inside_halo']
    return f'''<section class="hero"><div class="shell hero-inner"><div>
<div class="eyebrow">DOE GEMS · evidence-led fault discovery</div>
<h1>Protect the slot.<br><em>Follow the evidence.</em></h1>
<p class="hero-copy">A clear view of what is known, what remains unproven, and whether a new GeoTIFF is actually ready for the competition.</p>
<div class="hero-buttons"><a class="btn btn-primary" href="docs/k2-executive-summary.html">Review executive summary <span class="arrow">↗</span></a><a class="btn btn-outline" href="evidence/run-card.json">View the run card <span class="arrow">↗</span></a></div></div>
<aside class="decision-panel" aria-label="Current submission decision"><div class="decision-heading"><span class="panel-label">Current decision</span><span class="tag tag-dark">Do not submit</span></div>
<h2>No candidate is cleared.</h2><p>K2-SCALE stopped before placement: this lane produced no TIFF, holdout result or competition upload. Other parallel artifacts remain quarantined.</p>
<div class="panel-stats"><div class="panel-row"><span>K2 candidate file</span><strong>None generated</strong></div><div class="panel-row"><span>K2 holdout DTI / CI</span><strong>Not measured</strong></div><div class="panel-row"><span>Mandatory overlap</span><strong>At least {minimum:.2f}%*</strong></div></div>
<a class="decision-link" href="docs/k2-research.html#geometry">Why the lane stopped <span class="arrow">→</span></a></aside></div></section>
<section class="section-sm"><div class="shell"><div class="cards">
<article class="card metric-card"><span class="metric-number">01 / DOWNLOAD</span><h3>New submission</h3><div class="metric-value danger">Unavailable</div><p>No unique candidate was written after the duplicate stop.</p></article>
<article class="card metric-card"><span class="metric-number">02 / PERFORMANCE</span><h3>Leaderboard estimate</h3><div class="metric-value">Not estimable</div><p>Hidden labels and score-to-file receipts are unavailable.</p></article>
<article class="card metric-card"><span class="metric-number">03 / VALIDATION</span><h3>K2 holdout and canaries</h3><div class="metric-value">Not run</div><p>No K2 feature, dot, CI or format result is being invented.</p></article>
<article class="card metric-card"><span class="metric-number">04 / SLOT</span><h3>Competition upload</h3><div class="metric-value">None here</div><p>No upload was made by this session. Current quota remains unknown.</p></article></div></div></section>
<section class="section"><div class="shell"><div class="section-head"><div><div class="eyebrow">Executive summary</div><h2>The historical field, clearly labeled.</h2></div><p>File identity is not score identity. The strongest owner-reported claim belongs to GEMSDOE32, but its file is an already-used family member, not a new candidate.</p></div>{site_table(audit, '')}
<a class="inline-link" href="docs/k2-executive-summary.html">Read the full nine-site analysis <span class="arrow">→</span></a></div></section>
<section class="section section-muted"><div class="shell"><div class="section-head"><div><div class="eyebrow">What actually happened</div><h2>A stop, not a shortcut.</h2></div><p>Scientific and submission gates are separate. Passing a file-format check is never the same as demonstrating a likely high score.</p></div>
<div class="two-col"><article class="card explain-card"><div class="eyebrow">The overlap constraint</div><h3>One registry raster is enough to stop this lane.</h3><p>Only 6,649 footprint cells lie outside the registered lattice's three-pixel halo. With 37,654 distinct dots, at least 31,005 would necessarily be inside it.</p><div class="formula">31,005 / 37,654 = {minimum:.2f}% &gt; 70%</div><p>*A mathematical lower bound, not an observed overlap for a candidate. No surface or final dots were created.</p><a class="inline-link" href="evidence/lattice-feasibility-20261026.json">Open geometry receipt <span class="arrow">→</span></a></article>
<article class="card explain-card"><div class="eyebrow">Scientific interpretation</div><h3>Pruning can help. It is not proof.</h3><p>We verified that GEMSDOE32 B2 is exactly a distance-pruned subset of D2.8. Reducing false-positive mass could explain the owner-reported improvement, but the hidden true-positive loss is unknown.</p><ul class="rule-list"><li><span>01</span> Known fault pixels are masked exactly, not with a blanket buffer.</li><li><span>02</span> New fault labels may lie close to known faults.</li><li><span>03</span> A mapped-fault holdout cannot certify the hidden leaderboard.</li></ul><a class="inline-link" href="docs/k2-research.html">Explore the evidence <span class="arrow">→</span></a></article></div></div></section>
<section class="section"><div class="shell fresh-wrap"><div><div class="eyebrow">Source awareness</div><h2>Know when the evidence moves.</h2><p>The nine research repositories can change in parallel. Check their public GitHub heads for updates; a changed head flags a stale snapshot, not a new validated result.</p><a class="inline-link" href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/" target="_blank" rel="noopener noreferrer">Open the official leaderboard manually <span class="arrow">↗</span></a></div>{feed(heads)}</div></section>'''


def executive(audit: dict) -> str:
    return f'''<section class="subhero"><div class="shell"><a class="breadcrumb" href="../index.html">← Overview</a><div class="eyebrow">Nine-site executive summary</div><h1>Which file should I submit?</h1><p>None is approved today. The historical files below are linked for research, not for re-upload or a claim of uniqueness.</p></div></section>
<section class="content"><div class="shell"><div class="notice"><strong>Not OK to submit · no new candidate</strong><p>The K2-SCALE lane stopped before placement because the mandatory overlap threshold is mathematically impossible at its preregistered budget. No score estimate or local holdout has been produced.</p></div>
<div style="height:24px"></div>{site_table(audit, '../')}
<div class="prose"><h2>What the strongest claim tells us</h2><p>The largest owner-reported historical value in the nine-site prompt is GEMSDOE32 B2, <strong>0.2778</strong>. No organizer submission receipt linking that number to the identified bytes was available. The pinned B2 raster is exactly the older D2.8 mask after removing dots at or within two pixels of the visible catalogue.</p>
<p>It is scientifically plausible that reducing false-positive mass improved the distance-weighted Tversky index. But the organizer's hidden truth is unavailable, and the lost true-positive credit is unknown. New faults may also lie within 300 m of known faults. Therefore we cannot prove the reason for the claimed change, or infer a reliable leaderboard score for a new file.</p>
<h2>How the comparison was made</h2><p>All nine named files were fetched at immutable Git commits, verified by SHA-256 and compared on a hash-pinned owner-mirror footprint. The uniqueness column uses a directional 3-pixel overlap against the other eight historical focus files; it does not cover the original prediction surfaces or all concurrent registry rasters. Owner-mirror integrity is not organizer authentication.</p>
<p>GEMSDOE25 and GEMSDOE30 have identical prediction values inside the footprint, even though their TIFF bytes differ. GEMSDOE36 contains the entire GEMSDOE32 B2 set plus 1,200 dots. Renaming, zero-filling, or re-encoding these historical files is not a new scientific submission.</p>
<div class="source-list"><a class="card source-link" href="../evidence/focus-audit-20261026.json"><strong>Open the nine-file audit →</strong><small>Hashes, directed overlaps and lineage</small></a><a class="card source-link" href="../evidence/run-card.json"><strong>Open the negative run card →</strong><small>Unmeasured fields remain null</small></a></div>
<h2>Official sources and score limits</h2><p>{external('https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/','Problem and performance metric')} · {external('https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/','Current leaderboard')} · {external('https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4','Staff clarification on masking')}.</p></div></div></section>'''


def guide() -> str:
    return '''<section class="subhero"><div class="shell"><a class="breadcrumb" href="../index.html">← Overview</a><div class="eyebrow">Submission guide</div><h1>From evidence to upload.</h1><p>A checklist for a future approved candidate—not permission to upload any current file.</p></div></section>
<section class="content"><div class="shell"><div class="notice"><strong>Stop here today</strong><p>There is no approved TIFF in this project. Do not submit the historical links or a format-only research artifact.</p></div>
<div style="height:24px"></div><div class="steps">
<article class="card step"><span class="step-num">01</span><div><h3>Run the scientific gates first</h3><p>A future candidate needs a single preregistered lane, feature-only leakage canaries, whole-segment buffered hide-and-recover, visible-only catalogue features, pooled HOLDOUT-DTI with a 95% spatial CI, a same-evaluator paired win over the holdout best, and both surface and final-dot checks against the entire registry. A separate selector must approve the weekly slot.</p></div></article>
<article class="card step"><span class="step-num">02</span><div><h3>Validate the exact saved GeoTIFF</h3><p>Use one float32 band, the template CRS/shape/transform and values in [0, 1], with no masked or non-finite pixels inside the footprint. The official description specifies null/NaN outside the bounds. Re-open the saved bytes, verify their SHA-256, and keep the validator output. Local validation is not organizer acceptance.</p></div></article>
<article class="card step"><span class="step-num">03</span><div><h3>Identify the file and short note</h3><p>Once all gates and the selector pass, use its unique content-bound filename and a note no longer than 140 characters. The current run has no submission name because no file exists.</p></div></article>
<article class="card step"><span class="step-num">04</span><div><h3>Submit only after approval</h3><p>On DrivenData, sign in, open the GEMS competition, choose “Make new submission,” select the exact approved .tif or a zip containing one GeoTIFF, paste the short note, verify the current weekly quota, and submit. This project cannot access the account or spend a slot automatically.</p></div></article></div>
<div class="prose"><h2>If the portal reports a range error</h2><p>Do not guess that NaN or any other specific cause triggered the previously reported error: the rejected bytes and server diagnostic are unavailable. Re-open the exact file with the automated checker, inspect finite in-footprint values and GDAL masks, and compare its CRS, shape and transform with an authenticated sample. Never silently clip invalid predictions or treat a zero-filled alternative as organizer-approved.</p>
<pre><code>python scripts/check_format.py --candidate path/to/file.tif \\
  --template .cache/owner-data/sample_submission.tif \\
  --shared .cache/GEMSDOE33 --out evidence/format-check.json</code></pre>
<p>The checker uses the pinned shared validator, adds saved-byte and null-mask checks, rejects external GDAL sidecars for a single-file upload, and always leaves <code>ok_to_submit</code> false. The mirror template is not organizer-authenticated.</p>
<p><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format" target="_blank" rel="noopener noreferrer">Official submission format ↗</a> · <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/rules/" target="_blank" rel="noopener noreferrer">Competition rules ↗</a></p></div></div></section>'''


def research(geom: dict) -> str:
    return f'''<section class="subhero"><div class="shell"><a class="breadcrumb" href="../index.html">← Overview</a><div class="eyebrow">Research notes</div><h1>Think beyond the map.</h1><p>A preregistered single lane, a rigorous stop, and source-linked next steps for genuinely unmapped structure.</p></div></section>
<section class="content"><div class="shell prose"><div class="notice"><strong>Negative result · no experiment promoted</strong><p>The geometric feasibility test stopped the selected K2-SCALE lane before the predictive surface or candidate existed.</p></div>
<h2 id="geometry">The lattice makes this budget impossible</h2><p>Only {geom['footprint_cells_outside_halo']:,} cells in the pinned owner-mirror footprint lie more than three pixels from the registered lattice. At a fixed budget of {geom['candidate_budget']:,} unique dots, at least {geom['minimum_candidate_dots_inside_halo']:,} must be within its halo. The lower bound is <strong>{100*geom['minimum_fraction_inside_halo']:.2f}%</strong>, exceeding the protocol's 70% stop. It is a lower bound on any possible arrangement, not a measurement of a candidate.</p><p>A smaller budget could satisfy this one necessary condition, but that would be a new design and would still need every other gate. This stopped lane was not retuned.</p>
<h2>A parallel artifact is also a duplicate</h2><p>An independently produced E1 raster was already quarantined on the evolving main branch. We re-opened its exact bytes: <strong>37,395 of its 37,654 dots (99.31%)</strong> fall within three pixels of the same registered lattice. The earlier nine-file E1 comparison excluded that lattice. This one-raster check is a duplicate stop, not a new experiment or a surface-correlation audit. <a href="../evidence/parallel-e1-lattice-audit-20261026.json">Open the retrospective receipt →</a></p>
<h2>The selected hypothesis</h2><p><strong>K2-SCALE</strong> proposes that a concealed boundary may create colocated magnetic and topographic gradients with a relatively stable cross-scale curvature phase. A lithologic contact, volcanic flow edge, or processing artifact can mimic this signature. No result supports the hypothesis yet; it does not establish geothermal vent locations.</p>
<h2>Three alternatives, not experiments</h2><p>The preregistered slate also ranks cross-scarp drainage offsets, paleo-thermal deposits plus shallow probes, and multiscale magnetic–gravity junctions. The first two need specific official data products not directly obtainable in this sandbox; the last has substantial overlap risk with earlier work. None was substituted after the stop.</p>
<div class="source-list"><a class="card source-link" href="research/hypotheses.md"><strong>Read the preregistered slate →</strong><small>Layers, physical signatures, mimics and costs</small></a><a class="card source-link" href="research/irregularities.md"><strong>Read the irregularities →</strong><small>Shared evaluator, provenance and format limitations</small></a><a class="card source-link" href="research/audit.md"><strong>Read the full audit →</strong><small>Lineage, metric reasoning and next steps</small></a><a class="card source-link" href="../evidence/lattice-feasibility-20261026.json"><strong>Open the preflight receipt →</strong><small>Exact grid, hashes and geometry counts</small></a></div>
<h2>Grounded in official sources</h2><p>{external('https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and','USGS GeoDAWN data')} · {external('https://www.usgs.gov/publications/three-dimensional-geologic-mapping-assess-geothermal-potential-examples-nevada-and','USGS structural controls')} · {external('https://www.usgs.gov/publications/structural-controls-geothermal-circulation-surprise-valley-california-a-re-evaluation','USGS counterexample')} · {external('https://gdr.openei.org/submissions/1391','DOE INGENIOUS dataset')} · {external('https://www.usgs.gov/3d-elevation-program','USGS 3DEP')}.</p></div></section>'''


def build() -> dict[Path, str]:
    audit = json.loads((ROOT / 'evidence/focus-audit-20261026.json').read_text())
    geom = json.loads((ROOT / 'evidence/lattice-feasibility-20261026.json').read_text())
    card = json.loads((ROOT / 'evidence/run-card.json').read_text())
    heads = json.loads((ROOT / 'docs/data/source-heads.json').read_text())
    if card.get('verdict') != 'negative' or card.get('ok_to_submit') is not False or not geom['strict_more_than_70_percent_unavoidable']:
        raise ValueError('This static negative-decision template must not render a different verdict')
    if card['correlation_and_overlap_vs_registry']['minimum_possible_fraction_within_3px_of_pinned_lattice'] != geom['minimum_fraction_inside_halo']:
        raise ValueError('run card and geometry evidence disagree')
    return {
        ROOT / 'index.html': page('Overview', 'Evidence-led DOE GEMS research and submission readiness.', '', 'home', home(audit, geom, heads)),
        ROOT / 'docs/k2-executive-summary.html': page('Executive summary', 'Nine historical files, evidence labels, and current no-submit decision.', '../', 'executive', executive(audit)),
        ROOT / 'docs/k2-how-to-submit.html': page('How to submit', 'Future competition submission checklist and range validation.', '../', 'guide', guide()),
        ROOT / 'docs/k2-research.html': page('Research', 'K2-SCALE hypothesis, geometry stop, and official sources.', '../', 'research', research(geom)),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check', action='store_true', help='verify generated pages are current without writing')
    args = p.parse_args()
    stale=[]
    for path, content in build().items():
        if args.check:
            if not path.exists() or path.read_text() != content:
                stale.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            print('Built', path.relative_to(ROOT))
    if stale:
        print('Stale generated pages:', ', '.join(stale))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
