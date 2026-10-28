# Evidence index and historical status

**Current decision: NEGATIVE / DO NOT SUBMIT.** The sole current run card is
[`current_run_card.json`](current_run_card.json); the current exact-byte
findings are in [`release_recheck_20261027.json`](release_recheck_20261027.json),
[`independent_witness_20261027.json`](independent_witness_20261027.json),
[`dslup_literal_revalidation_20261027.json`](dslup_literal_revalidation_20261027.json),
[`parallel_hypothesis1_literal_audit_20261027.json`](parallel_hypothesis1_literal_audit_20261027.json),
and [`off36_literal_revalidation_20261027.json`](off36_literal_revalidation_20261027.json).
The [three-pass verification](verification_passes_20261027.json) distinguishes
initial checks from the follow-up integration recheck.

Other cards, receipts and reports in this directory are historical records.
Some include **retracted** control-exempt `promote`/`5/5` flags, unverified
"organizer-confirmed" claims, or hidden-truth projections. These are not current
validation and must never be consumed as approval. Some public cards were updated
with a negative verdict and explicit supersession fields; byte-identical originals
are retained under `superseded/` where available. The KG2-S2 validator delegates
to the shared fail-closed validator, which checks actual bytes and cannot authorize
an upload. The public DSLUP card points to the hashed original and carries the
current negative verdict.

Hashes authenticate owner-mirror bytes, not official dataset origin. The
[availability receipt](data_availability_20261027.json) records the incomplete
external restore. Per-site scores are user/owner reports unless an actual
organizer submission-page receipt is explicitly cited. Public leaderboard
snapshots are aggregate observations, not receipts for these files.
