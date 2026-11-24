-- The effective mastery curve for one applied grading epoch. A surprise row belongs to
-- one attempt, so activation can reconstruct at most its current epoch.
CREATE TABLE attempt_grade_curves (
    attempt_id TEXT NOT NULL REFERENCES practice_attempts(id),
    epoch_key TEXT NOT NULL,
    grading_revision INTEGER,
    item_a REAL,
    item_b REAL,
    algorithm_version TEXT NOT NULL,
    provenance TEXT NOT NULL CHECK (provenance IN ('graded', 'reconstructed_at_upgrade', 'missing_at_upgrade')),
    PRIMARY KEY (attempt_id, epoch_key),
    CHECK ((grading_revision IS NULL AND (epoch_key = 'no_evidence' OR epoch_key GLOB 'legacy:*'))
        OR (grading_revision IS NOT NULL AND epoch_key = 'revision:' || grading_revision)),
    CHECK ((provenance = 'missing_at_upgrade' AND item_a IS NULL AND item_b IS NULL)
        OR (provenance <> 'missing_at_upgrade' AND typeof(item_a) = 'real' AND typeof(item_b) = 'real'))
);
CREATE TRIGGER attempt_grade_curves_no_update BEFORE UPDATE ON attempt_grade_curves
BEGIN SELECT RAISE(ABORT, 'attempt_grade_curves is append-only'); END;
CREATE TRIGGER attempt_grade_curves_no_delete BEFORE DELETE ON attempt_grade_curves
BEGIN SELECT RAISE(ABORT, 'attempt_grade_curves is append-only'); END;
-- An insert naming an existing rowid is refused too: a replacing insert under another key would otherwise delete the
-- row holding that rowid through SQLite's implicit replacement, which no delete trigger sees.
CREATE TRIGGER attempt_grade_curves_no_replace BEFORE INSERT ON attempt_grade_curves
WHEN EXISTS (SELECT 1 FROM attempt_grade_curves WHERE attempt_id = NEW.attempt_id AND epoch_key = NEW.epoch_key)
  OR EXISTS (SELECT 1 FROM attempt_grade_curves WHERE rowid = NEW.rowid)
BEGIN SELECT RAISE(ABORT, 'attempt_grade_curves is append-only'); END;
