---
title: "learnloop.teacher.exposure"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/exposure.py"
source_paths:
  - "src/learnloop/teacher/exposure.py"
source_commit: "6cad8141ecef068e53fce83d54802d5a726e0b95"
source_commit_timestamp: "2026-11-06T08:54:29-05:00"
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
  - "learnloop.teacher.exposure module"
  - "src/learnloop/teacher/exposure.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-teacher"
---

# `learnloop.teacher.exposure`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.exposure` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: Teacher TE3a (landing ruling R1): what a lesson exposed, frozen at the moment it was shown.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/exposure.py](../../../../../../src/learnloop/teacher/exposure.py) |
| Source lines | 39 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `6cad8141ecef068e53fce83d54802d5a726e0b95` |
| Commit timestamp | `2026-11-06T08:54:29-05:00` |

## Public API

- `exposed_identities(vault: Any, item_ids: Sequence[Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/teacher/exposure.py), line 19) — Per exposed item still in the vault, in id order, its revision's protection identity, ``{practice_item_id, keys, whole}`` (the block keys and whole extractions its canonical exercise and provenance refs cite; ids, no text), the shape of AD's ``outside.source_identity``.

### Module constants

- `EXPOSURE_KEY` ([src/learnloop/teacher/exposure.py](../../../../../../src/learnloop/teacher/exposure.py), line 16)

### Explicit exports

`__all__` declares:

- `EXPOSURE_KEY`
- `exposed_identities`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/teacher/probes|learnloop.teacher.probes]] — imports `EXPOSURE_KEY`, `exposed_identities`; statically calls `exposed_identities`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `item_source_keys`; calls `item_source_keys`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/teacher/probes|learnloop.teacher.probes]], [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_te3a_lesson_opportunity.py](../../../../../../tests/test_te3a_lesson_opportunity.py) — imports consumer [[Reference/Modules/learnloop/teacher/probes|learnloop.teacher.probes]]
- [tests/test_teacher_te2_probes.py](../../../../../../tests/test_teacher_te2_probes.py) — imports consumer [[Reference/Modules/learnloop/teacher/probes|learnloop.teacher.probes]]
- [tests/test_teacher_te2_review_fixes.py](../../../../../../tests/test_teacher_te2_review_fixes.py) — imports consumer [[Reference/Modules/learnloop/teacher/probes|learnloop.teacher.probes]]
- [tests/teacher_fakes.py](../../../../../../tests/teacher_fakes.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_figures_prefetch.py](../../../../../../tests/test_figures_prefetch.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_figures_prefetch_review_fixes.py](../../../../../../tests/test_figures_prefetch_review_fixes.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_followups_batch5_lesson.py](../../../../../../tests/test_followups_batch5_lesson.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_followups_batch5_recap_dependencies.py](../../../../../../tests/test_followups_batch5_recap_dependencies.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_followups_batch5_recap_protection.py](../../../../../../tests/test_followups_batch5_recap_protection.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_followups_batch6_review_fixes.py](../../../../../../tests/test_followups_batch6_review_fixes.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_followups_batch6_router_report.py](../../../../../../tests/test_followups_batch6_router_report.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_followups_batch7_prefetch_capped_resume.py](../../../../../../tests/test_followups_batch7_prefetch_capped_resume.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]

## Modification guidance

- Make changes here when the responsibility remains exposure within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/exposure.py](../../../../../../src/learnloop/teacher/exposure.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
