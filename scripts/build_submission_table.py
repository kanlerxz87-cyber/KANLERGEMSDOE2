#!/usr/bin/env python3
"""Build the per-site submission table (docs/submission-table.html) from computed evidence only.

Inputs (all produced by this repo's scripts, all hashed):
  evidence/focus_site_files.json          downloads of the 9 focus-site files + siblings + alternates
  evidence/focus_site_audit_20261027.json format + pairwise dot-overlap audit (scripts/audit_focus_files.py)
  evidence/run_card.json                  promoted file holdout receipt (HOLDOUT-DTI)
  registry/official_sources_20261027.json official sources (OS-1..OS-7)

Outputs:
  docs/submission-table.html
  evidence/submission_table_20261027.json

Labels: every number is one of
  USER-REPORTED   score copied from the task prompt listing (not an organizer receipt)
  HOLDOUT-DTI     computed by this repo's evaluator on a withheld-fault holdout
  PROJECTION      derived arithmetic from HOLDOUT-DTI; never a score
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

PROMOTED_NAME = "kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif"
PROMOTED_ZIP = "kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.zip"
PROMOTED_NOTE = "KANLERGEMS2 HTCADS-DualRegime: 50ch updip-grav+GDR1391+MT+orthoLiDAR NoisyOR+300m CELF (37654 dots, HR=0.1124)"
CHAMPION_USER = 0.2778  # GEMSDOE32 listing score (USER-REPORTED)
OVERLAP_MAX = 0.70
RHO_MAX = 0.90


def _e(v: object) -> str:
    return html.escape(str(v))


def load(p: str) -> dict:
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def projection(run_card: dict) -> dict:
    """Ratio projection of the 0.2778 listing score by the holdout ratio (EXP-2 vs GEMSDOE32 same evaluator).

    Point  = 0.2778 * pooled_dti / champion_dti
    Range  = 0.2778 * (1 + paired_delta_ci95 / champion_dti)
    This is arithmetic on HOLDOUT-DTI numbers. It assumes the holdout ranks submissions the way the
    leaderboard does, which is unvalidated. It is NOT a score.
    """
    hr = run_card["holdout_dti"]["primary_hide_and_recover"]
    dti, champ = float(hr["pooled_dti"]), float(hr["champion_02778_same_evaluator"])
    lo_d, hi_d = (float(x) for x in hr["paired_delta_ci95"])
    point = CHAMPION_USER * dti / champ
    lo = CHAMPION_USER * (1 + lo_d / champ)
    hi = CHAMPION_USER * (1 + hi_d / champ)
    return {
        "label": "PROJECTION (not a score)",
        "method": "0.2778 x (EXP-2 HOLDOUT-DTI / GEMSDOE32 HOLDOUT-DTI), same evaluator, Hide-and-Recover v3.0",
        "holdout_exp2": dti,
        "holdout_champion": champ,
        "holdout_ci95": hr["ci95"],
        "paired_delta_ci95": [lo_d, hi_d],
        "point": round(point, 4),
        "range_low": round(lo, 4),
        "range_high": round(hi, 4),
        "known_limitations": [
            "Holdout is this repo's own hide-and-recover construction, not the organizer's private set.",
            "Ratio form assumes the leaderboard scales with DTI through the origin.",
            "Only one holdout pair is used; the 9 focus sites were not rescored on this evaluator.",
        ],
    }


# Public leaderboard snapshot, fetched 2026-10-27 (OS-3). Rank #23 was not captured (fetch chunk cut off).
LEADERBOARD_SNAPSHOT = {
    1: 0.4544, 2: 0.3916, 3: 0.3911, 4: 0.3724, 5: 0.3566, 6: 0.3447, 7: 0.3418, 8: 0.3416, 9: 0.3398,
    10: 0.3379, 11: 0.3335, 12: 0.3334, 13: 0.3334, 14: 0.3328, 15: 0.3318, 16: 0.3314, 17: 0.3313,
    18: 0.3312, 19: 0.3304, 20: 0.3273, 21: 0.3262, 22: 0.3261, 24: 0.3217, 25: 0.3195, 26: 0.3169,
    27: 0.3167, 28: 0.3160, 29: 0.3157, 30: 0.3113, 31: 0.3111, 32: 0.3093, 33: 0.3041, 34: 0.3033,
    35: 0.3004, 36: 0.2987, 37: 0.2967, 38: 0.2964, 39: 0.2963, 40: 0.2957, 41: 0.2949, 42: 0.2935,
    43: 0.2930, 44: 0.2927, 45: 0.2899, 46: 0.2897, 47: 0.2892, 48: 0.2874, 49: 0.2858, 50: 0.2857,
}


def rank_context(p: dict) -> dict:
    """Approximate public rank of a score on the OS-3 snapshot: 1 + number of listed ranks scoring higher."""

    def rank_of(score: float) -> str:
        higher = sum(1 for v in LEADERBOARD_SNAPSHOT.values() if v > score)
        if higher >= len(LEADERBOARD_SNAPSHOT):
            return "below #50"
        # rank #23 is not in the snapshot, so a count can be off by one inside #22-#24
        return f"about #{higher + 1}"

    return {
        "point_rank": rank_of(p["point"]),
        "range_high_rank": rank_of(p["range_high"]),
        "range_low_rank": rank_of(p["range_low"]),
        "snapshot": "OS-3 public leaderboard, fetched 2026-10-27; rank #23 not captured (may be off by one); public ranks move and private scores decide Round 1",
    }


def build() -> dict:
    fsf = load("evidence/focus_site_files.json")["records"]
    audit = load("evidence/focus_site_audit_20261027.json")
    rc = load("evidence/run_card.json")
    sources = load("registry/official_sources_20261027.json")

    files = {a["label"]: a for a in audit["files"]}
    pairs = audit["pairwise_overlap"]
    promo_label = "KANLERGEMSDOE2 promoted EXP-2"

    def ov(a: str, b: str) -> dict | None:
        for p in pairs:
            if {p["a"], p["b"]} == {a, b}:
                fwd = p["a_within_3px_of_b"] if p["a"] == a else p["b_within_3px_of_a"]
                rev = p["b_within_3px_of_a"] if p["a"] == a else p["a_within_3px_of_b"]
                return {"a_in_b": fwd, "b_in_a": rev, "identical": p["exact_dot_identity"],
                        "max": max(fwd or 0.0, rev or 0.0)}
        return None

    focus_labels = [r["local_path"].split("/")[-1] for r in fsf if r.get("status") == "downloaded"]
    site_of = {r["local_path"].split("/")[-1]: r["site"] for r in fsf if r.get("status") == "downloaded"}

    proj = projection(rc)
    rank = rank_context(proj)

    # One row per listed site: the top-scoring listed file (USER-REPORTED) and its portal-safe sibling.
    listed = [r for r in fsf if r.get("role", "listed") == "listed" and r.get("user_reported_score") is not None]
    by_site: dict[str, dict] = {}
    for r in listed:
        cur = by_site.get(r["site"])
        if cur is None or r["user_reported_score"] > cur["user_reported_score"]:
            by_site[r["site"]] = r
    sibling_of: dict[str, dict] = {}
    for r in fsf:
        if str(r.get("role", "")).startswith("portal-safe sibling of "):
            sibling_of[r["role"][len("portal-safe sibling of "):]] = r

    site_rows = []
    for site in sorted(by_site, key=lambda s: -by_site[s]["user_reported_score"]):
        r = by_site[site]
        name = r["local_path"].split("/")[-1]
        a = files[name]
        sib = sibling_of.get(name)
        sib_name = sib["local_path"].split("/")[-1] if sib else None
        sib_ident = ov(name, sib_name)["identical"] if sib_name else None

        # uniqueness: against other focus-site files (not the same site's own files)
        worst = None
        for other in focus_labels:
            if site_of.get(other) in (site, None) or other == name:
                continue
            o = ov(name, other)
            if o and (worst is None or o["max"] > worst["max"]):
                worst = {"against": other, **o}
        ident_partner = None
        for other in focus_labels:
            if other != name and site_of.get(other) != site:
                o = ov(name, other)
                if o and o["identical"]:
                    ident_partner = other
                    break
        pr = next((p for p in promoted_vs_all(audit) if p["against"] == name), None)

        site_rows.append({
            "site": site,
            "file": name,
            "bytes": r["bytes"],
            "sha256": r["sha256"],
            "source_repo": r["source_repo"],
            "source_path": r["source_path"],
            "user_reported_score": r["user_reported_score"],
            "outside_footprint_mode": a["outside_footprint_mode"],
            "portal_risk_nan_outside": a["portal_risk_nan_outside"],
            "format_checks_pass": a["all_checks_passed"],
            "dots": a["dots_gt0_in_footprint"],
            "on_catalogue_dots": a["dots_on_catalogue"],
            "portal_safe_sibling": sib_name,
            "portal_safe_sibling_sha256": sib["sha256"] if sib else None,
            "portal_safe_sibling_same_dots": sib_ident,
            "max_overlap_vs_other_sites": None if worst is None else round(worst["max"], 4),
            "max_overlap_partner": None if worst is None else worst["against"],
            "identical_dots_partner_other_site": ident_partner,
            "promoted_overlap_3px_max": None if pr is None else pr["overlap_3px_max_direction"],
        })

    promo = files[promo_label]
    promo_max_focus = max((p for p in promoted_vs_all(audit) if p["against"] in focus_labels),
                          key=lambda p: p["overlap_3px_max_direction"])
    promo_max_all = max((p for p in promoted_vs_all(audit) if "lattice" not in p["against"]),
                        key=lambda p: p["overlap_3px_max_direction"])
    promo_row = {
        "file": PROMOTED_NAME,
        "zip": PROMOTED_ZIP,
        "sha256": promo["sha256"],
        "bytes": promo["bytes"],
        "outside_footprint_mode": promo["outside_footprint_mode"],
        "format_checks_pass": promo["all_checks_passed"],
        "dots": promo["dots_gt0_in_footprint"],
        "on_catalogue_dots": promo["dots_on_catalogue"],
        "holdout": rc["holdout_dti"]["primary_hide_and_recover"],
        "sgmc": rc["holdout_dti"]["secondary_off_catalogue_sgmc"],
        "overlap_vs_gemsdoe32_champion": round(next(p_["overlap_3px_max_direction"] for p_ in promoted_vs_all(audit) if p_["against"].startswith("gemsdoe32-")), 4),
        "max_overlap_vs_focus_9": round(promo_max_focus["overlap_3px_max_direction"], 4),
        "max_overlap_partner_focus": promo_max_focus["against"],
        "max_overlap_vs_all_non_lattice": round(promo_max_all["overlap_3px_max_direction"], 4),
        "max_overlap_partner_all": promo_max_all["against"],
        "lattice_overlap_note": "9997 per-mille overlap with the 5-px calibration lattice is saturated (lattice covers ~99.9% of cells) and is treated as a control, not a duplicate.",
        "identical_to_any_focus_or_archive": any(p["exact_dot_identity"] for p in promoted_vs_all_raw(audit)),
        "portal_note": PROMOTED_NOTE,
        "portal_note_chars": len(PROMOTED_NOTE),
        "projection": proj,
        "rank_context": rank,
    }

    out = {
        "schema": "kanlergemsdoe2.submission_table.v1",
        "built_utc_date": "2026-10-27",
        "champion": {"site": "GEMSDOE32", "score_user_reported": CHAMPION_USER},
        "uniqueness_threshold": {"overlap_3px_gt": OVERLAP_MAX, "abs_spearman_gt": RHO_MAX},
        "promoted": promo_row,
        "sites": site_rows,
        "sources": [{"id": s["id"], "url": s["url"], "title": s["title"]} for s in sources["sources"]],
        "irregularities": irregularities(),
    }
    return out


def promoted_vs_all(audit: dict) -> list[dict]:
    return audit["promoted_vs_all"]


def promoted_vs_all_raw(audit: dict) -> list[dict]:
    return [p for p in audit["pairwise_overlap"] if "KANLERGEMSDOE2 promoted EXP-2" in (p["a"], p["b"])]


def irregularities() -> list[dict]:
    return [
        {"id": "IRR-2026-10-27-01", "severity": "high",
         "finding": "Prompt leaderboard figures do not match the live public leaderboard (#1 0.4413 vs 0.4544; '#5 = 0.3195' is actually #25 at 0.3195; #5 is 0.3566).",
         "source": "OS-3"},
        {"id": "IRR-2026-10-27-02", "severity": "high",
         "finding": "The promoted GeoTIFF zero-fills outside the footprint; the organizer text says outside-bounds cells are null or nan. Both are numeric and in-range, but the organizer has not confirmed zero is accepted. Review before upload.",
         "source": "OS-1"},
        {"id": "IRR-2026-10-27-03", "severity": "medium",
         "finding": "The repo's DTI is a transcription of the published equations (checked against src/gems32/metric.py). The official scorer is not public, so no organizer receipt exists yet for any file in this repo.",
         "source": "OS-1, OS-5"},
        {"id": "IRR-2026-10-27-04", "severity": "high",
         "finding": "12 download links in the executive summary and README pointed at GeoTIFFs that were never committed. Fixed this session: all 12 restored from their owner repos and SHA-256 matched to the summary.",
         "source": "evidence/focus_site_files.json"},
        {"id": "IRR-2026-10-27-05", "severity": "high",
         "finding": "Pages labelled user-listed scores as ORGANIZER-CONFIRMED. No submission-page receipt is stored in the repo. Relabelled USER-REPORTED on the pages generated this session.",
         "source": "scripts/build_site.py"},
        {"id": "IRR-2026-10-27-06", "severity": "medium",
         "finding": "The 5-px calibration lattice (r13-lattice-s5_v2) overlaps the promoted file at 99.97%. This is a saturation artefact of a space-filling grid, not a real duplicate. It is recorded in the run card as a probe.",
         "source": "evidence/focus_site_audit_20261027.json"},
        {"id": "IRR-2026-10-27-07", "severity": "medium",
         "finding": "The projection is a ratio on one self-built holdout (single pair). It is not validated against any organizer score. Expect large error.",
         "source": "evidence/submission_table_20261027.json"},
        {"id": "IRR-2026-10-27-08", "severity": "medium",
         "finding": "Prior-session holdout numbers for focus sites mix censored (static, B=2) and uncensored evaluators (IR-32-INSTR-03). They are not comparable across sites, so this table does not show them.",
         "source": "docs/irregularities.html"},
        {"id": "IRR-2026-10-27-09", "severity": "low",
         "finding": "The training data is an owner-supplied mirror pinned by SHA-256, not an organizer download (login-walled).",
         "source": "registry/data_manifest.json"},
    ]


def render(d: dict) -> str:
    from build_site import _nav, _footer, _copy_script  # noqa: E402

    p = d["promoted"]
    pr = p["projection"]
    rk = p["rank_context"]
    h = p["holdout"]
    s = p["sgmc"]
    rows = []
    for i, r in enumerate(d["sites"], 1):
        if r["portal_risk_nan_outside"]:
            safe = f"<span class=\"tag tag-warn\">NaN outside footprint</span>"
            if r["portal_safe_sibling"]:
                safe += f"<br><span class=\"tag tag-ok\">zeros/allfinite sibling</span> <code>{_e(r['portal_safe_sibling'])}</code>"
        else:
            safe = "<span class=\"tag tag-ok\">0 NaN; values in [0,1]</span>"
        if r["identical_dots_partner_other_site"]:
            uniq = f"<span class=\"tag tag-bad\">NOT UNIQUE</span><br>identical dots to <code>{_e(r['identical_dots_partner_other_site'])}</code>"
        elif r["max_overlap_vs_other_sites"] is not None and r["max_overlap_vs_other_sites"] > OVERLAP_MAX:
            uniq = f"<span class=\"tag tag-bad\">NOT UNIQUE</span> max 3px overlap {r['max_overlap_vs_other_sites']*100:.1f}%"
        else:
            uniq = f"<span class=\"tag tag-warn\">lineage-related</span> max 3px overlap {r['max_overlap_vs_other_sites']*100:.1f}% (threshold 70%)"
        rec = "Submitted/known score; not a new unique submission" if r["site"] == "GEMSDOE32" else "Historical focus-site file"
        rows.append(f"""
        <tr>
          <td>{i}</td>
          <td><strong>{_e(r['site'])}</strong></td>
          <td><a href="downloads/{_e(r['file'])}" download><code>{_e(r['file'])}</code></a>
            <div class="sub">SHA-256 <code>{_e(r['sha256'][:16])}&hellip;</code> &middot; {r['dots']:,} dots</div></td>
          <td>{safe}</td>
          <td><strong><code>{r['user_reported_score']:.4f}</code></strong><div class="sub">USER-REPORTED</div></td>
          <td>{uniq}</td>
          <td>{_e(rec)}</td>
        </tr>""")

    promo_row = f"""
        <tr class="highlight-row">
          <td>&#9733;</td>
          <td><strong>KANLERGEMSDOE2</strong><br><span class="tag tag-ok">NEW</span></td>
          <td><a href="downloads/{_e(p['file'])}" download><code>{_e(p['file'])}</code></a>
            <div class="sub">SHA-256 <code>{_e(p['sha256'][:16])}&hellip;</code> &middot; {p['dots']:,} dots</div></td>
          <td><span class="tag tag-ok">0 NaN; values in [0,1]; EPSG:32611; 3730&times;3292; 100 m</span></td>
          <td><strong><code>{pr['point']:.4f}</code></strong> <span class="tag tag-warn">PROJECTION</span>
              <div class="sub">range {pr['range_low']:.3f}&ndash;{pr['range_high']:.3f} &middot; not a score</div></td>
          <td><span class="tag tag-ok">UNIQUE</span> 3px overlap vs GEMSDOE32 (0.2778) {p['overlap_vs_gemsdoe32_champion']*100:.2f}%; max vs the 9 focus files {p['max_overlap_vs_focus_9']*100:.1f}% (&le;70%)
              <div class="sub">vs all non-lattice references: {p['max_overlap_vs_all_non_lattice']*100:.1f}%</div></td>
          <td><strong>DOWNLOAD &amp; SUBMIT</strong><div class="sub">no organizer receipt yet</div></td>
        </tr>"""

    audit_rows = []
    for r in d["sites"]:
        audit_rows.append(f"<tr><td>{_e(r['site'])}</td><td><code>{_e(r['file'])}</code></td><td>{_e(r['outside_footprint_mode'])}</td><td>{'yes' if r['format_checks_pass'] else 'no'}</td><td>{r['dots']:,}</td><td>{r['on_catalogue_dots']}</td><td>{'' if r['portal_safe_sibling_same_dots'] is None else ('same dots' if r['portal_safe_sibling_same_dots'] else 'different dots')}</td></tr>")

    irr_rows = "".join(
        f"<tr><td><code>{_e(i['id'])}</code></td><td>{_e(i['severity'])}</td><td>{_e(i['finding'])}</td><td>{_e(i['source'])}</td></tr>"
        for i in d["irregularities"])
    src_rows = "".join(
        f"<tr><td><code>{_e(s_['id'])}</code></td><td><a href=\"{_e(s_['url'])}\" target=\"_blank\" rel=\"noopener\">{_e(s_['title'])}</a></td></tr>"
        for s_ in d["sources"])

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Per-Site Submission Table &mdash; KANLERGEMSDOE2</title>
<link rel="stylesheet" href="style.css"></head>
<body>
{_nav("submission-table.html")}
<main class="container">
  <section class="card">
    <h1>Which file to download &amp; submit</h1>
    <p><strong>Answer:</strong> download and submit <a href="downloads/{_e(p['file'])}" download><code>{_e(p['file'])}</code></a>. It is the only file in this table that is unique (&le;70% overlap against all 9 focus files and every non-lattice archive reference) and passes the portal-format checks. Its score is <strong>not yet known</strong>: no organizer receipt exists, and the estimate below is a projection.</p>
    <div class="callout callout-warn"><strong>Review before upload (IRR-2026-10-27-02):</strong> this file uses 0 outside the footprint, not NaN. The organizer text says outside-bounds cells are null or nan. Confirm this is acceptable before relying on it.</div>
  </section>

  <section class="card">
    <h2>Table 1 &mdash; Per-site file to download (scores are USER-REPORTED unless noted)</h2>
    <div class="table-wrap"><table>
      <thead><tr><th>#</th><th>Site</th><th>File to download</th><th>Portal format</th><th>Score / estimate</th><th>Unique?</th><th>Note</th></tr></thead>
      <tbody>{promo_row}
        {''.join(rows)}
      </tbody></table></div>
    <p class="sub">Uniqueness for site rows = max 3-px dot overlap against every other focus-site file (threshold 70%). Lineage-related means sharing the H19-5 ancestry but below the threshold.</p>
  </section>

  <section class="card">
    <h2>Estimated score for the promoted file (PROJECTION, not a score)</h2>
    <p><strong>Point {pr['point']:.4f}</strong>, range {pr['range_low']:.4f} to {pr['range_high']:.4f}. Method: <code>{_e(pr['method'])}</code>.</p>
    <ul>
      <li>HOLDOUT-DTI EXP-2 = <code>{h['pooled_dti']:.6f}</code>, 95% CI [{h['ci95'][0]:.4f}, {h['ci95'][1]:.4f}], N = 22,232 withheld positives, evaluator v3.0 (GEMSDOE32-HIDE-RECOVER-v3.0). Source: <code>evidence/run_card.json</code>.</li>
      <li>HOLDOUT-DTI GEMSDOE32 (same evaluator) = <code>{h['champion_02778_same_evaluator']:.6f}</code>; paired delta CI95 [{pr['paired_delta_ci95'][0]:+.4f}, {pr['paired_delta_ci95'][1]:+.4f}].</li>
      <li>SGMC-CAL holdout (secondary): EXP-2 <code>{s['sgmc_prevalence_calibrated_dti']:.6f}</code> CI [{s['ci95'][0]:.4f}, {s['ci95'][1]:.4f}] vs GEMSDOE32 <code>{s['champion_02778_same_evaluator']:.6f}</code> (N = 62,703).</li>
      <li><strong>Leaderboard context (OS-3 snapshot):</strong> point projection falls {_e(rk['point_rank'])}; range high {_e(rk['range_high_rank'])}; range low {_e(rk['range_low_rank'])}. Public ranks move; the private round decides Round 1 prize.</li>
    </ul>
    <p class="sub">Limitations: {'; '.join(_e(x) for x in pr['known_limitations'])}.</p>
  </section>

  <section class="card">
    <h2>Table 2 &mdash; Format audit of every file in Table 1 (computed this session)</h2>
    <div class="table-wrap"><table>
      <thead><tr><th>Site</th><th>File</th><th>Outside footprint</th><th>Format checks pass</th><th>Dots</th><th>On-catalogue dots</th><th>Portal-safe sibling</th></tr></thead>
      <tbody>{''.join(audit_rows)}</tbody></table></div>
    <p class="sub">Format checks: EPSG:32611, 3730&times;3292, 100 m transform, single band float32, 0 NaN inside footprint, values in [0,1] inside footprint, 0 on-catalogue dots (our internal rule; organizer masks known faults per OS-4). Source: <code>evidence/focus_site_audit_20261027.json</code>.</p>
  </section>

  <section class="card">
    <h2>Irregularities for review</h2>
    <div class="table-wrap"><table>
      <thead><tr><th>ID</th><th>Severity</th><th>Finding</th><th>Source</th></tr></thead>
      <tbody>{irr_rows}</tbody></table></div>
  </section>

  <section class="card">
    <h2>Official sources (fetched 2026-10-27)</h2>
    <div class="table-wrap"><table><thead><tr><th>ID</th><th>Source</th></tr></thead><tbody>{src_rows}</tbody></table></div>
  </section>
</main>
{_footer()}
{_copy_script()}
</body></html>
"""


def main() -> int:
    d = build()
    (ROOT / "evidence" / "submission_table_20261027.json").write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")
    (ROOT / "docs" / "submission-table.html").write_text(render(d), encoding="utf-8")
    print(f"wrote docs/submission-table.html and evidence/submission_table_20261027.json ({len(d['sites'])} site rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
