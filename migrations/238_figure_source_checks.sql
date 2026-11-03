-- Reader RW5c P1: "matches the book's equation (checked)"
-- (docs/specs/spec_reader_rw5c_checked_labels_v1.md §10.2; docs/reviews/reader-rw5c-p1.md).
--
-- The check's append-only ledger: one row per check of a stored grammar figure,
-- each committed with its judgment_ledger verdict (task figure_source_check,
-- judge verifier) in one transaction. A recheck appends a row and never changes
-- one. The shown state is the newest row at the current certification version.
-- interactive_figures is unchanged: `verification` keeps recording steps 1-2.
--
-- definitions_json holds, per definition, its outcome, closed reason, the
-- candidate's provenance (extraction, span, page, the LaTeX, the left-hand side,
-- block health), the controls' answers and display agreement. elements_json is
-- the element map (roles and code-written TeX; no model text). reasons_json counts
-- the closed reason keys; duration_ms is the check's latency (§12), both
-- descriptive. Nothing outside learnloop.figures and the reader report reads it.

CREATE TABLE figure_source_checks (
  id TEXT PRIMARY KEY,
  figure_id TEXT NOT NULL REFERENCES interactive_figures(id),
  certification_version INTEGER NOT NULL CHECK (certification_version >= 1),
  "trigger" TEXT NOT NULL CHECK ("trigger" IN ('build', 'recheck')),
  outcome TEXT NOT NULL CHECK (outcome IN ('checked', 'differs', 'undecided', 'not_checkable')),
  definitions_json TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(definitions_json)),
  elements_json TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(elements_json)),
  reasons_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(reasons_json)),
  harness_sha256 TEXT NOT NULL,
  reader_version TEXT NOT NULL,
  sympy_version TEXT NOT NULL DEFAULT '',
  duration_ms INTEGER,
  judgment_id TEXT NOT NULL REFERENCES judgment_ledger(id),
  created_at TEXT NOT NULL
);

CREATE INDEX idx_figure_source_checks_figure
  ON figure_source_checks(figure_id, certification_version, created_at);

CREATE TRIGGER figure_source_checks_no_update
BEFORE UPDATE ON figure_source_checks
BEGIN
  SELECT RAISE(ABORT, 'figure_source_checks rows are immutable: a recheck appends a new row');
END;

CREATE TRIGGER figure_source_checks_no_delete
BEFORE DELETE ON figure_source_checks
BEGIN
  SELECT RAISE(ABORT, 'figure_source_checks is append-only');
END;
