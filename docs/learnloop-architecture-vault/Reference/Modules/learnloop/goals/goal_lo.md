---
title: "learnloop.goals.goal_lo"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/goals/goal_lo.py"
source_paths:
  - "src/learnloop/goals/goal_lo.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.goals"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.goals.goal_lo module"
  - "src/learnloop/goals/goal_lo.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-goals"
---

# `learnloop.goals.goal_lo`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.goals.goal_lo` exists within [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] to own the behavior summarized by its module contract: ``create_goal_lo``: a learning object a learner's goal names that the vault does not have yet (spec_teacher_v1 §11.5; spec_deliverable_curriculum_v1 §5.3).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/goals/goal_lo.py](../../../../../../src/learnloop/goals/goal_lo.py) |
| Source lines | 190 |
| Owning package | [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class GoalLoError(ValueError)` ([source](../../../../../../src/learnloop/goals/goal_lo.py), line 50) — A creation refused (``code``: validation_error | capped | no_subject).
  - `__init__(self, code: str, message: str) -> None` (line 53; internal)
- `class GoalLoRequest` ([source](../../../../../../src/learnloop/goals/goal_lo.py), line 59) — What the learner asked for: the phrase of their own words, and the LO proposed for it.
  - `key(self) -> str` (line 72; public) — The request's identity: one goal, one phrase (a retry names the same LO).
- `creation_ids(request: GoalLoRequest) -> tuple[str, str]` ([source](../../../../../../src/learnloop/goals/goal_lo.py), line 78) — ``(concept_id, learning_object_id)``, derived from the request.
- `goal_los_created_today(vault: Any, *, now_iso: str) -> list[str]` ([source](../../../../../../src/learnloop/goals/goal_lo.py), line 85) — Active LOs this action created since today's UTC midnight (any mechanism).
- `creations_today(vault: Any, repository: Any, *, now_iso: str) -> int` ([source](../../../../../../src/learnloop/goals/goal_lo.py), line 101) — The cap's count: text-gap creations kept today plus the goal LOs created today.
- `cap(vault: Any) -> int` ([source](../../../../../../src/learnloop/goals/goal_lo.py), line 107)
- `create_goal_lo(root: Path | str, repository: Any, request: GoalLoRequest, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/goal_lo.py), line 111) — Create the concept and the LO (idempotent per request).
- `undo_goal_lo(root: Path | str, repository: Any, learning_object_id: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/goal_lo.py), line 156) — The created LO goes dormant (its items are no longer served), as a text-gap creation's undo.

### Module constants

- `DELIVERABLE_MECHANISM` ([src/learnloop/goals/goal_lo.py](../../../../../../src/learnloop/goals/goal_lo.py), line 39)
- `TEACHER_MECHANISM` ([src/learnloop/goals/goal_lo.py](../../../../../../src/learnloop/goals/goal_lo.py), line 40)
- `MECHANISMS` ([src/learnloop/goals/goal_lo.py](../../../../../../src/learnloop/goals/goal_lo.py), line 41)
- `EXPLICIT_GOAL_ALLOWANCE` ([src/learnloop/goals/goal_lo.py](../../../../../../src/learnloop/goals/goal_lo.py), line 44)
- `TITLE_CHARS` ([src/learnloop/goals/goal_lo.py](../../../../../../src/learnloop/goals/goal_lo.py), line 46)
- `STATEMENT_CHARS` ([src/learnloop/goals/goal_lo.py](../../../../../../src/learnloop/goals/goal_lo.py), line 47)

### Explicit exports

`__all__` declares:

- `DELIVERABLE_MECHANISM`
- `EXPLICIT_GOAL_ALLOWANCE`
- `GoalLoError`
- `GoalLoRequest`
- `MECHANISMS`
- `TEACHER_MECHANISM`
- `cap`
- `create_goal_lo`
- `creation_ids`
- `creations_today`
- `goal_los_created_today`
- `undo_goal_lo`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `module`; statically calls `GoalLoRequest`, `create_goal_lo`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]] — imports `module`; calls `_hash`, `creations_today`, `day_start`, `slug`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `sync_vault_state`; calls `sync_vault_state`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `upsert_concept`, `upsert_learning_object`; calls `upsert_concept`, `upsert_learning_object`
- [[Reference/Modules/learnloop/vault_lock|learnloop.vault_lock]] — imports `vault_mutation_lock`; calls `vault_mutation_lock`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_deliverable_scope.py](../../../../../../tests/test_deliverable_scope.py) — direct import
  - `test_add_it_creates_the_lo_through_create_goal_lo_and_joins_the_scope`
  - `test_create_goal_lo_keeps_the_text_gap_cap_plus_one_and_undoes_to_dormant`

## Modification guidance

- Change goal lo policy here when goals owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/goals/goal_lo.py](../../../../../../src/learnloop/goals/goal_lo.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
