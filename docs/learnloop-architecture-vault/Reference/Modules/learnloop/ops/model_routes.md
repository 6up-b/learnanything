---
title: "learnloop.ops.model_routes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/model_routes.py"
source_paths:
  - "src/learnloop/ops/model_routes.py"
source_commit: "workspace/uncommitted @ HEAD 6d58440b8245a35099a0cdcd9b325518f0c1431d"
source_commit_timestamp: "2026-11-09T12:54:21-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ops"
layer: "domain"
concepts:
  - "State and Persistence"
  - "Configuration"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.ops.model_routes module"
  - "src/learnloop/ops/model_routes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops"
---

# `learnloop.ops.model_routes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ops.model_routes` exists within [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] to own the behavior summarized by its module contract: Model route health from call receipts (``learnloop doctor``).

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/model_routes.py](../../../../../../src/learnloop/ops/model_routes.py) |
| Source lines | 169 |
| Owning package | [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 6d58440b8245a35099a0cdcd9b325518f0c1431d` |
| Commit timestamp | `2026-11-09T12:54:21-05:00` |

## Public API

- `class RouteHealth` ([source](../../../../../../src/learnloop/ops/model_routes.py), line 44)
  - `as_dict(self) -> dict[str, Any]` (line 67; public)
  - `message(self) -> str` (line 70; public)
- `route_health(rows: Iterable[Mapping[str, Any]], configured_models: Mapping[str, str | None] | None=None) -> list[RouteHealth]` ([source](../../../../../../src/learnloop/ops/model_routes.py), line 94) — Facts per (purpose, provider) from root receipts, in any order.
- `check_model_routes(repository: Any, configured_models: Mapping[str, str | None]) -> list[RouteHealth]` ([source](../../../../../../src/learnloop/ops/model_routes.py), line 163) — The doctor's reader: every root receipt.

### Module constants

- `FINDING_CODE` ([src/learnloop/ops/model_routes.py](../../../../../../src/learnloop/ops/model_routes.py), line 36)
- `_TERMINAL` ([src/learnloop/ops/model_routes.py](../../../../../../src/learnloop/ops/model_routes.py), line 39)
- `_UNPARSED` ([src/learnloop/ops/model_routes.py](../../../../../../src/learnloop/ops/model_routes.py), line 40)

### Explicit exports

`__all__` declares:

- `FINDING_CODE`
- `RouteHealth`
- `check_model_routes`
- `route_health`

## Internal implementation anchors

- `_instant(value: Any) -> datetime` ([source](../../../../../../src/learnloop/ops/model_routes.py), line 84) — Receipt times compared as instants, not strings (``Z``, offsets and fractional seconds sort wrongly as text).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `FINDING_CODE`, `check_model_routes`; statically calls `check_model_routes`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_model_route_health.py](../../../../../../tests/test_model_route_health.py) — direct import
  - `test_a_configured_model_change_waits_for_the_next_call`
  - `test_a_model_change_restarts_the_judgment_both_ways`
  - `test_a_purpose_moved_to_another_profile_is_superseded_not_flagged`
  - `test_a_route_that_never_completed_is_flagged_with_its_last_error`
  - `test_doctor_flags_a_route_whose_current_model_never_completed`
  - `test_doctor_reports_routes_in_json_and_text_and_flags_the_dead_one`
  - `test_failures_after_a_completed_call_on_the_same_model_are_reported_not_flagged`
  - `test_one_purpose_on_two_profiles_keeps_both_routes`
  - `test_receipt_times_are_ordered_as_instants_not_text`
  - `test_started_interrupted_and_truncated_calls_are_neither_failures_nor_completions`

## Modification guidance

- Make changes here when the responsibility remains model routes within learnloop.ops; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/model_routes.py](../../../../../../src/learnloop/ops/model_routes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
