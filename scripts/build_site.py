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


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def header(active: str) -> str:
    pages = [("index.html", "Overview"), ("executive-summary.html", "Executive summary"),
             ("submission-table.html", "Site comparison"), ("research.html", "Research"),
             ("irregularities.html", "Open issues")]
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


def focus_table(audit):
    """The nine archived files are verified downloads, never slot recommendations."""
    rows = []
    for r in audit["focus_nine"]:
        name = Path(r["path"]).name
        path = DOCS / "downloads" / name
        if not path.is_file() or sha(path) != r["sha256"]:
            raise SystemExit(f"Focus artifact missing or differs from audited hash: {name}")
        overlap = 100 * r["max_directional_focus_overlap_within_3px"]
        rows.append(
            f'<tr><td><a href="{esc(r["site_url"])}">{esc(r["site"])} ↗</a>'
            f'<small>{r["positive_pixels"]:,} positive pixels</small></td>'
            f'<td class="file"><a href="downloads/{esc(name)}" download>{esc(name)}</a>'
            f'<small>SHA-256 {esc(r["sha256"])}</small></td>'
            f'<td><strong>{r["owner_reported_score"]:.4f}</strong><small>USER/OWNER-REPORTED; no receipt</small></td>'
            f'<td><strong>{overlap:.2f}%</strong><small>vs {esc(r["nearest_focus_site"])}, directional</small></td>'
            '<td><span class="pill stop">Do not submit</span><small>Duplicate; research only</small></td></tr>'
        )
    return ('<div class="table-wrap"><table><thead><tr><th>Focus site</th>'
            '<th>Exact archived TIFF</th><th>Historical reported value</th>'
            '<th>Nearest focus overlap</th><th>New-slot decision</th></tr></thead><tbody>'
            + "".join(rows) + '</tbody></table></div>')


def main():
    audit = read_json(ROOT / "evidence/release_recheck_20261027.json")
    card = read_json(ROOT / "evidence/current_run_card.json")
    revalidation = read_json(ROOT / "evidence/dslup_literal_revalidation_20261027.json")
    if (audit.get("verdict") != "negative" or card.get("verdict") != "negative"
            or card.get("ok_to_submit") is not False
            or card.get("generated_utc") != audit.get("generated_utc")
            or revalidation.get("verdict") != "negative"
            or revalidation.get("ok_to_submit") is not False):
        raise SystemExit("Site build requires a matching negative audit, validation and run card; refusing stale or positive card")

    pre = audit["preflight"]
    prior = audit["prior_candidate"]
    s2_name = revalidation["raster_filename"]
    files = {row["file"]: row for row in audit["all_local_candidate_artifacts"]}
    s2 = files[s2_name]
    hyp1 = next(row for name, row in files.items() if "unique-hypothesis1-binary" in name)
    reduced = next(row for name, row in files.items() if name.startswith("36GEMSDOE-") and name.endswith("-zeros.tif"))
    reduced_validation = read_json(ROOT / "evidence/off36_literal_revalidation_20261027.json")
    if (reduced_validation.get("ok_to_submit") is not False
            or reduced_validation.get("verdict") != "negative"
            or reduced_validation.get("raster_sha256") != reduced["sha256"]
            or reduced_validation["gates"]["assigned_37654_dot_budget_matches"] is not False):
        raise SystemExit("Reduced-budget validation is stale or unsafe; refusing to publish")
    if (s2["sha256"] != revalidation["raster_sha256"]
            or s2["duplicate_under_literal_rule"] is not True
            or revalidation["gates"]["literal_witness_not_duplicate"] is not False):
        raise SystemExit("Inconsistent Session-2 audit/validation; refusing to publish")
    for item in (prior, s2, hyp1, reduced):
        artifact_path = DOCS / "downloads" / item["file"]
        if not artifact_path.is_file() or sha(artifact_path) != item["sha256"]:
            raise SystemExit("Prior research artifact missing or differs from audited hash")

    old = read_json(ROOT / "evidence/dslup_unique_slot_run_card.json")
    if old.get("raster_sha256") != s2["sha256"]:
        raise SystemExit("Historical Session-2 card refers to a different TIFF")
    hr = old["holdout_dti"]["primary_hide_and_recover"]
    sg = old["holdout_dti"]["secondary_off_catalogue_sgmc"]
    table = focus_table(audit)
    minimum = 100 * pre["minimum_directional_overlap"]
    s2_overlap = 100 * s2["witness_overlap_fraction"]
    prior_overlap = 100 * prior["witness_overlap_fraction"]

    # Always overwrite formerly positive feeds; positive paths require a new,
    # independently implemented selector, not a change to a template string.
    data = DOCS / "data"
    data.mkdir(parents=True, exist_ok=True)
    feed = {
        "generated_utc": audit["generated_utc"],
        "source_audit": "evidence/release_recheck_20261027.json",
        "source_run_card": "evidence/current_run_card.json",
        "research_artifact_sha256": prior["sha256"],  # legacy reader compatibility; not authorization
        "submission": {"verdict": "negative", "ok_to_submit": False,
                       "current_candidate": None, "slot_spent_this_review": False},
        "archived_dslup": {"verdict": "negative", "ok_to_submit": False,
                           "research_only": True, "filename": s2["file"],
                           "sha256": s2["sha256"],
                           "literal_witness_overlap": s2["witness_overlap_fraction"]},
        "archived_reduced_budget": {"verdict": "negative", "ok_to_submit": False,
                                    "research_only": True, "filename": reduced["file"],
                                    "sha256": reduced["sha256"], "dots": reduced["inside_positive_pixels"],
                                    "literal_witness_overlap": reduced["witness_overlap_fraction"],
                                    "full_registry_cleared": False},
        "forced_budget_witness": {"budget": pre["candidate_dot_budget"],
                                  "minimum_overlap_fraction": pre["minimum_directional_overlap"]},
        "leaderboard_source": "public_leaderboard.json",
        "warning": "Historical holdouts and owner-reported values are not organizer-confirmed scores. All TIFFs are research only.",
    }
    (data / "status_feed.json").write_text(json.dumps(feed, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    for filename in ("run_card.json", "current_run_card.json"):
        (data / filename).write_text(json.dumps(card, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    home = f'''<div class="breadcrumb">DOE GEMS PRIZE &nbsp; / &nbsp; <span>Decision dashboard</span></div>
<section class="hero" aria-labelledby="hero-title"><div><div class="eyebrow">Geological fault discovery · 27 October 2026 review</div><span class="status">Submission on hold</span>
<h1 id="hero-title">No submission<br>cleared yet.</h1><p class="lead">The literal all-registry rule blocks the assigned 37,654-dot budget. A previous promotion exempted a calibration lattice without authorization; that decision is withdrawn.</p>
<div class="hero-actions"><a class="btn" href="executive-summary.html">View evidence &amp; submission guide →</a><a class="btn secondary" href="submission-table.html">Compare nine sites</a></div>
<p class="note"><strong>DO NOT SUBMIT.</strong> No new TIFF, holdout score, leaderboard estimate, or live-slot decision was produced in this review.</p></div>
<div class="hero-aside"><div class="eyebrow">Fresh exact-file check</div><h3>Archived DSLUP TIFF</h3><p><strong>{s2_overlap:.4f}%</strong> of its dots fall within 3 pixels of the registered lattice, above the 70% limit.</p><p>Local format checks pass; portal acceptance and independent holdout replay are not established.</p><a href="downloads/{esc(s2["file"])}" download>Download archived TIFF · research only ↗</a><div class="hash mono">SHA-256 {esc(s2["sha256"])}</div></div></section>
<div class="metrics" aria-label="Decision metrics"><div class="metric"><div class="label">DSLUP duplicate overlap</div><div class="value">{s2_overlap:.2f}%</div><div class="hint">{s2["witness_overlap_dots"]:,} of {s2["inside_positive_pixels"]:,} dots · ≤70% required</div></div>
<div class="metric"><div class="label">Minimum possible</div><div class="value">{minimum:.2f}%</div><div class="hint">Any {pre["candidate_dot_budget"]:,} distinct in-footprint dots · same witness</div></div>
<div class="metric"><div class="label">New experiments</div><div class="value">0</div><div class="hint">Stopped before fitting or placing dots</div></div>
<div class="metric"><div class="label"><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Public #1 DW-Tversky ↗</a></div><div class="value" id="leader-value">—</div><div class="hint" id="leader-status">Loading dated public snapshot…</div><noscript><span class="note">JavaScript disabled; view the official leaderboard.</span></noscript></div></div>
<section class="section"><div class="section-head"><div><div class="eyebrow">Start here</div><h2>One result, three different questions.</h2><p>A valid-looking file is not necessarily a distinct or high-scoring submission.</p></div></div><div class="grid-three">
<article class="card"><div class="card-icon">01</div><h3>Is the file in range?</h3><p>Locally, yes: one float32 band on the mirror grid, with finite whole-array values in [0, 1]. The mirror uses NaN outside its irregular footprint; this file uses zeros. Portal acceptance is unverified.</p></article>
<article class="card"><div class="card-icon">02</div><h3>Is it unique?</h3><p>No under the literal rule. A single registered witness proves failure. A different file hash or an alternate control-separated calculation does not override that stop.</p></article>
<article class="card"><div class="card-icon">03</div><h3>Will it score higher?</h3><p>Unknown. The historical holdout procedures were not independently replayed in this review. No reliable leaderboard projection or organizer receipt establishes a gain.</p></article></div></section>
<section class="section"><div class="section-head"><div><div class="eyebrow">The evidence</div><h2>Why the stop is unavoidable</h2><p>Exact counting on the pinned owner-mirror sample footprint and registered lattice.</p></div><a class="section-link" href="irregularities.html">See all open issues →</a></div><div class="grid-two">
<div class="card"><h3>The constraint</h3><p>The witness covers <strong>{pre["covered_pixels_within_3px"]:,}</strong> of {pre["footprint_pixels"]:,} footprint pixels within 3 px. Only <strong>{pre["uncovered_pixels"]:,}</strong> are outside its neighborhood.</p><p>For any {pre["candidate_dot_budget"]:,} distinct dots, at least {pre["minimum_overlapping_dots"]:,} must be inside it: <strong>{minimum:.4f}%</strong>.</p><p class="note">This bound is specific to this budget, footprint, witness and radius. It does not prove every smaller raster fails. Do not change the frozen budget to evade the stop.</p></div>
<div class="card"><h3>What we restored</h3><p>Four core, twelve scored and nine focus TIFF mirrors were hash-verified. The 30-column feature matrix was prepared without fitting a model. Fifteen of thirty external entries verified; the remainder returned 404.</p><p>Mirror hashes do not authenticate organizer origin. Bulk inputs live in an ephemeral cache; account quota, complete registry and independent holdout remain unavailable.</p><a class="section-link" href="../evidence/release_recheck_20261027.json">Open exact-byte audit ↗</a></div></div></section>
<section class="section"><div class="section-head"><div><div class="eyebrow">Focus sites</div><h2>The nine-site picture</h2><p>The largest historical value is GEMSDOE32’s 0.2778; it is user-reported, not a file-linked organizer receipt.</p></div><a class="section-link" href="submission-table.html">Full comparison →</a></div><div class="callout"><strong>No defensible leaderboard estimate for a new file.</strong><p>The nine archived results are unconfirmed reports; the locally replayed geometry is evidence of overlap, not of hidden-truth accuracy.</p></div></section>'''

    summary = f'''<div class="breadcrumb"><a href="index.html">Decision dashboard</a> &nbsp; / &nbsp; <span>Executive summary</span></div><div class="page-intro"><div class="eyebrow">Decision brief · 27 October 2026</div><h1>What to download.<br>What not to submit.</h1><p>There is currently <strong>no competition-ready, uniquely cleared file</strong>. The files below are historical research artifacts, not slot recommendations.</p></div>
<div class="callout red-callout"><strong>NO FILE AUTHORIZED. DO NOT SUBMIT.</strong><p>The former Session-2 and Session-1 promotion claims are withdrawn: neither an exemption for a lattice nor an alternate slot policy appears in the literal user protocol. A selector cannot waive a failed required gate.</p></div>
<section class="section"><div class="section-head"><div><div class="eyebrow">Archived candidates</div><h2>Exact downloads, not submit recommendations</h2><p>No public-score estimate or organizer acceptance is established for these files.</p></div></div><div class="table-wrap"><table><thead><tr><th>Research file and hash</th><th>Recorded holdout procedure</th><th>Literal lattice overlap</th><th>Decision</th></tr></thead><tbody>
<tr><td class="file"><a href="downloads/{esc(s2["file"])}" download>{esc(s2["file"])}</a><small>SHA-256 {esc(s2["sha256"])}</small></td><td><strong>{hr["pooled_dti"]:.6f}</strong><small>{esc(hr["label"])}<br>Historical procedure; not independently replayed and not a score for the final TIFF.</small><strong>{sg["sgmc_prevalence_calibrated_dti"]:.6f}</strong><small>{esc(sg["label"])}<br>Historical procedure; not independently replayed.</small></td><td>{s2_overlap:.4f}%<small>{s2["witness_overlap_dots"]:,} / {s2["inside_positive_pixels"]:,} dots</small></td><td><span class="pill stop">Do not submit</span><small><a href="../evidence/dslup_literal_revalidation_20261027.json">Fresh validator ↗</a></small></td></tr>
<tr><td class="file"><a href="downloads/{esc(prior["file"])}" download>{esc(prior["file"])}</a><small>SHA-256 {esc(prior["sha256"])}</small></td><td><strong>{audit["historical_holdout_not_replayed"]["dti"]:.6f}</strong><small>HOLDOUT-DTI · {esc(audit["historical_holdout_not_replayed"]["evaluator_version"])} · {audit["historical_holdout_not_replayed"]["withheld_positive_occurrences"]:,} withheld-positive occurrences · 95% CI [{audit["historical_holdout_not_replayed"]["ci95"][0]:.6f}, {audit["historical_holdout_not_replayed"]["ci95"][1]:.6f}]<br>Historical receipt; not replayed here.</small></td><td>{prior_overlap:.4f}%<small>{prior["witness_overlap_dots"]:,} / {prior["inside_positive_pixels"]:,} dots</small></td><td><span class="pill stop">Do not submit</span></td></tr>
<tr><td class="file"><a href="downloads/{esc(hyp1["file"])}" download>{esc(hyp1["file"])}</a><small>SHA-256 {esc(hyp1["sha256"])}</small></td><td>Not measured<small>No independent holdout or organizer receipt.</small></td><td>{100*hyp1["witness_overlap_fraction"]:.4f}%<small>{hyp1["on_catalogue_positive_pixels"]} known-fault pixels; contradicts the old note</small></td><td><span class="pill stop">Do not submit</span></td></tr>
<tr><td class="file"><a href="downloads/{esc(reduced["file"])}" download>{esc(reduced["file"])}</a><small>SHA-256 {esc(reduced["sha256"])}</small></td><td>Not measured<small>No independent holdout or organizer receipt.</small></td><td>{100*reduced["witness_overlap_fraction"]:.2f}%<small>Witness alone does not establish uniqueness. {reduced["on_catalogue_positive_pixels"]} known-fault pixels.</small></td><td><span class="pill stop">Do not submit</span><small>15,000 dots, not the frozen 37,654; lattice-gap placement.</small></td></tr></tbody></table></div><p class="note">The 82.34% forced bound applies only to the frozen 37,654-dot budget. A smaller file can pass this one witness yet fail the assigned method and other required gates.</p></section>
<section class="section"><div class="section-head"><div><div class="eyebrow">Evidence table</div><h2>Nine historical site leaders</h2><p>Reported numbers are <strong>USER/OWNER-REPORTED</strong>; no organizer submission-page receipts tie them to these bytes. No estimated DTI for a new file is available.</p></div></div>{table}<p class="note">Overlap is directional: the fraction of a row’s dots within 3 px of its closest other focus raster. Every row fails at least one focus comparison; this is not a complete current-registry clearance.</p></section>
<section class="section"><div class="section-head"><div><div class="eyebrow">For a future approved candidate</div><h2>How submission will work</h2><p>Instructions only. No weekly slot was used in this review.</p></div></div><div class="grid-two"><div class="card"><ol class="steps"><li><strong>Resolve the protocol and run the gates.</strong> With proper authorization, require visible-only catalogue features, every feature canary, buffered comparable holdout with CI, literal full-registry checks before and after placement, and verified current quota.</li><li><strong>Use the separate selector.</strong> Download only an exact, SHA-identified future file cleared by an independent selector; a local format pass is not approval.</li><li><strong>Open DrivenData → Submit → Make new submission.</strong> Select the approved TIFF or its single-TIFF ZIP and enter the unique name and note of at most 140 characters.</li><li><strong>Record the organizer receipt.</strong> Only an actual submission-page receipt can establish a file-linked live score.</li></ol></div><div class="card"><h3>Format versus acceptance</h3><p>The <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">official format</a> specifies a single float32 band in [0,1], EPSG:32611 and the supplied 100 m grid, with null/NaN outside bounds. The mirror’s irregular exterior is NaN; these files store zeros there.</p><p>The earlier <code>Predicted values must be in range [0, 1]</code> rejection has no retained rejected-file bytes or organizer diagnosis. A local check does not prove portal acceptance or diagnose that rejection.</p><p><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">Official competition &amp; rules ↗</a></p></div></div></section>'''

    submission_table = f'''<div class="breadcrumb"><a href="index.html">Decision dashboard</a> &nbsp; / &nbsp; <span>Site comparison</span></div><div class="page-intro"><div class="eyebrow">Nine focus sites</div><h1>Historical results, clearly labeled.</h1><p>These exact TIFFs are for forensic research. None is authorized for a new weekly slot.</p></div>
<div class="callout red-callout"><strong>Every row is a duplicate under the requested overlap rule.</strong><p>Scores are user/owner-reported without file-linked organizer receipts; they are not estimated scores for a new submission. Values and dated public ranks may have changed.</p></div>
<section class="section">{table}<p class="note">Fraction = row dots within 3 pixels of the closest other focus TIFF. Hashes are pinned to owner-mirror bytes. Complete current-registry coverage was not established.</p></section>
<section class="section"><div class="section-head"><div><div class="eyebrow">Mechanistic evidence</div><h2>What the masks actually show</h2></div></div><div class="grid-three"><article class="card"><h3>32 vs 25</h3><p>GEMSDOE32’s positive mask equals GEMSDOE25’s after removing 6,436 dots within 2 pixels of the known-fault raster. This pruning could improve precision, but cannot explain the reported scores causally without receipts or hidden labels.</p></article><article class="card"><h3>25 vs 30</h3><p>The two files have identical positive masks despite different names and file bytes. Their reported values are equal; file hash alone is not method novelty.</p></article><article class="card"><h3>36 vs 32</h3><p>GEMSDOE36 contains all GEMSDOE32 positives plus 1,200 additional pixels. Additional predictions need not improve DTI: the precision cost depends on unknown hidden truth.</p></article></div></section>'''

    research = f'''<div class="breadcrumb"><a href="index.html">Decision dashboard</a> &nbsp; / &nbsp; <span>Research agenda</span></div><div class="page-intro"><div class="eyebrow">Prioritized, untested hypotheses</div><h1>Physical signals, not score forecasts.</h1><p>These are future research directions, not an authorization to leave the assigned lane or fit before the current stop is resolved.</p></div>
<div class="callout"><strong>None is validated.</strong><p>Expected DTI effects are hypotheses, not measured scores. Official access, exact local coverage, scientific usefulness, fold-safe construction and fleet novelty remain open; the detailed <a href="../research/2026-10-27_htcads_hypotheses.md">preregistered-style slate</a> contains transforms, mimics, costs and access checks.</p></div>
<section class="section"><div class="grid-two"><article class="card"><div class="eyebrow">01 · Highest priority</div><h3>Height-persistent gravity–magnetic edges</h3><p>Combine multiscale upward-continued gravity and magnetics with independent hydrothermal evidence; test whether persistent aligned boundaries identify buried structures beyond simple terrain lineaments. Mimic: basin contacts, flight-line artifacts and lithologic edges.</p></article><article class="card"><div class="eyebrow">02 · Follow-on</div><h3>Thermal-transport direction uncertainty</h3><p>Test whether a family of plausible probe and spring/well transport directions intersects structural ridges. Mimic: groundwater flow, seasonal or land-use temperature anomalies and saline playas.</p></article><article class="card"><div class="eyebrow">03 · Follow-on</div><h3>Visible fault-tip orientation consistency</h3><p>Compare fold-visible fault tips with potential-field and detrended-elevation gradient orientations. Recompute catalogue features for every split. Mimic: a drainage-aligned escarpment or a continuing lithologic boundary.</p></article><article class="card"><div class="eyebrow">04 · Higher access risk</div><h3>Interferometric strain discontinuity</h3><p>Test persistent, atmosphere-corrected InSAR displacement gradients with independent geometry. Mimic: aquifer pumping, subsidence and atmospheric delay; exact OPERA tiles and access have not been verified.</p></article></div></section>
<section class="section"><div class="section-head"><div><div class="eyebrow">Primary sources</div><h2>Why these signals merit investigation</h2></div></div><div class="card"><ul class="sources"><li><a href="https://www.usgs.gov/publications/discovering-blind-geothermal-systems-great-basin-region-integrated-geologic-and">USGS Nevada play-fairway study ↗</a> describes a blind geothermal case with a structural transfer zone, gravity gradients, magnetic low, temperature and resistivity anomalies. It motivates corroboration, not a DTI gain.</li><li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN ↗</a> lists airborne magnetic and radiometric data (CC0); survey artifacts and local coverage must be tested.</li><li><a href="https://gdr.openei.org/submissions/1391">DOE GDR INGENIOUS compilation ↗</a> includes fault, thermal, well and related datasets (CC BY 4.0); licensing of derived layers and leakage still require checks.</li><li><a href="https://www.usgs.gov/3d-elevation-program">USGS 3DEP ↗</a> describes free, unrestricted elevation products; exact tiles and preprocessing are not yet verified.</li><li><a href="https://www.earthdata.nasa.gov/data/projects/opera">NASA OPERA ↗</a> describes U.S. displacement products; access and fitness for these candidate hypotheses are not established.</li></ul></div></section>'''

    issues = f'''<div class="breadcrumb"><a href="index.html">Decision dashboard</a> &nbsp; / &nbsp; <span>Open issues</span></div><div class="page-intro"><div class="eyebrow">Fail closed</div><h1>What remains unresolved.</h1><p>The negative decision is deliberate: no model fit, TIFF emission or live submission is justified by the current evidence.</p></div>
<section class="section"><div class="grid-two"><div class="card"><h3>Literal registry conflict</h3><p>At this specific fixed budget, ≥{minimum:.4f}% must overlap the registered lattice within 3 px. The requested maximum is 70%; calibration grids have no exemption. Stop before placement. Any change requires a new, explicitly authorized protocol rather than evasion.</p></div><div class="card"><h3>Authenticity &amp; incomplete data</h3><p>DrivenData data require login. Hash-pinned owner mirrors are not authenticated organizer bytes. Restoration verified 31 of 46 manifest files; 14 DEM10 files depend on a deleted ref and one heat-flow CSV is missing. Re-run the restore tool; it writes a partial receipt and exits nonzero.</p></div><div class="card"><h3>Uniqueness &amp; leakage</h3><p>One witness proves failure; it does not prove complete registry coverage. Pre-placement surface ranks, every feature canary and independent fold-safe holdouts remain unreplayed. Six declared benchmark cards and three historical verifier modules are missing, so the current-best inventory is incomplete.</p></div><div class="card"><h3>Portal &amp; quota</h3><p>Current account quota is unknown. The [0,1] rejection’s file bytes and diagnosis were not retained. Whole-array local checks do not demonstrate acceptance; zero-filled versus NaN exterior remains an ambiguity, not a proven fix.</p></div></div>
<div class="callout red-callout"><strong>Parallel artifacts are not exceptions.</strong><p>The PR #34 TIFF overlaps the lattice {100*hyp1["witness_overlap_fraction"]:.4f}% and has {hyp1["on_catalogue_positive_pixels"]} on-catalogue dots. The PR #36 TIFF uses only {reduced["inside_positive_pixels"]:,} dots and deliberately fills lattice gaps; its {100*reduced["witness_overlap_fraction"]:.2f}% witness overlap does not clear the assigned budget, full registry, holdout or quota. Both are research-only.</p></div>
<p><a href="../evidence/current_run_card.json">Current negative JSON run card ↗</a> · <a href="../evidence/release_recheck_20261027.json">Exact-byte recheck ↗</a> · <a href="../evidence/independent_witness_20261027.json">Independent witness review ↗</a> · <a href="../evidence/data_restore_recheck_20261027.json">Partial restore receipt ↗</a> · <a href="../evidence/dslup_literal_revalidation_20261027.json">DSLUP validator ↗</a> · <a href="../evidence/off36_literal_revalidation_20261027.json">15,000-dot validator ↗</a></p></section>'''

    for filename, title, body in (
        ("index.html", "Decision dashboard", home),
        ("executive-summary.html", "Executive summary", summary),
        ("submission-table.html", "Nine-site comparison", submission_table),
        ("research.html", "Research agenda", research),
        ("irregularities.html", "Open issues", issues),
        # Preserve older incoming links without publishing stale contradictory content.
        ("audit-review.html", "Open issues", issues),
        ("submission-howto.html", "Executive summary and submission guide", summary),
    ):
        script = FEED_SCRIPT if filename == "index.html" else ""
        (DOCS / filename).write_text(page(title, filename, body, script), encoding="utf-8")
    print("Built fail-closed Pages dashboard; all archived TIFFs are research-only.")


if __name__ == "__main__":
    main()
