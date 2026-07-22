-- P4 audit fix wave (spec_p4_controller_and_scale §6.4/§14.2, spec_ownership_ledger).
-- Migration numbering: follows 100_kinship_kernel_and_shadow_components. Never edit an
-- applied migration; this is additive over the fresh (>=66) migrations no fixture holds.
--
-- Four independent schema hardenings the P4 audit named:
--
--  (M4/D5) golden_path_artifacts gains the 'staged_veto_deferred' artifact kind: the live
--          cutover bridge (controller_cutover.advance_live) persists a typed run-level
--          MARKER on a staged veto so a caller loop can observe the deferral + its named
--          reason, WITHOUT a run event-stream state change. Widens the `kind` CHECK
--          (temp-then-rename, FK-safe, exactly as migrations 086/091 did); all prior
--          kinds are preserved.
--
--  (L2/D6) familiarity_kernel_features: the table's UNIQUE(model_id, subject_surface_id,
--          kin_surface_id) does NOT dedup rows whose kin_surface_id IS NULL (SQLite treats
--          NULLs as distinct in a UNIQUE), so the subject-only (self) feature could be
--          cached twice. A partial unique index over the NULL case restores the intended
--          one-row-per-(model, subject) dedup; INSERT OR REPLACE now collapses correctly.
--
--  (L5/D9) controller_prequential_reports: reports are rebuildable snapshots keyed by
--          content (`report_hash`); UNIQUE(report_hash) makes re-persisting the same
--          content idempotent instead of accumulating duplicate rows.
--
--  (L6/D10) composed_selector_telemetry_horizons: at most ONE horizon may be open at a
--           time (the register path already guards this in code). A partial unique index
--           WHERE status='open' enforces the single-open-row invariant at the DB level
--           against a race.

-- --- (M4) widen golden_path_artifacts.kind -------------------------------------
PRAGMA foreign_keys=OFF;

CREATE TABLE golden_path_artifacts__101 (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES golden_path_runs(id) ON DELETE CASCADE,
  seq INTEGER NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN (
    'assessment_result',
    'restoration',
    'boundary_diff',
    'baseline_boundary',
    'diagnostic_segment_closed',
    'milestone',
    'depth_invitation',
    'depth_accept',
    'depth_decline',
    'staged_veto_deferred')),  -- P4 §14.2/audit M4: live-bridge staged-veto deferral marker
  administration_id TEXT,
  payload_json TEXT NOT NULL,
  idempotency_key TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(run_id, seq),
  UNIQUE(run_id, idempotency_key)
);

INSERT INTO golden_path_artifacts__101 (
  id, run_id, seq, kind, administration_id, payload_json, idempotency_key, created_at
)
SELECT
  id, run_id, seq, kind, administration_id, payload_json, idempotency_key, created_at
FROM golden_path_artifacts;

DROP TABLE golden_path_artifacts;
ALTER TABLE golden_path_artifacts__101 RENAME TO golden_path_artifacts;

CREATE INDEX idx_gpa_run ON golden_path_artifacts(run_id, seq);
CREATE INDEX idx_gpa_run_kind ON golden_path_artifacts(run_id, kind);

PRAGMA foreign_keys=ON;

-- --- (L2) NULL-kin dedup for familiarity_kernel_features ------------------------
CREATE UNIQUE INDEX idx_familiarity_kernel_features_self
  ON familiarity_kernel_features(model_id, subject_surface_id)
  WHERE kin_surface_id IS NULL;

-- --- (L5) content-keyed idempotency for prequential reports ---------------------
CREATE UNIQUE INDEX idx_controller_prequential_reports_hash
  ON controller_prequential_reports(report_hash);

-- --- (L6) single open composed-selector telemetry horizon -----------------------
CREATE UNIQUE INDEX idx_composed_selector_horizon_single_open
  ON composed_selector_telemetry_horizons(status)
  WHERE status = 'open';
