#!/usr/bin/env python3
"""Build the evidence-linked Pages site without inventing an approved TIFF."""
from __future__ import annotations

from html import escape
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SCORES = {24: "0.2477", 25: "0.2600", 27: "0.2449", 28: "0.2710", 30: "0.2600", 31: "0.2708", 32: "0.2778", 33: "0.2632", 36: "0.2750"}


def page(title: str, content: str) -> str:
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{escape(title)} · KANLERGEMS</title><link rel="stylesheet" href="style.css">'
            '</head><body><main>' + content +
            '</main><footer>KANLERGEMS · Maximize P(Win) through evidence. Own the outcome, including negative results.</footer></body></html>\n')


def build() -> None:
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    audit = json.loads((ROOT / "research/raster_audit.json").read_text())
    manifest = json.loads((ROOT / "research/raster_manifest.json").read_text())
    card = json.loads((ROOT / "research/run_card.json").read_text())
    e1 = json.loads((ROOT / "evidence/e1_reaudit_20261026.json").read_text())
    board = json.loads((ROOT / "evidence/official-page-check-20261026.json").read_text())
    board_score = board["public_leaderboard"]["rank_1"]["public_score"]
    board_time = escape(board["retrieved_utc"])
    reports = {r["site"]: r for r in audit["format_reports"]}
    rows, details, focus_data = [], [], []
    for record in manifest:
        site = record["site"]
        number = int(site.removeprefix("GEMSDOE"))
        report = reports[site]
        comparisons = [p for p in audit["directed_pairs"] if p["a"] == site]
        max_rho = max(p["spearman_rho"] for p in comparisons if p["spearman_rho"] is not None)
        max_overlap = max(p["fraction_a_dots_within_3px_of_b"] for p in comparisons if p["fraction_a_dots_within_3px_of_b"] is not None)
        same = [p["b"] for p in comparisons if p["decoded_pixels_equal_inside_footprint"]]
        link = escape(record["url"], quote=True)
        filename = escape(Path(record["path"]).name)
        focus_data.append({"site": site, "historical_file": Path(record["path"]).name,
                           "historical_sha256": record["sha256"], "historical_source_url": record["url"],
                           "owner_reported_score_unverified": float(SCORES[number]),
                           "new_candidate_file": None, "new_candidate_score": None,
                           "maximum_rank_correlation_vs_other_selected_references": max_rho,
                           "maximum_directional_overlap_within_3px": max_overlap,
                           "identical_selected_reference_sites": same,
                           "historical_duplicate_gate": any(p["duplicate_gate"] for p in comparisons),
                           "decision": "DO NOT SUBMIT"})
        rows.append(
            f'<tr><th><a href="#s{number}">{site}</a></th>'
            f'<td>{SCORES[number]}<small>Unverified owner report</small></td>'
            '<td><strong>None eligible</strong><small>No new validated file</small></td>'
            '<td>Unavailable<small>No defensible leaderboard estimate</small></td>'
            '<td><b class="bad">NO</b><small>Historical file fails overlap gate</small></td>'
            f'<td><a href="{link}">{filename}</a><small>Historical source · learning only</small></td>'
            '<td class="bad"><strong>DO NOT SUBMIT</strong></td></tr>'
        )
        equal_text = ("Pixel-identical within the footprint to " + ", ".join(same) + ".") if same else "Not pixel-identical to the other eight selected references, but still fails near-duplicate screening."
        details.append(
            f'<article id="s{number}"><h3>{site}</h3>'
            f'<p>Highest historical value supplied by the owner: <strong>{SCORES[number]}</strong> '
            '(unverified owner report, not a submission-page receipt).</p>'
            f'<p>RASTER-AUDIT: {report["positive_pixels"]:,} positive pixels; whole-grid range and grid check '
            f'{"PASS" if report["strict_whole_grid_range_and_grid_valid"] else "FAIL"}. '
            f'Maximum Spearman correlation against the other eight references: {max_rho:.4f}; '
            f'maximum candidate-directional overlap within 3 pixels: {max_overlap:.2%}. {escape(equal_text)}</p>'
            '<p><strong>No new eligible file.</strong> The referenced artifact is historical; a different name or compression is not a new strategy.</p>'
            f'<details><summary>Exact raster provenance</summary><p class="mono">SHA-256: {record["sha256"]}</p>'
            f'<p><a href="{link}">Pinned historical source</a> · <a href="raster_audit.json">All directional comparisons</a></p></details></article>'
        )
    (docs / "focus_sites.json").write_text(json.dumps({
        "label_note": "Scores are unverified owner reports; comparisons cover only nine selected historical rasters. No new file or score is approved.",
        "source": "raster_audit.json", "sites": focus_data}, indent=2, allow_nan=False) + "\n")
    geo = e1["calibration_geometry"]
    overlap = e1["max_candidate_overlap_3px"]
    source_files = ["raster_audit.json", "raster_manifest.json", "source_manifest.json", "run_card.json", "hypotheses.md", "source_register.md", "input_pins.json", "registry_scope.json", "external-data-candidate-review-20261026.md"]
    for file in source_files:
        shutil.copyfile(ROOT / "research" / file, docs / file)
    for file in ("official-page-check-20261026.json", "e1_reaudit_20261026.json", "h33_lineage_20261026.json"):
        shutil.copyfile(ROOT / "evidence" / file, docs / file)
    (ROOT / "evidence/run_card.json").write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")

    content = f'''<header><span class="eyebrow">KANLERGEMS · EVIDENCE FIRST</span>
<h1>Submission decision desk</h1><p class="lead">Nine priority sites, one clear answer about what is safe to submit.</p>
<p><a href="executive-summary.html">How to submit</a> · <a href="hypotheses.md">Research slate</a> · <a href="source_register.md">Official sources</a></p>
<p>Organizer public-board snapshot: <strong>{board_score:.4f}</strong> at {board_time} · not this project's score; may be stale. <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">View the current official board</a>.</p></header>
<section class="alert"><span class="eyebrow">CURRENT VERDICT · NEGATIVE</span><h2>No new TIFF is approved for submission.</h2>
<p><strong>Do not upload a historical file or the inherited E1 raster.</strong> A valid-looking TIFF is not enough: the inherited candidate fails the literal uniqueness rule, its earlier holdout evidence is withdrawn, and no new method has passed the required gates.</p>
<a class="button" href="run_card.json" download>Download decision card (JSON)</a><a class="button secondary" href="e1_reaudit_20261026.json" download>Download duplicate audit</a>
<p>No renamed copy, dummy file or unvalidated score estimate is offered as a competition submission.</p></section>
<div class="stats"><section><strong>{overlap:.2%}</strong><span>RASTER-AUDIT · inherited E1 overlap with registered lattice</span></section>
<section><strong>{sum(r['strict_whole_grid_range_and_grid_valid'] for r in audit['format_reports'])} / {len(audit['format_reports'])}</strong><span>RASTER-AUDIT · historical whole-grid range + grid checks</span></section>
<section><strong>0</strong><span>New experiments or competition slots used this review</span></section></div>
<section><h2>Executive comparison</h2><p>Historical values are <strong>unverified owner reports</strong>, not organizer-confirmed submission receipts. There is no reliable estimate for a new upload. Historical links are for learning only; all selected files fail the stated near-duplicate rule against one another.</p>
<div class="scroll"><table><thead><tr><th>Site</th><th>Historical result</th><th>File to submit</th><th>Estimated new score</th><th>Unique?</th><th>Historical reference</th><th>Decision</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></section>
<section class="alert"><h2>Why the previous E1 result was stopped</h2><p>The corrected, shared Euclidean check finds <strong>{overlap:.2%}</strong> of E1 dots within 3 pixels of an included calibration lattice, above the literal 70% stop. Its previous audit excluded that lattice and used Manhattan rather than Euclidean dilation. E1's pre-placement surface is unavailable, so its surface uniqueness cannot be reconstructed.</p>
<p>The prior quadrant split did not hide whole connected fault components, and its fixed-mask analysis used a model trained on the full catalogue. Its holdout and projected leaderboard claims are therefore withdrawn. <a href="lane-e1-xg-hgb.html">Read the corrected audit →</a></p>
<p>The lattice covers {geo['footprint_3px_coverage']:.2%} of the footprint within 3 pixels. Any raster with at least {geo['minimum_dot_count_for_forced_overlap_above_70_percent']:,} positive pixels necessarily exceeds the 70% rule against it; this is a geometric conflict in the protocol, not proof of geological copying. We do not exempt the lattice or reposition dots to game the test.</p></section>
<section><h2>Why the reported GEMSDOE32 result may have led</h2><p>RASTER-AUDIT: the selected GEMSDOE32 H33 B=2 raster is exactly the selected GEMSDOE31 raster after removing 2,545 of 40,199 dots within two Euclidean pixels of the peer-mirrored known catalogue; no dots were added. <a href="h33_lineage_20261026.json">Inspect the lineage audit →</a></p><p>The official distance-tolerant metric can reward nonredundant coverage while penalizing false-positive mass, making this a plausible mechanism—not a causal proof. The exact score-to-file receipts and hidden truth are unavailable, and the competition asks for predictions of all faults. No result here establishes that a new strategy will beat the reported value or the current public leader.</p>
<p>GEMSDOE25 and GEMSDOE30 are pixel-identical in the footprint. GEMSDOE32 and GEMSDOE36 have a high overlap as well; a filename or compressed-byte change is not scientific novelty. <a href="source_register.md">Read the evidence and sources →</a></p></section>
<section><h2>Site-by-site reference audit</h2><div class="cards">{''.join(details)}</div></section>
<section><h2>Research and next steps</h2><p>Four ranked geological hypotheses include cross-scarp K/Th texture displacement and persistent thermal residuals. They are not established discoveries or new scores. Related magnetic-profile work exists in GEMSDOE30; remaining novelty is unverified. <a href="hypotheses.md">Read the ranked slate →</a></p>
<p>Hash-pinned peer mirrors of the 19-band input, catalogue, sample and derived layers were restored locally. They are not authenticated organizer files; the shared prepared feature cache, full registry, explicit lane and comparable fold-local best remain absent. The peer sample contains known-fault ones despite the official page describing a total-fault-absence example; only its grid and footprint are used.</p>
<p>The public leaderboard value above is a dated static observation, not a live feed or upload receipt. No automated organizer monitoring is performed; the authenticated weekly allowance remains unknown.</p></section>
<section><h2>Sources &amp; audit trail</h2><ul><li><a href="source_register.md">Official-source register</a> · <a href="input_pins.json">Mirror input pins</a> · <a href="registry_scope.json">Incomplete registry scope</a>.</li>
<li><a href="raster_manifest.json">Nine pinned raster sources</a> · <a href="raster_audit.json">72 directed historical comparisons</a> · <a href="h33_lineage_20261026.json">H33 lineage audit</a> · <a href="e1_reaudit_20261026.json">E1 corrected audit</a>.</li>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Official problem and metric</a> · <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Official rules PDF</a> · <a href="https://github.com/drivendataorg/gems-prize-reference-solution">Organizer reference code</a>.</li></ul><p>All geoscientific mechanisms are hypotheses until tested; fault prediction is not proof of a geothermal vent.</p></section>'''
    (docs / "index.html").write_text(page("Executive summary", content))

    guide = '''<header><a href="index.html">← Decision desk</a><h1>How to make a submission</h1><p class="lead">Automated evidence first; a separate selector must approve any real slot.</p></header>
<section class="alert"><h2>Current status: DO NOT SUBMIT</h2><p>There is no new approved TIFF. Do not upload a historical reference or the quarantined E1 file. No competition slot was used in this review.</p></section>
<section><h2>1. Generate and automatically verify</h2><ol><li>Establish one exclusive method lane; use verified inputs and the pinned shared evaluator and writer. Freeze the complete parallel registry and a reproducible, fold-local current-best baseline.</li><li>Run a holdout canary for every actual feature; flag AUC above 0.90. Hide entire fault components with a buffer, compute catalogue-based features from visible faults only, mask those pixels exactly, and report pooled HOLDOUT-DTI, evaluator version, withheld-positive count and 95% CI.</li><li>Check the candidate surface before placing dots, then the final dots against the complete registry. Stop on a rank correlation over 0.90 or candidate-directional overlap over 70% within 3 pixels. No calibration exemption is authorized here.</li><li>Use the shared writer to produce a float32 single-band GeoTIFF with finite predictions in [0,1] inside the footprint and exact CRS, dimensions and transform. The public format says null/NaN outside bounds; our conservative check uses the template footprint. Authenticate the sample and resolve that interpretation before release.</li><li>Run the separate selector after scientific and format gates pass. The official rules PDF stated three submissions per week at this audit; the current account allowance and any changes must be checked on the authenticated page. A format PASS does not authorize a slot.</li></ol></section>
<section><h2>2. Resolve the reported range error</h2><p>Out-of-range predictions, nonfinite in-footprint values, unmasked nodata sentinels, or a portal-specific NaN interpretation are possible causes; the rejected file was not supplied, so the cause is unknown. Do not silently clip or claim a format check guarantees portal acceptance.</p><pre>python scripts/validate_raster.py candidate.tif data/sample_submission.tif</pre><p>The validator reports published-format checks and a separate whole-grid-finite diagnostic. It never approves submission and the local sample is currently a peer mirror, not organizer-authenticated.</p></section>
<section><h2>3. Only after selector approval</h2><ol><li>Download the exact approved TIFF and verify the SHA-256 against its run card. Use its distinct name and note of at most 140 characters.</li><li>On <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DrivenData</a>, enroll, open Submit → Make new submission, choose the TIFF (or a ZIP containing one TIFF), and enter the note.</li><li>Save the organizer submission-page receipt and tie it to the exact uploaded hash. Only such a receipt can establish an organizer-confirmed result for this project.</li><li>Follow the <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">official rules</a>: disclose generative-AI use as required and retain reproducible code, source licenses and documentation. The official prize process includes an expert review; local raster validation itself is automated.</li></ol></section>'''
    for name in ("executive-summary.html", "how-to-submit.html", "submission.html"):
        (docs / name).write_text(page("Submission guide", guide))
    e1_page = f'''<header><a href="index.html">← Decision desk</a><h1>E1 XG-HGB: duplicate stop</h1><p class="lead">A previous result, preserved for audit. It is not an eligible download or a recommended submission.</p></header>
<section class="alert"><h2>DO NOT SUBMIT · NO DOWNLOAD</h2><p>Exact candidate-directional Euclidean overlap with the registered calibration lattice: <strong>{overlap:.2%}</strong> (limit: 70%). The previous surface is unavailable; its pre-placement test cannot be reconstructed. The registry checked here is incomplete.</p></section>
<section><h2>What changed</h2><ul><li>The earlier nine-site comparison excluded a calibration reference and used Manhattan rather than Euclidean dilation. Its novelty pass is withdrawn.</li><li>Quadrant blocking does not hide whole components crossing a boundary. The prior fixed-mask analysis also used a globally trained model. Those holdout claims and the SGMC-anchored projection are withdrawn.</li><li>The raster has finite [0,1] values and matches the peer template's CRS, shape and transform, but fails this project's conservative outside-footprint null/NaN check. Actual portal acceptance is unknown.</li><li>The lattice's 3-pixel neighborhood covers {geo['footprint_3px_coverage']:.2%} of the footprint. A budget of at least {geo['minimum_dot_count_for_forced_overlap_above_70_percent']:,} positive pixels is mathematically forced to fail the strict overlap rule against this reference.</li></ul><p><a href="e1_reaudit_20261026.json">Open corrected machine-readable audit</a> · <a href="run_card.json">Current run card</a></p></section>'''
    (docs / "lane-e1-xg-hgb.html").write_text(page("E1 corrected audit", e1_page))


if __name__ == "__main__":
    build()
