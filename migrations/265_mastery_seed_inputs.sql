-- The seed each learning object's mastery started from (mvp-0.67, the mastery seed a topic started from is recorded
-- and replayed; docs/reviews/algorithm-mvp-0.67.md).
--
-- A learning object's mastery row is created once, from the learner claims then in force (vault sync, an attempt on a
-- learning object that has no row yet, or a re-anchoring claim on one), and nothing re-seeds it after: a later
-- starting-level change only replaces the claim, by the profile setter's explicit contract. Replay instead seeded a
-- practised learning object from the claims made before its first attempt and an attempt-free one from the claims in
-- force at rebuild time, so a rebuild after such a change disagreed with live. From mvp-0.67 the writer that first
-- persists a learning object's mastery records here, in the same transaction, every claim it considered; replay
-- seeds from the record and applies only the re-anchoring claims made after it.
--
-- Additive: one new table (RAW_LEDGER in db.table_roles, never cleared by replay; DENIED to adaptive difficulty, like
-- the incumbent's other mastery inputs). Nothing is backfilled here: the upgrade to mvp-0.67 records, for every
-- learning object without a row, the claims the predecessor's own rebuild seeds it from (basis
-- 'legacy_reconstructed': a reconstruction, never observed history; when it was first materialized is unknown), then
-- rebuilds. Below mvp-0.67 nothing writes or reads the table.
--
-- learning_object_id: one row per learning object (an authored id: learning objects are vault content, not rows).
-- claims_made_json: every covering claim the seed considered, replaced ones included (a replaced re-anchoring claim
-- still bounds the seed's variance), each with the fields the seed reads and whether it was in force; a JSON list in
-- (created_at, id) order. Empty for a cold start with no claim on record.
-- selected_claim_id: the claim whose level seeded the mean, or NULL for the cold start.
-- materialized_at: when the mastery row was first persisted; NULL when unknown (a legacy reconstruction).
-- basis: 'captured_at_materialization' (written by the writer that persisted the row) or 'legacy_reconstructed'.
-- policy_version: how the seed reads the claims ('covering_claims_seed_v1': the most specific in-force claim's level,
-- the variance bounded by every earlier re-anchoring claim's seed, the vault's mastery settings at replay).
-- recorded_at: when the row was written (it orders nothing and reaches no hash).
CREATE TABLE mastery_seed_inputs (
  learning_object_id TEXT PRIMARY KEY,
  claims_made_json TEXT NOT NULL,
  selected_claim_id TEXT,
  materialized_at TEXT,
  basis TEXT NOT NULL CHECK (basis IN ('captured_at_materialization', 'legacy_reconstructed')),
  policy_version TEXT NOT NULL,
  recorded_at TEXT NOT NULL
);
