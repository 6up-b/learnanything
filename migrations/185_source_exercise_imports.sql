-- Canonical sources S1 (spec_source_practice_and_probes_v1.md §7.5): textbook
-- exercises as practice candidates, their answer-key checks, and the
-- attempt-time certification gate for unverified keys (C3, §7.3a).

-- One row per import of a source exercise: a paid output (authoring, the
-- verifier ladder, the family judge) never re-run on rebuild. Workflow state:
-- `status` moves authoring -> checking -> written | rejected | failed.
CREATE TABLE source_exercise_imports (
  id TEXT PRIMARY KEY,
  proposal_id TEXT,
  extraction_id TEXT NOT NULL,
  span_ids_json TEXT NOT NULL,
  source_id TEXT,
  revision_id TEXT,
  label TEXT,
  practice_item_id TEXT,
  -- reference_content_hash of the item as written (NULL until written).
  content_hash TEXT,
  key_status TEXT CHECK (key_status IS NULL OR key_status IN (
    'book_solution', 'checked', 'panel_agrees', 'panel_agrees_unconfirmed',
    'checking', 'model_answer', 'disputed'
  )),
  verification_json TEXT NOT NULL DEFAULT '{}',
  validation_json TEXT NOT NULL DEFAULT '{}',
  facet_basis TEXT CHECK (facet_basis IS NULL OR facet_basis IN ('authored', 'lo_fallback')),
  family_proposal_id TEXT,
  status TEXT NOT NULL CHECK (status IN ('authoring', 'checking', 'written', 'rejected', 'failed')),
  reason TEXT,
  caller TEXT NOT NULL CHECK (caller IN ('learner', 'reader', 'harvest', 'need')),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX idx_source_exercise_imports_item ON source_exercise_imports(practice_item_id);
CREATE INDEX idx_source_exercise_imports_region ON source_exercise_imports(extraction_id, created_at);

-- Captured verifier output: one append-only row per ladder run, bound to the
-- exact content it checked (reference_content_hash over the prompt, the
-- expected answer and the grading rubric). Never updated, never re-run on
-- rebuild. The attempt gate and the value intents read only this table.
CREATE TABLE reference_key_checks (
  id TEXT PRIMARY KEY,
  practice_item_id TEXT NOT NULL,
  import_id TEXT,
  content_hash TEXT NOT NULL,
  key_status TEXT NOT NULL CHECK (key_status IN (
    'book_solution', 'checked', 'panel_agrees', 'panel_agrees_unconfirmed',
    'model_answer', 'disputed'
  )),
  rung TEXT NOT NULL,
  verification_json TEXT NOT NULL DEFAULT '{}',
  ledger_ids_json TEXT NOT NULL DEFAULT '[]',
  trigger TEXT NOT NULL CHECK (trigger IN ('import', 'background', 'edit', 'verify')),
  started_at TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_reference_key_checks_item ON reference_key_checks(practice_item_id, created_at);
CREATE TRIGGER reference_key_checks_no_update BEFORE UPDATE ON reference_key_checks
BEGIN SELECT RAISE(ABORT, 'reference key checks are append-only'); END;
CREATE TRIGGER reference_key_checks_no_delete BEFORE DELETE ON reference_key_checks
BEGIN SELECT RAISE(ABORT, 'reference key checks are append-only'); END;

-- The attempt-time certification gate (DL3's §4.4 column; built here if DL3
-- has not merged first). Set once by the attempt transaction from the served
-- item's effective key status and never updated, so replay reads the same
-- value. Historical rows keep 'not_applicable'.
ALTER TABLE practice_attempts ADD COLUMN reference_status TEXT NOT NULL DEFAULT 'not_applicable'
  CHECK (reference_status IN ('not_applicable', 'verified', 'unverified'));
