-- Router R0 (spec_action_router_v1 §6.2): judgment-call receipts name their
-- judge, the versioned question set and the hash of the state the model read.
-- NULL on every other call. The judge is 'decider' (a decision model) or
-- 'llm' (a chat model with structured output).
ALTER TABLE model_call_receipts ADD COLUMN judge TEXT
  CHECK(judge IS NULL OR judge IN ('decider', 'llm'));
ALTER TABLE model_call_receipts ADD COLUMN question_set_version TEXT;
ALTER TABLE model_call_receipts ADD COLUMN state_hash TEXT;

-- The Decider's verdicts append to judgment_ledger as judge 'decider', with
-- the same provenance rule as 'llm' (model and question-set version). SQLite
-- cannot widen a CHECK in place, so the append-only ledger is rebuilt with
-- every row and id preserved (150/153/164 precedent). DROP TABLE removes the
-- old index and triggers, which are recreated on the renamed table. The
-- activity_family_membership_events foreign key names the table, so it resolves to
-- the rebuilt one.
--
-- The judge CHECK is the only value constraint on the ledger (task, left_kind
-- and right_kind are free text). It keeps every judge written through
-- migration 174 (166's six: llm, verifier, owner, diagnoser, learner_card,
-- exact_key, used by M2's diagnosis split, T4's contamination flags, T5's
-- same_concept nominations, 5a's PF roles, the Phase 3 families, T8's
-- zero-data arm, the practice index and placement) and adds 'decider'.
-- Written as 169 on router/r0; renumbered to 175 when merged after 169-174.
PRAGMA foreign_keys = OFF;

CREATE TABLE judgment_ledger__175 (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    supersedes_id TEXT REFERENCES judgment_ledger(id),
    task TEXT NOT NULL,
    left_kind TEXT NOT NULL,
    left_id TEXT NOT NULL,
    right_kind TEXT,
    right_id TEXT,
    judge TEXT NOT NULL CHECK(judge IN ('llm', 'verifier', 'owner', 'diagnoser', 'learner_card', 'exact_key', 'decider')),
    judge_model TEXT,
    prompt_version TEXT,
    input_hash TEXT NOT NULL,
    verdict TEXT NOT NULL,
    score REAL,
    rationale TEXT NOT NULL,
    CHECK((right_kind IS NULL) = (right_id IS NULL)),
    CHECK(supersedes_id IS NULL OR supersedes_id != id)
);
INSERT INTO judgment_ledger__175(
    id, created_at, supersedes_id, task, left_kind, left_id, right_kind, right_id,
    judge, judge_model, prompt_version, input_hash, verdict, score, rationale
)
SELECT
    id, created_at, supersedes_id, task, left_kind, left_id, right_kind, right_id,
    judge, judge_model, prompt_version, input_hash, verdict, score, rationale
FROM judgment_ledger;

DROP TABLE judgment_ledger;
ALTER TABLE judgment_ledger__175 RENAME TO judgment_ledger;

CREATE INDEX judgment_ledger_question ON judgment_ledger(task, left_kind, left_id, right_kind, right_id);
CREATE TRIGGER judgment_ledger_no_update
BEFORE UPDATE ON judgment_ledger
BEGIN
    SELECT RAISE(ABORT, 'judgment_ledger is append-only');
END;
CREATE TRIGGER judgment_ledger_no_delete
BEFORE DELETE ON judgment_ledger
BEGIN
    SELECT RAISE(ABORT, 'judgment_ledger is append-only');
END;
-- Also reject replacement even when SQLite recursive triggers are disabled.
CREATE TRIGGER judgment_ledger_validate_insert
BEFORE INSERT ON judgment_ledger
BEGIN
    SELECT RAISE(ABORT, 'judgment_ledger is append-only')
      WHERE EXISTS (SELECT 1 FROM judgment_ledger WHERE id = NEW.id);
    SELECT RAISE(ABORT, 'llm/diagnoser/decider judgments require nonempty judge_model and prompt_version')
      WHERE NEW.judge IN ('llm', 'diagnoser', 'decider')
        AND (COALESCE(NEW.judge_model, '') = '' OR COALESCE(NEW.prompt_version, '') = '');
    SELECT RAISE(ABORT, 'supersession must identify the same question')
      WHERE NEW.supersedes_id IS NOT NULL AND NOT EXISTS (
          SELECT 1 FROM judgment_ledger
          WHERE id = NEW.supersedes_id AND task = NEW.task
            AND left_kind = NEW.left_kind AND left_id = NEW.left_id
            AND right_kind IS NEW.right_kind AND right_id IS NEW.right_id
      );
END;

PRAGMA foreign_keys = ON;
