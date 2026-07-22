-- P3 slice 3, step 9 (spec_p3_reader_integration §10.1, design B step 9).
-- Commitment arcs: the longitudinal reading -> practice arc program composed with
-- P1 commitments. An arc is a PROGRAM / state machine (comprehend -> complete ->
-- retrieve -> discriminate -> integrate -> transfer -> revisit), NOT a precomputed
-- set of due dates. Arc state is a projection over memory time (card/readiness
-- decay) + arc time (intended stage + evidence-gated progress).
--
-- An arc version references P1 patterns, PINS the P1 depth-policy/envelope version,
-- and maps each stage to a reviewed depth-milestone edge. The arc projector may
-- record an achieved stage and request EXACTLY ONE P1 automatic transition; it
-- CANNOT create an edge, widen an envelope, or transfer scheduling state across a
-- card fork (§10.1, invariant 1.1.13). It never hard-gates continued reading.
--
-- No new evidence: arcs compose the landed P1 commitment/depth substrate. Reading
-- signals reaching an arc are salience-only (§8.2, firewall §C).

CREATE TABLE commitment_arcs (
  id TEXT PRIMARY KEY,
  commitment_id TEXT NOT NULL REFERENCES commitments(id),
  source_id TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_commitment_arcs_commitment ON commitment_arcs(commitment_id);
CREATE INDEX idx_commitment_arcs_source ON commitment_arcs(source_id);

CREATE TABLE commitment_arc_versions (
  id TEXT PRIMARY KEY,
  arc_id TEXT NOT NULL REFERENCES commitment_arcs(id),
  version_ordinal INTEGER NOT NULL,
  predecessor_version_id TEXT REFERENCES commitment_arc_versions(id),
  -- P1 pattern refs the arc unfolds through.
  pattern_refs_json TEXT NOT NULL DEFAULT '[]',
  -- The ordered conditional stage program (comprehend..transfer..revisit).
  stages_json TEXT NOT NULL DEFAULT '[]',
  -- The pinned P1 depth objects at authoring time (§10.1). An arc never widens
  -- these; a widen requires a confirmed commitment/envelope successor.
  depth_policy_version_id TEXT,
  depth_envelope_version_id TEXT,
  -- stage_slug -> reviewed depth-milestone edge id (§10.1).
  stage_milestone_map_json TEXT NOT NULL DEFAULT '{}',
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(arc_id, version_ordinal)
);
CREATE INDEX idx_commitment_arc_versions_arc ON commitment_arc_versions(arc_id, version_ordinal);

CREATE TABLE commitment_arc_events (
  id TEXT PRIMARY KEY,
  arc_id TEXT NOT NULL REFERENCES commitment_arcs(id),
  event_ordinal INTEGER NOT NULL,
  kind TEXT NOT NULL
    CHECK (kind IN (
      'arc_created', 'arc_version_appended', 'stage_reached',
      'transition_requested', 'transition_committed', 'transition_declined',
      'arc_paused', 'arc_resumed', 'envelope_shrink_requested', 'policy_changed',
      'prime_offered', 'prime_answered'
    )),
  detail_json TEXT,
  -- Idempotency for at-most-once transition requests (§10.2): a replayed decision
  -- receipt is a no-op.
  receipt_key TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(arc_id, event_ordinal)
);
CREATE INDEX idx_commitment_arc_events_arc ON commitment_arc_events(arc_id, event_ordinal);
CREATE UNIQUE INDEX idx_commitment_arc_events_receipt
  ON commitment_arc_events(arc_id, receipt_key) WHERE receipt_key IS NOT NULL;
