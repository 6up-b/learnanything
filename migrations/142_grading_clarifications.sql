-- Measurement A8 (spec_measurement_efficiency_v1 §3.A8): one clarification
-- question that resolves grading uncertainty.  Implementation plan item 6.3.
-- Authorized by the causal principle-8 amendment already in tree.
--
-- WHY THIS IS NOT A LEARNER TAX.  causal §1 principle 8 forbids spending learner
-- effort on MACHINE-resident uncertainty -- grader flakiness, a missing item
-- contract, symbolic correctness the CAS could settle, an unmapped repair class.
-- That prohibition is unchanged.  What this table serves is the other kind:
-- LEARNER-resident uncertainty -- what the learner meant by an ambiguous
-- notation, whether a skipped step was fluency or a gap, which of two methods
-- they believed they were using.  That information exists only in the learner's
-- head; no machine effort recovers it, and the alternatives are to guess (a
-- harmful write) or to discard the measurement (a wasted attempt).
--
-- THE POINT IS THE ABSTENTION DISCIPLINE, not coverage.  Today abstaining
-- forfeits the measurement entirely, so there is standing pressure on the grader
-- to fill in a guess -- which is the disease P0-P2 exists to cure.  If an
-- abstention can be repaired by one question, honest uncertainty stops costing
-- anything and the over-fill incentive drops at its source.  A8 REINFORCES the
-- abstention discipline; it does not compete with it.
--
--
-- TWO TABLES, BOTH APPEND-ONLY, BECAUSE STATUS IS DERIVED.
--
-- The obvious design is one row with a mutable `status`.  It is the wrong one
-- here: a clarification is a record of an exchange, and causal §1 principle 9
-- ("historical evidence is immutable; replay reproduces state") applies to it
-- exactly as it applies to grading evidence.  So the request is one immutable
-- row, the answer is another, and the status is a pure function of the two plus
-- the clock:
--
--   answered   -- a response row exists
--   timed_out  -- no response and now > expires_at
--   pending    -- otherwise
--
-- That is what makes replay reproduce the RESOLVED grade rather than re-asking
-- (§3.A8's own requirement): the resolved grade lives in `grading_evidence` as a
-- new revision superseding the provisional one, and the exchange that produced
-- it is still here to explain why.
--
-- AN UNANSWERED CLARIFICATION TIMES OUT TO THE ABSTENTION THAT TRIGGERED IT,
-- never to a guess.  That is structural rather than enforced: the provisional
-- grade already recorded the abstention/hedge, so a timeout writes nothing at
-- all.  There is no code path from "the learner ignored the question" to a
-- filled-in diagnosis, because nothing here writes a grade.
CREATE TABLE grading_clarifications (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL REFERENCES practice_attempts(id) ON DELETE CASCADE,
  -- The hedged or abstained criterion the question is about.  Nullable: an
  -- attribution-level abstention ("I cannot name what went wrong") is not scoped
  -- to one criterion, and forcing one would be fabricated structure.
  criterion_id TEXT,
  -- Which of the three §3.A8 uncertainty shapes this is.  Closed vocabulary
  -- with an explicit `other` arm, per the standing "no new enum without an
  -- abstention arm" constraint.
  reason TEXT NOT NULL CHECK (reason IN (
    'ambiguous_notation',
    'skipped_step',
    'correct_answer_possibly_invalid_reasoning',
    'method_ambiguity',
    'other'
  )),
  -- What actually licensed the question: which signal on the provisional grade
  -- was hedged or abstained.  A confident grade can never produce a row here
  -- (that would make it an interrogation), and this column is the record of
  -- which non-confident signal it was.
  trigger TEXT NOT NULL CHECK (trigger IN (
    'hedged_criterion',
    'abstained_attribution',
    'low_grader_confidence'
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

CREATE INDEX idx_grading_clarifications_pending
  ON grading_clarifications(expires_at, attempt_id);

CREATE TRIGGER grading_clarifications_no_update
BEFORE UPDATE ON grading_clarifications
BEGIN
  SELECT RAISE(ABORT, 'grading clarifications are append-only; answers go in grading_clarification_responses');
END;


-- The learner's answer.  Separate table so the request stays immutable, and so
-- "was this ever answered" is a join rather than a mutable flag that a failed
-- regrade could leave lying.
--
-- This one is insert-then-stamp-once rather than strictly append-only, and the
-- ordering is deliberate: the answer is written the moment the learner gives it,
-- and the regrade outcome is stamped on afterwards.  Writing the row only after
-- a successful regrade would lose the learner's words to a provider outage --
-- and the answer is the un-backfillable half of this exchange (standing
-- constraint 6), while the regrade can always be re-run.  DELETE is forbidden;
-- the answer text itself is never rewritten by any code path here.
CREATE TABLE grading_clarification_responses (
  id TEXT PRIMARY KEY,
  clarification_id TEXT NOT NULL REFERENCES grading_clarifications(id) ON DELETE CASCADE,
  answer_md TEXT NOT NULL,
  -- The grading revision the re-grade produced, once it lands.  Null means the
  -- answer is recorded but the re-grade has not completed -- which is a real,
  -- observable state (provider outage) and must not be indistinguishable from
  -- "never answered".
  resolved_grading_revision INTEGER,
  -- Whether the answer actually resolved the uncertainty.  `abstained` is a
  -- first-class outcome: a learner may answer and STILL leave the grader unable
  -- to name a cause, and recording that as unresolved is what stops A8 from
  -- becoming a machine for manufacturing resolutions.
  outcome TEXT CHECK (outcome IN ('resolved', 'abstained', 'regrade_failed')),
  created_at TEXT NOT NULL,
  UNIQUE(clarification_id)
);

CREATE TRIGGER grading_clarification_responses_no_delete
BEFORE DELETE ON grading_clarification_responses
BEGIN
  SELECT RAISE(ABORT, 'clarification responses are append-only');
END;
