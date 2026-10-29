# Standing Project Brief & Parallel-Run Protocol (`KANLERGEMSDOE2`)

> **2026-10-29 integrity correction — DO NOT SUBMIT.** New candidate filename: **NONE**; approved download: **NONE**; new leaderboard-score estimate: **NOT ESTIMABLE**. No candidate exists for uniqueness testing: pre-placement surface correlation is not computed and final-dot novelty is not applicable, not passed. The frozen 37,654-dot witness lower bound is 82.3418%, above the 70% stop. The [2026-10-29 review](evidence/review_20261029.md), [current-head score/source table](evidence/submission_table_20261029.json), and [five-mechanism prior-art screen](research/2026-10-29_focus-nine-hypotheses.md) supersede stale or conflicting claims below. GEMSDOE28's 0.2710 attribution is disputed. Current GEMSDOE32 peer status corrects that H51-1's favorable 0.115134 fold-local re-emission arm is not the downloadable TIFF; its saved-byte recheck is lower than B2 on that peer's static holdout. These are not leaderboard scores.

> **Epistemic integrity:** This is a prior-session condensed standing brief, not a verbatim transcript. Read it with `README.md`, including the current decision and preserved request, at the start of every session. Historical user/owner reports are not organizer receipts; old target scores are historical snapshots.

---

## Core Values

- **Maximize P(Win):** Optimize expected performance on both leaderboard and expert-reviewed evaluation per scarce submission slot. Never burn a weekly slot on cosmetic edits, duplicate `H19-5` clones, or candidates that fail to beat the spatially-blocked holdout benchmark.
- **Own the Outcome:** Automated code gates — never manual human inspection — verify `[0, 1]` GeoTIFF range safety and zero NaNs **inside the footprint**, leakage canaries, registry uniqueness, and holdout statistical significance end-to-end. Fix shared template defects at the root and document every irregularity and negative result transparently; independently confirm the required exterior encoding.

---

## Standing Project Prompt Record

Review the repo and execute any open next steps first.

Focus on the highest-scoring submissions from the following 9 focus sites:
- `GEMSDOE24`, `GEMSDOE25`, `GEMSDOE27`, `GEMSDOE28`, `GEMSDOE30`, `GEMSDOE31`, `GEMSDOE32`, `GEMSDOE33`, `GEMSDOE36` (and cross-check against all listed GEMSDOE and sister sites: `KANLERGEMSDOE1..3`, `EUGGEMSDOE1..3`, `WBGGEMSDOE1..3`, `GINNYGEMSDOE1..3`, `GEMSDOEkarage1..3`, `ApartGEMSDOE1..3`, `GEMSDOESASS1..3`, `GEMSDOE..GEMSDOE92`, including `kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros`).

**THE FOLLOWING IS THE HIGHEST URGENCY AND MUST BE FOLLOWED:**
- **Generate a unique `.TIF` candidate only if every frozen-lane, surface-novelty, final-dot-novelty, holdout, leakage, format, and independent-approval gate passes.** If any gate fails, emit no candidate; record `filename: NONE`, no approved download, and **DO NOT SUBMIT**. Never copy a prior file or alter the frozen budget/placement to evade a stop.
- **Make the decision explicit** at the top of the GitHub Pages site, README, and executive summary: candidate filename/download, score-estimate status, uniqueness status (including NOT COMPUTED / NOT APPLICABLE rather than a false pass), and `DO NOT SUBMIT` / `OK TO SUBMIT`, validated automatically without human intervention.
- **Investigate submission portal error:** `"Predicted values must be in range [0, 1]"`. Check a single-band float32 GeoTIFF against the sample CRS `EPSG:32611`, `3730 x 3292` shape, and `100 m` affine grid; check the entire array and NaNs. Official text says null/NaN outside bounds; a zeros-outside artifact passing a strict whole-array test does not establish portal acceptance.
- Give the submission a **unique filename** and a **short note (`<= 140` characters)** so submissions are never confused.
- Create an **executive summary subpage** (`docs/executive-summary.html`) as a guide across all sites with an auditable table showing for each site: exact file to download, its score / holdout metric (strictly labeled), portal safety, and whether the file is unique across sites.

### PhD-Level Forensic Analysis & Scientific Hypothesis Mandate

1. **Study, analyze, and understand `0.2778`:** Investigate `GEMSDOE32` (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`: `0.2778` USER/OWNER-REPORTED, no receipt binding it to the file hash) and whether a new strategy can exceed it. The latest local public-board snapshot is dated 2026-10-28 00:05 UTC (#5 `0.3566`, #1 `0.4544`); it is not a live refresh. Current peer correction says H51-1's `0.115134` fold-local re-emission arm was not the downloadable TIFF; saved-byte static HOLDOUT-DTI was `0.002289` vs B2 `0.004515` on that peer evaluator. Do not infer hidden-score causes or claim a new improvement without evidence.
2. **Hypothesis portfolio (3–5 concrete mechanism families):** Before any model code, screen each candidate against existing source code, scripts, preregistrations, experiment ledgers, and raster registries. Do not call an idea “untried” or novel before this check. For each candidate, specify:
   - Exact layers and the physical signature/transform (plus a named non-fault mimic and a control)
   - Why it could detect an unmapped/blind fault rather than merely re-score mapped faults
   - Exact difference from local and peer prior work, with a cited status (implemented, tested, registered/deferred, or unresolved)
   - Implementation cost and official-source availability/provenance; distinguish public landing pages from verified current data bytes/coverage
   - Expected HOLDOUT-DTI/leaderboard effect only when supported by validated evidence. Otherwise state “not estimated”; qualitative feasibility is not a score forecast.
   If fewer than three candidates clear novelty/eligibility, report that negative result rather than relabeling prior art.

### Parallel-Run Protocol (Strict)

1. **LANE:** Stay inside the single pre-registered method paragraph (`registry/preregistration_htcads.json`). If rank-correlation with any registry raster exceeds `0.90`, or more than `70%` of emitted dots fall within `3 px` of any registry raster's dots (no control exception), log as duplicate and stop. Check BOTH on the continuous surface before placement AND on the final dots.
2. **REUSE, DON'T REBUILD:** Reuse the template's cached feature stack, `evaluate_holdout.py`, and `submission_writer.py`. Holdout = hide-and-recover: withhold whole fault segments with a buffer, derive every catalogue-based feature only from visible faults, mask visible faults pixel-exactly, and score pooled DTI (`alpha = 0.2`, `beta = 0.8`, `300 m` triangular kernel). Fix shared tool bugs in the template and report them; never keep a private fork.
3. **LABEL EVERY NUMBER:** Strictly label every metric as `HOLDOUT-DTI (evaluator version, N withheld positives, 95% CI)` or `ORGANIZER-CONFIRMED (copied from submission-page receipt)`. Never write a projection as a score.
4. **LEAKAGE CANARY:** Test each feature alone on holdout first; single-feature `AUC > 0.90` is leakage until proven otherwise.
5. **RUN CARD:** Produce one current JSON Run Card (`evidence/current_run_card.json`; prior cards are archived and superseded): `hypothesis`, `mechanism`, `named_non_fault_mimic`, `holdout_dti` + `ci`, `correlation/overlap vs registry`, `raster_sha256`, `validator_output`, `submission_name` + `<=140`-char `note`, and `verdict` (`promote` or `negative` — negative results are valid deliverables).
6. **BUDGET:** Stop after `3` experiments or `2` hours. Do not directly spend live weekly slots.

### Workflow & Delivery

- Preserve this prompt and Arena Core Values in `README.md` as the starting point for future sessions.
- Verify every claim, file hash, calculation, and official URL line by line with zero hallucinations; flag any irregularities.
- Execute **3 verification passes** (Pass 1: complete implementation & verification; Pass 2: review & fix bugs, missing requirements, and edge cases; Pass 3: final accuracy, completeness, and quality check), then open and merge a Pull Request onto `main`.

### Session Addenda (fulfilment record — newest first)

- **Session 4 (2026-10-29, focus-nine source/prior-art review):** Refreshed current public GitHub HEADs for all nine focus repositories; all differ from the historical score-table refs. Preserved the G28 0.2710 and G31 0.2708 score/file attribution conflicts. The G32 H51-1 0.115134 fold-local arm is not its downloadable TIFF; the peer's saved-byte static recheck is 0.002289 vs B2 0.004515, and the peer candidate fails its literal r13 lattice gate. Five physically distinct geological mechanism families were screened against local/peer source, scripts, preregistrations, ledgers, and available raster registries; none is cleared as novel/eligible. Frozen 82.3418% witness bound >70% stops all local work before fitting, holdout, surface/dots, or TIFF. Experiments/holdouts/slots = 0/0/0; no score estimate; candidate/download NONE; **DO NOT SUBMIT**. See `evidence/review_20261029.md`, `evidence/submission_table_20261029.json`, and `research/2026-10-29_focus-nine-hypotheses.md`.

- **Session 3 (2026-10-27, KG2-S3 GMV):** Forensic mandate fulfilled in `research/2026-10-27_gmv_forensic_02778.md` (0.2778 = precision surgery on the shared H19-5 manifold; path past it = off-manifold discovery, not more pruning); hypotheses mandate fulfilled in `knowledge/03_preregistered_hypotheses_gmv_20261027.md` (5 ranked, top-2 implemented and validated: H1 geomorph HOLDOUT-DTI HR Δ+0.0184 CI+, H2 vent corridors no incremental value). Three GMV experiments ran in 716 s (budget: 3 exp / 2 h); verdict **negative** on SGMC significance + uniqueness vs own retracted file ([run card](evidence/gmv_run_card_20261027.json)). No GMV file emitted; this lane concurs with main's fail-closed DO-NOT-SUBMIT decision (Session-2 DSLUP promotion superseded by the literal rule). Latest local board snapshot: 2026-10-28T00:05Z, #1 = 0.4544, #5 = 0.3566, #25 = 0.3195 (`docs/data/public_leaderboard.json`).


## 2026-10-28 repeated-request review

Read the superseding [review](evidence/review_20261028.md) before archived lane claims. The current request repeats the unique-TIFF requirement, nine-site executive comparison, autonomous scientific research, three review passes, and PR/merge request. It supplies no new single-method lane paragraph. It does not authorize relaxing the all-registry duplicate stop, spending a weekly slot, or claiming a projection as a score. The request's 0.3195 and 0.4413 leaderboard targets conflict with each other and are not current verified measurements. The review preserves these requirements as a condensed record, not a verbatim transcript. No new training run was authorized or performed.
