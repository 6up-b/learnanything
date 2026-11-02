---
title: "learnloop.db.stores.pf"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/pf.py"
source_paths:
  - "src/learnloop/db/stores/pf.py"
source_commit: "e9ced35e32ffb2bb533ea1845f5dc3794720857b"
source_commit_timestamp: "2026-10-12T16:11:05-04:00"
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
  - "learnloop.db.stores.pf module"
  - "src/learnloop/db/stores/pf.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.pf`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.pf` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: SQL for PF-b candidates, solution skeletons and item fingerprints (migration 174).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/pf.py](../../../../../../../src/learnloop/db/stores/pf.py) |
| Source lines | 219 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e9ced35e32ffb2bb533ea1845f5dc3794720857b` |
| Commit timestamp | `2026-10-12T16:11:05-04:00` |

## Public API

- `insert_candidate(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/pf.py), line 29) — Insert once; a resumed run that regenerates the same id keeps the first row.
- `update_candidate(connection: sqlite3.Connection, candidate_id: str, **fields: Any) -> None` ([source](../../../../../../../src/learnloop/db/stores/pf.py), line 45)
- `candidate(connection: sqlite3.Connection, candidate_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/pf.py), line 58)
- `candidates(connection: sqlite3.Connection, *, where: str='1=1', params: Iterable[Any]=()) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/pf.py), line 63)
- `published_count_between(connection: sqlite3.Connection, start_iso: str, end_iso: str) -> int` ([source](../../../../../../../src/learnloop/db/stores/pf.py), line 70)
- `insert_skeleton(connection: sqlite3.Connection, *, skeleton_id: str, content_hash: str, subject_kind: str, subject_id: str, model_id: str, prompt_version: str, techniques: list[str], operations: list[str], checkpoints: list[str], skeleton_text: str, created_at: str) -> None` ([source](../../../../../../../src/learnloop/db/stores/pf.py), line 79)
- `skeletons_for_hashes(connection: sqlite3.Connection, content_hashes: Iterable[str]) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/db/stores/pf.py), line 93) — Every persisted skeleton per content hash, in a stable order.
- `replace_item_fingerprints(connection: sqlite3.Connection, rows: Iterable[Mapping[str, Any]]) -> tuple[int, int]` ([source](../../../../../../../src/learnloop/db/stores/pf.py), line 112) — DERIVED replacement: clear, then insert the deterministic rows.
- `item_fingerprints(connection: sqlite3.Connection, item_ids: Iterable[str] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/pf.py), line 128)
- `candidate_verdicts(connection: sqlite3.Connection, candidate_ids: Iterable[str]) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/pf.py), line 146) — The latest ledgered verdicts per PF candidate (Slice 2 §5.8: reports read the ledger).
- `verdict_verified(verdicts: Mapping[str, Any], generation_path: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/pf.py), line 192) — The path's complete reference contract passed and no current check failed.
- `verdict_survived(verdicts: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/pf.py), line 206) — No filter failed and the last filter (freshness) passed.
- `verdict_panel(verdicts: Mapping[str, Any]) -> tuple[int, int] | None` ([source](../../../../../../../src/learnloop/db/stores/pf.py), line 212) — (agreeing, total) panel solves recorded with the panel filter verdicts.

### Module constants

- `_VERDICT_TASKS` ([src/learnloop/db/stores/pf.py](../../../../../../../src/learnloop/db/stores/pf.py), line 15)
- `_CANDIDATE_COLUMNS` ([src/learnloop/db/stores/pf.py](../../../../../../../src/learnloop/db/stores/pf.py), line 17)
- `_UPDATABLE` ([src/learnloop/db/stores/pf.py](../../../../../../../src/learnloop/db/stores/pf.py), line 26)
- `REQUIRED_REFERENCE_CHECKS` ([src/learnloop/db/stores/pf.py](../../../../../../../src/learnloop/db/stores/pf.py), line 184)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/hints/map_seeds|learnloop.hints.map_seeds]] — imports `skeletons_for_hashes`; statically calls `skeletons_for_hashes`
- [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]] — imports `module`; statically calls `candidate`, `candidates`, `insert_candidate`, `insert_skeleton`, `skeletons_for_hashes`, `update_candidate`
- [[Reference/Modules/learnloop/ops/pf_publish|learnloop.ops.pf_publish]] — imports `candidate`, `candidate_verdicts`, `published_count_between`, `update_candidate`, `verdict_survived`, `verdict_verified`; statically calls `candidate`, `candidate_verdicts`, `published_count_between`, `update_candidate`, `verdict_survived`, `verdict_verified`
- [[Reference/Modules/learnloop/ops/pf_reports|learnloop.ops.pf_reports]] — imports `module`; statically calls `candidate_verdicts`, `candidates`, `verdict_panel`, `verdict_survived`, `verdict_verified`
- [[Reference/Modules/learnloop/substrate/item_fingerprints|learnloop.substrate.item_fingerprints]] — imports `candidates`, `replace_item_fingerprints`, `skeletons_for_hashes`; statically calls `candidates`, `replace_item_fingerprints`, `skeletons_for_hashes`
- [[Reference/Modules/learnloop/vault/embedding_recipes|learnloop.vault.embedding_recipes]] — imports `skeletons_for_hashes`; statically calls `skeletons_for_hashes`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/hints/map_seeds|learnloop.hints.map_seeds]], [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]], [[Reference/Modules/learnloop/ops/pf_publish|learnloop.ops.pf_publish]], [[Reference/Modules/learnloop/ops/pf_reports|learnloop.ops.pf_reports]], [[Reference/Modules/learnloop/substrate/item_fingerprints|learnloop.substrate.item_fingerprints]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/approach_map_fakes.py](../../../../../../../tests/approach_map_fakes.py) — direct import
- [tests/test_item_fingerprints.py](../../../../../../../tests/test_item_fingerprints.py) — direct import
  - `test_skeletons_from_one_model_at_two_prompt_versions_rebuild_without_a_key_collision`
- [tests/test_pf_generation.py](../../../../../../../tests/test_pf_generation.py) — direct import
  - `test_an_unverified_candidate_cannot_be_published`
  - `test_each_path_is_verified_only_by_its_complete_reference_contract`
  - `test_pilot_report_verdicts_come_from_the_ledger_not_workflow_json`
  - `test_publication_reads_the_ledger_so_forged_workflow_state_cannot_publish`
- [tests/test_practice_index_find.py](../../../../../../../tests/test_practice_index_find.py) — direct import
- [tests/test_required_method_authority.py](../../../../../../../tests/test_required_method_authority.py) — direct import
  - `test_a_variant_with_no_verdict_or_an_edited_stem_is_not_published`
- [tests/test_success_head_cli.py](../../../../../../../tests/test_success_head_cli.py) — direct import
  - `test_loader_reads_phase_5a_skeletons_keyed_by_item_id`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/pf.py](../../../../../../../src/learnloop/db/stores/pf.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
