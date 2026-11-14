---
title: "learnloop.refusal_records"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/refusal_records.py"
source_paths:
  - "src/learnloop/refusal_records.py"
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
  - "learnloop.refusal_records module"
  - "src/learnloop/refusal_records.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.refusal_records`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.refusal_records` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: Refusals and the follow-up gate's decision as decision records (ADR-017; refactor strategy §2.4, B5).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py) |
| Source lines | 436 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `spend_rule(exc: BaseException) -> tuple[str, dict[str, Any]]` ([source](../../../../../src/learnloop/refusal_records.py), line 136) — The rule a spend refusal names (``SpendLimitExceeded.rule``) and its numbers, as a record's facts.
- `route_rule(provider_name: str | None, providers: Mapping[str, Any] | None) -> tuple[str, str | None]` ([source](../../../../../src/learnloop/refusal_records.py), line 146) — Why a route gave no ready Decider, from what it names (no client is built): no profile routed (manual, empty, or a profile the config does not have), or one routed that is not ready; and the profile's name.
- `disabled_rule(config: Any, task: str, *, serving_tasks: tuple[str, ...], content_tasks: tuple[str, ...]) -> str` ([source](../../../../../src/learnloop/refusal_records.py), line 155) — Why ``decider_judgments.enabled`` said no, in its own order: not a judgment, its switch, its version.
- `decider_record(*, status: str, rule: str, route: str, task: str, ledger_task: str | None=None, left_kind: str | None=None, left_id: Any=None, input_hash: Any=None, model: Any=None, judgment_id: str | None=None, detail_table: str='judgment_ledger', facts: Mapping[str, Any] | None=None, versions: Mapping[str, Any] | None=None, error: BaseException | None=None, subject_kind: str | None=None, subject_id: Any=None) -> DecisionRecord` ([source](../../../../../src/learnloop/refusal_records.py), line 168) — A Decider judgment with no answer: ``status`` and ``rule`` say why, ``facts`` the limit that refused.
- `router_spend_record(*, cap_usd: Any, spent_usd: Any, request_usd: Any, owner_kind: Any, owner_id: Any, event: Mapping[str, Any]) -> DecisionRecord` ([source](../../../../../src/learnloop/refusal_records.py), line 201) — The router's daily guard refused a metered request: no receipt is written, so this is the only row.
- `envelope_record(*, envelope: Any, cap_usd: Any, spent_usd: Any, request_usd: Any, owner_kinds: Any=None) -> DecisionRecord` ([source](../../../../../src/learnloop/refusal_records.py), line 218) — A shared daily cap (``source_service.max_daily_cost_usd``, ``hints.max_daily_cost_usd``, the figures', the Reader's, ...) refused a metered request before it was sent: no call row exists, and each caller turns the refusal into its own status (``over_budget``, ``capped``, an empt…
- `lesson_budget_record(*, lesson_id: Any, exc: BaseException | None, refusal: Mapping[str, Any] | None) -> DecisionRecord` ([source](../../../../../src/learnloop/refusal_records.py), line 238) — A lesson's own envelope (or a cap below it) refused its next request, so the lesson closed with ``budget``: the close receipt says ``budget``, and this names which request (its purpose), the rule and the numbers.
- `figure_gate_record(*, rule: str, purpose: Any) -> DecisionRecord` ([source](../../../../../src/learnloop/refusal_records.py), line 269) — The figure gate refused a figure-derived request; every later request of the unit is refused with it.
- `router_row_record(row: Mapping[str, Any], exc: BaseException) -> DecisionRecord` ([source](../../../../../src/learnloop/refusal_records.py), line 278) — The ledger refused a router decision row; the caller's behaviour applies all the same (``applied``).
- `plan_logger_record(*, decision_kind: str, block_id: Any, plan_id: Any, logger: Any, exc: BaseException, logged_ref: Any=None) -> DecisionRecord` ([source](../../../../../src/learnloop/refusal_records.py), line 303) — A plan decision's logger raised: the block it describes is served all the same, with no ledger row (or, for a follow-up's interrupt, with a row whose linked rows stopped at ``logged_ref``).
- `followup_gate_record(row: Mapping[str, Any], decision: Any, *, logged: bool, retry: bool=False, value_check_error: BaseException | None=None) -> DecisionRecord` ([source](../../../../../src/learnloop/refusal_records.py), line 328) — The follow-up gate's decision for one workflow: what it chose, the rule, the arms, the components' answers.
- `built(kind: str, build: Callable[[], DecisionRecord]) -> DecisionRecord | None` ([source](../../../../../src/learnloop/refusal_records.py), line 396)
- `write(repository: Any, kind: str, build: Callable[[], DecisionRecord]) -> str | None` ([source](../../../../../src/learnloop/refusal_records.py), line 406) — Build and write one record through ``repository`` (joining its open transaction without committing it, else a short one of its own); its id, or None.
- `write_on(connection: Any, kind: str, build: Callable[[], DecisionRecord]) -> str | None` ([source](../../../../../src/learnloop/refusal_records.py), line 420) — Build and write one record on ``connection``, inside the transaction the caller holds; never raises.

### Module constants

- `LOG` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 43)
- `DECIDER_JUDGMENT` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 45)
- `SPEND_ADMISSION` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 46)
- `FIGURE_ADMISSION` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 47)
- `ROUTER_DECISION_ROW` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 48)
- `FOLLOWUP_GATE` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 49)
- `SWITCH_OFF` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 53)
- `BELOW_VERSION` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 55)
- `NOT_A_DECIDER_TASK` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 57)
- `NO_DECIDER_ROUTED` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 59)
- `DECIDER_NOT_READY` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 61)
- `MODELS_OFF` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 63)
- `PROVIDER_UNAVAILABLE` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 65)
- `REQUEST_FAILED` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 67)
- `TIME_BOX` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 69)
- `SPEND_REFUSED` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 71)
- `ROUTER_DAILY_CAP` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 73)
- `LOGGER_ERROR` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 75)
- `ENVELOPE_CAP` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 77)

### Explicit exports

`__all__` declares:

- `BELOW_VERSION`
- `DECIDER_JUDGMENT`
- `DECIDER_NOT_READY`
- `ENVELOPE_CAP`
- `FIGURE_ADMISSION`
- `FOLLOWUP_GATE`
- `LOGGER_ERROR`
- `MODELS_OFF`
- `NOT_A_DECIDER_TASK`
- `NO_DECIDER_ROUTED`
- `PROVIDER_UNAVAILABLE`
- `REQUEST_FAILED`
- `ROUTER_DAILY_CAP`
- `ROUTER_DECISION_ROW`
- `SPEND_ADMISSION`
- `SPEND_REFUSED`
- `SWITCH_OFF`
- `TIME_BOX`
- `decider_record`
- `disabled_rule`
- `envelope_record`
- `figure_gate_record`
- `followup_gate_record`
- `lesson_budget_record`
- `plan_logger_record`
- `route_rule`
- `router_row_record`
- `router_spend_record`
- `spend_rule`
- `built`
- `write`
- `write_on`

## Internal implementation anchors

- `_ref(value: Any) -> str | None` ([source](../../../../../src/learnloop/refusal_records.py), line 80) — An id as a record keeps it: itself, or a short hash of one that is not a code (vault ids are free-form, and one odd id must not drop the whole record).
- `_code(value: Any) -> str | None` ([source](../../../../../src/learnloop/refusal_records.py), line 92)
- `_number(value: Any) -> float | int | None` ([source](../../../../../src/learnloop/refusal_records.py), line 96)
- `_compact(values: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../src/learnloop/refusal_records.py), line 102)
- `_clean(value: Any) -> Any` ([source](../../../../../src/learnloop/refusal_records.py), line 106) — A caller's fact as a record keeps it: numbers and flags as they are, strings as ids (hashed when not a code), lists and maps element by element; anything else dropped.
- `_error(exc: BaseException | None) -> tuple[str | None, str | None]` ([source](../../../../../src/learnloop/refusal_records.py), line 123)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `module`; statically calls `plan_logger_record`, `write_on`
- [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] — imports `module`; statically calls `built`, `router_spend_record`
- [[Reference/Modules/learnloop/db/stores/router|learnloop.db.stores.router]] — imports `module`; statically calls `router_row_record`, `write_on`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `module`; statically calls `decider_record`, `disabled_rule`, `route_rule`, `spend_rule`, `write`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `module`; statically calls `figure_gate_record`, `write`
- [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] — imports `module`; statically calls `followup_gate_record`, `write`, `write_on`
- [[Reference/Modules/learnloop/hints/chooser|learnloop.hints.chooser]] — imports `module`; statically calls `decider_record`, `spend_rule`, `write`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `module`; statically calls `envelope_record`, `write_on`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `module`; statically calls `lesson_budget_record`, `write`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/provenance|learnloop.provenance]] — imports `DecisionRecord`, `module`; calls `DecisionRecord`, `current_cause`, `current_trace`, `is_code`, `where`, `write`, `write_through`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `logging`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]], [[Reference/Modules/learnloop/db/stores/router|learnloop.db.stores.router]], [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]], [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] and 4 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_arcb_close_fixes.py](../../../../../tests/test_arcb_close_fixes.py) — direct import
  - `test_a_record_written_under_a_pin_never_commits_the_callers_work`
  - `test_why_lesson_finds_the_record_the_real_lesson_budget_builder_writes`
- [tests/test_provenance.py](../../../../../tests/test_provenance.py) — direct import
  - `test_a_rebuild_never_calls_the_record_and_keeps_its_rows`
- [tests/test_refusal_records.py](../../../../../tests/test_refusal_records.py) — direct import
  - `test_a_guard_record_that_cannot_be_built_still_refuses`
  - `test_a_record_that_cannot_be_built_changes_no_judgment`
  - `test_a_spend_refusal_names_the_cap_and_its_numbers_and_keeps_its_message`
  - `test_every_record_here_passes_the_prose_check_with_item_text_planted`
  - `test_route_rule_tells_no_decider_routed_from_a_route_not_ready`
- [tests/test_remaining_decision_records.py](../../../../../tests/test_remaining_decision_records.py) — direct import
  - `test_a_cap_record_that_cannot_be_built_still_refuses`
  - `test_a_follow_up_interrupts_logger_that_raises_leaves_a_record`
  - `test_a_lesson_closed_with_budget_names_the_request_and_the_limit`
  - `test_a_plan_logger_that_raises_leaves_a_record_on_the_block_and_serves_the_same`
  - `test_a_shared_daily_caps_refusal_names_its_cap_and_leaves_a_record`
  - `test_every_b8_builder_passes_the_prose_check_with_learner_text_planted`
  - `test_the_gap_readings_figure_gate_records_its_refusal_in_the_jobs_trace`

## Modification guidance

- Make changes here when the responsibility remains refusal records within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
