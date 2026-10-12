-- Slice A Phase 5b: the practice index (spec_embedding_consumers_v1.md §5.9).
-- Paid outputs and receipts only. Nothing here is evidence, nothing is derived,
-- and replay never clears or regenerates any of it.

-- One LLM-written dossier per facet revision, source revision, model and prompt.
-- A row is a paid input: regenerated only when the facet or its grounding
-- sources change (a new key), never on rebuild.
CREATE TABLE facet_dossiers (
    id TEXT PRIMARY KEY,
    facet_id TEXT NOT NULL,
    facet_content_hash TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    model_id TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    scope TEXT NOT NULL CHECK(length(trim(scope)) > 0),
    moves TEXT NOT NULL CHECK(length(trim(moves)) > 0),
    errors TEXT NOT NULL,
    contrast TEXT NOT NULL,
    draft_json TEXT NOT NULL,
    grounding_json TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    provider TEXT,
    billing TEXT NOT NULL CHECK(billing IN ('subscription', 'metered')),
    run_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(facet_id, facet_content_hash, source_hash, model_id, prompt_version)
);
CREATE INDEX facet_dossiers_facet ON facet_dossiers(facet_id, created_at);

-- What each find_practice call proposed. It proposes and never serves; the row
-- is the join key for later usage signals (judgment_ledger task practice_usage).
CREATE TABLE practice_index_proposals (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    origin TEXT NOT NULL CHECK(origin IN ('rpc', 'cli', 'tool', 'api')),
    query_id TEXT NOT NULL,
    query_text TEXT NOT NULL,
    constraints_json TEXT NOT NULL,
    path TEXT NOT NULL CHECK(path IN ('dossier', 'direct')),
    path_reason TEXT NOT NULL,
    signals_json TEXT NOT NULL,
    reranked INTEGER NOT NULL CHECK(reranked IN (0, 1)),
    rerank_status TEXT NOT NULL,
    rerank_model TEXT,
    proposed_json TEXT NOT NULL,
    exclusions_json TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    algorithm_version TEXT NOT NULL
);
CREATE INDEX practice_index_proposals_created ON practice_index_proposals(created_at);

-- The persisted held-out retrieval query set. LLM-written queries are paid
-- outputs; logged queries copy real find_practice requests. Never regenerated.
CREATE TABLE practice_eval_queries (
    id TEXT PRIMARY KEY,
    query_text TEXT NOT NULL CHECK(length(trim(query_text)) > 0),
    seed_kind TEXT NOT NULL CHECK(seed_kind IN ('facet', 'item', 'logged')),
    seed_id TEXT NOT NULL,
    model_id TEXT,
    prompt_version TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    run_id TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(prompt_version, seed_kind, seed_id)
);

-- Aggregate result of each retrieval evaluation and the path it chose.
-- find_practice in retrieval_path = "auto" reads the latest row whose manifest
-- matches the current index.
CREATE TABLE practice_index_evaluations (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    winner TEXT NOT NULL CHECK(winner IN ('dossier', 'direct')),
    reason TEXT NOT NULL,
    manifest_hash TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    metrics_json TEXT NOT NULL,
    run_id TEXT NOT NULL
);
CREATE INDEX practice_index_evaluations_manifest
    ON practice_index_evaluations(manifest_hash, created_at);
