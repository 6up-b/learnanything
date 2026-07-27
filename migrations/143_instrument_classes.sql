-- Measurement A2/A3/A4/A5 (spec_measurement_efficiency_v1 §3.A2-§3.A5): the four
-- remaining instrument classes of Part I.  Implementation plan item 6.4.
-- (A7 is DEMOTED by the plan and is not built; E4 is dropped.)
--
-- WHY THREE TABLES AND NOT FOUR.  Each class owes a MEASURABLE revert criterion
-- -- §3's whole discipline is that "a rung kept on judgement is exactly what the
-- spec forbids" -- and a criterion is measurable only if the observation it needs
-- is durably recorded at the moment it happens.  Three of the four need a new
-- record; A2 needs none:
--
--   * A5 discrimination profiles -- revert if the `no_profile_applies` rate
--     collapses toward zero.  That rate is a property of GRADING outcomes, which
--     nothing today records: the grade stores which criterion failed, never which
--     candidate cause structure the trace matched.  Table 1.
--   * A4 contrast pairs -- revert if within-pair outcome differences are
--     dominated by ORDER effects, "check by randomizing which member is served
--     first".  Randomization is a decision made at serving time and is gone by
--     the time the attempts are read; a rate recomputed from attempt timestamps
--     would measure the order the learner chose, not the order the system
--     offered.  Table 2.
--   * A3 error hunts -- revert if the gate "passes items that real learners solve
--     by proofreading -- detectable as error-hunt outcomes uncorrelated with the
--     same learner's constructed-response outcomes on the same facet".  That
--     needs per-planted-error outcomes, and it needs the CLEAN-solution arm kept
--     separate, because a false-positive report on correct work is the one
--     outcome that must not read as a facet failure.  Table 3.
--   * A2 laddered stems -- revert if cross-column outcomes on one stem correlate
--     as tightly as within-column ones.  Every input already exists: the stem id
--     is `evidence_fingerprint.shared_stimulus_id` on the item, the column is the
--     item's own `capability`, and the outcomes are `practice_attempts`.  A table
--     here would be derived state wearing a ledger's clothes, so there is none.
--
-- All three are APPEND-ONLY.  They are records of what happened (what the grader
-- matched, what the scheduler offered, what the learner repaired), and causal §1
-- principle 9 -- historical evidence is immutable, replay reproduces state --
-- applies to them exactly as it applies to grading evidence.


-- 1. discrimination_profile_matches -- A5's grading-time outcome, both tails.
--
-- §3.A5: an item authors, per plausible candidate hypothesis, what a holder of
-- that hypothesis visibly produces; the diagnostician may match the trace against
-- that candidate set "and must be free to reject" it.  The discipline that keeps
-- the feature from becoming the disease it treats is stated in the same
-- paragraph: a profile INFORMS diagnosis and never CONSTRAINS it, and
-- `no_profile_applies` is "a first-class outcome carrying the same weight as any
-- named match".
--
-- First-class here means representable, recordable, and countable.  So the
-- outcome column has no default and no null arm: every graded attempt on a
-- profile-bearing item lands on exactly one of the arms below, and the arm that
-- says "none of your authored profiles describe this learner" is stored the same
-- way as the arm that names one.  A schema in which the no-match case were the
-- absence of a row would make the revert criterion uncomputable -- the
-- denominator would be missing precisely on the tail being watched.
CREATE TABLE discrimination_profile_matches (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL REFERENCES practice_attempts(id) ON DELETE CASCADE,
  practice_item_id TEXT NOT NULL,
  outcome TEXT NOT NULL CHECK (outcome IN (
    -- The trace matched one authored profile.  `profile_id` is required.
    'matched',
    -- Profiles were offered and the diagnostician rejected all of them.  This is
    -- the arm §3.A5 protects; standing constraint 2 says watch BOTH tails, and a
    -- rate that collapses toward zero here is the model matching the nearest
    -- authored profile rather than reading the trace.
    'no_profile_applies',
    -- The item authored no profiles, so no judgement was asked for.  Kept
    -- separate from `no_profile_applies` because pooling them would let an
    -- unauthored pool look like a healthy rejection rate.
    'no_profiles_offered',
    -- Profiles were offered and the grader returned nothing at all (an older
    -- prompt version, a provider that dropped the field).  An abstention arm the
    -- vocabulary owes itself: silence is not rejection.
    'not_reported'
  )),
  -- The authored profile id, present exactly on the `matched` arm.  Not a foreign
  -- key: profiles live in vault YAML on the item, and the vault is not in this
  -- database.  The id is validated against the item's authored profiles before
  -- the row is written.
  profile_id TEXT,
  -- The registry belief the matched profile names, when it has one.  Denormalized
  -- deliberately: a profile can be retired or reworded on the item, and a match
  -- record that could no longer say WHICH belief it meant would be unreadable
  -- history.
  misconception_id TEXT,
  -- The grader's citation from the trace.  Required on a match for the same
  -- reason A6 requires one: a match with no citation is an assertion, and this
  -- channel exists because the model is reporting rather than deciding.
  evidence TEXT,
  -- Whether the attempt was ultimately graded as a failure.  The two-tailed rate
  -- is only meaningful over failures -- a profile describing what a WRONG answer
  -- looks like has nothing to say about a correct one -- and recomputing this
  -- from the attempt later would key on a `rubric_score` that a regrade can move.
  attempt_failed INTEGER NOT NULL CHECK (attempt_failed IN (0, 1)),
  grading_prompt_version TEXT,
  agent_run_id TEXT,
  created_at TEXT NOT NULL,
  -- One judgement per attempt.  A regrade re-reports and is ignored by the
  -- INSERT OR IGNORE writer, so the first judgement survives -- the record is of
  -- what the grader said, and a record that can be rewritten is not evidence.
  UNIQUE(attempt_id)
);

CREATE INDEX idx_discrimination_profile_matches_outcome
  ON discrimination_profile_matches(outcome, created_at);
CREATE INDEX idx_discrimination_profile_matches_profile
  ON discrimination_profile_matches(profile_id, outcome);

CREATE TRIGGER discrimination_profile_matches_no_update
BEFORE UPDATE ON discrimination_profile_matches
BEGIN
  SELECT RAISE(ABORT, 'discrimination profile matches are append-only');
END;


-- 2. contrast_pair_servings -- A4's order-effect control, recorded at the
--    moment the order is decided.
--
-- §3.A4: "Revert if within-pair outcome differences are dominated by order
-- effects -- check by randomizing which member is served first."  Two facts have
-- to survive to make that checkable, and neither is recoverable afterwards:
--
--   * WHICH member the system offered first (the learner may work the queue out
--     of order, so attempt timestamps measure the learner's choice, not the
--     manipulation);
--   * that the choice was actually RANDOM.  A randomization nobody can audit is
--     indistinguishable from a constant, and the whole control rests on it, so
--     the seed the decision was drawn from is stored beside the decision.
--
-- The seed is the scheduler's existing deterministic-fraction input (session id
-- + pair key), not a fresh random draw: the scheduler must produce the same slate
-- twice for the same session, and a nondeterministic seed here would make the
-- queue unreproducible for a control that exists to remove a nuisance parameter.
CREATE TABLE contrast_pair_servings (
  id TEXT PRIMARY KEY,
  -- The pair identity: `contrast_of` resolves both members to one key (the
  -- lexicographically smaller item id), so the two rows of one pair join.
  pair_key TEXT NOT NULL,
  practice_item_id TEXT NOT NULL,
  -- 0 = offered first in this session's queue, 1 = offered second.  An integer
  -- rather than a boolean `served_first`, so a pair that somehow acquires a third
  -- member is representable as data instead of silently mis-recorded.
  serve_position INTEGER NOT NULL CHECK (serve_position >= 0),
  -- The other member, so a single row is readable without a self-join.
  counterpart_item_id TEXT NOT NULL,
  session_id TEXT,
  -- The deterministic seed the coin flip was drawn from, and the flip's result.
  -- Stored together so an auditor can both recompute the draw and count the
  -- realized balance across sessions -- the two different ways this can fail.
  randomization_seed TEXT NOT NULL,
  randomization_value REAL NOT NULL CHECK (
    randomization_value >= 0.0 AND randomization_value <= 1.0
  ),
  -- Whether the two members were separated in the queue rather than served
  -- adjacent.  §3.A4 forbids adjacency "unless the surfaces differ enough that
  -- the manipulation is not salient": a visible contrast measures "spots the
  -- manipulation", a facet nobody has.  Recorded rather than assumed, because the
  -- separation is a scheduling outcome and a queue too short to separate them is
  -- a real state.
  separated INTEGER NOT NULL CHECK (separated IN (0, 1)),
  -- Why adjacency was permitted or could not be avoided.  Closed vocabulary with
  -- an explicit abstention arm, per the standing "no new enum without an
  -- abstention arm" rule.
  adjacency_basis TEXT NOT NULL CHECK (adjacency_basis IN (
    'separated_by_interleaving',
    'surfaces_differ_sufficiently',
    'queue_too_short_to_separate',
    'unknown'
  )),
  created_at TEXT NOT NULL,
  -- One serving record per (item, session).  Re-planning the same session's
  -- queue -- which `build_due_queue` does on every call -- must not multiply the
  -- record, and the first decision is the one the learner saw.
  UNIQUE(practice_item_id, session_id)
);

CREATE INDEX idx_contrast_pair_servings_pair
  ON contrast_pair_servings(pair_key, created_at);

CREATE TRIGGER contrast_pair_servings_no_update
BEFORE UPDATE ON contrast_pair_servings
BEGIN
  SELECT RAISE(ABORT, 'contrast pair servings are append-only');
END;


-- 3. error_hunt_outcomes -- A3's per-attempt result, with the clean-solution arm
--    kept structurally distinct.
--
-- §3.A3 plants errors from the misconception registry and the facet payload's
-- `error_signatures` ("a freehand error is an untyped instrument"), requires the
-- REPAIR rather than the flag, does not declare the error count, and "rotates in
-- clean solutions".  The rotation is the part with teeth: "a learner who 'finds'
-- an error in a correct solution has just handed you a misconception directly".
--
-- That case is the reason this table exists rather than a JSON blob on the
-- attempt debug payload.  §10 states it as a validation line: a clean-solution
-- error-hunt on which the learner reports an error writes a misconception
-- CANDIDATE, not a facet failure.  Both halves need a durable record -- the
-- candidate id that was written, and the fact that no facet took a negative --
-- or the claim is unverifiable after the fact.
CREATE TABLE error_hunt_outcomes (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL REFERENCES practice_attempts(id) ON DELETE CASCADE,
  practice_item_id TEXT NOT NULL,
  -- 1 when the administered solution carried NO planted errors (the rotation).
  -- Stored rather than derived from `planted_total = 0`, because "this rotation
  -- served the clean variant" and "this item's plants failed to load" are
  -- different events and must not read alike.
  clean_solution INTEGER NOT NULL CHECK (clean_solution IN (0, 1)),
  planted_total INTEGER NOT NULL CHECK (planted_total >= 0),
  -- REPAIRED, not merely flagged.  §3.A3: "Flagging is recognition; repairing is
  -- construction.  This is what keeps the instrument on the right side of the
  -- no-recognition-items gate."  The two counts are separate columns precisely so
  -- that a pool drifting toward flag-only credit is visible instead of pooled
  -- into one "found" number.
  planted_repaired INTEGER NOT NULL CHECK (planted_repaired >= 0),
  planted_flagged_not_repaired INTEGER NOT NULL CHECK (planted_flagged_not_repaired >= 0),
  planted_missed INTEGER NOT NULL CHECK (planted_missed >= 0),
  -- Errors the learner reported that were never planted.  On a seeded solution
  -- this is noise; on a CLEAN one it is the misconception the spec is after.
  false_positive_reports INTEGER NOT NULL CHECK (false_positive_reports >= 0),
  -- The `misconception_candidates` row a clean-solution false positive minted.
  -- Null on every other arm.  Not a foreign key by choice: the candidate store
  -- is promotable and mergeable, and a hard reference would make this history
  -- undeletable rather than merely honest.
  misconception_candidate_id TEXT,
  -- The explicit record that the clean-solution path took no facet negative.
  -- §10's line is about what did NOT happen, and an invariant nobody can query is
  -- an invariant nobody can regress-test.
  facet_failure_suppressed INTEGER NOT NULL DEFAULT 0
    CHECK (facet_failure_suppressed IN (0, 1)),
  grading_prompt_version TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(attempt_id)
);

CREATE INDEX idx_error_hunt_outcomes_item
  ON error_hunt_outcomes(practice_item_id, created_at);
CREATE INDEX idx_error_hunt_outcomes_clean
  ON error_hunt_outcomes(clean_solution, created_at);

CREATE TRIGGER error_hunt_outcomes_no_update
BEFORE UPDATE ON error_hunt_outcomes
BEGIN
  SELECT RAISE(ABORT, 'error hunt outcomes are append-only');
END;
