-- P0.1 (spec_p0_measurement_correctness §3.3, §3.5-§3.8): the FINAL generic
-- activity-lineage substrate. Burn and lineage land here, never on exam-only or
-- probe-only tables. Split-hash presentation identity replaces the single
-- assessment_contract_versions.contract_hash, which becomes a compatibility
-- source (§3.5). Purely additive: no existing table is altered. Vault-owned ids
-- (practice_item_id, learning_object_id, goal_id, target_contract_version_id)
-- are unconstrained TEXT, matching 023/034 -- their authoritative records live in
-- the vault model, not SQLite, so no real FK target exists.

------------------------------------------------------------------------------
-- Family: stable authoring identity. Purpose is fixed for the life of the
-- family and never transitions (invariant §1.1). Versions are immutable.
------------------------------------------------------------------------------
CREATE TABLE activity_families (
  id TEXT PRIMARY KEY,
  purpose TEXT NOT NULL
    CHECK (purpose IN ('diagnostic', 'instructional', 'practice', 'assessment')),
  legacy_kind TEXT
    CHECK (legacy_kind IS NULL OR legacy_kind IN
      ('practice_item', 'probe', 'exam', 'synthetic')),
  title TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE activity_family_versions (
  id TEXT PRIMARY KEY,
  family_id TEXT NOT NULL REFERENCES activity_families(id) ON DELETE CASCADE,
  version INTEGER NOT NULL CHECK (version >= 1),
  family_spec_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(family_id, version)
);
CREATE INDEX idx_activity_family_versions_family
  ON activity_family_versions(family_id);

------------------------------------------------------------------------------
-- Card: stable executable identity + generic ActivityContract. card_contract_hash
-- is content-addressed over the semantic contract (design §2). lineage_kind
-- records how this card relates to its predecessor; certification never crosses
-- a 'fork' (invariant §1.1; enforced in the grading/cert package, edge recorded here).
------------------------------------------------------------------------------
CREATE TABLE activity_cards (
  id TEXT PRIMARY KEY,
  family_id TEXT NOT NULL REFERENCES activity_families(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_activity_cards_family ON activity_cards(family_id);

CREATE TABLE activity_card_versions (
  id TEXT PRIMARY KEY,
  card_id TEXT NOT NULL REFERENCES activity_cards(id) ON DELETE CASCADE,
  version INTEGER NOT NULL CHECK (version >= 1),
  card_contract_hash TEXT NOT NULL,
  contract_json TEXT NOT NULL,
  schema_version INTEGER NOT NULL,
  predecessor_card_version_id TEXT REFERENCES activity_card_versions(id),
  lineage_kind TEXT
    CHECK (lineage_kind IS NULL OR lineage_kind IN ('minor_successor', 'fork')),
  -- legacy provenance for backfill (§7.1 step 2/3): which legacy artifact this
  -- card was split from. NULL for natively authored cards.
  legacy_contract_version_id TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(card_id, version),
  UNIQUE(card_id, card_contract_hash)
);
CREATE INDEX idx_activity_card_versions_card
  ON activity_card_versions(card_id);
CREATE INDEX idx_activity_card_versions_hash
  ON activity_card_versions(card_contract_hash);

------------------------------------------------------------------------------
-- Surface: exact prompt/parameters/media/answer-key artifact bound to ONE card
-- version. surface_hash is the exact-collision key (§3.6 rule 1); fingerprint is
-- the shared-stimulus/near-clone key (§3.6 rule 2). legacy_surface_unverifiable
-- marks a historical surface whose exact content is unrecoverable (§7.1 step 4):
-- it grants no new pristine terminal credit.
------------------------------------------------------------------------------
CREATE TABLE activity_surfaces (
  id TEXT PRIMARY KEY,
  card_version_id TEXT NOT NULL
    REFERENCES activity_card_versions(id) ON DELETE CASCADE,
  surface_hash TEXT NOT NULL,
  fingerprint TEXT,
  surface_json TEXT NOT NULL,
  legacy_practice_item_id TEXT,
  legacy_surface_unverifiable INTEGER NOT NULL DEFAULT 0
    CHECK (legacy_surface_unverifiable IN (0, 1)),
  created_at TEXT NOT NULL,
  UNIQUE(card_version_id, surface_hash)
);
CREATE INDEX idx_activity_surfaces_hash ON activity_surfaces(surface_hash);
CREATE INDEX idx_activity_surfaces_fingerprint ON activity_surfaces(fingerprint);
CREATE INDEX idx_activity_surfaces_legacy_item
  ON activity_surfaces(legacy_practice_item_id);

------------------------------------------------------------------------------
-- Administration: fully resolved card+surface+context+policy snapshot with all
-- pins. administration_snapshot_hash covers resolved card + surface + target +
-- context + all decision/model versions (§3.5). One administration per resolved
-- presentation; created atomically at render (§4.5). Decision/model pins are
-- nullable now (later packages fill them); this table stores IDS + effective-value
-- hash, never a config copy (§6 registry rule). reservation_id is bare TEXT to
-- break the reservation<->administration circular DDL dependency (design §6).
------------------------------------------------------------------------------
CREATE TABLE activity_administrations (
  id TEXT PRIMARY KEY,
  surface_id TEXT NOT NULL REFERENCES activity_surfaces(id),
  card_version_id TEXT NOT NULL REFERENCES activity_card_versions(id),
  family_id TEXT NOT NULL REFERENCES activity_families(id),
  purpose TEXT NOT NULL
    CHECK (purpose IN ('diagnostic', 'instructional', 'practice', 'assessment')),
  administration_snapshot_hash TEXT NOT NULL,
  snapshot_json TEXT NOT NULL,
  target_contract_version_id TEXT,
  target_support_hash TEXT,
  grader_model_version_id TEXT,
  selection_policy_version_id TEXT,
  decision_params_hash TEXT,
  assistance_json TEXT,
  feedback_condition TEXT
    CHECK (feedback_condition IS NULL OR feedback_condition IN
      ('none', 'after_response', 'before_response')),
  eligibility_json TEXT,
  reservation_id TEXT,
  legacy_backfilled INTEGER NOT NULL DEFAULT 0
    CHECK (legacy_backfilled IN (0, 1)),
  created_at TEXT NOT NULL
);
CREATE INDEX idx_activity_administrations_surface
  ON activity_administrations(surface_id);
CREATE INDEX idx_activity_administrations_snapshot_hash
  ON activity_administrations(administration_snapshot_hash);
CREATE INDEX idx_activity_administrations_target
  ON activity_administrations(target_contract_version_id);

------------------------------------------------------------------------------
-- Reservation: an assessment surface set aside from the pinned target's frozen
-- distribution (§4.5). At most one LIVE (status='reserved') reservation per
-- surface, enforced by a partial unique index (mirrors 023/053). A reservation
-- does not burn; cancellation before render may append release_unseen.
------------------------------------------------------------------------------
CREATE TABLE activity_surface_reservations (
  id TEXT PRIMARY KEY,
  surface_id TEXT NOT NULL REFERENCES activity_surfaces(id),
  goal_id TEXT,
  target_contract_version_id TEXT,
  target_support_hash TEXT,
  purpose TEXT NOT NULL
    CHECK (purpose IN ('diagnostic', 'instructional', 'practice', 'assessment')),
  status TEXT NOT NULL
    CHECK (status IN ('reserved', 'rendered', 'cancelled', 'released_unseen')),
  eligibility_json TEXT NOT NULL,
  administration_id TEXT REFERENCES activity_administrations(id),
  reserved_at TEXT NOT NULL,
  closed_at TEXT
);
-- At most one live reservation per surface.
CREATE UNIQUE INDEX idx_activity_reservation_live_surface
  ON activity_surface_reservations(surface_id)
  WHERE status = 'reserved';
CREATE INDEX idx_activity_reservation_surface
  ON activity_surface_reservations(surface_id, status);

------------------------------------------------------------------------------
-- Exposure ledger: THE ONE shared familiarity ledger (§3.6). Every purpose
-- writes here. Held-out eligibility only ever queries this table. A partial
-- unique index guarantees a surface is RENDERED at most once (the atomic burn
-- boundary, §4.5; test 9.5 "two concurrent renders expose once").
------------------------------------------------------------------------------
CREATE TABLE activity_exposure_events (
  id TEXT PRIMARY KEY,
  surface_id TEXT NOT NULL REFERENCES activity_surfaces(id),
  administration_id TEXT REFERENCES activity_administrations(id),
  surface_hash TEXT NOT NULL,
  fingerprint TEXT,
  kind TEXT NOT NULL
    CHECK (kind IN
      ('rendered', 'submitted', 'feedback_revealed',
       'externally_reported', 'shared_stimulus')),
  purpose TEXT NOT NULL
    CHECK (purpose IN ('diagnostic', 'instructional', 'practice', 'assessment')),
  consumes_unseen INTEGER NOT NULL DEFAULT 0
    CHECK (consumes_unseen IN (0, 1)),
  detail_json TEXT,
  created_at TEXT NOT NULL
);
-- A surface is RENDERED at most once, ever: the burn boundary.
CREATE UNIQUE INDEX idx_activity_exposure_render_once
  ON activity_exposure_events(surface_id)
  WHERE kind = 'rendered';
CREATE INDEX idx_activity_exposure_surface
  ON activity_exposure_events(surface_id, kind);
CREATE INDEX idx_activity_exposure_surface_hash
  ON activity_exposure_events(surface_hash);
CREATE INDEX idx_activity_exposure_fingerprint
  ON activity_exposure_events(fingerprint)
  WHERE fingerprint IS NOT NULL;

------------------------------------------------------------------------------
-- Observation: joins one response/attempt to its raw grade events, active
-- interpretation, and purpose-specific evidence eligibility (§3.5). P0.1 creates
-- the row + linkage columns; the grading package fills interpretation.
------------------------------------------------------------------------------
CREATE TABLE activity_observations (
  id TEXT PRIMARY KEY,
  administration_id TEXT NOT NULL
    REFERENCES activity_administrations(id) ON DELETE CASCADE,
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
CREATE INDEX idx_activity_observations_admin
  ON activity_observations(administration_id);
CREATE INDEX idx_activity_observations_attempt
  ON activity_observations(attempt_id);

------------------------------------------------------------------------------
-- Surface lifecycle events: reserve, release_unseen, expose, consume,
-- quarantine, retire, practice_successor_minted (§3.5). Append-only audit of the
-- surface's held-out life; distinct from the familiarity ledger above.
------------------------------------------------------------------------------
CREATE TABLE activity_surface_lifecycle_events (
  id TEXT PRIMARY KEY,
  surface_id TEXT NOT NULL REFERENCES activity_surfaces(id),
  reservation_id TEXT REFERENCES activity_surface_reservations(id),
  administration_id TEXT REFERENCES activity_administrations(id),
  kind TEXT NOT NULL
    CHECK (kind IN
      ('reserve', 'release_unseen', 'expose', 'consume', 'quarantine',
       'retire', 'practice_successor_minted')),
  reason TEXT,
  detail_json TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_activity_surface_lifecycle_surface
  ON activity_surface_lifecycle_events(surface_id, created_at);

------------------------------------------------------------------------------
-- Interaction events envelope (§3.8): the Layer-5 corpus. EXPLICITLY NOT an
-- extension of content_events (which stays a closed content-mutation audit).
-- "Log now, model later": ships before any consumer. Day-one kinds:
-- attempt_duration, retirement_reason, affect_tap. P3 adds reading-event kinds
-- to the SAME table. Declared before retirement_records, which references it.
------------------------------------------------------------------------------
CREATE TABLE interaction_events (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN
    ('attempt_duration', 'retirement_reason', 'affect_tap')),
  subject_type TEXT,
  subject_id TEXT,
  administration_id TEXT,
  surface_id TEXT,
  attempt_id TEXT,
  -- affect-tap vocabulary (§4.6); NULL for non-affect kinds:
  affect_tap_kind TEXT CHECK (affect_tap_kind IS NULL OR affect_tap_kind IN (
    'cue_gave_it_away', 'ambiguous', 'misgraded', 'felt_rote',
    'not_worth_my_attention', 'meaningful_connection', 'wanted_more_depth'
  )),
  attempt_duration_ms INTEGER
    CHECK (attempt_duration_ms IS NULL OR attempt_duration_ms >= 0),
  payload_json TEXT,
  origin TEXT NOT NULL
    CHECK (origin IN ('learner', 'system', 'owner_tooling')),
  created_at TEXT NOT NULL
);
CREATE INDEX idx_interaction_events_kind
  ON interaction_events(kind, created_at);
CREATE INDEX idx_interaction_events_subject
  ON interaction_events(subject_type, subject_id);
CREATE INDEX idx_interaction_events_admin
  ON interaction_events(administration_id);

------------------------------------------------------------------------------
-- Retirement records (§3.7): richer than the bare 'retire' lifecycle event.
-- reason is drawn from the fixed umbrella-L0 taxonomy; provenance names the
-- signal source; replacement_proposal_json is a non-binding successor hook.
------------------------------------------------------------------------------
CREATE TABLE retirement_records (
  id TEXT PRIMARY KEY,
  scope TEXT NOT NULL CHECK (scope IN ('family', 'card', 'surface')),
  family_id TEXT REFERENCES activity_families(id),
  card_version_id TEXT REFERENCES activity_card_versions(id),
  surface_id TEXT REFERENCES activity_surfaces(id),
  reason TEXT NOT NULL CHECK (reason IN (
    'too_easy', 'ambiguous', 'missing_context', 'duplicate_surface',
    'wrong_granularity', 'no_longer_relevant', 'bad_underlying_explanation',
    'superseded_by_better_activity', 'should_be_reference_not_memorized',
    'dont_care_enough_to_retain', 'knew_prompt_not_concept'
  )),
  provenance TEXT NOT NULL
    CHECK (provenance IN ('learner_action', 'affect_signal_escalation', 'owner_tooling')),
  replacement_proposal_json TEXT,
  lifecycle_event_id TEXT REFERENCES activity_surface_lifecycle_events(id),
  interaction_event_id TEXT REFERENCES interaction_events(id),
  created_at TEXT NOT NULL
);
CREATE INDEX idx_retirement_records_family ON retirement_records(family_id);
CREATE INDEX idx_retirement_records_surface ON retirement_records(surface_id);

------------------------------------------------------------------------------
-- Measurement events: append-only spine tying a response through the grade
-- resolution pipeline (§4.1). P0.1 lands the table so exposure/observation rows
-- have a stable measurement anchor; the grading package (P0.2) writes raw-grade
-- and interpretation kinds. Generic + append-only for replay reproducibility.
------------------------------------------------------------------------------
CREATE TABLE measurement_events (
  id TEXT PRIMARY KEY,
  administration_id TEXT NOT NULL
    REFERENCES activity_administrations(id) ON DELETE CASCADE,
  observation_id TEXT REFERENCES activity_observations(id),
  -- kind is intentionally NOT constrained by a CHECK enum: later P0 packages
  -- (P0.2 grader channel: model activation/retirement, interpretation
  -- activation/supersession, quarantine open/resolve, adjudication recorded,
  -- measurement_reinterpretation; P0.3 adds more) append new kinds to THIS same
  -- ledger. Validated at the repository layer instead so widening never needs a
  -- table rebuild. P0.1 kinds: administration_opened, response_appended,
  -- exposure_recorded, raw_grade_appended, grade_classified, grade_interpreted,
  -- projection_rebuilt, correction_appended.
  kind TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  payload_json TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_measurement_events_admin
  ON measurement_events(administration_id, created_at);
CREATE INDEX idx_measurement_events_observation
  ON measurement_events(observation_id);
