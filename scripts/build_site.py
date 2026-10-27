#!/usr/bin/env python3
"""Build the current negative executive summary and static GitHub Pages site.

The audit JSON is the data source; this builder never performs experiments or
claims that a research artifact is authorized for a competition submission.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
AUDIT = json.loads((ROOT / "evidence/focus9_audit_20261027.json").read_text())
CARD = json.loads((ROOT / "evidence/run_card.json").read_text())
ROWS = AUDIT["rows"]
if CARD["verdict"] != "negative" or CARD["ok_to_submit"] is not False:
    raise SystemExit("This report builder requires the current negative run card")


def e(value: object) -> str:
    return html.escape(str(value), quote=True)


def row_md(row: dict) -> str:
    outside = "yes" if row["outside_nonfinite_pixels"] else "no"
    return (
        f"| [{row['site']}]({row['peer_page']}) | "
        f"[{row['filename']}]({row['download_url']}) | `{row['sha256']}` | "
        f"{row['reported_score']:.4f} | {row['positive_pixels']:,} | "
        f"{row['max_directional_3px_overlap_vs_other_eight'] * 100:.2f}% "
        f"({row['closest_site']}) | {outside} |"
    )


def row_html(row: dict) -> str:
    outside = "Yes" if row["outside_nonfinite_pixels"] else "No"
    return f'''<tr><th scope="row"><a href="{e(row['peer_page'])}">{e(row['site'])}</a></th>
<td><a class="file" href="{e(row['download_url'])}">{e(row['filename'])}</a>
<details><summary>SHA-256 &amp; pinned source</summary><code>{e(row['sha256'])}</code><br><a href="{e(row['source_blob_url'])}">View source commit</a></details></td>
<td class="num">{row['reported_score']:.4f}<span class="sub">owner/user reported</span></td>
<td class="num">{row['positive_pixels']:,}</td><td class="num">{row['max_directional_3px_overlap_vs_other_eight']*100:.2f}%<span class="sub">vs {e(row['closest_site'])}</span></td>
<td>{outside}<span class="sub">portal unknown</span></td></tr>'''


def build_markdown() -> str:
    rows = "\n".join(row_md(row) for row in ROWS)
    filename = CARD["existing_research_artifact"]["filename"]
    return f'''# Executive summary · 27 October 2026

> **NO SUBMISSION.** Literal-registry duplicate stop. Zero experiments, new rasters, uploads, or submission slots used in this review. A new unique submission cannot honestly be delivered under the current preregistered budget and literal registry rule.

## The decision in one calculation

The registered, SHA-pinned 5-pixel lattice covers **5,160,724 of 5,167,373** eligible footprint pixels within 3 pixels; only **6,649** are outside its halo. At preregistered **K = 37,654**, every possible set of distinct dots has at least `37,654 − 6,649 = 31,005` overlaps, or **82.3418%**. The protocol says stop at **more than 70%**, so the run stopped *before fitting or placement*. First forced-stop budget: 22,164 dots. One witness proves a stop; a non-stop with that witness would **not** prove uniqueness across the registry. [Proof and exact file checks](evidence/registry_preflight_20261027.json) · [Current JSON run card](evidence/run_card.json).

The historical [HTCADS GeoTIFF](docs/downloads/{filename}) is **research only, do not submit**. Its actual overlap with the lattice is **37,642/37,654 = 99.9681%**. Its local geometry and whole-array range tests pass, but complete scientific replay and current quota selection are unverified, and portal acceptance is unknown. Its SHA-256 is `{CARD['existing_research_artifact']['sha256']}`. It was not generated in this review. [Local validator](evidence/validator_receipt.json).

## Nine historical references — research downloads, not entry recommendations

The scores below are **OWNER/USER-REPORTED, UNVERIFIED**: no organizer submission-page receipts linking these files and scores were available. The filenames are independently hash-pinned peer files chosen for comparison, not proof those exact bytes received those scores. Links are exact commit-pinned historical downloads. The overlap is the *row's* fraction of positive pixels within inclusive 3 px of its nearest other reference among these nine; it is directional. **All nine fail the >70% rule within this subset.** Five have nonfinite values outside the footprint. “No” means the entire local array is finite and in [0,1], not that the portal will accept it. **Portal acceptance is unknown for every file; none is recommended for submission.** No holdout was independently recomputed for these artifacts in this run.

| Site | Exact historical GeoTIFF (pinned) | SHA-256 | User-reported score, unverified | Dots | Max 3-px overlap vs other 8 | Outside nonfinite? |
| --- | --- | --- | ---: | ---: | --- | --- |
{rows}

GEMSDOE25 and GEMSDOE30 have exactly identical in-footprint positive masks despite different file hashes. The complete [nine-file audit and directional matrix](evidence/focus9_audit_20261027.json) is not an exhaustive registry audit.

## What can and cannot be inferred about 0.2778

The reported value is the highest of the nine supplied reports, not an independently verified file-linked receipt or an overall leaderboard record. B2's thinning and distance-from-catalogue filtering *could* reduce redundant predictions and false-positive penalties under the [organizer's 300 m distance-weighted Tversky](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) metric, while potentially discarding true faults too. Differences among reported values do not establish causation, hidden true-positive counts, or a future score. A three-point reciprocal curve cannot identify private labels. Better predictions might exceed 0.2778, but **no new strategy here has an independently measured result or defensible projected score**.

For context only, the [organizer's public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) displayed **#1 = 0.4544, #5 = 0.3566 on 2026-10-27**; those public leaderboard values are not file-linked submission receipts. Earlier 0.4413 and 0.3195 figures are stale. [Refresh status](docs/data/leaderboard.json) — a dated snapshot until the refresh/deployment job succeeds.

## Geological research and evidence boundaries

[Four conditional, ranked hypotheses](knowledge/02_htcads_next_hypotheses_20261027.md) describe physical transforms, layers, plausible mimics, costs and official [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) / [DOE GDR INGENIOUS](https://gdr.openei.org/submissions/1391) sources. They are plausible research, not verified fleet-wide novel or tested improvements. The task is fault prediction, not proof of geothermal vents. Sources and license/coverage limitations are in the memo.

Historical **HOLDOUT-DTI** (not replayed here): HTCADS `0.112353`, 95% CI `[0.098995, 0.125743]`, `GEMSDOE32-HIDE-RECOVER-v3.0`, `N=22,232` withheld positives. It is not a public score prediction and does not authorize the old raster. Peer-reported **HOLDOUT-DTI** for different/latest candidates includes GEMSDOE24 `0.16606 [0.15186, 0.18034]` and GEMSDOE36 `0.170100 [0.1551, 0.1861]` (both reported as `gems-segment-pooled-v1`, `N=60,988` withheld positives); evaluator comparability and independent replay were not established. See the peer pages for their methods. **Current candidate: no holdout, no canary replay, no claimed gain.**

## Irregularities and verification

- The cached owner-mirror sample has **60,988 positives identical to the label mask** even though the [organizer description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format) describes a total-absence example. Use it only as footprint/grid template; never as a predictive feature. Labels and `existing_faults.tif` are byte-identical in the mirror. Mirror hashes do not establish official provenance. [Input diagnostics](evidence/input_diagnostics_20261027.json).
- A historical novelty gate excluded a registered space-filling control and checked after placement. Shared novelty now applies the literal gate to all entries and requires pre-placement support; legacy runners are blocked before fitting. A one-witness result is never a full-registry pass.
- The historical validator trusted self-reported promotion claims. The new byte-bound validator reports local format separately and fails closed on literal novelty, unreplayed science, and unverified quota. The official description permits null/NaN outside bounds while this project's stricter historical local screen requires finite values everywhere; this distinction does not prove the cause of a previous portal rejection.
- The feature stack was restored and prepared but not used to fit a model. Independent all-feature canary, all-entry surface/final replay, matched current-best holdout, and live quota verification remain outstanding. [Historical records](evidence/archive/README.md) are superseded, not current promotion authority.

See [README](README.md) for reproducibility, the preserved prompt and core values, and [Pages](docs/index.html) for the same current status.
'''


def build_html() -> str:
    rows = "\n".join(row_html(row) for row in ROWS)
    f = CARD["existing_research_artifact"]["filename"]
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Literal registry audit and nine-site research review for the GEMS Prize.">
<title>KANLERGEMSDOE2 · GEMS research review</title><link rel="stylesheet" href="style.css"></head>
<body><header class="top"><a class="brand" href="#top"><span class="brand-mark">K</span><span>KANLER <b>GEMS</b><small>RESEARCH / 2026</small></span></a><nav aria-label="Primary"><a href="#decision">Decision</a><a href="#comparison">Nine sites</a><a href="#research">Research</a><a href="#evidence">Evidence</a></nav><a class="top-link" href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Organizer leaderboard ↗</a></header>
<main id="top"><section class="hero"><div class="hero-copy"><div class="eyebrow"><span class="signal"></span> OCTOBER 27, 2026 / INDEPENDENT REVIEW</div><h1>A good result<br>is an <em>honest stop.</em></h1><p class="lede">Geothermal fault research, nine historical references, and a literal registry test. The current lane cannot pass its duplicate rule at the preregistered budget.</p><div class="hero-actions"><a class="button primary" href="#decision">Read the decision <span>↓</span></a><a class="button outline" href="#comparison">Explore the nine sites <span>↗</span></a></div></div><aside class="decision-card" aria-labelledby="decision-card-title"><div class="card-top"><span class="small-label">CURRENT VERDICT</span><span class="flag">NEGATIVE</span></div><h2 id="decision-card-title">Do not submit.</h2><p>No new GeoTIFF was generated. No competition slot was used.</p><div class="card-rule"></div><div class="decision-stats"><div><strong>82.34<span>%</span></strong><small>Minimum forced overlap</small></div><div><strong>70<span>%</span></strong><small>Protocol stop threshold</small></div></div><a class="card-link" href="data/run_card.json">Inspect the JSON run card <span>↗</span></a></aside><div class="hero-watermark" aria-hidden="true">02 / 09</div></section>
<div class="ticker"><span>◆ INTEGRITY BEFORE SUBMISSION</span><span>01 / NO NEW RASTER</span><span>02 / NO UPLOAD</span><span>03 / NO SLOT SPENT</span></div>
<section class="section proof" id="decision"><div class="section-heading"><div><div class="eyebrow">01 / THE DUPLICATE STOP</div><h2>One witness is enough.</h2></div><p>Even the best possible placement cannot satisfy the literal threshold at this budget.</p></div><div class="proof-grid"><div class="proof-copy"><p>The registered lattice reaches <strong>5,160,724</strong> of <strong>5,167,373</strong> footprint pixels within 3 pixels. Just <strong>6,649</strong> pixels lie outside its halo.</p><p>For any set of 37,654 distinct dots, at least 31,005 must lie inside it. That is <strong>82.3418%</strong>—above the rule's 70% stop threshold. This is a counting proof, not a model score.</p><div class="formula"><span>MINIMUM OVERLAP</span><code>(37,654 − 6,649) / 37,654 = 82.3418%</code></div><p class="muted">A non-stop against one witness is not a complete registry pass. No surface, canary, or holdout was run after this preflight.</p><a class="text-link" href="../evidence/registry_preflight_20261027.json">View the proof and file hashes ↗</a></div><div class="coverage" aria-label="Footprint coverage of the lattice"><div class="coverage-visual"><span class="ring"></span><div><strong>99.87%</strong><small>OF FOOTPRINT<br>WITHIN 3 PIXELS</small></div></div><div class="coverage-foot"><span><i></i> Covered <b>5,160,724</b></span><span><i></i> Uncovered <b>6,649</b></span></div></div></div><div class="notice"><span class="notice-icon">!</span><div><strong>Historical HTCADS file: research only.</strong> Its actual lattice overlap is 99.9681%. Local format checks passed; novelty failed and portal acceptance remains unknown. <a href="downloads/{e(f)}">Download historical TIFF ↗</a> <a href="../evidence/validator_receipt.json">Validator ↗</a></div></div></section>
<section class="section compare" id="comparison"><div class="section-heading"><div><div class="eyebrow">02 / THE COMPARISON</div><h2>Nine sites, one context.</h2></div><p>Exact, pinned reference downloads—not files recommended for entry.</p></div><div class="table-notice"><strong>Read before comparing:</strong> all scores are owner/user-reported and unverified; no submission-page receipts were located. Artifact-to-score links are unconfirmed. All nine fail the &gt;70% rule against at least one other file in this subset. Portal acceptance is unknown.</div><div class="table-wrap"><table><thead><tr><th>Site</th><th>Historical GeoTIFF / research only</th><th>Reported score</th><th>Dots</th><th>Max overlap vs 8</th><th>Outside nonfinite</th></tr></thead><tbody>{rows}</tbody></table></div><div class="table-footer"><span>Within inclusive 3 px · directional row → peer · not the full registry</span><a href="data/focus9_audit.json">Download full matrix ↗</a></div></section>
<section class="section research" id="research"><div class="section-heading"><div><div class="eyebrow">03 / INTERPRETATION</div><h2>What 0.2778 tells us—and doesn't.</h2></div><p>Research insight is not evidence of a hidden leaderboard outcome.</p></div><div class="research-grid"><article><div class="article-number">01</div><h3>A plausible mechanism</h3><p>Thinning redundant dots and filtering around known faults could reduce false-positive penalties in the organizer's 300 m metric. These choices can also remove true faults; the available reports cannot establish causation.</p></article><article><div class="article-number">02</div><h3>No forecast</h3><p>The reported GEMSDOE32 value is the highest of the nine supplied reports, not an independently verified file-linked score. A three-point curve cannot recover private labels. No new approach was evaluated here.</p></article><article><div class="article-number">03</div><h3>Promising, untested geology</h3><p>Thermal–alteration flank agreement and conductive-boundary persistence are research hypotheses, not discoveries or proven gains. Alluvial fans, contacts, and groundwater effects are plausible mimics.</p><a class="text-link" href="../knowledge/02_htcads_next_hypotheses_20261027.md">Read the ranked hypotheses ↗</a></article></div><div class="live-panel"><div><div class="eyebrow">PUBLIC LEADERBOARD / OBSERVATION ONLY</div><strong id="leader-score">0.4544</strong><span>public #1 DW-Tversky</span></div><div><p id="leader-status">Snapshot observed 2026-10-27. The public board may have changed.</p><a class="text-link" href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Check the organizer's current leaderboard ↗</a></div></div></section>
<section class="section evidence" id="evidence"><div class="section-heading"><div><div class="eyebrow">04 / VERIFY &amp; REPRODUCE</div><h2>Show the work.</h2></div><p>The current answer is negative. The supporting receipts explain why.</p></div><div class="evidence-grid"><a href="data/run_card.json"><span>01</span><strong>Current run card</strong><small>Verdict, mechanism and evidence limitations</small><b>↗</b></a><a href="data/registry_preflight.json"><span>02</span><strong>Registry preflight</strong><small>Counting proof and exact witness overlap</small><b>↗</b></a><a href="data/input_diagnostics.json"><span>03</span><strong>Input diagnostics</strong><small>Owner-mirror sample and label irregularity</small><b>↗</b></a><a href="../evidence/validator_receipt.json"><span>04</span><strong>Validator receipt</strong><small>Format valid ≠ submit authorized</small><b>↗</b></a></div><div class="footnote"><strong>Important limitation.</strong> The mirrored sample has 60,988 positive pixels identical to the label mask, unlike the organizer's described total-absence example. Use it only for the grid/footprint. All-entry replay, matched holdout, feature canaries and quota authorization remain unverified. <a href="../EXECUTIVE_SUMMARY.md">Read the full executive summary ↗</a></div></section></main>
<footer><span class="footer-brand">KANLER <b>GEMS</b></span><span>Evidence over optimism. Research over repetition.</span><span>Reviewed 27 OCT 2026 · <a href="https://github.com/kanlerxz87-cyber/KANLERGEMSDOE2">SOURCE ↗</a></span></footer><script src="site.js" defer></script></body></html>'''


def main() -> int:
    DOCS.mkdir(exist_ok=True)
    (ROOT / "EXECUTIVE_SUMMARY.md").write_text(build_markdown(), encoding="utf-8")
    (DOCS / "index.html").write_text(build_html(), encoding="utf-8")
    for name, fragment in (("executive-summary.html", "comparison"), ("research.html", "research"), ("irregularities.html", "evidence")):
        (DOCS / name).write_text(
            f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=index.html#{fragment}"><title>Current research review</title></head><body><p>HOLDOUT-DTI and all current review information: <a href="index.html#{fragment}">continue to the current report</a>.</p></body></html>\n',
            encoding="utf-8",
        )
    (ROOT / "index.html").write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=docs/index.html"><title>GEMS research review</title></head><body><p>Current verdict: negative, do not submit. <a href="docs/index.html">Open the research review</a>.</p></body></html>\n', encoding="utf-8")
    print("Built EXECUTIVE_SUMMARY.md and current static Pages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
