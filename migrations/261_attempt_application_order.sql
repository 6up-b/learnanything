-- The order in which attempts were applied (mvp-0.65, same-second grades replay in the order they were applied;
-- docs/reviews/algorithm-mvp-0.65.md).
--
-- An attempt's id is minted when grading starts and its created_at (whole seconds) when its grade is applied, so two
-- grades of one learning object applied in one second can carry ids in the opposite order from their application.
-- Every prefix reader ordered attempts by (created_at, id), so replay could fold them in another order than live did.
-- From mvp-0.65 apply_attempt reserves the next sequence here inside its own write transaction, before it computes
-- the attempt, and the ledger's order is (created_at, sequence, id): occurrence time stays first and the sequence only
-- breaks ties inside one created_at. A rollback takes the reservation with it; a retry of an attempt that already has
-- a row keeps it; a regrade or a replay never writes one (a regrade is not a new observation).
--
-- Additive: one new table (RAW_LEDGER in db.table_roles, never cleared by replay; PROTECTED to adaptive difficulty,
-- by the attempt it names). Nothing is backfilled here: the upgrade to mvp-0.65 ranks every attempt that has no row in
-- the predecessor's (created_at, id) order, basis 'legacy_order_unknown' (the order they were really applied in was
-- never recorded, and nothing stored recovers it), then rebuilds. Below mvp-0.65 nothing writes or reads the table.
--
-- sequence: INTEGER PRIMARY KEY without AUTOINCREMENT. Rows are never deleted (a RAW_LEDGER table), and a rolled-back
-- reservation leaves no row, so the next rowid is always above every row that exists, which is all the order needs;
-- AUTOINCREMENT would only add sqlite_sequence, an internal table every schema diff and backup would then carry.
-- attempt_id: one row per attempt. The reservation precedes the attempt's own row in the same transaction, so the
-- foreign key is checked at commit (DEFERRABLE INITIALLY DEFERRED).
-- basis: 'applied' (reserved by apply_attempt) or 'legacy_order_unknown' (ranked by the upgrade).
-- algorithm_version: the vault's tag when the row was written. recorded_at: when it was written (a capture time; it
-- orders nothing and reaches no hash).
CREATE TABLE attempt_application_order (
  sequence INTEGER PRIMARY KEY,
  attempt_id TEXT NOT NULL UNIQUE REFERENCES practice_attempts(id) DEFERRABLE INITIALLY DEFERRED,
  basis TEXT NOT NULL CHECK (basis IN ('applied', 'legacy_order_unknown')),
  algorithm_version TEXT NOT NULL,
  recorded_at TEXT NOT NULL
);
