-- Reader RW5d P1: "show me" (docs/specs/spec_reader_show_me_figures_v1.md
-- §7.1, §13.1; docs/reviews/reader-rw5d-p1-show-me.md). Numbered 224: 223 is
-- reserved for Reader CA2 (the runner is set-based, so a gap is fine; the
-- number is confirmed at landing).
--
-- figure_requests (RAW_LEDGER): what was asked, one row per request the
-- figure service built or reused a figure for: the learner's words (or a
-- tutor's goal, read back from its stored answer), the anchor and reading
-- position as sent (normalized), the verified host references, the policy
-- derived on the server, the grounding (anchor | retrieved | none) and the
-- find_sources manifest with the kept span keys. Append-only: a row is never
-- deleted, and the only update sets figure_id once (by the service, after
-- the figure row is stored). Never evidence: nothing in scoring, scheduling,
-- projection or serving reads it.
--
-- The columns P2b and P5 need are carried now (rev 2, Q12's precedent), so
-- neither needs a rebuild: build_mode, tiers_allowed_json and
-- prefetch_decision_id (no foreign key until P5's table exists). P1 writes
-- build_mode 'pressed' and tiers ["grammar"] only; origin and goal_author
-- 'prefetch' are refused from every RPC.
PRAGMA foreign_keys = OFF;

CREATE TABLE figure_requests (
  id TEXT PRIMARY KEY,
  origin TEXT NOT NULL CHECK (origin IN ('selection', 'library', 'tutor', 'show_me', 'ask', 'teacher', 'prefetch')),
  goal_text TEXT,
  goal_author TEXT CHECK (goal_author IS NULL OR goal_author IN ('learner', 'tutor', 'teacher', 'prefetch')),
  anchor_json TEXT,
  reading_at_json TEXT,
  host_ref_json TEXT NOT NULL DEFAULT '{}',
  policy TEXT NOT NULL,
  caller_kind TEXT NOT NULL,
  policy_derived_from TEXT,
  grounding TEXT NOT NULL CHECK (grounding IN ('anchor', 'retrieved', 'none')),
  grounding_manifest_json TEXT NOT NULL DEFAULT '{}',
  build_mode TEXT NOT NULL DEFAULT 'pressed' CHECK (build_mode IN ('pressed', 'prefetch')),
  tiers_allowed_json TEXT NOT NULL DEFAULT '["grammar"]',
  prefetch_decision_id TEXT,
  figure_id TEXT REFERENCES interactive_figures(id),
  created_at TEXT NOT NULL,
  CHECK (goal_text IS NULL OR goal_author IS NOT NULL),
  CHECK (goal_text IS NOT NULL OR anchor_json IS NOT NULL)
);
CREATE INDEX idx_figure_requests_figure ON figure_requests(figure_id);
CREATE INDEX idx_figure_requests_created ON figure_requests(created_at);

CREATE TRIGGER figure_requests_no_delete
BEFORE DELETE ON figure_requests
BEGIN
  SELECT RAISE(ABORT, 'figure_requests is append-only');
END;

CREATE TRIGGER figure_requests_figure_once
BEFORE UPDATE ON figure_requests
WHEN OLD.figure_id IS NOT NULL
  OR NEW.figure_id IS NULL
  OR NEW.id IS NOT OLD.id
  OR NEW.origin IS NOT OLD.origin
  OR NEW.goal_text IS NOT OLD.goal_text
  OR NEW.goal_author IS NOT OLD.goal_author
  OR NEW.anchor_json IS NOT OLD.anchor_json
  OR NEW.reading_at_json IS NOT OLD.reading_at_json
  OR NEW.host_ref_json IS NOT OLD.host_ref_json
  OR NEW.policy IS NOT OLD.policy
  OR NEW.caller_kind IS NOT OLD.caller_kind
  OR NEW.policy_derived_from IS NOT OLD.policy_derived_from
  OR NEW.grounding IS NOT OLD.grounding
  OR NEW.grounding_manifest_json IS NOT OLD.grounding_manifest_json
  OR NEW.build_mode IS NOT OLD.build_mode
  OR NEW.tiers_allowed_json IS NOT OLD.tiers_allowed_json
  OR NEW.prefetch_decision_id IS NOT OLD.prefetch_decision_id
  OR NEW.created_at IS NOT OLD.created_at
BEGIN
  SELECT RAISE(ABORT, 'figure_requests is append-only (figure_id is set once)');
END;

-- interactive_figures (WORKFLOW, as in 216): rebuilt temp-then-rename with
-- every row and id copied unchanged, under PRAGMA foreign_keys = OFF (SQLite
-- cannot widen a CHECK or relax NOT NULL in place; figure_predictions'
-- foreign key resolves to the renamed table, and the runner's
-- foreign_key_check runs before the migration commits). What changes:
-- * origin's CHECK takes RW5d's values (show_me, ask, teacher, prefetch);
-- * extraction_id is nullable, with a figure that has no reading position
--   (a practice-host figure, P3) named by its request instead;
-- * request_id, goal_text (denormalized for the collapsed line), grounding
--   (anchor by default: every RW5a/b row) and input_span_keys_json (the
--   (extraction_id, span_id) pairs of retrieved passages in any source,
--   rechecked for held-out material beside input_span_ids_json);
-- * tier (grammar by default) and, for later tiers, program_version,
--   engine_sha256, runtime_digest, instrumented_sha256, media_file_name,
--   fuller_of_id and checks_json: reserved by P1 (rev 2), unused until P2/P2b.
-- The same indexes (DROP TABLE removed them; recreated with the same names
-- and definitions) plus (request_id).

CREATE TABLE interactive_figures__224 (
  id TEXT PRIMARY KEY,
  extraction_id TEXT,
  span_ids_json TEXT NOT NULL DEFAULT '[]',
  region_json TEXT,
  asset_id TEXT,
  input_span_ids_json TEXT NOT NULL DEFAULT '[]',
  origin TEXT NOT NULL CHECK (origin IN ('selection', 'library', 'tutor', 'show_me', 'ask', 'teacher', 'prefetch')),
  supersedes_id TEXT REFERENCES interactive_figures(id),
  revision_note TEXT,
  spec_json TEXT,
  spec_version TEXT NOT NULL,
  kind TEXT CHECK (kind IS NULL OR kind IN ('reconstructed', 'illustrative')),
  verification TEXT NOT NULL CHECK (verification IN ('verified', 'illustrative', 'failed', 'unsupported')),
  verification_report_json TEXT NOT NULL DEFAULT '{}',
  unsupported_kind TEXT,
  model TEXT,
  prompt_version TEXT NOT NULL,
  input_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  request_id TEXT REFERENCES figure_requests(id),
  goal_text TEXT,
  grounding TEXT NOT NULL DEFAULT 'anchor' CHECK (grounding IN ('anchor', 'retrieved', 'none')),
  input_span_keys_json TEXT NOT NULL DEFAULT '[]',
  tier TEXT NOT NULL DEFAULT 'grammar' CHECK (tier IN ('grammar', 'sketch', 'js_animation', 'manim')),
  program_version TEXT,
  engine_sha256 TEXT,
  runtime_digest TEXT,
  instrumented_sha256 TEXT,
  media_file_name TEXT,
  fuller_of_id TEXT REFERENCES interactive_figures(id),
  checks_json TEXT NOT NULL DEFAULT '[]',
  CHECK (verification NOT IN ('verified', 'illustrative') OR (spec_json IS NOT NULL AND kind IS NOT NULL)),
  CHECK (verification != 'verified' OR kind = 'reconstructed'),
  CHECK (supersedes_id IS NULL OR supersedes_id != id),
  CHECK (extraction_id IS NOT NULL OR request_id IS NOT NULL),
  CHECK (fuller_of_id IS NULL OR fuller_of_id != id)
);
INSERT INTO interactive_figures__224 (
  id, extraction_id, span_ids_json, region_json, asset_id, input_span_ids_json, origin, supersedes_id,
  revision_note, spec_json, spec_version, kind, verification, verification_report_json, unsupported_kind,
  model, prompt_version, input_hash, created_at
)
SELECT
  id, extraction_id, span_ids_json, region_json, asset_id, input_span_ids_json, origin, supersedes_id,
  revision_note, spec_json, spec_version, kind, verification, verification_report_json, unsupported_kind,
  model, prompt_version, input_hash, created_at
FROM interactive_figures;
DROP TABLE interactive_figures;
ALTER TABLE interactive_figures__224 RENAME TO interactive_figures;

CREATE INDEX idx_interactive_figures_extraction ON interactive_figures(extraction_id, created_at);
CREATE INDEX idx_interactive_figures_input ON interactive_figures(input_hash, created_at);
CREATE INDEX idx_interactive_figures_supersedes ON interactive_figures(supersedes_id);
CREATE UNIQUE INDEX idx_interactive_figures_reuse ON interactive_figures(input_hash, spec_version)
  WHERE verification IN ('verified', 'illustrative', 'unsupported');
CREATE INDEX idx_interactive_figures_request ON interactive_figures(request_id);
