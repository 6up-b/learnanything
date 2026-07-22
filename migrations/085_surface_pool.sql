-- P2 PRACTICE track (spec_p2_narrow_golden_path §7.3, U-028, §12.4; design B.7):
-- the bounded, owner-admitted rotating practice pool.
--
-- Migration numbering: follows 084_pattern_ladder (this P2 learning+practice
-- pair). Never edit an applied migration.
--
-- Provenance mirrors blueprint / diagnostic-pack review (U-028): an LLM drafts
-- candidate surfaces within admitted-card / blueprint bounds and the owner reviews
-- each BEFORE it is admitted -- nothing serves as practice until 'admitted'. The
-- pool composes the landed P1 substrate: familiarity_projection_v1 (hard-collision
-- + warmth gate), surface_mint rotation_decision (lazy rotation after warmth /
-- cadence), and activities.open_administration (practice-purpose burn). It mints NO
-- new posterior, FSRS writer, or per-surface schedule -- scheduling stays
-- card-level (design B.7 / §2 non-negotiable).

-- Stable, reviewed practice pool bound to ONE reviewed blueprint version. A
-- material edit mints a SUCCESSOR pool (new slug/row); a reviewed row is never
-- mutated in place.
CREATE TABLE practice_pools (
  id TEXT PRIMARY KEY,
  pool_slug TEXT NOT NULL,
  blueprint_version_id TEXT NOT NULL
    REFERENCES task_blueprint_versions(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'draft'
    CHECK (status IN ('draft', 'reviewed', 'active', 'retired')),
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(pool_slug)
);
CREATE INDEX idx_practice_pools_blueprint ON practice_pools(blueprint_version_id);

-- Pool surfaces: reviewed practice surfaces, each with a rotation `angle` and named
-- provenance. `admission_status` is the U-028 owner gate -- a surface is never
-- servable until 'admitted'. `surface_id` links the resolved P0 activity surface
-- once the deterministic stub / minter has produced it.
CREATE TABLE practice_pool_surfaces (
  id TEXT PRIMARY KEY,
  pool_id TEXT NOT NULL REFERENCES practice_pools(id) ON DELETE CASCADE,
  surface_slug TEXT NOT NULL,
  angle TEXT NOT NULL,
  provenance TEXT NOT NULL DEFAULT 'llm_within_bounds',
  surface_id TEXT,
  admission_status TEXT NOT NULL DEFAULT 'candidate'
    CHECK (admission_status IN ('candidate', 'admitted', 'rejected')),
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(pool_id, surface_slug)
);
CREATE INDEX idx_practice_pool_surfaces_pool ON practice_pool_surfaces(pool_id);

-- Append-only admission / rotation ledger (U-028 artifacts-not-API-calls): every
-- register / review / admit / reject / activate / serve / rotate decision is a
-- durable, reviewable record.
CREATE TABLE practice_pool_events (
  id TEXT PRIMARY KEY,
  pool_id TEXT NOT NULL REFERENCES practice_pools(id) ON DELETE CASCADE,
  surface_slug TEXT,
  kind TEXT NOT NULL CHECK (kind IN (
    'registered', 'reviewed', 'admitted', 'rejected', 'activated', 'retired',
    'served', 'rotated')),
  detail_json TEXT,
  author TEXT NOT NULL DEFAULT 'owner',
  created_at TEXT NOT NULL
);
CREATE INDEX idx_practice_pool_events_pool ON practice_pool_events(pool_id, created_at);
