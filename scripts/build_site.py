#!/usr/bin/env python3
"""Build the static decision desk from committed, auditable evidence.

This never creates a candidate TIFF, modifies scientific evidence, submits a
competition entry, or turns a format check into an upload authorization.
"""
from __future__ import annotations

from html import escape
import json
from pathlib import Path
import shutil

import markdown

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SCORES = {24: '0.2477', 25: '0.2600', 27: '0.2449', 28: '0.2710', 30: '0.2600', 31: '0.2708', 32: '0.2778', 33: '0.2632', 36: '0.2750'}
METHODS = {
    24: 'D1.5 dense dotted H19-5 lineage.',
    25: 'D2.8 dotted H19-5 lineage.',
    27: 'Topographic gap closure on the D1.5 base.',
    28: 'Rung30 modification on the D2.8 family.',
    30: 'Poisson-spaced off-catalogue D2.8; pixel-identical to the selected GEMSDOE25 file.',
    31: 'H27-4 solo D2.8 family; an antecedent of the B2 variant.',
    32: 'H33 B2: sparse lineage with catalogue-flank pruning.',
    33: 'Analog tip/stepover extension of the dotted family.',
    36: 'Named Anderson geothermal PINN file; its support is very close to GEMSDOE32.',
}


def page(title, body):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} · KANLER GEMS</title><meta name="description" content="Evidence-first GEMS fault-prediction submission desk.">
<link rel="stylesheet" href="style.css"><script src="status.js" defer></script></head>
<body><header class="site-header"><div class="shell nav"><a class="brand" href="index.html"><span class="brand-mark">K</span><span>KANLER <b>GEMS</b><small>SUBMISSION DESK</small></span></a><nav aria-label="Primary"><a href="index.html">Overview</a><a href="executive-summary.html">Submission guide</a><a href="hypotheses.html">Research</a><a href="science-and-sources.html">Sources</a></nav></div></header>
<main class="shell">{body}</main><footer><div class="shell footer-inner"><span>Evidence before uploads. Results before assumptions.</span><span>Maximize P(Win) · Own the Outcome</span></div></footer></body></html>\n'''


def build():
    DOCS.mkdir(exist_ok=True)
    audit = json.loads((ROOT / 'research/raster_audit.json').read_text())
    manifest = json.loads((ROOT / 'research/raster_manifest.json').read_text())
    card = json.loads((ROOT / 'research/run_card.json').read_text())
    witness = json.loads((ROOT / 'evidence/registry_witness.json').read_text())
    board = json.loads((ROOT / 'evidence/leaderboard_snapshot.json').read_text())
    if card['verdict'] != 'negative' or card['ok_to_download_and_submit'] is not False:
        raise ValueError('This static builder supports only the independently recorded negative verdict')
    reportmap = {r['site']: r for r in audit['format_reports']}
    rows, details = [], []
    for r in sorted(manifest, key=lambda x: int(x['site'].removeprefix('GEMSDOE'))):
        site = r['site']
        n = int(site.removeprefix('GEMSDOE'))
        report = reportmap[site]
        comparisons = [p for p in audit['directed_pairs'] if p['a'] == site]
        if len(comparisons) != 8 or not all(p['duplicate_gate'] for p in comparisons):
            raise ValueError(f'Historical duplicate summary disagrees with audit for {site}')
        maxrho = max(p['spearman_rho'] for p in comparisons)
        maxov = max(p['fraction_a_dots_within_3px_of_b'] for p in comparisons)
        same = [p['b'] for p in comparisons if p['decoded_pixels_equal_inside_footprint']]
        filename = Path(r['path']).name
        rows.append(f'''<tr><th scope="row"><a href="#s{n}">{site}</a></th><td><strong>{SCORES[n]}</strong><small>Owner-reported · unverified</small></td><td><a class="file" href="{escape(r['url'], quote=True)}">{escape(filename)}</a><small>Historical source only</small></td><td>Unavailable<small>No validated new holdout</small></td><td><span class="chip bad">NO</span><small>Near-duplicate among selected references</small></td><td><strong>Do not submit</strong></td></tr>''')
        exact = ('Identical in-footprint pixels to ' + ', '.join(same) + '.') if same else 'Not pixel-identical to the other selected references; still fails the near-duplicate rule.'
        details.append(f'''<article class="site-card" id="s{n}"><div class="card-top"><h3>{site}</h3><span class="chip bad">Do not submit</span></div><p>{escape(METHODS[n])}</p><p class="muted">RASTER-AUDIT · {report['positive_pixels']:,} positive pixels · max directed overlap {maxov:.1%} · max Spearman {maxrho:.4f}. {escape(exact)}</p><a href="{escape(r['url'], quote=True)}">View pinned historical source →</a></article>''')
    cont = witness['references']['continuous_gemsdoe48']
    lattice = witness['references']['calibration_lattice']
    if not cont['universal_nonempty_candidate_blocker']:
        raise ValueError('Universal-stop site text is not supported by evidence')
    board_score = escape(board['top_public_dti'])
    board_time = escape(board['observed_utc'])
    body = f'''<section class="hero"><div class="hero-copy"><p class="eyebrow"><span class="live-dot"></span> DOE GEMS PRIZE · RESEARCH WORKSPACE</p><h1>Better evidence.<br><em>Better submissions.</em></h1><p class="lead">An auditable decision desk for fault-prediction experiments. See what is known, what is not, and whether a file is safe to submit.</p><div class="hero-links"><a class="text-link" href="executive-summary.html">How submission works <span aria-hidden="true">↗</span></a><a class="text-link" href="science-and-sources.html">Read the research <span aria-hidden="true">↗</span></a></div></div><aside class="hero-side"><span class="eyebrow">PUBLIC LEADERBOARD SNAPSHOT</span><strong id="board-score">{board_score}</strong><p>Rank-one public DW-Tversky. Not our team's submission receipt or a private score.</p><p class="muted" id="board-time">Observed {board_time}</p><p id="board-freshness" class="freshness">Timestamped snapshot; freshness requires JavaScript.</p><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Open official leaderboard ↗</a></aside></section>
<section class="decision" aria-labelledby="decision-title"><div class="decision-icon" aria-hidden="true">!</div><div><p class="eyebrow">CURRENT DECISION · NEGATIVE</p><h2 id="decision-title">No new TIFF is approved for submission.</h2><p>A registered continuous raster is positive at every footprint pixel. Under the shared template's literal “positive pixel = dot” rule, every possible nonempty dot set overlaps it completely. The protocol requires us to stop, not bypass the gate. No new candidate or competition slot was used in this session.</p><div class="actions"><button type="button" class="button disabled" disabled>Submission TIFF unavailable</button><a class="button outline" href="registry_witness.json" download>Download stop evidence</a><a class="text-link" href="run_card.json">View run card →</a></div><p class="small">A semantic distinction between continuous surfaces and discrete dots may be reasonable, but changing the stated all-registry rule requires a protocol decision. We did not grant ourselves an exception.</p></div></section>
<div class="stat-grid"><article><span class="stat-label">Highest supplied historical result</span><strong>0.2778</strong><small>Owner-reported GEMSDOE32 · no organizer receipt</small></article><article><span class="stat-label">Historical pair comparisons</span><strong>72 / 72</strong><small>RASTER-AUDIT · fail the near-duplicate gate</small></article><article><span class="stat-label">Core input placement</span><strong>Restored</strong><small>Peer hashes match · official origin not authenticated</small></article></div>
<section class="section" id="comparison"><div class="section-heading"><div><p class="eyebrow">THE NINE PRIORITY SITES</p><h2>Executive comparison</h2></div><p>Historical results are owner reports, not ORGANIZER-CONFIRMED receipts. No defensible new leaderboard estimate exists. The linked files are historical sources for education, not new submission downloads.</p></div><div class="table-wrap"><table><thead><tr><th>Site</th><th>Historical result</th><th>File / source</th><th>New score estimate</th><th>Unique?</th><th>Decision</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></section>
<section class="section split"><div><p class="eyebrow">THE CHAMPION · EXPLAINED</p><h2>Why did H33 B2 lead the supplied list?</h2><p>Its documented lineage sparsifies a ridge prediction and removes a near-catalogue flank. Under the organizer's 300 m distance-weighted metric, nearby dots may cover the same fault pixel while still adding false-positive mass. Spacing can reduce this redundancy; pruning may help or hurt depending on hidden faults.</p><p>This is a plausible mechanism, not causal proof. The hidden labels and a receipt linking the exact file to the reported result are unavailable. Neither a high public score nor a lineament confirms a geothermal vent.</p><a class="text-link" href="science-and-sources.html">Read the metric and science notes →</a></div><aside class="insight"><span class="eyebrow">THE CRITICAL DISTINCTION</span><h3>A valid TIFF is not a validated discovery.</h3><p>Format, leakage, holdout performance, novelty, and the separate slot selector are independent gates. None predicts an organizer score by itself.</p><a href="executive-summary.html">Review all submission gates →</a></aside></section>
<section class="section"><div class="section-heading"><div><p class="eyebrow">INDEPENDENT AUDIT</p><h2>Why we stopped</h2></div><p>These are geometric registry measurements, not competition scores. Two counterexamples are sufficient to explain the stop; they are not a certificate for the complete registry.</p></div><div class="proof-grid"><article class="proof-card"><span class="eyebrow">REGISTERED CONTINUOUS RASTER</span><strong>{cont['candidate_within_radius_fraction']:.0%}</strong><p>of the prior E1 dots fall within 3 pixels of this reference; every footprint pixel is positive in the reference.</p><a href="{escape(cont['source'], quote=True)}">Pinned witness ↗</a></article><article class="proof-card"><span class="eyebrow">REGISTERED CALIBRATION LATTICE</span><strong>{lattice['candidate_within_radius_fraction']:.1%}</strong><p>of prior E1 dots fall within 3 pixels of the lattice. The earlier nine-file-only uniqueness claim excluded it.</p><a href="{escape(lattice['source'], quote=True)}">Pinned lattice ↗</a></article><article class="proof-card"><span class="eyebrow">SURFACE / HOLDOUT</span><strong>Not run</strong><p>No new candidate surface, withheld-positive count, confidence interval or score estimate was generated after the stop.</p><a href="run_card.json">Machine-readable run card ↗</a></article></div><p class="callout">Previous E1 claims are withdrawn: the old audit omitted registered references, its quadrant split did not hide whole connected components, and its fixed-map holdout used a full-catalogue-pruned prediction. <a href="lane-e1-xg-hgb.html">Read the correction.</a></p></section>
<section class="section"><div class="section-heading"><div><p class="eyebrow">HISTORICAL REFERENCES</p><h2>Site-by-site notes</h2></div><p>Each card describes one selected historical artifact. Shared pixels and high overlap are not independent geological strategies.</p></div><div class="site-grid">{''.join(details)}</div></section>
<section class="section sources"><div><p class="eyebrow">WHAT COMES NEXT</p><h2>Resolve, then test.</h2><p>Clarify the registry's surface-versus-dot semantics and exclusive lane; freeze a complete registry and a comparable fold-local best; then test the preregistered physical hypothesis with per-feature canaries and buffered whole-segment holdout. No live slot should be spent on a failed or untested idea.</p><a class="button dark" href="hypotheses.html">See the research queue</a></div><div class="source-list"><span class="eyebrow">PRIMARY SOURCES</span><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">DrivenData · task, metric & format ↗</a><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">NLR · official prize rules ↗</a><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS · GeoDAWN data release ↗</a><a href="https://gdr.openei.org/submissions/1391">DOE GDR · INGENIOUS compilation ↗</a><a href="data_readiness.json">Local data-integrity evidence →</a></div></section>'''
    (DOCS / 'index.html').write_text(page('Decision desk', body))

    guide = '''<div class="subpage"><a class="back" href="index.html">← Back to decision desk</a><p class="eyebrow">EXECUTIVE SUBMISSION GUIDE</p><h1>From evidence<br><em>to upload.</em></h1><p class="lead">A practical checklist for the competition, with the current release decision first.</p></div>
<section class="decision compact"><div class="decision-icon" aria-hidden="true">!</div><div><p class="eyebrow">CURRENT STATUS</p><h2>Do not submit. No approved TIFF exists.</h2><p>The literal registry stop is active. Downloading an old file or changing its name does not make a new qualifying submission.</p><a class="text-link" href="registry_witness.json">Review the automated witness →</a></div></section>
<section class="section guide-grid"><div><h2>1. Generate within the assigned lane</h2><p>First resolve the full-registry support definition and exclusive lane. Reuse the shared feature cache, evaluator and writer. The repository's guarded commands fail closed while the witness remains decisive.</p></div><div><h2>2. Prove scientific eligibility</h2><p>Run every feature alone as a leakage canary; use buffered whole-segment holdout, visible-only catalogue features, pixel-exact visible masking and the pooled metric. Require a positive paired confidence interval against the frozen current best.</p></div><div><h2>3. Prove novelty and format</h2><p>Check surface before placement and final dots against the complete registry. Reopen the exact output and validate one float32 band, exact sample CRS/shape/transform and finite values within [0,1]. Record the SHA-256, a distinct name and a note of at most 140 characters. Format validity is not approval.</p></div><div><h2>4. Separate selector and upload</h2><p>Only after all gates pass, the separate selector checks the current rules and authenticated weekly allowance. Download the approved exact-byte TIFF (or one-TIFF ZIP), open <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DrivenData</a>, choose “Submit” → “Make new submission,” select the file and enter its note. Save the organizer receipt tied to the file hash.</p></div></section>
<section class="section notice"><h2>Diagnosing the [0, 1] range error</h2><p>The failed file was not supplied, so its cause is unknown. NaNs, infinities, negative nodata sentinels and out-of-range values are possible causes. The local strict validator checks every decoded pixel, including outside the footprint; it rejects invalid output rather than silently clipping it. Zero-outside is a conservative experiment to avoid nonfinite values, not a guarantee of portal acceptance or an authenticated substitute for the official sample.</p><pre><code>python scripts/validate_raster.py candidate.tif data/sample_submission.tif</code></pre><p>Exit code zero means local format checks passed, not scientific eligibility or organizer acceptance.</p></section>
<section class="section"><h2>Rules and remaining allowance</h2><p>The <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">official NLR rules</a> describe up to three submissions per week and selecting one submission for both prize rounds; the team's remaining allowance is unknown without the authenticated page. The rules also describe code/documentation and generative-AI disclosure requirements. Check the current competition page and rules before acting.</p><p>Our data files are pinned public mirrors, not independently authenticated organizer downloads. The organizer data page redirects to login. No credentials are stored or requested by this project.</p></section>'''
    (DOCS / 'executive-summary.html').write_text(page('Submission guide', guide))
    withdrawal = '''<div class="subpage"><a class="back" href="index.html">← Back to decision desk</a><p class="eyebrow">ARCHIVED LANE REVIEW</p><h1>Prior E1 claims<br><em>withdrawn.</em></h1></div><section class="decision compact"><div class="decision-icon">!</div><div><h2>Not a submission recommendation.</h2><p>The earlier E1 artifact is kept in repository quarantine for reproducibility, not as a live upload. Its claimed full-registry uniqueness and holdout-based ranking are not supported by the literal protocol. The independent witness records exact dot overlap; its format receipt alone cannot authorize submission.</p><a class="text-link" href="registry_witness.json">See independent witness →</a></div></section><section class="section"><h2>What changed</h2><ul><li>The earlier audit considered only nine priority files and excluded a registered lattice. A registered continuous raster also has positive support across the entire footprint.</li><li>The quadrant split could retain parts of a withheld connected component. The fixed-map hide-and-recover test used predictions built with the full catalogue; it is not a fold-local rebuild.</li><li>Prior code, figures and raster bytes remain in repository quarantine. The numerical live-score projection is not a score and has been removed from the public decision desk.</li></ul><p><a href="science-and-sources.html">Read the source and limitations register →</a></p></section>'''
    (DOCS / 'lane-e1-xg-hgb.html').write_text(page('Prior E1 review', withdrawal))
    alias = '''<div class="subpage"><a class="back" href="index.html">← Back to decision desk</a><h1>Submission guide</h1><p class="lead">The current decision and complete upload checklist are in the executive guide.</p><a class="button dark" href="executive-summary.html">Open the submission guide →</a></div>'''
    for name in ('how-to-submit.html', 'submission.html'):
        (DOCS / name).write_text(page('Submission guide', alias))
    for name in ('raster_audit.json', 'raster_manifest.json', 'source_manifest.json', 'run_card.json', 'hypotheses.md', 'science-and-sources.md', 'template-fixes.md'):
        shutil.copyfile(ROOT / 'research' / name, DOCS / name)
    for name in ('registry_witness.json', 'data_readiness.json', 'leaderboard_snapshot.json', 'selector_decision.json'):
        shutil.copyfile(ROOT / 'evidence' / name, DOCS / name)
    shutil.copyfile(ROOT / 'vendor/template/pins.json', DOCS / 'template-pins.json')
    for stem, title in (('hypotheses', 'Research queue'), ('science-and-sources', 'Science and sources'), ('template-fixes', 'Shared template fixes')):
        text = (ROOT / 'research' / (stem + '.md')).read_text()
        # Markdown is also available in the repo. Rewrite only local links to
        # the copies bundled with the static site; external source URLs stay pinned.
        text = text.replace('../evidence/', '').replace('../vendor/template/pins.json', 'template-pins.json')
        text = text.replace('template-fixes.md', 'template-fixes.html')
        html = markdown.markdown(text, extensions=['tables', 'fenced_code'])
        (DOCS / (stem + '.html')).write_text(page(title, '<article class="section prose">' + html + '</article>'))
    shutil.copyfile(ROOT / 'research/run_card.json', ROOT / 'evidence/run_card.json')
    shutil.copyfile(ROOT / 'research/run_card.json', DOCS / 'run-card.json')


if __name__ == '__main__':
    build()
