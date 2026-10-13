-- Slice 2 T1 (M3, spec_embedding_consumers_v1 §3): recurrence with authority.
--
-- The three hypothesis_recurrence_* tables are DERIVED: one replayer
-- (substrate.recurrence_groups) clears and rebuilds them from raw ledgers
-- (causal_hypotheses, attempt_diagnoses + their receipts, judgment_ledger,
-- diagnosis_feedback) with no model or embedding call. They are empty unless
-- the mvp-0.12 successor is active and recurrence.enabled is on.
--
-- Written as 172 (successor label mvp-0.11) on slice-2/t1; renumbered to 176
-- and relabelled mvp-0.12 when it merged after 171-175 (mobile M1, Phase 6
-- placement, Phase 5a PF-b, router R0). It touches neither judgment_ledger
-- (R0's 175 rebuilt it; T1's judges are within its CHECK) nor any table those
-- migrations created.

-- Members of MERGED groups only. A statement class that was never merged
-- with another keeps its exact statement_normalized key and has no row here.
CREATE TABLE hypothesis_recurrence_groups (
  episode_key TEXT PRIMARY KEY,
  statement_normalized TEXT NOT NULL,
  group_key TEXT NOT NULL,
  root_episode_key TEXT NOT NULL,
  class_count INTEGER NOT NULL CHECK (class_count >= 2),
  joined_by TEXT NOT NULL CHECK (joined_by IN ('root', 'exact_key', 'citation', 'judgment')),
  joined_by_ref TEXT,
  judge TEXT,
  builder_version TEXT NOT NULL
);
CREATE INDEX hypothesis_recurrence_groups_key ON hypothesis_recurrence_groups(group_key);
CREATE INDEX hypothesis_recurrence_groups_statement ON hypothesis_recurrence_groups(statement_normalized);

-- Cases for review, rebuilt with the groups: refused unions (the no-chaining
-- rule), different verdicts inside one exact-statement class, attempt-level
-- links that name no single statement class, and diagnoses whose registry
-- match differs from the top-1 registry neighbour by embedding (§3.5).
CREATE TABLE hypothesis_recurrence_review (
  id TEXT PRIMARY KEY,
  case_kind TEXT NOT NULL CHECK (
    case_kind IN ('refused_union', 'exact_key_conflict', 'unresolved_link', 'registry_disagreement')
  ),
  left_ref TEXT,
  right_ref TEXT,
  blocking_left_ref TEXT,
  blocking_right_ref TEXT,
  source_ref TEXT,
  occurred_at TEXT,
  detail_json TEXT NOT NULL DEFAULT '{}',
  builder_version TEXT NOT NULL
);
CREATE INDEX hypothesis_recurrence_review_kind ON hypothesis_recurrence_review(case_kind, occurred_at);

-- One row (scope 'vault'): the inputs the current groups were built from (a
-- cheap fingerprint lets normalization skip an unchanged rebuild) and counts.
-- active = 1: the groups are in force (the successor is active and
-- recurrence.enabled is on). active = 0: PREPARED by `upgrade --to mvp-0.12`
-- before its config switch; consumers read no group until activation flips
-- it. No row while the successor is off.
CREATE TABLE hypothesis_recurrence_state (
  scope TEXT PRIMARY KEY,
  input_fingerprint TEXT NOT NULL,
  builder_version TEXT NOT NULL,
  active INTEGER NOT NULL CHECK (active IN (0, 1)),
  group_count INTEGER NOT NULL DEFAULT 0,
  member_count INTEGER NOT NULL DEFAULT 0,
  review_count INTEGER NOT NULL DEFAULT 0
);

-- What an escalated repair showed (§3.7), written once when the diagnosis is
-- applied: the group, the earlier answers cited as evidence, the repair
-- chosen and whether its operator differs from the group's earlier repairs.
-- attempt_id has no foreign key, like the other append-only ledgers (164).
CREATE TABLE recurrence_escalations (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL,
  diagnosis_id TEXT NOT NULL,
  group_key TEXT NOT NULL,
  recurrence_count INTEGER NOT NULL CHECK (recurrence_count >= 1),
  earlier_attempt_ids_json TEXT NOT NULL DEFAULT '[]',
  repair_suggestion_id TEXT,
  repair_operator TEXT,
  prior_operators_json TEXT NOT NULL DEFAULT '[]',
  different_approach INTEGER NOT NULL CHECK (different_approach IN (0, 1)),
  -- Where the shown repair came from: one of the diagnosis's own repairs, a
  -- repair written at escalation time with a different operator and
  -- representation (its payload in repair_json), or none.
  repair_source TEXT NOT NULL DEFAULT 'diagnosis'
    CHECK (repair_source IN ('diagnosis', 'generated', 'none')),
  repair_json TEXT,
  -- The escalated-repair request: whether it ran, and why it was not used.
  generation_json TEXT NOT NULL DEFAULT '{}',
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (attempt_id, diagnosis_id),
  CHECK ((repair_source = 'generated') = (repair_json IS NOT NULL))
);
CREATE INDEX recurrence_escalations_group ON recurrence_escalations(group_key, created_at);
CREATE TRIGGER recurrence_escalations_no_update
BEFORE UPDATE ON recurrence_escalations
BEGIN
  SELECT RAISE(ABORT, 'recurrence_escalations are append-only');
END;
CREATE TRIGGER recurrence_escalations_no_delete
BEFORE DELETE ON recurrence_escalations
BEGIN
  SELECT RAISE(ABORT, 'recurrence_escalations are append-only');
END;

-- The same-answer/different-cause guard's planted cases beyond the built-in
-- suite (an M1 run's cases added with `recurrence guard --from-run`). Once
-- registered, a case is required: the switch to mvp-0.12 needs a verdict on
-- every registered negative from the configured judge (§3.6). Append-only.
CREATE TABLE recurrence_guard_cases (
  case_id TEXT PRIMARY KEY,
  suite_version TEXT NOT NULL,
  expected TEXT NOT NULL CHECK (expected IN ('same', 'different')),
  topic TEXT NOT NULL DEFAULT '',
  problem TEXT NOT NULL DEFAULT '',
  shared_answer TEXT,
  statement_a TEXT NOT NULL,
  statement_b TEXT NOT NULL,
  quote_a TEXT,
  quote_b TEXT,
  source TEXT NOT NULL,
  registered_at TEXT NOT NULL
);
CREATE TRIGGER recurrence_guard_cases_no_update
BEFORE UPDATE ON recurrence_guard_cases
BEGIN
  SELECT RAISE(ABORT, 'recurrence_guard_cases are append-only');
END;
CREATE TRIGGER recurrence_guard_cases_no_delete
BEFORE DELETE ON recurrence_guard_cases
BEGIN
  SELECT RAISE(ABORT, 'recurrence_guard_cases are append-only');
END;

-- Work claims of the shared "same or different?" judge (learnloop.matching):
-- one row per (task, producer, prompt version, input) question. A worker
-- claims it in a short write transaction BEFORE the model call (the call
-- itself runs outside any transaction); a live lease held by another worker
-- makes it skip the pair, an expired lease is re-claimed with a new epoch,
-- and the verdict is appended only while the worker's epoch still holds
-- (completion fencing), so two workers never pay for, or append, the same
-- verdict twice. Mutable workflow state, never replayed.
CREATE TABLE judgment_work_claims (
  claim_key TEXT PRIMARY KEY,
  task TEXT NOT NULL,
  producer TEXT NOT NULL,
  prompt_version TEXT,
  input_hash TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('leased', 'done', 'released')),
  lease_owner TEXT,
  lease_expires_at TEXT,
  lease_epoch INTEGER NOT NULL DEFAULT 0,
  judgment_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

-- diagnosis_feedback gains the escalation usefulness tap (§3.7): the response
-- is prefixed "escalation:". SQLite cannot widen a CHECK in place, so the
-- table is rebuilt with every row and id preserved (164 precedent); DROP TABLE
-- removes the old index and triggers, which are recreated on the renamed
-- table. Its foreign keys are kept exactly as migration 170 declared them.
PRAGMA foreign_keys = OFF;

CREATE TABLE diagnosis_feedback__176 (
  id TEXT PRIMARY KEY,
  diagnosis_id TEXT NOT NULL REFERENCES attempt_diagnoses(id),
  attempt_id TEXT NOT NULL REFERENCES practice_attempts(id),
  response TEXT NOT NULL CHECK (
    response IN (
      'believed_candidate', 'partly', 'slipped', 'diagnosis_wrong', 'unsure', 'not_same_mistake',
      'escalation:helped', 'escalation:didnt_help', 'escalation:not_sure'
    )
  ),
  cited_attempt_id TEXT,
  forwarded_factor_id TEXT,
  shown_at TEXT,
  responded_at TEXT NOT NULL,
  CHECK ((response = 'not_same_mistake') = (cited_attempt_id IS NOT NULL))
);
INSERT INTO diagnosis_feedback__176(
  id, diagnosis_id, attempt_id, response, cited_attempt_id, forwarded_factor_id, shown_at, responded_at
)
SELECT
  id, diagnosis_id, attempt_id, response, cited_attempt_id, forwarded_factor_id, shown_at, responded_at
FROM diagnosis_feedback;

DROP TABLE diagnosis_feedback;
ALTER TABLE diagnosis_feedback__176 RENAME TO diagnosis_feedback;

CREATE INDEX diagnosis_feedback_diagnosis ON diagnosis_feedback(diagnosis_id, responded_at);
CREATE TRIGGER diagnosis_feedback_no_update
BEFORE UPDATE ON diagnosis_feedback
BEGIN
  SELECT RAISE(ABORT, 'diagnosis_feedback is append-only');
END;
CREATE TRIGGER diagnosis_feedback_no_delete
BEFORE DELETE ON diagnosis_feedback
BEGIN
  SELECT RAISE(ABORT, 'diagnosis_feedback is append-only');
END;

PRAGMA foreign_keys = ON;
