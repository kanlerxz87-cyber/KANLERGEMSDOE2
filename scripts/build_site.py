#!/usr/bin/env python3
"""Build the fail-closed static evidence portal from committed audit records.

This builder has no positive authorization path. It verifies that the published
current card and release audit are negative and internally consistent before it
renders any page; archived rasters are linked only as historical research files.
"""
from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
EXPECTED_FOCUS = {
    "GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
    "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36",
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"Cannot read required evidence {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"Evidence must be a JSON object: {path.relative_to(ROOT)}")
    return data


def header(active: str) -> str:
    pages = [
        ("index.html", "Overview"),
        ("executive-summary.html", "Decision & sites"),
        ("research.html", "Hypotheses"),
        ("irregularities.html", "Open issues"),
    ]
    links = "".join(
        '<a href="{}"{}>{}</a>'.format(
            path,
            ' class="active" aria-current="page"' if path == active else "",
            label,
        )
        for path, label in pages
    )
    return f'''<a class="skip" href="#main">Skip to content</a>
<header class="topbar"><div class="wrap topbar-inner">
  <a href="index.html" class="brand" aria-label="GEMS Fieldnotes home"><span class="brand-mark">G</span><span class="brand-name">GEMS / FIELDNOTES<small>KANLERGEMSDOE2 · EVIDENCE PORTAL</small></span></a>
  <nav class="nav" aria-label="Main navigation">{links}<a href="https://github.com/kanlerxz87-cyber/KANLERGEMSDOE2">Repository ↗</a></nav>
</div></header>'''


def page(title: str, active: str, content: str, script: str = "") -> str:
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · GEMS Fieldnotes</title><meta name="description" content="Evidence-led, fail-closed review of geothermal fault submissions for the DOE GEMS Prize.">
<link rel="stylesheet" href="style.css"></head><body>{header(active)}
<main id="main" class="wrap">{content}</main>
<footer class="footer"><div class="wrap footer-inner"><div><strong>GEMS / FIELDNOTES</strong><br>Evidence before a submission slot.</div><div>Maximize P(Win) · Own the Outcome<br>Research artifacts are not submission authorization.</div><div><a href="data/status_feed.json">Status feed ↗</a> · <a href="../evidence/current_run_card.json">Current run card ↗</a></div></div></footer>{script}</body></html>'''


LEADERBOARD_SCRIPT = '''<script>
(async function () {
  const score = document.getElementById('public-top-score');
  const label = document.getElementById('public-top-label');
  if (!score || !label) return;
  try {
    const response = await fetch('data/public_leaderboard.json', {cache: 'no-store'});
    if (!response.ok) throw new Error('feed unavailable');
    const feed = await response.json();
    const snapshot = (feed.status === 'success' || feed.status === 'verified_snapshot')
      ? feed : feed.last_verified_snapshot;
    if (!snapshot || typeof snapshot.top_public_dti !== 'number'
        || snapshot.top_public_dti < 0 || snapshot.top_public_dti > 1) {
      score.textContent = 'Unavailable';
      label.textContent = 'No verified public snapshot';
      return;
    }
    score.textContent = snapshot.top_public_dti.toFixed(4);
    const stale = feed.status === 'unavailable';
    const when = snapshot.observed_utc || 'date not recorded';
    label.textContent = (stale ? 'Refresh failed; last verified snapshot · ' : 'Public leaderboard snapshot · ')
      + when + ' · not a score for our file';
  } catch (_) {
    score.textContent = 'Unavailable';
    label.textContent = 'Feed could not be loaded';
  }
})();
</script>'''


def focus_table(rows: list[dict[str, Any]], safety_by_sha: dict[str, dict[str, Any]]) -> str:
    output = []
    for row in sorted(rows, key=lambda r: (-float(r["owner_reported_score"]), r["site"])):
        name = Path(row["path"]).name
        local = DOCS / "downloads" / name
        if not local.is_file():
            raise SystemExit(f"Historical file missing from download directory: {name}")
        actual_sha = hashlib.sha256(local.read_bytes()).hexdigest()
        if actual_sha != row["sha256"]:
            raise SystemExit(f"Historical download differs from pinned evidence: {name}")

        overlap = 100.0 * float(row["max_directional_focus_overlap_within_3px"])
        safety = safety_by_sha[actual_sha]
        exterior = str(safety["outside_footprint_mode"])
        site_link = row.get("site_url", "")
        checks = safety["checks"]
        local_status = "PASS" if safety.get("all_checks_passed") is True else "FAIL"
        output.append(f'''<tr>
<td><strong><a href="{esc(site_link)}">{esc(row['site'])} ↗</a></strong><small>Historical mirror · {esc(exterior)} outside</small></td>
<td class="file"><a href="downloads/{esc(name)}" download>{esc(name)}</a><small>Research-only download · SHA-256 <code>{esc(actual_sha[:16])}…</code></small></td>
<td><strong>{float(row['owner_reported_score']):.4f}</strong><small>USER/OWNER-REPORTED<br>No organizer receipt located</small></td>
<td><strong>{local_status} · portal unverified</strong><small>Single-band float32, 3730×3292, EPSG:32611, 100 m; in-footprint [0,1] and no NaN. Outside: {esc(exterior)}. Local {int(sum(bool(v) for v in checks.values()))}/{len(checks)} checks pass; organizer acceptance unknown.</small></td>
<td><strong>No</strong><small>{overlap:.2f}% of this file’s positive pixels are within 3 px of {esc(row['nearest_focus_site'])}</small></td>
<td><strong>Not estimated</strong><small>No new file; historical score is not a projection</small></td>
<td><span class="pill stop">Do not submit</span><small>Historical artifact only</small></td>
</tr>''')
    return f'''<div class="table-wrap"><table>
<thead><tr><th scope="col">Focus site</th><th scope="col">File to download</th><th scope="col">Reported historical score</th><th scope="col">Local format / portal status</th><th scope="col">Unique vs. focus set?</th><th scope="col">New-file score estimate</th><th scope="col">Decision</th></tr></thead>
<tbody>{''.join(output)}</tbody></table></div>'''


def check_inputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, dict[str, Any]]]:
    audit = read_json(ROOT / "evidence/release_audit_20261027.json")
    card = read_json(ROOT / "evidence/current_run_card.json")
    if card.get("verdict") != "negative" or card.get("ok_to_submit") is not False or audit.get("verdict") != "negative":
        raise SystemExit("This portal builder only publishes the current negative decision; refusing stale or positive card")
    leaderboard = read_json(ROOT / "docs/data/public_leaderboard.json")
    format_audit = read_json(ROOT / "evidence/focus_site_audit_20261027.json")
    safety_by_sha = {
        row["sha256"]: row
        for row in format_audit.get("files", [])
        if row.get("sha256") and row.get("site") != "archive"
    }
    if card.get("new_raster_created") is not False or card.get("raster_sha256") is not None:
        raise SystemExit("Current card must state that no new raster was emitted")
    if card.get("submission_name") is not None:
        raise SystemExit("A negative no-candidate card must not name a submission file")
    current_holdout = card.get("current_holdout", {})
    if any(current_holdout.get(key) is not None for key in ("evaluator", "withheld_positive_n", "pooled_dti", "ci95")):
        raise SystemExit("No current holdout result is permitted in a no-experiment card")
    if audit.get("new_geotiff_created") is not False or audit.get("new_submissions") != 0:
        raise SystemExit("Release audit does not describe a no-emission review")

    pre = audit.get("preflight", {})
    prior = audit.get("prior_candidate", {})
    if not pre.get("forced_duplicate") or not prior.get("duplicate_under_literal_rule"):
        raise SystemExit("Stop evidence changed; rerun review before building")
    if float(pre.get("minimum_directional_overlap", 0.0)) <= float(pre.get("limit", 0.70)):
        raise SystemExit("The frozen budget no longer has a demonstrated literal-overlap stop")
    if float(prior.get("witness_overlap_fraction", 0.0)) <= float(pre.get("limit", 0.70)):
        raise SystemExit("Prior research artifact does not match the recorded duplicate result")
    hard_stop = card.get("hard_stop", {})
    if (
        int(hard_stop.get("candidate_dot_budget", -1)) != int(pre["candidate_dot_budget"])
        or int(hard_stop.get("minimum_overlapping_dots", -1)) != int(pre["minimum_overlapping_dots"])
        or float(hard_stop.get("minimum_directional_overlap", -1.0)) != float(pre["minimum_directional_overlap"])
        or hard_stop.get("witness_sha256") != pre.get("witness_sha256")
    ):
        raise SystemExit("Current run card and release-audit hard-stop fields disagree")

    artifact = DOCS / "downloads" / str(prior.get("file", ""))
    if not artifact.is_file() or hashlib.sha256(artifact.read_bytes()).hexdigest() != prior.get("sha256"):
        raise SystemExit("Research artifact missing or differs from current audit")

    rows = audit.get("focus_nine", [])
    if len(rows) != 9 or {row.get("site") for row in rows} != EXPECTED_FOCUS:
        raise SystemExit("Focus-site comparison is incomplete or has changed")
    for row in rows:
        if not str(row.get("score_evidence_class", "")).startswith("USER/OWNER-REPORTED"):
            raise SystemExit(f"Unexpected score evidence class for {row.get('site')}")
        if not row.get("duplicate_within_focus_nine") or float(row.get("max_directional_focus_overlap_within_3px", 0)) <= 0.70:
            raise SystemExit(f"Focus-site uniqueness claim is inconsistent for {row.get('site')}")
        safety = safety_by_sha.get(row.get("sha256", ""))
        if (
            safety is None
            or safety.get("site") != row.get("site")
            or safety.get("all_checks_passed") is not True
            or safety.get("organizer_acceptance_verified") is not False
        ):
            raise SystemExit(f"Missing, inconsistent or non-negative local format audit for {row.get('site')}")
    note = str(card.get("note", ""))
    submission_note = str(card.get("submission_note", ""))
    if (
        note != submission_note
        or len(note) > 140
        or card.get("note_characters") != len(note)
        or card.get("submission_note_characters") != len(submission_note)
    ):
        raise SystemExit("Current-card note is missing, inconsistent, or over the 140-character limit")
    if leaderboard.get("status") not in {"verified_snapshot", "success", "unavailable"}:
        raise SystemExit("Public leaderboard feed has an unrecognized status; do not render as live")
    return audit, card, leaderboard, safety_by_sha


def build_pages(
    audit: dict[str, Any], card: dict[str, Any], leaderboard: dict[str, Any], safety_by_sha: dict[str, dict[str, Any]]
) -> None:
    pre = audit["preflight"]
    prior = audit["prior_candidate"]
    lineage = audit["focus_lineage_geometry"]
    rows = audit["focus_nine"]
    table = focus_table(rows, safety_by_sha)

    bound = 100.0 * float(pre["minimum_directional_overlap"])
    prior_overlap = 100.0 * float(prior["witness_overlap_fraction"])
    minimum_dots = int(pre["minimum_overlapping_dots"])
    top_row = max(rows, key=lambda row: float(row["owner_reported_score"]))
    top_score = float(top_row["owner_reported_score"])
    max_focus_overlap = max(float(row["max_directional_focus_overlap_within_3px"]) for row in rows)
    note = str(card.get("submission_note", ""))
    if len(note) > 140:
        raise SystemExit("Current-card note exceeds the 140-character portal limit")

    home = f'''<div class="breadcrumb">DOE GEMS PRIZE <span>/</span> <strong>Current decision</strong></div>
<section class="hero"><div class="hero-main"><div class="eyebrow">HTCADS-K2 · review dated 27 October 2026</div>
<span class="pill stop large-pill">NEGATIVE · DO NOT SUBMIT</span>
<h1>No TIFF is cleared<br>for submission.</h1>
<p class="lead">The frozen {int(pre['candidate_dot_budget']):,}-dot lane is blocked by the literal any-registry uniqueness gate. No model was fit, no holdout was run, and no new raster or score was produced in this review.</p>
<div class="hero-actions"><a class="btn" href="executive-summary.html">Read the decision &amp; site table <span aria-hidden="true">→</span></a><a class="btn secondary" href="research.html">Review ranked hypotheses</a></div>
<p class="subtle"><strong>Submit:</strong> no file. &nbsp; <strong>Download:</strong> historical artifacts are linked for research comparison only.</p></div>
<aside class="hero-aside"><div class="eyebrow">Literal pre-fit stop</div><div class="big-number">{bound:.4f}%</div>
<p>Minimum possible within-3-pixel overlap at the frozen budget, versus the <strong>70%</strong> hard limit.</p>
<div class="divider"></div><div class="eyebrow">Best of nine historical reports</div><div class="mid-number">{top_score:.4f}</div>
<p>{esc(top_row['site'])} · USER/OWNER-REPORTED, not receipt-confirmed.</p></aside></section>

<div class="metrics">
<div class="metric"><div class="label">Forced minimum overlap</div><div class="value">{bound:.2f}%</div><div class="hint">{minimum_dots:,} of {int(pre['candidate_dot_budget']):,} dots must overlap</div></div>
<div class="metric"><div class="label">Prior raster vs witness</div><div class="value">{prior_overlap:.3f}%</div><div class="hint">{int(prior['witness_overlap_dots']):,} / {int(prior['inside_positive_pixels']):,} dots</div></div>
<div class="metric"><div class="label">Unique focus-site rasters</div><div class="value">0 / 9</div><div class="hint">All exceed the 70% directional 3 px threshold</div></div>
<div class="metric"><div class="label">New HOLDOUT-DTI</div><div class="value">Not measured</div><div class="hint">No new candidate; hard stop precedes fitting</div></div>
<div class="metric leader-metric"><div class="label"><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Public leaderboard #1 ↗</a></div><div class="value" id="public-top-score">Loading…</div><div class="hint" id="public-top-label">Dated snapshot; never a score for this project</div></div>
</div>
<section class="section"><div class="section-head"><div><div class="eyebrow">Why the answer is “no”</div><h2>The gate fails before modeling.</h2><p>A mathematically forced collision is not fixed by hand-picking dots, changing filenames, or calling the lattice a calibration control.</p></div></div>
<div class="grid-two"><article class="card accent-card"><div class="step">01</div><h3>One witness blocks every placement at this budget</h3><p>Within 3 px, the registered witness covers <strong>{int(pre['covered_pixels_within_3px']):,}</strong> of {int(pre['footprint_pixels']):,} footprint pixels. Only {int(pre['uncovered_pixels']):,} pixels lie outside its neighborhood, so at least {minimum_dots:,} of any {int(pre['candidate_dot_budget']):,} distinct dots overlap.</p><p class="small-warning">This is a precise lower bound for this footprint, witness, radius and frozen dot budget—not a claim that every possible smaller raster fails.</p></article>
<article class="card"><div class="step muted-step">02</div><h3>No live validation followed</h3><p>The complete current registry, pre-placement surface, shared cached stack, leakage canary and buffered hide-and-recover evaluator were not replayed. The sandbox has no restored <code>data/</code> or <code>.cache/</code> stack.</p><p>Not running holdout or fitting is the correct fail-closed result while the hard stop holds.</p></article></div></section>
<section class="callout stop-callout"><div class="eyebrow">Clear download / submit decision</div><h2>There is no approved file to download or submit.</h2><p>The old {esc(prior['file'])} is an archived research artifact. Its exact bytes are locally range-valid but it has {prior_overlap:.3f}% overlap with the registered witness and zero organizer acceptance evidence. Do not use it for a live slot.</p><a href="executive-summary.html" class="section-link">See historical files and the full comparison →</a></section>
<section class="section compact-section"><div class="section-head"><div><div class="eyebrow">Public leaderboard reference</div><h2>A dated observation, not a project prediction.</h2></div></div>
<div class="card"><p>The committed official-source snapshot records public #1 = <strong>0.4544</strong>, #5 = <strong>0.3566</strong>, and 0.3195 at #25. The user’s earlier statement that 0.3195 was the highest is inconsistent with that snapshot. Ranks change; the auto-refreshed feed above is explicitly dated or marked unavailable.</p><p>The reported GEMSDOE32 0.2778 is below the snapshot’s rank-50 0.2857, but is not receipt-confirmed. None of these values predicts a new submission’s score.</p><a href="../registry/official_sources_20261027.json">Open official-source snapshot and limitations ↗</a></div></section>
<section class="section compact-section"><div class="grid-three"><article class="card"><div class="eyebrow">Evidence class</div><h3>Reported ≠ confirmed</h3><p>All nine site scores are user/owner-reported. No matching organizer submission receipt was found in the reviewed evidence.</p></article><article class="card"><div class="eyebrow">Physics labeling</div><h3>Two proxy caveats</h3><p>HTCADS index 28 was fixed-axis strike alignment, not slip tendency. Its “upgradient” plume follows terrain elevation, not measured groundwater head.</p></article><article class="card"><div class="eyebrow">Next</div><h3>Rank hypotheses; do not fit</h3><p>Three physically grounded variants are documented with exact layers, signatures, mimics and data-access limits. They remain untested and unpreregistered.</p></article></div></section>'''

    executive = f'''<div class="breadcrumb"><a href="index.html">Overview</a> <span>/</span> <strong>Decision &amp; site comparison</strong></div>
<div class="page-intro"><div class="eyebrow">Executive summary · evidence cutoff 27 October 2026</div><h1>No submission candidate<br>is authorized.</h1><p>The literal any-registry overlap lower bound is {bound:.4f}% for the frozen {int(pre['candidate_dot_budget']):,}-dot lane, above the 70% stop. No model fitting, holdout run, or TIFF emission is permitted under that result.</p></div>
<div class="decision-grid"><div class="decision-box"><span class="eyebrow">File to submit</span><strong>None</strong><small>No new TIFF was emitted; no historical file is authorized.</small></div><div class="decision-box"><span class="eyebrow">New-file score estimate</span><strong>Not available</strong><small>No projection is a score; no candidate passed validation.</small></div><div class="decision-box"><span class="eyebrow">Current verdict</span><strong class="red-text">NEGATIVE</strong><small>No organizer receipt, current quota check, or complete registry replay.</small></div></div>
<section class="section"><div class="section-head"><div><div class="eyebrow">Requested per-site comparison</div><h2>Files and reports are research references only.</h2><p>The highest reported artifact per focus site is listed below. Downloading is for byte-level comparison; <strong>none is a submit recommendation</strong>.</p></div></div>
{table}
<p class="note">Directional overlap definition: candidate positive pixels with a reference positive pixel within a 3-pixel disk, divided by candidate positive-pixel count. Each row shows its nearest other focus-site raster. This is not a full current-registry comparison. Hashes pin the mirror bytes, not the claimed organizer origin or score association. Local format checks do not establish portal acceptance.</p></section>
<section class="section"><div class="section-head"><div><div class="eyebrow">Why 0.2778 is only reported</div><h2>Geometry explains a possibility—not causation.</h2></div></div>
<div class="grid-two"><article class="card"><h3>What is reproducibly geometric</h3><p>The GEMSDOE32 37,654-dot mask equals GEMSDOE25 after removing its {int(lineage['g25_to_g32_removed_pixels']):,} dots within 2 pixels of the restored known-fault catalogue (XOR = {int(lineage['g32_b2_vs_g25_d28_filtered_by_distance_gt_2px_xor']):,}). GEMSDOE36 adds {int(lineage['g36_extra_pixels_over_g32']):,} dots to the GEMSDOE32 mask. GEMSDOE25 and GEMSDOE30 have identical in-footprint positive masks.</p><p>The nine-site audit found every row’s directional overlap with at least one other site above 70%; maximum nearest-peer overlap is {100.0 * max_focus_overlap:.2f}%.</p></article>
<article class="card"><h3>Why score causation cannot be established</h3><p>The score 0.2778 is labeled USER/OWNER-REPORTED: the reviewed records do not contain an organizer submission-page receipt tying that score to the pinned TIFF. The official private truth and exact scored file are not available here.</p><p>The recorded metric is distance-weighted Tversky (α=0.2, β=0.8) with a 300 m triangular kernel; the known-fault mask is pixel-exact, not a 2-pixel buffer. Pruning catalog-adjacent dots could plausibly remove predictions outside useful hidden-truth support and reduce false-positive cost, but it could also discard nearby distance-weighted credit or increase false negatives, which carry the larger coefficient. Geometry alone cannot identify which pixels affected hidden truth or the score.</p><p>Therefore no hidden score, causal gain, “zero true positives” result, or score projection is asserted.</p></article></div></section>
<section class="section"><div class="section-head"><div><div class="eyebrow">Current run card</div><h2>One machine-readable negative result.</h2></div><a class="section-link" href="../evidence/current_run_card.json">Open JSON run card ↗</a></div>
<div class="card"><dl class="key-values"><dt>New experiments</dt><dd>{int(card.get('experiments_run_in_this_review', 0))}</dd><dt>New TIFF SHA-256</dt><dd>None — no TIFF emitted</dd><dt>New HOLDOUT-DTI</dt><dd>Not measured</dd><dt>Current submission name</dt><dd>None</dd><dt>≤140-character note recorded</dt><dd><code>{esc(note)}</code> ({len(note)} characters)</dd><dt>Verdict</dt><dd><strong class="red-text">NEGATIVE · do not submit</strong></dd></dl></div></section>
<section class="section"><div class="section-head"><div><div class="eyebrow">Automated future pathway</div><h2>What must change before a later run.</h2></div></div>
<div class="grid-two"><article class="card"><ol class="steps"><li>Resolve the control/literal-rule contradiction formally; do not silently exempt the witness.</li><li>Restore and hash the official/authorized shared stack, then replay the complete live registry before any surface or placement.</li><li>Run every feature-alone leakage canary; AUC &gt; 0.90 is a stop unless explained. Keep fault geometry fold-visible-only.</li><li>Use buffered whole-segment holdout and the shared evaluator/writer only if the hard stop clears. Report pooled HOLDOUT-DTI, evaluator, withheld-positive N and 95% CI.</li><li>Run the independent selector only after all gates pass. No automatic live slot selection or upload.</li></ol></article><article class="card"><h3>Submission steps after approval only</h3><ol class="steps"><li>Download the exact SHA-pinned approved GeoTIFF/ZIP.</li><li>Check one float32 band, authenticated grid/CRS/transform, no NaN/Inf inside footprint, [0,1] values, and the official exterior convention.</li><li>Follow the official competition page to upload the selected file and a ≤140-character note.</li><li>Archive the organizer receipt and label its score ORGANIZER-CONFIRMED only after that receipt exists.</li></ol><p class="small-warning">This page is not upload authorization. No current file or score is supplied.</p></article></div></section>
<section class="section"><div class="card"><div class="eyebrow">Official source links</div><ul class="source-list"><li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DOE GEMS Prize overview ↗</a></li><li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Official metric and submission format ↗</a></li><li><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Official challenge rules PDF ↗</a></li><li><a href="https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516">DrivenData scoring clarification on known-fault masking ↗</a></li><li><a href="https://doi.org/10.5066/P93LGLVQ">USGS GeoDAWN release ↗</a> · <a href="https://gdr.openei.org/submissions/1391">DOE GDR INGENIOUS #1391 ↗</a> · <a href="https://www.usgs.gov/3d-elevation-program">USGS 3DEP ↗</a></li></ul><p class="note">The official competition data page is login-walled in the source record. Owner-mirror SHA-256 pins confirm identity to those mirrors only, not organizer origin. See <a href="../registry/official_sources_20261027.json">dated source verification and irregularities ↗</a>.</p></div></section>'''

    submission_page = f'''<div class="breadcrumb"><a href="index.html">Overview</a> <span>/</span> <strong>Historical submission comparison</strong></div>
<div class="page-intro"><div class="eyebrow">All nine focus sites · exact pinned file identities</div><h1>Historical artifacts,<br>not submit candidates.</h1><p>No file is cleared. All reported scores are USER/OWNER-REPORTED, not ORGANIZER-CONFIRMED. New-file estimate: none.</p></div>
<div class="callout stop-callout"><h2>Do not submit any file in this table.</h2><p>Links download historical TIFFs for research comparison only. All nine exceed the 70% within-3-pixel overlap rule against another focus site. This does not substitute for a complete current-registry check.</p></div>
<section class="section">{table}<p class="note">Exact mirror identities are pinned by SHA-256 in <a href="../evidence/release_audit_20261027.json">release_audit_20261027.json</a>. “NaN outside” and “zero/finite outside” describe local historical bytes, not organizer acceptance. Each link is a research download, not a recommendation.</p></section>
<div class="card"><h3>Current KANLERGEMSDOE2 result</h3><dl class="key-values"><dt>File to submit</dt><dd>None</dd><dt>Estimated score</dt><dd>Not available; no projection or new candidate</dd><dt>HOLDOUT-DTI</dt><dd>Not measured in this review</dd><dt>Reason</dt><dd>At the frozen dot count, at least {bound:.4f}% overlap is forced by one registry witness.</dd><dt>Decision</dt><dd><strong class="red-text">Negative — do not submit</strong></dd></dl></div>'''

    research = f'''<div class="breadcrumb"><a href="index.html">Overview</a> <span>/</span> <strong>Ranked hypotheses</strong></div>
<div class="page-intro"><div class="eyebrow">HTCADS-K2 · research only</div><h1>Three testable mechanisms.<br>Zero score claims.</h1><p>Rank is qualitative expected-gain priority, not a numeric DTI forecast. These are candidates for a future preregistration, not permission to run the exhausted frozen lane.</p></div>
<div class="callout stop-callout"><strong>Validation is blocked.</strong><p>The literal registry witness forces {bound:.4f}% overlap at the frozen budget, above the 70% limit. No data cache is present; the current HTCADS three-experiment lane is already archived with its experiment record. None of these variants was fit or evaluated here. Fleet-wide novelty is unverified.</p></div>
<section class="section hypothesis-list">
<article class="hypothesis card"><div class="hypothesis-rank">01 <span>Highest qualitative priority · medium implementation effort</span></div><h2>Thermal-path direction-uncertainty ensemble</h2>
<p><strong>Mechanism.</strong> Shallow probe and well/spring thermal anomalies can be laterally displaced from a deeper feeder by basin-fill transport. Instead of treating the smoothed terrain-elevation gradient as measured groundwater head, propagate each independent thermal source along a small, fixed set of terrain-gradient perturbations, then score only where paths meet independently supported structural ridges. The physical claim is a robustness test of the proxy, not a groundwater-flow inversion.</p>
<p><strong>Exact layers.</strong> GDR #1391 2 m temperature-probe residuals and well/spring temperatures/geothermometers; `det_elev`, `cond_surf`, `grav_hg`, `rtp_hess_ridge_s15`, `base_depth_grad`, and `gallardo_meju_xgrad` from the supplied competition stack.</p>
<p><strong>Blind-fault rationale &amp; signature.</strong> A buried feeder may have no exposed scarp; independent probe and geothermometer sources should point toward a persistent gravity/magnetic/MT structural ridge. Predefine a directional-convergence score and require the thermal and structural components to remain individually sub-threshold outside that convergence. Use buffered whole-fault-segment holdout and exact visible-fault masking.</p>
<p><strong>Mimics / controls.</strong> Shallow groundwater flow, irrigation or land-use heat, saline playa discharge, and topographic drainage can create terrain-following thermal patterns without geothermal faults. Negative controls: rotate/reverse transport directions and compare against non-geothermal GDR points; keep paleolake/tufa exclusions fixed.</p>
<p><strong>What is already in this repo.</strong> `src/gems32/htcads.py` already back-projects 2 m probe and well/spring seeds along one terrain-elevation-gradient proxy and separately builds structural ridges. The proposed uncertainty ensemble and independent-component controls are not the same as that implementation; no claim is made about other repositories.</p>
<p><strong>Data access.</strong> GDR #1391 is a public DOE repository record, listed as CC BY 4.0 in the dated source catalog (<a href="https://gdr.openei.org/submissions/1391">official record ↗</a>, DOI <a href="https://doi.org/10.15121/1881483">10.15121/1881483 ↗</a>). The local manifest identifies owner-mirrored files, but `data/` and `.cache/` are absent here and no official bytes were re-fetched in this review. Competition layers are login-walled per the dated source record. Feasible after authorized restore; not now.</p>
<p class="note"><strong>Expected-gain rank:</strong> 1 of 3 (qualitative). <strong>Expected numerical DTI:</strong> not estimated.</p></article>

<article class="hypothesis card"><div class="hypothesis-rank">02 <span>Medium qualitative priority · medium effort</span></div><h2>Multi-field, depth-persistent crest migration</h2>
<p><strong>Mechanism.</strong> A dipping Basin-and-Range fault can place a deep-source horizontal gravity-gradient maximum basinward of its surface trace. Potential-field continuation should move or sharpen the crest systematically with source depth; matching gravity, magnetic/RTP, and basement-depth orientations can distinguish a structural step from a one-channel contact.</p>
<p><strong>Exact layers.</strong> `iso_grav_anom` continued at predeclared 150/400/800 m; `rtp`, `tmi_vg`/GeoDAWN TMI and upward-continued TMI where available; `depth_to_base_surf`, `grav_hg`, and `base_flexure_curv`. Use existing 3DEP terrain only as a surface-contact control, not as the subsurface target.</p>
<p><strong>Blind-fault rationale &amp; signature.</strong> Require coherent displacement of potential-field crests across continuation heights, a gravity–magnetic cross-gradient orientation match, and an independently aligned basement-depth gradient; back-project along a preregistered dip range. A candidate fault should show a repeatable depth-ordered crest shift toward its basinward hanging wall, not just high edge strength.</p>
<p><strong>Mimics / controls.</strong> Lithologic contacts, dikes, plutons, remanent magnetization, interpolation edges and survey seams can produce coincident gradients. Use lithology/contact controls, amplitude-preserving line shuffles, and hold out whole catalog fault segments; no same-segment neighbors enter training.</p>
<p><strong>What is already in this repo.</strong> HTCADS computes an updip projection from one 400 m gravity continuation and a Gallardo–Meju cross-gradient; `src/gems32/dslup.py` already evaluates multilevel gravity continuation/strike coherence. The proposed joint migration signature across gravity, RTP/magnetics and basement depth is a distinct untested interaction in the inspected source tree, not a claim of fleet-wide novelty.</p>
<p><strong>Data access.</strong> GeoDAWN’s official DOI is <a href="https://doi.org/10.5066/P93LGLVQ">10.5066/P93LGLVQ ↗</a>; its dated source catalog lists the landing page as CC0. USGS <a href="https://www.usgs.gov/3d-elevation-program">3DEP ↗</a> is listed as free and without use restrictions, but derived-tile coverage is not confirmed. Competition gravity/RTP/basement layers are described in the frozen manifest as owner mirrors, not independently organizer-authenticated; files are absent in this sandbox. No new external layer is required after authorized restore.</p>
<p class="note"><strong>Expected-gain rank:</strong> 2 of 3 (qualitative). <strong>Expected numerical DTI:</strong> not estimated.</p></article>

<article class="hypothesis card"><div class="hypothesis-rank">03 <span>Lower qualitative priority · medium-to-high effort</span></div><h2>Structural-ridge graph connectivity of independent thermal evidence</h2>
<p><strong>Mechanism.</strong> Blind faults may connect deep structural lineaments to separated surface thermal/geochemical manifestations. Represent independently detected gravity/magnetic/MT ridges as a graph and measure least-cost path/current-flow connectivity between separate GDR thermal sources; avoid scoring a hot spring merely because it is close to a known vent.</p>
<p><strong>Exact layers.</strong> `struct_1d`, `grav_hess_ridge_s1`, `rtp_hess_ridge_s15`, `base_depth_grad`, `mt_claycap_edge`, GDR 2 m probes, well/spring temperatures and geothermometers, sinter/breccia/vent points, plus `det_elev` and `cond_surf` as transport/mimic controls.</p>
<p><strong>Blind-fault rationale &amp; signature.</strong> Require a path that links at least two independent thermal evidence classes to a subsurface structural ridge, remains after exact visible-fault masking, and persists when individual known vents are removed. Score the hidden conduit corridor rather than endpoint density alone.</p>
<p><strong>Mimics / controls.</strong> Drainage networks, alluvial aquifers, lithologic contacts and clustered sampling can create apparent connectivity. Compare against degree-preserving randomized graphs, rotated ridge networks, and disconnected thermal endpoints; use only fold-visible catalogue geometry.</p>
<p><strong>What is already in this repo.</strong> HTCADS currently smooths probe, well/spring and vent seeds into fields and combines evidence with ridge/conduit features; the inspected feature builder does not construct a graph or path-connectivity operator. This distinction is limited to this repository; no sister-site novelty claim is made.</p>
<p><strong>Data access.</strong> The core GDR inputs are listed under official DOE GDR #1391 (<a href="https://gdr.openei.org/submissions/1391">record ↗</a>), listed as CC BY 4.0 in the dated catalog. Owner-mirror file hashes are in `registry/data_manifest.json`; no actual data/cache directory exists in the workspace. Feasible after authorized restore; a fresh official download and provenance check remain necessary.</p>
<p class="note"><strong>Expected-gain rank:</strong> 3 of 3 (qualitative). <strong>Expected numerical DTI:</strong> not estimated.</p></article>
</section>
<section class="section"><div class="card"><h2>Code-review correction before any future HTCADS interpretation</h2><p>Feature index 28 was labeled `anderson_slip_tendency` but computed <code>cos(dom_strike_fp − 62°)²</code>. It has now been renamed <code>strike_alignment_fixed_62deg</code>; the pixel values are unchanged. It does not use a stress tensor, fault-plane normal, friction or a slip calculation. Further, the plume “upgradient” vector is derived from smoothed terrain elevation, not observed groundwater hydraulic head. Historical receipts retain their original names and must be read with this caveat.</p><p><a href="../evidence/three_pass_review_20261027.md">Three-pass code/release review ↗</a> · <a href="../registry/PREREGISTRATION_STATUS.md">Frozen-lane status ↗</a> · <a href="../research/2026-10-27_htcads_hypotheses.md">Full hypothesis slate ↗</a></p></div></section>
<section class="section"><div class="card"><div class="eyebrow">Official sources</div><ul class="source-list"><li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Metric and submission format ↗</a></li><li><a href="https://doi.org/10.5066/P93LGLVQ">USGS GeoDAWN ↗</a></li><li><a href="https://gdr.openei.org/submissions/1391">DOE GDR INGENIOUS #1391 ↗</a> · <a href="https://www.usgs.gov/3d-elevation-program">USGS 3DEP ↗</a></li><li><a href="../registry/official_sources_20261027.json">Dated source-verification record ↗</a> (historical, not live)</li></ul><p class="note">Fleet-wide novelty is not established: the complete sister-repository/source registry was not replayed, and the uniqueness gate already prevents a safe experiment.</p></div></section>'''

    irregular = f'''<div class="breadcrumb"><a href="index.html">Overview</a> <span>/</span> <strong>Open issues &amp; review</strong></div>
<div class="page-intro"><div class="eyebrow">Fail-closed audit · 27 October 2026</div><h1>Known gaps, plainly stated.</h1><p>Each issue is classified as a measured result, a recorded-but-not-replayed check, or an unresolved source/portal question.</p></div>
<div class="issue-grid">
<article class="card issue-block"><div class="issue-kicker">BLOCKING · measured lower bound</div><h2>Literal uniqueness fails at the frozen budget</h2><p>The registered lattice witness covers {int(pre['covered_pixels_within_3px']):,}/{int(pre['footprint_pixels']):,} footprint cells within 3 px. At {int(pre['candidate_dot_budget']):,} dots, at least {minimum_dots:,} ({bound:.4f}%) must overlap; the cap is 70%. No exemption was applied. This does not prove all lower dot counts fail.</p></article>
<article class="card issue-block"><div class="issue-kicker">BLOCKING · not replayed</div><h2>No complete current-registry or pre-placement replay</h2><p>The release audit is explicitly scoped to a single witness and the nine focus files. The pre-placement continuous surface, complete live registry, shared cached stack, all-feature leakage canary and independent buffered holdout were not replayed in this review.</p></article>
<article class="card issue-block"><div class="issue-kicker">EVIDENCE CLASS · user/owner report</div><h2>GEMSDOE32’s 0.2778 is not receipt-confirmed</h2><p>No organizer receipt ties the score to the SHA-pinned file. The geometry is reproducible; which hidden labels were detected, and whether the 6,436-pixel pruning caused a gain, cannot be established.</p></article>
<article class="card issue-block"><div class="issue-kicker">CORRECTED · implementation semantics</div><h2>Feature index 28 was misnamed</h2><p>HTCADS code computed cosine-squared axial strike alignment to a fixed 62° axis, not Anderson slip tendency. The shared feature name is corrected to <code>strike_alignment_fixed_62deg</code>; values are unchanged. Old run cards and canaries preserve the old historical label and are not evidence of a stress calculation.</p></article>
<article class="card issue-block"><div class="issue-kicker">SCIENTIFIC LIMITATION</div><h2>“Upgradient” uses topography as a proxy</h2><p>The plume transport direction is derived from smoothed detrended terrain elevation. No measured groundwater hydraulic head is consumed by this code, so it cannot be described as an observed hydraulic gradient or groundwater-flow vector.</p></article>
<article class="card issue-block"><div class="issue-kicker">SOURCE DISCREPANCY · dated snapshot</div><h2>0.3195 is not the recorded public #1</h2><p>The repository’s 2026-10-27 snapshot records public #1=0.4544, #5=0.3566, and 0.3195 at #25; rank #50=0.2857. The snapshot is date-only and may now be stale. It contradicts the prior statement that 0.3195 was the highest.</p></article>
<article class="card issue-block"><div class="issue-kicker">HISTORICAL POLICY CLAIM · superseded</div><h2>Archived “promote” verdicts are not current authorization</h2><p>An older DSLUP run card records a policy-specific control-separated <code>promote</code> verdict under an earlier reading of the lattice. The standing protocol now applies the literal any-registry rule with no control exemption. That old policy claim is historical and is superseded by this current negative run card; do not submit the archived DSLUP TIFF. See the <a href="../evidence/supersession_manifest_20261027.json">historical-promotion supersession manifest ↗</a>.</p></article>
<article class="card issue-block"><div class="issue-kicker">PORTAL · unresolved</div><h2>Local TIFF checks are not acceptance</h2><p>The prior research TIFF passes local grid, dtype and [0,1] checks, but writes zero outside the footprint while the owner sample uses NaN. Official instructions say null/NaN outside. No acceptance receipt or diagnosis of the earlier range error is available.</p></article>
<article class="card issue-block"><div class="issue-kicker">DATA PROVENANCE · unresolved</div><h2>Owner-mirror identity is not official origin</h2><p>SHA-256 validates bytes against the manifest’s owner mirror only. The competition data page is recorded as login-walled; no raw data/cache directories exist in the workspace. No feature fit or holdout run was attempted.</p></article>
</div>
<section class="section"><div class="card"><div class="eyebrow">Three review passes</div><h2>Source, science, and release were checked separately.</h2><ol class="review-passes"><li><strong>Pass 1 — source/evidence.</strong> Re-read the brief, frozen preregistration, release audit, score records, focus-site hashes, official-source snapshot and cached-data status. Separate owner-reported scores from organizer receipts.</li><li><strong>Pass 2 — scientific/code audit.</strong> Trace feature index 28 from name to builder assignment; correct its geometric label and add an axial-angle unit test. Trace the thermal “upgradient” vector back to `det_elev`; document it as a terrain proxy. Search existing HTCADS/DSLUP/DARP implementations before ranking candidate mechanisms.</li><li><strong>Pass 3 — release and reproducibility.</strong> Rebuild the site from the negative card only; verify links, exact file hashes, status/table consistency, no positive authorization copy, and the full automated test suite. Result and any limitation are recorded in <a href="../evidence/three_pass_review_20261027.md">the review note ↗</a>.</li></ol></div></section>'''

    styles = '''/* GEMS Fieldnotes — accessible, responsive, no external runtime assets. */
:root{--ink:#172728;--muted:#5b6c6b;--paper:#f4f6f2;--panel:#fff;--line:#d9e2dc;--green:#0e5b4d;--green2:#dcefe7;--red:#922d28;--red2:#fae7e3;--amber:#81540e;--amber2:#fff1d0;--navy:#132c33;--shadow:0 16px 42px rgba(22,45,40,.08);font-synthesis:none;text-rendering:optimizeLegibility}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.62 Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:#075d55;text-decoration-thickness:1px;text-underline-offset:3px}a:hover{color:#083e38}a:focus-visible,button:focus-visible{outline:3px solid #dc8b28;outline-offset:3px}.wrap{width:min(1160px,calc(100% - 40px));margin-inline:auto}.skip{position:absolute;left:-9999px;top:auto}.skip:focus{left:12px;top:12px;z-index:99;background:white;padding:10px}.topbar{position:sticky;top:0;z-index:5;background:rgba(244,246,242,.94);backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}.topbar-inner{min-height:76px;display:flex;align-items:center;justify-content:space-between;gap:22px}.brand{display:flex;align-items:center;gap:11px;color:var(--ink);text-decoration:none}.brand-mark{width:36px;height:36px;border-radius:11px;background:var(--green);color:white;display:grid;place-items:center;font-weight:850;font-family:Georgia,serif;font-size:21px}.brand-name{font-weight:850;letter-spacing:.07em;font-size:12px;line-height:1.3}.brand-name small{display:block;color:var(--muted);font-size:9px;letter-spacing:.13em;margin-top:3px}.nav{display:flex;align-items:center;gap:20px;flex-wrap:wrap}.nav a{font-size:13px;font-weight:700;text-decoration:none;color:#455956}.nav a.active{color:var(--green);box-shadow:inset 0 -2px var(--green);padding-block:26px}.nav a:hover{color:var(--green)}main{padding-bottom:54px}.breadcrumb{padding:22px 0 10px;color:#73827d;font-size:12px;font-weight:650;letter-spacing:.035em}.breadcrumb span{padding-inline:8px;color:#9eaaa4}.hero{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(260px,.8fr);gap:32px;padding:46px 0 34px;align-items:stretch}.hero-main{padding:30px 38px;border-radius:26px;background:linear-gradient(135deg,#fff 0%,#edf5ef 100%);border:1px solid var(--line);box-shadow:var(--shadow)}.eyebrow{text-transform:uppercase;letter-spacing:.13em;font-size:10px;line-height:1.4;font-weight:850;color:#55706a;margin-bottom:11px}.pill{display:inline-flex;align-items:center;padding:5px 10px;border-radius:999px;font-size:10px;letter-spacing:.08em;font-weight:900}.pill.stop{background:var(--red2);color:var(--red);border:1px solid #edc4bc}.large-pill{margin-top:7px;padding:7px 12px;font-size:11px}.hero h1,.page-intro h1{font-size:clamp(42px,6vw,72px);letter-spacing:-.055em;line-height:.99;margin:19px 0 20px;max-width:790px}.lead{max-width:750px;font-size:18px;line-height:1.62;color:#405450}.hero-actions{display:flex;gap:11px;flex-wrap:wrap;margin:25px 0 12px}.btn{display:inline-flex;align-items:center;gap:8px;padding:12px 16px;border-radius:10px;background:var(--green);color:#fff!important;text-decoration:none;font-size:13px;font-weight:800;box-shadow:0 5px 16px rgba(14,91,77,.14)}.btn:hover{background:#09483d}.btn.secondary{background:#fff;color:var(--green)!important;border:1px solid #c6d9d0;box-shadow:none}.btn.secondary:hover{background:var(--green2)}.subtle,.note{color:var(--muted);font-size:12px}.hero-aside{padding:26px;border-radius:24px;background:var(--navy);color:#f5fbf8;display:flex;flex-direction:column;justify-content:center;box-shadow:var(--shadow)}.hero-aside .eyebrow{color:#a8c6b9}.hero-aside p{color:#d2dfdb;font-size:14px}.big-number{font-weight:900;font-size:clamp(47px,6vw,68px);line-height:1;letter-spacing:-.06em;color:#ffc8b8}.mid-number{font-size:42px;line-height:1;font-weight:900;color:#9bdfbf}.divider{height:1px;background:#476068;margin:24px 0}.metrics{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:0 0 42px}.metric{background:#fff;border:1px solid var(--line);border-radius:15px;padding:17px 18px;min-height:116px}.metric .label{font-size:10px;font-weight:850;text-transform:uppercase;letter-spacing:.09em;color:#63746f}.metric .value{font-size:26px;line-height:1.15;font-weight:900;letter-spacing:-.04em;margin:9px 0 4px;color:#1c3d35}.metric .hint{font-size:10px;line-height:1.4;color:#73817b}.leader-metric .value{font-size:24px}.section{margin:48px 0}.compact-section{margin:30px 0}.section-head{display:flex;justify-content:space-between;align-items:end;gap:20px;margin:0 0 18px}.section-head h2,.callout h2,.card h2{margin:0 0 8px;letter-spacing:-.035em;font-size:clamp(25px,3vw,35px);line-height:1.15}.section-head p{margin:0;color:var(--muted);max-width:740px}.section-link{font-weight:800;font-size:13px;white-space:nowrap}.grid-two,.grid-three{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.grid-three{grid-template-columns:repeat(3,minmax(0,1fr))}.card{background:var(--panel);border:1px solid var(--line);border-radius:17px;padding:23px;box-shadow:0 7px 23px rgba(23,39,40,.035)}.card h3{font-size:18px;line-height:1.3;margin:7px 0 9px;letter-spacing:-.02em}.card p{margin:8px 0;color:#4f625e}.card p:last-child{margin-bottom:0}.card-icon,.step{font-size:11px;letter-spacing:.12em;font-weight:900;color:var(--green);background:var(--green2);width:33px;height:29px;border-radius:8px;display:grid;place-items:center}.muted-step{background:#eef0ed;color:#76827b}.accent-card{border-top:3px solid var(--green)}.small-warning{padding:10px 12px;background:var(--amber2);color:#73521c;border-radius:9px;font-size:12px}.stop-callout{background:var(--red2);border:1px solid #e9bdb5;color:#572522;border-radius:18px;padding:24px 27px;margin:36px 0}.stop-callout h2{margin:8px 0}.stop-callout p{margin:8px 0}.stop-callout .eyebrow{color:var(--red)}.callout{background:var(--green2);border:1px solid #c6dfd2;border-radius:17px;padding:22px 24px;margin:26px 0}.callout p{margin:7px 0;color:#42554d}.page-intro{padding:48px 0 21px;max-width:900px}.page-intro h1{font-size:clamp(39px,5.5vw,66px);margin:12px 0 18px}.page-intro p{font-size:18px;color:var(--muted);max-width:820px}.decision-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:13px;margin:10px 0 40px}.decision-box{padding:19px;border:1px solid var(--line);background:white;border-radius:14px}.decision-box span{display:block}.decision-box strong{display:block;font-size:26px;letter-spacing:-.04em;margin:5px 0}.decision-box small{color:var(--muted);line-height:1.4}.red-text{color:var(--red)}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:14px;background:#fff;box-shadow:0 8px 24px rgba(23,39,40,.04)}table{width:100%;border-collapse:collapse;min-width:1000px;font-size:12px}th{text-align:left;background:#eef3ef;color:#536660;font-size:10px;letter-spacing:.09em;text-transform:uppercase;padding:13px 14px}td{vertical-align:top;padding:14px;border-top:1px solid #e7ece8}td strong{font-size:13px}td small{display:block;color:var(--muted);font-size:10px;line-height:1.45;margin-top:5px}.file{max-width:280px;overflow-wrap:anywhere}.file a{font-weight:750}.table-wrap code,code,.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.92em}.note{margin:12px 1px;line-height:1.55}.key-values{display:grid;grid-template-columns:minmax(170px,.5fr) 1fr;gap:8px 18px;margin:12px 0 0;font-size:13px}.key-values dt{color:var(--muted);font-weight:700}.key-values dd{margin:0;overflow-wrap:anywhere}.steps{padding-left:20px}.steps li{padding:4px 0 9px;color:#51635e}.source-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 26px;padding-left:19px}.source-list li{padding:3px 0;color:#51635e}.hypothesis-list{display:grid;gap:18px}.hypothesis{padding:27px}.hypothesis h2{font-size:25px;letter-spacing:-.03em;margin:8px 0 14px}.hypothesis-rank{font-weight:900;font-size:12px;color:var(--green);letter-spacing:.1em;text-transform:uppercase}.hypothesis-rank span{color:#6f7d77;font-weight:700;letter-spacing:0;text-transform:none;margin-left:9px}.hypothesis p{line-height:1.62}.issue-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:15px;margin-top:28px}.issue-block{border-left:3px solid #d37f71}.issue-kicker{font-size:10px;font-weight:900;letter-spacing:.1em;color:var(--red);text-transform:uppercase}.issue-block h2{font-size:20px;margin:8px 0}.issue-block p{font-size:14px}.review-passes{padding-left:20px}.review-passes li{padding:6px 0 9px;color:#50615d}.footer{border-top:1px solid var(--line);padding:25px 0 30px;background:#edf1ed;color:#52635f;font-size:11px}.footer-inner{display:grid;grid-template-columns:1fr 1fr auto;gap:20px;align-items:center}.footer strong{color:var(--ink)}.footer a{font-weight:800}.red-callout{background:var(--red2);border-color:#e9bdb5}.red-callout strong{color:var(--red)}
@media(max-width:960px){.metrics{grid-template-columns:repeat(3,1fr)}.nav{gap:12px}.hero{grid-template-columns:1fr}.hero-aside{min-height:225px}.grid-three{grid-template-columns:repeat(2,1fr)}}
@media(max-width:680px){.wrap{width:min(100% - 26px,1160px)}.topbar{position:relative}.topbar-inner{align-items:flex-start;padding:12px 0;flex-direction:column}.nav{gap:11px}.nav a.active{padding-block:5px}.hero{padding-top:24px}.hero-main{padding:24px 21px}.hero h1{font-size:45px}.lead{font-size:16px}.metrics{grid-template-columns:repeat(2,1fr)}.grid-two,.grid-three,.issue-grid,.decision-grid{grid-template-columns:1fr}.section-head{align-items:flex-start;flex-direction:column}.source-list{grid-template-columns:1fr}.footer-inner{grid-template-columns:1fr}.page-intro{padding-top:32px}.key-values{grid-template-columns:1fr;gap:2px}.key-values dd{margin-bottom:10px}.hypothesis{padding:21px}.hypothesis-rank span{display:block;margin:4px 0 0}.table-wrap table{min-width:970px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
'''

    (DOCS / "data").mkdir(exist_ok=True)
    (DOCS / "style.css").write_text(styles, encoding="utf-8")
    for filename, title, content, script in (
        ("index.html", "Current decision", home, LEADERBOARD_SCRIPT),
        ("executive-summary.html", "Decision & site comparison", executive, ""),
        ("submission-table.html", "Historical submission comparison", submission_page, ""),
        ("research.html", "Ranked hypotheses", research, ""),
        ("irregularities.html", "Open issues & review", irregular, ""),
        ("audit-review.html", "Open issues & review", irregular, ""),
    ):
        (DOCS / filename).write_text(page(title, filename, content, script), encoding="utf-8")


def write_feeds(audit: dict[str, Any], card: dict[str, Any], leaderboard: dict[str, Any]) -> None:
    pre = audit["preflight"]
    prior = audit["prior_candidate"]
    pct = 100.0 * float(pre["minimum_directional_overlap"])
    feed = {
        "schema": "gems.current-status.v3",
        "updated_utc": card.get("review_date_utc"),
        "updated_time_precision": "date only; source audit timestamp is recorded separately",
        "source_audit_generated_utc": card.get("generated_utc"),
        "decision": "negative",
        "verdict": "negative",
        "ok_to_submit": False,
        "file_to_submit": None,
        "new_raster_sha256": None,
        "new_raster": None,
        "new_file_score_estimate": None,
        "leaderboard_estimate": None,
        "new_holdout_dti": None,
        "holdout_status": "not measured; hard pre-fit uniqueness stop",
        "experiments_run_in_this_review": int(card.get("experiments_run_in_this_review", 0)),
        "research_artifact_sha256": prior["sha256"],
        "research_artifact": {
            "filename": prior["file"],
            "sha256": prior["sha256"],
            "authorized_for_submission": False,
            "purpose": "historical research comparison only",
        },
        "literal_stop": {
            "candidate_dot_budget": int(pre["candidate_dot_budget"]),
            "minimum_directional_overlap_pct": pct,
            "limit_pct": 100.0 * float(pre["limit"]),
            "forced_duplicate": bool(pre["forced_duplicate"]),
            "scope": pre.get("scope"),
        },
        "score_evidence": {
            "GEMSDOE32_0_2778": "USER/OWNER-REPORTED; no organizer receipt located",
            "organizer_confirmed_score": None,
        },
        "public_leaderboard": {
            "feed": "public_leaderboard.json",
            "status": leaderboard.get("status"),
            "observed_utc": leaderboard.get("observed_utc"),
            "evidence_class": leaderboard.get("evidence_class"),
        },
        "current_run_card": "../../evidence/current_run_card.json",
        "release_audit": "../../evidence/release_audit_20261027.json",
        "reason": f"At the frozen {int(pre['candidate_dot_budget']):,}-dot budget, one registered witness forces at least {pct:.4f}% within-3-pixel overlap; the hard limit is {100*float(pre['limit']):.0f}%.",
        "portal_note": card.get("submission_note"),
        "portal_note_characters": len(str(card.get("submission_note", ""))),
    }
    (DOCS / "data/status_feed.json").write_text(json.dumps(feed, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    table = {
        "schema": "gems.submission-comparison.v3",
        "generated_utc": card.get("review_date_utc"),
        "evidence_source_generated_utc": card.get("generated_utc"),
        "verdict": "negative",
        "ok_to_submit": False,
        "current_candidate": None,
        "new_raster": None,
        "new_file_score_estimate": None,
        "leaderboard_estimate": None,
        "warning": "Historical scores are USER/OWNER-REPORTED without submission receipts; these files are research-only and none is unique within the focus nine.",
        "prior_research_artifact": audit["prior_candidate"],
        "focus_nine": audit["focus_nine"],
        "focus_lineage_geometry": audit["focus_lineage_geometry"],
    }
    (ROOT / "evidence/submission_table_20261027.json").write_text(
        json.dumps(table, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def main() -> None:
    audit, card, leaderboard, safety_by_sha = check_inputs()
    build_pages(audit, card, leaderboard, safety_by_sha)
    write_feeds(audit, card, leaderboard)
    print(f"Built six fail-closed pages from {audit.get('generated_utc')}; verdict=negative; no candidate/download authorization.")


if __name__ == "__main__":
    main()
