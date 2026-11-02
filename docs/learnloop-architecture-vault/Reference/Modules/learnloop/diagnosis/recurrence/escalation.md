---
title: "learnloop.diagnosis.recurrence.escalation"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/recurrence/escalation.py"
source_paths:
  - "src/learnloop/diagnosis/recurrence/escalation.py"
source_commit: "09c9f8d3375a4750bbdd6be835982527e5f687fd"
source_commit_timestamp: "2026-10-13T02:38:19-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.recurrence"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.recurrence.escalation module"
  - "src/learnloop/diagnosis/recurrence/escalation.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-recurrence"
---

# `learnloop.diagnosis.recurrence.escalation`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.recurrence.escalation` exists within [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] to own the behavior summarized by its module contract: The escalated repair (Slice 2 §3.7): a DIFFERENT operator and representation.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/recurrence/escalation.py](../../../../../../../src/learnloop/diagnosis/recurrence/escalation.py) |
| Source lines | 179 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `09c9f8d3375a4750bbdd6be835982527e5f687fd` |
| Commit timestamp | `2026-10-13T02:38:19-04:00` |

## Public API

- `class EscalatedRepair(WireModel)` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/escalation.py), line 54) — One repair of the same cause, through a different operator and representation.
  - `_eliciting_needs_a_question(self) -> 'EscalatedRepair'` (line 68; internal)
- `repair_key(repair: Mapping[str, Any]) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/escalation.py), line 74)
- `escalation_repair_prompt(*, cause: str, learning_object: str | None, count: int, earlier_repairs: Sequence[Mapping[str, Any]], current_repairs: Sequence[Mapping[str, Any]]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/escalation.py), line 90)
- `request_different_repair(*, client: Any, cause: str, learning_object: str | None, count: int, earlier_repairs: Sequence[Mapping[str, Any]], current_repairs: Sequence[Mapping[str, Any]], spend: ReviewSpend, reserve: Reserve | None=None) -> tuple[dict[str, Any] | None, dict[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/escalation.py), line 118) — (the repair, what happened).
- `per_job_spend(cancelled: Callable[[], bool] | None=None, config: Any | None=None) -> ReviewSpend` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/escalation.py), line 163)

### Module constants

- `LOG` ([src/learnloop/diagnosis/recurrence/escalation.py](../../../../../../../src/learnloop/diagnosis/recurrence/escalation.py), line 35)
- `ESCALATION_REPAIR_PROMPT_VERSION` ([src/learnloop/diagnosis/recurrence/escalation.py](../../../../../../../src/learnloop/diagnosis/recurrence/escalation.py), line 37)
- `ESCALATION_REPAIR_PURPOSE` ([src/learnloop/diagnosis/recurrence/escalation.py](../../../../../../../src/learnloop/diagnosis/recurrence/escalation.py), line 38)
- `ESCALATION_REPAIR_ROUTE` ([src/learnloop/diagnosis/recurrence/escalation.py](../../../../../../../src/learnloop/diagnosis/recurrence/escalation.py), line 40)
- `ESCALATION_REPAIR_CAPS` ([src/learnloop/diagnosis/recurrence/escalation.py](../../../../../../../src/learnloop/diagnosis/recurrence/escalation.py), line 42)
- `ESCALATION_REPAIR_PROMPT_TOKENS` ([src/learnloop/diagnosis/recurrence/escalation.py](../../../../../../../src/learnloop/diagnosis/recurrence/escalation.py), line 51)

### Explicit exports

`__all__` declares:

- `ESCALATION_REPAIR_CAPS`
- `ESCALATION_REPAIR_PROMPT_TOKENS`
- `ESCALATION_REPAIR_PROMPT_VERSION`
- `ESCALATION_REPAIR_PURPOSE`
- `ESCALATION_REPAIR_ROUTE`
- `EscalatedRepair`
- `escalation_repair_prompt`
- `per_job_spend`
- `repair_key`
- `request_different_repair`

## Internal implementation anchors

- `_shown(repair: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/escalation.py), line 82)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/recurrence/live|learnloop.diagnosis.recurrence.live]] — imports `per_job_spend`, `repair_key`, `request_different_repair`; statically calls `per_job_spend`, `repair_key`, `request_different_repair`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `ESCALATION_REPAIR_PROMPT_TOKENS`, `ESCALATION_REPAIR_ROUTE`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`; calls `SpendCaps`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `execute_structured_operation`, `render_structured_prompt`; calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/diagnosis/offline_review/spend|learnloop.diagnosis.offline_review.spend]] — imports `ReviewSpend`; calls `ReviewSpend`
- [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] — imports `Reserve`, `admit_beside`, `estimate_tokens`, `model_label`; calls `admit_beside`, `estimate_tokens`, `model_label`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `logging`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/recurrence/live|learnloop.diagnosis.recurrence.live]], [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/recurrence_fakes.py](../../../../../../../tests/recurrence_fakes.py) — direct import
- [tests/test_t6_followup_composition.py](../../../../../../../tests/test_t6_followup_composition.py) — direct import
  - `test_the_escalated_repair_budgets_with_the_vaults_policy`

## Modification guidance

- Change escalation policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/recurrence/escalation.py](../../../../../../../src/learnloop/diagnosis/recurrence/escalation.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
