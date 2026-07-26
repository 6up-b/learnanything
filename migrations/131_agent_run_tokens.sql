-- Token accounting on agent runs (spec_diagnostic_augmentation_v1.md §2 A7).
--
-- `agent_runs` dates from 001 and records WHICH model ran, with which prompt
-- version, over which context hash -- but never what the call cost. §3 C3 makes
-- `tokens_per_resolved_diagnostic_episode` the revert criterion for the
-- augmented diagnostic loop: if the richer receipt costs more per resolved
-- episode than it buys, the loop reverts. Without a per-run token column that
-- ratio has no numerator, so the criterion is unmeasurable and the guardrail is
-- decorative. v1 §11 scheduled these under P3; they land in Phase A because a
-- run completed before the columns exist carries no usage anywhere else -- the
-- provider response is gone by then (standing constraint 6: not backfillable).
--
-- NAMING follows `reader_background_requests` (093), the only table that already
-- tracks tokens: est_/actual_ x input_/output_. A second convention over the
-- same quantity would make the cost rollup a union of two spellings.
--
-- est_* are the pre-flight budget the caller committed to (0 when the caller
-- does not budget); actual_* are what the provider reported, summed over every
-- model call the run made -- a run is one logical episode but several requests
-- (JSON repair rounds, sharded synthesis, per-window ingest), so the write path
-- accumulates per-client and drains once at completion. 0 is therefore
-- "unreported or free", never "unknown": NOT NULL DEFAULT 0 keeps the rollup a
-- plain SUM with no COALESCE, and providers that expose no usage (the local
-- app-server adapter) stay at 0 rather than poisoning the average with NULL.
--
-- Reasoning/cached tokens are deliberately NOT separate columns: no consumer
-- exists for the split yet (standing constraint 2 -- no schema growth without a
-- second consumer), and the codex SDK folds reasoning output into its
-- `outputTokens` breakdown already.

ALTER TABLE agent_runs ADD COLUMN est_input_tokens INTEGER NOT NULL DEFAULT 0;
ALTER TABLE agent_runs ADD COLUMN est_output_tokens INTEGER NOT NULL DEFAULT 0;
ALTER TABLE agent_runs ADD COLUMN actual_input_tokens INTEGER NOT NULL DEFAULT 0;
ALTER TABLE agent_runs ADD COLUMN actual_output_tokens INTEGER NOT NULL DEFAULT 0;

-- The C3 rollup slices by purpose over a time window ("grading" /
-- "grading_regrade" runs against resolved diagnostic episodes); without this the
-- ratio is a full scan of every run the vault has ever made.
CREATE INDEX idx_agent_runs_purpose_completed
  ON agent_runs(purpose, completed_at);
