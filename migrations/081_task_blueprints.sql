-- P2 step 1 (spec_p2_narrow_golden_path §3.1, §3.2, §12.1): reviewed, immutable
-- TaskBlueprint versions + exemplar link rows.
--
-- Migration numbering: highest applied on disk = 080 (P1 audit Wave B fixes;
-- 067 skipped, never renumbered). The design allocated 080 for blueprints, but
-- P1 consumed 080 -- P2 substrate therefore starts at 081. Never edit an applied
-- migration.
--
-- These are legitimately NEW P2 bookkeeping substrate (spec §3.2): a versioned,
-- content-addressed, human-reviewed target-family contract. NOT a second
-- posterior / FSRS writer / certification path -- every MEASUREMENT primitive the
-- golden path uses composes a landed P0/P1 service. A blueprint version binds one
-- chapter/unit and one target family (invariant 1); mixed-unit / multi-family
-- versions are rejected before they can validate.

-- Stable blueprint: one per (source revision, unit, family). goal_id is bare TEXT
-- (vault-owned; no FK target, same pattern as goal_contract_versions.goal_id).
CREATE TABLE task_blueprints (
  id TEXT PRIMARY KEY,
  blueprint_slug TEXT NOT NULL,
  source_rev TEXT NOT NULL,
  unit_id TEXT NOT NULL,
  family_key TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(blueprint_slug)
);
CREATE INDEX idx_task_blueprints_unit ON task_blueprints(source_rev, unit_id);

-- Immutable, content-addressed version. `spec_json` carries the full §3.2 shape
-- (facets + closed P1 capability vocab, solution recipes all_of/any_of + optional
-- integration component, TaskFeature ranges + administration conditions,
-- invariants + permitted variation axes, response/outcome/rubric/fatal-errors,
-- failure-signature->triage map, source neighborhoods, target-distribution support
-- + weights, ordered reviewed depth-milestone DAG, leakage boundaries). A version
-- advances draft -> reviewed -> active; a material edit mints a SUCCESSOR version
-- (append-only), it never mutates a reviewed row.
CREATE TABLE task_blueprint_versions (
  id TEXT PRIMARY KEY,
  blueprint_id TEXT NOT NULL REFERENCES task_blueprints(id) ON DELETE CASCADE,
  version INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft'
    CHECK (status IN ('draft', 'reviewed', 'active', 'retired')),
  spec_json TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  canonical_hash TEXT NOT NULL,
  authoring_version TEXT NOT NULL DEFAULT 'stub-1',
  model_version TEXT,
  provenance_version TEXT NOT NULL DEFAULT 'owner-review-1',
  reviewed_at TEXT,
  activated_at TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(blueprint_id, version),
  UNIQUE(blueprint_id, content_hash)
);
CREATE INDEX idx_tbv_blueprint ON task_blueprint_versions(blueprint_id, version);
CREATE INDEX idx_tbv_status ON task_blueprint_versions(status);

-- Append-only review ledger (U-034 artifacts-not-API-calls): every draft/review/
-- activate/retire/reject decision is a durable, independently reviewable record.
CREATE TABLE task_blueprint_review_events (
  id TEXT PRIMARY KEY,
  blueprint_version_id TEXT NOT NULL
    REFERENCES task_blueprint_versions(id) ON DELETE CASCADE,
  kind TEXT NOT NULL CHECK (kind IN (
    'registered', 'reviewed', 'activated', 'retired', 'rejected',
    'reading_question_placed')),
  detail_json TEXT,
  author TEXT NOT NULL DEFAULT 'owner',
  created_at TEXT NOT NULL
);
CREATE INDEX idx_tbre_version ON task_blueprint_review_events(blueprint_version_id, created_at);

-- Exemplar link rows (§3.3): the selected exercises carry exposure status
-- `familiar_anchor` and ZERO held-out weight -- an anchor grounds generation and
-- explanation but can never count as unseen assessment (invariant 4 / §12.1).
CREATE TABLE target_exemplars (
  id TEXT PRIMARY KEY,
  blueprint_version_id TEXT NOT NULL
    REFERENCES task_blueprint_versions(id) ON DELETE CASCADE,
  exemplar_ref TEXT NOT NULL,
  weight REAL NOT NULL DEFAULT 1.0,
  exposure_status TEXT NOT NULL DEFAULT 'familiar_anchor'
    CHECK (exposure_status IN ('familiar_anchor', 'unseen_sibling')),
  held_out_weight REAL NOT NULL DEFAULT 0.0
    CHECK (held_out_weight = 0.0 OR exposure_status = 'unseen_sibling'),
  created_at TEXT NOT NULL,
  UNIQUE(blueprint_version_id, exemplar_ref)
);
CREATE INDEX idx_target_exemplars_version ON target_exemplars(blueprint_version_id);
