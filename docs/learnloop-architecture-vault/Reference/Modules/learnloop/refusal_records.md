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
| Source lines | 358 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `spend_rule(exc: BaseException) -> tuple[str, dict[str, Any]]` ([source](../../../../../src/learnloop/refusal_records.py), line 129) — The rule a spend refusal names (``SpendLimitExceeded.rule``) and its numbers, as a record's facts.
- `route_rule(provider_name: str | None, providers: Mapping[str, Any] | None) -> tuple[str, str | None]` ([source](../../../../../src/learnloop/refusal_records.py), line 139) — Why a route gave no ready Decider, from what it names (no client is built): no profile routed (manual, empty, or a profile the config does not have), or one routed that is not ready; and the profile's name.
- `disabled_rule(config: Any, task: str, *, serving_tasks: tuple[str, ...], content_tasks: tuple[str, ...]) -> str` ([source](../../../../../src/learnloop/refusal_records.py), line 148) — Why ``decider_judgments.enabled`` said no, in its own order: not a judgment, its switch, its version.
- `decider_record(*, status: str, rule: str, route: str, task: str, ledger_task: str | None=None, left_kind: str | None=None, left_id: Any=None, input_hash: Any=None, model: Any=None, judgment_id: str | None=None, detail_table: str='judgment_ledger', facts: Mapping[str, Any] | None=None, versions: Mapping[str, Any] | None=None, error: BaseException | None=None, subject_kind: str | None=None, subject_id: Any=None) -> DecisionRecord` ([source](../../../../../src/learnloop/refusal_records.py), line 161) — A Decider judgment with no answer: ``status`` and ``rule`` say why, ``facts`` the limit that refused.
- `router_spend_record(*, cap_usd: Any, spent_usd: Any, request_usd: Any, owner_kind: Any, owner_id: Any, event: Mapping[str, Any]) -> DecisionRecord` ([source](../../../../../src/learnloop/refusal_records.py), line 194) — The router's daily guard refused a metered request: no receipt is written, so this is the only row.
- `figure_gate_record(*, rule: str, purpose: Any) -> DecisionRecord` ([source](../../../../../src/learnloop/refusal_records.py), line 211) — The figure gate refused a figure-derived request; every later request of the unit is refused with it.
- `router_row_record(row: Mapping[str, Any], exc: BaseException) -> DecisionRecord` ([source](../../../../../src/learnloop/refusal_records.py), line 220) — The ledger refused a router decision row; the caller's behaviour applies all the same (``applied``).
- `followup_gate_record(row: Mapping[str, Any], decision: Any, *, logged: bool, retry: bool=False, value_check_error: BaseException | None=None) -> DecisionRecord` ([source](../../../../../src/learnloop/refusal_records.py), line 245) — The follow-up gate's decision for one workflow: what it chose, the rule, the arms, the components' answers.
- `write(repository: Any, kind: str, build: Callable[[], DecisionRecord]) -> str | None` ([source](../../../../../src/learnloop/refusal_records.py), line 323) — Build and write one record through ``repository`` (joining its open transaction, else a short one of its own); its id, or None.
- `write_on(connection: Any, kind: str, build: Callable[[], DecisionRecord]) -> str | None` ([source](../../../../../src/learnloop/refusal_records.py), line 343) — Build and write one record on ``connection``, inside the transaction the caller holds; never raises.

### Module constants

- `LOG` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 40)
- `DECIDER_JUDGMENT` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 42)
- `SPEND_ADMISSION` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 43)
- `FIGURE_ADMISSION` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 44)
- `ROUTER_DECISION_ROW` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 45)
- `FOLLOWUP_GATE` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 46)
- `SWITCH_OFF` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 50)
- `BELOW_VERSION` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 52)
- `NOT_A_DECIDER_TASK` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 54)
- `NO_DECIDER_ROUTED` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 56)
- `DECIDER_NOT_READY` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 58)
- `MODELS_OFF` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 60)
- `PROVIDER_UNAVAILABLE` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 62)
- `REQUEST_FAILED` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 64)
- `TIME_BOX` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 66)
- `SPEND_REFUSED` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 68)
- `ROUTER_DAILY_CAP` ([src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py), line 70)

### Explicit exports

`__all__` declares:

- `BELOW_VERSION`
- `DECIDER_JUDGMENT`
- `DECIDER_NOT_READY`
- `FIGURE_ADMISSION`
- `FOLLOWUP_GATE`
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
- `route_rule`
- `figure_gate_record`
- `followup_gate_record`
- `router_row_record`
- `router_spend_record`
- `spend_rule`
- `write`
- `write_on`

## Internal implementation anchors

- `_ref(value: Any) -> str | None` ([source](../../../../../src/learnloop/refusal_records.py), line 73) — An id as a record keeps it: itself, or a short hash of one that is not a code (vault ids are free-form, and one odd id must not drop the whole record).
- `_code(value: Any) -> str | None` ([source](../../../../../src/learnloop/refusal_records.py), line 85)
- `_number(value: Any) -> float | int | None` ([source](../../../../../src/learnloop/refusal_records.py), line 89)
- `_compact(values: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../src/learnloop/refusal_records.py), line 95)
- `_clean(value: Any) -> Any` ([source](../../../../../src/learnloop/refusal_records.py), line 99) — A caller's fact as a record keeps it: numbers and flags as they are, strings as ids (hashed when not a code), lists and maps element by element; anything else dropped.
- `_error(exc: BaseException | None) -> tuple[str | None, str | None]` ([source](../../../../../src/learnloop/refusal_records.py), line 116)
- `_built(kind: str, build: Callable[[], DecisionRecord]) -> DecisionRecord | None` ([source](../../../../../src/learnloop/refusal_records.py), line 313)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] — imports `module`; statically calls `router_spend_record`, `write`
- [[Reference/Modules/learnloop/db/stores/router|learnloop.db.stores.router]] — imports `module`; statically calls `router_row_record`, `write_on`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `module`; statically calls `decider_record`, `disabled_rule`, `route_rule`, `spend_rule`, `write`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `module`; statically calls `figure_gate_record`, `write`
- [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] — imports `module`; statically calls `followup_gate_record`, `write`, `write_on`
- [[Reference/Modules/learnloop/hints/chooser|learnloop.hints.chooser]] — imports `module`; statically calls `decider_record`, `spend_rule`, `write`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/provenance|learnloop.provenance]] — imports `DecisionRecord`, `module`; calls `DecisionRecord`, `current_trace`, `is_code`, `where`, `write`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `logging`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]], [[Reference/Modules/learnloop/db/stores/router|learnloop.db.stores.router]], [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]], [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]], [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_provenance.py](../../../../../tests/test_provenance.py) — direct import
  - `test_a_rebuild_never_calls_the_record_and_keeps_its_rows`
- [tests/test_refusal_records.py](../../../../../tests/test_refusal_records.py) — direct import
  - `test_a_guard_record_that_cannot_be_built_still_refuses`
  - `test_a_record_that_cannot_be_built_changes_no_judgment`
  - `test_a_spend_refusal_names_the_cap_and_its_numbers_and_keeps_its_message`
  - `test_every_record_here_passes_the_prose_check_with_item_text_planted`
  - `test_route_rule_tells_no_decider_routed_from_a_route_not_ready`

## Modification guidance

- Make changes here when the responsibility remains refusal records within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/refusal_records.py](../../../../../src/learnloop/refusal_records.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
