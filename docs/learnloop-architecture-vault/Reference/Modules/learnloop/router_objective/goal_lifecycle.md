---
title: "learnloop.router_objective.goal_lifecycle"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/goal_lifecycle.py"
source_paths:
  - "src/learnloop/router_objective/goal_lifecycle.py"
source_commit: "workspace/uncommitted @ HEAD 4a801f1afce0faaf0246a9bd404a8ed73abf2dfb"
source_commit_timestamp: "2026-11-04T19:32:38-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router_objective"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.router_objective.goal_lifecycle module"
  - "src/learnloop/router_objective/goal_lifecycle.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.goal_lifecycle`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.goal_lifecycle` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO0 row 11 (spec_router_objective_v1 §4): a goal's lifecycle, seen at load.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/goal_lifecycle.py](../../../../../../src/learnloop/router_objective/goal_lifecycle.py) |
| Source lines | 98 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 4a801f1afce0faaf0246a9bd404a8ed73abf2dfb` |
| Commit timestamp | `2026-11-04T19:32:38-05:00` |

## Public API

- `changes(vault: Any, latest: Mapping[str, Mapping[str, Any]], *, at: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/goal_lifecycle.py), line 49) — What the vault's goals say that the newest rows do not (pure).
- `sweep(vault: Any, repository: Any, *, clock: Clock | None=None) -> int` ([source](../../../../../../src/learnloop/router_objective/goal_lifecycle.py), line 76) — Write what changed since the last load.

### Module constants

- `RECEIPT_VERSION` ([src/learnloop/router_objective/goal_lifecycle.py](../../../../../../src/learnloop/router_objective/goal_lifecycle.py), line 25)
- `CREATED` ([src/learnloop/router_objective/goal_lifecycle.py](../../../../../../src/learnloop/router_objective/goal_lifecycle.py), line 26)
- `DATE_CHANGED` ([src/learnloop/router_objective/goal_lifecycle.py](../../../../../../src/learnloop/router_objective/goal_lifecycle.py), line 27)
- `REMOVED` ([src/learnloop/router_objective/goal_lifecycle.py](../../../../../../src/learnloop/router_objective/goal_lifecycle.py), line 28)
- `RESUMED` ([src/learnloop/router_objective/goal_lifecycle.py](../../../../../../src/learnloop/router_objective/goal_lifecycle.py), line 29)
- `_BY_STATUS` ([src/learnloop/router_objective/goal_lifecycle.py](../../../../../../src/learnloop/router_objective/goal_lifecycle.py), line 31)
- `SEEN_AT_LOAD` ([src/learnloop/router_objective/goal_lifecycle.py](../../../../../../src/learnloop/router_objective/goal_lifecycle.py), line 33)

### Explicit exports

`__all__` declares:

- `CREATED`
- `DATE_CHANGED`
- `RECEIPT_VERSION`
- `REMOVED`
- `RESUMED`
- `SEEN_AT_LOAD`
- `changes`
- `sweep`

## Internal implementation anchors

- `_goals(vault: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/goal_lifecycle.py), line 36)
- `_row(goal_id: str, event: str, *, reason: str, status: Any, previous_status: Any, due_at: Any, previous_due_at: Any, contract: Any, occurred_at: Any, at: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/goal_lifecycle.py), line 42)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `module`; statically calls `sweep`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/data_capture/gates|learnloop.data_capture.gates]] — imports `objective_receipts_on`; calls `objective_receipts_on`
- [[Reference/Modules/learnloop/db/stores/router_objective|learnloop.db.stores.router_objective]] — imports `module`; calls `insert_goal_event`, `latest_goal_events`, `table_present`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro0_codex_review.py](../../../../../../tests/test_ro0_codex_review.py) — direct import
  - `test_f8_an_unchanged_load_takes_no_write_lock`
  - `test_f8_two_loaders_sweeping_a_new_goal_write_it_once`
  - `test_f8_two_loaders_sweeping_a_pause_write_it_once`
- [tests/test_ro0_report.py](../../../../../../tests/test_ro0_report.py) — direct import
  - `test_each_row_reports_what_was_written_and_measured_bytes`
- [tests/test_ro0_row11_goal_lifecycle.py](../../../../../../tests/test_ro0_row11_goal_lifecycle.py) — direct import
  - `test_a_goal_is_seen_once_with_its_own_start`
  - `test_a_pause_a_new_date_a_resumption_and_a_completion`
  - `test_a_refused_row_rolls_back_alone`
  - `test_a_removal_says_whether_the_goal_was_active_and_a_return_is_a_new_goal`
  - `test_status_and_date_changed_together_are_two_events`
  - `test_the_sidecar_sweeps_at_load`

## Modification guidance

- Make changes here when the responsibility remains goal lifecycle within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/goal_lifecycle.py](../../../../../../src/learnloop/router_objective/goal_lifecycle.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
