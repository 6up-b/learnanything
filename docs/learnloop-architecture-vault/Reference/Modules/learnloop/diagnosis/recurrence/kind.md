---
title: "learnloop.diagnosis.recurrence.kind"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/recurrence/kind.py"
source_paths:
  - "src/learnloop/diagnosis/recurrence/kind.py"
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
  - "learnloop.diagnosis.recurrence.kind module"
  - "src/learnloop/diagnosis/recurrence/kind.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-recurrence"
---

# `learnloop.diagnosis.recurrence.kind`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.recurrence.kind` exists within [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] to own the behavior summarized by its module contract: The first match kind: hypothesis recurrence (task ``same_cause``, Slice 2 §3).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/recurrence/kind.py](../../../../../../../src/learnloop/diagnosis/recurrence/kind.py) |
| Source lines | 184 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class HypothesisScope` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/kind.py), line 75)
- `scope_of(subject: Subject) -> HypothesisScope` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/kind.py), line 84)
- `hypothesis_subjects(vault: LoadedVault, repository: Repository, *, attempt_ids: Iterable[str] | None=None) -> list[Subject]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/kind.py), line 94) — Every concrete hypothesis head as a subject (text and hash = its vector's).
- `compatible(query: Subject, candidate: Subject) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/kind.py), line 162) — §9.5 blocking filter: earlier attempt, same facet (else same LO).

### Module constants

- `SAME_CAUSE_TASK` ([src/learnloop/diagnosis/recurrence/kind.py](../../../../../../../src/learnloop/diagnosis/recurrence/kind.py), line 30)
- `SAME_CAUSE_PROMPT_VERSION` ([src/learnloop/diagnosis/recurrence/kind.py](../../../../../../../src/learnloop/diagnosis/recurrence/kind.py), line 31)
- `SAME_CAUSE_ROUTE` ([src/learnloop/diagnosis/recurrence/kind.py](../../../../../../../src/learnloop/diagnosis/recurrence/kind.py), line 32)
- `SAME_CAUSE_PURPOSE` ([src/learnloop/diagnosis/recurrence/kind.py](../../../../../../../src/learnloop/diagnosis/recurrence/kind.py), line 33)
- `HYPOTHESIS_RECIPE` ([src/learnloop/diagnosis/recurrence/kind.py](../../../../../../../src/learnloop/diagnosis/recurrence/kind.py), line 35)
- `_QUESTION` ([src/learnloop/diagnosis/recurrence/kind.py](../../../../../../../src/learnloop/diagnosis/recurrence/kind.py), line 37)
- `_GUIDANCE` ([src/learnloop/diagnosis/recurrence/kind.py](../../../../../../../src/learnloop/diagnosis/recurrence/kind.py), line 43)
- `SAME_CAUSE` ([src/learnloop/diagnosis/recurrence/kind.py](../../../../../../../src/learnloop/diagnosis/recurrence/kind.py), line 57)

### Explicit exports

`__all__` declares:

- `HYPOTHESIS_RECIPE`
- `HypothesisScope`
- `SAME_CAUSE`
- `SAME_CAUSE_PROMPT_VERSION`
- `SAME_CAUSE_PURPOSE`
- `SAME_CAUSE_ROUTE`
- `SAME_CAUSE_TASK`
- `compatible`
- `hypothesis_subjects`
- `scope_of`

## Internal implementation anchors

- `_render(subject: Subject) -> Mapping[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/kind.py), line 52)
- `_facet(target_ref: Any) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/kind.py), line 88)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/recurrence/backlog|learnloop.diagnosis.recurrence.backlog]] — imports `SAME_CAUSE`, `SAME_CAUSE_ROUTE`, `hypothesis_subjects`; statically calls `hypothesis_subjects`
- [[Reference/Modules/learnloop/diagnosis/recurrence/benchmarks|learnloop.diagnosis.recurrence.benchmarks]] — imports `SAME_CAUSE`, `compatible`, `hypothesis_subjects`, `scope_of`; statically calls `compatible`, `hypothesis_subjects`, `scope_of`
- [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]] — imports `SAME_CAUSE`
- [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] — imports `SAME_CAUSE`, `SAME_CAUSE_ROUTE`, `compatible`, `scope_of`; statically calls `scope_of`
- [[Reference/Modules/learnloop/diagnosis/recurrence/live|learnloop.diagnosis.recurrence.live]] — imports `SAME_CAUSE`, `hypothesis_subjects`; statically calls `hypothesis_subjects`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `SAME_CAUSE_ROUTE`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/split/embeddings|learnloop.diagnosis.split.embeddings]] — imports `HYPOTHESIS_FIELD`, `HYPOTHESIS_KIND`, `HYPOTHESIS_VERSION`, `TASK_PREFIX`, `hypothesis_records`; calls `hypothesis_records`
- [[Reference/Modules/learnloop/matching/kinds|learnloop.matching.kinds]] — imports `MatchKind`, `Subject`; calls `MatchKind`, `Subject`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/recurrence/backlog|learnloop.diagnosis.recurrence.backlog]], [[Reference/Modules/learnloop/diagnosis/recurrence/benchmarks|learnloop.diagnosis.recurrence.benchmarks]], [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]], [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]], [[Reference/Modules/learnloop/diagnosis/recurrence/live|learnloop.diagnosis.recurrence.live]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_output_budget.py](../../../../../../../tests/test_output_budget.py) — direct import
  - `test_the_same_cause_judge_is_no_longer_held_to_600_tokens`

## Modification guidance

- Change kind policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/recurrence/kind.py](../../../../../../../src/learnloop/diagnosis/recurrence/kind.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
