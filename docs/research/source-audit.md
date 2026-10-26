# Source and irregularity audit

**Reviewed:** 2026-10-26 UTC. This is a read-only review of the supplied score list and the linked, public, owner-maintained site pages. It does not independently validate any TIFF bytes, owner-reported DTI, or DrivenData submission receipt.

## Evidence hierarchy

1. **Organizer primary source:** DrivenData competition description/rules, data and submission pages, official leaderboard, and a submission-page receipt tied to exact file/hash.
2. **Scientific/official source:** USGS and INGENIOUS primary data/documentation.
3. **Owner-maintained generated site:** valuable for locating files and run cards, but claims are not organizer-confirmed unless accompanied by a checkable organizer receipt. A local `HOLDOUT-DTI` remains a local metric, not a leaderboard result.
4. **Prompt-provided claim:** useful as a hypothesis/benchmark inventory only.

## Specific irregularities to resolve

| Source page | Public page content observed during this review | Irregularity / safe interpretation |
|---|---|---|
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | The current page identifies a newer `DPRF1` local point-best and describes its HOLDOUT-DTI; the user-provided history identifies the older dotted H25 submission as the site's historical leaderboard result. | Different artifact and metric scope. Do not substitute a local holdout result for an organizer score or treat the newest artifact as a scored submission. |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | Current page says no eligible competition TIFF and calls scores/leaderboard estimates unavailable; it also carries many archived experiments. | Supports a conservative no-submit decision, but the historical 0.2600 is still only an owner/prompt claim here. |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | Current front page presents an H31-1 file as passing a site-specific gate; the historical supplied score list refers to the prior topo-gap-closure file. | A site-local selector is not evidence the file passed this project's literal full-registry protocol or a current slot selector. Re-audit byte-bound evidence across the full registry. |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | Current page contains many dated sessions and research TIFFs, with explicit negative/no-submit statuses, while older embedded sections retain alternate results. | Multiple archived decision blocks make “current” ambiguous unless a single timestamped selector record is pinned. The old score list cannot be used as current eligibility. |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | Current landing page says no new submission; it describes a recent GDX-1 negative holdout and research-only artifact. | This is not a current leaderboard improvement and does not authenticate the older score claim. |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | A single page includes several selector/status blocks, including a pseudogravity DO-NOT-SUBMIT entry and later blocks claiming H31-T/H31-X is approved. | Mutually inconsistent or superseded authorization statements appear in one page. Do not select any TIFF from this page without identifying one authoritative latest selector receipt and rechecking all gates. |
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | Current banner states no new file is authorized; it labels the historical 0.2778 score OWNER-REPORT and says no submission receipt ties score to the raster hash. The pinned source archive also contains a later `H33-A..E` experiment module, while the historical winning filename has the alias `h33-h33-2-b2`. | The 0.2778 is not organizer-confirmed on the page. No current upload recommendation is present. The filename does not prove which later H33-A..E formula generated the historic raster; do not conflate the two without a hash-bound source/run record. |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | Current landing content contains several candidate sections; at least one recent section reports negative holdout and no submission approval. | Keep each candidate/run card separate. A “unique TIFF” or “download” label alone does not imply a positive holdout or slot authorization. |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | Current top section labels recent HVG-36/MTO-36 research files negative/do-not-submit and gives local HOLDOUT-DTI; it separately preserves prior 0.2750 as a historical claim. | A local holdout comparison cannot be relabelled as public leaderboard score; recent negative outcomes do not undo or confirm old score receipts. |

## Score discrepancy

The user prompt gives both `0.3195` and `0.4413` as the “current” high score in different places. A fresh read of the official public leaderboard displayed `0.4437` for its first-ranked public entry at review time. Treat the official live page as authoritative for the current public leaderboard snapshot; retain prior values only as dated historical claims. The public leaderboard is not private-round/final-prize evidence.

## What remains unverified

- Exact-byte identity and TIFF internal values for the nine historical files.
- Which organizer receipt, if any, maps each historical owner score to an exact TIFF hash.
- Full registry coverage and the protocol's pre-placement-surface and final-dot correlations/overlaps.
- Reproducibility of published local holdout metrics under one pinned evaluator and one fixed withheld-positive cohort.
- Any current candidate's competitive score or calibration from holdout to leaderboard.

Until these items are reconciled, the status for every historical file in this checkout is **reference only / do not resubmit / uniqueness not established**.
