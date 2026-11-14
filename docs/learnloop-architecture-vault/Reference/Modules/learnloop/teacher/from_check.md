---
title: "learnloop.teacher.from_check"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/from_check.py"
source_paths:
  - "src/learnloop/teacher/from_check.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.teacher"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.teacher.from_check module"
  - "src/learnloop/teacher/from_check.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-teacher"
---

# `learnloop.teacher.from_check`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.from_check` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: What a diagnostic check found, for a lesson the learner opened from it (``brief["from_check"]``).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/from_check.py](../../../../../../src/learnloop/teacher/from_check.py) |
| Source lines | 141 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `from_check(vault: Any, repository: Any, *, probe_episode_id: str, learning_object_ids: Sequence[str]) -> tuple[dict[str, Any] | None, dict[str, Any]]` ([source](../../../../../../src/learnloop/teacher/from_check.py), line 99) — ``(the brief's entry or None, the open turn's record)`` for a lesson opened from this check.

### Module constants

- `_LOG` ([src/learnloop/teacher/from_check.py](../../../../../../src/learnloop/teacher/from_check.py), line 39)
- `VERSION` ([src/learnloop/teacher/from_check.py](../../../../../../src/learnloop/teacher/from_check.py), line 41)
- `ABOUT` ([src/learnloop/teacher/from_check.py](../../../../../../src/learnloop/teacher/from_check.py), line 44)
- `_TEMPLATE_WORDS` ([src/learnloop/teacher/from_check.py](../../../../../../src/learnloop/teacher/from_check.py), line 48)
- `NOT_FOUND` ([src/learnloop/teacher/from_check.py](../../../../../../src/learnloop/teacher/from_check.py), line 60)
- `OTHER_TOPIC` ([src/learnloop/teacher/from_check.py](../../../../../../src/learnloop/teacher/from_check.py), line 61)
- `STILL_OPEN` ([src/learnloop/teacher/from_check.py](../../../../../../src/learnloop/teacher/from_check.py), line 62)
- `NO_DECISION` ([src/learnloop/teacher/from_check.py](../../../../../../src/learnloop/teacher/from_check.py), line 63)
- `UNREADABLE` ([src/learnloop/teacher/from_check.py](../../../../../../src/learnloop/teacher/from_check.py), line 64)
- `_ENDED` ([src/learnloop/teacher/from_check.py](../../../../../../src/learnloop/teacher/from_check.py), line 66)

### Explicit exports

`__all__` declares:

- `ABOUT`
- `VERSION`
- `from_check`

## Internal implementation anchors

- `_misconception_statement(repository: Any, misconception_id: str) -> str | None` ([source](../../../../../../src/learnloop/teacher/from_check.py), line 69)
- `_gap(vault: Any, repository: Any, label: str) -> dict[str, str]` ([source](../../../../../../src/learnloop/teacher/from_check.py), line 75)
- `_confidence(value: Any) -> str | None` ([source](../../../../../../src/learnloop/teacher/from_check.py), line 89)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `from_check`; statically calls `from_check`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/diagnosis/probe_hypotheses|learnloop.diagnosis.probe_hypotheses]] — imports `CONFUSES_PREFIX`, `H_OTHER`, `H_PROCEDURE_WITHOUT_SELECTION`, `H_RECALL_WITHOUT_MECHANISM`, `H_ROBUST`, `H_SCHEMA_WITHOUT_TRANSFER`, `H_SURFACE_ONLY`, `H_UNFAMILIAR`, `MISCONCEPTION_PREFIX`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_teacher_from_check.py](../../../../../../tests/test_teacher_from_check.py) — direct import
  - `test_a_lesson_opened_from_a_stopped_check_is_told_the_finding_in_topic_words`
  - `test_an_episode_that_does_not_fit_is_ignored_and_the_lesson_still_opens`
  - `test_each_kind_of_gap_is_named_in_the_topic_s_own_words`
  - `test_the_stop_reports_its_episode_and_a_real_decision_reads_as_topic_words`

## Modification guidance

- Make changes here when the responsibility remains from check within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/from_check.py](../../../../../../src/learnloop/teacher/from_check.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
