-- Facet locks removed (owner, 2026-10-12; handoff §4 "Facet locks no longer
-- block merges"). Two new kinds of facet_identity_actions row:
--
-- * action 'reword': a proposal apply that changes an existing facet's
--   meaning (kind, claim, conditions, non-goals) writes a facet version. The
--   row keeps the entry it replaced (before_json) and the one it wrote
--   (after_json) for one facet (survivor_facet_id, no retired facets), so the
--   one-tap undo restores the old wording exactly. origin 'proposal'.
-- * origin 'registry': a merge the owner asked for from registry review or
--   the facet inspector, applied live with the same undo as a judge's merge.
--
-- SQLite cannot widen a CHECK in place, so the WORKFLOW table is rebuilt with
-- every row and id kept (175/179 precedent). No other table references it.
-- Written as 188 on facets/locks-and-depends-on (184-187 were placeholders
-- for branches in flight); renumbered 185 when it merged onto merge/facet-locks
-- after 184_voi_forecasts, and renumbered 196 when it landed on main after
-- main's 185-195 (RW1a, the route check and the sources track, none of which
-- touches facet_identity_actions).
PRAGMA foreign_keys = OFF;

CREATE TABLE facet_identity_actions__196 (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    -- ingest (bootstrap synthesis), append, dedupe, proposal (a reword
    -- applied from a proposal) or registry (an owner-requested merge).
    origin TEXT NOT NULL CHECK (origin IN ('ingest', 'append', 'dedupe', 'proposal', 'registry')),
    -- in_run: candidates of one run; attach: a candidate into a registered
    -- facet; vault: registered facets (a merge, or one facet's reword).
    scope TEXT NOT NULL CHECK (scope IN ('in_run', 'attach', 'vault')),
    run_id TEXT NOT NULL,
    proposal_id TEXT,
    action TEXT NOT NULL CHECK (action IN ('merge', 'absorb', 'reword')),
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
    status TEXT NOT NULL CHECK (
        status IN ('proposed', 'applying', 'applied', 'undoing', 'undone', 'abandoned')
    ),
    applied_at TEXT,
    undone_at TEXT,
    undo_detail_json TEXT
);
INSERT INTO facet_identity_actions__196(
    id, created_at, origin, scope, run_id, proposal_id, action, survivor_facet_id,
    retired_facet_ids_json, before_json, after_json, merge_rows_json, judgment_ids_json,
    judge, judge_model, prompt_version, detail_json, status, applied_at, undone_at,
    undo_detail_json
)
SELECT
    id, created_at, origin, scope, run_id, proposal_id, action, survivor_facet_id,
    retired_facet_ids_json, before_json, after_json, merge_rows_json, judgment_ids_json,
    judge, judge_model, prompt_version, detail_json, status, applied_at, undone_at,
    undo_detail_json
FROM facet_identity_actions;

DROP TABLE facet_identity_actions;
ALTER TABLE facet_identity_actions__196 RENAME TO facet_identity_actions;

CREATE INDEX facet_identity_actions_run ON facet_identity_actions(run_id, created_at);
CREATE INDEX facet_identity_actions_survivor ON facet_identity_actions(survivor_facet_id, status);

PRAGMA foreign_keys = ON;
