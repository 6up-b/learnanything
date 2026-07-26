-- A6 "the system must be able to say it was wrong"
-- (spec_diagnostic_augmentation_v1.md §2 A6; implementation_plan_v1.md item 1.4).
--
-- THE MISSING EDGE.  v1 already gives the learner a contest action (§5.6
-- `doesnt_fit`) and already gives the system a demotion lifecycle
-- (`misconception_disposition_events`, migration 116: `demoted` / `superseded`
-- with history preserved).  The two are not connected in the LEARNER's
-- direction: a diagnosis can be asserted to the learner's face, later retired
-- as a misdiagnosis, and the learner is left holding a false claim about their
-- own mind.  That is the failure mode `harmful_write_rate` (§3 B5) exists to
-- measure, and silent retraction is the version of it that undoes the win.
--
-- SCOPE GUARD, and why it needs a stored flag rather than a query.  A6 narrates
-- ONLY beliefs the learner actually saw.  Retiring an internal provisional
-- hypothesis nobody was shown is housekeeping; narrating it is noise.  "Was
-- surfaced" is capture-now data (standing constraint 6) — after the fact there
-- is no way to reconstruct which claims reached a viewport, so the flag is
-- written at presentation time and never backfilled.  Pre-existing rows keep
-- `surfaced_to_learner = 0`: they predate the capture and we decline to guess.
--
-- WHY THE FLAG LIVES ON `hypothesis_events` rather than in a new table.
-- Migration 055 already models exactly one thing: a typed claim PRESENTED to
-- the learner on a named surface, with `visible_at` set by the UI's
-- IntersectionObserver (components/ClaimSurface.tsx) and `suppression_reason`
-- set when the attention budget swallowed the card.  A separate "surfaced"
-- table would duplicate that row and immediately be able to disagree with it.
-- The columns below make the existing presentation row self-describing instead.

-- 1 iff this presentation actually reached the learner: dispatched with
-- affordances (`suppression_reason IS NULL`) AND reported visible.  A suppressed
-- card was authored, not shown, and must never trigger an apology.
ALTER TABLE hypothesis_events
  ADD COLUMN surfaced_to_learner INTEGER NOT NULL DEFAULT 0;

-- The claim IN THE WORDS THE LEARNER WAS SHOWN.  A6 requires naming the
-- previous claim verbatim, and the underlying belief's `statement` is mutable
-- (re-authored by synthesis) and its row is deletable, so quoting the live
-- statement at correction time would put words in the learner's memory that
-- were never on their screen.  The presenting surface already computes this
-- string (`statementPairText` / `statementPairCopy`); the sidecar already
-- accepted it as `claim_text` and then dropped it on the floor.  Now it lands.
ALTER TABLE hypothesis_events ADD COLUMN claim_text_as_shown TEXT;

-- The NORMALIZED belief reference, resolved at capture time.
--
-- WHY NOT JUST JOIN ON `claim_ref`.  `claim_ref` is caller-shaped and the two
-- production surfaces that present a diagnosis disagree about its shape:
--   * ReviewScreen.tsx  → claimRef = "<misconceptionId>"                  (bare id)
--   * FeedbackScreen.tsx → claimRef = {"attemptId":…,"misconceptionId":…}  (JSON)
-- and `canonical_claim_ref` json-encodes the second, so an equality join
-- against `misconception_disposition_events.misconception_id` silently matches
-- the Review presentations and silently misses every Feedback one.  Half the
-- surfaced beliefs would never be apologised for and nothing would report it.
-- Normalizing once, at the moment of capture, makes the A6 join a plain
-- equality join and keeps the lossy parsing in one audited place.
ALTER TABLE hypothesis_events ADD COLUMN belief_kind TEXT;
ALTER TABLE hypothesis_events ADD COLUMN belief_id TEXT;

-- The A6 lookup: "was this belief ever shown, and in what words".  Partial on
-- the flag because the correction path only ever reads surfaced rows, and the
-- overwhelming majority of presentations are estimates/policies with no belief.
CREATE INDEX idx_hypothesis_events_surfaced_belief
  ON hypothesis_events(belief_kind, belief_id, created_at, id)
  WHERE surfaced_to_learner = 1;

-- A demotion that hands the learner a REPLACEMENT belief is the exact case A6
-- forbids handling quietly: "never quietly re-state it as a weaker belief
-- instead".  Recording the successor next to the disposition is what lets the
-- feed narrate the withdrawal FIRST and the replacement second, instead of
-- letting a softened restatement stand in for the retraction.  No FK, matching
-- `diagnosis_adjudications.attempt_id` (126): the audit row must outlive
-- whatever projection owns the successor.
ALTER TABLE misconception_disposition_events
  ADD COLUMN replacement_misconception_id TEXT;

-- Migration 116's only index is keyed on `misconception_id`; the review feed
-- enumerates dispositions chronologically across all beliefs.
CREATE INDEX idx_misconception_disposition_events_at
  ON misconception_disposition_events(created_at, id);

-- THE TYPED WITHDRAWAL REASON, and why it is not a new CHECK constraint.
--
-- A6 names four reasons the learner may be told: contradicted by trace /
-- superseded / adjudicated / retired as misdiagnosed.  Migration 116's
-- `disposition` CHECK admits two values (`demoted`, `superseded`) and sits on a
-- table guarded by no-update/no-delete triggers, so widening the enum would
-- mean recreating the table and re-writing immutable audit rows — a worse trade
-- than the one below.  Instead the pair (`disposition`, `reason`) carries it:
--
--   disposition='superseded'                  → superseded
--   disposition='demoted', reason=<typed token> → that token
--
-- `services/surfaced_beliefs.py` owns the vocabulary, validates every NEW write
-- into `reason`, and maps the one legacy free-text reason migration 116 itself
-- backfilled (`first_error_trace_had_no_durable_promotion_authority`, which is
-- an authority defect, NOT a trace contradiction) through an explicit alias
-- table rather than substring guesswork.
