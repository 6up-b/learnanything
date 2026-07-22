-- P3 slice 2, step 7 (spec_p3_reader_integration §7, design B step 7).
-- Source-object layer: stable identity + immutable, per-revision, span-cited
-- versions; versioned relations; append-only canonical mapping proposals.
--
-- A source object is a PER-SOURCE reviewed/proposed semantic object -- NOT a
-- cross-source truth claim (§7.1). Inventory/reader output begins `proposed`; an
-- explicit learner-authored capture may be durable immediately as learner content
-- but still carries a `proposed` canonical mapping. The reader CANNOT create a
-- transcript-shaped graph merely because content was visible or highlighted (§7.3):
-- new canonical objects flow through the existing proposal/gate/review path.
--
-- Accepting a mapping does not overwrite the source object; rejecting one does not
-- delete the annotation or suppress alternative mappings (§7.3).

CREATE TABLE source_objects (
  id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES source_artifacts(id),
  created_at TEXT NOT NULL
);
CREATE INDEX idx_source_objects_source ON source_objects(source_id);

CREATE TABLE source_object_versions (
  id TEXT PRIMARY KEY,
  source_object_id TEXT NOT NULL REFERENCES source_objects(id),
  version_ordinal INTEGER NOT NULL,
  revision_id TEXT NOT NULL,
  object_type TEXT NOT NULL
    CHECK (object_type IN ('claim', 'definition', 'procedure', 'worked_example',
                           'problem', 'proof_move', 'motif_or_passage', 'artifact')),
  authorial_role TEXT,
  salience_proposal REAL,
  exact_text TEXT NOT NULL DEFAULT '',
  content_json TEXT NOT NULL DEFAULT '{}',
  authorship TEXT NOT NULL DEFAULT 'ai'
    CHECK (authorship IN ('learner', 'ai', 'expert', 'author')),
  model_provenance_json TEXT,
  status TEXT NOT NULL DEFAULT 'proposed'
    CHECK (status IN ('proposed', 'reviewed', 'rejected', 'superseded')),
  created_at TEXT NOT NULL,
  UNIQUE(source_object_id, version_ordinal)
);
CREATE INDEX idx_source_object_versions_obj ON source_object_versions(source_object_id, version_ordinal);
CREATE INDEX idx_source_object_versions_revision ON source_object_versions(revision_id);

CREATE TABLE source_object_citations (
  id TEXT PRIMARY KEY,
  source_object_version_id TEXT NOT NULL REFERENCES source_object_versions(id),
  citation_ordinal INTEGER NOT NULL,
  revision_id TEXT NOT NULL,
  span_id TEXT NOT NULL,
  block_content_hash TEXT,
  exact_quote TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(source_object_version_id, citation_ordinal)
);

CREATE TABLE source_object_relations (
  id TEXT PRIMARY KEY,
  source_object_id TEXT NOT NULL REFERENCES source_objects(id),
  related_object_id TEXT REFERENCES source_objects(id),
  version_ordinal INTEGER NOT NULL DEFAULT 1,
  relation_type TEXT NOT NULL
    CHECK (relation_type IN ('supports', 'contradicts', 'refines',
                             'alternate_definition', 'unresolved', 'learner_connects')),
  learner_text TEXT,
  authorship TEXT NOT NULL DEFAULT 'learner'
    CHECK (authorship IN ('learner', 'ai', 'expert', 'author')),
  review_status TEXT NOT NULL DEFAULT 'proposed'
    CHECK (review_status IN ('proposed', 'reviewed', 'rejected', 'superseded')),
  created_at TEXT NOT NULL
);
CREATE INDEX idx_source_object_relations_obj ON source_object_relations(source_object_id);

CREATE TABLE canonical_mapping_proposals (
  id TEXT PRIMARY KEY,
  source_object_id TEXT REFERENCES source_objects(id),
  annotation_id TEXT,
  target_kind TEXT NOT NULL
    CHECK (target_kind IN ('facet', 'lo', 'blueprint', 'commitment', 'new_object')),
  target_ref TEXT,
  confidence REAL,
  status TEXT NOT NULL DEFAULT 'proposed'
    CHECK (status IN ('proposed', 'accepted', 'rejected')),
  rationale TEXT,
  provenance_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  decided_at TEXT
);
CREATE INDEX idx_canonical_mapping_proposals_obj ON canonical_mapping_proposals(source_object_id);
CREATE INDEX idx_canonical_mapping_proposals_status ON canonical_mapping_proposals(status, created_at);
