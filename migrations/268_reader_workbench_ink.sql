-- Reader workbench v2, pen and ink (docs/specs/spec_reader_workbench_v2.md §10.10, §15.1): the learner's ink and
-- what LearnLoop read it as.
--
-- Two new tables:
--   ink_strokes          RAW_LEDGER, append-only by trigger: one row per ink save (a group of strokes the client
--                        flushed) or per erase (a tombstone over earlier strokes' ids), owned by a pad block of kind
--                        'ink' or by a source annotation (a handwritten margin note). An owner's ink as it stands is
--                        every 'strokes' row in write order without the strokes an 'erase' row names.
--   ink_transcriptions   RECEIPT, append-only by trigger: the reading of one owner's standing strokes (its content
--                        hash), written once, so the same strokes are never read twice and a retry spends nothing.
--                        A block owner's reading also becomes the block's next version (provenance
--                        'ink_transcription'); a learner's correction is a block version, never a row here.
--
-- Workflow data and the learner's own writing, never evidence: nothing that scores, schedules, certifies or writes
-- evidence reads these tables (the import fences in pyproject.toml), so no algorithm tag moves. Nothing is
-- backfilled: no ink exists before this migration.

-- One ink save or erase. ink_id is client-minted, so a retried save finds its row. strokes_blob holds the strokes,
-- encoded as 'encoding' says: 'zlib-json-v1' is zlib over the canonical JSON (sorted keys, no spaces) of
-- [{stroke_id, points: [[x, y, t, pressure, tilt_x, tilt_y], ...]}, ...] for a 'strokes' row, and of the erased
-- stroke ids for an 'erase' row; content_hash is the sha256 of that JSON, so a retry is told from a reused id.
-- pointer_meta is the client's pointer description (pointer type, device pixel ratio) as JSON.
CREATE TABLE ink_strokes (
  ink_id TEXT PRIMARY KEY,
  owner_kind TEXT NOT NULL CHECK (owner_kind IN ('block', 'annotation')),
  owner_id TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('strokes', 'erase')),
  encoding TEXT NOT NULL CHECK (encoding IN ('zlib-json-v1')),
  strokes_blob BLOB NOT NULL,
  content_hash TEXT NOT NULL,
  stroke_count INTEGER NOT NULL CHECK (stroke_count >= 1),
  pointer_meta TEXT NOT NULL DEFAULT '{}',
  client_id TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_ink_strokes_owner ON ink_strokes(owner_kind, owner_id);

CREATE TRIGGER ink_strokes_no_update
BEFORE UPDATE ON ink_strokes
BEGIN
    SELECT RAISE(ABORT, 'ink_strokes is append-only');
END;

CREATE TRIGGER ink_strokes_no_delete
BEFORE DELETE ON ink_strokes
BEGIN
    SELECT RAISE(ABORT, 'ink_strokes is append-only');
END;

CREATE TRIGGER ink_strokes_no_replace
BEFORE INSERT ON ink_strokes
WHEN EXISTS (SELECT 1 FROM ink_strokes WHERE ink_id = NEW.ink_id)
BEGIN
    SELECT RAISE(ABORT, 'ink_strokes is append-only');
END;

-- What one owner's standing strokes were read as. content_hash is the sha256 of the standing strokes' canonical JSON
-- (the image sent was rendered from exactly those); latex_md is the reading (Markdown with LaTeX), confidence_label
-- what the learner is told about it ('may_be_wrong': a model's reading, never checked; 'nothing_read': the model read
-- no writing). task, provider and model name the route that read it; prompt_version the request's wording.
CREATE TABLE ink_transcriptions (
  transcription_id TEXT PRIMARY KEY,
  owner_kind TEXT NOT NULL CHECK (owner_kind IN ('block', 'annotation')),
  owner_id TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  latex_md TEXT NOT NULL,
  confidence_label TEXT NOT NULL CHECK (confidence_label IN ('may_be_wrong', 'nothing_read')),
  task TEXT NOT NULL,
  provider TEXT,
  model TEXT,
  prompt_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (owner_kind, owner_id, content_hash)
);

CREATE TRIGGER ink_transcriptions_no_update
BEFORE UPDATE ON ink_transcriptions
BEGIN
    SELECT RAISE(ABORT, 'ink_transcriptions is append-only');
END;

CREATE TRIGGER ink_transcriptions_no_delete
BEFORE DELETE ON ink_transcriptions
BEGIN
    SELECT RAISE(ABORT, 'ink_transcriptions is append-only');
END;

CREATE TRIGGER ink_transcriptions_no_replace
BEFORE INSERT ON ink_transcriptions
WHEN EXISTS (SELECT 1 FROM ink_transcriptions WHERE transcription_id = NEW.transcription_id)
BEGIN
    SELECT RAISE(ABORT, 'ink_transcriptions is append-only');
END;
