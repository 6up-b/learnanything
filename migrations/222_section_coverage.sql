-- Deliverable curriculum C0a: section coverage, the correspondence backbone
-- (spec_deliverable_curriculum_v1 §6; docs/reviews/curriculum-c0a-section-coverage.md).
--
-- Numbered 222: main's head is 220 and the LP claim fixes hold 221 on their
-- own branch (the migration runner has no contiguity rule; renumbered at
-- landing if needed).
--
-- section_coverage (WORKFLOW: paid outputs, never re-run on rebuild): one
-- judged row per (section, learning object). The coverage judge
-- (route section_coverage_judge) reads one LO and its candidate sections
-- across every teaching source of the library and writes, per candidate,
-- its treatment (introduces, develops, applies, mentions, not_about: a
-- structural vocabulary describing the section, not a weight), the roles it
-- saw or proposed, the LO ids the section takes as known (assumes_json), a
-- notation line, how the candidate arrived (provenance, retrieval, learner)
-- and its place in the candidate list. Two sections of two books correspond
-- when their coverage names the same LO: correspondence is a join on the LO,
-- never a section-to-section relation.
--
-- state_key hashes the prompt version, the LO's statement and every
-- candidate section with its block hashes: a judge row is unique per (LO,
-- state_key, reading, section), a changed key writes new rows and the old
-- ones are no longer read. section_hash and lo_hash let a read drop a row
-- whose section or LO changed since it was judged without re-searching.
--
-- A learner's correction ("not about this", "also about...", or 'none',
-- cleared) is its own row: learner_override set, origin 'learner', a
-- learner_card judgment_ledger verdict; the newest learner row per
-- (reading, section, LO) stands over judge rows across re-judgments.
-- Append-only by trigger.
--
-- Nothing here is evidence: no plan, scheduling, projection, grading,
-- serving or replay path reads it; it never writes provenance or a
-- prerequisite edge. Exam and held-out material is never a candidate (the
-- one predicate, before any model sees anything). Kill switch:
-- curriculum.enabled.
CREATE TABLE section_coverage (
  id TEXT PRIMARY KEY,
  extraction_id TEXT NOT NULL,
  section_id TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  treatment TEXT CHECK (treatment IS NULL OR treatment IN ('introduces', 'develops', 'applies', 'mentions', 'not_about')),
  roles_json TEXT NOT NULL DEFAULT '[]',
  assumes_json TEXT NOT NULL DEFAULT '[]',
  notation_md TEXT,
  origin TEXT NOT NULL CHECK (origin IN ('provenance', 'retrieval', 'learner')),
  candidate_rank INTEGER,
  learner_override TEXT CHECK (learner_override IS NULL OR learner_override IN ('is_about', 'not_about', 'none')),
  learner_text TEXT,
  section_hash TEXT NOT NULL,
  lo_hash TEXT NOT NULL,
  state_key TEXT NOT NULL,
  ledger_id TEXT NOT NULL REFERENCES judgment_ledger(id),
  model TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  CHECK (learner_override IS NOT NULL OR treatment IS NOT NULL)
);
CREATE UNIQUE INDEX idx_section_coverage_judged
  ON section_coverage(learning_object_id, state_key, extraction_id, section_id) WHERE learner_override IS NULL;
CREATE INDEX idx_section_coverage_section ON section_coverage(extraction_id, section_id, created_at);
CREATE INDEX idx_section_coverage_lo ON section_coverage(learning_object_id, created_at);

CREATE TRIGGER section_coverage_no_update
BEFORE UPDATE ON section_coverage
BEGIN
  SELECT RAISE(ABORT, 'section_coverage is append-only');
END;

CREATE TRIGGER section_coverage_no_delete
BEFORE DELETE ON section_coverage
BEGIN
  SELECT RAISE(ABORT, 'section_coverage is append-only');
END;
