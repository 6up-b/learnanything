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
| Source lines | 636 |
| Owning package | [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class GoalLo` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 75) — One LO of the goal: needed, a prerequisite at the chosen depth, or one needed only deeper.
- `class PathPlace` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 92) — An LO's line on the path as the learner sees it now (``deliverable_path.effective_lines``).
  - `alternate(self, ref: str) -> tuple[str, str] | None` (line 106; public)
- `class Coverage` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 111) — One standing coverage row at a section (judge or learner).
- `class SectionReads` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 119)
- `class GoalReads` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 136)
- `class LoLevel` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 152)
- `class SectionLevel` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 160)
- `lo_level(lo: GoalLo, place: PathPlace | None, row: Coverage, ref: str) -> LoLevel` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 175) — One goal LO's level at the section ``ref``, which covers it with ``row``'s treatment.
- `section_level(section: SectionReads, goal: GoalReads) -> SectionLevel` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 209) — The section's level for the goal (the rules in this module's docstring).
- `reason_text(level: SectionLevel, section: SectionReads, goal: GoalReads) -> str` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 266) — The why card's "For <goal>: <why>" line (§12.3 point 6): the path's per-section reason for a section it places, assembled from the labels otherwise.
- `learner_line(level: SectionLevel, section: SectionReads, goal: GoalReads) -> str | None` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 308) — The learner's own part in the level: their choice here or on the path, or today's answer.
- `coverage_line(level: SectionLevel, section: SectionReads, goal: GoalReads) -> str | None` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 329) — "coverage: introduces “<LO>” · a goal LO · its primary section · core" (§12.3).
- `level_view(level: SectionLevel, section: SectionReads, goal: GoalReads) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 349) — One section's level as ``goal.lens`` returns it (the frontend's marks, dimming and why card).
- `class BandLo` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 382)
- `band_learning_objects(los: Sequence[BandLo]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 396) — One dot per LO in path order.
- `band_counts(los: Iterable[BandLo]) -> dict[str, int]` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 414) — "N LEARNING OBJECTS · a LIKELY · b UNTESTED": the LOs within the chosen depth.
- `class NextLine` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 423) — One path line as "next for the goal" reads it.
- `next_for_goal(checks_due: int, first_check: Mapping[str, Any] | None, lines: Sequence[NextLine]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 433) — "◇ n cold checks due today", else the next unread primary section, else "the path is read".
- `class Protection` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 474)
  - `of(cls, held: Iterable[str], titles: Iterable[str], sections: Iterable[str]=(), depends: Iterable[str]=()) -> Protection` (line 486; public)
  - `active(self) -> bool` (line 492; public)
  - `names_held(self, text: Any) -> bool` (line 495; public) — Whether words name a held LO: its title as whole words, in any case (so "Rank" is not "ranking").
  - `protects(self, extraction_id: Any, section_id: Any) -> bool` (line 503; public)
  - `lo_masked(self, lo_id: Any) -> bool` (line 506; public)
- `protect_path(view: Mapping[str, Any] | None, protection: Protection) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 534) — The band's path view: a held LO's line names nothing; any line's section, alternates, exercise and reason are masked by what they treat, depend on or say.
- `protect_band(reply: Mapping[str, Any], protection: Protection) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 568) — ``goal.band``: its dots, its next step and its path.
- `protect_lens(reply: Mapping[str, Any], protection: Protection) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 595) — ``goal.lens``: a section treating a held LO (in any goal) is held: its title, reason, coverage line and every LO's name withheld; any other section's words are withheld where they name a held LO.

### Module constants

- `TREATMENTS` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 39)
- `PRIMARY_TREATMENTS` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 40)
- `TREATMENT_VERBS` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 41)
- `LEARNER_ABOUT` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 45)
- `ABOUT` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 46)
- `NEED_ORDER` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 49)
- `LO_LEVELS` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 50)
- `SECTION_LEVELS` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 52)
- `MAPPINGS` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 53)
- `DIMMED` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 55)
- `LO_KINDS` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 59)
- `REASON_KEYS` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 62)
- `HELD_REASON` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 259)
- `READINESS` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 378)
- `NEUTRAL_LO` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 466)
- `NEUTRAL_SECTION` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 468)
- `NEUTRAL_EXERCISE` ([src/learnloop/curriculum/goal_lens.py](../../../../../../src/learnloop/curriculum/goal_lens.py), line 470)

### Explicit exports

`__all__` declares:

- `BandLo`
- `Coverage`
- `GoalLo`
- `GoalReads`
- `LoLevel`
- `NEUTRAL_EXERCISE`
- `NEUTRAL_LO`
- `NEUTRAL_SECTION`
- `NextLine`
- `PathPlace`
- `Protection`
- `SectionLevel`
- `SectionReads`
- `band_counts`
- `band_learning_objects`
- `level_view`
- `lo_level`
- `next_for_goal`
- `protect_band`
- `protect_lens`
- `protect_path`
- `section_level`

## Internal implementation anchors

- `_need_rank(level: str) -> int` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 205)
- `_quoted(title: str) -> str` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 262)
- `_neutral(section: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 510) — A section reference with nothing of what it treats: neutral title, no treatment, no difference.
- `_section(section: Mapping[str, Any] | None, protection: Protection) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/curriculum/goal_lens.py), line 520) — A section reference (a path line's, an alternate, a band dot's primary, ``next``): neutral words when it treats a held LO or its title names one.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/source_retrieval/goal_lens_reads|learnloop.source_retrieval.goal_lens_reads]] — imports `module`; statically calls `BandLo`, `Coverage`, `GoalLo`, `GoalReads`, `NextLine`, `PathPlace`, `Protection`, `SectionReads`, `band_counts`, `band_learning_objects`, `level_view`, `next_for_goal`, `protect_band`, `protect_lens`, `section_level`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/source_retrieval/goal_lens_reads|learnloop.source_retrieval.goal_lens_reads]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rd6_fix_protection.py](../../../../../../tests/test_reader_rd6_fix_protection.py) — direct import
  - `test_a_held_los_own_path_row_names_nothing`
  - `test_a_title_is_matched_as_whole_words`
  - `test_another_goals_due_check_masks_a_shared_section_and_names_nothing_of_it`
  - `test_every_text_bearing_band_field_is_masked`
  - `test_every_text_bearing_lens_field_is_masked`
  - `test_no_string_left_names_the_held_lo_and_nothing_changes_without_a_due_check`
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
