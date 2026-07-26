-- Augmentation A2 (spec_diagnostic_augmentation_v1 §2 A2): the mechanism
-- taxonomy keys on REPAIR AND MEASUREMENT NEED, not on the grader's lexical
-- habits.
--
-- `mint_causal_mechanism_taxonomy` grouped on the exact `operation` string, so
-- `dropped_sign`, `sign_dropped` and `lost_negative_branch` were three
-- singletons that all abstained and then minted as three mechanisms once counts
-- grew.  §9's own criterion -- a cluster earns an id only when it "predicts a
-- distinct repair or measurement need" -- was never applied to §6.1.  A
-- mechanism distinction that changes no repair and no probe is a synonym.
--
-- WHY A DURABLE REPAIR-CLASS DEFINITION TABLE.  The new grouping key needs the
-- repair class's *definition*, and `repair_class_id` cannot supply it for two
-- reasons:
--
--   * The id is a content hash whose payload includes `episode_id`
--     (`_repair_class`, equivalence_scope `episode_repair_equivalence`), so two
--     episodes needing the identical repair carry two different ids.  Grouping
--     on the id directly yields singletons forever -- the abstention arm would
--     swallow the whole taxonomy and look like honest caution.
--   * The definition itself lived ONLY inside the diagnosis receipt in
--     `attempt_debug_payloads`, which `services/replay.py` rebuilds.  A
--     taxonomy key read from a rebuildable payload silently changes meaning
--     after a rebuild -- the same argument migration 130 makes for the
--     discriminating-observation receipt.
--
-- So the definition becomes durable, append-only data, and each row carries a
-- `repair_equivalence_id`: the content hash of (operator, target refs, preserve
-- refs) with `episode_id` and the model's own `expected_minutes` /
-- `answer_reveal_budget` excluded.  That is the cross-episode "same help"
-- relation the A2 key needs.  Model self-reports are excluded deliberately: A1
-- demoted them to tie-breakers because ordering on a noisy self-estimate
-- maximizes the wrong thing, and keying an append-only taxonomy on a float the
-- model volunteered would fragment synonyms right back apart.
--
-- Rows are content-addressed, so an insert of an existing id is a no-op rather
-- than a conflict, and the table is append-only for the same reason
-- `causal_hypotheses` is: the definition that selected a repair is the audit
-- record of that decision.

CREATE TABLE causal_repair_class_definitions (
  repair_class_id TEXT PRIMARY KEY,
  -- Cross-episode "same help" relation. NOT unique: many episode-scoped repair
  -- classes share one equivalence id, which is exactly the collapse A2 wants.
  repair_equivalence_id TEXT NOT NULL,
  -- The episode the class was minted for, kept for provenance. It is part of
  -- `repair_class_id`'s hash and deliberately NOT part of the equivalence id.
  episode_id TEXT NOT NULL,
  operator TEXT NOT NULL,
  repair_policy_version TEXT NOT NULL,
  target_refs_json TEXT NOT NULL,
  preserve_refs_json TEXT NOT NULL,
  -- Model self-reports, recorded because A1's receipts consume them as
  -- tie-breakers; never part of either id.
  expected_minutes REAL,
  answer_reveal_budget REAL NOT NULL DEFAULT 0.0,
  definition_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX idx_causal_repair_class_equivalence
  ON causal_repair_class_definitions(repair_equivalence_id, created_at, repair_class_id);

CREATE TRIGGER causal_repair_class_definitions_no_update
BEFORE UPDATE ON causal_repair_class_definitions
BEGIN
  SELECT RAISE(ABORT, 'causal repair class definitions are append-only');
END;

CREATE TRIGGER causal_repair_class_definitions_no_delete
BEFORE DELETE ON causal_repair_class_definitions
BEGIN
  SELECT RAISE(ABORT, 'causal repair class definitions are append-only');
END;

-- RETIRING THE WRONG-KEY TAXONOMIES.  Migration 119 makes taxonomy versions and
-- their assignments append-only, so the assignments minted under
-- `exact_operation_v1` cannot be rewritten and must not be deleted: receipts
-- pin a taxonomy version id, and replaying one has to resolve the taxonomy that
-- actually labelled it.  Retirement is therefore a sibling append-only fact
-- rather than a status edit: pinned reads keep working, and
-- `latest_active_causal_mechanism_taxonomy` -- the only path by which a NEW
-- receipt acquires a taxonomy -- skips retired versions.  Until a fresh
-- `learnloop build-causal-taxonomy --activate` runs, new receipts carry no
-- taxonomy version, which is the honest state: no active taxonomy exists.
CREATE TABLE causal_mechanism_taxonomy_retirements (
  taxonomy_version_id TEXT PRIMARY KEY
    REFERENCES causal_mechanism_taxonomy_versions(id),
  reason TEXT NOT NULL,
  retired_at TEXT NOT NULL
);

CREATE TRIGGER causal_mechanism_taxonomy_retirements_no_update
BEFORE UPDATE ON causal_mechanism_taxonomy_retirements
BEGIN
  SELECT RAISE(ABORT, 'causal mechanism taxonomy retirements are append-only');
END;

CREATE TRIGGER causal_mechanism_taxonomy_retirements_no_delete
BEFORE DELETE ON causal_mechanism_taxonomy_retirements
BEGIN
  SELECT RAISE(ABORT, 'causal mechanism taxonomy retirements are append-only');
END;

-- Retire every taxonomy minted under the string key. `created_at` is reused as
-- `retired_at` so the retirement carries no fabricated timestamp: a migration
-- has no clock, and the A2 verdict applies to the row from the moment it was
-- written, not from the moment the migration ran.
INSERT INTO causal_mechanism_taxonomy_retirements(
  taxonomy_version_id, reason, retired_at
)
SELECT id, 'wrong_grouping_key_exact_operation_v1', created_at
  FROM causal_mechanism_taxonomy_versions
 WHERE algorithm = 'exact_operation_v1';
