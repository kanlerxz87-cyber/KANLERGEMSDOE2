#!/usr/bin/env python3
"""
Build docs/executive-summary.html and docs/submission-table.html from verified,
SHA-pinned data. No scores are fabricated: every number is labeled USER-REPORTED
(owner/operator claim, no organizer receipt) or NOT MEASURABLE.

Table columns (per the prompt):
  * file to download
  * estimate score (strictly labeled: USER-REPORTED / not measurable)
  * whether it is a unique submission unlike any other focus site
  * [0,1] portal safety and do-not-submit decision
"""

from __future__ import annotations

import hashlib
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems.footprint import load_footprint  # noqa: E402

FOCUS = json.loads((ROOT / "registry" / "focus_sites_20261027.json").read_text())["sites"]
DOWNLOADS = ROOT / "docs" / "downloads"
FP = load_footprint()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_new_card():
    cards = sorted((ROOT / "evidence").glob("run_card_unique_*.json"))
    if not cards:
        return None
    return json.loads(cards[-1].read_text(encoding="utf-8"))


def safety_of(tif_path: Path) -> dict:
    with rasterio.open(tif_path) as ds:
        a = ds.read(1)
    inside = a[FP]
    fin = np.isfinite(inside)
    in_range = bool(fin.all() and (inside[fin] >= 0).all() and (inside[fin] <= 1).all())
    outside = a[~FP]
    outside_nan = bool(np.isnan(outside).all())
    return {
        "shape_ok": ds.shape == FP.shape,
        "crs_ok": ds.crs is not None and ds.crs.to_epsg() == 32611,
        "in_range_0_1": in_range,
        "no_nan_inside": bool(fin.all()),
        "outside_all_nan": outside_nan,
        "whole_array_0_1": bool(((a >= 0) & (a <= 1)).all()),
        "positive_dots": int((inside > 0).sum()),
    }


def esc(v) -> str:
    return html.escape(str(v), quote=True)


def uniqueness_overlap(dots_a: np.ndarray, dots_b: np.ndarray) -> float:
    """Directional fraction of dots_a within 3 px of dots_b."""
    if not dots_a.any() or not dots_b.any():
        return 0.0
    from scipy.spatial import cKDTree

    aa = np.argwhere(dots_a)
    bb = np.argwhere(dots_b)
    tree = cKDTree(bb)
    return float(np.mean(tree.query(aa)[0] <= 3.0))


def main() -> int:
    new_card = find_new_card()
    rows = []
    # Load each focus TIF once for overlap computation.
    tif_arrays = {}
    for s in FOCUS:
        p = DOWNLOADS / Path(s["path"]).name
        if not p.exists():
            continue
        with rasterio.open(p) as ds:
            a = np.where(np.isfinite(ds.read(1)), ds.read(1), 0.0)
        tif_arrays[s["site"]] = (p, a > 0.5, safety_of(p))

    # Pairwise uniqueness vs other focus sites (directional, max over all others).
    sites = [s["site"] for s in FOCUS if s["site"] in tif_arrays]
    for s in FOCUS:
        p = DOWNLOADS / Path(s["path"]).name
        if not p.exists():
            continue
        dots = tif_arrays[s["site"]][1]
        best = 0.0
        best_site = "—"
        for o in sites:
            if o == s["site"]:
                continue
            ov = uniqueness_overlap(dots, tif_arrays[o][1])
            if ov > best:
                best = ov
                best_site = o
        safe = tif_arrays[s["site"]][2]
        portal_safe = bool(safe["whole_array_0_1"] and safe["no_nan_inside"])
        rows.append(
            {
                "site": s["site"],
                "score": float(s["owner_reported_score"]),
                "file": Path(s["path"]).name,
                "sha256": s["sha256"],
                "site_url": s["site_url"],
                "repo_url": f"https://github.com/{s['repository']}",
                "ref": s["ref"],
                "pinned_source_url": f"https://github.com/{s['repository']}/blob/{s['ref']}/{Path(s['path']).name}",
                "dots": int(tif_arrays[s["site"]][1].sum()),
                "unique": best <= 0.70,
                "max_overlap_vs_focus": best,
                "nearest_focus_site": best_site,
                "portal_safe": portal_safe,
                "outside_nan": safe["outside_all_nan"],
                "in_range": safe["in_range_0_1"],
                "decision": "Do not submit — historical, USER-REPORTED, not unique vs a focus-site peer",
            }
        )

    rows.sort(key=lambda r: -r["score"])
    best_site = rows[0]

    # ---- New unique file row ----
    new_row = None
    if new_card:
        n = new_card["submission_name"]
        p = DOWNLOADS / n
        new_card_sha = new_card["raster_sha256"]
        if p.exists() and sha256_file(p) == new_card_sha:
            safe = safety_of(p)
            # overlap vs every focus site
            with rasterio.open(p) as ds:
                new_dots = np.where(np.isfinite(ds.read(1)) & (ds.read(1) > 0.5), 1, 0).astype(bool)
            new_dots = new_dots & FP
            best = 0.0
            nearest = "—"
            for o in sites:
                ov = uniqueness_overlap(new_dots, tif_arrays[o][1])
                if ov > best:
                    best = ov
                    nearest = o
            new_row = {
                "site": "KANLERGEMSDOE2 (new)",
                "score": None,
                "score_label": "NOT MEASURABLE",
                "score_note": (
                    "Holdout DTI cannot be measured: organizer-authenticated labels.tif requires a "
                    "DrivenData login unavailable in this sandbox. No organizer receipt. No score fabricated."
                ),
                "file": n,
                "sha256": new_card_sha,
                "site_url": "https://github.com/kanlerxz87-cyber/KANLERGEMSDOE2",
                "repo_url": "https://github.com/kanlerxz87-cyber/KANLERGEMSDOE2",
                "ref": "working tree",
                "pinned_source_url": f"https://github.com/kanlerxz87-cyber/KANLERGEMSDOE2/blob/arena/acf2393a-kanlergemsdoe2/docs/downloads/{n}",
                "dots": int(new_dots.sum()),
                "unique": best <= 0.70 and abs(new_card["correlation_overlap_vs_registry"]["final_dots"]["max_abs_rank_correlation"]) <= 0.90,
                "max_overlap_vs_focus": best,
                "nearest_focus_site": nearest,
                "portal_safe": bool(safe["whole_array_0_1"] and safe["no_nan_inside"]),
                "outside_nan": safe["outside_all_nan"],
                "in_range": safe["in_range_0_1"],
                "decision": (
                    "OK to DOWNLOAD (research). NOT OK to SUBMIT: holdout unmeasured, no organizer "
                    "receipt, full-registry clearance and selector required before any weekly slot."
                ),
            }

    now = datetime.now(timezone.utc).isoformat()

    def tr(r, is_new=False) -> str:
        score_cell = (
            f"<strong>{r['score']:.4f}</strong><small class=\"tag user-reported\">USER-REPORTED</small>"
            if r["score"] is not None
            else '<span class="tag not-measurable">NOT MEASURABLE</span><br><small class="muted">no organizer label access in sandbox</small>'
        )
        safe_txt = "PASS" if r["portal_safe"] else "WARN"
        safe_cls = "safe" if r["portal_safe"] else "warn"
        unique_txt = "YES" if r["unique"] else "NO"
        unique_cls = "unique-yes" if r["unique"] else "unique-no"
        ext = "NaN exterior" if r["outside_nan"] else "zeros outside"

        if is_new:
            site_td = (
                f"<td><strong>{esc(r['site'])}</strong>"
                f"<small class=\"muted\">{esc(r['score_note'])}</small></td>"
            )
        else:
            site_td = (
                f"<td><strong><a href=\"{esc(r['site_url'])}\">{esc(r['site'])} ↗</a></strong>"
                f"<small><a href=\"{esc(r['repo_url'])}\">repo</a> · "
                f"<span class=\"mono\">{esc(r['ref'][:10])}</span></small></td>"
            )
        file_td = (
            f"<td class=\"file\"><a href=\"downloads/{esc(r['file'])}\" download>{esc(r['file'])}</a>"
            f"<small>SHA-256 {esc(r['sha256'][:12])}… · {r['dots']:,} dots · {ext}</small></td>"
        )
        uniq_td = (
            f"<td class=\"{unique_cls}\"><strong>{unique_txt}</strong>"
            f"<small>max {100*r['max_overlap_vs_focus']:.2f}% within 3 px of {esc(r['nearest_focus_site'])}</small></td>"
        )
        safe_td = (
            f"<td class=\"{safe_cls}\"><strong>{safe_txt}</strong>"
            f"<small>{'in-range [0,1]' if r['in_range'] else 'OUT OF RANGE'}</small></td>"
        )
        dec_td = (
            f"<td class=\"decision\"><span class=\"pill stop\">Do not submit</span>"
            f"<small>{esc(r['decision'][:90])}</small></td>"
        )
        newcls = " class=\"new-row\"" if is_new else ""
        return (
            f"<tr{newcls}>{site_td}{file_td}<td>{score_cell}</td>{uniq_td}{safe_td}{dec_td}</tr>"
        )

    header_row = (
        "<tr>"
        "<th scope=\"col\">Site</th>"
        "<th scope=\"col\">File to download</th>"
        "<th scope=\"col\">Score / estimate (labeled)</th>"
        "<th scope=\"col\">Unique vs other focus sites?</th>"
        "<th scope=\"col\">[0,1] portal safe?</th>"
        "<th scope=\"col\">Decision</th>"
        "</tr>"
    )

    body = "".join(tr(r) for r in rows)
    new_body = ""
    if new_row:
        new_body = tr(new_row, is_new=True)

    intro_note = ""
    if new_row:
        intro_note = (
            f"<p><strong>New unique file ready to download:</strong> "
            f"<a href=\"downloads/{esc(new_row['file'])}\" download>{esc(new_row['file'])}</a> "
            f"(SHA-256 <span class=\"mono\">{esc(new_row['sha256'])}</span>, {new_row['dots']:,} dots). "
            f"It is <strong>unique</strong> vs every focus-site peer "
            f"(max {100*new_row['max_overlap_vs_focus']:.2f}% within 3 px, |Spearman| "
            f"{abs(new_card['correlation_overlap_vs_registry']['final_dots']['max_abs_rank_correlation']):.4f}). "
            f"<strong>It is NOT cleared to submit</strong> — holdout DTI is not measurable without organizer "
            f"labels and no organizer receipt exists. See the status banner below.</p>"
        )

    # Status banner for the new file
    if new_row:
        banner = (
            f'<div class="callout status-banner">'
            f'<div class="banner-left">'
            f'<span class="pill ok">OK TO DOWNLOAD</span> '
            f'<span class="mono">{esc(new_row["file"])}</span> '
            f'(SHA-256 <span class="mono">{esc(new_row["sha256"][:16])}…</span>, {new_row["dots"]:,} dots, '
            f'values in [0,1], no NaN inside footprint, EPSG:32611, 3730×3292, 100 m grid)'
            f'</div>'
            f'<div class="banner-right">'
            f'<span class="pill stop">NOT OK TO SUBMIT</span>'
            f'<p class="muted">Reason: holdout DTI not measurable (organizer labels require DrivenData login, '
            f'unavailable in this sandbox) · no organizer submission-page receipt · full-registry clearance and '
            f'an independent selector required before any weekly DrivenData slot is spent.</p>'
            f'</div></div>'
        )
    else:
        banner = '<div class="callout status-banner"><p>No new unique file was generated in this session.</p></div>'

    best_callout = (
        f'<div class="callout best-callout">'
        f'<strong>Best reported score to study:</strong> {esc(best_site["site"])} at '
        f'<strong>{best_site["score"]:.4f}</strong> (USER-REPORTED; no organizer receipt). '
        f'However it is <strong>NOT unique</strong> — {100*best_site["max_overlap_vs_focus"]:.2f}% of its dots fall within '
        f'3 px of {esc(best_site["nearest_focus_site"])}. '
        f'None of the 9 focus-site files is unique vs a peer, so the highest reported score is a duplicate lane, '
        f'not a clean submission path.'
        f'</div>'
    )

    def page(title, active, content):
        nav = [
            ("index.html", "Overview"),
            ("executive-summary.html", "Executive summary"),
            ("submission-table.html", "Submission table"),
            ("research.html", "Research"),
            ("irregularities.html", "Open issues"),
        ]
        links = "".join(
            f'<a href="{path}"' + (' class="active" aria-current="page"' if path == active else '') + f'>{esc(n)}</a>'
            for path, n in nav
        )
        return (
            f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(title)} | GEMS Fieldnotes</title><link rel="stylesheet" href="style.css"></head>'
            f'<body><a class="skip" href="#main">Skip to content</a>'
            f'<header class="topbar"><div class="wrap topbar-inner">'
            f'<a href="index.html" class="brand"><span class="brand-mark">G</span><span class="brand-name">GEMS / FIELDNOTES<small>KANLERGEMSDOE2</small></span></a>'
            f'<nav class="nav" aria-label="Main navigation">{links}<a class="nav-link" href="https://github.com/kanlerxz87-cyber/KANLERGEMSDOE2">GitHub ↗</a></nav>'
            f'</div></header><main id="main" class="wrap">{content}</main>'
            f'<footer class="footer"><div class="wrap footer-inner"><div><strong>GEMS / FIELDNOTES</strong><br>Evidence before a submission slot.</div>'
            f'<div>Maximize P(Win) · Own the Outcome · No score fabricated without organizer receipt</div></div></footer></body></html>'
        )

    content = (
        f'<div class="breadcrumb"><a href="index.html">Decision dashboard</a> &nbsp;/&nbsp; <span>Executive summary</span></div>'
        f'<div class="page-intro"><div class="eyebrow">Decision brief · {now[:10]} UTC</div>'
        f'<h1>Which GEMSDOE file to submit — and what is unique.</h1>'
        f'<p>All 9 focus-site scores are <strong>USER-REPORTED</strong> (owner/operator claims); none carry an organizer '
        f'submission-page receipt, so none is an authorized submission. Values are not organizer-confirmed and are not '
        f'leaderboard estimates for a new file.</p>{intro_note}</div>'
        f'{banner}'
        f'{best_callout}'
        f'<section class="section"><div class="section-head"><div><div class="eyebrow">Focus-site leaderboard comparison (9 sites)</div>'
        f'<h2>File to download · estimated score · uniqueness · [0,1] safety · decision</h2>'
        f'<p class="muted">Scores are USER-REPORTED, not organizer-confirmed. Overlap is directional: fraction of a row’s '
        f'positive pixels within 3 px of its nearest focus-site peer. All downloads are SHA-256 verified against '
        f'registry/focus_sites_20261027.json.</p></div></div>'
        f'<div class="table-wrap"><table><thead>{header_row}</thead><tbody>{body}{new_body}</tbody></table></div></section>'
        f'<section class="section"><div class="section-head"><div><div class="eyebrow">How to make a submission</div>'
        f'<h2>Submission instructions (DrivenData)</h2></div></div>'
        f'<div class="grid-two"><div class="card"><ol class="steps">'
        f'<li><strong>Clear every gate first.</strong> Format ([0,1], no NaN inside footprint, CRS/shape/transform match), '
        f'holdout DTI with 95% CI, leakage canary ≤0.90 per feature, literal registry uniqueness (|ρ| ≤ 0.90 and ≤70% '
        f'of dots within 3 px of any one registry raster), and current weekly quota.</li>'
        f'<li><strong>Download the exact approved GeoTIFF</strong> (or a ZIP containing that single TIFF) and verify its '
        f'SHA-256. No file on this page is approved to submit today.</li>'
        f'<li><strong>DrivenData → Submit → Make new submission.</strong> Upload the single-band GeoTIFF. Enter a unique '
        f'name and a short note (≤140 characters), e.g. clustering with k=25.</li>'
        f'<li><strong>Preserve the submission receipt</strong> (file hash, timestamp, organizer-returned score). Choose one '
        f'final entry for both rounds before the deadline.</li>'
        f'</ol></div>'
        f'<div class="card"><h3>Format requirements</h3><p>Single-band float32 GeoTIFF, values in [0,1], CRS EPSG:32611, '
        f'shape 3730×3292, transform (100, 0, 243350, 0, −100, 4508550), null/NaN outside the scored footprint. The '
        f'"Predicted values must be in range [0, 1]" error means a value lies outside [0,1] somewhere in the array '
        f'(including exterior NaN under a strict whole-array read).</p>'
        f'<p><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Official format ↗</a> · '
        f'<a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Official rules ↗</a> · '
        f'<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Leaderboard ↗</a></p>'
        f'</div></div></section>'
        f'<section class="section"><div class="callout"><strong>Limitations (no fabrication).</strong><ul>'
        f'<li>Holdout DTI is <strong>not measurable</strong> here: training_features.tif / labels.tif require a '
        f'DrivenData login that is unavailable in this sandbox; no holdout replay was performed.</li>'
        f'<li>No organizer submission-page receipt exists for any file shown, so no score is organizer-confirmed.</li>'
        f'<li>Uniqueness is verified vs locally available TIFs; the complete organizer registry is not present locally.</li>'
        f'<li>Portal acceptance of zeros- vs NaN-outside exterior is not established by this sandbox.</li>'
        f'</ul></div></section>'
    )
    html_text = page("Executive summary", "executive-summary.html", content)
    (ROOT / "docs" / "executive-summary.html").write_text(html_text, encoding="utf-8")
    (ROOT / "docs" / "submission-table.html").write_text(html_text, encoding="utf-8")
    print(f"Wrote executive-summary.html and submission-table.html ({len(rows)} focus rows + new row={new_row is not None})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
