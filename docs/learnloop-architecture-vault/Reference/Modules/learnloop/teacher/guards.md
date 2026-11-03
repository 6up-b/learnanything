---
title: "learnloop.teacher.guards"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/guards.py"
source_paths:
  - "src/learnloop/teacher/guards.py"
source_commit: "b27393627421b08fcbc773e113271c3a55a594f7"
source_commit_timestamp: "2026-11-01T22:15:41-05:00"
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
  - "learnloop.teacher.guards module"
  - "src/learnloop/teacher/guards.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-teacher"
---

# `learnloop.teacher.guards`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.guards` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: The output guards (spec_teacher_v1 §9.3): every learner-facing field passes three (the message and its choices, a prediction, a check, plan statements and a close's recap: ``service._displayed``).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/guards.py](../../../../../../src/learnloop/teacher/guards.py) |
| Source lines | 142 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `b27393627421b08fcbc773e113271c3a55a594f7` |
| Commit timestamp | `2026-11-01T22:15:41-05:00` |

## Public API

- `class GuardVerdict` ([source](../../../../../../src/learnloop/teacher/guards.py), line 34)
  - `as_dict(self) -> dict[str, Any]` (line 39; public)
- `lesson_keys(vault: Any, repository: Any, learning_object_ids: Iterable[str], exempt_items: Iterable[str]) -> tuple[list[Any], bool]` ([source](../../../../../../src/learnloop/teacher/guards.py), line 47) — ``(keys, unreadable)``: every recorded answer key on these LOs except the exempt items'.
- `key_guard(message: str, keys: Sequence[Any], unreadable: bool) -> GuardVerdict` ([source](../../../../../../src/learnloop/teacher/guards.py), line 69)
- `solution_overlap(text: str, solution: str) -> float` ([source](../../../../../../src/learnloop/teacher/guards.py), line 80) — How much of a committed solution ``text`` exposes (0..1; the tutor's span measure).
- `open_check_guard(message: str, open_check: Mapping[str, Any] | None) -> GuardVerdict` ([source](../../../../../../src/learnloop/teacher/guards.py), line 90)
- `citation_guard(message: str, book: SourceBook) -> GuardVerdict` ([source](../../../../../../src/learnloop/teacher/guards.py), line 101)
- `check_all(message: str, *, keys: Sequence[Any], unreadable: bool, book: SourceBook, open_check: Mapping[str, Any] | None, help_reply: bool) -> GuardVerdict` ([source](../../../../../../src/learnloop/teacher/guards.py), line 116) — The three guards in order (the open check's is skipped for a reply to the learner's own question).
- `cited_aliases(message: str) -> list[str]` ([source](../../../../../../src/learnloop/teacher/guards.py), line 128)

### Module constants

- `CITATION` ([src/learnloop/teacher/guards.py](../../../../../../src/learnloop/teacher/guards.py), line 28)
- `QUOTE_CITATION` ([src/learnloop/teacher/guards.py](../../../../../../src/learnloop/teacher/guards.py), line 30)

### Explicit exports

`__all__` declares:

- `CITATION`
- `GuardVerdict`
- `check_all`
- `citation_guard`
- `cited_aliases`
- `key_guard`
- `lesson_keys`
- `open_check_guard`
- `solution_overlap`

## Internal implementation anchors

- `_normalize(text: str) -> str` ([source](../../../../../../src/learnloop/teacher/guards.py), line 43)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `module`; statically calls `check_all`, `cited_aliases`, `key_guard`, `lesson_keys`, `open_check_guard`, `solution_overlap`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/learner_context|learnloop.learner_context]] — imports `key_book`, `leaks_key`; calls `key_book`, `leaks_key`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `SourceBook`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `span_answer_overlap`, `span_leaks_expected`; calls `span_answer_overlap`, `span_leaks_expected`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/teacher_fakes.py](../../../../../../tests/teacher_fakes.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_figures_prefetch.py](../../../../../../tests/test_figures_prefetch.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_figures_prefetch_review_fixes.py](../../../../../../tests/test_figures_prefetch_review_fixes.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_followups_batch5_lesson.py](../../../../../../tests/test_followups_batch5_lesson.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_followups_batch5_recap_dependencies.py](../../../../../../tests/test_followups_batch5_recap_dependencies.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_followups_batch5_recap_protection.py](../../../../../../tests/test_followups_batch5_recap_protection.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_followups_batch6_review_fixes.py](../../../../../../tests/test_followups_batch6_review_fixes.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_followups_batch6_router_report.py](../../../../../../tests/test_followups_batch6_router_report.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_followups_batch7_prefetch_capped_resume.py](../../../../../../tests/test_followups_batch7_prefetch_capped_resume.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_followups_nov2_figure_provenance.py](../../../../../../tests/test_followups_nov2_figure_provenance.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_reader_rw5d_p4b_teacher_visuals.py](../../../../../../tests/test_reader_rw5d_p4b_teacher_visuals.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_teacher_te1_curriculum_c4.py](../../../../../../tests/test_teacher_te1_curriculum_c4.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]

## Modification guidance

- Make changes here when the responsibility remains guards within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/guards.py](../../../../../../src/learnloop/teacher/guards.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
