-- P1 compatibility projections filter latest hypothesis heads by LO,
-- normalized statement, and status. Keep that read path bounded while legacy
-- candidate consumers are retired.
CREATE INDEX idx_causal_hypotheses_projection
  ON causal_hypotheses(
    learning_object_id, statement_normalized, status, episode_key, version
  );
