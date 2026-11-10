---
title: "learnloop.daily_plan.boundary_records"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/boundary_records.py"
source_paths:
  - "src/learnloop/daily_plan/boundary_records.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.daily_plan"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.daily_plan.boundary_records module"
  - "src/learnloop/daily_plan/boundary_records.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.boundary_records`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.boundary_records` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: A plan boundary's decision records (ADR-017; refactor strategy §3.6, case 1): what was chosen, what each model said.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/boundary_records.py](../../../../../../src/learnloop/daily_plan/boundary_records.py) |
| Source lines | 314 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `wall_now() -> str` ([source](../../../../../../src/learnloop/daily_plan/boundary_records.py), line 52) — The wall clock in the receipts' format (``ai.execution``): a record's time is compared with theirs.
- `ref(value: Any) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/boundary_records.py), line 58) — An option's id as a record keeps it: the id itself, or a short hash of one that isn't a code (a space in a vault's id would otherwise drop the whole record).
- `forced_entry(item_id: Any, *, origin: Any, workflow: Mapping[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/boundary_records.py), line 107) — One forced item as a record names it: its id and origin, and its follow-up workflow, source attempt and state when a workflow holds it (a follow-up from a recorded need has none).
- `forced_facts(entries: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/boundary_records.py), line 122) — The forced items' ids, workflows and source attempts as lists (capped), and how many there were.
- `plan_block_records(decision: Any, *, block_id: str, detail_id: str | None, config: Any, stop: bool, trace_id: str | None=None, parent_id: str | None=None, trigger_attempt: str | None=None) -> list[DecisionRecord]` ([source](../../../../../../src/learnloop/daily_plan/boundary_records.py), line 150) — A boundary decision's plan_block record, its components' model_answer records and any failed step's record, oldest first.
- `component_records(block: DecisionRecord, router: Mapping[str, Any], mixture: Mapping[str, Any], *, timeouts: Mapping[str, Any], waited_ms: Any, crashed: bool, models: Mapping[str, Any] | None=None) -> list[DecisionRecord]` ([source](../../../../../../src/learnloop/daily_plan/boundary_records.py), line 256) — One ``model_answer`` per component of ``block``'s decision (the Decider, the LLM, the numeric policy, the staged rule), from the router's record of it: a plan block's (B2) or a follow-up's ``plan_interrupt`` (B3).

### Module constants

- `PLAN_BLOCK` ([src/learnloop/daily_plan/boundary_records.py](../../../../../../src/learnloop/daily_plan/boundary_records.py), line 36)
- `MODEL_ANSWER` ([src/learnloop/daily_plan/boundary_records.py](../../../../../../src/learnloop/daily_plan/boundary_records.py), line 37)
- `FAILURE_NOTE` ([src/learnloop/daily_plan/boundary_records.py](../../../../../../src/learnloop/daily_plan/boundary_records.py), line 40)
- `_STATUS` ([src/learnloop/daily_plan/boundary_records.py](../../../../../../src/learnloop/daily_plan/boundary_records.py), line 43)
- `_DECIDED_BY` ([src/learnloop/daily_plan/boundary_records.py](../../../../../../src/learnloop/daily_plan/boundary_records.py), line 46)
- `_ERROR_TYPE` ([src/learnloop/daily_plan/boundary_records.py](../../../../../../src/learnloop/daily_plan/boundary_records.py), line 48)
- `_NOT_CODE` ([src/learnloop/daily_plan/boundary_records.py](../../../../../../src/learnloop/daily_plan/boundary_records.py), line 49)
- `IDS_KEPT` ([src/learnloop/daily_plan/boundary_records.py](../../../../../../src/learnloop/daily_plan/boundary_records.py), line 104)

### Explicit exports

`__all__` declares:

- `FAILURE_NOTE`
- `IDS_KEPT`
- `MODEL_ANSWER`
- `PLAN_BLOCK`
- `component_records`
- `forced_entry`
- `forced_facts`
- `plan_block_records`
- `ref`
- `wall_now`

## Internal implementation anchors

- `_code(value: Any) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/boundary_records.py), line 70)
- `_number(value: Any) -> float | int | None` ([source](../../../../../../src/learnloop/daily_plan/boundary_records.py), line 74)
- `_where(value: Any) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/boundary_records.py), line 80)
- `_error_type(error: Any) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/boundary_records.py), line 85)
- `_compact(values: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/boundary_records.py), line 90)
- `_favoured(distribution: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/boundary_records.py), line 94)
- `_superseding(value: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/boundary_records.py), line 141) — IH2's contest: the open offer this decision replaces (its block and its decision).
- `_answer(name: str, *, status: str, raw: str, chosen_ref: Any, block: DecisionRecord, distribution: Mapping[str, Any], facts: Mapping[str, Any], versions: Mapping[str, Any], error_type: str | None) -> DecisionRecord` ([source](../../../../../../src/learnloop/daily_plan/boundary_records.py), line 290)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `FAILURE_NOTE`, `module`, `wall_now`; statically calls `forced_entry`, `plan_block_records`, `wall_now`
- [[Reference/Modules/learnloop/daily_plan/plan_records|learnloop.daily_plan.plan_records]] — imports `IDS_KEPT`, `MODEL_ANSWER`, `component_records`, `forced_entry`, `forced_facts`, `ref`, `wall_now`; statically calls `component_records`, `forced_facts`, `ref`, `wall_now`
- [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] — imports `FAILURE_NOTE`, `wall_now`; statically calls `wall_now`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/provenance|learnloop.provenance]] — imports `DecisionRecord`, `module`; calls `DecisionRecord`, `current_trace`, `is_code`, `new_trace_id`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `hashlib`, `math`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/plan_records|learnloop.daily_plan.plan_records]], [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_forced_withdrawal_records.py](../../../../../../tests/test_forced_withdrawal_records.py) — direct import
  - `test_the_builders_keep_ids_numbers_and_codes_only`
- [tests/test_router_failure_records.py](../../../../../../tests/test_router_failure_records.py) — direct import
  - `test_a_record_that_cannot_be_built_never_blocks_the_block`
  - `test_records_hold_codes_only_and_an_id_that_is_not_a_code_is_hashed`

## Modification guidance

- Make changes here when the responsibility remains boundary records within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/boundary_records.py](../../../../../../src/learnloop/daily_plan/boundary_records.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
