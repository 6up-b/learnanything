---
title: "learnloop.cli.card"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/card.py"
source_paths:
  - "src/learnloop/cli/card.py"
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
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Inspect Persistent State"
aliases:
  - "learnloop.cli.card module"
  - "src/learnloop/cli/card.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.card`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps card behavior inside its owning package, [[Reference/Modules/learnloop/cli/_package|learnloop.cli]]. Its public surface centers on `card_write`, `card_reword`, `card_retire`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/card.py](../../../../../../src/learnloop/cli/card.py) |
| Source lines | 78 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `card_write(learning_object_id: Annotated[str, typer.Argument(help='Learning Object to attach the card to.')], prompt: Annotated[str, typer.Option('--prompt', help='The question.')], answer: Annotated[str, typer.Option('--answer', help='The expected answer.')], vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/card.py), line 11) — Author a new card of your own.
- `card_reword(practice_item_id: Annotated[str, typer.Argument(help='Card id.')], prompt: Annotated[str | None, typer.Option('--prompt', help='New prompt wording.')]=None, answer: Annotated[str | None, typer.Option('--answer', help='New expected answer.')]=None, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/card.py), line 34) — Reword a card in place (prompt and/or expected answer).
- `card_retire(practice_item_id: Annotated[str, typer.Argument(help='Card id.')], reason: Annotated[str, typer.Option('--reason', help='Typed reason (see error output for the taxonomy).')], note: Annotated[str | None, typer.Option('--note', help='Optional free-text note.')]=None, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/card.py), line 57) — Retire a card: never served again, all history kept.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `module`
- [[Reference/Modules/learnloop/content/authoring/item_authoring|learnloop.content.authoring.item_authoring]] — imports `ItemAuthoringError`, `author_item`, `edit_item`, `retire_item`; calls `author_item`, `edit_item`, `retire_item`

### Platform and third-party dependencies

- Standard library: `__future__`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Inspect Persistent State]]

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

1. Modify [src/learnloop/cli/card.py](../../../../../../src/learnloop/cli/card.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
