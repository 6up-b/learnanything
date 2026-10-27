-- Mobile PR-4: atomic session operations and ownership
-- (docs/specs/spec_mobile_tailnet_v1.md §6.5, §8; docs/reviews/mobile-pr3-pr4.md).
-- Numbered 225 on its base and renumbered 226 at its landing, after the
-- learner-report successor's 225_learner_claim_superseded_by.
--
-- sessions gains its owner: owner_device_id names the mobile_devices row
-- that owns the session (NULL is the desktop, so every existing session and
-- every desktop start keeps NULL), and owner_generation counts the handoffs,
-- for adopt_session's compare-and-swap. No foreign key: NULL is a real owner
-- (the desktop), and a revoked device keeps its row.
--
-- session_handoffs (RECEIPT, append-only by trigger): one row per handoff,
-- an adopt (the session moves to another device, its checkpoint untouched)
-- or a replace (the learner started fresh on another device; the replaced
-- session's checkpoint, with any draft, is kept here before it ends).
-- Never evidence: nothing in scoring, scheduling, projection or replay reads
-- either.

ALTER TABLE sessions ADD COLUMN owner_device_id TEXT;
ALTER TABLE sessions ADD COLUMN owner_generation INTEGER NOT NULL DEFAULT 0;

CREATE TABLE session_handoffs (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(id),
  kind TEXT NOT NULL CHECK (kind IN ('adopt', 'replace')),
  from_device_id TEXT,
  to_device_id TEXT,
  generation INTEGER NOT NULL CHECK (generation >= 0),
  checkpoint_json TEXT,
  at TEXT NOT NULL
);
CREATE INDEX idx_session_handoffs_session ON session_handoffs(session_id, at, id);

CREATE TRIGGER session_handoffs_no_update
BEFORE UPDATE ON session_handoffs
BEGIN
  SELECT RAISE(ABORT, 'session_handoffs is append-only');
END;

CREATE TRIGGER session_handoffs_no_delete
BEFORE DELETE ON session_handoffs
BEGIN
  SELECT RAISE(ABORT, 'session_handoffs is append-only');
END;
