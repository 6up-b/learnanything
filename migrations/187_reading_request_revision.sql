-- UX Phase 1 finishing pass (docs/reviews/ux-phase1-finish.md, Codex F8 and F9):
-- the Reader's "keep one chapter ahead" request becomes one durable request
-- per book, the only state that path keeps. Built as 187 on
-- ux/phase1-first-run after the branch's own 186; expect a renumber at merge.
--
-- * wanted_revision: advanced by every new request (the newest position wins),
--   never reset, so whoever acts on a request settles exactly that revision
--   and a newer one recorded meanwhile survives (F9).
-- * wanted_attempts: failed attempts at the current request. A failed request
--   (attempts > 0) is asked again by the Reader's next report instead of being
--   coalesced (F8).
-- * wanted_retry_at: when the ingest worker acts on the request next (due at
--   once when recorded; backed off after each failure; NULL once the worker's
--   retries ran out, when the Reader's next report or the next start asks).
--   It survives a restart, so nothing waits on an in-memory map (F8).
ALTER TABLE source_auto_build_state ADD COLUMN wanted_revision INTEGER NOT NULL DEFAULT 0 CHECK (wanted_revision >= 0);
ALTER TABLE source_auto_build_state ADD COLUMN wanted_attempts INTEGER NOT NULL DEFAULT 0 CHECK (wanted_attempts >= 0);
ALTER TABLE source_auto_build_state ADD COLUMN wanted_retry_at TEXT;

-- A position already waiting is a request due now, at revision 1.
UPDATE source_auto_build_state
SET wanted_revision = 1,
    wanted_retry_at = COALESCE(wanted_at, updated_at)
WHERE wanted_section_id IS NOT NULL;
