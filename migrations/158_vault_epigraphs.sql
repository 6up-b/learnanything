-- Vault epigraphs: short aphoristic quotes and three-line haiku about a
-- vault's material, authored by the synthesis model once per completed
-- bootstrap/append synthesis and cycled on the desktop Start screen.
--
-- CAPTURED PROVIDER OUTPUT. Rows are generated only when a synthesis
-- completes (never on demand) and are never rebuilt from other state, so the
-- table is a raw ledger the rebuild umbrella must not clear.
-- `synthesis_run_id` names the run whose material the epigraph is about;
-- `mode` mirrors synthesis_runs.mode. `text` stores a haiku as three
-- "\n"-joined lines and a quote as one line; readers split on "\n".
--
-- `ordinal` is the row's position within its synthesis batch: ULIDs minted in
-- the same millisecond are not monotonic, so the batch's own order is the only
-- deterministic newest-first tiebreaker under a shared `created_at`.
--
-- Rows are dated artifacts of one synthesis: newer syntheses add rows, older
-- ones stay as history, and a row is never edited (UPDATE is refused). DELETE
-- is left open so a future purge does not need a schema change.

CREATE TABLE vault_epigraphs (
  id TEXT PRIMARY KEY,
  subject_id TEXT NOT NULL,
  source_set_id TEXT,
  synthesis_run_id TEXT,
  mode TEXT NOT NULL CHECK (mode IN ('bootstrap', 'append')),
  kind TEXT NOT NULL CHECK (kind IN ('quote', 'haiku')),
  text TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  provider TEXT,
  model TEXT,
  ordinal INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);

-- The Start screen's read: newest first, optionally for one subject.
CREATE INDEX idx_vault_epigraphs_subject_recent
  ON vault_epigraphs(subject_id, created_at DESC, ordinal DESC);
CREATE INDEX idx_vault_epigraphs_run
  ON vault_epigraphs(synthesis_run_id);

CREATE TRIGGER vault_epigraphs_no_update
BEFORE UPDATE ON vault_epigraphs
BEGIN
  SELECT RAISE(ABORT, 'vault epigraphs are append-only');
END;
