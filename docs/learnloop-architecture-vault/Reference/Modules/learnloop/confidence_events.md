---
title: "learnloop.confidence_events"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/confidence_events.py"
source_paths:
  - "src/learnloop/confidence_events.py"
source_commit: "e821b00def1604485708ab22d056f785fd075560"
source_commit_timestamp: "2026-10-25T02:47:07-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.confidence_events module"
  - "src/learnloop/confidence_events.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.confidence_events`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.confidence_events` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: Teacher TE0: the learner's confidence, rendered as events (spec_teacher_v1 §15.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/confidence_events.py](../../../../../src/learnloop/confidence_events.py) |
| Source lines | 360 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e821b00def1604485708ab22d056f785fd075560` |
| Commit timestamp | `2026-10-25T02:47:07-04:00` |

## Public API

- `enabled(vault: Any) -> bool` ([source](../../../../../src/learnloop/confidence_events.py), line 97) — TE0's kill switch, ``teacher.confidence_events_enabled`` (default on).
- `class Reading` ([source](../../../../../src/learnloop/confidence_events.py), line 105) — One attempt's tap and hedge read (either may be missing).
  - `present(self) -> bool` (line 113; public)
- `valid_tap(value: Any) -> int | None` ([source](../../../../../src/learnloop/confidence_events.py), line 117)
- `combine_hedges(values: Iterable[Any]) -> str | None` ([source](../../../../../src/learnloop/confidence_events.py), line 125) — An attempt's hedge read from its criterion reads: all hedged, all confident, or ``mixed``; None when no criterion was read either way.
- `hedge_from_record(record: Mapping[str, Any] | None) -> str | None` ([source](../../../../../src/learnloop/confidence_events.py), line 135) — The hedge read of a blind-grade record (its criteria's ``learner_confidence``).
- `result_class(score: Any, max_points: Any, *, held: bool=False) -> str` ([source](../../../../../src/learnloop/confidence_events.py), line 142) — The outcome class of a score out of ``max_points`` (``attempt_result``'s classes).
- `event_text(reading: Reading | None, result: str) -> str | None` ([source](../../../../../src/learnloop/confidence_events.py), line 156) — The event in words ("marked 5/5 sure; wrong"), or None with no reading.
- `current_block(reading: Reading | None, result: str, taps: Sequence[Any]=()) -> dict[str, Any] | None` ([source](../../../../../src/learnloop/confidence_events.py), line 168) — The diagnosed attempt's block (version, note, event and the stated limit over ``taps``, which include its own); None with no reading.
- `taps_limit(taps: Sequence[Any]) -> str | None` ([source](../../../../../src/learnloop/confidence_events.py), line 183) — The stated limit when the taps so far do not span the tap's scale, or None.
- `read_hedges(connection: Any, attempt_ids: Iterable[Any] | None=None) -> dict[str, str]` ([source](../../../../../src/learnloop/confidence_events.py), line 212) — Each attempt's hedge read from its current grading evidence (all attempts when ``attempt_ids`` is None); attempts with none are absent.
- `taps_before(connection: Any, before_iso: str) -> list[int]` ([source](../../../../../src/learnloop/confidence_events.py), line 240) — Every tap on an attempt created strictly before ``before_iso`` (for :func:`taps_limit`).
- `readings(connection: Any, attempts: Sequence[Mapping[str, Any]]) -> dict[str, Reading]` ([source](../../../../../src/learnloop/confidence_events.py), line 252) — The readings of ``attempts`` (rows carrying ``id`` and, when read, ``answer_confidence``); attempts with neither reading are absent.
- `learner_events(vault: Any, repository: Any, *, learning_object_ids: Sequence[str], before_iso: str, titles: Mapping[str, str] | None=None, limit: int=CONTEXT_EVENT_LIMIT) -> dict[str, Any] | None` ([source](../../../../../src/learnloop/confidence_events.py), line 265) — The block a hint-writer or tutor context carries: per topic in ``learning_object_ids``, the learner's confidence events before ``before_iso``, newest first, each "YYYY-MM-DD: <event>", with the stated limit.
- `safe_learner_events(vault: Any, repository: Any, **kwargs: Any) -> dict[str, Any] | None` ([source](../../../../../src/learnloop/confidence_events.py), line 331) — :func:`learner_events`, or None when it cannot be read (never fails a hint or an answer).

### Module constants

- `_LOG` ([src/learnloop/confidence_events.py](../../../../../src/learnloop/confidence_events.py), line 60)
- `VERSION` ([src/learnloop/confidence_events.py](../../../../../src/learnloop/confidence_events.py), line 63)
- `NOTE` ([src/learnloop/confidence_events.py](../../../../../src/learnloop/confidence_events.py), line 65)
- `TAP_MIN` ([src/learnloop/confidence_events.py](../../../../../src/learnloop/confidence_events.py), line 72)
- `TAP_MAX` ([src/learnloop/confidence_events.py](../../../../../src/learnloop/confidence_events.py), line 73)
- `HEDGE_VALUES` ([src/learnloop/confidence_events.py](../../../../../src/learnloop/confidence_events.py), line 74)
- `NOT_GRADER_READS` ([src/learnloop/confidence_events.py](../../../../../src/learnloop/confidence_events.py), line 77)
- `CONTEXT_EVENT_LIMIT` ([src/learnloop/confidence_events.py](../../../../../src/learnloop/confidence_events.py), line 80)
- `_CHUNK` ([src/learnloop/confidence_events.py](../../../../../src/learnloop/confidence_events.py), line 81)
- `_RESULT_WORDS` ([src/learnloop/confidence_events.py](../../../../../src/learnloop/confidence_events.py), line 83)
- `_HEDGE_WORDS` ([src/learnloop/confidence_events.py](../../../../../src/learnloop/confidence_events.py), line 90)

### Explicit exports

`__all__` declares:

- `CONTEXT_EVENT_LIMIT`
- `NOTE`
- `NOT_GRADER_READS`
- `Reading`
- `VERSION`
- `combine_hedges`
- `current_block`
- `enabled`
- `event_text`
- `hedge_from_record`
- `learner_events`
- `read_hedges`
- `readings`
- `result_class`
- `safe_learner_events`
- `taps_before`
- `taps_limit`
- `valid_tap`

## Internal implementation anchors

- `_columns(connection: Any, table: str) -> set[str]` ([source](../../../../../src/learnloop/confidence_events.py), line 203)
- `_chunks(values: Sequence[str]) -> Iterable[Sequence[str]]` ([source](../../../../../src/learnloop/confidence_events.py), line 207)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]] — imports `module`; statically calls `enabled`, `event_text`, `readings`, `taps_before`, `taps_limit`
- [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]] — imports `module`; statically calls `Reading`, `enabled`, `event_text`, `hedge_from_record`, `read_hedges`, `result_class`, `valid_tap`
- [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]] — imports `module`; statically calls `Reading`, `current_block`, `enabled`, `hedge_from_record`, `read_hedges`, `result_class`, `taps_before`, `valid_tap`
- [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]] — imports `module`; statically calls `safe_learner_events`
- [[Reference/Modules/learnloop/reader_learner_state|learnloop.reader_learner_state]] — imports `module`; statically calls `safe_learner_events`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `module`; statically calls `safe_learner_events`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/write_provenance|learnloop.db.stores.write_provenance]] — imports `read_snapshot`; calls `read_snapshot`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `attempt_result`, `module`; calls `attempt_protection`, `attempt_result`, `held_attempts`, `withheld_items`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]], [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]], [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]], [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]], [[Reference/Modules/learnloop/reader_learner_state|learnloop.reader_learner_state]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_teacher_te0_confidence_events.py](../../../../../tests/test_teacher_te0_confidence_events.py) — direct import
  - `test_a_held_grade_reads_held_for_review_in_the_events`
  - `test_events_are_words_with_the_outcome_never_scalars`
  - `test_hedge_reads_combine_without_a_threshold`
  - `test_the_blind_grader_never_reads_a_tap_or_a_hedge_read`
  - `test_the_hint_writer_reads_the_events_and_never_a_protected_attempts`
  - `test_the_hint_writers_events_fail_closed_when_the_protection_cannot_be_read`
  - `test_the_limit_is_stated_only_when_the_taps_do_not_span_the_scale`
  - `test_with_no_confidence_data_the_hint_writers_prompt_is_unchanged`
- [tests/test_teacher_te0_fix_round2.py](../../../../../tests/test_teacher_te0_fix_round2.py) — direct import
  - `test_the_metadata_goes_only_after_every_event_and_the_limit_before_the_notice`
- [tests/test_teacher_te0_review_fixes.py](../../../../../tests/test_teacher_te0_review_fixes.py) — direct import
  - `test_a_regrade_between_the_reads_never_mixes_revisions_in_the_tutor_and_hint_block`
  - `test_offline_and_live_diagnosis_share_the_confidence_block`
  - `test_switched_off_every_reader_gets_its_predecessor_context`
  - `test_switched_off_the_card_is_the_predecessors_card`
  - `test_the_gatherer_bounds_each_topics_events_and_states_the_omission`
  - `test_the_offline_runner_renders_the_confidence_block_into_each_arms_prompt`
- [tests/test_teacher_te1_weight.py](../../../../../tests/test_teacher_te1_weight.py) — direct import
  - `test_the_hedge_reader_matches_confidence_events`

## Modification guidance

- Make changes here when the responsibility remains confidence events within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/confidence_events.py](../../../../../src/learnloop/confidence_events.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
