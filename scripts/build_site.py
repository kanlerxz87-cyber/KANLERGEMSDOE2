#!/usr/bin/env python3
"""Render the audited, fail-closed GitHub Pages site from checked-in evidence.

This renderer intentionally has no positive authorization path. A new
candidate requires a new, independently replayed selector before changing it.
"""
from __future__ import annotations

import csv
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def page(title: str, active: str, body: str) -> str:
    nav = [("index.html", "Overview"), ("executive-summary.html", "Executive summary"),
           ("research.html", "Research"), ("irregularities.html", "Limitations")]
    links = "".join(f'<a {"aria-current=page" if href == active else ""} href="{href}">{label}</a>' for href, label in nav)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Auditable DOE GEMS fault discovery research and submission status.">
<title>{esc(title)} · GEMS Research</title><link rel="stylesheet" href="style.css"></head>
<body><header class="topbar"><div class="shell nav"><a class="brand" href="index.html"><span class="brand-mark">G</span><span>GEMS <small>RESEARCH</small></span></a><nav aria-label="Main navigation">{links}</nav><a class="source-link" href="https://github.com/kanlerxz87-cyber/KANLERGEMSDOE2">View repository ↗</a></div></header>
<main class="shell">{body}</main><footer><div class="shell footer-inner"><span>Evidence before submission. &nbsp; Maximize P(Win) · Own the Outcome.</span><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">Official competition ↗</a></div></footer></body></html>'''


def main() -> None:
    card = load(ROOT / "run_card.json")
    audit = load(ROOT / "evidence/focus_reaudit_20261027.json")
    snapshot = load(DOCS / "data/leaderboard_snapshot.json")
    if card.get("verdict") != "negative" or card.get("ok_to_submit") is not False:
        raise SystemExit("Site renderer only handles the current negative audited run card")
    if audit.get("missing_focus_sites") or len(audit.get("focus_sites", [])) != 9:
        raise SystemExit("Incomplete nine-site audit; do not publish a complete-looking table")
    if snapshot.get("source_url") != "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/":
        raise SystemExit("Unexpected leaderboard snapshot source")
    rows = audit["focus_sites"]
    candidate = next(x for x in audit["previous_local_candidates"] if x["file"] == card["submission_name"])
    if candidate["file_audit"]["sha256"] != card["raster_sha256"] or candidate["lattice_overlap_fraction"] <= 0.70:
        raise SystemExit("Candidate evidence and hard-stop run card disagree")
    hold = card["holdout_dti"]
    hold_text = (f"{hold['dti']:.6f} HOLDOUT-DTI · {hold['evaluator_version']} · "
                 f"N={hold['n_withheld_positive_pixels']:,} · 95% CI "
                 f"[{hold['ci95'][0]:.4f}, {hold['ci95'][1]:.4f}]")
    artifact = esc(card["submission_name"])
    sha = esc(card["raster_sha256"])
    lattice = 100 * candidate["lattice_overlap_fraction"]
    focus_max = 100 * card["correlation_overlap_vs_registry"]["max_focus_site_3px_overlap"]
    timestamp = esc(snapshot["observed_utc"])
    rank1, rank5 = float(snapshot["public_rank_1"]), float(snapshot["public_rank_5"])
    if not (0 <= rank5 <= rank1 <= 1):
        raise SystemExit("Invalid public leaderboard snapshot")
    official = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"
    files_link = f'downloads/{artifact}'
    badge = '<span class="badge danger"><span aria-hidden="true">●</span> DO NOT SUBMIT</span>'

    hero = f'''
<section class="hero"><div class="eyebrow"><span class="live-dot"></span> DOE GEMS / AUDIT DASHBOARD</div>
<h1>Better fault discovery<br><em>starts with evidence.</em></h1><p class="hero-lead">An independent check of the priority submissions, the current research raster, and the gates that protect a scarce competition slot.</p>
<div class="hero-links"><a class="button button-primary" href="executive-summary.html">Read executive summary <span>↗</span></a><a class="text-link" href="{official}">Open live leaderboard ↗</a></div></section>
<section class="alert" aria-labelledby="gate-title"><div class="alert-icon" aria-hidden="true">!</div><div><div class="alert-top">{badge}<span class="muted mono">AUDITED 27 OCT 2026</span></div><h2 id="gate-title">No submission is approved.</h2><p>The existing HTCADS research TIFF is finite and matches the pinned grid, but <strong>{lattice:.3f}%</strong> of its dots lie within 3 pixels of a registry lattice. The protocol's limit is 70%. The older “promote” receipt excluded that comparator and has been superseded.</p><div class="actions"><a class="button button-outline" href="{files_link}" download>Download TIFF for audit only ↓</a><a class="plain-link" href="irregularities.html">Why was it stopped? →</a></div></div></section>
<section class="stats" aria-label="At a glance"><article><span class="stat-label">RESEARCH RASTER</span><strong>Format checked</strong><p>Single-band float32; all stored cells finite in [0, 1]. Not a portal-acceptance guarantee.</p></article><article><span class="stat-label">UNIQUENESS GATE</span><strong class="red">Failed</strong><p>{lattice:.3f}% near the registry lattice; the full registry was not replayed.</p></article><article><span class="stat-label">WEEKLY SLOTS USED</span><strong>0</strong><p>No upload or automatic slot selection occurred in this session.</p></article><article><span class="stat-label">PUBLIC LEADERBOARD</span><strong>{rank1:.4f}</strong><p>Organizer's public #1 snapshot, {timestamp}. <a href="{official}">Live ↗</a></p></article></section>
<section class="section-grid"><article class="panel"><div class="panel-heading"><div><div class="eyebrow">THE RESEARCH FILE</div><h2>Validated format ≠ submit-ready</h2></div><span class="panel-num">01</span></div><p>The file below was produced in an earlier session. Its exact bytes have been rechecked, but it failed the written uniqueness rule. It is available for inspection, not for a competition upload.</p><div class="file-box"><span class="file-icon">TIF</span><div><strong>{artifact}</strong><small>SHA-256 <span class="mono break">{sha}</span></small></div></div><p class="small"><strong>Prior recorded estimate:</strong> {esc(hold_text)}. This is a local hide-and-recover result, not a predicted public or private leaderboard score; it was not independently replayed in this session.</p><a class="plain-link" href="data/run_card.json">Open run card (JSON) →</a></article>
<article class="panel"><div class="panel-heading"><div><div class="eyebrow">THE DECISION</div><h2>What needs to happen next</h2></div><span class="panel-num">02</span></div><ol class="steps"><li><b>Resolve the literal lattice conflict.</b><span>Do not silently exclude a registry raster or perturb dots to evade the stop.</span></li><li><b>Replay the scientific gates.</b><span>Use fold-visible features, per-feature canaries and paired holdout comparison against the current best.</span></li><li><b>Run a separate selector.</b><span>Verify artifact identity, full registry, official input provenance and account quota. No slot is auto-spent.</span></li></ol><a class="plain-link" href="research.html">Explore the next hypotheses →</a></article></section>
<section class="bottom-callout"><div><div class="eyebrow">THE NINE-SITE REVIEW</div><h2>Which historical file leads?</h2><p>GEMSDOE32 has the highest <em>user/owner-reported</em> value in the supplied list. No submission-page receipt linking it to the bytes was available.</p></div><a class="button button-dark" href="executive-summary.html">Compare all nine sites →</a></section>'''

    table_rows = []
    for r in rows:
        comp = r["focus_site_comparisons"][0]
        overlap = comp["fraction_candidate_dots_within_3px"] * 100
        exact = " · exact footprint duplicate" if comp["same_footprint_pixels"] else ""
        finite = "All cells finite" if r["file_audit"]["all_cells_finite_and_in_range"] else "Contains non-finite cells"
        table_rows.append(f'''<tr><td><a href="{esc(r['site_url'])}"><b>{esc(r['site'])} ↗</b></a></td><td><a class="mono file-name" href="{esc(r['blob_url'])}">{esc(r['file'])}</a><small>{finite}; historical file</small></td><td><strong>{esc(r['reported_value'])}</strong><small>USER/OWNER REPORT<br>no receipt verified</small></td><td><b class="red">No</b><small>{overlap:.2f}% near {esc(comp['site'])}{exact}</small></td><td><span class="mini-danger">DO NOT SUBMIT</span></td></tr>''')
    table_html = "\n".join(table_rows)
    summary = f'''
<div class="page-heading"><div class="eyebrow">DECISION BRIEF / 27 OCT 2026</div><h1>Executive summary</h1><p>The best file to submit under the current protocol is <strong>none</strong>. These are historical comparisons, not an invitation to resubmit someone else's raster.</p></div>
<div class="alert compact"><div class="alert-icon">!</div><div>{badge}<h2>Research artifact, not a submission</h2><p><a href="{files_link}" download>{artifact}</a> · SHA-256 <span class="mono break">{sha}</span></p><p>{esc(hold_text)} (previously recorded, not replayed). A reliable leaderboard estimate is unavailable. Dots fail the literal registry test ({lattice:.3f}% overlap); do not submit.</p></div></div>
<section class="panel"><div class="panel-heading"><div><div class="eyebrow">HISTORICAL HIGH VALUES</div><h2>Priority-site comparison</h2></div><span class="panel-num">09</span></div><p>Files and overlap were rechecked against pinned GitHub bytes. Values below were supplied by the user/owner; no organizer submission receipt linking a value to a file hash was available. They are <strong>not verified estimates or organizer-confirmed scores</strong>. “Unique” means the requested directional ≤3-pixel overlap test against the other eight historical files, not merely different file hashes.</p>
<div class="table-wrap"><table><thead><tr><th>Site</th><th>Historical file to inspect</th><th>Reported value<br><small>not a score receipt</small></th><th>Unique vs other sites?</th><th>Submission</th></tr></thead><tbody>{table_html}</tbody></table></div>
<p class="small">GEMSDOE25 and GEMSDOE30 have identical in-footprint predictions despite different file hashes and exterior encodings. The other high-overlap pairs need not be exact duplicates. No prior file is a newly generated submission.</p></section>
<section class="section-grid"><article class="panel"><div class="eyebrow">HOW TO SUBMIT — WHEN A FILE IS APPROVED</div><h2>Five steps, no guesswork</h2><ol class="steps numbered"><li><b>Open the current run card.</b><span>Proceed only if a fresh, independent selector explicitly authorizes the exact SHA-256. It does not currently do so.</span></li><li><b>Download its named .tif.</b><span>Confirm single band, float32, the competition CRS, shape and geotransform, and values in [0, 1].</span></li><li><b>Check the official account.</b><span>Sign in, verify remaining weekly allowance and rules on <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">DrivenData submissions ↗</a>.</span></li><li><b>Choose New submission.</b><span>Select the file or a ZIP containing exactly one TIFF; use the run card's unique name and note of at most 140 characters.</span></li><li><b>Keep the receipt.</b><span>Record the organizer's result and the exact file hash. Do not call a projection or holdout an organizer score.</span></li></ol></article>
<article class="panel"><div class="eyebrow">FORMAT &amp; QUOTA CAVEAT</div><h2>What the checks can—and cannot—prove</h2><p>The current file has no NaNs anywhere and passes the local whole-array [0, 1] test. The organizer's <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format">published format</a> says data outside the bounds are null/NaN. The relation between those bounds and the irregular mirrored footprint is not established here; neither encoding is guaranteed accepted.</p><p>Current-account quota and submission receipts require login; this project has no account access and no independent replay certificate. Its selector therefore remains fail-closed. The system does not upload.</p><a class="plain-link" href="irregularities.html">See all limitations →</a></article></section>'''

    research = f'''
<div class="page-heading"><div class="eyebrow">GEOLOGY / REPRODUCIBILITY</div><h1>Research, not inference by wishful thinking.</h1><p>Target faults that may indicate geothermal resources. A geothermal observation alone is not proof of a fault or a vent.</p></div>
<section class="panel"><div class="panel-heading"><div><div class="eyebrow">THE LEADING HISTORICAL CLAIM</div><h2>Why might the GEMSDOE32 file have done well?</h2></div><span class="panel-num">01</span></div><p>The inspected file is a sparse, catalogue-flank-pruned descendant of a historical dotted family. A 300 m triangular kernel can reward coverage without requiring every prediction to occupy every neighboring pixel. Reducing redundant false-positive mass is therefore a <strong>plausible hypothesis</strong>, not a measured causal explanation.</p><p>The reported 0.2778 is an <strong>unverified user/owner report</strong>, not an organizer receipt. The private truth is hidden, and the prior reciprocal fit cannot infer true-positive mass or fault prevalence from a few dot counts and rounded values. New fault pixels can also occur near known traces: <a href="https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516">DrivenData staff clarify the pixel-exact mask ↗</a>. A wider catalogue exclusion can discard real corrections.</p></section>
<section class="panel"><div class="panel-heading"><div><div class="eyebrow">FROZEN BEFORE NEW MODEL WORK</div><h2>Four testable next hypotheses</h2></div><span class="panel-num">04</span></div><p>Qualitative ranking within the registered HTCADS family. None was trained or tested in this session; the duplicate stop remains binding. Novelty across every other repository is unknown.</p><div class="hypotheses"><article><span>01 / MEDIUM COST</span><h3>Uncertainty-aware thermal orientation</h3><p>Test probe-gradient direction and uncertainty against gravity/magnetic edges over plausible up-gradient offsets. Mimic: alluvial flow, irrigation or road access.</p></article><article><span>02 / LOW–MEDIUM COST</span><h3>Paired-flank magnetic trough</h3><p>Look for opposite-sign short-wave magnetic slopes corroborated by a gravity edge and survey-resolution sensitivity. Mimic: volcanic contacts and leveling artifacts.</p></article><article><span>03 / MEDIUM COST</span><h3>Persistent opposing-scarp asymmetry</h3><p>Use multi-neighborhood LiDAR face asymmetry and structural direction, with shoreline and road controls. Mimic: terrace risers and berms.</p></article><article><span>04 / LOW–MEDIUM COST</span><h3>Alteration contrast across a ridge</h3><p>Compare K/Th on opposite sides of a structural edge and assess deposit-free ablation. Mimic: lithologic contacts and weathering.</p></article></div><p class="small">Exact layers, why each might detect unmapped faults, distinctions from this checkout, access and limitations: <a href="https://github.com/kanlerxz87-cyber/KANLERGEMSDOE2/blob/main/research/2026-10-27-next-hypotheses.md">full hypothesis register ↗</a>.</p></section>
<section class="panel"><div class="eyebrow">OFFICIAL SOURCES</div><h2>Evidence to review</h2><div class="source-list"><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/"><b>DrivenData problem &amp; metric</b><span>Task, weighted Tversky, grid and submission format ↗</span></a><a href="https://github.com/drivendataorg/gems-prize-reference-solution"><b>Official reference solution</b><span>Baseline model and CPU/GPU environment ↗</span></a><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and"><b>USGS GeoDAWN</b><span>Survey properties, resolution and licensing ↗</span></a><a href="https://gdr.openei.org/submissions/1391"><b>DOE INGENIOUS dataset</b><span>Thermal, geophysical, volcanic and paleo-geothermal data; CC BY 4.0 ↗</span></a><a href="https://www.osti.gov/dataexplorer/biblio/dataset/1148722"><b>DOE geothermal structural inventory</b><span>Documented fault tips, intersections and stepovers ↗</span></a></div></section>'''

    irregular = f'''
<div class="page-heading"><div class="eyebrow">AUDIT TRAIL / ACTION ITEMS</div><h1>Known limitations</h1><p>Failures and uncertainty are part of the result. No human inspector is used to override the gates.</p></div>
<section class="panel"><div class="eyebrow">IR-01 / HARD STOP</div><h2>The lattice makes the literal test unusually restrictive</h2><p>The verified registry lattice covers <strong>{audit['registry_lattice']['covered_within_3px']:,} of {audit['registry_lattice']['footprint_pixels']:,}</strong> footprint pixels within 3 pixels. Only <strong>{audit['registry_lattice']['uncovered_within_3px']:,}</strong> pixels are outside that radius. For any {candidate['file_audit']['positive_pixels_inside']:,}-dot candidate, at least <strong>{100*candidate['pigeonhole_min_overlap_fraction']:.2f}%</strong> must overlap by the pigeonhole principle; this candidate actually overlaps <strong>{lattice:.3f}%</strong>.</p><p>This does not prove geological copying: the lattice is a space-filling calibration pattern. It nevertheless triggers the user's unqualified “any registry raster” stop. A better scientific comparator policy requires an explicit protocol change; this project must not create an exception on its own.</p></section>
<section class="section-grid"><article class="panel"><div class="eyebrow">IR-02 / EVIDENCE</div><h2>Historical approval was invalid</h2><p>Prior code excluded the lattice, reported detector-only passing results, and labeled owner-supplied values as organizer-confirmed. The old approval flags have been superseded. The re-audit checks nine historical rasters plus the lattice; it does not claim a complete registry replay or recomputed pre-placement surface.</p><a class="plain-link" href="data/focus_audit.json">View exact re-audit JSON →</a></article><article class="panel"><div class="eyebrow">IR-03 / ACCESS</div><h2>Official input and quota access</h2><p>The official data and submission pages redirect to login. A public GitHub mirror restored the feature, template and label files, with hashes checked; identical hashes do not prove organizer origin or permission. The prepared feature-stack hash matches the historical cache. Official files, independent source verification and account quota remain unavailable here.</p></article></section>
<section class="panel"><div class="eyebrow">IR-04 / INFERENCE</div><h2>A holdout is not the leaderboard</h2><p>Mapped-fault hide-and-recover is an imperfect proxy for newly expert-mapped faults. Scores from different evaluators or label populations are not directly comparable. Neither a historical point estimate nor a fit to a few reported values establishes performance on hidden test data.</p><p>The selector is intentionally fail-closed until a complete independent replay and a legitimate account quota adapter exist. The static leaderboard snapshot is dated {timestamp}; <a href="{official}">the organizer's live page</a> remains the source of truth.</p></section>'''

    for name, title, body in [("index.html", "Overview", hero), ("executive-summary.html", "Executive summary", summary),
                              ("research.html", "Research", research), ("irregularities.html", "Limitations", irregular)]:
        (DOCS / name).write_text(page(title, name, body), encoding="utf-8")

    (DOCS / "data/focus_audit.json").write_text(json.dumps(audit, indent=2, allow_nan=False) + "\n")
    status = {"schema": "kanlergems2.status.v2", "generated_utc": card["generated_utc"],
              "verdict": "negative", "ok_to_submit": False, "reason": "literal registry duplicate",
              "audit_file": "data/focus_audit.json", "run_card": "data/run_card.json",
              "leaderboard_snapshot": snapshot, "new_experiments": card["new_experiments_this_session"],
              "submission_slots_used": card["submission_slots_used"]}
    (DOCS / "data/status_feed.json").write_text(json.dumps(status, indent=2, allow_nan=False) + "\n")
    # Replace the stale, falsely labeled public summary rather than serve it as current.
    (DOCS / "data/nine_site_summary_20261026.json").write_text(json.dumps({
        "superseded": True, "replacement": "focus_audit.json",
        "notice": "Historical user/owner reports are not organizer receipts; see current audited file.",
    }, indent=2) + "\n")
    with (DOCS / "data/nine_site_summary_20261026.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["site", "historical_file", "reported_value_unverified", "max_3px_overlap", "nearest_site", "ok_to_submit"])
        for r in rows:
            c = r["focus_site_comparisons"][0]
            writer.writerow([r["site"], r["file"], r["reported_value"], f"{c['fraction_candidate_dots_within_3px']:.6f}", c["site"], "false"])

    md_rows = []
    for r in rows:
        comp = r["focus_site_comparisons"][0]
        md_rows.append(f"| [{r['site']}]({r['site_url']}) | [{r['file']}]({r['blob_url']}) | {r['reported_value']} (unverified user/owner report) | No — {100*comp['fraction_candidate_dots_within_3px']:.2f}% vs {comp['site']} | **NO** |")
    md = f'''# Executive summary and submission guide

## **DO NOT SUBMIT — no candidate is approved**

The existing [HTCADS research TIFF](docs/downloads/{card['submission_name']}) is available **for audit only**. Its SHA-256 is `{card['raster_sha256']}`. It matches the pinned mirror's grid and all stored cells are finite in `[0,1]`, but {lattice:.3f}% of its dots are within three pixels of the registry lattice, above the literal 70% stop. The prior promotion omitted that raster and is superseded. File-format checks do not guarantee portal acceptance.

Prior recorded **{hold_text}** (not independently replayed this session) is an internal estimate, not a leaderboard forecast. **Estimated organizer score: unavailable.** The leaderboard snapshot observed {timestamp} was public #1 {rank1:.4f} and #5 {rank5:.4f}; [check live](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/). These are official public observations, not a submission-page receipt for our file.

| Site | Historical file for audit | Value supplied by user/owner | Unique vs other eight sites? | OK to submit? |
|---|---|---|---|---|
{chr(10).join(md_rows)}

The historical values are **not verified organizer receipts**. Uniqueness here is the directional within-3-pixel rule, not just file-hash inequality. GEMSDOE25 and GEMSDOE30 have identical footprint predictions. No older file is recommended for resubmission.

## Submission procedure — only after a future selector approves a new file

1. Check the exact file hash, canary, independent holdout replay, complete all-registry novelty, quota and a `promote` selector verdict. **The current selector cannot authorize a slot.**
2. Download the named single-band float32 GeoTIFF; validate CRS, shape, transform and values `[0,1]`. The published [format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format) says data outside bounds should be null/NaN; its relationship to the mirrored irregular footprint is unresolved.
3. Sign in at [DrivenData submissions](https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/); check the current weekly quota and rules.
4. Choose **New submission**, select the approved TIFF (or ZIP with exactly one TIFF), and use its distinct name and note of at most 140 characters.
5. Keep the organizer receipt and file hash. Only a receipt establishes a score for that file. No automatic upload occurs.

See the [research hypotheses](research/2026-10-27-next-hypotheses.md), [re-audit](evidence/focus_reaudit_20261027.json), [current run card](run_card.json), and [website](docs/index.html).
'''
    (ROOT / "EXECUTIVE_SUMMARY.md").write_text(md, encoding="utf-8")
    print("Built fail-closed Pages, nine-site table, status feed and executive summary.")


if __name__ == "__main__":
    main()
