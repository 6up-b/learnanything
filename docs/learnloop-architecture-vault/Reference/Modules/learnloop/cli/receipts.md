---
title: "learnloop.cli.receipts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/receipts.py"
source_paths:
  - "src/learnloop/cli/receipts.py"
source_commit: "f45f737a65729be21d0e4e4b826e4e896972917c"
source_commit_timestamp: "2026-10-12T13:49:19-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
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
  - "learnloop.cli.receipts module"
  - "src/learnloop/cli/receipts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.receipts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.receipts` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: Model-call receipts for one CLI command run.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/receipts.py](../../../../../../src/learnloop/cli/receipts.py) |
| Source lines | 145 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `f45f737a65729be21d0e4e4b826e4e896972917c` |
| Commit timestamp | `2026-10-12T13:49:19-04:00` |

## Public API

- `class CommandReceipts` ([source](../../../../../../src/learnloop/cli/receipts.py), line 35) — The receipt store of one command run, bound to its vault on first use.
  - `__init__(self, fallback_label: str) -> None` (line 38; internal)
  - `owner_id(self) -> str` (line 47; public) — ``<command path>:<run ulid>``, fixed the first time it is read.
  - `bind_vault(self, vault_root: Path) -> None` (line 59; public)
  - `bind_repository(self, repository: Repository) -> None` (line 67; public)
  - `record(self, action: str, event: dict[str, Any]) -> None` (line 70; public)
  - `_store(self) -> Repository | None` (line 76; internal) — The repository to record into, or None when receipts cannot be kept.
- `command_receipts(fallback_label: str) -> Iterator[CommandReceipts]` ([source](../../../../../../src/learnloop/cli/receipts.py), line 106)
- `current_command_recorder()` ([source](../../../../../../src/learnloop/cli/receipts.py), line 116) — The running command's receipt recorder, or None outside a command.
- `bind_command_vault(vault_root: Path) -> None` ([source](../../../../../../src/learnloop/cli/receipts.py), line 127)
- `bind_command_repository(repository: Repository) -> None` ([source](../../../../../../src/learnloop/cli/receipts.py), line 133)

### Module constants

- `CLI_OWNER_KIND` ([src/learnloop/cli/receipts.py](../../../../../../src/learnloop/cli/receipts.py), line 28)
- `RECEIPT_SCHEMA_VERSION` ([src/learnloop/cli/receipts.py](../../../../../../src/learnloop/cli/receipts.py), line 30)

## Internal implementation anchors

- `_command_path() -> str | None` ([source](../../../../../../src/learnloop/cli/receipts.py), line 139) — The running subcommand's path below the program name, e.g.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/ai|learnloop.cli.ai]] — imports `bind_command_vault`; statically calls `bind_command_vault`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `command_receipts`, `current_command_recorder`; statically calls `command_receipts`, `current_command_recorder`
- [[Reference/Modules/learnloop/cli/diagnose|learnloop.cli.diagnose]] — imports `bind_command_repository`, `bind_command_vault`; statically calls `bind_command_repository`, `bind_command_vault`
- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `bind_command_repository`, `bind_command_vault`; statically calls `bind_command_repository`, `bind_command_vault`
- [[Reference/Modules/learnloop/cli/experiments|learnloop.cli.experiments]] — imports `bind_command_repository`
- [[Reference/Modules/learnloop/cli/gaps|learnloop.cli.gaps]] — imports `bind_command_repository`, `bind_command_vault`; statically calls `bind_command_repository`, `bind_command_vault`
- [[Reference/Modules/learnloop/cli/mcp|learnloop.cli.mcp]] — imports `bind_command_vault`; statically calls `bind_command_vault`
- [[Reference/Modules/learnloop/cli/recurrence|learnloop.cli.recurrence]] — imports `bind_command_repository`, `bind_command_vault`; statically calls `bind_command_repository`, `bind_command_vault`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `bind_command_repository`, `bind_command_vault`; statically calls `bind_command_repository`, `bind_command_vault`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `observe_model_calls`; calls `observe_model_calls`
- [[Reference/Modules/learnloop/db/migrate|learnloop.db.migrate]] — imports `applied_versions`; calls `applied_versions`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`, `find_vault_root`; calls `VaultPaths`, `find_vault_root`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `contextvars`, `pathlib`, `typing`
- Third party: `click`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/ai|learnloop.cli.ai]], [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/cli/diagnose|learnloop.cli.diagnose]], [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]], [[Reference/Modules/learnloop/cli/experiments|learnloop.cli.experiments]] and 4 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/rw5c_golden_source.py](../../../../../../tests/rw5c_golden_source.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_ad1_outside_and_cli.py](../../../../../../tests/test_ad1_outside_and_cli.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_ad23_successor.py](../../../../../../tests/test_ad23_successor.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_ad3_monitoring.py](../../../../../../tests/test_ad3_monitoring.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_ad3_relatedness.py](../../../../../../tests/test_ad3_relatedness.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_ad_denial_log.py](../../../../../../tests/test_ad_denial_log.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_ai_compare.py](../../../../../../tests/test_ai_compare.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_approach_maps.py](../../../../../../tests/test_approach_maps.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_attempt_content_state_successor.py](../../../../../../tests/test_attempt_content_state_successor.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_auto_build_spend_report.py](../../../../../../tests/test_auto_build_spend_report.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_batch3_landing.py](../../../../../../tests/test_batch3_landing.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/receipts.py](../../../../../../src/learnloop/cli/receipts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
