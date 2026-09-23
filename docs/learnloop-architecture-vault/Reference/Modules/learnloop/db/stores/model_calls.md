---
title: "learnloop.db.stores.model_calls"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/model_calls.py"
source_paths:
  - "src/learnloop/db/stores/model_calls.py"
source_commit: "5f7340aaf0366e30dca27f6cfc233dae3e37c850"
source_commit_timestamp: "2026-09-23T12:54:18-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.stores.model_calls module"
  - "src/learnloop/db/stores/model_calls.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.model_calls`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.model_calls` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Short transactions for call receipts and validated ingestion checkpoints.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/model_calls.py](../../../../../../../src/learnloop/db/stores/model_calls.py) |
| Source lines | 60 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `5f7340aaf0366e30dca27f6cfc233dae3e37c850` |
| Commit timestamp | `2026-09-23T12:54:18-04:00` |

## Public API

- `class ModelCallStoreMixin` ([source](../../../../../../../src/learnloop/db/stores/model_calls.py), line 13)
  - `record_model_event(self, action: str, event: dict[str, Any], *, owner_kind: str, owner_id: str) -> None` (line 14; public)
  - `model_checkpoint(self, cache_key: str) -> dict[str, Any] | None` (line 37; public)
  - `save_model_checkpoint(self, cache_key: str, *, purpose: str, result: dict[str, Any], usage: dict[str, Any] | None=None) -> None` (line 42; public)
  - `discard_model_checkpoint(self, cache_key: str) -> None` (line 52; public) — Delete a checkpoint whose stored result no longer validates.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `ModelCallStoreMixin`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/scopes|learnloop.db.scopes]] — imports `allow_late_model_records`; calls `allow_late_model_records`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `datetime`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/helpers.py](../../../../../../../tests/helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/test_action_loss.py](../../../../../../../tests/test_action_loss.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/test_activity_backfill.py](../../../../../../../tests/test_activity_backfill.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/test_activity_contract_extensions.py](../../../../../../../tests/test_activity_contract_extensions.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/test_activity_patterns.py](../../../../../../../tests/test_activity_patterns.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/test_activity_substrate.py](../../../../../../../tests/test_activity_substrate.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/test_administration_adapters.py](../../../../../../../tests/test_administration_adapters.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/test_agent_run_tokens.py](../../../../../../../tests/test_agent_run_tokens.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/test_agent_runs.py](../../../../../../../tests/test_agent_runs.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/test_annotations.py](../../../../../../../tests/test_annotations.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/test_answer_calibration_duel.py](../../../../../../../tests/test_answer_calibration_duel.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/test_anti_double_count.py](../../../../../../../tests/test_anti_double_count.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/model_calls.py](../../../../../../../src/learnloop/db/stores/model_calls.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
