-- The write-ahead intent of a Library save (Codex re-review 2 of the facet
-- authority chokepoint, F7, 2026-10-13). Written as 186 on merge/facet-locks
-- and renumbered 197 when it landed on main after main's 186-195 (the route
-- check and the sources track) and the facet rewords' 196.
--
-- The owner's own edit of facets.yaml in the desktop Library is the explicit
-- manual authority over a facet's meaning (ingestion §4.2): every facet whose
-- meaning a save changes, a new facet or a worked-example edit included, gets
-- the owner's `granted` verdict in judgment_ledger (task
-- facet_manual_authority), committed before the file is written and
-- `withdrawn` if the save never lands. Until now only a save's `reword`
-- actions (facet versions) carried that write-ahead state, so a save with no
-- reword, stopped between its verdicts and its file write, kept `granted`
-- verdicts for wording the registry never showed.
--
-- One row per save with verdicts, committed in the same transaction as the
-- verdicts and any reword actions: `applying` until the file write and the
-- refresh finish (`applied`). Recovery (recover_interrupted_actions, under
-- the vault lock) settles a row left `applying` from facets.yaml: the save
-- landed when the registry shows one of its facets with the wording its
-- verdict names (`applied`); otherwise its verdicts are withdrawn and the row
-- is `abandoned`. WORKFLOW: lifecycle state, never cleared by replay; the
-- verdicts themselves are judgment_ledger's.
CREATE TABLE facet_registry_saves (
    -- The save id the owner's verdicts carry (rationale.save_id).
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('applying', 'applied', 'abandoned')),
    -- {facet_id: {"before": wording key or null for a new facet,
    --             "after": wording key, "fields": [...]}}: the facets whose
    -- meaning the save changes; a wording key is the verdict's right_id.
    facets_json TEXT NOT NULL,
    -- {facet_id: judgment_ledger id}: the owner's granted verdict for each.
    judgment_ids_json TEXT NOT NULL,
    -- The reword actions (facet versions) the save recorded, if any.
    action_ids_json TEXT NOT NULL DEFAULT '[]',
    applied_at TEXT,
    abandoned_at TEXT,
    -- Why an abandoned save never landed, and the verdicts withdrawn.
    settle_detail_json TEXT
);

CREATE INDEX facet_registry_saves_status ON facet_registry_saves(status, created_at);
