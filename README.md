# GEMS Research Office

**DO NOT SUBMIT. No new GeoTIFF was generated, no holdout DTI was calculated, and no competition slot was used.** The sole preregistered feasibility probe failed the required pre-placement novelty gate: **74.9758%** of its positive surface cells lay within three pixels of a registered GEMSDOE32 raster, above the **70%** limit. The scan stopped at that witness after 306 distinct-byte comparisons; it did not establish uniqueness against the rest. A negative result is a deliverable, not a reason to evade the stop.

**Dashboard:** [GitHub Pages](https://kanlerxz87-cyber.github.io/KANLERGEMSDOE2/) · [run card](docs/data/run-card.json) · [nine-site audit](knowledge/03_site_by_site_2026-10-26.md) · [scientific findings and sources](knowledge/02_findings_and_sources_2026-10-26.md) · [upload contract](knowledge/05_upload_contract.md)

## The decision in a minute

- The highest historical figure supplied for the nine sites is **0.2778**, an **owner-reported, unverified claim** for GEMSDOE32. No organizer receipt ties it to the cited hash. The decoded 37,654-dot H33-B2 file is exactly the 44,090-dot D2.8 map pruned within two pixels of mirrored known faults. Lower false-positive mass could improve the metric, but hidden labels are unavailable, so the cause and any future score remain unknown.
- The official public leaderboard read **0.4437** on 2026-10-26 at approximately 21:37 UTC for another participant. It is not a score for this project. The dashboard is timestamped and attempts a six-hourly refresh; failures retain the old observation rather than relabeling it live.
- A registered every-fifth-pixel lattice covers 99.8713% of the footprint within three pixels. Any 37,654-point raster has at least **82.34%** overlap with it, no matter where its points go. A ≤70% result requires at most 22,163 distinct dots, a necessary—not sufficient—condition. Do not silently remove a reference from the registry.
- Post-run review found that the probe implemented **unsigned**, not the proposed signed-polarity signal, and that its full-catalogue-masked production-surface AUC was not a valid withheld-fold canary. The measured feature AUCs are diagnostics only; no DTI or clean test of the proposed signed mechanism is claimed.
- The shared evaluator drops false-positive mass in a zero-truth cell; a synthetic reproducer is included and [the defect was reported upstream](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41). We lack write permission to that template and did not privately fork its evaluator. The stopped probe never called it.

## Project charter / prompt to reread each session

The exact original user message is not available in the condensed session context; the following is a faithful **requirements reconstruction**, not a verbatim quotation. Re-read it before changing science or submission status:

> Review the DOE GEMS geothermal-fault competition using official sources and an auditable site-by-site executive analysis of GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36. Explain the owner-reported 0.2778 GEMSDOE32 result and assess whether it can be beaten. Generate an independently unique, valid, high-performing GeoTIFF only if the scientific, format and uniqueness gates pass; no human inspection should be required. Never copy an old submission except for educational analysis. State clearly whether submission is permitted. Use trusted free data and automatically obtain and prepare inputs where possible; disclose any authentication or format blocker. Build a clean GitHub Pages report with live-or-dated evidence, clear sources and download/submit instructions. Perform three review/fix passes, and create a PR and merge to main when permitted.
>
> Work in one assigned method lane. Before implementation rank 3–5 not-yet-tried geological hypotheses with layers, physical signatures, mimics, cost and rationale; verify the sources are obtainable and appropriately licensed. Reuse the shared feature stack, `evaluate_holdout.py`, and `submission_writer.py`; repair any shared tool once in its template, rather than keeping a private fork. Before placement and on final dots, stop if surface rank correlation exceeds 0.90 or more than 70% of dots lie within three pixels of any registered raster. Do not reinterpret the registry to bypass the rule. Budget at most three experiments or two hours.
>
> Hide complete fault segments with a buffer; derive catalogue features only from visible faults and mask visible faults pixel-exactly. Test features individually: AUC above 0.90 is leakage until disproved. Use pooled distance-weighted Tversky with α=.2, β=.8 and a 300 m triangular kernel. Any HOLDOUT-DTI must identify evaluator version, withheld positive count and 95% CI. Never call a projection a score; reserve ORGANIZER-CONFIRMED for an actual submission-page receipt. A candidate must beat the comparable holdout best before a separate selector may approve a real weekly slot; do not spend or choose one automatically.
>
> Check the saved GeoTIFF bytes for finite in-footprint [0,1] values, band count, CRS, shape and transform; account for the reported portal range error rather than assuming a fix. Produce one JSON run card with hypothesis, mechanism, named non-fault mimic, holdout DTI/CI, registry overlap/correlation, raster SHA-256, validator result, unique name, ≤140-character note, and promote/negative verdict. Negative results are deliverables.

The protocol refers to an assigned single method paragraph, but none was identifiable in the preserved request. H1 was self-preregistered as a **feasibility probe**, not represented as an assigned lane. The original Dropbox URLs are not present in the condensed context; the first attempt to access the supplied Dropbox link failed TLS, so the runnable restoration below uses pinned public owner mirrors. Mirror hashes establish byte integrity, not organizer origin or redistribution rights.

### Arena values

- **Maximize P(Win):** optimize for a real, verified competition outcome, not a simulated score, a filename, or an invalid upload. Preserve submission budget and compare only compatible evidence.
- **Own the Outcome:** record failures and uncertainty, fix what can be fixed in the authoritative shared location, provide automated checks and actionable next steps, and do not silently claim completion when a gate fails.

## Reproduce the audit without placing data manually

Prerequisites: Python 3.11, `git`, `curl`, `tar`, `sha256sum` and `gh`; enough disk (at least 5 GB, more for features), network access to GitHub/PyPI and, for large registries, sufficient GitHub API quota. The research data are excluded from Git. We used Linux, two CPU cores and ~3.8 GiB RAM. No GPU is required for the audit; the organizer reference offers a CPU environment.

```bash
# Restore pinned shared template, locally pinned owner-mirror data, current registry
# cache and historical registry lock; independently verify Git blob identities.
bash scripts/download_competition_data.sh

# Optional: also build the upstream shared 35-channel cached feature stack (~1.7 GB).
bash scripts/download_competition_data.sh --build-stack

# Run fast offline tests and the shared-tool synthetic defect diagnostic.
.venv/bin/python -m pytest -q
.venv/bin/python scripts/reproduce_template_defect.py

# Serve the static dashboard locally.
python3 -m http.server 8000 --bind 0.0.0.0 --directory docs
```

`data/registry-lock.json` records the nine immutable trees used for the stopped audit. The helper fetches the shared registry and independently checks/restores locked blobs, detects truncation and oversized omissions, and refuses mismatches. This historical lock does **not** prove a later or private registry complete. Concurrent template restore commands overwrite a common receipt, so the helper runs them sequentially. Bootstrap fails closed on exhausted GitHub API quota, unavailable mirrors or checksum mismatches; it never invokes DrivenData submissions. Packages are locked in `requirements-lock.txt`; cache and venv may be safely removed and rebuilt. The actual original organizer files and portal receipt remain unverified. The H1 script contains a persistent duplicate-stop guard and must not be rerun or retuned under the same lane.

## Evidence map

| Path | Purpose |
|---|---|
| `knowledge/01_preregistration_2026-10-26.md` | Ranked hypotheses, frozen probe, post-run arithmetic erratum and implementation disclosures. |
| `knowledge/02_findings_and_sources_2026-10-26.md` | Metric, causal limitations, official sources, provenance and defects. |
| `knowledge/03_site_by_site_2026-10-26.md` | Nine independently reopened historical file briefs and research-only links. |
| `knowledge/05_upload_contract.md` | Conditional upload and exact-byte checking, explicitly not permission. |
| `docs/data/run-card.json` | The one negative run card; null DTI/CI/hash/validator; no slot. |
| `evidence/novelty_surface.json` | First-failure novelty evidence, 306 distinct-byte comparisons. |
| `data/registry-lock.json` | Pinned public nine-repository registry inventory. |
| `scripts/validate_saved_tiff.py` | Independent fail-closed saved-byte reader; cannot authorize submission. |
| `evidence/historical_h33_format.json` | Research-only zero-exterior read-back example, not portal acceptance. |
| `.github/workflows/pages.yml` | Pages publication and stale-safe scheduled leaderboard snapshot refresh. |

## Limitations and next steps

The owner-mirrored sample matches the mirrored training labels rather than the all-zero sample described by the organizer; reconcile with authenticated original downloads. The written spec requires null/NaN outside the footprint, while the user's portal range error has no retained rejected bytes. An all-finite zero exterior may pass a local check but is not proven acceptable to the portal. Repair the shared evaluator upstream, authenticate inputs, obtain the missing lane assignment, resolve the literal lattice constraint rather than excluding it, then run a new independent science/format/registry evaluation. Only a separate selector may decide whether a genuinely passing future file deserves a weekly slot. See the [full upload contract](knowledge/05_upload_contract.md).
