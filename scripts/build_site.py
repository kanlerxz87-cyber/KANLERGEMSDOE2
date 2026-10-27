#!/usr/bin/env python3
"""Build the provenance-first, download-ready static GEMS research portal.

The site intentionally separates artifact safety, selector eligibility, and permission
to submit. It never polls or invents a DrivenData score.
"""
from __future__ import annotations

import csv
import html
import io
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def esc(x: object) -> str:
    return html.escape(str(x), quote=True)


def write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = "\n".join(line.rstrip() for line in body.splitlines()) + "\n"
    path.write_text(normalized, encoding="utf-8")


def page(title: str, content: str, active: str = "index.html") -> str:
    nav = [
        ("index.html", "Overview"),
        ("executive-summary.html", "Summary"),
        ("research.html", "Research & sources"),
        ("irregularities.html", "Audit & limitations"),
    ]
    nav_html = "\n".join(
        f'<a class="{"active" if path == active else ""}" href="{path}">{label}</a>'
        for path, label in nav
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Audited GEMS submission artifact, holdout evidence, source provenance, and limitations.">
  <title>{esc(title)} · KANLERGEMSDOE2</title>
  <style>
    :root {{ --ink:#18252a; --muted:#53676c; --line:#d8e1dc; --paper:#f4f6f1; --card:#fff; --green:#124d40; --mint:#d9eee3; --amber:#805719; --amberbg:#fff0d3; --red:#8b3737; --redbg:#ffebeb; --blue:#265b79; --shadow:0 14px 36px rgba(18,45,42,.08); }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; color:var(--ink); background:var(--paper); font:16px/1.6 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif; }}
    a {{ color:#176a58; }}
    a:hover {{ color:#0b4639; }}
    .wrap {{ width:min(1180px,calc(100% - 36px)); margin:auto; }}
    header {{ background:#0c302b; color:#f4fbf7; border-bottom:4px solid #4cc096; }}
    .mast {{ display:flex; align-items:center; justify-content:space-between; gap:24px; padding:26px 0 18px; }}
    .brand {{ font-size:14px; letter-spacing:.12em; text-transform:uppercase; color:#98d8bf; font-weight:800; }}
    h1 {{ font-size:clamp(2rem,5vw,3.5rem); line-height:1.05; letter-spacing:-.045em; margin:.3rem 0 .75rem; }}
    header p {{ max-width:760px; color:#d8e9e1; margin:0 0 20px; }}
    nav {{ display:flex; flex-wrap:wrap; gap:8px; padding:0 0 18px; }}
    nav a {{ color:#dceae5; text-decoration:none; padding:8px 12px; border:1px solid #48625a; border-radius:999px; font-size:14px; }}
    nav a.active,nav a:hover {{ color:#0c302b; background:#c8efdc; border-color:#c8efdc; }}
    main {{ padding:26px 0 60px; }}
    .grid {{ display:grid; gap:16px; }}
    .cols2 {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
    .cols3 {{ grid-template-columns:repeat(3,minmax(0,1fr)); }}
    .card {{ background:var(--card); border:1px solid var(--line); border-radius:18px; padding:22px; box-shadow:var(--shadow); }}
    .card h2,.card h3 {{ line-height:1.2; letter-spacing:-.02em; margin:0 0 12px; }}
    h2 {{ font-size:clamp(1.5rem,3vw,2.2rem); margin:38px 0 14px; }}
    h3 {{ font-size:1.16rem; }}
    .eyebrow {{ color:var(--green); font-size:12px; letter-spacing:.13em; text-transform:uppercase; font-weight:800; }}
    .muted {{ color:var(--muted); }}
    .small {{ font-size:13px; }}
    .notice {{ border:1px solid #e3c987; background:var(--amberbg); color:#493914; border-radius:16px; padding:16px 18px; margin:18px 0; }}
    .good {{ background:var(--mint); border-color:#a8d9c0; color:#163b31; }}
    .bad {{ background:var(--redbg); border-color:#efc2c2; color:#572323; }}
    .pills {{ display:flex; flex-wrap:wrap; gap:8px; margin:14px 0; }}
    .pill {{ display:inline-flex; align-items:center; border-radius:999px; padding:5px 10px; background:#e8efeb; color:#28443c; font-size:12px; font-weight:800; letter-spacing:.025em; }}
    .pill.warn {{ color:#704c14; background:#ffedc3; }}
    .pill.danger {{ color:#7c3030; background:#ffe1e1; }}
    .pill.blue {{ color:#234e69; background:#e3f0f9; }}
    .metric {{ font-size:2.15rem; line-height:1.05; font-weight:850; letter-spacing:-.04em; color:#103f35; margin:10px 0; }}
    .metric-label {{ font-size:13px; line-height:1.45; color:var(--muted); }}
    .actions {{ display:flex; flex-wrap:wrap; gap:10px; margin:16px 0; }}
    .btn {{ display:inline-block; border-radius:10px; padding:10px 14px; font-weight:750; text-decoration:none; border:1px solid #0f5848; background:#0f5848; color:white; cursor:pointer; }}
    .btn.secondary {{ background:white; color:#124d40; }}
    .btn:hover {{ filter:brightness(.94); }}
    code,.mono {{ font-family:ui-monospace,SFMono-Regular,Menlo,monospace; overflow-wrap:anywhere; }}
    .hash {{ font-size:12px; line-height:1.5; display:block; color:#35484a; word-break:break-all; }}
    .table-wrap {{ overflow-x:auto; border:1px solid var(--line); border-radius:14px; background:white; }}
    table {{ width:100%; border-collapse:collapse; min-width:820px; }}
    th,td {{ text-align:left; padding:12px 13px; vertical-align:top; border-bottom:1px solid var(--line); }}
    th {{ background:#e9f1ec; font-size:12px; letter-spacing:.05em; text-transform:uppercase; color:#365249; }}
    tr:last-child td {{ border-bottom:0; }}
    .score {{ font-weight:850; white-space:nowrap; }}
    .source-list li {{ margin:.5rem 0; }}
    .two-col {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(260px,.65fr); gap:20px; align-items:start; }}
    .callout {{ border-left:4px solid #369775; background:#eff8f1; padding:14px 18px; margin:14px 0; }}
    footer {{ border-top:1px solid var(--line); padding:22px 0 36px; color:var(--muted); font-size:13px; }}
    .footer-links {{ display:flex; flex-wrap:wrap; gap:14px; }}
    @media(max-width:800px) {{ .cols3,.cols2,.two-col {{ grid-template-columns:1fr; }} .mast {{ display:block; }} .card {{ padding:18px; }} }}
  </style>
</head>
<body>
<header><div class="wrap">
  <div class="mast"><div><div class="brand">GEMS · Evidence-first submission workflow</div><h1>{esc(title)}</h1><p>Research artifact and audit record for the GEMS Prize challenge. Download safety, scientific selector eligibility, and submission authorization are tracked as different states.</p></div></div>
  <nav>{nav_html}</nav>
</div></header>
<main class="wrap">{content}</main>
<footer><div class="wrap"><div class="footer-links"><a href="../README.md">Repository README</a><a href="data/status_feed.json">Status feed JSON</a><a href="data/source_register.json">Source register JSON</a><a href="data/nine_site_audit.csv">Focus-nine CSV</a><a href="../evidence/nine_site_audit.json">Tracked audit evidence</a></div><p><strong>Own the Outcome:</strong> each claim is bounded by its evidence provenance. Generated by <code>scripts/build_site.py</code>; this is a static audit snapshot—not a live DrivenData leaderboard feed. No upload or slot selection is performed by this site.</p></div></footer>
<script>
async function copyText(id) {{
  const element = document.getElementById(id);
  if (!element) return;
  const value = element.textContent || "";
  try {{
    await navigator.clipboard.writeText(value);
  }} catch (_) {{
    const input = document.createElement("textarea");
    input.value = value;
    input.setAttribute("readonly", "");
    input.style.position = "fixed";
    input.style.opacity = "0";
    document.body.appendChild(input);
    input.select();
    document.execCommand("copy");
    input.remove();
  }}
}}
</script>
</body></html>"""


def metric_card(value: str, label: str, sub: str) -> str:
    return f'<div class="card"><div class="eyebrow">{esc(label)}</div><div class="metric">{esc(value)}</div><div class="metric-label">{sub}</div></div>'


def build() -> None:
    run = read_json("evidence/run_card.json")
    validation = read_json("evidence/validator_receipt.json")
    nine = read_json("evidence/nine_site_audit.json")
    focus = read_json("evidence/focus9_submission_audit_20261027.json")
    experiments = read_json("evidence/htcads_experiments.json")
    sources = read_json("registry/sources.json")

    tif = run["submission_filename"]
    zip_name = run["zip_filename"]
    note = run["submission_note"]
    tif_sha = run["raster_sha256"]
    format_info = validation["format_audit"]
    hr = run["holdout_dti"]["primary_hide_and_recover"]
    sg = run["holdout_dti"]["secondary_off_catalogue_sgmc"]
    focus_check = focus["candidate"]["focus9_final_dots_check"]
    current_status = validation["status"]
    site_rows = []
    for s in sorted(nine["focus_9_sites"], key=lambda x: x["reported_score"], reverse=True):
        score = f'{s["reported_score"]:.4f}'
        safe = bool(s["portal_range_0_1_safe_as_stored"])
        safe_text = '<span class="pill">RAW TIFF FORMAT-SAFE</span>' if safe else '<span class="pill danger">RAW TIFF RANGE-UNSAFE (NaN outside grid)</span>'
        file_link = f'<a href="{esc(s["source_view_url"])}">{esc(s["filename"])}</a>'
        site_rows.append(
            '<tr>'
            f'<td><strong>{esc(s["site"])}</strong><br><span class="small muted">{esc(s["repo"])}</span></td>'
            f'<td class="score">{score}<br><span class="pill warn">USER/OWNER-REPORTED · UNVERIFIED</span></td>'
            f'<td>{int(s["positive_dots_in_footprint"]):,}<br><span class="small muted">positive pixels · raster audit</span></td>'
            f'<td>{safe_text}<br><span class="small muted">Single band / template grid: {"yes" if s["raster_metadata"]["grid_matches_template"] else "no"}</span></td>'
            f'<td>{100*s["candidate_dots_within_3px_of_peer_fraction"]:.2f}%<br><span class="small muted">candidate dots near this site’s dots</span></td>'
            f'<td>{file_link}<br><span class="small muted">SHA-256 {esc(s["source_sha256_verified"][:12])}… · pinned commit {esc(s["source_ref"][:12])}</span></td>'
            '</tr>'
        )

    experiments_rows = []
    for e in experiments["experiments"]:
        h = e["holdout_hide_recover"]
        g = e["holdout_sgmc_offcat"]
        experiments_rows.append(
            '<tr>'
            f'<td><strong>{esc(e["experiment_id"])}</strong><br>{esc(e["name"])}</td>'
            f'<td><strong>{h["pooled_dti"]:.6f}</strong><br><span class="small">HOLDOUT-DTI · {esc(h["label"].split("(",1)[1].rstrip(")"))}</span></td>'
            f'<td>{g["sgmc_prevalence_calibrated_dti"]:.6f}<br><span class="small">HOLDOUT-DTI · {esc(g["label"].split("(",1)[1].rstrip(")"))}</span></td>'
            f'<td>{"SELECTED FOR FROZEN RUN CARD" if e["experiment_id"] == experiments["selected_experiment"] else "not selected"}</td>'
            '</tr>'
        )

    holdout_html = f"""
      <div class="grid cols2">
        {metric_card(f'{hr["pooled_dti"]:.6f}', 'HOLDOUT-DTI · primary', esc(hr['label']))}
        {metric_card(f'{sg["sgmc_prevalence_calibrated_dti"]:.6f}', 'HOLDOUT-DTI · secondary', esc(sg['label']))}
      </div>
      <p class="small muted">These are frozen spatial-holdout results from the recorded run, not rerun during this audit and not public/private leaderboard scores. Do not convert either value into a live-score projection.</p>
    """

    file_actions = f"""
      <div class="actions">
        <a class="btn" download href="downloads/{esc(tif)}">Download unique GeoTIFF</a>
        <a class="btn secondary" download href="downloads/{esc(zip_name)}">Download single-TIFF ZIP</a>
        <button class="btn secondary" type="button" onclick="copyText('submission-name')">Copy submission name</button>
        <button class="btn secondary" type="button" onclick="copyText('submission-note')">Copy note</button>
      </div>
    """

    top_content = f"""
    <div class="notice"><strong>No live submission has been made.</strong> No slot was selected, no upload was performed, and no organizer receipt is present. Historical focus-site scores on this page are user/owner-reported and unverified. The current live score is therefore <strong>not available</strong>.</div>
    <section class="two-col">
      <div class="card">
        <div class="eyebrow">Candidate · {esc(run['hypothesis'].split('—')[0].strip())}</div>
        <h2 style="margin:8px 0 10px">A unique, format-safe TIFF—eligible for a separate selector, not authorized to submit</h2>
        <p class="muted">The candidate is the frozen HTCADS EXP-2 artifact. This review verified its SHA-256, one-band float32 format, competition grid, complete [0, 1] range, zero non-finite cells, and ZIP contents. It did not rerun the model or its holdout evaluator.</p>
        <div class="pills">
          <span class="pill">FORMAT: {esc(current_status['format_validation'])}</span>
          <span class="pill">DOWNLOAD: {esc(current_status['download'])}</span>
          <span class="pill">SELECTOR: {esc(current_status['selector_eligibility'])}</span>
          <span class="pill danger">SUBMISSION: {esc(current_status['submission_authorization'])}</span>
        </div>
        {file_actions}
        <p><strong>Filename</strong><br><code>{esc(tif)}</code></p>
        <p><strong>SHA-256</strong><span class="hash">{esc(tif_sha)}</span></p>
        <p><strong>Submission name</strong><br><code id="submission-name">{esc(run['submission_name'])}</code></p>
        <p><strong>Submission note ({int(run['note_length'])}/140 characters)</strong><br><code id="submission-note">{esc(note)}</code></p>
      </div>
      <aside class="grid">
        <div class="card"><div class="eyebrow">Format audit · automated</div><div class="pills"><span class="pill">PASS</span><span class="pill">Single-band float32</span><span class="pill">All pixels finite</span><span class="pill">[0, 1] full-array range</span></div>
          <p><strong>Grid:</strong> {format_info['shape'][0]} × {format_info['shape'][1]}, {esc(format_info['crs'])}<br><strong>Transform:</strong> <code>{esc(format_info['transform'])}</code><br><strong>Positive pixels:</strong> {format_info['emitted_positive_pixels']:,} · format audit<br><strong>On known catalogue:</strong> {format_info['on_catalogue_positive_pixels']:,} · format audit</p>
          <p class="small muted">Exact grid and range are tested against the checked-in sample-template mirror; this proves format safety, not organizer authorization.</p>
        </div>
        <div class="card"><div class="eyebrow">Separate decision states</div><ul>
          <li><strong>Format-safe:</strong> yes; automated exact-grid and value-range checks passed.</li>
          <li><strong>OK to download:</strong> yes; TIFF and one-TIFF ZIP hashes match.</li>
          <li><strong>Selector-eligible:</strong> yes under the recorded evidence gates.</li>
          <li><strong>Authorized to submit:</strong> no; no live slot was selected.</li>
          <li><strong>Live score / receipt:</strong> none available; no upload was made.</li>
        </ul></div>
      </aside>
    </section>

    <h2>Recorded holdout evidence</h2>
    {holdout_html}
    <div class="callout"><strong>Uniqueness protocol:</strong> the current final-dot comparison was recomputed against the nine pinned focus-site TIFFs. The largest directed 3-pixel overlap is <strong>{focus_check['max_candidate_dots_within_3px_fraction']*100:.2f}%</strong> ({esc(focus_check['max_overlap_site'])}, below the 70% limit); maximum absolute final-raster Spearman is <strong>{abs(focus_check['max_abs_final_raster_spearman']):.5f}</strong> ({esc(focus_check['max_rho_site'])}, below 0.90). These are <strong>REGISTRY AUDIT</strong> values, not DTI scores. The full 192-raster/pre-placement checks are only recorded in the frozen run card, not independently reproduced now.</div>

    <h2>Three preregistered experiments · no additional experiment run</h2>
    <p class="muted">The HTCADS lane used its maximum of three experiments. Values below are each labeled <strong>HOLDOUT-DTI</strong> with evaluator, withheld-positive count and interval. EXP-2 was selected into the frozen research run card; that is not a live-slot selection.</p>
    <div class="table-wrap"><table><thead><tr><th>Experiment</th><th>Primary spatial holdout</th><th>Secondary off-catalogue holdout</th><th>Research status</th></tr></thead><tbody>{''.join(experiments_rows)}</tbody></table></div>

    <h2>Focus-site comparison · owner/user claims, not organizer receipts</h2>
    <div class="notice"><strong>Score provenance:</strong> every reported value below is supplied in the user prompt and/or found in owner-controlled mirrors. None has a verified DrivenData receipt in this workspace. These values are not confirmed current standings.</div>
    <div class="table-wrap"><table><thead><tr><th>Site</th><th>Reported historical value</th><th>Positive pixels<br><span class="small">raster audit, not score</span></th><th>Raw TIFF format</th><th>Current candidate overlap<br><span class="small">directed, 3 px</span></th><th>Pinned artifact</th></tr></thead><tbody>{''.join(site_rows)}</tbody></table></div>
    <p class="small muted">All nine peer rasters match the sample-template grid. Several raw owner TIFs contain NaN outside the footprint and therefore fail the strict full-array [0, 1] format gate as stored; the table does not make them submission recommendations. GEMSDOE25 and GEMSDOE30 have different file bytes but identical positive-pixel masks inside the competition footprint.</p>

    <h2>What can be said about the reported GEMSDOE32 value 0.2778?</h2>
    <div class="card">
      <p><span class="pill warn">USER/OWNER-REPORTED · UNVERIFIED</span> The available file hash and pixel count can be checked, but its leaderboard value cannot be reconstructed from a TIFF or a GitHub mirror. No organizer receipt was verified.</p>
      <p>The reference-solution notebook at pinned commit <a href="https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/unet-mc-cv-reference-solution.ipynb">aebe92f7…</a> uses Tversky-loss weights α=0.2 and β=0.8. That supports only the loss-weight convention, not an assertion that this notebook implements the official leaderboard score. Under a neighborhood-overlap objective, thinning can reduce redundant false-positive mass while preserving local coverage; it is a plausible mechanism for why sparse outputs may fare better, not proof of what happened on the private test set.</p>
      <p><strong>Withdrawn:</strong> a former three-point linear fit was used to infer hidden true-positive counts and the size of the private fault set, and to claim pruned catalogue-near dots were all false positives. Those quantities are not identifiable from three reported score/count pairs. The inference has been removed.</p>
      <p>GEMSDOE32's mirrored TIFF contains {next(s['positive_dots_in_footprint'] for s in nine['focus_9_sites'] if s['site']=='GEMSDOE32'):,} positive pixels and passes the raw full-array format/range check as stored. Its reported {next(s['reported_score'] for s in nine['focus_9_sites'] if s['site']=='GEMSDOE32'):.4f} value remains unverified. The candidate is a different SHA-256 and does not exactly copy any of the nine audited site files.</p>
    </div>
    """

    executive = f"""
    <div class="notice"><strong>Decision snapshot:</strong> candidate is format-safe and downloadable; its recorded scientific gates support promotion to a separate selector. <strong>It is not authorized to submit.</strong> No slot was selected or spent and no live score was obtained.</div>
    <div class="grid cols3">
      {metric_card('FORMAT-SAFE', 'Artifact format', 'One float32 band; exact sample-template grid; all values finite and in [0, 1].')}
      {metric_card('OK TO DOWNLOAD', 'TIF + ZIP', f'Single-TIFF ZIP and inner TIFF hashes verified. Candidate SHA-256: {tif_sha[:16]}…')}
      {metric_card('NOT AUTHORIZED', 'Live submission', 'Requires a separately selected live slot and user action. No upload or organizer receipt exists.')}
    </div>
    <h2>Candidate evidence</h2>{holdout_html}
    <p><strong>HOLDOUT-DTI:</strong> results are recorded from the frozen run card, not rerun in this review. The holdout DTI is not a score projection or a leaderboard value.</p>
    <div class="card"><h3>Download</h3>{file_actions}<p><code>{esc(tif)}</code></p><p>Note ({run['note_length']}/140): <code>{esc(note)}</code></p><p>Full SHA-256: <span class="hash">{esc(tif_sha)}</span></p></div>
    <h2>Scope and limitations</h2><ul>
      <li>Full pre-placement surface correlation was recorded as 0.179514 against 192 archive rasters in the prior run card; it was not reproduced because the pre-placement surface was not retained.</li>
      <li>Current final-dot uniqueness was independently checked against all nine pinned focus-site rasters; maximum directed 3-pixel overlap is {focus_check['max_candidate_dots_within_3px_fraction']*100:.2f}%.</li>
      <li>The recorded model and holdout results were generated on prior branch <code>{esc(run['branch'])}</code>. The artifact hash and format were rechecked on this branch; no model rerun occurred.</li>
      <li>No official organizer score receipt was available. Historical 0.2778 is user/owner-reported, not organizer-confirmed.</li>
      <li>The current static site is not a live leaderboard poll. The DrivenData data page is login-walled; official-host data downloads and a submission were not performed from this sandbox.</li>
    </ul>
    """

    source_items = []
    for s in sources["official_competition_sources"]:
        source_items.append(f'<li><a href="{esc(s["url"])}"><strong>{esc(s["title"])}</strong></a><br><span class="small muted">{esc(s["verification"])} {esc(s.get("supports", ""))}</span></li>')
    for s in sources["official_geoscience_data_sources"]:
        source_items.append(f'<li><a href="{esc(s["url"])}"><strong>{esc(s["title"])}</strong></a><br><span class="small muted">{esc(s["verification"])} {esc(s.get("supports", ""))}</span></li>')

    research = f"""
    <div class="notice"><strong>Untested queue only:</strong> no new hypothesis below was implemented or tested. HTCADS H-K1 used all three permitted experiments. Each proposal is qualitative; none carries a projected DTI number.</div>
    <h2>Ranked new hypotheses</h2>
    <div class="grid">
      <div class="card"><div class="eyebrow">Rank 1 · local mirrored data</div><h3>Geothermometer discordance / disequilibrium</h3><p>H-K1 uses maximum quartz/chalcedony/Na-K-Ca values. New transform: estimate robust inter-geothermometer spread and pairwise residuals (only compare measured temperatures when source definitions support it), then test a spatially sparse, uncertainty-weighted field gated by visible structural evidence. Potential is moderate but low-confidence because thermometer columns are sparse; implementation cost is low-to-moderate. Mimics include shallow mixing, boiling/cooling, sample differences, and host-lithology effects.</p><p><a href="https://gdr.openei.org/submissions/1391">DOE GDR #1391</a> · official source record; current bytes in the workspace are owner-mirror copies. Never use <code>dist_known_fault_px</code>.</p></div>
      <div class="card"><div class="eyebrow">Rank 2 · new official imagery</div><h3>Landsat SWIR hydrothermal alteration</h3><p>Construct seasonally robust clay/hydroxyl and carbonate/silica-sensitive surface-reflectance composites, mask clouds/vegetation/playa moisture/mines, residualize by lithology and illumination, then aggregate 30 m anomalies to the 100 m grid. Potential is moderate; cost medium-to-high. Mimics include lithologic contacts, evaporites, mines, soil moisture, and vegetation. This is distinct from airborne radiometrics, MT, and H-K5 InSAR.</p><p><a href="https://www.usgs.gov/landsat-missions/landsat-collection-2-surface-reflectance">USGS Landsat Collection 2 surface reflectance</a> · no scenes are cached.</p></div>
      <div class="card"><div class="eyebrow">Rank 3 · new time dimension</div><h3>ComCat earthquake migration / swarm geometry</h3><p>Model time-ordered, uncertainty-weighted event migration and depth progression; H-K3 only had static seismic-density fields. Potential is moderate-to-high only where the catalog is complete and activity is present; cost high. Mimics include aftershocks, geothermal injection, volcanic swarms, quarry blasts, and network changes.</p><p><a href="https://earthquake.usgs.gov/data/comcat/index.php">USGS ComCat</a> · API/docs reviewed; no AOI query was run.</p></div>
      <div class="card"><div class="eyebrow">Rank 4 · sparse hydrogeology</div><h3>Groundwater head discontinuity / seasonal lag</h3><p>Test persistent head offsets and recharge-response phase shifts across candidate structures using matched monitoring wells and aquifer/pumping controls. Potential is low-to-moderate and coverage-dependent; cost high. Mimics include aquifer contacts, pumping, irrigation, recharge variation, and well construction.</p><p><a href="https://api.waterdata.usgs.gov/">USGS Water Data APIs</a> · no AOI query was run.</p></div>
    </div>
    <p><a href="../knowledge/02_untried_hypotheses_20261027.md">Full ranked hypothesis notes (layers, transforms, mimics, cost and source availability)</a>. Existing H-K1–H-K5 are listed in <a href="../registry/preregistration_htcads.json">the frozen preregistration</a>; the numeric ranges there are projections, not scores.</p>
    <h2>Official source audit register</h2>
    <p>The links are direct to official agency/challenge/reference records. “Reviewed” means page metadata/content was inspected; it does not mean source data bytes were downloaded. Owner-mirror SHA-256 matches establish mirror integrity only.</p>
    <ul class="source-list">{''.join(source_items)}</ul>
    <div class="card"><h3>Scoring provenance</h3><p>The only official reference-solution fact independently retrieved in this review is its Tversky-loss weighting (α=0.2, β=0.8). The notebook does not authenticate any historical score or reproduce the official leaderboard implementation. Historical focus-site values are therefore unverified user/owner reports.</p><p><a href="data/source_register.json">Download full source register</a> · <a href="data/focus9_submission_audit.json">Download pinned-raster audit JSON</a></p></div>
    """

    irregularities = f"""
    <div class="notice bad"><strong>Corrective audit:</strong> multiple earlier files and generated pages asserted organizer-confirmed scores without a verified receipt, inferred hidden test-set properties from an underdetermined three-point fit, and conflated artifact safety with submission permission. Those claims have been withdrawn.</div>
    <h2>Known irregularities and current handling</h2>
    <div class="grid">
      <div class="card"><h3>1 · Historical score provenance</h3><p>Previous records called site scores <code>ORGANIZER-CONFIRMED</code> while citing owner-controlled receipt ledgers that were not present in this workspace. This review did not retrieve a DrivenData receipt. All nine values are now labeled <strong>USER/OWNER-REPORTED · UNVERIFIED</strong>.</p><p>Official leaderboard review link: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">DrivenData GEMS public leaderboard</a>. No current ranking claim is made.</p></div>
      <div class="card"><h3>2 · GEMSDOE32 0.2778 inversion withdrawn</h3><p>A prior three-point regression was treated as proof of hidden-set size, weighted true-positive count, and zero true positives among removed catalogue-collar pixels. The regression is non-identifying: weighted TP, FP, FN, kernel overlap, and the hidden set all vary with pixel placement. The score/count fit does not isolate them. The inference and its implied projections were deleted.</p></div>
      <div class="card"><h3>3 · Legacy holdout self-censoring</h3><p>Some older per-site Hide-and-Recover results used static full-catalogue distance collars. A full-catalogue collar can remove predictions near a withheld segment, self-censoring the evaluation. Those old per-site holdout values are not displayed as calibrated live-score proxies. The frozen current-candidate record is retained with its evaluator/version and is explicitly not rerun in this audit.</p></div>
      <div class="card"><h3>4 · Evaluator entrypoint mismatch fixed</h3><p><code>scripts/evaluate_holdout.py</code> formerly contained an MTR1/multi-experiment runner despite its documented evaluator role and could fall through to an old experiment. It now delegates normal candidate evaluation to the canonical spatially blocked holdout evaluator. The legacy <code>--verify-kg2</code> path is read-only artifact verification; it cannot run MTR1, launch another experiment, select a slot, or authorize an upload.</p></div>
      <div class="card"><h3>5 · Missing independent pre-placement surface</h3><p>The prior run card records a maximum absolute surface Spearman value of 0.179514 against 192 registry rasters. The actual pre-placement surface array was not retained, so this review could not reproduce that check. The current final-dot audit against nine pinned focus-site TIFs is independently recomputed; it is not a substitute for the full registry surface check.</p></div>
      <div class="card"><h3>6 · Mirror provenance</h3><p>Competition and external data restored from owner-controlled GitHub mirrors matched their pinned hashes. This proves consistency with the mirror manifest, not official-host authenticity, licensing beyond the cited record, or organizer score provenance. The competition data page is login-walled and was not accessed.</p></div>
      <div class="card"><h3>7 · No live selector or upload</h3><p>The candidate is format-safe, downloadable, and recorded as selector-eligible. It is <strong>not authorized to submit</strong>: no live slot was selected and no upload was performed. The static status feed does not poll DrivenData and should not be read as live standings.</p></div>
      <div class="card"><h3>8 · Parallel KG2 lane archived separately</h3><p>KG2-MGHV has a separate archived run card and a different holdout evaluator. Its DTI cannot be compared numerically with HTCADS results. It is not selected as the current candidate and cannot overwrite the active run card through its verifier.</p></div>
    </div>
    <h2>Current audit state</h2>
    <div class="grid cols3">
      {metric_card(f'{focus_check["max_candidate_dots_within_3px_fraction"]:.5f}', 'REGISTRY AUDIT · max focus-9 overlap', 'Directed candidate-dot fraction within 3 px of the nearest pinned focus-site raster; threshold 0.70.')}
      {metric_card(f'{abs(focus_check["max_abs_final_raster_spearman"]):.5f}', 'REGISTRY AUDIT · max |Spearman|', 'Final-raster Spearman against the nine pinned focus-site TIFs; threshold 0.90.')}
      {metric_card('NO RECEIPT', 'ORGANIZER SCORE', 'No submission-page receipt or authenticated current leaderboard snapshot was verified.')}
    </div>
    <p class="small muted">The two decimal registry values are similarity diagnostics—not HOLDOUT-DTI scores. The historical public score claims remain unverified.</p>
    """

    # A machine-readable status snapshot: deliberately no live-score field with a value.
    status_feed = {
        "schema": "kanlergemsdoe2.status_feed.v2",
        "generated_utc": nine["generated_utc"],
        "feed_type": "static audit snapshot; not a live leaderboard feed",
        "candidate": {
            "hypothesis": run["hypothesis"],
            "filename": tif,
            "zip_filename": zip_name,
            "sha256": tif_sha,
            "holdout_dti": {
                "primary": hr,
                "secondary_sgmc": sg,
                "labels_are_holdout_not_live_score": True,
            },
            "status": validation["status"],
            "format_audit": {
                "count": format_info["count"],
                "shape": format_info["shape"],
                "crs": format_info["crs"],
                "transform": format_info["transform"],
                "dtype": format_info["dtype"],
                "full_array_values_in_0_1": format_info["values_in_0_1"],
                "finite_pixels": format_info["full_grid_finite_pixels"],
                "nan_pixels": format_info["full_grid_nan_pixels"],
                "positive_pixels": format_info["emitted_positive_pixels"],
            },
            "organizer_confirmed_score": None,
            "organizer_receipt_present": False,
            "live_slot_selected": False,
            "live_submission_performed": False,
        },
        "score_provenance": nine["score_provenance"],
        "focus_sites": [
            {
                "site": s["site"],
                "reported_score": s["reported_score"],
                "reported_score_label": s["reported_score_label"],
                "source_view_url": s["source_view_url"],
                "source_ref": s["source_ref"],
                "sha256": s["source_sha256_verified"],
                "format_safe_as_stored": s["portal_range_0_1_safe_as_stored"],
            }
            for s in nine["focus_9_sites"]
        ],
        "current_focus9_uniqueness": focus_check,
        "historical_full_registry_status": run["registry_comparison"],
        "sources": "source_register.json",
        "limitations": [
            "Historical focus-site scores are user/owner-reported and not organizer-verified.",
            "The frozen holdout evaluation was not rerun in this audit.",
            "The full registry pre-placement surface comparison was recorded but not independently recomputed.",
            "No slot was selected and no live submission was authorized or performed.",
        ],
    }

    # Copy the canonical audit documents into the static site's data endpoint.
    (DOCS / "data").mkdir(parents=True, exist_ok=True)
    write(DOCS / "data" / "status_feed.json", json.dumps(status_feed, indent=2, allow_nan=False) + "\n")

    # Current focus-nine CSV keeps every historic score explicitly unverified and
    # separates it from raster/format/overlap diagnostics.
    audit_csv = io.StringIO(newline="")
    audit_writer = csv.writer(audit_csv)
    audit_writer.writerow([
        "audit_generated_utc", "site", "reported_value", "score_provenance",
        "organizer_receipt_present", "positive_pixels_in_footprint",
        "raw_tiff_format_safe_as_stored", "template_grid_match",
        "candidate_directed_overlap_within_3px_fraction", "source_view_url",
        "pinned_source_ref", "source_sha256",
    ])
    for s in nine["focus_9_sites"]:
        audit_writer.writerow([
            nine["generated_utc"], s["site"], f'{s["reported_score"]:.4f}',
            s["reported_score_label"], "false", s["positive_dots_in_footprint"],
            str(bool(s["portal_range_0_1_safe_as_stored"])).lower(),
            str(bool(s["raster_metadata"]["grid_matches_template"])).lower(),
            f'{s["candidate_dots_within_3px_of_peer_fraction"]:.8f}',
            s["source_view_url"], s["source_ref"], s["source_sha256_verified"],
        ])
    write(DOCS / "data" / "nine_site_audit.csv", audit_csv.getvalue())
    write(
        DOCS / "data" / "nine_site_summary_20261026.csv",
        "status,notice,replacement\n"
        'WITHDRAWN,"Legacy summary withdrawn: it mixed user/owner claims, holdout diagnostics, projections, and submission recommendations without sufficient provenance. See nine_site_audit.csv and nine_site_audit.json.",../data/nine_site_audit.csv\n',
    )
    for src, dst in [
        (ROOT / "evidence" / "nine_site_audit.json", DOCS / "data" / "nine_site_audit.json"),
        (ROOT / "evidence" / "focus9_submission_audit_20261027.json", DOCS / "data" / "focus9_submission_audit.json"),
        (ROOT / "evidence" / "validator_receipt.json", DOCS / "data" / "validator_receipt.json"),
        (ROOT / "evidence" / "run_card.json", DOCS / "data" / "run_card.json"),
        (ROOT / "registry" / "sources.json", DOCS / "data" / "source_register.json"),
        (ROOT / "registry" / "focus9_site_registry.json", DOCS / "data" / "focus9_site_registry.json"),
    ]:
        shutil.copyfile(src, dst)

    write(DOCS / "index.html", page("GEMS submission research portal", top_content, "index.html"))
    write(DOCS / "executive-summary.html", page("Executive summary", executive, "executive-summary.html"))
    write(DOCS / "research.html", page("Research, hypotheses & sources", research, "research.html"))
    write(DOCS / "irregularities.html", page("Audit trail & limitations", irregularities, "irregularities.html"))
    write(ROOT / "EXECUTIVE_SUMMARY.md", f"""# KANLERGEMSDOE2 — Executive summary

## Decision states

- **Format validation:** `{current_status['format_validation']}` — single-band float32 TIFF on the sample grid, finite and within `[0, 1]` over the full array.
- **Download:** `{current_status['download']}` — the unique TIFF and single-TIFF ZIP hashes match.
- **Selector eligibility:** `{current_status['selector_eligibility']}` — recorded research gates passed; the full-registry pre-placement surface check is recorded, not reproduced in this review.
- **Submission authorization:** `{current_status['submission_authorization']}` — no live slot selected; no upload performed.
- **Organizer receipt / live score:** none verified or available.

## Candidate

- File: `docs/downloads/{tif}`
- SHA-256: `{tif_sha}`
- Format audit: one band, `{format_info['dtype']}`, `{format_info['shape'][0]}×{format_info['shape'][1]}`, `{format_info['crs']}`, exact template transform, full-array `[0, 1]`, no NaN/Inf.
- Primary **HOLDOUT-DTI**: `{hr['pooled_dti']:.6f}` — {hr['label']}.
- Secondary **HOLDOUT-DTI**: `{sg['sgmc_prevalence_calibrated_dti']:.6f}` — {sg['label']}.
- Both values are frozen run-card results, not rerun in this audit and not live-score projections.
- Submission note ({run['note_length']}/140 characters): `{note}`

## Focus sites and score provenance

The historical values GEMSDOE24/25/27/28/30/31/32/33/36 are **USER/OWNER-REPORTED · UNVERIFIED**. No DrivenData receipt was verified. See [`evidence/nine_site_audit.json`](evidence/nine_site_audit.json) for the per-site raster/hash/format summary, source pins, and candidate comparisons.

The prior `R²=0.998523` inversion used to infer hidden-set size and zero true positives among pruned dots has been withdrawn as non-identifiable from the available score/count pairs.

## Current uniqueness evidence

Current final-dot comparisons were recomputed against the nine pinned focus-site TIFFs: max directed 3-pixel overlap `{focus_check['max_candidate_dots_within_3px_fraction']:.6f}` ({focus_check['max_overlap_site']}); max absolute final-raster Spearman `{abs(focus_check['max_abs_final_raster_spearman']):.6f}` ({focus_check['max_rho_site']}). The prior full-registry pre-placement surface result `{run['registry_comparison']['pre_placement_surface_max_abs_spearman']}` against `{run['registry_comparison']['unique_rasters_checked']}` rasters is recorded but not independently reproduced because the pre-placement array was not retained.

## Review and next steps

No new experiment was run; the HTCADS lane has used all three preregistered experiments. The four untested ideas in [`knowledge/02_untried_hypotheses_20261027.md`](knowledge/02_untried_hypotheses_20261027.md) are a research queue only, not a new preregistration or score projection. Official sources and what was actually checked are in [`registry/sources.json`](registry/sources.json). The static site is not a live leaderboard poll and requires a separate user-controlled live-slot decision before any submission.
""")
    write(ROOT / "README.md", f"""# KANLERGEMSDOE2 — evidence-first GEMS submission workflow

> **Maximize P(Win), without inventing evidence. Own the Outcome:** artifact safety, selector eligibility, and permission to submit are separate states.

This repository contains a unique HTCADS candidate GeoTIFF, frozen spatial-holdout evidence, an automated format/registry audit, and a static review portal. It does **not** contain an organizer score receipt for the historic focus-site values. No live slot was selected and no upload was performed in this review.

## Current status snapshot

| State | Result | Meaning |
|---|---|---|
| Format | **{current_status['format_validation']}** | Exact template grid, one float32 band, full-array values in `[0, 1]`, no NaN/Inf |
| Download | **{current_status['download']}** | Unique TIFF and single-TIFF ZIP hashes verified |
| Selector | **{current_status['selector_eligibility']}** | Frozen evidence gates passed; not a live slot selection |
| Submission | **{current_status['submission_authorization']}** | No slot selected; no upload made |
| Live score | **Not available** | No organizer receipt was fetched or generated |

**Candidate:** [`docs/downloads/{tif}`](docs/downloads/{tif})<br>
**ZIP:** [`docs/downloads/{zip_name}`](docs/downloads/{zip_name})<br>
**SHA-256:** `{tif_sha}`

**Submission name:** `{run['submission_name']}`<br>
**Note ({run['note_length']}/140):** `{note}`

## HOLDOUT-DTI evidence (not live scores)

- **Primary:** `{hr['pooled_dti']:.6f}` — {hr['label']}.
- **Secondary:** `{sg['sgmc_prevalence_calibrated_dti']:.6f}` — {sg['label']}.

Both are pre-existing frozen HTCADS run-card results; this review did not rerun model training or holdout evaluation. They are not projections of an organizer score.

## Historical focus-site values

All values below are **USER/OWNER-REPORTED · UNVERIFIED** and are not current organizer-confirmed standings. No DrivenData submission-page receipt is stored.

| Site | Reported value | Source record |
|---|---:|---|
""" + "\n".join(f"| {s['site']} | {s['reported_score']:.4f} USER/OWNER-REPORTED · UNVERIFIED | [Pinned owner mirror]({s['source_view_url']}) |" for s in sorted(nine['focus_9_sites'], key=lambda x:x['reported_score'], reverse=True)) + f"""

**Scientific note on GEMSDOE32's reported 0.2778:** the raster/hash and positive-pixel count can be verified; the score cannot be reconstructed from that file. The former three-point linear inversion was non-identifying and its hidden-set/zero-TP claims have been withdrawn. See the [audit and limitations](docs/irregularities.html).

## Reproduce and verify safely

```bash
python scripts/restore_data.py --group core
python scripts/audit_focus_sites.py
python scripts/validate_submission.py \\
  --tif docs/downloads/{tif} \\
  --run-card evidence/run_card.json \\
  --zip docs/downloads/{zip_name} \\
  --out evidence/validator_receipt.json
python scripts/evaluate_holdout.py docs/downloads/{tif} --out /tmp/candidate_holdout.json
```

The last command runs the canonical spatially blocked holdout evaluator on the named candidate; it does **not** train or implicitly launch MTR1. `python scripts/evaluate_holdout.py --verify-kg2` is a read-only compatibility check for archived KG2 files. Do not run any new experiment under the exhausted three-experiment cap.

Tests: `python -m pytest -q` (or `.venv/bin/pytest -q` in the prepared local environment).

## Sources, limitations, and review portal

- [Static review portal](docs/index.html) · [Executive summary](docs/executive-summary.html) · [Research and source links](docs/research.html) · [Audit and limitations](docs/irregularities.html)
- [Tracked per-site audit](evidence/nine_site_audit.json) · [Pinned-raster audit receipt](evidence/focus9_submission_audit_20261027.json) · [Focus-nine CSV](docs/data/nine_site_audit.csv) · [Current status JSON](docs/data/status_feed.json)
- [Official-source register](registry/sources.json) · [Untested hypotheses](knowledge/02_untried_hypotheses_20261027.md)

Competition data and several external layers were restored from owner-controlled GitHub mirrors. SHA-256 pins demonstrate byte integrity against the pinned mirror, not official-host authenticity. Direct official-host source data, current DrivenData standings, and submission receipts were not available to this review. See [`registry/sources.json`](registry/sources.json) for exact verification scope and links.

### PARALLEL-RUN PROTOCOL safeguards

- Keep the unique single-band TIFF on the exact competition grid and values in `[0,1]`.
- Keep format-safe/downloadable, selector-eligible, and authorized-to-submit as separate statuses.
- Before any future test, use spatially blocked whole-segment holdouts and visible-fault-only feature derivation; enforce the 0.90 correlation/AUC and 70% 3-pixel overlap limits.
- Label every model-performance metric `HOLDOUT-DTI` with evaluator, withheld-positive count, and confidence interval, or `ORGANIZER-CONFIRMED` only when copied from an organizer-controlled receipt; label diagnostics as format, registry, or provenance audits.
- Never present or publish a live-score projection. Never select or spend a live slot automatically.
- Read the complete standing project brief and parallel-run protocol in [`PROMPT.md`](PROMPT.md).
""")

    # Root GitHub Pages entry point delegates to the audited docs portal.
    write(ROOT / "index.html", """<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><meta http-equiv=\"refresh\" content=\"0; url=docs/index.html\"><title>KANLERGEMSDOE2 audit portal</title></head><body><p><a href=\"docs/index.html\">Open the GEMS evidence-first submission portal</a></p></body></html>\n""")
    print("[build_site] Wrote provenance-first static site, status feed, executive summary, and README.")


if __name__ == "__main__":
    build()
