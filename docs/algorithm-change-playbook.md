# Algorithm-change playbook

Use this process when scoring, scheduling, projection, or admissibility
semantics change. A code change is not complete merely because new attempts use
it; existing vault history must remain interpretable and reproducible.

1. Decide whether the change alters persisted meaning. If it does, add a new
   immediate-successor `algorithm_version` in
   `learnloop.algorithm_versions`. Never silently reuse an old tag.
2. Keep raw ledgers and append-only receipts immutable. Add a correction or
   reinterpretation event when history needs new meaning; do not update the
   original evidence.
3. Add or update the explicit vault-upgrade function. It must refuse jumps,
   prepare the candidate projection before the atomic config rename, and leave
   the prior version readable if preparation fails.
4. Update the effective-default fingerprint keyed by the new version. A default
   change without a version/fingerprint decision is a reproducibility bug.
5. Classify every new table in `learnloop.db.table_roles`. A new `DERIVED` table
   must have exactly one registered rebuild owner; a new `RAW_LEDGER` or
   `RECEIPT` table must never be cleared by replay.
6. Extend replay-completeness and rebuild-equivalence tests. The same-version
   rebuild on the golden fixture must reproduce the same semantic projection,
   ignoring only explicitly documented surrogate IDs and write timestamps.
7. Run a shadow rebuild against a copied database and inspect mastery, facet,
   and scheduling deltas before applying the version to a live vault. Verify the
   live database hash is unchanged.
8. Add or regenerate a fixture at the migration head and exercise the complete
   predecessor-to-successor upgrade path, foreign-key checks, doctor, and a
   second idempotent rebuild.

Changes in `learnloop.substrate.compat` require a separate compatibility
decision and a fixture representing the historical vault shape. They are never
folded into an algorithm bump as incidental cleanup.
