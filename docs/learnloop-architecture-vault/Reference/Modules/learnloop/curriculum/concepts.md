---
title: "learnloop.curriculum.concepts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/curriculum/concepts.py"
source_paths:
  - "src/learnloop/curriculum/concepts.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.curriculum"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Build a Study Map"
aliases:
  - "learnloop.curriculum.concepts module"
  - "src/learnloop/curriculum/concepts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-curriculum"
---

# `learnloop.curriculum.concepts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps concepts behavior inside its owning package, [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]]. Its public surface centers on `ConceptMergeError`, `ConceptMergeResult`, `merge_concepts`.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/curriculum/concepts.py](../../../../../../src/learnloop/curriculum/concepts.py) |
| Source lines | 469 |
| Owning package | [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ConceptMergeError(ValueError)` ([source](../../../../../../src/learnloop/curriculum/concepts.py), line 22)
- `class ConceptMergeResult` ([source](../../../../../../src/learnloop/curriculum/concepts.py), line 27)
  - `as_dict(self) -> dict[str, Any]` (line 35; public)
- `merge_concepts(root: Path, canonical_id: str, duplicate_id: str, *, add_alias: bool=True, dry_run: bool=False, force: bool=False, clock: Clock | None=None) -> ConceptMergeResult` ([source](../../../../../../src/learnloop/curriculum/concepts.py), line 46)

## Internal implementation anchors

- `_merge_concepts_file(path: Path, canonical_id: str, duplicate_id: str, *, add_alias: bool, clock_iso: str, changed_files: set[str], dry_run: bool) -> None` ([source](../../../../../../src/learnloop/curriculum/concepts.py), line 127)
- `_rewrite_relations_file(path: Path, canonical_id: str, duplicate_id: str, changed_files: set[str], *, dry_run: bool) -> None` ([source](../../../../../../src/learnloop/curriculum/concepts.py), line 164)
- `_rewrite_goals_file(path: Path, canonical_id: str, duplicate_id: str, changed_files: set[str], *, dry_run: bool, clock_iso: str) -> None` ([source](../../../../../../src/learnloop/curriculum/concepts.py), line 208)
- `_rewrite_error_types_file(path: Path, canonical_id: str, duplicate_id: str, changed_files: set[str], *, dry_run: bool, clock_iso: str) -> None` ([source](../../../../../../src/learnloop/curriculum/concepts.py), line 241)
- `_rewrite_subject_graph_file(path: Path, canonical_id: str, duplicate_id: str, changed_files: set[str], *, dry_run: bool) -> None` ([source](../../../../../../src/learnloop/curriculum/concepts.py), line 265)
- `_rewrite_learning_object_file(path: Path, canonical_id: str, duplicate_id: str, changed_files: set[str], *, dry_run: bool, clock_iso: str) -> None` ([source](../../../../../../src/learnloop/curriculum/concepts.py), line 286)
- `_rewrite_note_file(path: Path, canonical_id: str, duplicate_id: str, changed_files: set[str], *, dry_run: bool, clock_iso: str) -> None` ([source](../../../../../../src/learnloop/curriculum/concepts.py), line 313)
- `_rewrite_pending_proposal_refs(repository: Repository, canonical_id: str, duplicate_id: str, *, clock_iso: str) -> None` ([source](../../../../../../src/learnloop/curriculum/concepts.py), line 336)
- `_rewrite_proposal_payload(payload: Any, canonical_id: str, duplicate_id: str) -> Any` ([source](../../../../../../src/learnloop/curriculum/concepts.py), line 380)
- `_record_concept_merge_events(repository: Repository, canonical_id: str, duplicate_id: str, *, clock_iso: str) -> str` ([source](../../../../../../src/learnloop/curriculum/concepts.py), line 393)
- `_write_yaml_if_changed(path: Path, data: dict[str, Any], changed_files: set[str], *, dry_run: bool, force_changed: bool=True) -> None` ([source](../../../../../../src/learnloop/curriculum/concepts.py), line 427)
- `_rewrite_value(value: Any, canonical_id: str, duplicate_id: str) -> Any` ([source](../../../../../../src/learnloop/curriculum/concepts.py), line 442)
- `_rewrite_list(values: list[Any], canonical_id: str, duplicate_id: str) -> list[Any]` ([source](../../../../../../src/learnloop/curriculum/concepts.py), line 446)
- `_unique_strings(values: Any, *, exclude: set[Any] | None=None) -> list[str]` ([source](../../../../../../src/learnloop/curriculum/concepts.py), line 450)
- `_relative(root: Path, path: str) -> str` ([source](../../../../../../src/learnloop/curriculum/concepts.py), line 465)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `ConceptMergeError`, `merge_concepts`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`; calls `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `sync_vault_state`; calls `sync_vault_state`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] — imports `read_markdown_with_frontmatter`, `read_yaml`, `write_markdown_with_frontmatter`, `write_yaml`; calls `read_markdown_with_frontmatter`, `read_yaml`, `write_markdown_with_frontmatter`, `write_yaml`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_concepts.py](../../../../../../tests/test_concepts.py) — direct import
  - `test_merge_concepts_dry_run_does_not_write`
  - `test_merge_concepts_rewrites_vault_references`

## Modification guidance

- Change concepts policy here when curriculum owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/curriculum/concepts.py](../../../../../../src/learnloop/curriculum/concepts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
