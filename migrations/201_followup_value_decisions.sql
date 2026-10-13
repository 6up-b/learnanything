-- mvp-0.21 (value-of-information stopping), Codex re-review F1: one immutable
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
-- replay, never updated or deleted (triggers). Below mvp-0.21, or with
-- voi_stopping.followups off, nothing writes it. Built as migration 188 (a
-- placeholder) and renumbered 201 when it merged onto main after 184-199.
-- Main's voi_forecasts (184) also records each value decision as a forecast
-- (site followup_value_decision, behind evsi.forecast_logging); this table
-- stays the decision's own receipt, which serving reads back.
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

-- Codex final verify F12: a vault that ran the successor before this table
-- existed kept each follow-up value decision on the follow-up's
-- decision_features row (context_json.voi_stopping, one row per source
-- attempt). Each becomes this table's first decision on its attempt, with a
-- stable identity derived from that row ('legacy_decision_features:' || id),
-- its source-attempt link, and its body marked backfilled_from. The reader
-- (voi_stopping.followup_receipts) reads only this table, so a legacy
-- decision is counted exactly once; a later decision on the same attempt is
-- ordinal 2. mvp-0.16 follow-up rows (no voi_stopping body) are not value
-- decisions and are not copied.
INSERT OR IGNORE INTO followup_value_decisions(
  id, source_attempt_id, decision_ordinal, learning_object_id, session_id,
  decision_outcome, verdict, manual_override, recommended_ref, served_ref,
  need_id, candidate_count, forecast_version, decision_json, algorithm_version,
  created_at
)
SELECT
  'legacy_decision_features:' || df.id,
  df.decision_id,
  1,
  COALESCE(
    json_extract(df.context_json, '$.voi_stopping.learning_object_id'),
    (SELECT pa.learning_object_id FROM practice_attempts pa WHERE pa.id = df.decision_id),
    ''
  ),
  json_extract(df.context_json, '$.voi_stopping.context.session_id'),
  COALESCE(json_extract(df.context_json, '$.decision_outcome'), 'legacy_unrecorded'),
  CASE
    WHEN json_extract(df.context_json, '$.voi_stopping.decision') IN ('continue', 'stop')
      THEN json_extract(df.context_json, '$.voi_stopping.decision')
  END,
  CASE WHEN json_type(df.context_json, '$.manual_trigger') IN ('object', 'array', 'text', 'true') THEN 1 ELSE 0 END,
  json_extract(df.context_json, '$.voi_stopping.recommended_ref'),
  json_extract(df.context_json, '$.voi_stopping.served_ref'),
  json_extract(df.context_json, '$.need_id'),
  MAX(COALESCE(CAST(json_extract(df.context_json, '$.voi_stopping.candidate_count') AS INTEGER), 0), 0),
  json_extract(df.context_json, '$.voi_stopping.forecast_version'),
  json_set(
    json_extract(df.context_json, '$.voi_stopping'),
    '$.backfilled_from', 'decision_features.context_json.voi_stopping'
  ),
  df.algorithm_version,
  df.created_at
FROM decision_features df
WHERE df.decision_type = 'followup'
  AND json_valid(df.context_json)
  AND json_type(df.context_json, '$.voi_stopping') = 'object'
ORDER BY df.created_at, df.id;

CREATE TRIGGER followup_value_decisions_immutable_update BEFORE UPDATE ON followup_value_decisions
BEGIN SELECT RAISE(ABORT, 'follow-up value decisions are immutable'); END;
CREATE TRIGGER followup_value_decisions_immutable_delete BEFORE DELETE ON followup_value_decisions
BEGIN SELECT RAISE(ABORT, 'follow-up value decisions are immutable'); END;
