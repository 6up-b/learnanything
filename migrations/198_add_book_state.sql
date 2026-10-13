-- UX Phase 1 review (docs/reviews/ux-phase1-codex-review.md F1, F5, F7):
-- per-book state for Add's automatic work. Built as 186 on ux/phase1-first-run
-- while main's chain held 181-183, and renumbered 198 when it landed on main
-- after main's 184-197 (EVSI forecasts, RW1a, the route check, the sources
-- track and the facet reword confirm, none of which touches source_artifacts'
-- columns or source_auto_build_state).

-- "Keep this book on this computer" (spec ux_learnloop_v1 §6.4, Q4): the
-- learner's per-book privacy choice, beside the per-source reader switch
-- (migration 104). Every outbound boundary reads it: extraction that would
-- upload the file, the question builds, and the Reader's AI requests.
ALTER TABLE source_artifacts ADD COLUMN keep_local INTEGER NOT NULL DEFAULT 0;

-- WORKFLOW state for a book's automatic question builds:
-- * generation: advanced by "Undo this book's questions"; a build planned in an
--   older generation never applies (it is cancelled, and a late result stays an
--   unapplied record), so an in-flight build cannot put content back.
-- * wanted_*: the latest reading position a progressive build could not act on
--   yet (work was already running); reconciled when that work finishes, when an
--   AI is connected and when the library opens.
CREATE TABLE source_auto_build_state (
  source_id TEXT PRIMARY KEY REFERENCES source_artifacts(id),
  generation INTEGER NOT NULL DEFAULT 0 CHECK (generation >= 0),
  undone_at TEXT,
  wanted_extraction_id TEXT,
  wanted_section_id TEXT,
  wanted_at TEXT,
  updated_at TEXT NOT NULL,
  CHECK ((wanted_section_id IS NULL) = (wanted_extraction_id IS NULL))
);
