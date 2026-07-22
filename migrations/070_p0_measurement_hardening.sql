-- P0 audit hardening (spec_p0_measurement_correctness §4.3, §3.4, §4.5, §9.2).
-- Consolidated schema half of the four-audit fix brief. A NEW migration (not an
-- in-place edit of 065/066) because a durable vault (fixtures/linear_algebra) has
-- already applied migration 065 -- editing it in place would never reach that
-- vault. Everything here is data-preserving.
--
-- H1  grade_interpretations.shared_certainty_lcb: the ONE certainty LCB computed
--     at interpretation time from the pooled resolved model, consumed identically
--     by mastery and certification (§4.3 final paragraph).
-- M1  duplicate-row backstops: UNIQUE authoring key on activity_families,
--     UNIQUE(family_id) on activity_cards, UNIQUE(content_hash) on
--     grader_calibration_models (check-then-act races, §3.5).
-- L1  drop ON DELETE CASCADE from measurement_events.administration_id and
--     activity_observations.administration_id (append-only ledgers must never be
--     silently deleted with an administration).
-- L2  covering indices for target-version / active-interpretation lookups.

------------------------------------------------------------------------------
-- H1: the shared certainty LCB. Nullable: legacy rows and adjudication rows that
-- predate this column fall back to a shared-helper recompute at read time.
------------------------------------------------------------------------------
ALTER TABLE grade_interpretations ADD COLUMN shared_certainty_lcb REAL;

------------------------------------------------------------------------------
-- M1: duplicate-row backstops behind the check-then-act ensure_* methods.
-- Expression index normalizes NULL legacy_kind/title to '' so (diagnostic, NULL,
-- NULL) and (diagnostic, '', '') collide exactly as ensure_activity_family reads.
------------------------------------------------------------------------------
CREATE UNIQUE INDEX idx_activity_families_authoring
  ON activity_families(purpose, COALESCE(legacy_kind, ''), COALESCE(title, ''));

CREATE UNIQUE INDEX idx_activity_cards_family_unique
  ON activity_cards(family_id);

CREATE UNIQUE INDEX idx_gcm_content_hash
  ON grader_calibration_models(content_hash);

------------------------------------------------------------------------------
-- L2: covering indices.
------------------------------------------------------------------------------
CREATE INDEX idx_asr_target_version
  ON activity_surface_reservations(target_contract_version_id);
CREATE INDEX idx_probe_episodes_target_version
  ON probe_episodes(target_contract_version_id);

------------------------------------------------------------------------------
-- L1: drop ON DELETE CASCADE from the two administration-owned append-only
-- ledgers via the SQLite table-rebuild procedure. foreign_keys is toggled OFF
-- around the rebuild (referencing tables keep their definitions by name; child
-- data is preserved). Column definitions are otherwise byte-identical to 065.
------------------------------------------------------------------------------
PRAGMA foreign_keys=OFF;

-- activity_observations: administration_id loses ON DELETE CASCADE.
CREATE TABLE activity_observations_new (
  id TEXT PRIMARY KEY,
  administration_id TEXT NOT NULL
    REFERENCES activity_administrations(id),
  surface_id TEXT NOT NULL REFERENCES activity_surfaces(id),
  attempt_id TEXT,
  response_ref TEXT,
  active_interpretation_id TEXT,
  evidence_eligibility TEXT
    CHECK (evidence_eligibility IS NULL OR evidence_eligibility IN
      ('terminal', 'diagnostic', 'practice', 'ineligible')),
  eligibility_reason TEXT,
  created_at TEXT NOT NULL
);
INSERT INTO activity_observations_new
  SELECT id, administration_id, surface_id, attempt_id, response_ref,
         active_interpretation_id, evidence_eligibility, eligibility_reason,
         created_at
    FROM activity_observations;
DROP TABLE activity_observations;
ALTER TABLE activity_observations_new RENAME TO activity_observations;
CREATE INDEX idx_activity_observations_admin
  ON activity_observations(administration_id);
CREATE INDEX idx_activity_observations_attempt
  ON activity_observations(attempt_id);
-- L2 (folded into the rebuild): active-interpretation head lookups.
CREATE INDEX idx_activity_observations_active_interp
  ON activity_observations(active_interpretation_id);

-- measurement_events: administration_id loses ON DELETE CASCADE.
CREATE TABLE measurement_events_new (
  id TEXT PRIMARY KEY,
  administration_id TEXT NOT NULL
    REFERENCES activity_administrations(id),
  observation_id TEXT REFERENCES activity_observations(id),
  kind TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  payload_json TEXT,
  created_at TEXT NOT NULL
);
INSERT INTO measurement_events_new
  SELECT id, administration_id, observation_id, kind, algorithm_version,
         payload_json, created_at
    FROM measurement_events;
DROP TABLE measurement_events;
ALTER TABLE measurement_events_new RENAME TO measurement_events;
CREATE INDEX idx_measurement_events_admin
  ON measurement_events(administration_id, created_at);
CREATE INDEX idx_measurement_events_observation
  ON measurement_events(observation_id);

PRAGMA foreign_key_check;
PRAGMA foreign_keys=ON;
