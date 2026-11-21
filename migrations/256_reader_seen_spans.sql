-- Seen passages: WHICH passages the learner saw, not only how many,
-- and the observation that a section's last readable passage was reached by the learner's own reading.
--
-- Additive: two new append-only tables (WORKFLOW in db.table_roles, as reader_section_progress beside
-- them; DENIED to adaptive difficulty). No row is changed or backfilled: reader_section_progress keeps its
-- counts, and a count is never turned into passage identities (the phone's count cannot say which
-- passages were seen). Nothing that scores, schedules, certifies, counts exposure or credits reading
-- reads either table, so there is no algorithm tag: a later step reads reader_seen_spans as generation
-- evidence only.
--
-- reader_seen_spans: one row per passage of one reading, written the first time the Reader reported it
-- observed during the learner's own reading (scrolling or playback, on the desktop or the phone; never a
-- restore, a jump or an explicit completion). section_id is the section it was reported in, checked
-- against the reading. A later report of the same passage changes nothing: reports union, and the first
-- time and origin stay.
--
-- reader_section_ends: one row per section of one reading, written the first time the section's last
-- readable passage (span_id) was reported observed that way. Recorded only: a section is finished
-- exactly as before.
CREATE TABLE reader_seen_spans (
  extraction_id TEXT NOT NULL,
  span_id TEXT NOT NULL,
  section_id TEXT NOT NULL,
  first_seen_at TEXT NOT NULL,
  origin TEXT NOT NULL CHECK (origin IN ('desktop', 'phone')),
  PRIMARY KEY (extraction_id, span_id)
);
CREATE INDEX idx_reader_seen_spans_section ON reader_seen_spans(extraction_id, section_id);

CREATE TRIGGER reader_seen_spans_no_update
BEFORE UPDATE ON reader_seen_spans
BEGIN
    SELECT RAISE(ABORT, 'reader_seen_spans is append-only');
END;

CREATE TRIGGER reader_seen_spans_no_delete
BEFORE DELETE ON reader_seen_spans
BEGIN
    SELECT RAISE(ABORT, 'reader_seen_spans is append-only');
END;

CREATE TABLE reader_section_ends (
  extraction_id TEXT NOT NULL,
  section_id TEXT NOT NULL,
  span_id TEXT NOT NULL,
  first_seen_at TEXT NOT NULL,
  origin TEXT NOT NULL CHECK (origin IN ('desktop', 'phone')),
  PRIMARY KEY (extraction_id, section_id)
);

CREATE TRIGGER reader_section_ends_no_update
BEFORE UPDATE ON reader_section_ends
BEGIN
    SELECT RAISE(ABORT, 'reader_section_ends is append-only');
END;

CREATE TRIGGER reader_section_ends_no_delete
BEFORE DELETE ON reader_section_ends
BEGIN
    SELECT RAISE(ABORT, 'reader_section_ends is append-only');
END;
