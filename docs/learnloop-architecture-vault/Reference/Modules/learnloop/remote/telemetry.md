---
title: "learnloop.remote.telemetry"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/remote/telemetry.py"
source_paths:
  - "src/learnloop/remote/telemetry.py"
source_commit: "52756865dbdcfd48e1fe2adbd6c7d87996a15d65"
source_commit_timestamp: "2026-11-04T09:17:25-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.remote"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.remote.telemetry module"
  - "src/learnloop/remote/telemetry.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-remote"
---

# `learnloop.remote.telemetry`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/remote/_package|learnloop.remote]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.remote.telemetry` exists within [[Reference/Modules/learnloop/remote/_package|learnloop.remote]] to own the behavior summarized by its module contract: Every chat tool call in the existing ledgers (spec_mcp_frontend_c1 §5).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/remote/telemetry.py](../../../../../../src/learnloop/remote/telemetry.py) |
| Source lines | 239 |
| Owning package | [[Reference/Modules/learnloop/remote/_package|learnloop.remote]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `52756865dbdcfd48e1fe2adbd6c7d87996a15d65` |
| Commit timestamp | `2026-11-04T09:17:25-05:00` |

## Public API

- `canonical_hash(value: Any) -> str` ([source](../../../../../../src/learnloop/remote/telemetry.py), line 62)
- `bounded_arguments(arguments: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/remote/telemetry.py), line 80) — A tool call's arguments as the ledger keeps them (the topic, the query, the ids, the counts): each string at most :data:`ARGUMENT_CHARS`, each list at most :data:`ARGUMENT_ITEMS` items, at most :data:`ARGUMENT_KEYS` names; anything deeper is kept as bounded text.
- `class CallOrigin` ([source](../../../../../../src/learnloop/remote/telemetry.py), line 94) — Where a call came from, read from the request (hints only: never authority).
  - `__post_init__(self) -> None` (line 101; internal)
- `record_shown_passages(repository: Repository, keys: Sequence[str], *, call_id: str, source_versions: Mapping[str, Any] | None=None, clock: Clock | None=None, exposure_fields: Mapping[str, Any] | None=None) -> list[str]` ([source](../../../../../../src/learnloop/remote/telemetry.py), line 108) — Exposure first, always: one row per span a chat tool is about to show.
- `record_tool_call(repository: Repository, *, call_id: str, tool: str, origin: CallOrigin, arguments: Any, result: Any, status: str, summary: Mapping[str, Any] | None=None, error_code: str | None=None, duration_ms: int | None=None, learning_object_ids: Sequence[str]=(), exposure_event_ids: Sequence[str]=(), algorithm_version: str | None=None, adapter_version: str | None=None, started_at: str | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/remote/telemetry.py), line 120) — The call's ``interaction_events`` row (its id).
- `chat_activity(repository: Repository, *, days: int=7, limit: int=20, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/remote/telemetry.py), line 181) — What the chat frontend did in the last ``days`` days (read-only).

### Module constants

- `CHAT_TOOL_CALL_KIND` ([src/learnloop/remote/telemetry.py](../../../../../../src/learnloop/remote/telemetry.py), line 39)
- `CHAT_HOST_ORIGIN` ([src/learnloop/remote/telemetry.py](../../../../../../src/learnloop/remote/telemetry.py), line 40)
- `CHAT_SURFACE` ([src/learnloop/remote/telemetry.py](../../../../../../src/learnloop/remote/telemetry.py), line 41)
- `CHAT_EXPOSURE_ENTITY` ([src/learnloop/remote/telemetry.py](../../../../../../src/learnloop/remote/telemetry.py), line 42)
- `CHAT_EXPOSURE_CONTEXT` ([src/learnloop/remote/telemetry.py](../../../../../../src/learnloop/remote/telemetry.py), line 46)
- `HOSTS` ([src/learnloop/remote/telemetry.py](../../../../../../src/learnloop/remote/telemetry.py), line 47)
- `TRANSPORTS` ([src/learnloop/remote/telemetry.py](../../../../../../src/learnloop/remote/telemetry.py), line 48)
- `PAYLOAD_SCHEMA_VERSION` ([src/learnloop/remote/telemetry.py](../../../../../../src/learnloop/remote/telemetry.py), line 50)
- `ACTOR` ([src/learnloop/remote/telemetry.py](../../../../../../src/learnloop/remote/telemetry.py), line 51)
- `ARGUMENT_CHARS` ([src/learnloop/remote/telemetry.py](../../../../../../src/learnloop/remote/telemetry.py), line 54)
- `ARGUMENT_ITEMS` ([src/learnloop/remote/telemetry.py](../../../../../../src/learnloop/remote/telemetry.py), line 56)
- `ARGUMENT_KEYS` ([src/learnloop/remote/telemetry.py](../../../../../../src/learnloop/remote/telemetry.py), line 59)

### Explicit exports

`__all__` declares:

- `ACTOR`
- `CHAT_EXPOSURE_CONTEXT`
- `CHAT_EXPOSURE_ENTITY`
- `CHAT_HOST_ORIGIN`
- `CHAT_SURFACE`
- `CHAT_TOOL_CALL_KIND`
- `CallOrigin`
- `HOSTS`
- `PAYLOAD_SCHEMA_VERSION`
- `bounded_arguments`
- `canonical_hash`
- `chat_activity`
- `record_shown_passages`
- `record_tool_call`

## Internal implementation anchors

- `_bounded(value: Any, *, depth: int=0) -> Any` ([source](../../../../../../src/learnloop/remote/telemetry.py), line 67)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/mcp|learnloop.cli.mcp]] — imports `chat_activity`; statically calls `chat_activity`
- [[Reference/Modules/learnloop/remote/sources|learnloop.remote.sources]] — imports `CHAT_EXPOSURE_CONTEXT`, `record_shown_passages`; statically calls `record_shown_passages`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/salience_firewall|learnloop.attempts.salience_firewall]] — imports `salience_payload`; calls `salience_payload`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/instructional/interventions|learnloop.instructional.interventions]] — imports `record_shown_spans`; calls `record_shown_spans`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/mcp|learnloop.cli.mcp]], [[Reference/Modules/learnloop/remote/sources|learnloop.remote.sources]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_learner_data_relax_2.py](../../../../../../tests/test_learner_data_relax_2.py) — direct import
  - `test_the_mcp_ledger_row_carries_its_arguments`

## Modification guidance

- Make changes here when the responsibility remains telemetry within learnloop.remote; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/remote/telemetry.py](../../../../../../src/learnloop/remote/telemetry.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
