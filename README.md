# KANLER GEMS — evidence-first competition desk

**Maximize the probability of winning. Own the outcome.** This is a standing research brief and an auditable submission decision desk for the [DOE GEMS Prize](https://www.drivendata.org/competitions/306/competition-doe-gems/). A strong-looking map is not a valid submission without independent scientific, novelty, format and selector evidence.

> **Current decision, 26 October 2026: NEGATIVE. Do not submit.** The registered GEMSDOE48 continuous reference is positive at all 5,167,373 pixels of the mirrored competition footprint. The shared template defines a raster's “dots” as positive pixels. Consequently every nonempty candidate dot set has **100%** directional 3-pixel overlap with that one registered reference, exceeding the specified >70% stop. The full proof, byte hashes, pinned reference and prior-E1 measurements are in [`evidence/registry_witness.json`](evidence/registry_witness.json). This result is conditional on that literal support convention; treating a continuous raster differently would require an explicit change to the shared protocol, not an unannounced exemption.
>
> No new geological experiment, candidate TIFF, competition upload or weekly slot was used in this session. Earlier E1 uniqueness, holdout and score-projection claims are withdrawn; see [`docs/lane-e1-xg-hgb.html`](docs/lane-e1-xg-hgb.html) and the quarantined records. Historical files are not approved submissions.

## Decision desk and key evidence

- [Executive site](docs/index.html) and [submission guide](docs/executive-summary.html): nine priority projects, sources, file names, unambiguous current eligibility and an explanation of the range-error checks.
- [One negative run card](research/run_card.json), [selector decision](evidence/selector_decision.json), [registry witness](evidence/registry_witness.json) and [data-readiness audit](evidence/data_readiness.json).
- [Ranked scientific hypotheses](research/hypotheses.md), [scientific source register](research/science-and-sources.md), [shared-template fixes](research/template-fixes.md), [audit review](research/review.md), and [nine-raster comparisons](research/raster_audit.json).
- [Competition leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/): the retained 26 October 2026 public snapshot shows **0.4437** as rank one, not an exact-file organizer receipt or a private score. The desk displays the observation time and staleness, but does not automatically access or scrape DrivenData; consult the official page for a current value. See [`evidence/leaderboard_snapshot.json`](evidence/leaderboard_snapshot.json).

The best of the nine supplied historical owner reports is **GEMSDOE32 at 0.2778**, for `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`; the exact-file organizer receipt is unavailable. Sparse, spaced dots and known-catalogue flank pruning are plausible under the 300 m distance-weighted metric, but neither the cause of this value nor a higher score for any new idea is established. The nine selected historical rasters match the mirrored grid and pass local value checks, but all 72 directed pairs fail the near-duplicate rule. That limited audit is not a full-registry comparison.

## Standing protocol

1. Assign **one exclusive method lane**. The current prompt mentions a single-method paragraph but does not identify one; do not invent exclusivity. Preregister 3–5 evidence-based hypotheses, transforms, costs, known non-fault mimics and usable sources before implementation.
2. Freeze a complete registry and the current best. Check the **candidate surface before placement** and the **final dots** against every registered raster: stop when Spearman rank correlation is >0.90 or more than 70% of candidate dots are within Euclidean 3 pixels of any reference. Do not evade the rule by renaming, perturbing or excluding inconvenient references. Current literal support semantics make this stop universal.
3. When the protocol is legitimately resolved, reuse the shared template's features, evaluator and writer. Hide whole connected fault segments with a buffer, derive catalogue features only from fold-visible labels, and mask visible pixels exactly. Every feature alone is a leakage canary: AUC >0.90 is leakage until disproved, but a smaller value is not proof of independence. Use pooled DTI, alpha 0.2, beta 0.8 and the 300 m triangular kernel. Compare with a reproducibly rebuilt frozen best on identical folds, with a paired 95% CI and withheld-positive count. A catalogue holdout is not the organizer's hidden-label score.
4. At most three experiments or two hours. If the experiment is negative, stop; never create a superficially different historical copy. Any candidate TIFF must be reopened and checked for single float32 band, exact grid, finite values and [0,1] range; record its exact SHA-256, name and note ≤140 characters. Local format success is not portal acceptance or scientific approval.
5. Selection is separate from research. Require independently authenticated evidence and the remaining competition allowance before authorizing any upload. The [official NLR rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf) describe up to three submissions per week, one selected submission for both rounds, reproducibility and a generative-AI disclosure. Our remaining allowance is unknown; no code here submits or spends slots.

## Reproduce audits locally

Python 3.11 and the dependencies in `requirements.txt` are needed. Large data are deliberately ignored and must not be committed. The restore downloads pinned public **peer mirrors**, verifies full file hashes and installs only explicitly named archive members; it is not an authenticated organizer download. It needs network access to GitHub codeload and substantial disk space.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python scripts/restore_competition_data.py
python scripts/prepare_data.py --output evidence/data_readiness.json
python scripts/audit_registry_witness.py --output evidence/registry_witness.json
python scripts/compare_registry.py
python scripts/select_submission.py
python scripts/run_tests.py
python scripts/build_site.py
```

The mirrored sample has positive values matching known labels although the [official page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) describes its example as total fault absence. Use this mirror **only for grid and footprint**, never as a model feature or hidden truth. Compare it and the other inputs against authenticated organizer files when available. A hash match proves equality to the pinned mirror, not organizer origin, source licensing or fold independence.

The local scripts use [`vendor/template`](vendor/template/) as the selected shared implementation. A marginal-credit helper and the literal novelty check were fixed there once; upstream and patched hashes, the exact limits of the fixes and unresolved competing peer-template authority are documented in [`research/template-fixes.md`](research/template-fixes.md). Quarantined E1 scripts are historical, not a second implementation or an execution path.

## Next work

Resolve the continuous-surface versus discrete-dot interpretation of the stated all-registry rule and identify the exclusive lane; obtain and pin the complete current registry and an authenticated organizer grid; reconstruct the frozen best with whole-segment fold-local training; verify external raw-data availability and provenance; then attempt the highest-ranked eligible physical hypothesis with the canary, paired confidence interval and two-stage registry checks. Until these are achieved, no candidate is authorized and no leaderboard score is projected.
