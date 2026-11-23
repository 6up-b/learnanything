---
title: "learnloop_sidecar.handlers.goal_lens"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/goal_lens.py"
source_paths:
  - "src/learnloop_sidecar/handlers/goal_lens.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop_sidecar.handlers.goal_lens module"
  - "src/learnloop_sidecar/handlers/goal_lens.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.goal_lens`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.goal_lens` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Reader workbench v2 RD6 RPCs: the goal lens (spec §3.4, §12.2-§12.5, §12.8).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/goal_lens.py](../../../../../../src/learnloop_sidecar/handlers/goal_lens.py) |
| Source lines | 224 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `class GoalBandInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/goal_lens.py), line 120)
- `goal_band(ctx: SidecarContext, params: GoalBandInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/goal_lens.py), line 125) — The goal band (§12.2) and the path view's data (§12.5).
- `class GoalLensInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/goal_lens.py), line 145)
  - `_range(self) -> GoalLensInput` (line 154; internal)
- `goal_lens(ctx: SidecarContext, params: GoalLensInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/goal_lens.py), line 165) — Each section's level for the goal across one reading, or the visible range of it (§12.3).
- `class SectionChoiceInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/goal_lens.py), line 193)
- `goal_section_choice(ctx: SidecarContext, params: SectionChoiceInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/goal_lens.py), line 204) — *Read it anyway* on a section the lens dims, for this goal (``none`` clears it).

### Module constants

- `LOG` ([src/learnloop_sidecar/handlers/goal_lens.py](../../../../../../src/learnloop_sidecar/handlers/goal_lens.py), line 38)
- `GOAL_LENS_RPCS` ([src/learnloop_sidecar/handlers/goal_lens.py](../../../../../../src/learnloop_sidecar/handlers/goal_lens.py), line 41)

### Explicit exports

`__all__` declares:

- `GOAL_LENS_RPCS`

## Internal implementation anchors

- `_day_start(clock: Any=None) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/goal_lens.py), line 44) — Today's first instant on the learner's clock, in UTC as stored stamps are.
- `_progress(ctx: SidecarContext, goal_id: str) -> reads.Progress` ([source](../../../../../../src/learnloop_sidecar/handlers/goal_lens.py), line 53) — The Guide's background work for this goal, read without starting any (the path view's inputs).
- `_settled(ctx: SidecarContext, vault: Any, goal_id: str) -> set[str]` ([source](../../../../../../src/learnloop_sidecar/handlers/goal_lens.py), line 68) — The unjudged LOs this sidecar's coverage already tried for the goal with nothing left to judge (no candidate section): their sections are settled.
- `_checks(vault: Any, repository: Any, goal_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop_sidecar/handlers/goal_lens.py), line 81)
- `_model(ctx: SidecarContext, vault: Any, repository: Any, goal_id: str, due: list[dict[str, Any]], answered: list[dict[str, Any]]) -> reads.GoalModel` ([source](../../../../../../src/learnloop_sidecar/handlers/goal_lens.py), line 87)
- `_not_a_deliverable(vault: Any, goal_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/goal_lens.py), line 97) — A goal the learner did not make (it has no deliverable to map): the band says so, the lens is off.
- `_pace(vault: Any, repository: Any, goal: Any) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/goal_lens.py), line 109)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/goals/goal_pace|learnloop.goals.goal_pace]] — imports `compute_goal_pace`; calls `compute_goal_pace`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `goal_report`; calls `goal_report`
- [[Reference/Modules/learnloop/intent/inline_checks|learnloop.intent.inline_checks]] — imports `answered_checks`, `due_checks`; calls `answered_checks`, `due_checks`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `module`; calls `reader_enabled`
- [[Reference/Modules/learnloop/section_map|learnloop.section_map]] — imports `RangeError`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `module`; calls `coverage_key`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `module`; calls `goal_of`
- [[Reference/Modules/learnloop/source_retrieval/goal_lens_choices|learnloop.source_retrieval.goal_lens_choices]] — imports `module`; calls `choose`
- [[Reference/Modules/learnloop/source_retrieval/goal_lens_reads|learnloop.source_retrieval.goal_lens_reads]] — imports `module`; calls `band_view`, `goal_view`, `lens_view`, `read_goal`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/deliverables|learnloop_sidecar.handlers.deliverables]] — imports `module`; calls `_error`, `_likely`, `_require`, `_work`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `_require_source_reader`, `_source_id_for_extraction`; calls `_require_source_reader`, `_source_id_for_extraction`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `logging`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_the_pinned_rd6a_rpcs_are_all_of_them`
- [tests/test_reader_rd6a_goal_lens.py](../../../../../../tests/test_reader_rd6a_goal_lens.py) — direct import
  - `test_the_rpcs_are_registered_desktop_only_and_refuse_extra_fields`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/goal_lens.py](../../../../../../src/learnloop_sidecar/handlers/goal_lens.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
