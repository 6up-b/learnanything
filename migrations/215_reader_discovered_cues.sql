-- Reader workbench RW3b: discovered cues (spec_reader_workbench_v1 §6.2, §6.3;
-- docs/reviews/reader-workbench-RW3b.md).
--
-- Numbered 215: adaptive difficulty AD2+AD3 holds 214 on its own branch, and
-- the migration runner has no contiguity rule, so 213 -> 215 applies as is.
--
-- passage_links (WORKFLOW: paid outputs, never re-run on rebuild): the cue
-- judge's picks, one row per (open source's extraction, target at its state,
-- passage). A target is a durable misconception, an open hypothesis, a named
-- learner-text gap, a demonstrated facet or (reserved) a recurrence group,
-- each judged by its LLM-written statement; ``state_key`` is that statement
-- and its status, so a new or resolved target recomputes only its own links
-- and an old state's rows are simply no longer read. Each row cites the
-- judge's judgment_ledger verdict, carries the quote the judge relied on
-- (verified in code against the block), the pick rank, the ranks the
-- passage had in each retrieval list (the contrast and correction-span lists
-- among them), the facets the target is about (the holdout's outcome reads
-- the next attempt on them) and the instructional roles the judge proposed for RW4e (used
-- only positively, never to exclude; G44). Append-only: a new state writes
-- new rows.
--
-- reader_cue_impressions (RECEIPT): one row per (visit, cue) the Reader could
-- show: shown (in the learner's view), or not shown with its reason
-- (``holdout``: the seeded random withholding of a discovered cue, with its
-- seed and the propensity of the arm it drew; ``density``, ``spacing``,
-- ``restored_line``: the restraint rules, never a holdout). ``p_open`` and its
-- source are the value the cue was ordered by. ``link_id`` is null for a
-- Guide cue (RW3a), which is never held out. Append-only, except that the
-- learner's first response (and its time and text hash) is written once.
--
-- Nothing here is evidence: replay and rebuild never read either table, and
-- no scoring, scheduling, projection, grading or serving path does.
-- Kill switches: cues.enabled, cues.discovery_enabled, cues.try_first_enabled,
-- cues.value_order_enabled, cues.holdout_rate = 0.
CREATE TABLE passage_links (
  id TEXT PRIMARY KEY,
  extraction_id TEXT NOT NULL,
  span_id TEXT NOT NULL,
  target_kind TEXT NOT NULL CHECK (target_kind IN (
    'recurrence_group', 'hypothesis', 'misconception', 'learner_text_gap', 'demonstrated_facet', 'unchecked_claim'
  )),
  target_id TEXT NOT NULL,
  relation TEXT NOT NULL CHECK (relation IN (
    'clarifies_distinction', 'new_application', 'prerequisite_for', 'try_first'
  )),
  quote TEXT NOT NULL,
  pick_rank INTEGER NOT NULL CHECK (pick_rank >= 1),
  ranks_json TEXT NOT NULL DEFAULT '{}',
  roles_json TEXT NOT NULL DEFAULT '[]',
  target_facets_json TEXT NOT NULL DEFAULT '[]',
  ledger_id TEXT NOT NULL REFERENCES judgment_ledger(id),
  state_key TEXT NOT NULL,
  model TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (extraction_id, target_kind, target_id, state_key, span_id)
);
CREATE INDEX idx_passage_links_extraction ON passage_links(extraction_id, state_key);
CREATE INDEX idx_passage_links_target ON passage_links(target_kind, target_id);

CREATE TRIGGER passage_links_no_update
BEFORE UPDATE ON passage_links
BEGIN
  SELECT RAISE(ABORT, 'passage_links is append-only');
END;

CREATE TRIGGER passage_links_no_delete
BEFORE DELETE ON passage_links
BEGIN
  SELECT RAISE(ABORT, 'passage_links is append-only');
END;

CREATE TABLE reader_cue_impressions (
  id TEXT PRIMARY KEY,
  cue_id TEXT NOT NULL,
  link_id TEXT REFERENCES passage_links(id),
  extraction_id TEXT NOT NULL,
  span_id TEXT NOT NULL,
  -- The learning object the cue is about: the holdout's estimate reads the
  -- next attempt on it (shown vs held out, weighted by the propensity).
  learning_object_id TEXT,
  kind TEXT NOT NULL CHECK (kind IN ('revisit', 'distinction', 'application', 'prerequisite', 'try_first')),
  visit_id TEXT NOT NULL,
  shown INTEGER NOT NULL CHECK (shown IN (0, 1)),
  suppressed_reason TEXT CHECK (suppressed_reason IS NULL OR suppressed_reason IN (
    'holdout', 'density', 'spacing', 'restored_line'
  )),
  -- The probability of the arm the holdout drew (shown: 1 - rate; held out:
  -- rate); null for a Guide cue, which is never drawn.
  propensity REAL CHECK (propensity IS NULL OR (propensity > 0 AND propensity <= 1)),
  seed TEXT,
  p_open REAL CHECK (p_open IS NULL OR (p_open >= 0 AND p_open <= 1)),
  p_open_source TEXT,
  density TEXT NOT NULL CHECK (density IN ('off', 'fewer', 'normal', 'more')),
  response TEXT NOT NULL DEFAULT 'none' CHECK (response IN (
    'opened', 'check_me', 'try_first', 'not_relevant', 'fewer', 'none'
  )),
  response_text_hash TEXT,
  created_at TEXT NOT NULL,
  responded_at TEXT,
  CHECK ((shown = 1) = (suppressed_reason IS NULL)),
  CHECK ((suppressed_reason = 'holdout') <= (link_id IS NOT NULL)),
  CHECK ((response = 'none') = (responded_at IS NULL)),
  UNIQUE (visit_id, cue_id)
);
CREATE INDEX idx_reader_cue_impressions_link ON reader_cue_impressions(link_id);
CREATE INDEX idx_reader_cue_impressions_created ON reader_cue_impressions(extraction_id, created_at);

-- The learner's first response is written once; nothing else ever changes.
CREATE TRIGGER reader_cue_impressions_response_once
BEFORE UPDATE ON reader_cue_impressions
WHEN OLD.response != 'none'
  OR NEW.id IS NOT OLD.id OR NEW.cue_id IS NOT OLD.cue_id OR NEW.link_id IS NOT OLD.link_id
  OR NEW.extraction_id IS NOT OLD.extraction_id OR NEW.span_id IS NOT OLD.span_id
  OR NEW.learning_object_id IS NOT OLD.learning_object_id
  OR NEW.kind IS NOT OLD.kind OR NEW.visit_id IS NOT OLD.visit_id OR NEW.shown IS NOT OLD.shown
  OR NEW.suppressed_reason IS NOT OLD.suppressed_reason OR NEW.propensity IS NOT OLD.propensity
  OR NEW.seed IS NOT OLD.seed OR NEW.p_open IS NOT OLD.p_open OR NEW.p_open_source IS NOT OLD.p_open_source
  OR NEW.density IS NOT OLD.density OR NEW.created_at IS NOT OLD.created_at
BEGIN
  SELECT RAISE(ABORT, 'reader_cue_impressions is append-only but for the first response');
END;

CREATE TRIGGER reader_cue_impressions_no_delete
BEFORE DELETE ON reader_cue_impressions
BEGIN
  SELECT RAISE(ABORT, 'reader_cue_impressions is append-only');
END;
