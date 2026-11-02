---
title: "learnloop.db.stores.deliverables"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/deliverables.py"
source_paths:
  - "src/learnloop/db/stores/deliverables.py"
source_commit: "75122bd88322931f60cbb30f9b670b4996acafba"
source_commit_timestamp: "2026-10-31T14:14:14-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.stores.deliverables module"
  - "src/learnloop/db/stores/deliverables.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.deliverables`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.deliverables` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Deliverable curriculum C0b's tables (migration 228): ``deliverable_scope_inputs`` (RAW_LEDGER), ``deliverable_scope_resolutions`` and ``deliverable_path_sections`` (WORKFLOW).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/deliverables.py](../../../../../../../src/learnloop/db/stores/deliverables.py) |
| Source lines | 174 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `75122bd88322931f60cbb30f9b670b4996acafba` |
| Commit timestamp | `2026-10-31T14:14:14-04:00` |

## Public API

- `tables_present(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/deliverables.py), line 30)
- `insert_input(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/deliverables.py), line 60)
- `inputs(connection: sqlite3.Connection, goal_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/deliverables.py), line 64) — The goal's scope inputs in the order the learner gave them.
- `goals_with_inputs(connection: sqlite3.Connection) -> list[str]` ([source](../../../../../../../src/learnloop/db/stores/deliverables.py), line 71)
- `insert_resolution(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/deliverables.py), line 78)
- `latest_resolution(connection: sqlite3.Connection, goal_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/deliverables.py), line 82)
- `resolution(connection: sqlite3.Connection, resolution_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/deliverables.py), line 89)
- `resolver_state(connection: sqlite3.Connection, goal_id: str, state_key: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/deliverables.py), line 94) — The newest resolver row for exactly this state (the cache hit).
- `resolved_goals(connection: sqlite3.Connection) -> list[str]` ([source](../../../../../../../src/learnloop/db/stores/deliverables.py), line 103)
- `insert_path_row(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/deliverables.py), line 110)
- `judged(connection: sqlite3.Connection, goal_id: str, depth: str, state_key: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/deliverables.py), line 114) — The judge's rows for exactly this goal, depth and state (the cache hit).
- `latest_judged(connection: sqlite3.Connection, goal_id: str, depth: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/deliverables.py), line 122) — The newest judgment's rows at this depth (whatever its state).
- `overrides(connection: sqlite3.Connection, goal_id: str, depth: str) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/deliverables.py), line 131) — The learner's newest row per LO at this depth (``none`` included: it clears).
- `rows_naming(connection: sqlite3.Connection, extraction_ids: Iterable[str]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/deliverables.py), line 142)
- `all_path_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/deliverables.py), line 151)

### Module constants

- `INPUT_COLUMNS` ([src/learnloop/db/stores/deliverables.py](../../../../../../../src/learnloop/db/stores/deliverables.py), line 16)
- `RESOLUTION_COLUMNS` ([src/learnloop/db/stores/deliverables.py](../../../../../../../src/learnloop/db/stores/deliverables.py), line 17)
- `PATH_COLUMNS` ([src/learnloop/db/stores/deliverables.py](../../../../../../../src/learnloop/db/stores/deliverables.py), line 21)
- `_JSON` ([src/learnloop/db/stores/deliverables.py](../../../../../../../src/learnloop/db/stores/deliverables.py), line 26)

### Explicit exports

`__all__` declares:

- `INPUT_COLUMNS`
- `PATH_COLUMNS`
- `RESOLUTION_COLUMNS`
- `all_path_rows`
- `goals_with_inputs`
- `inputs`
- `insert_input`
- `insert_path_row`
- `insert_resolution`
- `judged`
- `latest_judged`
- `latest_resolution`
- `overrides`
- `resolution`
- `resolved_goals`
- `resolver_state`
- `rows_naming`
- `tables_present`

## Internal implementation anchors

- `_dicts(cursor: sqlite3.Cursor) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/deliverables.py), line 37)
- `_insert(connection: sqlite3.Connection, table: str, columns: tuple[str, ...], row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/deliverables.py), line 52)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `module`; statically calls `all_path_rows`, `insert_path_row`, `judged`, `latest_judged`, `overrides`, `rows_naming`, `tables_present`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `module`; statically calls `inputs`, `insert_input`, `insert_resolution`, `latest_resolution`, `resolution`, `resolved_goals`, `resolver_state`, `tables_present`
- [[Reference/Modules/learnloop_sidecar/handlers/deliverables|learnloop_sidecar.handlers.deliverables]] — imports `module`; statically calls `judged`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]], [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]], [[Reference/Modules/learnloop_sidecar/handlers/deliverables|learnloop_sidecar.handlers.deliverables]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_curriculum_c2b_past_papers.py](../../../../../../../tests/test_curriculum_c2b_past_papers.py) — direct import
  - `test_ambiguous_subject_sends_the_ids_grouped_by_subject_name_and_the_resolver_picks_its_group`
- [tests/test_curriculum_c3_codex_review.py](../../../../../../../tests/test_curriculum_c3_codex_review.py) — direct import
- [tests/test_curriculum_c3_exam_scoping.py](../../../../../../../tests/test_curriculum_c3_exam_scoping.py) — direct import
  - `test_off_is_c0b_byte_for_byte`
- [tests/test_deliverable_codex_review.py](../../../../../../../tests/test_deliverable_codex_review.py) — direct import
  - `test_f8_a_stop_before_the_receipt_publishes_nothing`
- [tests/test_notes_vault_search.py](../../../../../../../tests/test_notes_vault_search.py) — direct import
  - `test_c2b_r3_f4_several_named_subjects_send_the_grouped_form_for_those`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/deliverables.py](../../../../../../../src/learnloop/db/stores/deliverables.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
