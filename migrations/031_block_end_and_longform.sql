-- Probe redesign remainder (spec_probe_eig_redesign.md §5.7/§7.1/§8.2).
--
-- practice_attempts.answer_confidence: the learner's committed answer
-- confidence (1-5), a logged-only observation feature (§7.1). Never consumed
-- by grading or scheduling; NULL when the surface did not ask.
--
-- probe_observations.features_json: logged-only observation features (§7.1)
-- and the long-form structured trace (§8.2): first invalid step, correct
-- prefix, unassessable downstream obligations, and per-element evidence
-- shares. Replay never reads this column; it exists for telemetry and audit.

ALTER TABLE practice_attempts ADD COLUMN answer_confidence INTEGER;

ALTER TABLE probe_observations ADD COLUMN features_json TEXT;
