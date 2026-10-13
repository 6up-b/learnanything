-- mvp-0.15 (the valid-alternative gate for proofs and explanations; built on
-- branch grading/proof-alternatives as 185 while main's merge chain was adding
-- 181-183, so expect renumbering at the merge): a clarification may be
-- licensed by the independent route check.
--
-- On a proof-like item the route check re-derives the learner's own route on
-- a second model. When it finds valid a step the grader marked down with a
-- quoted error, the criterion is unverified (PF-c's unassessed type) and the
-- grade provisional. A question goes to the learner only when the checker
-- says the dispute turns on what the LEARNER meant (ambiguous notation, a step
-- skipped as obvious, which method they intended): A8's learner-resident
-- uncertainty. A dispute about whether a written step is valid is
-- machine-resident and never asks (causal principle 8). None of the three
-- existing triggers names this licence honestly, so the CHECK gains
-- 'route_check_disagreement'.
--
-- SQLite cannot widen a CHECK in place, so the append-only table is rebuilt
-- with every row, index and trigger as migration 142 created them (unchanged
-- through 184); only the trigger CHECK gains the new value. Foreign keys are
-- off for the rebuild (the responses table cascades on delete), and the
-- responses' foreign key names the table, so it resolves to the rebuilt one.
PRAGMA foreign_keys = OFF;

DROP TRIGGER grading_clarifications_no_update;

CREATE TABLE grading_clarifications_new (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL REFERENCES practice_attempts(id) ON DELETE CASCADE,
  -- The hedged, abstained or disputed criterion the question is about.
  -- Nullable: an attribution-level abstention ("I cannot name what went
  -- wrong") is not scoped to one criterion, and forcing one would be
  -- fabricated structure.
  criterion_id TEXT,
  -- Which of the §3.A8 uncertainty shapes this is.  Closed vocabulary with an
  -- explicit `other` arm, per the standing "no new enum without an abstention
  -- arm" constraint.
  reason TEXT NOT NULL CHECK (reason IN (
    'ambiguous_notation',
    'skipped_step',
    'correct_answer_possibly_invalid_reasoning',
    'method_ambiguity',
    'other'
  )),
  -- What actually licensed the question: which signal on the provisional grade
  -- was hedged, abstained or (mvp-0.15) disputed by the independent route
  -- check on a point that turns on the learner's meaning.  A confident,
  -- undisputed grade can never produce a row here.
  trigger TEXT NOT NULL CHECK (trigger IN (
    'hedged_criterion',
    'abstained_attribution',
    'low_grader_confidence',
    'route_check_disagreement'
  )),
  question_md TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  grading_prompt_version TEXT,
  agent_run_id TEXT,
  created_at TEXT NOT NULL,
  -- ONE question per attempt (§3.A8's bound, enforced by the schema rather than
  -- by a check in a service that a second caller could forget).
  UNIQUE(attempt_id)
);

INSERT INTO grading_clarifications_new(
  id, attempt_id, criterion_id, reason, trigger, question_md, expires_at,
  grading_prompt_version, agent_run_id, created_at
)
SELECT
  id, attempt_id, criterion_id, reason, trigger, question_md, expires_at,
  grading_prompt_version, agent_run_id, created_at
FROM grading_clarifications;

DROP TABLE grading_clarifications;
ALTER TABLE grading_clarifications_new RENAME TO grading_clarifications;

CREATE INDEX idx_grading_clarifications_pending
  ON grading_clarifications(expires_at, attempt_id);

CREATE TRIGGER grading_clarifications_no_update
BEFORE UPDATE ON grading_clarifications
BEGIN
  SELECT RAISE(ABORT, 'grading clarifications are append-only; answers go in grading_clarification_responses');
END;
