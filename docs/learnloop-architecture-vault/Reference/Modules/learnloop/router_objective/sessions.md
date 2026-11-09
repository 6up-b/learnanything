---
title: "learnloop.router_objective.sessions"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/sessions.py"
source_paths:
  - "src/learnloop/router_objective/sessions.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router_objective"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.router_objective.sessions module"
  - "src/learnloop/router_objective/sessions.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.sessions`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.sessions` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO0 rows 7 and 8 (spec_router_objective_v1 §4): what a session had available, and how it ended.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/sessions.py](../../../../../../src/learnloop/router_objective/sessions.py) |
| Source lines | 272 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `record_availability(vault: Any, repository: Any, session_id: str, *, available_minutes: float | None=None, device: str | None=None, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/router_objective/sessions.py), line 107) — Row 8, stamped at the session's start, before its first block is served.
- `record_end(vault: Any, repository: Any, session_id: str, *, reason: str | None=None, ended_at: str | None=None, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/router_objective/sessions.py), line 159) — Row 7, explicit: the learner's own ending.
- `record_stop_override(vault: Any, repository: Any, *, session_id: str | None, plan_id: str, via: str, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/router_objective/sessions.py), line 188) — The learner went on past a finished plan: the offered stop, overridden.
- `record_stop_acceptance(vault: Any, repository: Any, *, session_id: str | None, plan_id: str, stop_decision_id: str, via: str, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/router_objective/sessions.py), line 208) — Landing ruling R2 (mobile v2, F8): the learner took a stop a device was offered while the plan stays open for work held for the desktop (*Done for today* on a pending stop).
- `sweep_unreported(vault: Any, repository: Any, *, trigger: str, clock: Clock | None=None) -> int` ([source](../../../../../../src/learnloop/router_objective/sessions.py), line 236) — Recovery: every session with an availability row that has ended with no end row gets one, inferred.

### Module constants

- `RECEIPT_VERSION` ([src/learnloop/router_objective/sessions.py](../../../../../../src/learnloop/router_objective/sessions.py), line 30)
- `AVAILABILITY` ([src/learnloop/router_objective/sessions.py](../../../../../../src/learnloop/router_objective/sessions.py), line 31)
- `END` ([src/learnloop/router_objective/sessions.py](../../../../../../src/learnloop/router_objective/sessions.py), line 32)
- `STOP_RESPONSE` ([src/learnloop/router_objective/sessions.py](../../../../../../src/learnloop/router_objective/sessions.py), line 33)
- `EXPLICIT` ([src/learnloop/router_objective/sessions.py](../../../../../../src/learnloop/router_objective/sessions.py), line 34)
- `INFERRED` ([src/learnloop/router_objective/sessions.py](../../../../../../src/learnloop/router_objective/sessions.py), line 35)
- `OFFERED_STOP_ACCEPTED` ([src/learnloop/router_objective/sessions.py](../../../../../../src/learnloop/router_objective/sessions.py), line 36)
- `OFFERED_STOP_OVERRIDDEN` ([src/learnloop/router_objective/sessions.py](../../../../../../src/learnloop/router_objective/sessions.py), line 37)
- `UNPROMPTED_STOP` ([src/learnloop/router_objective/sessions.py](../../../../../../src/learnloop/router_objective/sessions.py), line 38)
- `APP_CLOSED` ([src/learnloop/router_objective/sessions.py](../../../../../../src/learnloop/router_objective/sessions.py), line 39)
- `FOREGROUND_LOST` ([src/learnloop/router_objective/sessions.py](../../../../../../src/learnloop/router_objective/sessions.py), line 40)
- `EXTERNAL_INTERRUPTION` ([src/learnloop/router_objective/sessions.py](../../../../../../src/learnloop/router_objective/sessions.py), line 41)
- `RULE` ([src/learnloop/router_objective/sessions.py](../../../../../../src/learnloop/router_objective/sessions.py), line 42)
- `UNKNOWN` ([src/learnloop/router_objective/sessions.py](../../../../../../src/learnloop/router_objective/sessions.py), line 43)
- `CLIENT_END_REASONS` ([src/learnloop/router_objective/sessions.py](../../../../../../src/learnloop/router_objective/sessions.py), line 45)
- `MISSING` ([src/learnloop/router_objective/sessions.py](../../../../../../src/learnloop/router_objective/sessions.py), line 48)
- `_STOP_ACTION` ([src/learnloop/router_objective/sessions.py](../../../../../../src/learnloop/router_objective/sessions.py), line 50)

### Explicit exports

`__all__` declares:

- `APP_CLOSED`
- `AVAILABILITY`
- `CLIENT_END_REASONS`
- `END`
- `EXPLICIT`
- `EXTERNAL_INTERRUPTION`
- `FOREGROUND_LOST`
- `INFERRED`
- `MISSING`
- `OFFERED_STOP_ACCEPTED`
- `OFFERED_STOP_OVERRIDDEN`
- `RECEIPT_VERSION`
- `RULE`
- `STOP_RESPONSE`
- `UNKNOWN`
- `UNPROMPTED_STOP`
- `record_availability`
- `record_end`
- `record_stop_acceptance`
- `record_stop_override`
- `sweep_unreported`

## Internal implementation anchors

- `_dumps(value: Any) -> str` ([source](../../../../../../src/learnloop/router_objective/sessions.py), line 53)
- `_base(*, session_id: str | None, kind: str, at: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/sessions.py), line 57)
- `_today(clock: Clock | None) -> str` ([source](../../../../../../src/learnloop/router_objective/sessions.py), line 62)
- `_todays_plan(connection: Any, clock: Clock | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/router_objective/sessions.py), line 66)
- `_session_plan(connection: Any, session_id: str | None, clock: Clock | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/router_objective/sessions.py), line 75) — The plan this session's newest block belongs to, else today's.
- `_in_force(connection: Any, plan: dict[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/sessions.py), line 88) — The plan, its newest numbered block and its newest stop decision.
- `_ready(vault: Any, connection: Any) -> bool` ([source](../../../../../../src/learnloop/router_objective/sessions.py), line 103)
- `_derived_reason(plan: dict[str, Any] | None, *, stop_accepted: bool=False) -> str` ([source](../../../../../../src/learnloop/router_objective/sessions.py), line 138) — The plan's own state, when no client said: a finished plan had offered the stop the learner took, and so had an open one whose pending stop this session accepted (``stop_accepted``).
- `_accepted_here(connection: Any, session_id: str, stop_decision_id: str | None) -> bool` ([source](../../../../../../src/learnloop/router_objective/sessions.py), line 147) — This session accepted the stop in force (a ``stop_response`` naming it, accepted) and nothing overrode it since.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `module`; statically calls `record_stop_acceptance`, `record_stop_override`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `module`; statically calls `record_availability`, `record_end`, `sweep_unreported`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `utc_now_iso`; calls `SystemClock`, `utc_now_iso`
- [[Reference/Modules/learnloop/data_capture/gates|learnloop.data_capture.gates]] — imports `objective_receipts_on`; calls `objective_receipts_on`
- [[Reference/Modules/learnloop/db/stores/router_objective|learnloop.db.stores.router_objective]] — imports `module`; calls `insert_session_receipt`, `table_present`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro0_gate.py](../../../../../../tests/test_ro0_gate.py) — direct import
  - `test_rebuild_leaves_the_receipts_alone`
- [tests/test_ro0_report.py](../../../../../../tests/test_ro0_report.py) — direct import
  - `test_each_row_reports_what_was_written_and_measured_bytes`
- [tests/test_ro0_rows7_8_sessions.py](../../../../../../tests/test_ro0_rows7_8_sessions.py) — direct import
  - `test_a_clients_word_stands_when_it_is_one_of_ours`
  - `test_a_crash_is_inferred_at_recovery_and_marked_inferred`
  - `test_a_session_another_device_replaced_ended_by_the_rule`
  - `test_a_session_from_before_ro0_is_not_backfilled`
  - `test_a_stop_after_a_finished_plan_accepts_the_offer`
  - `test_availability_comes_before_the_sessions_first_serve`
  - `test_availability_is_stamped_before_the_first_block`
  - `test_going_on_past_a_finished_plan_overrides_the_offer_and_is_no_end`
  - `test_missing_is_recorded_as_missing`
  - `test_stopping_an_open_plan_is_unprompted`
  - `test_todays_plan_is_the_source_when_the_client_says_nothing`

## Modification guidance

- Make changes here when the responsibility remains sessions within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/sessions.py](../../../../../../src/learnloop/router_objective/sessions.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
