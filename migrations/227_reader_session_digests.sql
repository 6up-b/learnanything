-- Reader workbench RW6b part 1: cold follow-ups (docs/specs/
-- spec_reader_workbench_v1.md §9.3, §9.4; docs/reviews/reader-rw6b-p1-followups.md).
-- Numbered 227 (RW5c's unbuilt design also proposes a 227; it renumbers).
--
-- reader_session_digests (WORKFLOW): one row per reader session RW6b
-- planned follow-ups for (a session is RW6a's: one visit, or visits less
-- than 30 minutes apart, keyed by its first visit). It holds
--
--   * summary_json: RW6a's typed session summary as it stood when the
--     follow-ups were planned, with each open question and its outcome
--     (the checks chosen, `no_item`, or why nothing was asked);
--   * followup_commitment_ids_json: the test_me_later commitments created,
--     in check order. The follow-ups themselves live in `commitments`; a
--     re-valuation retirement or an undo is a commitment event with its
--     reason (nothing else is added);
--   * valuation_json: the valuation receipt (the questions, every
--     candidate with its novelty, exposure verdicts, EIG, value interval,
--     expected minutes and predicted outcomes, each verdict and stop
--     reason, the chosen ids in order and the module versions). Replay
--     never re-values;
--   * revaluation_json / revalued_on: the latest daily re-valuation's
--     receipt and its local day (it runs at most once a day);
--   * narrative_md, cited_event_ids_json, model, prompt_version: RW6b
--     part 2's narrative (route reader_digest). Carried now so part 2 needs
--     no table rebuild; part 1 leaves them NULL.
--
-- WORKFLOW, not DERIVED: the receipt records a paid relevance step and the
-- commitments it created, so a rebuild never clears or re-runs it. Never
-- evidence: nothing in scoring, scheduling, projection or serving reads it
-- (DL2 serves the commitments, as any "Check once").
CREATE TABLE reader_session_digests (
  id TEXT PRIMARY KEY,
  extraction_id TEXT NOT NULL,
  session_key TEXT NOT NULL,
  visit_ids_json TEXT NOT NULL DEFAULT '[]',
  started_at TEXT NOT NULL,
  ended_at TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('planned', 'incomplete')),
  summary_json TEXT NOT NULL DEFAULT '{}',
  followup_commitment_ids_json TEXT NOT NULL DEFAULT '[]',
  valuation_json TEXT NOT NULL DEFAULT '{}',
  revaluation_json TEXT,
  revalued_on TEXT,
  narrative_md TEXT,
  cited_event_ids_json TEXT,
  model TEXT,
  prompt_version TEXT,
  dismissed_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE (extraction_id, session_key)
);
CREATE INDEX idx_reader_session_digests_extraction ON reader_session_digests(extraction_id, ended_at);
CREATE INDEX idx_reader_session_digests_ended ON reader_session_digests(ended_at);
