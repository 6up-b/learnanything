-- Follow-ups Nov 2 (c): curriculum C5's retraction kind for note-derived gaps
-- (docs/reviews/followups-nov2.md; C5 ruling R2,
-- docs/reviews/curriculum-c5-notes-as-learner-text.md: "Hiding a link after its
-- note was read leaves existing tier-2 gap rows (append-only); a retraction kind
-- needs another FK-safe rebuild and is queued as a follow-up").
--
-- Numbered 235: main's head is 231, and RW5d P3 (232) and curriculum C2b (233)
-- claim the next numbers in parallel (the runner has no contiguity rule;
-- renumbered at landing if needed).
--
-- learner_text_gap_reversals.reversal gains 'unlinked': a gap read from a
-- linked note's snapshot (source_kind 'learner_note') whose snapshot is no
-- longer linked (the learner hid the link, or it is unlinked otherwise) is set
-- aside by one appended reversal row; the gap row itself is append-only and
-- stays. Every reader that leaves out a reversed gap (the router's card, the
-- learner context, the figure author's learner state, the router reader) then
-- leaves it out. Written by the gap pipeline, never a learner's tap. No
-- successor (tier 2: steers suggestions only). Nothing else changes.
--
-- SQLite cannot widen a CHECK in place, so the table is rebuilt
-- temp-then-rename with every row and id preserved, under
-- PRAGMA foreign_keys = OFF (the FK-safe precedent of 208, 212 and 231). Its
-- own foreign key (gap_id -> learner_text_gaps) is recreated as it was; no
-- table references it. DROP TABLE removes the old append-only triggers, which
-- are recreated on the renamed table (the same names and definitions), and
-- the runner's foreign_key_check runs before the migration commits. The same
-- columns, defaults, CHECKs and UNIQUE key.
PRAGMA foreign_keys = OFF;

CREATE TABLE learner_text_gap_reversals__235 (
  id TEXT PRIMARY KEY,
  gap_id TEXT NOT NULL REFERENCES learner_text_gaps(id),
  reversal TEXT NOT NULL CHECK (reversal IN ('undo_edge', 'undo_creation', 'not_this_belief', 'unlinked')),
  actor TEXT NOT NULL CHECK (actor IN ('learner', 'owner')),
  detail_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  UNIQUE (gap_id, reversal)
);
INSERT INTO learner_text_gap_reversals__235 (id, gap_id, reversal, actor, detail_json, created_at)
SELECT id, gap_id, reversal, actor, detail_json, created_at
FROM learner_text_gap_reversals;

DROP TABLE learner_text_gap_reversals;
ALTER TABLE learner_text_gap_reversals__235 RENAME TO learner_text_gap_reversals;

CREATE TRIGGER learner_text_gap_reversals_no_update BEFORE UPDATE ON learner_text_gap_reversals
BEGIN SELECT RAISE(ABORT, 'learner_text_gap_reversals is append-only'); END;
CREATE TRIGGER learner_text_gap_reversals_no_delete BEFORE DELETE ON learner_text_gap_reversals
BEGIN SELECT RAISE(ABORT, 'learner_text_gap_reversals is append-only'); END;

PRAGMA foreign_keys = ON;
