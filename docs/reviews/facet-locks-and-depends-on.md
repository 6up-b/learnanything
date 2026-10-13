# Facet locks removed; synthesis criterion `depends_on` checked

Branch `facets/locks-and-depends-on` from `main` at `11177f6f` (mvp-0.16,
migrations to 183). Owner-directed (2026-10-12). Prompts:
`docs/specs/implementation_handoffs.md` §4, "Facet locks no longer block
merges", and the doctor investigation of 2026-10-12 (criterion `depends_on`).

## 1. Plan (written before coding)

### Part 1: facet locks no longer block anything

Inventory of every place a facet lock blocks or alters a merge, absorb,
dedupe or edit (found by reading every caller of `curriculum_locks`):

| Where | What the lock did today | Change |
|---|---|---|
| `facet_identity/actions.merge_registered_facets` | refused under `merge_locked_facets = false`; recorded lock reasons | no lock check; records which facets carried evidence (provenance) |
| `facet_identity/dedupe.run_dedupe` | `locked_facets`, `lock_policy`, `locked_proposals` | removed |
| `facet_identity/plan` + `source_set_synthesis._normalize` (attach) | an absorbed example never grew a locked registered facet | grows it; a precondition still stays alias-only (§10.2 additivity, not a lock) |
| `curriculum/subject_registry.propose_facet_merge` | refused a locked facet; otherwise filed a facet `deactivate` review item that proposal apply cannot compile (verified) | applies live through `merge_registered_facets` with undo, owner verdict in `judgment_ledger` |
| `source_set_synthesis._bootstrap_lock_refusal` | refused every create-study-map (and revalidation) in a vault with any locked facet, even for a new subject | removed; a re-bootstrap that rewords an existing facet now writes a facet version (below) |
| `synthesis_gates._gate_lock_guard`, `patches._accept_time_rechecks` | hard-fail / refuse an update or deactivate whose facet closure is locked | facet arms gone; the learning-object arm (the LO has attempts) stays |
| `append_neighborhood` + append prompt rule 6 | showed the model which facets were locked | removed; prompt version bumped |
| `graph_edit_proposals.queue_restructure_request` | only for locked facets | a durable split/merge request for any facet (no split endpoint exists) |
| display: knowledge map, well view, recipe editor, facet inspector, registry review, facet-identity panel | padlocks, "pre-lock" pills, lock reasons, merge disabled | removed (nothing is locked); the inspector merges live with undo |

What locks still protected, in-place rewording of an evidenced facet's
meaning, becomes history instead of a refusal: a proposal apply that changes
an existing facet's `kind`, `claim`, conditions or non-goals bumps its
`version` and records a `reword` action in `facet_identity_actions` (the old
entry kept), undoable with `learnloop facets undo` and from the desktop.

- **`can_apply`** keeps the learning-object arm only (destructive LO and
  practice-item operations on an LO with attempts). That is a blueprint lock,
  not a facet lock; open question.
- **Held back:** a graded criterion naming a retiree and its survivor at one
  capability is still held back (correctness, review F1).
- **Migration 188** widens `facet_identity_actions` CHECKs: `action` gains
  `reword`, `origin` gains `proposal` and `registry`. Head fixture
  183 -> 188.
- **Config:** `[locks]` and `facet_identity.merge_locked_facets` stay in the
  schema as ignored compatibility keys (removing them would move every
  defaults snapshot for no serving change); the template drops `[locks]`;
  doctor warns when a vault sets either.
- **Specs:** knowledge model §3.4, §12.1, §13; ingestion §8.1, §8.2, §10.3.
- **No serving change, no successor:** merges were already live by default;
  this changes which content operations are allowed and adds content history,
  not scoring, scheduling or projection.

### Part 2: criterion `depends_on`

- `_normalize` keeps only `depends_on` entries naming a sibling criterion id of
  the same item (not itself); the rest drop with a `criterion_dependency`
  review diagnostic.
- Prompt: a criterion's `depends_on` names sibling criterion ids only; both
  synthesis prompt versions and the append ones bumped where the text is
  shared.
- `learnloop doctor --fix-content [--dry-run]`: removes invalid `depends_on`
  entries from practice-item YAML under the vault lock; demonstrated on a
  backup-API copy of `fixtures/probability`.
- Tests fail first. No paid calls (none needed).
