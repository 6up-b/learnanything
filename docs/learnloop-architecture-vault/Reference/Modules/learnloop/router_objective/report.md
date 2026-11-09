---
title: "learnloop.router_objective.report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/report.py"
source_paths:
  - "src/learnloop/router_objective/report.py"
source_commit: "2ffac8021ab164e5294b86f628c3747099919ac0"
source_commit_timestamp: "2026-11-04T18:38:52-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router_objective"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.router_objective.report module"
  - "src/learnloop/router_objective/report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.report` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: ``learnloop data-capture report``'s RO0 section: coverage per row of spec §4, and bytes measured per day.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/report.py](../../../../../../src/learnloop/router_objective/report.py) |
| Source lines | 247 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `2ffac8021ab164e5294b86f628c3747099919ac0` |
| Commit timestamp | `2026-11-04T18:38:52-05:00` |

## Public API

- `section(connection: sqlite3.Connection, *, goal_ids: Sequence[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/report.py), line 200) — Coverage per row, and what it costs.
- `lines(report: dict[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/router_objective/report.py), line 236)

### Module constants

- `_ACTIVE_TABLES` ([src/learnloop/router_objective/report.py](../../../../../../src/learnloop/router_objective/report.py), line 18)

### Explicit exports

`__all__` declares:

- `lines`
- `section`

## Internal implementation anchors

- `_value(connection: sqlite3.Connection, sql: str, *parameters: Any) -> Any` ([source](../../../../../../src/learnloop/router_objective/report.py), line 29)
- `_coverage(written: int, of: int) -> float | None` ([source](../../../../../../src/learnloop/router_objective/report.py), line 33)
- `_row(written: int, of: int, stored_bytes: int, **more: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/report.py), line 37)
- `_first(connection: sqlite3.Connection, table: str, clock: str, where: str) -> str | None` ([source](../../../../../../src/learnloop/router_objective/report.py), line 41)
- `_pages(connection: sqlite3.Connection, table: str) -> int | None` ([source](../../../../../../src/learnloop/router_objective/report.py), line 45) — The table's pages and its indexes', where this SQLite has ``dbstat``.
- `_question_rows(connection: sqlite3.Connection) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/report.py), line 56)
- `_row3(connection: sqlite3.Connection, opportunity: tuple[int, int, int]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/report.py), line 78)
- `_row4(connection: sqlite3.Connection) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/report.py), line 93)
- `_row5(connection: sqlite3.Connection) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/report.py), line 105)
- `_sessions(connection: sqlite3.Connection) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/report.py), line 115)
- `_decision_state(connection: sqlite3.Connection) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/report.py), line 135)
- `_row10(connection: sqlite3.Connection) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/report.py), line 153)
- `_row11(connection: sqlite3.Connection, goal_ids: Sequence[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/report.py), line 170)
- `_row12(connection: sqlite3.Connection) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/report.py), line 179)
- `_active_days(connection: sqlite3.Connection) -> list[str]` ([source](../../../../../../src/learnloop/router_objective/report.py), line 191)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]] — imports `module`; statically calls `lines`, `section`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/router_objective|learnloop.db.stores.router_objective]] — imports `module`; calls `table_present`
- [[Reference/Modules/learnloop/router_objective/trajectory|learnloop.router_objective.trajectory]] — imports `module`; calls `rows`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_data_capture_codex_rereview.py](../../../../../../tests/test_data_capture_codex_rereview.py) — imports consumer [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]]
- [tests/test_data_capture_codex_review.py](../../../../../../tests/test_data_capture_codex_review.py) — imports consumer [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]]
- [tests/test_data_capture_landing_review.py](../../../../../../tests/test_data_capture_landing_review.py) — imports consumer [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]]
- [tests/test_data_capture_report.py](../../../../../../tests/test_data_capture_report.py) — imports consumer [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]]
- [tests/test_followup_fg1c_codex_review.py](../../../../../../tests/test_followup_fg1c_codex_review.py) — imports consumer [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]]
- [tests/test_hypothesis_marks_context.py](../../../../../../tests/test_hypothesis_marks_context.py) — imports consumer [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]]
- [tests/test_ih4_preferences_inform_router.py](../../../../../../tests/test_ih4_preferences_inform_router.py) — imports consumer [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]]
- [tests/test_ro0_report.py](../../../../../../tests/test_ro0_report.py) — imports consumer [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]]

## Modification guidance

- Make changes here when the responsibility remains report within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/report.py](../../../../../../src/learnloop/router_objective/report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
