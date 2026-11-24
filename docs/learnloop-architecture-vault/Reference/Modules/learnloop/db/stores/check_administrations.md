---
title: "learnloop.db.stores.check_administrations"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/check_administrations.py"
source_paths:
  - "src/learnloop/db/stores/check_administrations.py"
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
  - "learnloop.db.stores.check_administrations module"
  - "src/learnloop/db/stores/check_administrations.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.check_administrations`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.check_administrations` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: The only SQL for the Reader's inline check administrations (migration 270): ``check_administrations`` (WORKFLOW: the open administration and the lock it holds with Today) and the append-only ``check_veil_sets`` (RECEIPT: what each protection computation veiled and what had been…

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/check_administrations.py](../../../../../../../src/learnloop/db/stores/check_administrations.py) |
| Source lines | 171 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `table_present(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/check_administrations.py), line 20)
- `insert_administration(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/check_administrations.py), line 44)
- `by_token(connection: sqlite3.Connection, token: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/check_administrations.py), line 56)
- `by_request(connection: sqlite3.Connection, request_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/check_administrations.py), line 60)
- `open_administration(connection: sqlite3.Connection) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/check_administrations.py), line 64) — The one open administration, if any (the partial unique index allows no second).
- `open_commitments(connection: sqlite3.Connection) -> frozenset[str]` ([source](../../../../../../../src/learnloop/db/stores/check_administrations.py), line 70) — The commitments an open administration holds (the lock Today reads).
- `administration_counts(connection: sqlite3.Connection) -> dict[str, int]` ([source](../../../../../../../src/learnloop/db/stores/check_administrations.py), line 79) — Per commitment, how many inline administrations it has had (a due check's handle is spent by each begin).
- `held_windows(connection: sqlite3.Connection) -> dict[str, list[tuple[str, str | None]]]` ([source](../../../../../../../src/learnloop/db/stores/check_administrations.py), line 88) — Per commitment, every inline administration's (opened_at, closed_at): the times it held the check.
- `set_exposure(connection: sqlite3.Connection, token: str, exposure: Sequence[Mapping[str, Any]], exposure_ids: Sequence[str] | None=None) -> bool` ([source](../../../../../../../src/learnloop/db/stores/check_administrations.py), line 100) — Record the exposure (and the client's ids of the openings recorded); False when the row is not open, or a submission is reserved on it (the caller then refuses: nothing is recorded).
- `set_submission(connection: sqlite3.Connection, token: str, submission_id: str, *, pending_before: bool) -> bool` ([source](../../../../../../../src/learnloop/db/stores/check_administrations.py), line 117) — Name the submission before the attempt is recorded (a crash between the attempt and the close is found by it), with whether the check was pending then.
- `close(connection: sqlite3.Connection, token: str, *, state: str, now: str, attempt_id: str | None=None, outcome: Mapping[str, Any] | None=None, unreserved: bool=False) -> bool` ([source](../../../../../../../src/learnloop/db/stores/check_administrations.py), line 131) — Close an open administration (with its attempt and the outcome it promised).
- `insert_veil_set(connection: sqlite3.Connection, *, veil_set_id: str, token: str, commitment_id: str, kind: str, method: str, veiled: Iterable[Mapping[str, Any]], opened: Iterable[Mapping[str, Any]], now: str) -> int` ([source](../../../../../../../src/learnloop/db/stores/check_administrations.py), line 145)
- `veil_sets(connection: sqlite3.Connection, token: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/check_administrations.py), line 159)

### Module constants

- `_ADMIN_COLUMNS` ([src/learnloop/db/stores/check_administrations.py](../../../../../../../src/learnloop/db/stores/check_administrations.py), line 12)
- `_SELECT` ([src/learnloop/db/stores/check_administrations.py](../../../../../../../src/learnloop/db/stores/check_administrations.py), line 41)

### Explicit exports

`__all__` declares:

- `by_request`
- `by_token`
- `close`
- `insert_administration`
- `insert_veil_set`
- `open_administration`
- `open_commitments`
- `set_exposure`
- `set_submission`
- `table_present`
- `veil_sets`

## Internal implementation anchors

- `_admin(row: sqlite3.Row | Sequence[Any] | None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/check_administrations.py), line 25)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/intent/inline_administration|learnloop.intent.inline_administration]] — imports `module`; statically calls `by_request`, `by_token`, `close`, `insert_administration`, `insert_veil_set`, `open_administration`, `open_commitments`, `set_exposure`, `set_submission`, `veil_sets`
- [[Reference/Modules/learnloop/intent/inline_checks|learnloop.intent.inline_checks]] — imports `module`; statically calls `administration_counts`, `open_administration`, `table_present`
- [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]] — imports `module`, `open_commitments`; statically calls `held_windows`, `open_commitments`
- [[Reference/Modules/learnloop_sidecar/check_hold|learnloop_sidecar.check_hold]] — imports `module`; statically calls `open_administration`, `table_present`
- [[Reference/Modules/learnloop_sidecar/handlers/goal_lens|learnloop_sidecar.handlers.goal_lens]] — imports `module`; statically calls `open_commitments`
- [[Reference/Modules/learnloop_sidecar/handlers/inline_checks|learnloop_sidecar.handlers.inline_checks]] — imports `module`; statically calls `by_request`, `table_present`

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

Static participation evidence comes from [[Reference/Modules/learnloop/intent/inline_administration|learnloop.intent.inline_administration]], [[Reference/Modules/learnloop/intent/inline_checks|learnloop.intent.inline_checks]], [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]], [[Reference/Modules/learnloop_sidecar/check_hold|learnloop_sidecar.check_hold]], [[Reference/Modules/learnloop_sidecar/handlers/goal_lens|learnloop_sidecar.handlers.goal_lens]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/inline_hold_helpers.py](../../../../../../../tests/inline_hold_helpers.py) — direct import
- [tests/test_reader_rd7a_inline_checks.py](../../../../../../../tests/test_reader_rd7a_inline_checks.py) — direct import
  - `test_no_prompt_leaves_when_the_veils_cannot_be_recorded`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/check_administrations.py](../../../../../../../src/learnloop/db/stores/check_administrations.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
