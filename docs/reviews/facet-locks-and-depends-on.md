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

## 2. What was built

### Part 1: facet locks removed

**`can_apply`** (`curriculum/curriculum_locks.py`) lost every facet arm:
accrued attempt evidence, independent surface groups, independent mass, an
active goal's certified scope, misconceptions, and probes on an LO using the
facet. Facet merge and split are now always legal and review-required. The
learning-object arm stays: a destructive op on an LO (or one of its practice
items) is refused while that LO has recorded attempts. `identity_locks()`
(the read adapter) is gone, and with it a per-facet `can_apply` loop on
every `get_knowledge_map` call.

**Merges, absorbs, dedupe.**
- `merge_registered_facets` has no `merge_locked` parameter and no
  `identity_locked` refusal. Each action records `detail.evidence`: which of
  its facets carried graded evidence (surface groups, independent mass)
  when it applied. That is the provenance of what the merge re-keyed;
  nothing is refused because of it.
- `describe()` returns `evidenced_facets` (and `reworded` for a reword)
  instead of `locked` / `lock_sources`. Rows written before this change
  keep their `lock_reasons` on disk and show no evidence.
- `run_dedupe` drops `locked_facets`, `lock_policy` and `locked_proposals`
  and reports `evidenced_facets`.
- The attach plan drops `survivor_lock_reasons`. `_normalize` grows a
  registered facet's examples on an absorb whatever its history. A
  precondition still stays alias-only: that is §10.2 additivity, not a lock.
- **Held back, unchanged:** a retiree that a graded criterion names together
  with the survivor at one capability stays registered (review F1). This
  holds for the judge's merge, dedupe, recovery and the owner's registry
  merge.

**The owner's merge** (`curriculum/subject_registry.propose_facet_merge`,
used by registry review, coarsening and the facet inspector) now applies
live through `merge_registered_facets`:
- `origin = 'registry'`, `judge = 'owner'`;
- an owner `same` verdict appended to `judgment_ledger` (task `same_facet`);
- the result carries the action id and its undo.

Until now it refused a locked facet. Otherwise it filed a facet `deactivate`
review item that proposal apply cannot compile; I checked this on a test
vault: "Deactivate is only supported for Learning Objects and concept edges
in this slice, not facet". The method keeps its RPC name, so the desktop
bridge is unchanged, but its client cache invalidation is now `mutatingAll`.

**What locks protected becomes history: facet versions.**
- `_compile_facet` (proposal apply, the one in-app path that writes an
  existing facet) compares the entry before and after the write over
  `MEANING_FIELDS`: kind, claim, description, preconditions, postconditions,
  applicability, non-goals.
- When one changes, the write bumps `version` by one. A `facet_version` side
  effect in the write-ahead apply protocol records a `reword` action. That
  action keeps the replaced entry and the written one, the changed fields,
  the facet's evidence, the proposal and its synthesis run.
- Undo (`learnloop facets undo`, the facet inspector's history, the ingest
  panel) restores the old wording and version. It refuses if the facet
  changed since, naming the later action. A reword moves no evidence (the
  facet keeps its id), so its undo re-syncs without re-folding any learning
  object.
- Growth-only writes (aliases, examples) are not versions.
- This covers append restructures, edited payloads, and a re-bootstrap whose
  minted id collides with a registered facet.

**Synthesis and append gates.**
- `_bootstrap_lock_refusal` and the `subject_identity_locked` refusal are
  removed, for bootstrap and for revalidation of a preserved candidate.
  Bootstrap used to refuse in a vault with any locked facet, even for a new
  subject.
- `StudyMapError.lock_reasons` and its consumers (jobs, CLI, sidecar) are
  removed.
- The `lock_guard` gate keeps its name and now fires only for the
  learning-object arm.
- The append neighbourhood no longer carries `lock_reasons`. Append prompt
  rule 6 now says a facet reword keeps the old wording and an LO with
  attempts cannot be restructured.

**Restructure requests** (`queue_restructure_request`) no longer require a
locked facet. The inspector's "propose split…" queues a split request for
any facet (there is no split endpoint), and the maintenance notice no longer
says "locked".

**Display.** Padlocks are removed from the knowledge map, the well view
ring, the recipe editor picker and the inspector autocomplete. Also removed:
- the lock legend;
- the registry review "locked / pre-lock" pills and the disabled merge
  button;
- the inspector lock section and its locked-merge branch;
- the ingest panel's "identity locked: …" label.

Added in their place:
- the facet's `v<version>` pill;
- a **History** section in the inspector (rewords show "was: <old
  wording>"), each entry with its undo;
- the ingest panel's line "re-keys N facets' recorded evidence to the
  survivor";
- reword rows in the ingest panel with both wordings.

**Config.** `[locks]` (`facet_lock_mass`, `facet_surface_groups`) and
`facet_identity.merge_locked_facets` stay in the schema with their defaults
and are never read.
- Removing them would move every recorded defaults snapshot (mvp-0.9 to
  mvp-0.16) for no serving change; all 8 snapshots are unchanged (checked).
- The template no longer writes `[locks]`.
- Doctor reports `config:retired_setting` when a vault sets either key.
- The configuration reference marks both COMPAT.

**Migration 188** rebuilds `facet_identity_actions` (WORKFLOW, same columns,
rows and indexes): `action` gains `reword`, and `origin` gains `proposal`
and `registry`. The head fixture was upgraded on a backup-API copy
(checkpointed, `journal_mode=DELETE`, `integrity_check` ok,
`foreign_key_check` clean) and renamed `migration_head_188`. Its README and
the 13 test/script paths were updated, and `SCHEMA_HEAD` moved to 188 in
both reference scripts. Numbers 184-187 are placeholders for branches in
flight; expect a renumber at merge.

**Specs.** `spec_knowledge_model.md` (revision 5):
- §3.4 is rewritten around live merges with undo, the held-back case and
  facet versions;
- §12.1 (`can_apply`: the learning-object arm only), §12.2, §13, §15, §16
  and §18 are aligned with it;
- the "restructure-with-history" milestone is annotated as delivered in this
  form.

`spec_source_ingestion_v2.md`: §5.7, §8.1, §8.2, §10.2 table, §10.3 and the
§14 acceptance line.

### Part 2: criterion `depends_on`

- **Normalize.** `_keep_sibling_criterion_dependencies` runs per practice
  item in `_normalize`, which append reuses. It keeps a criterion's
  `depends_on` entries only when they name a sibling criterion id of the
  same item, not itself, and drops repeats. Everything else (facet ids,
  facet client ids, blueprint ids, other items' criteria, self) is dropped,
  with one `criterion_dependency` review diagnostic per item in
  `dropped_diagnostics`.
- **Fail-first.** Before the fix, the new test's synthesis did not even
  reach the assertion: the self-reference made the gates hard-fail the
  whole paid build (dependency cycle). The test failed, then passed after
  the fix.
- **Prompt.** Bootstrap rule 5 now says a criterion's `depends_on` names
  only sibling criterion `id`s, never facet, blueprint, learning-object,
  recipe or client ids. It also asks for an `id` on any criterion a sibling
  depends on. Append rule 2 says the same. Versions moved:

  | Prompt | Old version | New version |
  |---|---|---|
  | Bootstrap synthesis | `mvp-1.1-brief-authoring-presets` | `mvp-1.3-sibling-criterion-dependencies` |
  | Bootstrap synthesis, facet identity | `mvp-1.2-one-facet-per-testable-skill` | `mvp-1.3-one-facet-per-testable-skill-sibling-criterion-dependencies` |
  | Append | (bumped) | `mvp-0.10-append-no-locks-sibling-criterion-dependencies` |
  | Append, facet identity | (bumped) | `mvp-0.10-append-one-facet-per-testable-skill-no-locks-sibling-criterion-dependencies` |

  Cached shard checkpoints and completed runs keyed on the old versions are
  not reused, as intended.
- **`learnloop doctor --fix-content [--dry-run]`** (`ops/content_fixes.py`).
  It runs before the doctor report, so the report describes the repaired
  vault.
  - The dry run lists every edit (item, criterion, removed and kept
    entries) and writes nothing.
  - The apply holds the vault mutation lock and edits only
    `grading_rubric.criteria[*].depends_on` by a ruamel round trip. Each
    file goes through a staged, fsynced temp file and an atomic rename, and
    only after the new text reads back, outside the vault, as the same item
    with only those lists changed. Otherwise the file is listed under
    `not_rewritten`.
  - An unparseable item is listed under `unreadable` and left alone.
  - `--dry-run` without `--fix-content` exits 2.
  - The report's note says each edited item's `rubric_content_hash`
    changes. Its next presentation snapshots a new assessment-contract
    version, and graded attempts keep the contract they were graded
    against.

## 3. What else depended on locks, and the decisions

| Dependency | Decision | Reason |
|---|---|---|
| **Identity**: facet merge/split/reword legality | Removed | A merge is an alias plus `facet_merges` resolved at replay, with an exact undo; history is immutable observations against immutable contract versions. The one hazard (a graded criterion naming both facets) is held back. |
| **Identity**: rewording an evidenced facet | Facet version with undo | What locks actually protected; kept as history instead of refusal (handoff). |
| **Identity**: bootstrap refusal | Removed | It was a proxy for "this vault has history" and blocked every new study map in an evidenced vault. Facet overwrites are now versions; practice-item rewrites are contract versions; proposals stay reviewable. |
| **Identity**: learning-object arm (LO with attempts) | Kept | Not a facet lock; the owner's decision covered facets. Open question 1. |
| **Scoring / serving** | None existed | No projection, scheduler or grading path read a lock. `facet_independence_evidence` (also used by the KM2 sim gate test) stays as evidence provenance. |
| **Display** | Removed padlocks, lock chips, "pre-lock" pills, lock legend and lock labels; added version and history | A padlock on a facet nothing locks would be a UI claim that does not happen (frictionless-defaults rule). |
| **Restructure requests** | Kept as a split request for any facet | Still the only way to record a split. |
| **Config keys** | Kept, unread, doctor warns | Snapshot stability (see §2). |

**Serving: no change and no successor.** Merges were already live by
default (`merge_locked_facets = true`). This stage changes which content
operations are allowed and adds content history. It does not change scoring,
scheduling, projection or what is served. Kill switches are unchanged
(`facet_identity.enabled`).

## 4. Demonstration on backup-API copies (no paid calls)

Copies were made with `learnloop.db.copies.copy_tree_with_databases` from
the worktree's tracked `fixtures/probability` and `fixtures/arxiv_v2` into
`fixtures-local/fl-*-fixcontent`. The working vaults were not opened
otherwise.

| Vault copy | `criterion:unknown_dependency` before | Dry run | Applied | After |
|---|---|---|---|---|
| probability | 46 | 46 entries, 28 criteria, 13 items, 1 unreadable | same, 0 not rewritten | **0** |
| arxiv_v2 | 46 | 46 entries, 38 criteria, 15 items | same, 0 not rewritten | **0** |

- On probability the removed entries were facet ids (11 `facet_…`, 24
  hyphenated facet client ids such as `facet-binomial-coefficient`) and 11
  blueprint ids (`bp_…`). No criterion kept a dependency, because none had a
  valid one.
- A recursive diff of `subjects/` before and after shows only the
  `depends_on` lines changed, in the 13 files.
- **Grading neutrality, checked:** on all 28 edited items each item's
  `rubric_content_hash` moved. First-error localization
  (`localize_criterion_outcomes`) is identical before and after for every
  pass/fail combination of each item's criteria. A dependency naming no
  criterion was already treated as passed.
- The doctor run also shows the new `config:retired_setting` warning for
  `[locks]` on these copies (expected).

**Facet versions on real data.** On the arxiv_v2 copy I applied a proposal
rewording the claim of 9 facets, one at a time (every 8th registered facet;
one of them carries graded evidence). Each apply wrote `version: 2` and a
`reword` action. Each undo restored `facets.yaml` exactly (normalized
entries equal before and after, 9 of 9).

## 5. The broken YAML file in probability (reported, not fixed)

`subjects/counting/practice-items/pi_exercise_01kyn22qcffk7sae9ttxvz4j5n.yaml`
fails to parse ("mapping values are not allowed here", line 32). Under
`trace_contract.recipes[0].dependencies` the keys are whole checkpoint
sentences. Three are longer than the 80-column line width, and the app's own
YAML writer (`vault/yaml_io._yaml`, ruamel round-trip, default width)
wrapped them over two lines as plain implicit keys. That is invalid YAML. I
reproduced it from scratch with `yaml_to_string` on a dict with a 76-character
key.

**Fix for the file:** put each wrapped key back on one line, quoted. The
same applies to the wrapped list entries under it. For example:

```yaml
dependencies:
  "Define the six missing-value events and express the target as their union.": []
  "Compute the probability of an intersection corresponding to k specified missing values.":
    - "Define the six missing-value events and express the target as their union."
```

Then run `learnloop doctor --vault fixtures/probability`. A one-off repair
command could do it: re-read with a tolerant join of continuation lines, then
re-dump.

**Root-cause fix (successor):** either set a large `width` in
`yaml_io._yaml()`, which re-wraps long plain scalars everywhere on the next
write but is otherwise semantics-neutral, or key `TraceRecipe.dependencies`
by checkpoint index instead of sentence text. Other items with long
trace-checkpoint keys can break the same way on their next write.
`--fix-content` lists such a file as unreadable and never rewrites it.

## 6. Tests added or changed

- **New `tests/test_facet_rewords.py` (6):**
  - an evidenced facet's reword records a version, keeps the old text, and
    its undo restores it, with beliefs unchanged;
  - a growth-only update is not a version;
  - a reword undo refuses after a later edit;
  - no facet arm refuses, and the LO arm still does;
  - the gate lets a facet update through and still guards a practised LO;
  - the inspector RPC shows the history and undoes a reword.
- **New `tests/test_synthesis_criterion_dependencies.py` (6):**
  - normalize keeps siblings only;
  - the prompt text and version;
  - fix-content dry run, apply (idempotent), the CLI (dry run then apply),
    and an unparseable item.
- **Rewritten for no locks:**
  - `test_curriculum_locks.py` (7);
  - lock-policy tests in `test_facet_identity_actions.py`, including "a facet
    that used to be locked merges and undoes exactly" and "dedupe applies a
    set whose facets carry evidence";
  - `test_facet_identity_composition.py`, `test_facet_identity_ingest.py`,
    `test_subject_registry.py` (live owner merge with undo and ledger row;
    the held-back case still refuses), `test_graph_editor_reads.py`,
    `test_graph_edit_proposals.py`;
  - `test_source_set_synthesis.py`: a vault whose facets used to be locked
    still bootstraps.
- **Frontend:**
  - new `FacetInspector.test.tsx` (2): history with old wording and undo, no
    lock text;
  - `FacetIdentityPanel.test.tsx`: evidence label and a reword row with undo;
  - `KnowledgeWellView.test.tsx`: fixture.
- `tests/cli_help_snapshot.json` regenerated (`doctor`, `facets*`).

## 6a. Gate

Run on `5d136445` (clean tree; the commit after it adds only this section
and the real-data reword note in §4).

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **15 contracts kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **8,951 passed**, 0 failed, 46 warnings (existing: mobile host tests, fork and sqlite datetime deprecations), 334 s of test time (1,132 s including waiting for the lock) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **95 passed**, 8,856 deselected, 1 warning, 92 s |
| Frontend (`npm install`, `npm run typecheck`, `npm test`, `npm run frontend:build`) | typecheck clean; **36 files, 184 tests passed**; build ok |
| `cargo check` | not needed: nothing under `src-tauri` changed |
| DB/config references (`db_generate_reference.py`, `db_validate_reference.py`) | schema head 188, 307 table notes, 749 config leaves (723 ACTIVE, 7 COMPAT, 15 DORMANT, 4 LEGACY), **0 errors**; docs-vault validator passed (1,083 notes) |

The first full-suite run on `cf077450` failed one test,
`test_architecture.py::test_function_local_domain_imports_match_the_frozen_edge_inventory`.
The owner merge and `--fix-content` had added function-local cross-domain
imports, and removing locks left two stale inventory entries. `5d136445`
moves those imports to module level (import-linter still kept, a fresh
import of every touched module works) and shrinks the ratchet.

## 7. Deviations

1. **Review file name.** The handoff names `docs/reviews/facet-locks.md`;
   the stage prompt asked for `docs/reviews/facet-locks-and-depends-on.md`,
   which covers both parts.
2. **Every existing facet's reword is versioned, not only an evidenced
   one.** The handoff says "an evidenced facet". Versioning every meaning
   change to a registered facet is simpler and never loses wording. Whether
   the facet carried evidence is recorded on the action.
3. **The owner's registry merge applies live.** The handoff speaks of the
   judge's merges. The registry/inspector merge was a lock-gated review item
   that could never apply, so it now uses the same live merge and undo.
4. **Config keys kept.** The handoff allows "keep `merge_locked_facets`
   with default true only as a compatibility key"; `[locks]` is treated the
   same way, for snapshot stability.

## 8. Files touched

- **New:**
  - `migrations/188_facet_identity_rewords.sql`;
  - `src/learnloop/ops/content_fixes.py`;
  - `tests/test_facet_rewords.py`, `tests/test_synthesis_criterion_dependencies.py`;
  - `apps/learnloop-tauri/src/components/FacetInspector.test.tsx`;
  - this file.
- **Changed, Python:**
  - `curriculum/{curriculum_locks,subject_registry,graph_edit_proposals}.py`;
  - `content/facet_identity/{actions,dedupe,plan}.py`;
  - `content/synthesis/{source_set_synthesis,source_append,append_neighborhood,ai_contracts,synthesis_gates}.py`;
  - `content/proposals/{patches,apply_protocol}.py`;
  - `content/pipeline/jobs.py`;
  - `db/stores/facet_identity.py`;
  - `config/{schema,template}.py`;
  - `ops/{doctor,maintenance_feed}.py`;
  - `cli/{app,facets}.py`;
  - sidecar `handlers/{facet_detail,knowledge_map,registry,graph_edit,ingest}.py`.
- **Changed, frontend:** `api/{dto,client}.ts`, `FacetInspector.tsx`,
  `FacetIdentityPanel.tsx` (+ test), `RegistryReviewScreen.tsx`,
  `KnowledgeMapScreen.tsx`, `KnowledgeWellView.tsx` (+ test),
  `RecipeTreeEditor.tsx`, `MaintenanceScreen.tsx`. Nothing under
  `src-tauri` changed (no RPC was added or removed).
- **Changed, tests:** see §6, plus the head-fixture path in 13 test files.
- **Changed, docs:** `spec_knowledge_model.md`, `spec_source_ingestion_v2.md`,
  the reference generator and validator, and the regenerated database and
  configuration reference.
- **Fixtures:** `migration_head_183` upgraded through 188 and renamed
  `migration_head_188`. `fixtures/linear_algebra`, `probability` and
  `arxiv_v2` were untouched (copies only).

## 9. Migrations

`188_facet_identity_rewords.sql` rebuilds the WORKFLOW table
`facet_identity_actions` with widened CHECKs (no new table, so no
`table_roles` change). Branches in flight hold 184-187. At merge:
- renumber to the next free number;
- rename the head fixture and update its README, the 13 test/script paths
  and both `SCHEMA_HEAD` constants;
- regenerate the references.

## 10. Owner-run commands

No paid calls are needed for anything here.

1. **Repair criterion dependencies** in the working vaults, dry run first:
   ```bash
   uv run learnloop doctor --vault fixtures/probability --fix-content --dry-run
   uv run learnloop doctor --vault fixtures/probability --fix-content
   uv run learnloop doctor --vault fixtures/arxiv_v2 --fix-content --dry-run
   uv run learnloop doctor --vault fixtures/arxiv_v2 --fix-content
   uv run learnloop doctor --vault fixtures/linear_algebra --fix-content --dry-run
   ```
   On the tracked copies the result was 46 entries in 13 items
   (probability) and 46 in 15 (arxiv_v2), and `criterion:unknown_dependency`
   went from 46 to 0. The linear_algebra copy's dry run found nothing to
   change. Your live vaults may differ. Grading does not change.
   Each edited item gets a new assessment-contract version at its next
   presentation.
2. **Fix the broken probability item by hand** (§5), then run
   `uv run learnloop doctor --vault fixtures/probability`. Until then
   `--fix-content` reports it as unreadable and leaves it alone.
3. **Optional:** delete `[locks]` and any `merge_locked_facets` line from
   each vault's `learnloop.toml`. Doctor now warns about both; they do
   nothing.
4. **Facets that used to be locked** can now be merged from the facet
   inspector or registry review (live, with undo). Queued restructure
   requests for locked merges can be done directly.

## 11. Paid calls

None, so cost $0. The stage needed no model call, and the demonstration runs
were deterministic.

## 12. Open questions

1. **The learning-object arm.** It refuses a destructive op on an LO, or one
   of its practice items, once the LO has attempts. That is not a facet lock,
   so I kept it. With immutable assessment-contract versions, a practice-item
   or blueprint rewrite does not reinterpret graded attempts either. Remove
   it too (an append restructure of a practised LO would then apply on
   acceptance, reviewable and with proposal reject), or keep it?
2. **Retire the compatibility keys for real?** Removing `[locks]` and
   `merge_locked_facets` from the schema moves every defaults snapshot
   (mvp-0.9 to mvp-0.16). Do it at the next version bump, or keep them
   unread?
3. **YAML writer width** (§5). Set a large ruamel `width` (re-wraps long
   scalars on the next write of each file), or key trace dependencies by
   checkpoint index? Either stops the long-key corruption.
4. **Module reference notes** (`docs/learnloop-architecture-vault/Reference/Modules`)
   still describe `identity_locks` and the old lock arms. They are
   regenerated by `module_generate.py`, which is outside this gate and
   touches many notes. Regenerate on main after the merge?
