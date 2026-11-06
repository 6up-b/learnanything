-- Teacher TE3a: adaptive difficulty's lesson opportunity (spec_teacher_v1 rev 5
-- §14.2, §20 row TE3a, §24; spec_adaptive_difficulty_v1 §5.11 as amended at
-- TE3a's landing (Q5: A12 limit 1 and D20); docs/reviews/teacher-te3a.md).
--
-- Built as 248 on TE3a's base (main 5565bede25, head 247) and renumbered 249
-- at its landing, after TE2's 248 (248_teacher_te2_sources.sql, which touches
-- no table here) landed first; the runner has no contiguity rule.
--
-- ad_reading_opportunities (RECEIPT, append-only) gains the kind 'lesson': one
-- row per closed lesson's node with an LO whose final status is landed or
-- taught (subkind), written by AD's sweep from the lesson's receipt
-- (source_table 'lesson_receipts', source_id '<lesson id>/<node id>'). It is
-- a learning opportunity, prediction-only, under the reading-signal firewall's
-- carve-out (salience_only, as every row of the table); nothing else changes.
--
-- SQLite cannot widen a CHECK in place, so the table is rebuilt
-- temp-then-rename with every row and id preserved, as migration 214 rebuilt
-- it: the same columns, defaults, CHECKs (the kind list widened by one value),
-- unique keys, indexes and append-only triggers. DROP TABLE removes the old
-- indexes and triggers, which are recreated on the renamed table with the same
-- names and definitions. No table references this one.
CREATE TABLE ad_reading_opportunities_v249 (
  id TEXT PRIMARY KEY,
  opportunity_key TEXT NOT NULL,
  kind TEXT NOT NULL
    CHECK (kind IN ('reading', 'reader_tutor_exchange', 'worked_example', 'in_passage_question', 'lesson')),
  subkind TEXT NOT NULL,
  source_table TEXT NOT NULL,
  source_id TEXT NOT NULL,
  source_written_at TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  facet_doses_json TEXT NOT NULL,
  dose_offer_id TEXT,
  mapping_version TEXT NOT NULL,
  authority_class TEXT NOT NULL DEFAULT 'salience_only' CHECK (authority_class = 'salience_only'),
  sweep TEXT NOT NULL CHECK (sweep IN ('serve', 'backfill')),
  sweep_ref TEXT,
  swept_at TEXT NOT NULL,
  -- '' for a receipt recorded before receipts carried an epoch (never in force).
  protection_epoch TEXT NOT NULL DEFAULT '',
  UNIQUE (opportunity_key, protection_epoch),
  UNIQUE (kind, subkind, source_table, source_id, learning_object_id, protection_epoch)
);
INSERT INTO ad_reading_opportunities_v249 (
  id, opportunity_key, kind, subkind, source_table, source_id, source_written_at, learning_object_id,
  facet_doses_json, dose_offer_id, mapping_version, authority_class, sweep, sweep_ref, swept_at, protection_epoch)
SELECT id, opportunity_key, kind, subkind, source_table, source_id, source_written_at, learning_object_id,
  facet_doses_json, dose_offer_id, mapping_version, authority_class, sweep, sweep_ref, swept_at, protection_epoch
FROM ad_reading_opportunities;
DROP TABLE ad_reading_opportunities;
ALTER TABLE ad_reading_opportunities_v249 RENAME TO ad_reading_opportunities;
CREATE INDEX idx_ad_reading_opportunities_lo ON ad_reading_opportunities(learning_object_id, source_written_at);
CREATE INDEX idx_ad_reading_opportunities_written ON ad_reading_opportunities(source_written_at, id);

CREATE TRIGGER ad_reading_opportunities_no_update
BEFORE UPDATE ON ad_reading_opportunities
BEGIN
  SELECT RAISE(ABORT, 'ad_reading_opportunities is append-only');
END;

CREATE TRIGGER ad_reading_opportunities_no_delete
BEFORE DELETE ON ad_reading_opportunities
BEGIN
  SELECT RAISE(ABORT, 'ad_reading_opportunities is append-only');
END;
