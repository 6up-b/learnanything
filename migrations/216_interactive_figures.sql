-- Reader workbench RW5a: explorable figures (spec_reader_workbench_v1 §8.5,
-- §11; docs/reviews/reader-workbench-RW5a.md). Numbered 216: AD2+AD3 hold 214
-- and RW3b 215 (the runner is set-based, so a gap is fine).
--
-- interactive_figures (WORKFLOW): one row per built figure version, a paid
-- output never re-run on rebuild. The declarative spec (InteractiveFigureSpecV1,
-- never code), what was asked for (the selection, a region of a figure and
-- the block whose crop was sent), how it verified (verified | illustrative |
-- failed | unsupported, with the report), and the reuse key (input_hash). A
-- "not right?" version supersedes an earlier one (supersedes_id, with the
-- learner's revision_note); the earlier one is kept. Replay, rebuild and
-- every scoring, scheduling, projection or serving path never read it.
CREATE TABLE interactive_figures (
  id TEXT PRIMARY KEY,
  extraction_id TEXT NOT NULL,
  span_ids_json TEXT NOT NULL DEFAULT '[]',
  -- {span_id, bbox}: a region of a figure (Ctrl+drag), only its crop was sent.
  region_json TEXT,
  -- The figure block (span id) whose image or crop was sent, if any.
  asset_id TEXT,
  origin TEXT NOT NULL CHECK (origin IN ('selection', 'library', 'tutor')),
  supersedes_id TEXT REFERENCES interactive_figures(id),
  revision_note TEXT,
  spec_json TEXT,
  spec_version TEXT NOT NULL,
  kind TEXT CHECK (kind IS NULL OR kind IN ('reconstructed', 'illustrative')),
  verification TEXT NOT NULL CHECK (verification IN ('verified', 'illustrative', 'failed', 'unsupported')),
  verification_report_json TEXT NOT NULL DEFAULT '{}',
  unsupported_kind TEXT,
  model TEXT,
  prompt_version TEXT NOT NULL,
  input_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  CHECK (verification NOT IN ('verified', 'illustrative') OR (spec_json IS NOT NULL AND kind IS NOT NULL)),
  CHECK (verification != 'verified' OR kind = 'reconstructed'),
  CHECK (supersedes_id IS NULL OR supersedes_id != id)
);
CREATE INDEX idx_interactive_figures_extraction ON interactive_figures(extraction_id, created_at);
CREATE INDEX idx_interactive_figures_input ON interactive_figures(input_hash, created_at);
CREATE INDEX idx_interactive_figures_supersedes ON interactive_figures(supersedes_id);

-- figure_predictions (RAW_LEDGER): the learner's prediction on a figure, the
-- observed before/after readout and whether it matched (decided by code),
-- and the optional "what changed?" text. Formative (tier 2, W1): never an
-- attempt, an evidence observation or a field signal; a missed one is read
-- by learner-text gaps as a reader_formative text. extraction_id is the
-- figure's source (RW6a's "Last time here" reads it). Append-only: a row is
-- never deleted, and the only update sets explanation_text once.
CREATE TABLE figure_predictions (
  id TEXT PRIMARY KEY,
  figure_id TEXT NOT NULL REFERENCES interactive_figures(id),
  extraction_id TEXT NOT NULL,
  prediction_index INTEGER NOT NULL CHECK (prediction_index >= 0),
  learner_answer TEXT NOT NULL,
  observed_json TEXT NOT NULL,
  matched INTEGER NOT NULL CHECK (matched IN (0, 1)),
  explanation_text TEXT,
  created_at TEXT NOT NULL,
  UNIQUE (figure_id, prediction_index)
);
CREATE INDEX idx_figure_predictions_extraction ON figure_predictions(extraction_id, created_at);

CREATE TRIGGER figure_predictions_no_delete
BEFORE DELETE ON figure_predictions
BEGIN
  SELECT RAISE(ABORT, 'figure_predictions is append-only');
END;

CREATE TRIGGER figure_predictions_explanation_once
BEFORE UPDATE ON figure_predictions
WHEN OLD.explanation_text IS NOT NULL
  OR NEW.explanation_text IS NULL
  OR NEW.id IS NOT OLD.id
  OR NEW.figure_id IS NOT OLD.figure_id
  OR NEW.extraction_id IS NOT OLD.extraction_id
  OR NEW.prediction_index IS NOT OLD.prediction_index
  OR NEW.learner_answer IS NOT OLD.learner_answer
  OR NEW.observed_json IS NOT OLD.observed_json
  OR NEW.matched IS NOT OLD.matched
  OR NEW.created_at IS NOT OLD.created_at
BEGIN
  SELECT RAISE(ABORT, 'figure_predictions is append-only (explanation_text is set once)');
END;
