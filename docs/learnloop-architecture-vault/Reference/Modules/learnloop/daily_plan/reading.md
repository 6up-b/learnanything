---
title: "learnloop.daily_plan.reading"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/reading.py"
source_paths:
  - "src/learnloop/daily_plan/reading.py"
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
  - "learnloop.daily_plan.reading module"
  - "src/learnloop/daily_plan/reading.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.reading`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.reading` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: Reading blocks (``spec_daily_loop_v1.md`` §6.10, Q5): as-you-read, no pre-questions in DL1.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/reading.py](../../../../../../src/learnloop/daily_plan/reading.py) |
| Source lines | 307 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `as_you_read_extraction_ids(repository: Any) -> list[str]` ([source](../../../../../../src/learnloop/daily_plan/reading.py), line 48) — Extractions of sources whose applied synthesis brief is ``as_you_read``.
- `next_reading_target(repository: Any, *, extraction_ids: list[str] | None=None, from_furthest: bool=True, exam: Any=None, section_filter: SectionFilter | None=None) -> ReadingTarget | None` ([source](../../../../../../src/learnloop/daily_plan/reading.py), line 87) — The as-you-read section to continue: the most recently progressed source's next unfinished section, else the newest import's first unfinished one.
- `next_listed_reading_target(repository: Any, steps: Sequence[tuple[str, str]], *, from_furthest: bool=True, exam: Any=None, allowed: Callable[[str], bool] | None=None) -> tuple[ReadingTarget | None, int | None]` ([source](../../../../../../src/learnloop/daily_plan/reading.py), line 220) — Curriculum C1 (spec_deliverable_curriculum_v1 §7.6): the first unfinished section of ``steps`` (``(extraction_id, section_id)`` in the deliverable path's order, across books), with the predecessor's rules run first on each candidate: * ``exam`` (the one exam predicate, as :func:…
- `section_start_span(repository: Any, extraction_id: str, section_id: str) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/reading.py), line 290) — The section's first readable span: where the reader opens a reading step.

### Explicit exports

`__all__` declares:

- `SectionFilter`
- `as_you_read_extraction_ids`
- `next_listed_reading_target`
- `next_reading_target`
- `section_start_span`

## Internal implementation anchors

- `_section_words(ir: Any, span_ids: list[str]) -> int` ([source](../../../../../../src/learnloop/daily_plan/reading.py), line 77)
- `_desc(value: str) -> str` ([source](../../../../../../src/learnloop/daily_plan/reading.py), line 143)
- `_first_unfinished(repository: Any, extraction_id: str, progress: dict[str, dict[str, Any]], *, from_furthest: bool=True, exam: Any=None, plannable: Callable[[str], bool] | None=None) -> ReadingTarget | None` ([source](../../../../../../src/learnloop/daily_plan/reading.py), line 148)
- `_unfinished_target(ir: Any, source_id: str, extraction_id: str, section: dict[str, Any], row: dict[str, Any] | None) -> ReadingTarget | None` ([source](../../../../../../src/learnloop/daily_plan/reading.py), line 193) — The section as a reading step, or None when it is finished (completed, no words, or nothing left to read): DL1's rule, shared by every order.
- `_listed_book(repository: Any, extraction_id: str, *, from_furthest: bool, exam: Any) -> tuple[Any, str, dict[str, dict[str, Any]], dict[str, dict[str, Any]]] | None` ([source](../../../../../../src/learnloop/daily_plan/reading.py), line 260) — One book's readable sections for :func:`next_listed_reading_target`, by id, after the exam filter and (U4's order on) the front-matter rule, with its progress rows.
- `_has_progress(row: dict[str, Any] | None) -> bool` ([source](../../../../../../src/learnloop/daily_plan/reading.py), line 286)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `as_you_read_extraction_ids`, `next_listed_reading_target`, `next_reading_target`, `section_start_span`; statically calls `as_you_read_extraction_ids`, `next_listed_reading_target`, `next_reading_target`, `section_start_span`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/front_matter|learnloop.content.sources.front_matter]] — imports `is_front_matter_label`; calls `is_front_matter_label`
- [[Reference/Modules/learnloop/daily_plan/types|learnloop.daily_plan.types]] — imports `ReadingTarget`; calls `ReadingTarget`
- [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]] — imports `extraction_sections`; calls `extraction_sections`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_curriculum_c1_plan_follows_path.py](../../../../../../tests/test_curriculum_c1_plan_follows_path.py) — direct import
  - `test_the_front_matter_rule_runs_first_on_each_candidate`
- [tests/test_daily_plan_reading.py](../../../../../../tests/test_daily_plan_reading.py) — direct import
  - `test_only_as_you_read_imports_offer_reading_and_words_left_shrinks_with_progress`
- [tests/test_exam_protection_identity.py](../../../../../../tests/test_exam_protection_identity.py) — direct import
  - `test_f15_no_reading_order_offers_a_held_back_reading`
  - `test_identity_review_f6_the_kill_switch_restores_the_predecessors_reading_step`
- [tests/test_exam_protection_landing.py](../../../../../../tests/test_exam_protection_landing.py) — direct import
  - `test_the_reading_step_never_offers_a_held_out_section_of_a_book_in_no_source_set`
- [tests/test_ux_phase1_landing.py](../../../../../../tests/test_ux_phase1_landing.py) — direct import
  - `test_the_reading_step_never_offers_exam_material`
- [tests/test_ux_phase1_round2_review.py](../../../../../../tests/test_ux_phase1_round2_review.py) — direct import
  - `test_f2_the_successor_continues_from_the_furthest_section_and_skips_contents`
  - `test_f2_the_switch_off_restores_dl1s_reading_selection_exactly`
- [tests/test_ux_phase1_usability_round1.py](../../../../../../tests/test_ux_phase1_usability_round1.py) — direct import
  - `test_u4_reading_through_a_section_moves_the_reading_step_on`
  - `test_u4_the_reading_step_continues_where_the_learner_left_off`
  - `test_u4_the_reading_step_skips_the_table_of_contents`

## Modification guidance

- Make changes here when the responsibility remains reading within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/reading.py](../../../../../../src/learnloop/daily_plan/reading.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
