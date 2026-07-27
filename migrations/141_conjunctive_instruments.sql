-- Measurement A1 + A6 (spec_measurement_efficiency_v1 §3.A1 / §3.A6):
-- conjunctive instruments and the trace-evidence channel that discharges A1's
-- first guard.  Implementation plan items 6.1 and 6.2.
--
-- WHY THE TWO SHIP TOGETHER.  A1 lets one criterion declare `supporting`
-- targets -- facets the step it owns *consumes* -- and a pass then credits them
-- as embedded evidence.  That is the single largest lever on §0's
-- cells-per-question denominator, and it is also the one change in the document
-- that manufactures positive smearing: the passed-facet firewall (causal §1
-- principle 5) protects only the negative direction, and nobody contests being
-- told they know something.  §3.A1 guard 1 is what stops it -- supporting
-- credit confers nothing unless the graded trace shows the facet actually
-- exercised -- and the observation it requires is exactly what A6 produces.
-- Shipping A1's schema without A6's would mean every supporting target
-- permanently unexercised; shipping A6 without A1's guard would mean the
-- observation has no consumer.
--
--
-- 1. trace_exercised_facets -- A6's raw observation log.
--
-- The grader already reads the whole natural-language trace.  A6 lets it report
-- facets it saw *exercised* beyond the item's declared set.  Three bounds, all
-- structural rather than conventional, and all visible in this DDL:
--
--   * POSITIVE ONLY.  There is no polarity column and no negative arm.
--     Opportunistic evidence may credit a facet; it may never indict one.
--     Indicting a facet the item did not intend to measure is precisely the
--     smearing principle 5 forbids, and there is no criterion to appeal to.
--   * SUPPORTING AT MOST.  `role` is a one-value CHECK rather than the
--     two-value vocabulary used everywhere else, so an observation from this
--     channel cannot become primary by a later code change that forgets why.
--     It therefore lands as embedded credit under A1's cap.
--   * NEVER CERTIFICATION-ELIGIBLE ON ITS OWN (§5.3).  Enforced downstream by
--     the embedded-share cap; recorded here so the provenance survives.
--
-- This is a RAW LOG, not derived state: it is what the grader said it saw,
-- stamped with the run that said it, and `rebuild-derived-state` must project
-- from it rather than recompute it (there is no provider call on the replay
-- path, so a recompute would silently drop every observation).  It is therefore
-- append-only and lives alongside `grading_evidence`, not alongside
-- `facet_capability_evidence`.
--
-- `capability` is deliberately NOT recorded.  Standing constraint 8 says an
-- instrument's evidence is bounded by the capability it actually observes, and
-- the capability a trace observation counts at is decided by the criterion's
-- own authored target -- a deterministic quantity -- never by the grader's
-- report, which is a model-reported one.  Letting the grader name the cell
-- would invert constraint 8's ladder.  The facet is the whole observation.
CREATE TABLE trace_exercised_facets (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL REFERENCES practice_attempts(id) ON DELETE CASCADE,
  facet_id TEXT NOT NULL,
  -- 'declared' when the facet is already in the item's contract (the grader
  -- confirming what the item intended to measure), 'opportunistic' when it is
  -- not.  Kept separate because the A6 revert criterion -- "opportunistic
  -- credit concentrates on a few facets" -- is a statement about the second
  -- population only.
  observation_scope TEXT NOT NULL CHECK (observation_scope IN ('declared', 'opportunistic')),
  role TEXT NOT NULL DEFAULT 'supporting' CHECK (role = 'supporting'),
  -- The grader's own words for what in the trace showed the facet exercised.
  -- Required: an observation with no citation is an assertion, and this channel
  -- exists precisely because the model is reporting rather than deciding.
  evidence TEXT NOT NULL,
  -- Which criterion's work the observation was seen in, when the grader
  -- localizes it.  Null is honest and common: the trace is one artifact.
  criterion_id TEXT,
  -- Where the observation came from.  'grader_trace' is A6; the column exists
  -- so a later channel (a teach-back artifact, a probe dialogue turn) is
  -- separable rather than pooled into A6's revert criterion.
  source TEXT NOT NULL DEFAULT 'grader_trace',
  agent_run_id TEXT,
  grading_prompt_version TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(attempt_id, facet_id, source)
);

CREATE INDEX idx_trace_exercised_facets_attempt
  ON trace_exercised_facets(attempt_id, facet_id);
CREATE INDEX idx_trace_exercised_facets_facet
  ON trace_exercised_facets(facet_id, observation_scope, created_at);

CREATE TRIGGER trace_exercised_facets_no_update
BEFORE UPDATE ON trace_exercised_facets
BEGIN
  SELECT RAISE(ABORT, 'trace exercised-facet observations are append-only');
END;


-- 2. facet_capability_evidence -- the audit columns A1's guards need.
--
-- `certification_credit` already exists and stays the ONE number
-- `capability_grid` reads for Demonstrated.  What it could not previously say
-- is how much of itself came from embedded observations, which is exactly the
-- question guard 2 answers: no cell may take more than
-- `[evidence.certification].max_embedded_credit_share` of its credit from
-- embedded evidence, so a cell whose entire history is supporting credit is not
-- demonstrated -- it is inferred, and Part II already has an honest label for
-- that.  Storing the split makes the cap auditable after the fact instead of
-- only reproducible by re-running the projection.
ALTER TABLE facet_capability_evidence
  ADD COLUMN direct_certification_credit REAL NOT NULL DEFAULT 0;
ALTER TABLE facet_capability_evidence
  ADD COLUMN embedded_certification_credit REAL NOT NULL DEFAULT 0;
-- Guard 1's typed record: mass that a `supporting` target would have earned had
-- the trace shown its facet exercised.  "Recorded, not silent" is the spec's
-- wording -- this is the recording.  It is also the measurement that tells an
-- author whether their supporting targets are honest: a cell accumulating large
-- unexercised mass is an item claiming to consume a facet it never touches.
ALTER TABLE facet_capability_evidence
  ADD COLUMN unexercised_supporting_mass REAL NOT NULL DEFAULT 0;

-- Existing rows predate the split.  Attributing their whole credit to `direct`
-- would be a fabrication in the safe direction and `embedded` a fabrication in
-- the unsafe one, so both stay 0 and the next projection -- which rebuilds this
-- table whole from the immutable observation ledger (`replace_canonical_facet_state`
-- DELETEs and re-INSERTs) -- fills them from the real allocation.  Until then
-- the split reads as "not yet measured", which it is.
