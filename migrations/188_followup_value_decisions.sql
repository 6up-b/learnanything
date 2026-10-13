-- mvp-0.17 (value-of-information stopping), Codex re-review F1: one immutable
-- receipt per follow-up decision the value rule takes part in. A source
-- attempt can be decided more than once (an automatic decision, then the
-- learner's manual follow-up from the feedback screen; a generation need
-- recorded, then a later evaluation once a candidate exists), so each
-- decision gets its own id and ordinal, keeping its source-attempt link.
-- The follow-up's decision_features row (one per source attempt, first write
-- wins) cannot hold the later decisions, and attempt_surprise's gate
-- diagnostics are DERIVED (a rebuild drops them).
--
-- decision_json is the value decision (voi_stopping.SiteDecision.as_dict:
-- the candidates' forecasts, the served candidate's complete forecast and how
-- it was served, the heuristic parameters, the former cap's counterfactual);
-- NULL when there was no candidate to value (a generation need recorded).
-- RECEIPT: written once by the live follow-up path, never by a rebuild or a
-- replay, never updated or deleted (triggers). Below mvp-0.17, or with
-- voi_stopping.followups off, nothing writes it. Numbered 188 as a
-- placeholder (184-186 are held by other branches in flight; main's 184
-- voi_forecasts may absorb these rows at the merge).
CREATE TABLE followup_value_decisions (
  id TEXT PRIMARY KEY,
  source_attempt_id TEXT NOT NULL,
  -- 1, 2, ... per source attempt, in decision order.
  decision_ordinal INTEGER NOT NULL CHECK (decision_ordinal >= 1),
  learning_object_id TEXT NOT NULL,
  session_id TEXT,
  -- queued_diagnostic | queued_non_diagnostic_review |
  -- suppressed_voi_value_below_minutes_cost | created_need_for_generation |
  -- created_need_no_discriminator
  decision_outcome TEXT NOT NULL,
  -- The value decision's verdict; NULL when no candidate was valued.
  verdict TEXT CHECK (verdict IS NULL OR verdict IN ('continue', 'stop')),
  manual_override INTEGER NOT NULL DEFAULT 0 CHECK (manual_override IN (0, 1)),
  recommended_ref TEXT,
  served_ref TEXT,
  need_id TEXT,
  candidate_count INTEGER NOT NULL DEFAULT 0 CHECK (candidate_count >= 0),
  forecast_version TEXT,
  decision_json TEXT,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (source_attempt_id, decision_ordinal)
);
CREATE INDEX idx_followup_value_decisions_lo
  ON followup_value_decisions(learning_object_id, created_at);

CREATE TRIGGER followup_value_decisions_immutable_update BEFORE UPDATE ON followup_value_decisions
BEGIN SELECT RAISE(ABORT, 'follow-up value decisions are immutable'); END;
CREATE TRIGGER followup_value_decisions_immutable_delete BEFORE DELETE ON followup_value_decisions
BEGIN SELECT RAISE(ABORT, 'follow-up value decisions are immutable'); END;
