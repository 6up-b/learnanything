-- Augmentation A5 (spec_diagnostic_augmentation_v1 §2 A5): materialize
-- missing-vocabulary notes.
--
-- Abstention rate is the system's measurement of its OWN vocabulary
-- inadequacy, and it cannot be backfilled (standing constraint 6): every
-- abstention recorded before this store exists is a vocabulary-inadequacy
-- signal lost permanently.  Until now an abstention wrote
-- `resolution_status='abstained'` plus `abstention_reason` on the attribution
-- and stopped there -- a per-attempt fact with no cross-attempt substrate, so
-- the clustering Phase D is supposed to do had nothing to read.
--
-- CAPTURE ONLY.  No clustering, no facet proposals, no review surface: those
-- are Phase D, and shipping them here would mean minting vocabulary from a
-- handful of notes.  What this table owes Phase D is the raw material: the
-- trace, the criterion, the abstention reason, the selected repair class, and
-- the item context, per abstention.
--
-- TWO PRODUCERS, ONE STORE.  §2 A5 names the diagnostic abstention; causal
-- §5.8 rule 4 names the other -- a rung variant that declines to inherit its
-- parent's facets because the canonical vocabulary has no word for what it
-- measures ("an abstention here becomes a missing-vocabulary note (§13)").
-- They are the same signal from opposite ends of the loop (grading cannot name
-- what the learner did / authoring cannot name what the item measures), and
-- clustering them together is the point.  `source` keeps them separable so a
-- cluster drawn only from one end is visible as such.
--
-- VERSION STAMPS mirror the A4 adjudication store's set exactly.  A later
-- cluster has to be able to tell a real vocabulary gap from an artifact of one
-- prompt version or one grader model, and a note that had to re-read a
-- replay-rebuildable payload to answer that would silently change meaning after
-- a rebuild.
--
-- IDS ARE CONTENT-ADDRESSED over (source, subject, reason, versions), so
-- re-materializing an episode -- which happens on every regrade and every
-- replay -- inserts nothing new.  Append-only for the usual reason: a note is
-- the audit record of a refusal, and a refusal that can be edited afterwards is
-- not evidence.

CREATE TABLE missing_vocabulary_notes (
  id TEXT PRIMARY KEY,
  source TEXT NOT NULL CHECK (source IN (
    -- The diagnostician declined to name a cause (§2 A5).
    'diagnostic_abstention',
    -- An authored item declined to name canonical facets (§5.8 rule 4).
    'authoring_facet_abstention'
  )),
  -- The typed refusal itself. For diagnosis this is the grader's
  -- `abstention_reason`; for authoring it is the criterion's
  -- `measurement_status` (`no_canonical_facet` / `item_local`).
  abstention_reason TEXT NOT NULL,

  learning_object_id TEXT,
  practice_item_id TEXT,
  -- Present for the diagnostic arm; null for authoring, which abstains before
  -- any attempt exists.
  attempt_id TEXT,
  error_event_id TEXT,
  criterion_id TEXT,

  -- What could not be named: the learner work / divergence anchor for the
  -- diagnostic arm, the criterion text for the authoring arm.
  trace_json TEXT NOT NULL DEFAULT '{}',
  item_context_json TEXT NOT NULL DEFAULT '{}',

  -- The repair the episode selected despite the abstention. Phase D clusters by
  -- repair equivalence, so the cross-episode id (migration 133) is stored
  -- alongside the episode-scoped one.
  selected_repair_class_id TEXT,
  repair_equivalence_id TEXT,

  grading_prompt_version TEXT,
  decision_policy_version TEXT,
  repair_policy_version TEXT,
  grader_model TEXT,
  grader_provider TEXT,
  grader_provider_revision TEXT,
  agent_run_id TEXT,

  note_version TEXT NOT NULL,
  detail_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);

CREATE INDEX idx_missing_vocabulary_notes_source
  ON missing_vocabulary_notes(source, created_at, id);
-- Phase D's clustering entry point: abstentions for one learning object,
-- grouped by the reason given.
CREATE INDEX idx_missing_vocabulary_notes_lo
  ON missing_vocabulary_notes(learning_object_id, abstention_reason, created_at);
CREATE INDEX idx_missing_vocabulary_notes_repair
  ON missing_vocabulary_notes(repair_equivalence_id, created_at)
  WHERE repair_equivalence_id IS NOT NULL;

CREATE TRIGGER missing_vocabulary_notes_no_update
BEFORE UPDATE ON missing_vocabulary_notes
BEGIN
  SELECT RAISE(ABORT, 'missing vocabulary notes are append-only');
END;

CREATE TRIGGER missing_vocabulary_notes_no_delete
BEFORE DELETE ON missing_vocabulary_notes
BEGIN
  SELECT RAISE(ABORT, 'missing vocabulary notes are append-only');
END;
