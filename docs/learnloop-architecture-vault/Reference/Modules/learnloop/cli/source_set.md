---
title: "learnloop.cli.source_set"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/source_set.py"
source_paths:
  - "src/learnloop/cli/source_set.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.cli"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.cli.source_set module"
  - "src/learnloop/cli/source_set.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.source_set`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps source set behavior inside its owning package, [[Reference/Modules/learnloop/cli/_package|learnloop.cli]]. Its public surface centers on `source_set_create`, `source_set_add`, `source_set_update`, `source_set_list`, `source_set_show`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/source_set.py](../../../../../../src/learnloop/cli/source_set.py) |
| Source lines | 110 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `source_set_create(set_id: Annotated[str, typer.Argument(help='Source-set id.')], subject_id: Annotated[str, typer.Option('--subject', help='Subject id the set belongs to.')], title: Annotated[str, typer.Option('--title', help='Human title.')]='', json_output: Annotated[bool, typer.Option('--json')]=False, vault: Annotated[Path | None, typer.Option('--vault')]=None) -> None` ([source](../../../../../../src/learnloop/cli/source_set.py), line 8) — Create an empty source collection (§4.3).
- `source_set_add(set_id: Annotated[str, typer.Argument(help='Source-set id.')], source_id: Annotated[str, typer.Option('--source', help='Library source id.')], revision_id: Annotated[str, typer.Option('--revision', help='Pinned revision id (required, §4.3).')], role: Annotated[str, typer.Option('--role', help='Membership role (open string).')]='reference', units: Annotated[list[str] | None, typer.Option('--unit', help='Scope unit id (repeatable). Empty = whole artifact.')]=None, priority: Annotated[int, typer.Option('--priority')]=1, json_output: Annotated[bool, typer.Option('--json')]=False, vault: Annotated[Path | None, typer.Option('--vault')]=None) -> None` ([source](../../../../../../src/learnloop/cli/source_set.py), line 24) — Add a pinned source to a collection (membership owns role/scope, §4.3).
- `source_set_update(set_id: Annotated[str, typer.Argument(help='Source-set id.')], title: Annotated[str | None, typer.Option('--title')]=None, json_output: Annotated[bool, typer.Option('--json')]=False, vault: Annotated[Path | None, typer.Option('--vault')]=None) -> None` ([source](../../../../../../src/learnloop/cli/source_set.py), line 63) — Update a collection's title (membership edits use add).
- `source_set_list(json_output: Annotated[bool, typer.Option('--json')]=False, vault: Annotated[Path | None, typer.Option('--vault')]=None) -> None` ([source](../../../../../../src/learnloop/cli/source_set.py), line 81) — List source collections.
- `source_set_show(set_id: Annotated[str, typer.Argument(help='Source-set id.')], json_output: Annotated[bool, typer.Option('--json')]=False, vault: Annotated[Path | None, typer.Option('--vault')]=None) -> None` ([source](../../../../../../src/learnloop/cli/source_set.py), line 101) — Show a collection's members, roles, and scopes.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `module`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `upsert_source_set`; calls `upsert_source_set`

### Platform and third-party dependencies

- Standard library: `__future__`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_cli_generate_practice.py](../../../../../../tests/test_cli_generate_practice.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_cli_ingest.py](../../../../../../tests/test_cli_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_teach_back_generation.py](../../../../../../tests/test_teach_back_generation.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/source_set.py](../../../../../../src/learnloop/cli/source_set.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
