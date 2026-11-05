-- Router objective RO1 (docs/specs/spec_router_objective_v1.md §5.3, §5.5).
--
-- Additive: two nullable columns on practice_attempts and one on
-- derived_state_rebuilds; no row is deleted, no evidence column changes, and
-- nothing scoring, FSRS, mastery or the projection reads is touched.
--
-- 1. practice_attempts.received_at: when the attempt became known to the
--    system, set only where created_at is not the write time (exam seeding
--    writes the exam's past instant). Decision-time reads use
--    available_at = coalesce(received_at, created_at); outcomes, FSRS and
--    mastery keep created_at (an exam sat on its date was a real exposure
--    then). practice_attempts is RAW_LEDGER: replay updates graded columns in
--    place and never this one.
--
-- 2. practice_attempts.received_at_source: 'recorded' when the writer stamped
--    received_at at its own write, 'inferred' when this migration recovered it.
--
--    The backfill: an imported exam row (attempt_type 'exam_evidence') has its
--    id minted at the write (exam_seeding.py: new_ulid() per seeded attempt),
--    so the id's ULID time is when it was received, to the second. An id that
--    is not a ULID (26 Crockford characters, the first at most 7) is left null
--    and reads as created_at. Nothing else is backfilled: every other writer
--    stamps created_at at its write.
--
-- 3. derived_state_rebuilds.projection_switches_json: the switches a rebuild
--    derived persisted state under (RO1: whether the surprise interval factor
--    was removed), the projection's defaults snapshot. doctor warns when the
--    vault's config and the latest whole-vault rebuild's record disagree.
--    Null on every earlier rebuild (not recorded).
ALTER TABLE practice_attempts ADD COLUMN received_at TEXT;

ALTER TABLE practice_attempts ADD COLUMN received_at_source TEXT
  CHECK (received_at_source IS NULL OR received_at_source IN ('recorded', 'inferred'));

ALTER TABLE derived_state_rebuilds ADD COLUMN projection_switches_json TEXT;

UPDATE practice_attempts
   SET received_at = strftime('%Y-%m-%dT%H:%M:%SZ', ((((((((((instr('0123456789ABCDEFGHJKMNPQRSTVWXYZ', substr(upper(id), 1, 1)) - 1) * 32 + (instr('0123456789ABCDEFGHJKMNPQRSTVWXYZ', substr(upper(id), 2, 1)) - 1)) * 32 + (instr('0123456789ABCDEFGHJKMNPQRSTVWXYZ', substr(upper(id), 3, 1)) - 1)) * 32 + (instr('0123456789ABCDEFGHJKMNPQRSTVWXYZ', substr(upper(id), 4, 1)) - 1)) * 32 + (instr('0123456789ABCDEFGHJKMNPQRSTVWXYZ', substr(upper(id), 5, 1)) - 1)) * 32 + (instr('0123456789ABCDEFGHJKMNPQRSTVWXYZ', substr(upper(id), 6, 1)) - 1)) * 32 + (instr('0123456789ABCDEFGHJKMNPQRSTVWXYZ', substr(upper(id), 7, 1)) - 1)) * 32 + (instr('0123456789ABCDEFGHJKMNPQRSTVWXYZ', substr(upper(id), 8, 1)) - 1)) * 32 + (instr('0123456789ABCDEFGHJKMNPQRSTVWXYZ', substr(upper(id), 9, 1)) - 1)) * 32 + (instr('0123456789ABCDEFGHJKMNPQRSTVWXYZ', substr(upper(id), 10, 1)) - 1)) / 1000, 'unixepoch'),
       received_at_source = 'inferred'
 WHERE attempt_type = 'exam_evidence'
   AND received_at IS NULL
   AND upper(id) GLOB '[0-7][0-9A-HJKMNP-TV-Z][0-9A-HJKMNP-TV-Z][0-9A-HJKMNP-TV-Z][0-9A-HJKMNP-TV-Z][0-9A-HJKMNP-TV-Z][0-9A-HJKMNP-TV-Z][0-9A-HJKMNP-TV-Z][0-9A-HJKMNP-TV-Z][0-9A-HJKMNP-TV-Z][0-9A-HJKMNP-TV-Z][0-9A-HJKMNP-TV-Z][0-9A-HJKMNP-TV-Z][0-9A-HJKMNP-TV-Z][0-9A-HJKMNP-TV-Z][0-9A-HJKMNP-TV-Z][0-9A-HJKMNP-TV-Z][0-9A-HJKMNP-TV-Z][0-9A-HJKMNP-TV-Z][0-9A-HJKMNP-TV-Z][0-9A-HJKMNP-TV-Z][0-9A-HJKMNP-TV-Z][0-9A-HJKMNP-TV-Z][0-9A-HJKMNP-TV-Z][0-9A-HJKMNP-TV-Z][0-9A-HJKMNP-TV-Z]';
