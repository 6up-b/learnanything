---
title: "learnloop.router.plan_log"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router/plan_log.py"
source_paths:
  - "src/learnloop/router/plan_log.py"
source_commit: "workspace/uncommitted @ HEAD efd894886714472c5495a6a6b87e97e8a774701a"
source_commit_timestamp: "2026-11-04T00:19:09-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.router.plan_log module"
  - "src/learnloop/router/plan_log.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router"
---

# `learnloop.router.plan_log`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router/_package|learnloop.router]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router.plan_log` exists within [[Reference/Modules/learnloop/router/_package|learnloop.router]] to own the behavior summarized by its module contract: Router R1: daily-plan block decisions as ``plan_block`` router decisions.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router/plan_log.py](../../../../../../src/learnloop/router/plan_log.py) |
| Source lines | 775 |
| Owning package | [[Reference/Modules/learnloop/router/_package|learnloop.router]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD efd894886714472c5495a6a6b87e97e8a774701a` |
| Commit timestamp | `2026-11-04T00:19:09-05:00` |

## Public API

- `build_plan_block_decision(decision: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router/plan_log.py), line 114) — The ``router_decisions`` row for one plan block decision (pure).
- `log_plan_block_decision(connection: Any, decision: Any) -> str | None` ([source](../../../../../../src/learnloop/router/plan_log.py), line 465) — DL1's plan-decision logger: write the ``plan_block`` row, return its id.
- `build_plan_interrupt_decision(decision: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router/plan_log.py), line 495) — The ``router_decisions`` row of one ``plan_interrupt`` decision (pure).
- `log_plan_interrupt_decision(connection: Any, decision: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/router/plan_log.py), line 605) — Write one ``plan_interrupt`` row on the caller's transaction; returns its id.
- `build_followup_decision(decision: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router/plan_log.py), line 634) — FG1's ``plan_interrupt`` row: it names the workflow, since no item exists yet.
- `existing_followup_decision(connection: Any, *, block_id: Any, workflow_id: str) -> Mapping[str, Any] | None` ([source](../../../../../../src/learnloop/router/plan_log.py), line 732) — The decision this workflow already logged on this block, or None: its immutable receipt.
- `log_followup_decision(connection: Any, decision: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/router/plan_log.py), line 744) — Write one FG1 row on the caller's transaction, its card and payloads beside it.

### Module constants

- `DECISION_KIND` ([src/learnloop/router/plan_log.py](../../../../../../src/learnloop/router/plan_log.py), line 69)
- `SURFACE` ([src/learnloop/router/plan_log.py](../../../../../../src/learnloop/router/plan_log.py), line 70)
- `MODE` ([src/learnloop/router/plan_log.py](../../../../../../src/learnloop/router/plan_log.py), line 71)
- `CONTINUE_REF` ([src/learnloop/router/plan_log.py](../../../../../../src/learnloop/router/plan_log.py), line 72)
- `STOP_REF` ([src/learnloop/router/plan_log.py](../../../../../../src/learnloop/router/plan_log.py), line 73)
- `PICK_PREFIX` ([src/learnloop/router/plan_log.py](../../../../../../src/learnloop/router/plan_log.py), line 75)
- `FALLBACK_POLICY` ([src/learnloop/router/plan_log.py](../../../../../../src/learnloop/router/plan_log.py), line 77)
- `_DETERMINISTIC_TOLERANCE` ([src/learnloop/router/plan_log.py](../../../../../../src/learnloop/router/plan_log.py), line 79)
- `MODEL_PAYLOAD_KINDS` ([src/learnloop/router/plan_log.py](../../../../../../src/learnloop/router/plan_log.py), line 365)
- `INTERRUPT_KIND` ([src/learnloop/router/plan_log.py](../../../../../../src/learnloop/router/plan_log.py), line 490)
- `INSERT_REF` ([src/learnloop/router/plan_log.py](../../../../../../src/learnloop/router/plan_log.py), line 491)
- `DECLINE_REF` ([src/learnloop/router/plan_log.py](../../../../../../src/learnloop/router/plan_log.py), line 492)
- `NO_INTERVENTION_REF` ([src/learnloop/router/plan_log.py](../../../../../../src/learnloop/router/plan_log.py), line 631)

### Explicit exports

`__all__` declares:

- `DECISION_KIND`
- `DECLINE_REF`
- `INSERT_REF`
- `INTERRUPT_KIND`
- `MODEL_PAYLOAD_KINDS`
- `NO_INTERVENTION_REF`
- `build_followup_decision`
- `build_plan_block_decision`
- `log_followup_decision`
- `build_plan_interrupt_decision`
- `existing_followup_decision`
- `log_plan_block_decision`
- `log_plan_interrupt_decision`

## Internal implementation anchors

- `_dumps(value: Any) -> str` ([source](../../../../../../src/learnloop/router/plan_log.py), line 82)
- `_hash(value: Any) -> str` ([source](../../../../../../src/learnloop/router/plan_log.py), line 86)
- `_logging_enabled(config: Any) -> bool` ([source](../../../../../../src/learnloop/router/plan_log.py), line 90)
- `_ledger_present(connection: Any) -> bool` ([source](../../../../../../src/learnloop/router/plan_log.py), line 99)
- `_probability(value: Any) -> float | None` ([source](../../../../../../src/learnloop/router/plan_log.py), line 108)
- `_model_columns(record: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router/plan_log.py), line 343) — The R2b columns (reserved since R1, migration 181) from a router record.
- `_store_payloads(connection: Any, record: Mapping[str, Any], row: Mapping[str, Any]) -> None` ([source](../../../../../../src/learnloop/router/plan_log.py), line 368) — R2b: both models' requests and raw answers, beside the decision (own savepoints).
- `_store_context_vector(connection: Any, record: Mapping[str, Any], row: Mapping[str, Any]) -> None` ([source](../../../../../../src/learnloop/router/plan_log.py), line 392) — R2c: the decision's ``decision/context`` vector (computed at prefetch, written after the decision, in its own savepoint; a cache replay never reads).
- `_store_card(connection: Any, decision: Any, row: Mapping[str, Any]) -> None` ([source](../../../../../../src/learnloop/router/plan_log.py), line 424) — R2a: the learner-state card the chooser built, beside its decision.
- `_followup_receipt_key(block_id: Any, workflow_id: Any) -> str` ([source](../../../../../../src/learnloop/router/plan_log.py), line 728)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `INSERT_REF`, `log_plan_block_decision`, `log_plan_interrupt_decision`; statically calls `log_plan_interrupt_decision`
- [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]] — imports `module`
- [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] — imports `existing_followup_decision`, `log_followup_decision`; statically calls `existing_followup_decision`, `log_followup_decision`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/stores/embedding_vectors|learnloop.db.stores.embedding_vectors]] — imports `put_vector`; calls `put_vector`
- [[Reference/Modules/learnloop/db/stores/router|learnloop.db.stores.router]] — imports `ROUTER_LOG_VERSION`, `append_router_decision`, `append_router_payload`, `prune_router_payloads`; calls `append_router_decision`, `append_router_payload`, `prune_router_payloads`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `hashlib`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]], [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_daily_plan_owner_decisions.py](../../../../../../tests/test_daily_plan_owner_decisions.py) — direct import
  - `test_router_r1_logs_plan_block_decisions_through_the_boundary_hook`
- [tests/test_data_capture_a5_not_ready_floor.py](../../../../../../tests/test_data_capture_a5_not_ready_floor.py) — direct import
  - `test_the_restraint_keeps_the_floor_on_not_ready_too`

## Modification guidance

- Make changes here when the responsibility remains plan log within learnloop.router; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router/plan_log.py](../../../../../../src/learnloop/router/plan_log.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
