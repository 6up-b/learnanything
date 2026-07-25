-- Causal-attribution P2 (§5.3, principle 8): record HOW a causal hypothesis
-- reached its repair class, and WHY it failed to.
--
-- `repair_class_id` is the only vocabulary allowed to say that two plausible
-- causes need different help; facets are the vocabulary under indictment. With
-- the facet fallback correctly removed, an unmapped hypothesis makes a cause set
-- `incomplete_repair_mapping` — a machine-side backfill obligation. Stored as a
-- bare NULL that obligation is unroutable: "author a repair for this episode",
-- "re-target the authored repair", "disambiguate two rival repairs", and
-- "localize the hypothesis" are four different remedies and only the reason
-- distinguishes them.
--
-- Both columns are nullable and back-fill as NULL on historical rows, which
-- reads as "provenance not recorded" rather than as any particular verdict.
-- `causal_hypotheses` is append-only (migration 118 installs UPDATE/DELETE
-- ABORT triggers), so a later re-materialization appends a new VERSION carrying
-- the resolved mapping instead of rewriting the row that recorded the gap.

ALTER TABLE causal_hypotheses ADD COLUMN repair_class_basis TEXT;
ALTER TABLE causal_hypotheses ADD COLUMN repair_class_unresolved_reason TEXT;

-- The backfill queue: concrete hypotheses still owed a repair-class mapping.
CREATE INDEX idx_causal_hypotheses_repair_gap
  ON causal_hypotheses(learning_object_id, repair_class_unresolved_reason)
  WHERE repair_class_id IS NULL AND status != 'open_set';
