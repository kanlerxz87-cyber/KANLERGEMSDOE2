# Standing Project Brief & Parallel-Run Protocol (`KANLERGEMSDOE2`)

> **Epistemic Integrity Note (Zero Hallucinations):** This file preserves the complete standing project brief, 9-site / 92-site audit mandate, Parallel-Run Protocol (Rules 1–6), and Arena Core Values (**Maximize P(Win)** and **Own the Outcome**) governing `kanlerxz87-cyber/KANLERGEMSDOE2`. Read this brief together with `README.md` at the start of every session before writing code or running experiments.

---

## Core Values

- **Maximize P(Win):** Optimize expected leaderboard and Phase 2 ($250k / $395k expert-reviewed evaluation) return per scarce submission slot. Never burn a weekly slot on cosmetic edits, duplicate `H19-5` clones, or candidates that fail to beat the spatially-blocked holdout benchmark.
- **Own the Outcome:** Automated code gates — never manual human inspection — verify `[0, 1]` GeoTIFF range safety, zero NaNs, leakage canaries, registry uniqueness, and holdout statistical significance end-to-end. Fix shared template defects at the root and document every irregularity and negative result transparently.

---

## Standing Project Prompt Record

Review the repo and execute any open next steps first.

Focus on the highest-scoring submissions from the following 9 focus sites:
- `GEMSDOE24`, `GEMSDOE25`, `GEMSDOE27`, `GEMSDOE28`, `GEMSDOE30`, `GEMSDOE31`, `GEMSDOE32`, `GEMSDOE33`, `GEMSDOE36` (and cross-check against all ~65+ listed GEMSDOE/KANLER/EUG/WBG/GINNY sites across the fleet, including `KANLERGEMSDOE2`: `kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros` and `kanlergems2-ldah-exp-2-37654dots-20261027T021500Z-0ab4d26c-zeros`).

**THE FOLLOWING IS THE HIGHEST URGENCY AND MUST BE FOLLOWED:**
- **MUST GENERATE A UNIQUE `.TIF` SUBMISSION FOR THE COMPETITION.** Do not copy a previous submission unless it is strictly for learning and forensic baseline comparison.
- **IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT THE GENERATED `.TIF` SUBMISSION** at the top of the GitHub Pages site and executive summary subpage, validated automatically in code **without human intervention**.
- **Fix submission portal error:** `"Predicted values must be in range [0, 1]"` (single-band float32 GeoTIFF matching `sample_submission.tif` CRS `EPSG:32611`, `3730 x 3292` shape, and `100 m` Affine geotransform, with `0` NaNs and all values strictly in `[0, 1]`).
- Give the submission a **unique filename** and a **short note (`<= 140` characters)** so submissions are never confused.
- Create an **executive summary subpage** (`docs/executive-summary.html`) as a guide across all sites with an auditable table showing for each site: exact file to download, its score / holdout metric (strictly labeled), portal safety, and whether the file is unique across sites.

### PhD-Level Forensic Analysis & Scientific Hypothesis Mandate

1. **Study, analyze, and understand `0.2778`:** Explain why and how `GEMSDOE32` (`https://buffedlizard55-lab.github.io/GEMSDOE32/`, `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`: `0.2778` `ORGANIZER-CONFIRMED`) achieved the highest score across the focus sites, and whether/how a new strategy can score higher (`> 0.2778`, targeting `#5 = 0.3195` and public `#1 = 0.4413`).
2. **Pre-Implementation Hypotheses (3–5 Untried Geological Hypotheses):** Emphasizing scientific discovery of geothermal vents and unmapped faults, propose 3–5 concrete hypotheses before writing model code, specifying for each:
   - Exact layer(s) involved
   - Physical fault signature or mathematical transform targeted (plus named non-fault mimic process)
   - Why it catches faults missing from the USGS/INGENIOUS catalogue rather than already-mapped ones
   - How it differs from prior implementations across the GEMSDOE fleet
   - Rank by expected DTI improvement vs. implementation cost, checking free official external data obtainability before proposing as viable.

### Parallel-Run Protocol (Strict)

1. **LANE:** Stay inside the single pre-registered method paragraph (`registry/preregistration_htcads.json`). If rank-correlation with any registry raster exceeds `0.90`, or more than `70%` of emitted dots fall within `3 px` of any registry detector raster's dots, log as duplicate and stop. Check BOTH on the continuous surface before placement AND on the final dots.
2. **REUSE, DON'T REBUILD:** Reuse the template's cached feature stack, `evaluate_holdout.py`, and `submission_writer.py`. Holdout = hide-and-recover: withhold whole fault segments with a buffer, derive every catalogue-based feature only from visible faults, mask visible faults pixel-exactly, and score pooled DTI (`alpha = 0.2`, `beta = 0.8`, `300 m` triangular kernel). Fix shared tool bugs in the template and report them; never keep a private fork.
3. **LABEL EVERY NUMBER:** Strictly label every metric as `HOLDOUT-DTI (evaluator version, N withheld positives, 95% CI)` or `ORGANIZER-CONFIRMED (copied from submission-page receipt)`. Never write a projection as a score.
4. **LEAKAGE CANARY:** Test each feature alone on holdout first; single-feature `AUC > 0.90` is leakage until proven otherwise.
5. **RUN CARD:** Produce one JSON Run Card (`evidence/run_card.json`): `hypothesis`, `mechanism`, `named_non_fault_mimic`, `holdout_dti` + `ci`, `correlation/overlap vs registry`, `raster_sha256`, `validator_output`, `submission_name` + `<=140`-char `note`, and `verdict` (`promote` or `negative` — negative results are valid deliverables).
6. **BUDGET:** Stop after `3` experiments or `2` hours. Do not directly spend live weekly slots.

### Workflow & Delivery

- Preserve this prompt and Arena Core Values in `README.md` as the starting point for future sessions.
- Verify every claim, file hash, calculation, and official URL line by line with zero hallucinations; flag any irregularities.
- Execute **3 verification passes** (Pass 1: complete implementation & verification; Pass 2: review & fix bugs, missing requirements, and edge cases; Pass 3: final accuracy, completeness, and quality check), then open and merge a Pull Request onto `main`.
