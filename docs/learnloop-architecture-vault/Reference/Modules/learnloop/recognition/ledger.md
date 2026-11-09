---
title: "learnloop.recognition.ledger"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/recognition/ledger.py"
source_paths:
  - "src/learnloop/recognition/ledger.py"
source_commit: "workspace/uncommitted @ HEAD cd6759fcb9e7c6a3877c0dd019a9c37b7305f90d"
source_commit_timestamp: "2026-11-09T01:34:53-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
package: "learnloop.recognition"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.recognition.ledger module"
  - "src/learnloop/recognition/ledger.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-recognition"
---

# `learnloop.recognition.ledger`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/recognition/_package|learnloop.recognition]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.recognition.ledger` exists within [[Reference/Modules/learnloop/recognition/_package|learnloop.recognition]] to own the behavior summarized by its module contract: RE0 §4.2: the records the cue label reads, gathered once into a :class:`~learnloop.recognition.cue.CueLedger`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/recognition/ledger.py](../../../../../../src/learnloop/recognition/ledger.py) |
| Source lines | 146 |
| Owning package | [[Reference/Modules/learnloop/recognition/_package|learnloop.recognition]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD cd6759fcb9e7c6a3877c0dd019a9c37b7305f90d` |
| Commit timestamp | `2026-11-09T01:34:53-05:00` |

## Public API

- `attempt_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/recognition/ledger.py), line 39) — Every attempt with what the label and the report read; ``active_seconds`` is None on a database below 252.
- `build(connection: sqlite3.Connection, vault: Any, repository: Any, *, window_hours: float, session_gap_minutes: float, attempts: list[dict[str, Any]] | None=None) -> CueLedger` ([source](../../../../../../src/learnloop/recognition/ledger.py), line 133) — The ledger of ``connection``'s records.

### Module constants

- `_EVERYTHING` ([src/learnloop/recognition/ledger.py](../../../../../../src/learnloop/recognition/ledger.py), line 28)

## Internal implementation anchors

- `_present(connection: sqlite3.Connection, table: str) -> bool` ([source](../../../../../../src/learnloop/recognition/ledger.py), line 31)
- `_columns(connection: sqlite3.Connection, table: str) -> set[str]` ([source](../../../../../../src/learnloop/recognition/ledger.py), line 35)
- `_reveals(connection: sqlite3.Connection) -> list[Exposure]` ([source](../../../../../../src/learnloop/recognition/ledger.py), line 50)
- `_lessons(connection: sqlite3.Connection) -> list[Exposure]` ([source](../../../../../../src/learnloop/recognition/ledger.py), line 59)
- `_methods(connection: sqlite3.Connection, attempts: list[dict[str, Any]]) -> dict[str, bool | None]` ([source](../../../../../../src/learnloop/recognition/ledger.py), line 72) — Whether each attempt's pinned contract froze a required method; None where it has no pinned contract.
- `_followups(connection: sqlite3.Connection, attempts: list[dict[str, Any]]) -> frozenset[str]` ([source](../../../../../../src/learnloop/recognition/ledger.py), line 97) — The attempts bound to a follow-up of an earlier miss.
- `_checks(connection: sqlite3.Connection) -> frozenset[str]` ([source](../../../../../../src/learnloop/recognition/ledger.py), line 122) — The attempts RO5's randomized daily checks resolved to (whatever the grade later did with them).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/recognition/report|learnloop.recognition.report]] — imports `module`; statically calls `attempt_rows`, `build`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/data_capture/reading_exposures|learnloop.data_capture.reading_exposures]] — imports `module`; calls `read`
- [[Reference/Modules/learnloop/db/stores/write_provenance|learnloop.db.stores.write_provenance]] — imports `pinned_contract_ids`; calls `pinned_contract_ids`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `contract_required_method`; calls `contract_required_method`
- [[Reference/Modules/learnloop/recognition/cue|learnloop.recognition.cue]] — imports `CueLedger`, `Exposure`, `LESSON`, `READING`; calls `CueLedger`, `Exposure`
- [[Reference/Modules/learnloop/router_objective/checks|learnloop.router_objective.checks]] — imports `module`; calls `resolve`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/recognition/report|learnloop.recognition.report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_re0_capture.py](../../../../../../tests/test_re0_capture.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains ledger within learnloop.recognition; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/recognition/ledger.py](../../../../../../src/learnloop/recognition/ledger.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
