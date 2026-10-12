-- Facet identity (handoff §4): every merge or absorb a judge applied, with the
-- facets.yaml entries before and after it, so a one-tap undo restores them
-- exactly. Lifecycle state (proposed -> applied -> undone), never cleared by
-- replay; the verdicts themselves live in judgment_ledger (task same_facet).
CREATE TABLE facet_identity_actions (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    -- ingest (bootstrap synthesis), append, or dedupe.
    origin TEXT NOT NULL CHECK (origin IN ('ingest', 'append', 'dedupe')),
    -- in_run: candidates of one run; attach: a candidate into a registered
    -- facet; vault: two registered facets.
    scope TEXT NOT NULL CHECK (scope IN ('in_run', 'attach', 'vault')),
    run_id TEXT NOT NULL,
    proposal_id TEXT,
    action TEXT NOT NULL CHECK (action IN ('merge', 'absorb')),
    survivor_facet_id TEXT NOT NULL,
    retired_facet_ids_json TEXT NOT NULL,
    -- {facet_id: entry or null}: the facets.yaml entries the action replaced.
    before_json TEXT NOT NULL,
    -- {facet_id: entry or null}: the entries it wrote.
    after_json TEXT NOT NULL,
    -- [[retired, survivor], ...] facet_merges rows the action inserted.
    merge_rows_json TEXT NOT NULL DEFAULT '[]',
    judgment_ids_json TEXT NOT NULL DEFAULT '[]',
    judge TEXT NOT NULL,
    judge_model TEXT,
    prompt_version TEXT,
    detail_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL CHECK (status IN ('proposed', 'applied', 'undone')),
    applied_at TEXT,
    undone_at TEXT,
    undo_detail_json TEXT
);
CREATE INDEX facet_identity_actions_run ON facet_identity_actions(run_id, created_at);
CREATE INDEX facet_identity_actions_survivor ON facet_identity_actions(survivor_facet_id, status);
