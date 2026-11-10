---
title: "learnloop.attempts.grade_records"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/grade_records.py"
source_paths:
  - "src/learnloop/attempts/grade_records.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.attempts.grade_records module"
  - "src/learnloop/attempts/grade_records.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.grade_records`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.grade_records` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: The grade's decision records (refactor B7, ADR-017): what the grader decided, and when a hold first applied.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/grade_records.py](../../../../../../src/learnloop/attempts/grade_records.py) |
| Source lines | 209 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `review_reason_class(reason: str | None) -> tuple[str | None, list[str]]` ([source](../../../../../../src/learnloop/attempts/grade_records.py), line 55) — ``unknown_target_criterion:c1,c2`` -> (``unknown_target_criterion``, [``c1``, ``c2``]); prose -> ``unnamed``.
- `verdict_class(*, rubric_score: float, max_points: float | None, correctness: float | None, attempt_type: str | None, declared_dont_know: bool, declared_stuck: bool) -> str` ([source](../../../../../../src/learnloop/attempts/grade_records.py), line 65)
- `grade_record(*, attempt_id: str, practice_item_id: str | None, learning_object_id: str | None, rubric_score: float, max_points: float | None, correctness: float | None, grader_confidence: float | None, grading_source: str | None, grader_mode: str | None, manual_review_reason: str | None, fallback_reason: str | None=None, agent_run_id: str | None=None, attempt_type: str | None=None, hints_used: int=0, declared_dont_know: bool=False, declared_stuck: bool=False, primed: bool=False, fsrs_rating: str | None=None, error_types: Iterable[Any]=(), held: bool=False, plan_presentation_id: str | None=None, probe_presentation_id: str | None=None, session_id: str | None=None, algorithm_version: str | None=None, grader_identity: tuple[str, str] | None=None, decided_by: str | None=None) -> provenance.DecisionRecord` ([source](../../../../../../src/learnloop/attempts/grade_records.py), line 80) — One grade's record (pure): the verdict class as ``rule``; the score, its maximum and the review reason's code in ``facts``; the grader's identity in ``versions``.
- `held_record(*, attempt_id: str, parent_id: str | None, manual_review_reason: str | None, unverified_criterion_ids: Iterable[Any]=(), contract_unrecorded: bool=False, algorithm_version: str | None=None) -> provenance.DecisionRecord` ([source](../../../../../../src/learnloop/attempts/grade_records.py), line 145) — The record of a hold's first application (pure): the grade is provisional, no evidence and no FSRS review, until a regrade or an adjudication assesses a criterion.
- `record_grade(repository: Any, *, held: bool, unverified_criterion_ids: Iterable[Any]=(), **grade: Any) -> str | None` ([source](../../../../../../src/learnloop/attempts/grade_records.py), line 166) — Write the grade's record, and its hold's when ``held``, in the caller's transaction; the grade record's id.
- `held_now(repository: Any, attempt_id: str) -> bool` ([source](../../../../../../src/learnloop/attempts/grade_records.py), line 194) — THE held predicate over the ledger for one attempt, for a record only: a failed read is ``False`` and a warning, never an exception into the grade it describes.
- `error_types_of(events: Iterable[Mapping[str, Any]]) -> list[Any]` ([source](../../../../../../src/learnloop/attempts/grade_records.py), line 208)

### Module constants

- `LOG` ([src/learnloop/attempts/grade_records.py](../../../../../../src/learnloop/attempts/grade_records.py), line 26)
- `GRADE` ([src/learnloop/attempts/grade_records.py](../../../../../../src/learnloop/attempts/grade_records.py), line 28)
- `GRADE_HELD` ([src/learnloop/attempts/grade_records.py](../../../../../../src/learnloop/attempts/grade_records.py), line 29)
- `_DECIDED_BY` ([src/learnloop/attempts/grade_records.py](../../../../../../src/learnloop/attempts/grade_records.py), line 37)
- `IDS_PER_LIST` ([src/learnloop/attempts/grade_records.py](../../../../../../src/learnloop/attempts/grade_records.py), line 40)

## Internal implementation anchors

- `_code(value: Any) -> str | None` ([source](../../../../../../src/learnloop/attempts/grade_records.py), line 43)
- `_ids(values: Iterable[Any]) -> tuple[list[str], int]` ([source](../../../../../../src/learnloop/attempts/grade_records.py), line 47) — Up to :data:`IDS_PER_LIST` code ids, and how many there were in all (odd ids counted, never named).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `error_types_of`, `record_grade`; statically calls `error_types_of`, `record_grade`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `held_now`, `record_grade`; statically calls `held_now`, `record_grade`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/provenance|learnloop.db.stores.provenance]] — imports `module`; calls `write_decision`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `attempt_grade_held`; calls `attempt_grade_held`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `GRADE_CONTRACT_UNRECORDED`, `GRADE_HELD_FOR_REVIEW`
- [[Reference/Modules/learnloop/provenance|learnloop.provenance]] — imports `module`; calls `DecisionRecord`, `current_cause`, `current_trace`, `is_code`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_attempt_chain_records.py](../../../../../../tests/test_attempt_chain_records.py) — direct import
  - `test_a_held_grade_gets_a_record_when_the_hold_first_applies`
  - `test_a_live_held_attempt_writes_its_hold_record_in_the_attempt_step`
  - `test_grade_records_hold_no_prose`
  - `test_verdict_classes`
- [tests/test_provenance.py](../../../../../../tests/test_provenance.py) — direct import
  - `test_a_rebuild_never_calls_the_record_and_keeps_its_rows`

## Modification guidance

- Change grade records policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/grade_records.py](../../../../../../src/learnloop/attempts/grade_records.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
