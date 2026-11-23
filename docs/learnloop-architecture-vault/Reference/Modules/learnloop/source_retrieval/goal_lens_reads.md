---
title: "learnloop.source_retrieval.goal_lens_reads"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/goal_lens_reads.py"
source_paths:
  - "src/learnloop/source_retrieval/goal_lens_reads.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.source_retrieval"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.source_retrieval.goal_lens_reads module"
  - "src/learnloop/source_retrieval/goal_lens_reads.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.goal_lens_reads`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.goal_lens_reads` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: The goal lens's reads (Reader workbench v2 §12): everything ``curriculum.goal_lens`` (the pure level rules) is computed from, gathered from the real model and never computed a second time.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/goal_lens_reads.py](../../../../../../src/learnloop/source_retrieval/goal_lens_reads.py) |
| Source lines | 371 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class GoalModel` ([source](../../../../../../src/learnloop/source_retrieval/goal_lens_reads.py), line 39) — One goal's lens inputs, read once per request.
- `read_goal(vault: Any, repository: Repository, goal_id: str, *, held: Iterable[str]=(), answered: Iterable[str]=(), settled: Iterable[str]=(), progress: Progress=_no_progress, clock: Any=None) -> GoalModel` ([source](../../../../../../src/learnloop/source_retrieval/goal_lens_reads.py), line 83) — The goal's model now.
- `primary_of(model: GoalModel, lo_id: str) -> DP.Treatment | None` ([source](../../../../../../src/learnloop/source_retrieval/goal_lens_reads.py), line 172) — The section a click on the LO opens: its path primary, else the first primary-eligible coverage row.
- `depth_sizes(model: GoalModel) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/goal_lens_reads.py), line 181) — Each depth with the size of its path (§12.5, decision D3): its LOs, and the distinct primary sections they read (the path's choice, else coverage's first eligible one) with their minutes at DL1's pace.
- `reading_sections(vault: Any, repository: Repository, model: GoalModel, extraction_id: str, *, from_span_id: str | None=None, to_span_id: str | None=None, t0: float | None=None, t1: float | None=None) -> list[tuple[dict[str, Any], GL.SectionReads]]` ([source](../../../../../../src/learnloop/source_retrieval/goal_lens_reads.py), line 202) — Each section of the reading that the range touches (every section without a range), with the passages of the range it holds and its lens reads.
- `goal_view(goal: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/goal_lens_reads.py), line 257) — "◎ YOUR GOAL · <KIND> · <deadline> (your words, <date set>)" (§12.2 part 1).
- `band_view(vault: Any, repository: Repository, model: GoalModel, *, due: Sequence[Mapping[str, Any]], answered: Sequence[Mapping[str, Any]], likely: LikelyReader | None=None, pace: Mapping[str, Any] | None=None, progress: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/goal_lens_reads.py), line 284) — ``goal.band``: the goal, its LOs as dots, the depth with each depth's size, the next step, pace and the path's view (lines hide their purpose text while a check is due on their LO).
- `lens_view(vault: Any, repository: Repository, model: GoalModel, extraction_id: str, *, from_span_id: str | None=None, to_span_id: str | None=None, t0: float | None=None, t1: float | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/goal_lens_reads.py), line 350) — ``goal.lens``: one level per section the range touches (passages inherit it, decision D1).

### Module constants

- `DEMONSTRATED_LINE` ([src/learnloop/source_retrieval/goal_lens_reads.py](../../../../../../src/learnloop/source_retrieval/goal_lens_reads.py), line 253)
- `UNTESTED_LINE` ([src/learnloop/source_retrieval/goal_lens_reads.py](../../../../../../src/learnloop/source_retrieval/goal_lens_reads.py), line 254)

### Explicit exports

`__all__` declares:

- `GoalModel`
- `LikelyReader`
- `Progress`
- `band_view`
- `depth_sizes`
- `goal_view`
- `lens_view`
- `primary_of`
- `read_goal`
- `reading_sections`

## Internal implementation anchors

- `_closure(vault: Any, needed: Sequence[str], depth: str, background: Mapping[str, set[str]]) -> dict[str, set[str]]` ([source](../../../../../../src/learnloop/source_retrieval/goal_lens_reads.py), line 67)
- `_no_progress(_depth: str | None, _key: str | None) -> tuple[None, bool, None]` ([source](../../../../../../src/learnloop/source_retrieval/goal_lens_reads.py), line 79)
- `_readiness(model: GoalModel, lo_id: str, likely: LikelyReader | None) -> tuple[str, str]` ([source](../../../../../../src/learnloop/source_retrieval/goal_lens_reads.py), line 264)
- `_section_ref(treatment: DP.Treatment | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/source_retrieval/goal_lens_reads.py), line 277)
- `_held_line(line: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/goal_lens_reads.py), line 343) — A path row whose LO has a due check: its purpose text hidden until the check is answered (§12.6.1).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/goal_lens|learnloop_sidecar.handlers.goal_lens]] — imports `module`; statically calls `band_view`, `goal_view`, `lens_view`, `read_goal`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/curriculum/goal_lens|learnloop.curriculum.goal_lens]] — imports `module`; calls `BandLo`, `Coverage`, `GoalLo`, `GoalReads`, `NextLine`, `PathPlace`, `SectionReads`, `band_counts`, `band_learning_objects`, `level_view`, `next_for_goal`, `section_level`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/section_coverage|learnloop.db.stores.section_coverage]] — imports `module`; calls `learning_objects_in_reading`, `table_present`
- [[Reference/Modules/learnloop/section_map|learnloop.section_map]] — imports `extraction_sections`, `range_span_ids`; calls `extraction_sections`, `range_span_ids`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `module`; calls `_current_rows`, `_read`, `_treatments`, `effective_lines`, `owed_among`, `path_inputs`, `path_view`, `prerequisite_closure`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `module`; calls `depth_of`, `goal_of`, `kind_of`, `latest_resolution`
- [[Reference/Modules/learnloop/source_retrieval/goal_lens_choices|learnloop.source_retrieval.goal_lens_choices]] — imports `module`; calls `section_choices`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `module`; calls `lo_statuses`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `module`; calls `Library`, `_active`, `standing`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/goal_lens|learnloop_sidecar.handlers.goal_lens]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/goal_lens|learnloop_sidecar.handlers.goal_lens]]
- [tests/test_reader_rd6a_goal_lens.py](../../../../../../tests/test_reader_rd6a_goal_lens.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/goal_lens|learnloop_sidecar.handlers.goal_lens]]

## Modification guidance

- Make changes here when the responsibility remains goal lens reads within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/goal_lens_reads.py](../../../../../../src/learnloop/source_retrieval/goal_lens_reads.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
