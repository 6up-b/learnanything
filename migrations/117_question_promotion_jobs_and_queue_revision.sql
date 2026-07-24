-- Durable question-to-practice authoring and lightweight Today queue
-- invalidation.
--
-- A promotion request is written before model work starts, then linked to the
-- ingest batch that performs analysis/authoring.  This makes retries and
-- failures visible instead of collapsing a two-turn model workflow into one
-- synchronous RPC.
CREATE TABLE question_promotion_requests (
  question_event_id TEXT PRIMARY KEY REFERENCES question_events(id) ON DELETE CASCADE,
  intent TEXT NOT NULL,
  subject_id TEXT,
  learning_object_id TEXT,
  status TEXT NOT NULL,
  stage TEXT NOT NULL,
  batch_id TEXT REFERENCES ingest_batches(id) ON DELETE SET NULL,
  promotion_route TEXT,
  error_code TEXT,
  error_message TEXT,
  retryable INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX idx_question_promotion_requests_batch
  ON question_promotion_requests(batch_id);
CREATE INDEX idx_question_promotion_requests_status
  ON question_promotion_requests(status, updated_at);

-- Backfill the already-persisted promotion ledger.  In particular, expose
-- legacy review_required rows whose patch contains no practice item as failed
-- instead of leaving a permanent, misleading "queued for review" chip.
INSERT INTO question_promotion_requests(
  question_event_id, intent, status, stage, promotion_route,
  error_code, error_message, retryable, created_at, updated_at
)
SELECT
  promotion.question_event_id,
  promotion.intent,
  CASE
    WHEN promotion.route = 'review_required' AND NOT EXISTS (
      SELECT 1
      FROM proposed_patch_items item
      WHERE item.proposed_patch_id = promotion.proposed_patch_id
        AND item.item_type = 'practice_item'
        AND item.operation = 'create'
    ) THEN 'failed'
    ELSE 'completed'
  END,
  CASE
    WHEN promotion.route = 'review_required' AND NOT EXISTS (
      SELECT 1
      FROM proposed_patch_items item
      WHERE item.proposed_patch_id = promotion.proposed_patch_id
        AND item.item_type = 'practice_item'
        AND item.operation = 'create'
    ) THEN 'failed'
    WHEN promotion.route = 'review_required' THEN 'review'
    ELSE 'ready'
  END,
  promotion.route,
  CASE
    WHEN promotion.route = 'review_required' AND NOT EXISTS (
      SELECT 1
      FROM proposed_patch_items item
      WHERE item.proposed_patch_id = promotion.proposed_patch_id
        AND item.item_type = 'practice_item'
        AND item.operation = 'create'
    ) THEN 'no_practice_item'
    ELSE NULL
  END,
  CASE
    WHEN promotion.route = 'review_required' AND NOT EXISTS (
      SELECT 1
      FROM proposed_patch_items item
      WHERE item.proposed_patch_id = promotion.proposed_patch_id
        AND item.item_type = 'practice_item'
        AND item.operation = 'create'
    ) THEN 'The promotion proposal did not contain a practice item.'
    ELSE NULL
  END,
  CASE
    WHEN promotion.route = 'review_required' AND NOT EXISTS (
      SELECT 1
      FROM proposed_patch_items item
      WHERE item.proposed_patch_id = promotion.proposed_patch_id
        AND item.item_type = 'practice_item'
        AND item.operation = 'create'
    ) THEN 0
    ELSE 0
  END,
  promotion.created_at,
  promotion.updated_at
FROM question_promotions promotion;

-- Reader questions used to retain only a synthetic `note_id` span key.  Keep
-- the structured extraction/span/LO provenance needed by later promotion.
ALTER TABLE question_events ADD COLUMN source_context_json TEXT;

-- A single durable high-water mark lets Today poll cheaply.  Queue-affecting
-- mutations bump it; the expensive scheduler RPC is called only after change.
CREATE TABLE queue_state (
  singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
  revision INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL
);

INSERT INTO queue_state(singleton, revision, updated_at)
VALUES (1, 0, '1970-01-01T00:00:00Z');
