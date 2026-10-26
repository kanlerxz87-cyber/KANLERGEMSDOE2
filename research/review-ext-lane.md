# Three-pass verification — Lane KANLER-EXT-CORROB, 2026-10-26

## Pass 1: implement and verify
- Restored full competition data (training_features 4371c82e…, labels 7ba308cc…, sample 2176d08e… — all sha256 == pinned manifest) via anonymous git sparse clone after the GitHub contents API returned 403 (invalid GH_TOKEN + rate limit). `prepare_data.py` ready=true. Footprint 5,167,373 px; catalogue 60,988 px; sample ones == catalogue exactly (IR-EXT-03).
- Verified from official sources (fetch tool, 2026-10-26): problem/metric/prize structure; public leaderboard top 0.4437 (resolves the prompt's conflicting 0.4413/0.3195 as stale snapshots); staff clarification that known-fault pixels are masked in scoring (community 11516). Thread 11527 staff bodies did not render — not paraphrased.
- Byte autopsy (`champion_forensics.py`): exact nesting champion ⊂ G31 ⊂ D2.8; G25≡G30; G36 = champion+1,200; near-catalogue shares 14.6/6.3/0.0% track the live ladder; NN spacing 2.24 (D1.5) vs 3.0 (D2.8).
- Reproduced prior baselines exactly (champion fixed-mask v3 0.00452, E1 0.02506, SGMC 0.09606/0.07521) and showed fixed-mask hide-recover anti-ranks the B-ladder — gating moved to fold-local emission only.
- Pre-registered 5 hypotheses + 3 experiments + decision rule BEFORE running (`preregistration-ext-corrob.md`). Ran them: CORROB OOF 0.0792 / clean SGMC 0.1015 / callable 0.0499; MCSUP OOF 0.1181; EMIT @44,090 OOF 0.1264 [0.098,0.154]. Canary max AUC 0.5798 (matches E1 run — deterministic). Wrote unique TIF (44,090 dots, all-finite [0,1], receipt PASS, sha 06c56b9a…), run card (negative), selector gate (negative: registry scope + no positive paired CI), rebuilt the Pages site.

## Pass 2: bugs / edge cases found and fixed
- **IR-EXT-01 contamination (critical, self-caught):** EXP2/EXP3 callable hide-recover (0.1598) and final SGMC (0.3288) evaluate the globally trained model on its own positives. Quarantined in card/site; gates use fold-local OOF + SGMC-OOF only. The naive SGMC-ratio estimate (0.39) is explicitly rejected with the direct-SGMC falsification (live 0.0512).
- Committed merge-conflict markers in `scripts/build_site_e1_xg_hgb.py` + `docs/lane-e1-xg-hgb.html` (IR-EXT-05): resolved (E1 side kept; stale builder quarantined to `research/quarantine/prior-scripts/`; lane page now regenerated deterministically).
- Dead .zip links (`{tif}.zip` vs writer's `.zip` suffix swap): fixed; added automated local-link sweep (now clean).
- `tests/test_submission.py` used pytest-style functions silently skipped by unittest/CI: rewritten as TestCase (32 tests now actually run, incl. E1 + EXT TIF checks).
- Two legacy tests encoded the previous session's "no candidate" state (`raster_sha256 is None`, "no TIF under docs/"): rewritten to the durable invariant — negative card + selector never authorize; any published TIF must hash-equal the card raster with passing receipt.
- Independent uniqueness rerun (`audit_uniqueness.py`, dilation method) confirms the KDTree-exact result; independent `validate_raster.py` confirms format; TIF bytes == cached dot mask exactly.

## Pass 3: requirement recheck
- Executive table (file / labelled estimate / uniqueness / submit?) at the top of the site; per-site decisions for all nine focus sites with decoded-raster stats. Download obvious at top with explicit NO verdict. Unique name + 93/140-char note; [0,1] portal error root-caused and machine-proofed. How-to-submit subpage included.
- Protocol: lane stayed single (EXT-CORROB); surface checked before placement and dots after vs 10 rasters (max ρ 0.101, max overlap 39.1% — both pass; scope limit flagged IR-EXT-02 vs the full ~100-site list); shared writer/evaluator reused (no fork); every number labelled HOLDOUT-DTI / OWNER-REPORTED / MODEL ESTIMATE / ORGANIZER-PUBLISHED; canaries before trust; 3/3 experiments then stopped; promotion left to fail-closed selector (no slot approved, none used).
- Not fulfilled (explicit, not disguised): no unique file with evidence of beating 0.2778 exists — two independent lanes converge on ~0.22 MODEL ESTIMATE. Beating 0.2778 / 0.4437 needs GPU segmentation and/or new data fetched off-sandbox (ranked queue published). Full-registry uniqueness certificate and organizer receipts remain outstanding.
- Builder idempotency verified (identical md5 across rebuilds); 32 tests pass.

Verification scope note: data mirrors are sha-pinned but not organizer-authenticated; live scores for new files do not exist and none is claimed.
