-- Post-reveal admissibility, and the channel a discriminating observation came
-- from.
--
-- Migration 130 built `causal_discriminating_observations` around ONE producer:
-- a blind-bundle classification of an administered probe. Two things have since
-- changed, and both need a column rather than a convention.
--
-- CHANNEL. Slice 3 records a second kind of row: a falsifiable expectation the
-- learner's own tutor question asserted (`learner_question_embedded`). It is a
-- real observation about the learner's model — it is what they said they
-- expected, in their words, before anyone corrected them — and the ledger is
-- the right home for it. But it is not a probe, and every consumer that counts
-- rows as "probes administered" (`scoreboard.probe_action_change_rate`,
-- `causal_health`) would silently absorb it into a denominator it does not
-- belong in. `channel` is NULL on every pre-existing row and on every blind
-- classification, so readers filter on it explicitly and legacy rows keep
-- meaning exactly what they meant.
--
-- ADMISSIBILITY. `admitted` already answers "did the instrument discriminate?".
-- It cannot answer the separate question this slice raises: was the learner's
-- production INDEPENDENT of what we had already shown them? A learner who was
-- handed the answer (reveal_events, migration 154) and then produces the
-- matching feature vector has demonstrated reading comprehension. Admitting
-- that as discriminating evidence would let a revealed solution close a causal
-- factor — the exact contamination the reveal ledger was built to see.
--
-- The asymmetry that matters: an expectation extracted from the learner's OWN
-- QUESTION stays admissible no matter what has been revealed since. The
-- question was written before the answer existed; it is the learner's model
-- speaking, and post-hoc exposure cannot reach backwards into it.
--
-- All four columns are additive and nullable. A NULL
-- `admissible_as_independent` means "not assessed" (every row written before
-- this migration), which is deliberately distinct from `0` = "assessed and
-- contaminated".

ALTER TABLE causal_discriminating_observations ADD COLUMN channel TEXT;
ALTER TABLE causal_discriminating_observations
  ADD COLUMN admissible_as_independent INTEGER;
ALTER TABLE causal_discriminating_observations
  ADD COLUMN inadmissibility_reason TEXT;
-- The reveal that contaminated the production, so the finding is auditable
-- back to the row that caused it rather than being re-derived from a window.
ALTER TABLE causal_discriminating_observations
  ADD COLUMN contaminating_reveal_event_id TEXT;

CREATE INDEX idx_causal_discriminating_observation_channel
  ON causal_discriminating_observations(channel, created_at, id);
