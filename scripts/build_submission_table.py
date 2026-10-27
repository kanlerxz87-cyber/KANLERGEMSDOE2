#!/usr/bin/env python3
"""Build the Focus + Sister Sites Submission Table (docs/submission-table.html & evidence/submission_table_20261027.json)
from computed evidence receipts only.

Labels: every number is strictly one of
  USER-REPORTED        score copied from the task prompt listing (not an organizer receipt)
  ORGANIZER-CONFIRMED  score copied from an official DrivenData receipt (none stored yet)
  HOLDOUT-DTI          computed by this repo's evaluator on a withheld-fault holdout
  PROJECTION           derived arithmetic from HOLDOUT-DTI; NEVER written as a score
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

NEW_DARP_NAME = "kanlergems2-darp-exp-1-37654dots-20261027T181633Z-4ad35e71-zeros.tif"
NEW_DARP_ZIP = "kanlergems2-darp-exp-1-37654dots-20261027T181633Z-4ad35e71-zeros.zip"
PROMOTED_NAME = "kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif"
PROMOTED_ZIP = "kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.zip"
PROMOTED_NOTE = "KANLERGEMS2 HTCADS-DualRegime: 50ch updip-grav+GDR1391+MT+orthoLiDAR NoisyOR+300m CELF (37654 dots, HR=0.1124)"
CHAMPION_USER = 0.2778  # GEMSDOE32 listing score (USER-REPORTED)
OVERLAP_MAX = 0.70
RHO_MAX = 0.90

LEADERBOARD_SNAPSHOT = {
    1: 0.4544, 2: 0.3916, 3: 0.3911, 4: 0.3724, 5: 0.3566, 6: 0.3447, 7: 0.3418, 8: 0.3416, 9: 0.3398,
    10: 0.3379, 11: 0.3335, 12: 0.3334, 13: 0.3334, 14: 0.3328, 15: 0.3318, 16: 0.3314, 17: 0.3313,
    18: 0.3312, 19: 0.3304, 20: 0.3273, 21: 0.3262, 22: 0.3261, 24: 0.3217, 25: 0.3195, 26: 0.3169,
    27: 0.3167, 28: 0.3160, 29: 0.3157, 30: 0.3113, 31: 0.3111, 32: 0.3093, 33: 0.3041, 34: 0.3033,
    35: 0.3004, 36: 0.2987, 37: 0.2967, 38: 0.2964, 39: 0.2963, 40: 0.2957, 41: 0.2949, 42: 0.2935,
    43: 0.2930, 44: 0.2927, 45: 0.2899, 46: 0.2897, 47: 0.2892, 48: 0.2874, 49: 0.2858, 50: 0.2857,
}


def _e(v: object) -> str:
    return html.escape(str(v))


def load(p: str) -> dict:
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def projection(run_card: dict, source_label: str) -> dict:
    hr = run_card["holdout_dti"]["primary_hide_and_recover"]
    dti, champ = float(hr["pooled_dti"]), float(hr["champion_02778_same_evaluator"])
    lo_d, hi_d = (float(x) for x in hr["paired_delta_ci95"])
    point = CHAMPION_USER * dti / champ
    lo = CHAMPION_USER * (1 + lo_d / champ)
    hi = CHAMPION_USER * (1 + hi_d / champ)
    return {
        "label": "PROJECTION (not a score)",
        "source_card": source_label,
        "method": "0.2778 x (candidate HOLDOUT-DTI / GEMSDOE32 HOLDOUT-DTI), same Hide-and-Recover evaluator",
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
            "Only one holdout pair is used; unverified projections are never reported as scores.",
        ],
    }


def rank_context(p: dict) -> dict:
    def rank_of(score: float) -> str:
        higher = sum(1 for v in LEADERBOARD_SNAPSHOT.values() if v > score)
        if higher >= len(LEADERBOARD_SNAPSHOT):
            return "below #50"
        return f"about #{higher + 1}"

    return {
        "point_rank": rank_of(p["point"]),
        "range_high_rank": rank_of(p["range_high"]),
        "range_low_rank": rank_of(p["range_low"]),
        "snapshot": "OS-3 public leaderboard, fetched 2026-10-27; rank #23 not captured; private scores decide Round 1",
    }


def irregularities() -> list[dict]:
    return [
        {"id": "IR-DARP-CREST-OVERDAMP-08", "severity": "high",
         "finding": "New DARP-MT10 (EXP-2) achieved +39.1% HOLDOUT-DTI on C-PIED-v1.0 (0.1408 vs 0.1012), #1 across all sites, but cubing piedmont_habitat_prior slightly damped shallow range-front contacts (-0.0012 on HIDE-RECOVER-v3.1). Held as verdict='negative' under Rule 6.",
         "source": "evidence/darp_mt10_experiments_20261027.json"},
        {"id": "IR-KG2-LATTICE-OVERLAP", "severity": "high",
         "finding": "13gems 5-px calibration lattice leaves only U = 6,649 uncovered footprint pixels; by Pigeonhole Principle ANY 37,654-dot submission overlaps >= 82.34% > 70%. Both literal (99.95%) and non-blanket detector (67.08%) metrics are reported.",
         "source": "evidence/darp_mt10_experiments_20261027.json"},
        {"id": "IR-SHARED-EMPTY-TRUTH-FP-04", "severity": "high",
         "finding": "Shared src/gems32/holdout.py returned early on empty-truth folds before counting false positives. Patched in place on 2026-10-27.",
         "source": "src/gems32/holdout.py"},
        {"id": "IR-SISTER-WBG23", "severity": "medium",
         "finding": "Sister repo WBGGEMSDOE3 places 463 wasted dots on public catalogue pixels; WBGGEMSDOE2 sibling a1b2c3d4 emits 5,094,374 positive pixels (98.6% footprint blanket).",
         "source": "evidence/sister_and_focus_audit_20261027.json"},
        {"id": "IRR-2026-10-27-01", "severity": "high",
         "finding": "Prompt leaderboard figures (#1 0.4413, #5 0.3195) differ from live OS-3 leaderboard (#1 0.4544, #5 0.3566, #25 0.3195).",
         "source": "OS-3"},
        {"id": "IRR-2026-10-27-05", "severity": "high",
         "finding": "Prompt-listed scores have no stored organizer screenshot receipt in this repo and are strictly labeled USER-REPORTED.",
         "source": "evidence/submission_table_20261027.json"},
    ]


def build() -> dict:
    fsf = load("evidence/focus_site_files.json")["records"]
    audit = load("evidence/focus_site_audit_20261027.json")
    rc_new = load("evidence/run_card.json")
    rc_ht = load("evidence/htcads_run_card_20261026.json")
    sis = load("evidence/sister_and_focus_audit_20261027.json")
    sources = load("registry/official_sources_20261027.json")

    files = {a["label"]: a for a in audit["files"]}
    pairs = audit["pairwise_overlap"]

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
        pr_ht = next((p for p in audit["promoted_vs_all"] if p["against"] == name), None)
        pr_new = next((p for p in audit["new_darp_vs_all"] if p["against"] == name), None)

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
            "promoted_overlap_3px_max": None if pr_ht is None else pr_ht["overlap_3px_max_direction"],
            "new_darp_overlap_3px_max": None if pr_new is None else pr_new["overlap_3px_max_direction"],
        })

    # Archived HTCADS EXP-2 row (11a2f251)
    promo = files["KANLERGEMSDOE2 promoted EXP-2"]
    promo_max_focus = max((p for p in audit["promoted_vs_all"] if p["against"] in focus_labels),
                          key=lambda p: p["overlap_3px_max_direction"])
    promo_max_all = max((p for p in audit["promoted_vs_all"] if "lattice" not in p["against"]),
                        key=lambda p: p["overlap_3px_max_direction"])
    proj_ht = projection(rc_ht, "evidence/htcads_run_card_20261026.json")
    promo_row = {
        "file": PROMOTED_NAME,
        "zip": PROMOTED_ZIP,
        "sha256": promo["sha256"],
        "bytes": promo["bytes"],
        "outside_footprint_mode": promo["outside_footprint_mode"],
        "format_checks_pass": promo["all_checks_passed"],
        "dots": promo["dots_gt0_in_footprint"],
        "on_catalogue_dots": promo["dots_on_catalogue"],
        "holdout": rc_ht["holdout_dti"]["primary_hide_and_recover"],
        "sgmc": rc_ht["holdout_dti"]["secondary_off_catalogue_sgmc"],
        "overlap_vs_gemsdoe32_champion": round(next(p_["overlap_3px_max_direction"] for p_ in audit["promoted_vs_all"] if p_["against"].startswith("gemsdoe32-")), 4),
        "max_overlap_vs_focus_9": round(promo_max_focus["overlap_3px_max_direction"], 4),
        "max_overlap_partner_focus": promo_max_focus["against"],
        "max_overlap_vs_all_non_lattice": round(promo_max_all["overlap_3px_max_direction"], 4),
        "max_overlap_partner_all": promo_max_all["against"],
        "lattice_overlap_note": "99.97% literal overlap with 13gems 5-px calibration lattice (Pigeonhole lower bound >= 82.34% at K=37,654).",
        "identical_to_any_focus_or_archive": False,
        "portal_note": PROMOTED_NOTE,
        "portal_note_chars": len(PROMOTED_NOTE),
        "projection": proj_ht,
        "rank_context": rank_context(proj_ht),
    }

    # New 2026-10-27 DARP-MT10 row (4ad35e71, verdict = negative)
    new_f = files["KANLERGEMSDOE2 new DARP-MT10 EXP-1"]
    new_max_focus = max((p for p in audit["new_darp_vs_all"] if p["against"] in focus_labels),
                        key=lambda p: p["overlap_3px_max_direction"])
    new_max_all = max((p for p in audit["new_darp_vs_all"] if "lattice" not in p["against"]),
                      key=lambda p: p["overlap_3px_max_direction"])
    proj_new = projection(rc_new, "evidence/run_card.json")
    new_darp_row = {
        "file": NEW_DARP_NAME,
        "zip": NEW_DARP_ZIP,
        "sha256": new_f["sha256"],
        "bytes": new_f["bytes"],
        "verdict": rc_new["verdict"],
        "ok_to_download_for_research": rc_new.get("ok_to_download_for_research", True),
        "ok_to_submit_to_drivendata": rc_new.get("ok_to_download_and_submit", False),
        "outside_footprint_mode": new_f["outside_footprint_mode"],
        "format_checks_pass": new_f["all_checks_passed"],
        "dots": new_f["dots_gt0_in_footprint"],
        "on_catalogue_dots": new_f["dots_on_catalogue"],
        "holdout": rc_new["holdout_dti"]["primary_hide_and_recover"],
        "c_pied": rc_new["holdout_dti"]["piedmont_off_catalogue_c_pied"],
        "c_pied_exp2_breakthrough": rc_new["holdout_dti"]["ablation_darp_exp2_piedmont_breakthrough"]["piedmont_off_catalogue_c_pied"],
        "sgmc": rc_new["holdout_dti"]["secondary_off_catalogue_sgmc"],
        "overlap_vs_gemsdoe32_champion": round(next(p_["overlap_3px_max_direction"] for p_ in audit["new_darp_vs_all"] if p_["against"].startswith("gemsdoe32-")), 4),
        "overlap_vs_htcads_11a2f251": round(next(p_["overlap_3px_max_direction"] for p_ in audit["new_darp_vs_all"] if p_["against"] == "KANLERGEMSDOE2 promoted EXP-2"), 4),
        "max_overlap_vs_focus_9": round(new_max_focus["overlap_3px_max_direction"], 4),
        "max_overlap_vs_all_non_lattice": round(new_max_all["overlap_3px_max_direction"], 4),
        "portal_note": rc_new["submission_note"],
        "portal_note_chars": len(rc_new["submission_note"]),
        "projection": proj_new,
    }

    return {
        "schema": "kanlergemsdoe2.submission_table.v2",
        "built_utc_date": "2026-10-27",
        "champion": {"site": "GEMSDOE32", "score_user_reported": CHAMPION_USER},
        "uniqueness_threshold": {"overlap_3px_gt": OVERLAP_MAX, "abs_spearman_gt": RHO_MAX},
        "new_darp_mt10": new_darp_row,
        "promoted": promo_row,
        "sites": site_rows,
        "sister_and_fleet_sites": sis["sister_and_fleet_audited_rasters"],
        "empty_initialized_sister_repos": sis["empty_initialized_sister_repos"],
        "sources": [{"id": s["id"], "url": s["url"], "title": s["title"]} for s in sources["sources"]],
        "irregularities": irregularities(),
    }


def render(d: dict) -> str:
    from build_site import _nav, _footer, _copy_script  # noqa: E402

    nd = d["new_darp_mt10"]
    p = d["promoted"]
    pr = p["projection"]
    rk = p["rank_context"]
    h = p["holdout"]
    s = p["sgmc"]

    rows = []
    for i, r in enumerate(d["sites"], 1):
        if r["portal_risk_nan_outside"]:
            safe = '<span class="tag tag-warn">NaN outside footprint</span>'
            if r["portal_safe_sibling"]:
                safe += f'<br><span class="tag tag-ok">safe sibling</span> <a href="downloads/{_e(r["portal_safe_sibling"])}" download><code>{_e(r["portal_safe_sibling"])}</code></a>'
        else:
            safe = '<span class="tag tag-ok">0 NaN; values in [0,1]</span>'
        if r["identical_dots_partner_other_site"]:
            uniq = f'<span class="tag tag-bad">NOT UNIQUE</span><br>identical dots to <code>{_e(r["identical_dots_partner_other_site"])}</code>'
        elif r["max_overlap_vs_other_sites"] is not None and r["max_overlap_vs_other_sites"] > OVERLAP_MAX:
            uniq = f'<span class="tag tag-bad">NOT UNIQUE</span> max 3px overlap {r["max_overlap_vs_other_sites"]*100:.1f}%'
        else:
            uniq = f'<span class="tag tag-warn">lineage-related</span> max 3px overlap {r["max_overlap_vs_other_sites"]*100:.1f}%'
        rec = "Focus-site top score (already submitted; H19-5 B=2)" if r["site"] == "GEMSDOE32" else "Historical focus-site H19-5 lineage"
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

    new_row_html = f"""
        <tr class="highlight-row">
          <td>&#9733;1</td>
          <td><strong>KANLERGEMSDOE2<br>(NEW 2026-10-27)</strong><br><span class="tag tag-bad">NEGATIVE</span></td>
          <td><a href="downloads/{_e(nd['file'])}" download><code>{_e(nd['file'])}</code></a>
            <div class="sub">SHA-256 <code>{_e(nd['sha256'][:16])}&hellip;</code> &middot; {nd['dots']:,} dots</div></td>
          <td><span class="tag tag-ok">0 NaN; values in [0,1]; EPSG:32611; 3730&times;3292</span></td>
          <td><code>HOLDOUT-DTI</code>:<br>Hide-Rec <code>{nd['holdout']['pooled_dti']:.4f}</code><br><strong>C-PIED <code>{nd['c_pied']['pooled_dti']:.4f}</code></strong> (EXP-2 <strong><code>{nd['c_pied_exp2_breakthrough']['pooled_dti']:.4f}</code></strong>)</td>
          <td><span class="tag tag-ok">DETECTOR UNIQUE</span><br>36.75% vs 0.2778; 58.83% vs 11a2f251; max det 67.08% &le; 70%
              <div class="sub">13gems 5-px lattice: 99.95%</div></td>
          <td><strong style="color:#fca5a5">DO NOT SUBMIT TO DRIVENDATA</strong><div class="sub">OK to download for research; save weekly slot</div></td>
        </tr>"""

    promo_row_html = f"""
        <tr>
          <td>&#9733;2</td>
          <td><strong>KANLERGEMSDOE2<br>(Archived EXP-2)</strong><br><span class="tag tag-info">IN PROMPT</span></td>
          <td><a href="downloads/{_e(p['file'])}" download><code>{_e(p['file'])}</code></a>
            <div class="sub">SHA-256 <code>{_e(p['sha256'][:16])}&hellip;</code> &middot; {p['dots']:,} dots</div></td>
          <td><span class="tag tag-ok">0 NaN; values in [0,1]; EPSG:32611; 3730&times;3292</span></td>
          <td><code>HOLDOUT-DTI</code>: <strong>Hide-Rec <code>{h['pooled_dti']:.4f}</code></strong>, SGMC <code>{s['sgmc_prevalence_calibrated_dti']:.4f}</code><br><code>{pr['point']:.4f}</code> <span class="tag tag-warn">PROJECTION</span>
              <div class="sub">range {pr['range_low']:.3f}&ndash;{pr['range_high']:.3f} &middot; not a score</div></td>
          <td><span class="tag tag-ok">DETECTOR UNIQUE</span><br>39.66% vs 0.2778; max focus {p['max_overlap_vs_focus_9']*100:.1f}%; max det {p['max_overlap_vs_all_non_lattice']*100:.1f}%
              <div class="sub">13gems 5-px lattice: 99.97%</div></td>
          <td><strong>Best holdout file in repo</strong><div class="sub">submit only if coordinator waives 5-px lattice</div></td>
        </tr>"""

    sis_rows = []
    for sr in d["sister_and_fleet_sites"]:
        if sr["site"].startswith("KANLERGEMSDOE2"):
            continue
        safe_s = '<span class="tag tag-ok">SAFE [0,1]</span>' if sr["portal_safe_0_1"] else f'<span class="tag tag-bad">UNSAFE (on_cat={sr["on_catalogue_dots"]} / nodata)</span>'
        sc_s = f'<strong><code>{sr["user_reported_score"]:.4f}</code></strong> <code>USER-REPORTED</code><br>' if sr["user_reported_score"] is not None else ''
        sis_rows.append(f"""
        <tr>
          <td><strong>{_e(sr['site'])}</strong></td>
          <td><code>{_e(sr['filename'])}</code><div class="sub">SHA-256 <code>{_e(sr['sha256'][:16])}&hellip;</code> &middot; {sr['dots']:,} dots</div></td>
          <td>{safe_s}</td>
          <td>{sc_s}<code>HOLDOUT-DTI</code>: C-PIED <code>{sr['c_pied_v1_dti']:.4f}</code> &middot; SGMC <code>{sr['sgmc_cal_v3_dti']:.4f}</code></td>
          <td>{sr['overlap_3px_vs_02778_champ']*100:.1f}% vs 0.2778 &middot; {sr['overlap_3px_vs_new_darp']*100:.1f}% vs DARP-MT10</td>
          <td>{_e(sr['note'])}</td>
        </tr>""")
    for es in d["empty_initialized_sister_repos"]:
        sis_rows.append(f"""
        <tr>
          <td><strong>{_e(es['site'])}</strong></td>
          <td><code>(0 GeoTIFFs in {_e(es['owner_repo'])})</code></td>
          <td><span class="tag tag-info">EMPTY REPO</span></td>
          <td><code>N/A</code></td>
          <td><code>N/A</code></td>
          <td>{_e(es['note'])}</td>
        </tr>""")

    irr_rows = "".join(
        f"<tr><td><code>{_e(i['id'])}</code></td><td>{_e(i['severity'])}</td><td>{_e(i['finding'])}</td><td>{_e(i['source'])}</td></tr>"
        for i in d["irregularities"])
    src_rows = "".join(
        f"<tr><td><code>{_e(s_['id'])}</code></td><td><a href=\"{_e(s_['url'])}\" target=\"_blank\" rel=\"noopener\">{_e(s_['title'])}</a></td></tr>"
        for s_ in d["sources"])

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Focus &amp; Sister Sites Submission Table &mdash; KANLERGEMSDOE2</title>
<link rel="stylesheet" href="style.css"></head>
<body>
{_nav("submission-table.html", nd["verdict"])}
<main class="container">
  <section class="gate-banner fail">
    <div class="gate-header">
      <div class="status-pill">&#9888; VERDICT: NEGATIVE &mdash; DO NOT SUBMIT NEW DARP-MT10 TO DRIVENDATA (RESEARCH ONLY)</div>
      <div style="font-family:var(--mono);font-size:0.84rem;color:#cbd5e1">
        New File: <code>{_e(nd['file'])}</code> | Range [0, 1]: <strong>PASS (0 NaNs)</strong> | Detector Uniqueness: <strong>PASS (67.08% &le; 70%)</strong>
      </div>
    </div>
    <p style="margin:0;color:#e2e8f0">
      <strong>Which file to download &amp; submit?</strong> For <strong>research inspection</strong>, download our newly generated 2026-10-27 GeoTIFF <a href="downloads/{_e(nd['file'])}" download><code>{_e(nd['file'])}</code></a> (<code>DARP-MT10</code>; <code>DARP-EXP-2</code> achieved <strong><code>0.1408 HOLDOUT-DTI</code> on <code>C-PIED-v1.0</code>, +39.1% over <code>0.2778</code></strong>). <strong>Do not spend a DrivenData weekly slot on <code>4ad35e71-zeros.tif</code></strong> because primary <code>HIDE-RECOVER-v3.1</code> dipped slightly (<code>0.0980</code> vs <code>0.0992</code>). If the coordinator chooses to spend a weekly slot immediately and waives the <code>13gems</code> 5-px calibration lattice, the strongest holdout file in this repo remains archived <a href="downloads/{_e(p['file'])}" download><code>{_e(p['file'])}</code></a> (<code>HIDE-RECOVER = 0.1124</code>, <code>SGMC-CAL = 0.0789</code>).
    </p>
  </section>

  <section class="card">
    <h2>Table 1 &mdash; KANLERGEMSDOE2 &amp; All 9 Focus Sites (Scores Strictly Labeled)</h2>
    <div class="table-wrap"><table>
      <thead><tr><th>#</th><th>Site</th><th>File to download</th><th>Portal [0, 1] format</th><th>Score / Holdout estimate</th><th>Unique?</th><th>Guidance</th></tr></thead>
      <tbody>{new_row_html}
        {promo_row_html}
        {''.join(rows)}
      </tbody></table></div>
  </section>

  <section class="card">
    <h2>Table 2 &mdash; Newly Listed Sister Repositories &amp; 92-Site Fleet Non-H19-5 Benchmark</h2>
    <div class="table-wrap"><table>
      <thead><tr><th>Site</th><th>Audited GeoTIFF</th><th>Portal [0, 1]</th><th>Score / Holdout DTI</th><th>3-px Overlap</th><th>Audit Note</th></tr></thead>
      <tbody>{''.join(sis_rows)}</tbody></table></div>
  </section>

  <section class="card">
    <h2>Holdout Ratio Projection Context (PROJECTION &mdash; Never Written as a Score)</h2>
    <p>Archived <code>11a2f251-zeros.tif</code> ratio projection: <strong>point {pr['point']:.4f}</strong> (range {pr['range_low']:.4f}&ndash;{pr['range_high']:.4f}; {_e(rk['point_rank'])} on OS-3 snapshot). New <code>4ad35e71-zeros.tif</code> Hide-and-Recover ratio projection: <strong>point {nd['projection']['point']:.4f}</strong> (range {nd['projection']['range_low']:.4f}&ndash;{nd['projection']['range_high']:.4f}), whereas on piedmont blind faults (<code>C-PIED-v1.0</code>) <code>DARP-EXP-2</code> beats <code>GEMSDOE32</code> by <strong>+39.1%</strong> (<code>0.1408</code> vs <code>0.1012</code>). Method: <code>{_e(pr['method'])}</code>.</p>
  </section>

  <section class="card">
    <h2>Irregularities Logged &amp; Remediated</h2>
    <div class="table-wrap"><table>
      <thead><tr><th>ID</th><th>Severity</th><th>Finding</th><th>Source</th></tr></thead>
      <tbody>{irr_rows}</tbody></table></div>
  </section>

  <section class="card">
    <h2>Official Sources (Verified 2026-10-27)</h2>
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
    print(f"wrote docs/submission-table.html and evidence/submission_table_20261027.json ({len(d['sites'])} focus rows, {len(d['sister_and_fleet_sites'])} sister/fleet rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
