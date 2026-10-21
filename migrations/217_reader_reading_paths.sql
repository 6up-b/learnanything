-- Reader workbench RW7a: reading paths in the Guide, display only
-- (spec_reader_workbench_v1 §10.1; docs/reviews/reader-workbench-RW7a.md).
--
-- Numbered 217: adaptive difficulty AD2+AD3 holds 214 and RW5a 216 on their
-- own branches, and the migration runner has no contiguity rule.
--
-- reader_path_sections (WORKFLOW: paid outputs, never re-run on rebuild): per
-- reading, depth and section, the path judge's label (core, prerequisite,
-- enrichment, already_shown, assumed) after the honest-label rule in code,
-- its one-line reason, the exercise worth trying (an exercise region's lead
-- span, re-read at display) and the judge's judgment_ledger verdict. A judge
-- row has learner_override NULL and is unique per (reading, depth, state_key,
-- section): state_key hashes the depth, the section list sent and every
-- linked LO's status, so a change writes new rows and old ones are simply no
-- longer read. A learner's "read it anyway" / "skip it" (or 'none', cleared)
-- is its own row with a learner_card ledger verdict; the newest per (reading,
-- depth, section) stands across re-judgments. Append-only.
--
-- reader_path_depths (WORKFLOW): the Guide's "How deep do you want to go?"
-- per source, the newest standing. DL2's intent control is read beside it
-- (display-level mapping); nothing here is written to DL2's commitments.
--
-- Nothing here is evidence: no plan, scheduling, projection, grading,
-- serving or replay path reads either table. Kill switch: reading_paths.enabled.
CREATE TABLE reader_path_sections (
  id TEXT PRIMARY KEY,
  extraction_id TEXT NOT NULL,
  depth TEXT NOT NULL CHECK (depth IN ('get_the_idea', 'learn_to_use_it', 'fluency')),
  section_id TEXT NOT NULL,
  label TEXT NOT NULL CHECK (label IN ('core', 'prerequisite', 'enrichment', 'already_shown', 'assumed')),
  reason TEXT NOT NULL,
  exercise_span_id TEXT,
  learner_override TEXT CHECK (learner_override IS NULL OR learner_override IN ('read_anyway', 'skip', 'none')),
  ledger_id TEXT NOT NULL REFERENCES judgment_ledger(id),
  state_key TEXT NOT NULL,
  model TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE UNIQUE INDEX idx_reader_path_sections_judged
  ON reader_path_sections(extraction_id, depth, state_key, section_id) WHERE learner_override IS NULL;
CREATE INDEX idx_reader_path_sections_reading ON reader_path_sections(extraction_id, depth, created_at);

CREATE TRIGGER reader_path_sections_no_update
BEFORE UPDATE ON reader_path_sections
BEGIN
  SELECT RAISE(ABORT, 'reader_path_sections is append-only');
END;

CREATE TRIGGER reader_path_sections_no_delete
BEFORE DELETE ON reader_path_sections
BEGIN
  SELECT RAISE(ABORT, 'reader_path_sections is append-only');
END;

CREATE TABLE reader_path_depths (
  id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL,
  depth TEXT NOT NULL CHECK (depth IN ('get_the_idea', 'learn_to_use_it', 'fluency')),
  created_at TEXT NOT NULL
);
CREATE INDEX idx_reader_path_depths_source ON reader_path_depths(source_id, created_at);

CREATE TRIGGER reader_path_depths_no_update
BEFORE UPDATE ON reader_path_depths
BEGIN
  SELECT RAISE(ABORT, 'reader_path_depths is append-only');
END;

CREATE TRIGGER reader_path_depths_no_delete
BEFORE DELETE ON reader_path_depths
BEGIN
  SELECT RAISE(ABORT, 'reader_path_depths is append-only');
END;
