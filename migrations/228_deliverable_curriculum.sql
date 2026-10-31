-- Deliverable curriculum C0b: scope resolution and the deliverable path
-- (spec_deliverable_curriculum_v1 §5, §7.1-§7.5, §8.5, §9, §12 C0;
-- docs/reviews/curriculum-c0b-scope-path.md).
--
-- Numbered 228: main's head is 226 and Reader RW6b part 1 holds 227 on its
-- own branch (the migration runner has no contiguity rule; renumbered at
-- landing if needed).
--
-- A deliverable is an existing learner Goal (goals.yaml): no goal object and
-- no kind field here. These tables record HOW the learner scoped it, how
-- that was resolved to learning objects, and the path chosen across books.
--
-- deliverable_scope_inputs (RAW_LEDGER): the learner's own words, one
-- append-only row each: a sentence or text ('text'), a pasted topic list
-- ('topic_list'), a passage of a library source ('passage': span refs only;
-- its text is read through the exam predicate when it is resolved, and an
-- exam-withheld span is refused before a row is written), a correction
-- ("not Jordan form; we skipped it", 'correction': learner text over a
-- delete button) and the depth asked once ('depth', the newest standing).
--
-- deliverable_scope_resolutions (WORKFLOW: paid outputs, never re-run on
-- rebuild): one row per resolution. The resolver (route
-- deliverable_scope_resolver, a pressed action) reads the inputs in order and
-- the vault's active LOs as compact records, and returns the LOs the
-- deliverable needs (each with the phrase of the learner's input it answers)
-- and the phrases it could not match (each with a proposed LO statement).
-- origin 'learner' rows are the learner's own decisions on an unmatched
-- phrase (add it: the created LO joins; no: declined), copied forward from
-- the resolution they decide on. The newest row per goal stands.
--
-- deliverable_path_sections (WORKFLOW, append-only): the curated path across
-- every book, per (goal, depth): for each needed LO one primary section
-- (core, prerequisite, already_shown or assumed), its alternates, an
-- ordinal, a one-line reason and one exercise worth trying. A unique index
-- keeps one judge row per (goal, depth, state_key, LO, section). Learner
-- rows (learner_override set: use_instead, read_anyway, skip, check_later,
-- none) are the learner's verdicts on a path line; the newest per (goal,
-- depth, LO) stands across re-judgments. A check_later row names the Check
-- once commitment it created (DL2's unchanged rule serves it).
--
-- Nothing here is evidence: no scoring, scheduling, projection, grading,
-- serving or replay path reads these tables (C1, the plan following the
-- path, is a successor). Exam and held-out material never reaches the
-- resolver or the path judge. Kill switches: curriculum.enabled and
-- curriculum.coverage_on_extract. Append-only by trigger.
CREATE TABLE deliverable_scope_inputs (
  id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('text', 'topic_list', 'passage', 'correction', 'depth')),
  text_md TEXT,
  extraction_id TEXT,
  span_ids_json TEXT NOT NULL DEFAULT '[]',
  context_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  CHECK (kind <> 'passage' OR extraction_id IS NOT NULL),
  CHECK (kind = 'passage' OR text_md IS NOT NULL)
);
CREATE INDEX idx_deliverable_scope_inputs_goal ON deliverable_scope_inputs(goal_id, created_at);

CREATE TRIGGER deliverable_scope_inputs_no_update
BEFORE UPDATE ON deliverable_scope_inputs
BEGIN
  SELECT RAISE(ABORT, 'deliverable_scope_inputs is append-only');
END;

CREATE TRIGGER deliverable_scope_inputs_no_delete
BEFORE DELETE ON deliverable_scope_inputs
BEGIN
  SELECT RAISE(ABORT, 'deliverable_scope_inputs is append-only');
END;

CREATE TABLE deliverable_scope_resolutions (
  id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL,
  origin TEXT NOT NULL CHECK (origin IN ('resolver', 'learner')),
  input_ids_json TEXT NOT NULL DEFAULT '[]',
  learning_objects_json TEXT NOT NULL DEFAULT '[]',
  unmatched_json TEXT NOT NULL DEFAULT '[]',
  facet_scope_json TEXT NOT NULL DEFAULT '{}',
  state_key TEXT NOT NULL,
  ledger_id TEXT NOT NULL REFERENCES judgment_ledger(id),
  model TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_deliverable_scope_resolutions_goal ON deliverable_scope_resolutions(goal_id, created_at);

CREATE TRIGGER deliverable_scope_resolutions_no_update
BEFORE UPDATE ON deliverable_scope_resolutions
BEGIN
  SELECT RAISE(ABORT, 'deliverable_scope_resolutions is append-only');
END;

CREATE TRIGGER deliverable_scope_resolutions_no_delete
BEFORE DELETE ON deliverable_scope_resolutions
BEGIN
  SELECT RAISE(ABORT, 'deliverable_scope_resolutions is append-only');
END;

CREATE TABLE deliverable_path_sections (
  id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL,
  depth TEXT NOT NULL CHECK (depth IN ('get_the_idea', 'learn_to_use_it', 'fluency')),
  learning_object_id TEXT NOT NULL,
  extraction_id TEXT NOT NULL,
  section_id TEXT NOT NULL,
  label TEXT NOT NULL CHECK (label IN ('core', 'prerequisite', 'alternate', 'already_shown', 'assumed')),
  ordinal INTEGER NOT NULL,
  reason TEXT NOT NULL,
  exercise_span_id TEXT,
  learner_override TEXT CHECK (learner_override IS NULL
    OR learner_override IN ('use_instead', 'read_anyway', 'skip', 'check_later', 'none')),
  commitment_id TEXT,
  state_key TEXT NOT NULL,
  ledger_id TEXT NOT NULL REFERENCES judgment_ledger(id),
  model TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE UNIQUE INDEX idx_deliverable_path_sections_judged
  ON deliverable_path_sections(goal_id, depth, state_key, learning_object_id, extraction_id, section_id)
  WHERE learner_override IS NULL;
CREATE INDEX idx_deliverable_path_sections_goal ON deliverable_path_sections(goal_id, depth, created_at);
CREATE INDEX idx_deliverable_path_sections_reading ON deliverable_path_sections(extraction_id, section_id);

CREATE TRIGGER deliverable_path_sections_no_update
BEFORE UPDATE ON deliverable_path_sections
BEGIN
  SELECT RAISE(ABORT, 'deliverable_path_sections is append-only');
END;

CREATE TRIGGER deliverable_path_sections_no_delete
BEFORE DELETE ON deliverable_path_sections
BEGIN
  SELECT RAISE(ABORT, 'deliverable_path_sections is append-only');
END;
