---
title: "learnloop.activation_journal"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/activation_journal.py"
source_paths:
  - "src/learnloop/activation_journal.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.activation_journal module"
  - "src/learnloop/activation_journal.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.activation_journal`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.activation_journal` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: An activation that did not commit: its journal, and what may open the vault meanwhile.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/activation_journal.py](../../../../../src/learnloop/activation_journal.py) |
| Source lines | 162 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class InterruptedActivation(RuntimeError)` ([source](../../../../../src/learnloop/activation_journal.py), line 55) — The vault's activation did not commit; it is not served until it completes.
- `journal_path(sqlite_path: Path) -> Path` ([source](../../../../../src/learnloop/activation_journal.py), line 59) — The activation journal beside ``sqlite_path``.
- `pending(sqlite_path: Path) -> bool` ([source](../../../../../src/learnloop/activation_journal.py), line 66) — Whether an activation journal stands beside ``sqlite_path``.
- `completing() -> bool` ([source](../../../../../src/learnloop/activation_journal.py), line 72) — Whether this context is completing (or running) the activation itself.
- `completing_activation() -> Iterator[None]` ([source](../../../../../src/learnloop/activation_journal.py), line 79) — Mark this context as the activation's own writer, so its opens are not refused.
- `message(sqlite_path: Path) -> str` ([source](../../../../../src/learnloop/activation_journal.py), line 89) — What to tell the learner: which upgrade did not finish, and the command that completes it.
- `install_completer(completer: Callable[[Path], object] | None) -> None` ([source](../../../../../src/learnloop/activation_journal.py), line 115) — Install the process's completion (an entry point does, at import); None removes it.
- `complete(vault_root: Path, sqlite_path: Path) -> None` ([source](../../../../../src/learnloop/activation_journal.py), line 122) — Complete a journalled activation before an opener attaches, or raise :class:`InterruptedActivation`.
- `refuse_if_interrupted(sqlite_path: Path) -> None` ([source](../../../../../src/learnloop/activation_journal.py), line 144) — Raise :class:`InterruptedActivation` while a journal stands (unless this context completes it).

### Module constants

- `JOURNAL_SUFFIX` ([src/learnloop/activation_journal.py](../../../../../src/learnloop/activation_journal.py), line 46)
- `_COMPLETING` ([src/learnloop/activation_journal.py](../../../../../src/learnloop/activation_journal.py), line 49)
- `_COMPLETER` ([src/learnloop/activation_journal.py](../../../../../src/learnloop/activation_journal.py), line 52)

### Explicit exports

`__all__` declares:

- `JOURNAL_SUFFIX`
- `InterruptedActivation`
- `complete`
- `completing`
- `completing_activation`
- `install_completer`
- `journal_path`
- `message`
- `pending`
- `refuse_if_interrupted`

## Internal implementation anchors

- `_link(sqlite_path: Path) -> tuple[str, str] | None` ([source](../../../../../src/learnloop/activation_journal.py), line 105) — The journalled upgrade's ``(predecessor, target)``, or None for a torn journal (its completion decides).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `module`; statically calls `install_completer`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `refuse_if_interrupted`; statically calls `refuse_if_interrupted`
- [[Reference/Modules/learnloop/ops/upgrades|learnloop.ops.upgrades]] — imports `module`; statically calls `completing_activation`, `journal_path`, `message`, `pending`
- [[Reference/Modules/learnloop/remote/runtime|learnloop.remote.runtime]] — imports `module`; statically calls `message`, `pending`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `module`; statically calls `complete`, `completing`, `pending`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `module`; statically calls `install_completer`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/version_floor|learnloop.version_floor]] — imports `refuse_journal_below_floor`; calls `refuse_journal_below_floor`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `contextvars`, `json`, `pathlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/ops/upgrades|learnloop.ops.upgrades]], [[Reference/Modules/learnloop/remote/runtime|learnloop.remote.runtime]], [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad_denial_log.py](../../../../../tests/test_ad_denial_log.py) — direct import
- [tests/test_upgrades.py](../../../../../tests/test_upgrades.py) — direct import
  - `test_a_failure_before_the_commit_leaves_the_predecessor_readable_and_no_journal`
  - `test_an_activation_that_cannot_complete_stops_the_opener`
  - `test_an_opener_in_a_process_that_cannot_complete_refuses`
  - `test_attaches_that_never_write_refuse_while_the_journal_stands`
- [tests/test_version_floor.py](../../../../../tests/test_version_floor.py) — direct import
  - `test_a_journal_from_the_floor_is_still_completed_by_an_opener`
  - `test_a_journal_naming_a_link_below_the_floor_is_refused`
  - `test_the_upgrade_command_refuses_a_journal_from_below_the_floor_with_the_route`

## Modification guidance

- Make changes here when the responsibility remains activation journal within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/activation_journal.py](../../../../../src/learnloop/activation_journal.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
