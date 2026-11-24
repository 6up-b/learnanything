---
title: "learnloop.teacher.compaction"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/compaction.py"
source_paths:
  - "src/learnloop/teacher/compaction.py"
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
  - "learnloop.teacher.compaction module"
  - "src/learnloop/teacher/compaction.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-teacher"
---

# `learnloop.teacher.compaction`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.compaction` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: Lesson-local context forecasts and the durable prompt projection (teacher v2 §4.3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/compaction.py](../../../../../../src/learnloop/teacher/compaction.py) |
| Source lines | 201 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Projection` ([source](../../../../../../src/learnloop/teacher/compaction.py), line 20)
  - `apply(self, history: list[dict[str, Any]]) -> list[dict[str, Any]]` (line 25; public)
- `context_limit(config: Any, client: Any) -> int | None` ([source](../../../../../../src/learnloop/teacher/compaction.py), line 31)
- `forecast(repository: Any, lesson_id: str, client: Any, *, prefix: int, estimated_input: int, output_budget: int, estimate: Callable[[str], int]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/compaction.py), line 36) — Take one sample per physical send.
- `latest(repository: Any, lesson_id: str) -> Projection` ([source](../../../../../../src/learnloop/teacher/compaction.py), line 100)
- `record_requests(repository: Any, lesson_id: str, projection: Projection)` ([source](../../../../../../src/learnloop/teacher/compaction.py), line 114) — Publish the boundary and its decision together at receipt start, before the teacher can send.
- `recent_start(history: Sequence[Mapping[str, Any]]) -> int` ([source](../../../../../../src/learnloop/teacher/compaction.py), line 154) — Preserve the last accepted teacher turn and everything since the one before it.
- `selected(row: Mapping[str, Any], fields: Sequence[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/compaction.py), line 160)
- `summarize(repository: Any, state: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/compaction.py), line 164)
- `decision(state: Any, prefix: int, summary: Mapping[str, Any], facts: Mapping[str, Any], limit: int, entries: int) -> provenance.DecisionRecord` ([source](../../../../../../src/learnloop/teacher/compaction.py), line 189)

### Module constants

- `VERSION` ([src/learnloop/teacher/compaction.py](../../../../../../src/learnloop/teacher/compaction.py), line 16)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `module`; statically calls `Projection`, `context_limit`, `decision`, `forecast`, `latest`, `recent_start`, `record_requests`, `summarize`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `tee_model_calls`; calls `tee_model_calls`
- [[Reference/Modules/learnloop/db/stores/lessons|learnloop.db.stores.lessons]] — imports `module`; calls `checks`, `episode_tables_present`, `episodes`
- [[Reference/Modules/learnloop/db/stores/model_calls|learnloop.db.stores.model_calls]] — imports `annotate_started_receipt`; calls `annotate_started_receipt`
- [[Reference/Modules/learnloop/provenance|learnloop.provenance]] — imports `module`; calls `DecisionRecord`, `ref`, `write`
- [[Reference/Modules/learnloop/teacher/probes|learnloop.teacher.probes]] — imports `module`; calls `probes`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `statistics`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_teacher_te5_compaction.py](../../../../../../tests/test_teacher_te5_compaction.py) — direct import
  - `test_a_long_current_reply_after_short_measured_sends_is_forecast`
  - `test_compacted_correction_records_one_boundary`
  - `test_decision_write_failure_retries_before_any_compacted_send`
  - `test_growth_spread_and_cold_start_are_lesson_local`
  - `test_last_turn_plan_in_receipt_matches_stored_versions`
  - `test_live_boundary_and_predecessor_bytes`

## Modification guidance

- Make changes here when the responsibility remains compaction within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/compaction.py](../../../../../../src/learnloop/teacher/compaction.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
