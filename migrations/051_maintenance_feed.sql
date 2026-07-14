-- ING M7 (source-ingestion §11, §10.2): the maintenance feed required to operate
-- append safely, plus the conflict-resolution audit trail. Deterministic notices
-- are generated from existing tables; each notice type declares an aging policy
-- (auto-expiry / auto-resolution / escalation) so the feed stays bounded.
--
-- Migrations 041-049 are taken; M7 owns 050+.

-- §11 Maintenance notices. One row per (notice_type, dedup_key); regeneration is
-- idempotent and never duplicates a live notice. status/snooze_count/snoozed_until
-- drive dismiss/snooze without changing source or curriculum state. aging_policy
-- is declared per notice TYPE (stored on the row for auditability); the generator
-- honours it: auto-expiry drops stale notices, auto-resolution clears notices whose
-- underlying condition cleared, escalation raises severity after N snoozes.
CREATE TABLE maintenance_notices (
  id TEXT PRIMARY KEY,
  subject_id TEXT,
  notice_type TEXT NOT NULL,
  dedup_key TEXT NOT NULL,
  severity TEXT NOT NULL DEFAULT 'info' CHECK (severity IN ('info', 'warning', 'action_needed')),
  aging_policy TEXT NOT NULL CHECK (
    aging_policy IN ('auto_expiry', 'auto_resolution', 'escalation')
  ),
  entity_type TEXT,
  entity_id TEXT,
  title TEXT NOT NULL,
  detail_json TEXT,
  action_json TEXT NOT NULL,        -- {action, label, ...} — one concrete action link
  status TEXT NOT NULL DEFAULT 'active' CHECK (
    status IN ('active', 'snoozed', 'dismissed', 'resolved', 'expired')
  ),
  snooze_count INTEGER NOT NULL DEFAULT 0,
  snoozed_until TEXT,
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  resolved_at TEXT,
  UNIQUE (notice_type, dedup_key)
);

CREATE INDEX idx_maintenance_notices_status
  ON maintenance_notices(status, notice_type);
CREATE INDEX idx_maintenance_notices_subject
  ON maintenance_notices(subject_id);

-- §10.2 Conflict-resolution audit: resolution is a LATER explicit action with its
-- own audit history (prefer-for-context / keep-both-scoped / notation-mapping /
-- dismiss). Resolving preserves both evidence locators and every prior decision.
CREATE TABLE source_conflict_resolutions (
  id TEXT PRIMARY KEY,
  conflict_id TEXT NOT NULL REFERENCES source_conflicts(id),
  resolution_kind TEXT NOT NULL CHECK (
    resolution_kind IN ('prefer_for_context', 'keep_both_scoped', 'notation_mapping', 'dismiss')
  ),
  resolution_json TEXT NOT NULL,
  actor TEXT,
  rationale TEXT,
  created_at TEXT NOT NULL
);

CREATE INDEX idx_source_conflict_resolutions_conflict
  ON source_conflict_resolutions(conflict_id);
