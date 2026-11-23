-- The lifecycle inputs each attempt's grade application read (mvp-0.66, retired items replay at the right point in
-- history; docs/reviews/algorithm-mvp-0.66.md).
--
-- A grade's relative coverage and its legacy breadth denominator count the facets of its learning object's ACTIVE
-- items (required_facets). Retiring, parking, superseding or removing a sibling item changes that set, and nothing in
-- the attempt ledger records when: replay saw today's flags for the whole history, so an unattempted retired sibling
-- looked closed before its closure and an attempted one looked open after it. From mvp-0.66 the live grade
-- application reads the set once, uses it for both, and stores it here in the attempt's own transaction; replay and
-- regrade read it back instead of today's flags (and never write or replace a row).
--
-- Additive: one new table (RAW_LEDGER in db.table_roles, never cleared by replay; DENIED to adaptive difficulty, like
-- the incumbent's other grade-application state). Nothing is backfilled here: the upgrade to mvp-0.66 records, for
-- every attempt without a row, the set the predecessor's own replay reads at that attempt (basis
-- 'legacy_reconstructed': a reconstruction from the lifecycle as it stood at the upgrade, never observed history),
-- then rebuilds. Below mvp-0.66 nothing writes or reads the table.
--
-- attempt_id: one row per attempt, written after the attempt's own row in the same transaction.
-- learning_object_id: the learning object the set was read for (replay uses the row only for that one).
-- required_facets_json: the set, as a sorted JSON list of facet ids (its canonical iteration order).
-- basis: 'captured_at_application' (written by the live grade application) or 'legacy_reconstructed' (the upgrade).
-- policy_version: how the set was read ('active_item_evidence_facets_v1': the evidence facets of the learning
-- object's items whose serving row is active or absent).
-- recorded_at: when the row was written (a capture time; it orders nothing and reaches no hash).
CREATE TABLE attempt_lifecycle_inputs (
  attempt_id TEXT PRIMARY KEY REFERENCES practice_attempts(id),
  learning_object_id TEXT NOT NULL,
  required_facets_json TEXT NOT NULL,
  basis TEXT NOT NULL CHECK (basis IN ('captured_at_application', 'legacy_reconstructed')),
  policy_version TEXT NOT NULL,
  recorded_at TEXT NOT NULL
);
