---
title: "learnloop.teacher.topics"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/topics.py"
source_paths:
  - "src/learnloop/teacher/topics.py"
source_commit: "dc5302d98cfcd397c2bb3678cdb2bf12f232164a"
source_commit_timestamp: "2026-11-06T04:43:14-05:00"
source_worktree_state: "clean"
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
  - "learnloop.teacher.topics module"
  - "src/learnloop/teacher/topics.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-teacher"
---

# `learnloop.teacher.topics`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.topics` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: Teacher TE2: a lesson on a typed goal (spec_teacher_v1 rev 5 §11.5; §7 step 1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/topics.py](../../../../../../src/learnloop/teacher/topics.py) |
| Source lines | 136 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `dc5302d98cfcd397c2bb3678cdb2bf12f232164a` |
| Commit timestamp | `2026-11-06T04:43:14-05:00` |

## Public API

- `class TopicsRefused(ValueError)` ([source](../../../../../../src/learnloop/teacher/topics.py), line 27)
  - `__init__(self, code: str, message: str) -> None` (line 28; internal)
- `protected(vault: Any, repository: Any, text: str) -> bool` ([source](../../../../../../src/learnloop/teacher/topics.py), line 33) — The typed words reproduce a question still reserved or withheld (fail closed: unreadable protection is protected).
- `resolve(vault: Any, repository: Any, text: str, *, client: Any | None=None, clock: Any=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/topics.py), line 49) — The typed goal resolved (``lesson.goal``): ``{"status", "goal_key", "topics": [{learning_object_id, title, phrase}], "unmatched": [{phrase, proposed_title, proposed_statement}], "subject_id", "subjects", "message"}``.
- `class OpenPlan` ([source](../../../../../../src/learnloop/teacher/topics.py), line 80)
- `plan_open(vault: Any, repository: Any, *, text: str, lesson_id: str, add_topics: Sequence[str], subject_id: str | None, client: Any | None=None, clock: Any=None) -> OpenPlan` ([source](../../../../../../src/learnloop/teacher/topics.py), line 87) — Resolve the typed goal again (the stored resolution: no call when nothing changed), create each accepted leftover through ``create_goal_lo`` (``teacher_goal_v1``) and return the lesson's LOs.

### Module constants

- `PROTECTED_LINE` ([src/learnloop/teacher/topics.py](../../../../../../src/learnloop/teacher/topics.py), line 23)
- `FROM_MODEL` ([src/learnloop/teacher/topics.py](../../../../../../src/learnloop/teacher/topics.py), line 24)

### Explicit exports

`__all__` declares:

- `FROM_MODEL`
- `OpenPlan`
- `PROTECTED_LINE`
- `TopicsRefused`
- `plan_open`
- `protected`
- `resolve`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `module`; statically calls `plan_open`
- [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]] — imports `module`; statically calls `resolve`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]] — imports `reserved_findings`, `reserved_questions`; calls `reserved_findings`, `reserved_questions`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `withheld_items`; calls `withheld_items`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `module`; calls `create_lesson_topic`, `resolve_typed_goal`, `typed_goal_key`, `typed_goal_subject`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]], [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_teacher_te2_lessons.py](../../../../../../tests/test_teacher_te2_lessons.py) — direct import
  - `test_a_typed_goal_opens_on_the_los_c0bs_resolver_names_and_says_what_is_not_in_the_books`
- [tests/test_teacher_te2_review_fixes.py](../../../../../../tests/test_teacher_te2_review_fixes.py) — direct import
  - `test_f5_a_metered_typed_goal_resolver_is_sent_nothing`

## Modification guidance

- Make changes here when the responsibility remains topics within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/topics.py](../../../../../../src/learnloop/teacher/topics.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
