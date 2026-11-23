---
title: "learnloop.curriculum.goal_lens"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/curriculum/goal_lens.py"
source_paths:
  - "src/learnloop/curriculum/goal_lens.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.curriculum"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.curriculum.goal_lens module"
  - "src/learnloop/curriculum/goal_lens.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-curriculum"
---

# `learnloop.curriculum.goal_lens`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.curriculum.goal_lens` exists within [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] to own the behavior summarized by its module contract: The goal lens (Reader workbench v2 §12.2-§12.5): how critical each section is for one goal, and the goal band's summary.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py) |
| Source lines | 446 |
| Owning package | [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class GoalLo` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 74) — One LO of the goal: needed, a prerequisite at the chosen depth, or one needed only deeper.
- `class PathPlace` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 91) — An LO's line on the path as the learner sees it now (``deliverable_path.effective_lines``).
  - `alternate(self, ref: str) -> tuple[str, str] | None` (line 105; public)
- `class Coverage` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 110) — One standing coverage row at a section (judge or learner).
- `class SectionReads` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 118)
- `class GoalReads` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 132)
- `class LoLevel` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 148)
- `class SectionLevel` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 156)
- `lo_level(lo: GoalLo, place: PathPlace | None, row: Coverage, ref: str) -> LoLevel` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 171) — One goal LO's level at the section ``ref``, which covers it with ``row``'s treatment.
- `section_level(section: SectionReads, goal: GoalReads) -> SectionLevel` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 205) — The section's level for the goal (the rules in this module's docstring).
- `reason_text(level: SectionLevel, section: SectionReads, goal: GoalReads) -> str` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 261) — The why card's "For <goal>: <why>" line (§12.3 point 6): the path's per-section reason for a section it places, assembled from the labels otherwise.
- `learner_line(level: SectionLevel, section: SectionReads, goal: GoalReads) -> str | None` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 303) — The learner's own part in the level: their choice here or on the path, or today's answer.
- `coverage_line(level: SectionLevel, section: SectionReads, goal: GoalReads) -> str | None` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 324) — "coverage: introduces “<LO>” · a goal LO · its primary section · core" (§12.3).
- `level_view(level: SectionLevel, section: SectionReads, goal: GoalReads) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 344) — One section's level as ``goal.lens`` returns it (the frontend's marks, dimming and why card).
- `class BandLo` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 377)
- `band_learning_objects(los: Sequence[BandLo]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 391) — One dot per LO in path order.
- `band_counts(los: Iterable[BandLo]) -> dict[str, int]` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 409) — "N LEARNING OBJECTS · a LIKELY · b UNTESTED": the LOs within the chosen depth.
- `class NextLine` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 418) — One path line as "next for the goal" reads it.
- `next_for_goal(checks_due: int, first_check: Mapping[str, Any] | None, lines: Sequence[NextLine]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 428) — "◇ n cold checks due today", else the next unread primary section, else "the path is read".

### Module constants

- `TREATMENTS` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 38)
- `PRIMARY_TREATMENTS` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 39)
- `TREATMENT_VERBS` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 40)
- `LEARNER_ABOUT` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 44)
- `ABOUT` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 45)
- `NEED_ORDER` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 48)
- `LO_LEVELS` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 49)
- `SECTION_LEVELS` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 51)
- `MAPPINGS` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 52)
- `DIMMED` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 54)
- `LO_KINDS` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 58)
- `REASON_KEYS` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 61)
- `HELD_REASON` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 254)
- `READINESS` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 373)

### Explicit exports

`__all__` declares:

- `BandLo`
- `Coverage`
- `GoalLo`
- `GoalReads`
- `LoLevel`
- `NextLine`
- `PathPlace`
- `SectionLevel`
- `SectionReads`
- `band_counts`
- `band_learning_objects`
- `level_view`
- `lo_level`
- `next_for_goal`
- `section_level`

## Internal implementation anchors

- `_need_rank(level: str) -> int` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 201)
- `_quoted(title: str) -> str` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 257)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/source_retrieval/goal_lens_reads|learnloop.source_retrieval.goal_lens_reads]] — imports `module`; statically calls `BandLo`, `Coverage`, `GoalLo`, `GoalReads`, `NextLine`, `PathPlace`, `SectionReads`, `band_counts`, `band_learning_objects`, `level_view`, `next_for_goal`, `section_level`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/source_retrieval/goal_lens_reads|learnloop.source_retrieval.goal_lens_reads]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rd6a_goal_lens.py](../../../../../../tests/test_reader_rd6a_goal_lens.py) — direct import
  - `test_a_due_check_hides_its_los_purpose_text_and_comes_first_next`
- [tests/test_reader_rd6a_goal_lens_core.py](../../../../../../tests/test_reader_rd6a_goal_lens_core.py) — direct import
  - `test_a_held_lo_hides_the_purpose_text_of_every_section_it_is_in`
  - `test_every_level_rule`
  - `test_next_for_the_goal_is_checks_then_the_next_unread_primary_then_read`
  - `test_protected_or_left_out_sections_are_never_mapped`
  - `test_reason_text_is_the_paths_own_line_on_the_path_and_assembled_off_it`
  - `test_the_band_counts_within_the_depth_and_hides_held_names`
  - `test_the_cores_vocabulary_is_coverages`
  - `test_the_learner_line_names_their_choice_or_todays_answer`

## Modification guidance

- Change goal lens policy here when curriculum owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
