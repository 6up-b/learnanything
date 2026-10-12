-- Slice A Phase 5a (PF-b, spec_embedding_consumers_v1 §5.3-§5.4, §12):
-- generated candidates, LLM-written solution skeletons and deterministic item
-- fingerprints. Generation jobs reuse surface_mint_requests (078); fingerprint
-- keys reuse the 077 namespaces. Verdicts live in judgment_ledger (166).

-- WORKFLOW: pipeline state for one generated candidate (filters, verification,
-- difficulty, selection, publication, cost). Never evidence; never re-run on
-- rebuild. An unverified candidate is never published (P9).
CREATE TABLE pf_candidates (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  mint_request_id TEXT REFERENCES surface_mint_requests(id),
  round TEXT NOT NULL,
  tier TEXT,
  family_id TEXT NOT NULL,
  parent_item_id TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  generation_path TEXT NOT NULL
    CHECK (generation_path IN ('generator', 'ensemble', 'source_anchored', 'single_shot')),
  declared_relation TEXT NOT NULL
    CHECK (declared_relation IN ('same_target', 'isomorph', 'near', 'far')),
  final_relation TEXT
    CHECK (final_relation IS NULL OR final_relation IN ('same_target', 'isomorph', 'near', 'far')),
  proposer_model TEXT,
  prompt_version TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  verification TEXT NOT NULL DEFAULT 'unverified'
    CHECK (verification IN ('verified', 'unverified')),
  verification_check TEXT,
  status TEXT NOT NULL CHECK (status IN (
    'generated', 'rejected', 'survivor', 'selected', 'not_selected',
    'published', 'baseline')),
  rejection_filter TEXT,
  filters_json TEXT NOT NULL DEFAULT '{}',
  difficulty REAL CHECK (difficulty IS NULL OR (difficulty >= 0 AND difficulty <= 1)),
  difficulty_source TEXT CHECK (difficulty_source IS NULL OR difficulty_source = 'solver_panel'),
  panel_json TEXT,
  selection_json TEXT,
  cost_json TEXT NOT NULL DEFAULT '{}',
  -- The parent/family revisions and effective rubric the judges saw;
  -- publication revalidates them and refuses a stale selection.
  judged_inputs_json TEXT NOT NULL DEFAULT '{}',
  published_item_id TEXT,
  published_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  -- Publication requires a verified reference (P9).
  CHECK (status <> 'published' OR (verification = 'verified' AND published_item_id IS NOT NULL))
);
CREATE INDEX idx_pf_candidates_request ON pf_candidates(mint_request_id);
CREATE INDEX idx_pf_candidates_family ON pf_candidates(family_id, round);
CREATE INDEX idx_pf_candidates_published ON pf_candidates(published_at);

-- WORKFLOW: LLM-written solution skeletons (technique sequence + operation
-- graph), keyed by the described item text's content hash. Paid output:
-- never regenerated on rebuild.
CREATE TABLE item_skeletons (
  id TEXT PRIMARY KEY,
  content_hash TEXT NOT NULL,
  subject_kind TEXT NOT NULL CHECK (subject_kind IN ('practice_item', 'pf_candidate')),
  subject_id TEXT NOT NULL,
  model_id TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  techniques_json TEXT NOT NULL,
  operations_json TEXT NOT NULL,
  checkpoints_json TEXT NOT NULL,
  skeleton_text TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(content_hash, model_id, prompt_version)
);
CREATE INDEX idx_item_skeletons_hash ON item_skeletons(content_hash);

-- DERIVED: deterministic symbolic fingerprints of practice-family items, one
-- row per namespaced key (077 namespaces; never interchangeable). Rebuilt
-- from vault content, persisted skeletons and family generator hashes; no
-- model call, no generator execution.
CREATE TABLE item_fingerprints (
  practice_item_id TEXT NOT NULL,
  namespace TEXT NOT NULL CHECK (namespace IN (
    'surface_hash', 'shared_stimulus', 'source_example', 'solution_recipe',
    'parameter_template', 'verbatim_target', 'external_artifact')),
  component TEXT NOT NULL,
  value_hash TEXT NOT NULL,
  item_content_hash TEXT NOT NULL,
  fingerprint_version TEXT NOT NULL,
  PRIMARY KEY (practice_item_id, namespace, component)
);
CREATE INDEX idx_item_fingerprints_value ON item_fingerprints(namespace, value_hash);
