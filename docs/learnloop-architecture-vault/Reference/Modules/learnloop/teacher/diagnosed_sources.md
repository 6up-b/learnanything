---
title: "learnloop.teacher.diagnosed_sources"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/diagnosed_sources.py"
source_paths:
  - "src/learnloop/teacher/diagnosed_sources.py"
source_commit: "0cd4a38533deb97d437aef4384c19a05c01d2cf3"
source_commit_timestamp: "2026-11-09T05:33:51-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.teacher"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.teacher.diagnosed_sources module"
  - "src/learnloop/teacher/diagnosed_sources.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-teacher"
---

# `learnloop.teacher.diagnosed_sources`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.diagnosed_sources` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: Instruct hand-off IH7 (spec_instruct_handoff_v1 §7c): the sections a lesson opened after a miss also reads.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/diagnosed_sources.py](../../../../../../src/learnloop/teacher/diagnosed_sources.py) |
| Source lines | 355 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `0cd4a38533deb97d437aef4384c19a05c01d2cf3` |
| Commit timestamp | `2026-11-09T05:33:51-05:00` |

## Public API

- `class Confusion` ([source](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 74) — One statement the sections were searched with.
  - `as_dict(self) -> dict[str, Any]` (line 86; public)
- `class Follow` ([source](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 100) — What :func:`follow` found: the sections to add (in the order they are tried against the budget), the statement indexes that found each, and the record (``status`` and ``why`` always; the rest when searched).
  - `none(self, why: str) -> 'Follow'` (line 110; public)
  - `settle(self, library: Any, rendered: Sequence[Mapping[str, Any]]) -> dict[str, Any]` (line 114; public) — The record once the brief rendered the sections: what was added whole, what the outline holds and why.
  - `brief_entry(self) -> dict[str, Any] | None` (line 136; public) — What the teacher is told: each section, the statement that found it, and where it is listed instead.
- `follow(vault: Any, repository: Any, library: Any, *, origin: str, origin_ref: str | None, learning_object_ids: Sequence[str], in_hand: Collection[tuple[str, str]]) -> Follow | None` ([source](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 288) — The sections a lesson opened from this origin also reads, or None when the lesson is not one that applies (a learner's own start: nothing to say, so no record).

### Module constants

- `_LOG` ([src/learnloop/teacher/diagnosed_sources.py](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 48)
- `VERSION` ([src/learnloop/teacher/diagnosed_sources.py](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 50)
- `_SET_ASIDE` ([src/learnloop/teacher/diagnosed_sources.py](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 53)
- `_NAMING_KINDS` ([src/learnloop/teacher/diagnosed_sources.py](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 55)
- `STATEMENT_CHARS` ([src/learnloop/teacher/diagnosed_sources.py](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 57)
- `NO_ORIGIN` ([src/learnloop/teacher/diagnosed_sources.py](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 59)
- `NO_MISS` ([src/learnloop/teacher/diagnosed_sources.py](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 60)
- `PENDING` ([src/learnloop/teacher/diagnosed_sources.py](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 61)
- `FAILED` ([src/learnloop/teacher/diagnosed_sources.py](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 62)
- `SUPERSEDED` ([src/learnloop/teacher/diagnosed_sources.py](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 63)
- `ABSENT` ([src/learnloop/teacher/diagnosed_sources.py](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 64)
- `NO_CONFUSION` ([src/learnloop/teacher/diagnosed_sources.py](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 65)
- `NOTHING_MATCHED` ([src/learnloop/teacher/diagnosed_sources.py](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 66)
- `PROTECTED` ([src/learnloop/teacher/diagnosed_sources.py](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 67)
- `UNREADABLE` ([src/learnloop/teacher/diagnosed_sources.py](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 68)
- `OVER_BUDGET` ([src/learnloop/teacher/diagnosed_sources.py](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 69)
- `TOPIC_FILLS_BUDGET` ([src/learnloop/teacher/diagnosed_sources.py](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 70)

### Explicit exports

`__all__` declares:

- `Follow`
- `VERSION`
- `follow`

## Internal implementation anchors

- `_clip(text: Any) -> str` ([source](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 148)
- `_table(connection: Any, name: str) -> bool` ([source](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 153)
- `_record_reason(past: Any, connection: Any, kind: str, record_id: str) -> str | None` ([source](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 158) — Why a text's write-time record names something protected, or None: no record is no more than the attempt itself (the router card reads a cause the same way); an incomplete one cannot be established (fail closed).
- `_named(row: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 182)
- `_decision_time(connection: Any, decision_id: str) -> str | None` ([source](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 195)
- `_miss(connection: Any, config: Any, learning_object_ids: Sequence[str], decided_at: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 200) — The latest attempt on the lesson's topics known at the offer's decision (THE availability predicate: a backdated import that arrived later was not what the offer was made on).
- `_why_no_diagnosis(connection: Any, attempt_id: str) -> str` ([source](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 218) — Pending, failed, superseded or absent: the one plain reason the attempt has no diagnosis in force.
- `_statements(vault: Any, repository: Any, connection: Any, past: Any, attempt: Mapping[str, Any]) -> list[Confusion]` ([source](../../../../../../src/learnloop/teacher/diagnosed_sources.py), line 240) — The miss's hypotheses, then its learner-text gaps, each passed through the shared protection.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `OVER_BUDGET`, `TOPIC_FILLS_BUDGET`, `module`; statically calls `follow`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/hypothesis_marks|learnloop.db.stores.hypothesis_marks]] — imports `module`; calls `marks_for_attempt`, `present`
- [[Reference/Modules/learnloop/db/stores/learner_gaps|learnloop.db.stores.learner_gaps]] — imports `module`; calls `gaps_for_attempt`, `reversals`
- [[Reference/Modules/learnloop/db/stores/write_provenance|learnloop.db.stores.write_provenance]] — imports `stored_record`; calls `stored_record`
- [[Reference/Modules/learnloop/followup_serve/marks|learnloop.followup_serve.marks]] — imports `module`; calls `latest_marks`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `PastWork`, `hypothesis_answers`; calls `PastWork`, `hypothesis_answers`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `attempt_time_sql`; calls `attempt_time_sql`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `module`; calls `search_sections`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ih4_preferences_inform_router.py](../../../../../../tests/test_ih4_preferences_inform_router.py) — direct import
  - `test_the_miss_a_lesson_reads_is_what_was_known_at_the_decision`
- [tests/test_ih7_lesson_sources_follow_diagnosis.py](../../../../../../tests/test_ih7_lesson_sources_follow_diagnosis.py) — direct import
  - `test_no_score_or_stuck_flag_selects_sections`

## Modification guidance

- Make changes here when the responsibility remains diagnosed sources within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/diagnosed_sources.py](../../../../../../src/learnloop/teacher/diagnosed_sources.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
