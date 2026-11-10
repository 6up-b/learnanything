---
title: "learnloop.daily_plan.plan_records"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/plan_records.py"
source_paths:
  - "src/learnloop/daily_plan/plan_records.py"
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
  - "learnloop.daily_plan.plan_records module"
  - "src/learnloop/daily_plan/plan_records.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.plan_records`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.plan_records` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: The plan's decision records besides its blocks (ADR-017; refactor strategy §3.6, case 2): an offer taken back, a follow-up held or let in, and a boundary step that failed and left the rest of the boundary to decide.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/plan_records.py](../../../../../../src/learnloop/daily_plan/plan_records.py) |
| Source lines | 281 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `offer_withdrawn(*, why: str, block_id: Any, offer_decision_id: Any, forced: Sequence[Mapping[str, Any]]=(), superseded_by: Any=None, shown_on: Any=None, expired_row: bool | None=None, parent_id: str | None=None, record_id: str | None=None) -> DecisionRecord` ([source](../../../../../../src/learnloop/daily_plan/plan_records.py), line 76) — An unanswered offer taken back by the plan, or replaced by a newer decision (``superseded_by``).
- `step_failure(kind: str, rule: str, exc: BaseException, *, facts: Mapping[str, Any] | None=None) -> DecisionRecord` ([source](../../../../../../src/learnloop/daily_plan/plan_records.py), line 106) — A boundary step that raised: its type and ``module:function:line``, never its message.
- `children(records: Iterable[DecisionRecord], parent: DecisionRecord) -> list[DecisionRecord]` ([source](../../../../../../src/learnloop/daily_plan/plan_records.py), line 122) — ``records`` as children of ``parent``: its trace, subject and time, and their own ids.
- `check_block(*, block_id: str, detail_id: str | None, forced: Sequence[Mapping[str, Any]], assignments: Sequence[Any], checks: Sequence[Any], trigger_attempt: str | None, parent_id: str | None, algorithm_version: Any) -> DecisionRecord` ([source](../../../../../../src/learnloop/daily_plan/plan_records.py), line 130) — The day's randomized check block, placed by the rules before the boundary's decision (RO5 §9 item 2): no draw, no alternatives; it names the checks and the forced items it holds first.
- `plan_interrupt(*, outcome: Any, item_id: Any, block_id: Any, plan_id: Any, detail_id: str | None, displaced: Sequence[Any]=(), est_minutes: Any=None, trigger_attempt: str | None=None, config: Any=None) -> list[DecisionRecord]` ([source](../../../../../../src/learnloop/daily_plan/plan_records.py), line 163) — The restraint gate's decision on one follow-up and its components' answers (``model_answer`` children).
- `ad_unavailable(*, phase: str, code: Any, subject_kind: str, subject_id: Any, facts: Mapping[str, Any] | None=None, denials: Sequence[Mapping[str, Any]]=(), error_type: Any=None) -> DecisionRecord` ([source](../../../../../../src/learnloop/daily_plan/plan_records.py), line 224) — Adaptive difficulty could not decide (its view, the plan's facts, its decision, or the plan's re-check of it), so the incumbent did.
- `serve_eligibility(decision: Any, *, block_id: Any, displaced: bool) -> DecisionRecord` ([source](../../../../../../src/learnloop/daily_plan/plan_records.py), line 245) — A planned cold check the serve could not take cold (``serve_eligibility.EligibilityDecision``): displaced from its block, or served as ordinary practice with its task re-timed.

### Module constants

- `OFFER_WITHDRAWN` ([src/learnloop/daily_plan/plan_records.py](../../../../../../src/learnloop/daily_plan/plan_records.py), line 37)
- `PLAN_INTERRUPT` ([src/learnloop/daily_plan/plan_records.py](../../../../../../src/learnloop/daily_plan/plan_records.py), line 38)
- `RANDOMIZED_CHECK` ([src/learnloop/daily_plan/plan_records.py](../../../../../../src/learnloop/daily_plan/plan_records.py), line 39)
- `LESSON_OFFER_BUILD` ([src/learnloop/daily_plan/plan_records.py](../../../../../../src/learnloop/daily_plan/plan_records.py), line 40)
- `AD_SLOT` ([src/learnloop/daily_plan/plan_records.py](../../../../../../src/learnloop/daily_plan/plan_records.py), line 41)
- `SERVE_ELIGIBILITY` ([src/learnloop/daily_plan/plan_records.py](../../../../../../src/learnloop/daily_plan/plan_records.py), line 42)
- `CHECK_DRAW_ERROR` ([src/learnloop/daily_plan/plan_records.py](../../../../../../src/learnloop/daily_plan/plan_records.py), line 45)
- `CHECK_PLACE_ERROR` ([src/learnloop/daily_plan/plan_records.py](../../../../../../src/learnloop/daily_plan/plan_records.py), line 46)
- `BUILDER_ERROR` ([src/learnloop/daily_plan/plan_records.py](../../../../../../src/learnloop/daily_plan/plan_records.py), line 47)
- `CHECK_BLOCK_RULE` ([src/learnloop/daily_plan/plan_records.py](../../../../../../src/learnloop/daily_plan/plan_records.py), line 49)
- `INCUMBENT` ([src/learnloop/daily_plan/plan_records.py](../../../../../../src/learnloop/daily_plan/plan_records.py), line 51)
- `PLAN` ([src/learnloop/daily_plan/plan_records.py](../../../../../../src/learnloop/daily_plan/plan_records.py), line 52)
- `_NUMBER` ([src/learnloop/daily_plan/plan_records.py](../../../../../../src/learnloop/daily_plan/plan_records.py), line 54)
- `_INTERRUPT_STATUS` ([src/learnloop/daily_plan/plan_records.py](../../../../../../src/learnloop/daily_plan/plan_records.py), line 160)

### Explicit exports

`__all__` declares:

- `AD_SLOT`
- `BUILDER_ERROR`
- `CHECK_BLOCK_RULE`
- `CHECK_DRAW_ERROR`
- `CHECK_PLACE_ERROR`
- `INCUMBENT`
- `LESSON_OFFER_BUILD`
- `MODEL_ANSWER`
- `OFFER_WITHDRAWN`
- `PLAN`
- `PLAN_INTERRUPT`
- `RANDOMIZED_CHECK`
- `SERVE_ELIGIBILITY`
- `ad_unavailable`
- `check_block`
- `children`
- `forced_entry`
- `forced_facts`
- `offer_withdrawn`
- `plan_interrupt`
- `serve_eligibility`
- `step_failure`

## Internal implementation anchors

- `_code(value: Any) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/plan_records.py), line 57)
- `_number(value: Any) -> float | int | None` ([source](../../../../../../src/learnloop/daily_plan/plan_records.py), line 61)
- `_compact(values: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/plan_records.py), line 67)
- `_refs(values: Iterable[Any], *, limit: int=IDS_KEPT) -> list[str]` ([source](../../../../../../src/learnloop/daily_plan/plan_records.py), line 71)
- `_where(value: Any) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/plan_records.py), line 116)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `module`; statically calls `ad_unavailable`, `check_block`, `children`, `plan_interrupt`, `serve_eligibility`, `step_failure`
- [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]] — imports `module`; statically calls `offer_withdrawn`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/daily_plan/boundary_records|learnloop.daily_plan.boundary_records]] — imports `IDS_KEPT`, `MODEL_ANSWER`, `component_records`, `forced_entry`, `forced_facts`, `ref`, `wall_now`; calls `component_records`, `forced_facts`, `ref`, `wall_now`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/provenance|learnloop.provenance]] — imports `DecisionRecord`, `module`; calls `DecisionRecord`, `is_code`, `where`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_forced_withdrawal_records.py](../../../../../../tests/test_forced_withdrawal_records.py) — direct import
  - `test_the_builders_keep_ids_numbers_and_codes_only`

## Modification guidance

- Make changes here when the responsibility remains plan records within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/plan_records.py](../../../../../../src/learnloop/daily_plan/plan_records.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
