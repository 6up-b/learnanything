---
title: "learnloop.reader_learner_state"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader_learner_state.py"
source_paths:
  - "src/learnloop/reader_learner_state.py"
source_commit: "a2d2176b105ab0dc48837944ad2d6663280cc4d2"
source_commit_timestamp: "2026-11-01T16:13:42-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader_learner_state module"
  - "src/learnloop/reader_learner_state.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.reader_learner_state`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader_learner_state` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: The Reader tutor's learner state (learner-blindness relax; owner direction 2026-11-01).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader_learner_state.py](../../../../../src/learnloop/reader_learner_state.py) |
| Source lines | 279 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `a2d2176b105ab0dc48837944ad2d6663280cc4d2` |
| Commit timestamp | `2026-11-01T16:13:42-05:00` |

## Public API

- `enabled(vault: Any) -> bool` ([source](../../../../../src/learnloop/reader_learner_state.py), line 96) — The kill switch, ``reader_tutor.learner_state_enabled`` (default on).
- `class ReaderLearnerState` ([source](../../../../../src/learnloop/reader_learner_state.py), line 109) — What one Reader question's tutor context gains (or why it gains nothing).
  - `apply(self, context: Any) -> Any` (line 123; public) — The tutor context with the state (unchanged when there is none).
  - `receipt(self) -> dict[str, Any]` (line 130; public) — What the question's ``source_context`` records (no text).
  - `manifest(self) -> dict[str, Any]` (line 143; public) — The manifest's record: the receipt and exactly what the tutor was given.
- `omitted(reason: str, learning_object_ids: Sequence[str]=()) -> ReaderLearnerState` ([source](../../../../../src/learnloop/reader_learner_state.py), line 149)
- `build(vault: Any, repository: Any, *, learning_object_ids: Sequence[str], now_iso: str) -> ReaderLearnerState` ([source](../../../../../src/learnloop/reader_learner_state.py), line 178) — The learner state on these learning objects strictly before ``now_iso``.

### Module constants

- `_LOG` ([src/learnloop/reader_learner_state.py](../../../../../src/learnloop/reader_learner_state.py), line 53)
- `VERSION` ([src/learnloop/reader_learner_state.py](../../../../../src/learnloop/reader_learner_state.py), line 56)
- `NOTE` ([src/learnloop/reader_learner_state.py](../../../../../src/learnloop/reader_learner_state.py), line 57)
- `TOPIC_LIMIT` ([src/learnloop/reader_learner_state.py](../../../../../src/learnloop/reader_learner_state.py), line 64)
- `ATTEMPT_LIMIT` ([src/learnloop/reader_learner_state.py](../../../../../src/learnloop/reader_learner_state.py), line 65)
- `EXCHANGE_LIMIT` ([src/learnloop/reader_learner_state.py](../../../../../src/learnloop/reader_learner_state.py), line 66)
- `TEXT_LIMIT` ([src/learnloop/reader_learner_state.py](../../../../../src/learnloop/reader_learner_state.py), line 67)
- `READINESS_WORDS` ([src/learnloop/reader_learner_state.py](../../../../../src/learnloop/reader_learner_state.py), line 69)
- `READINESS_UNREAD` ([src/learnloop/reader_learner_state.py](../../../../../src/learnloop/reader_learner_state.py), line 75)
- `READINESS_INACTIVE` ([src/learnloop/reader_learner_state.py](../../../../../src/learnloop/reader_learner_state.py), line 76)
- `OMITTED_COLD` ([src/learnloop/reader_learner_state.py](../../../../../src/learnloop/reader_learner_state.py), line 79)
- `OMITTED_NO_TOPICS` ([src/learnloop/reader_learner_state.py](../../../../../src/learnloop/reader_learner_state.py), line 80)
- `OMITTED_UNREADABLE` ([src/learnloop/reader_learner_state.py](../../../../../src/learnloop/reader_learner_state.py), line 81)
- `OMITTED_UNGUARDED_BINDING` ([src/learnloop/reader_learner_state.py](../../../../../src/learnloop/reader_learner_state.py), line 84)
- `_RESULT_WORDS` ([src/learnloop/reader_learner_state.py](../../../../../src/learnloop/reader_learner_state.py), line 86)
- `_EXCHANGE_CONTEXTS` ([src/learnloop/reader_learner_state.py](../../../../../src/learnloop/reader_learner_state.py), line 93)

### Explicit exports

`__all__` declares:

- `ATTEMPT_LIMIT`
- `EXCHANGE_LIMIT`
- `NOTE`
- `OMITTED_COLD`
- `OMITTED_NO_TOPICS`
- `OMITTED_UNGUARDED_BINDING`
- `OMITTED_UNREADABLE`
- `READINESS_WORDS`
- `ReaderLearnerState`
- `TEXT_LIMIT`
- `TOPIC_LIMIT`
- `VERSION`
- `build`
- `enabled`
- `omitted`

## Internal implementation anchors

- `_excerpt(text: Any, limit: int=TEXT_LIMIT) -> str` ([source](../../../../../src/learnloop/reader_learner_state.py), line 103)
- `_readiness(vault: Any, repository: Any, los: Sequence[str], now_iso: str) -> dict[str, str]` ([source](../../../../../src/learnloop/reader_learner_state.py), line 153)
- `_attempt_text(row: Mapping[str, Any], held: frozenset[str]) -> str` ([source](../../../../../src/learnloop/reader_learner_state.py), line 166)
- `_build(vault: Any, repository: Any, los: list[str], now_iso: str) -> ReaderLearnerState` ([source](../../../../../src/learnloop/reader_learner_state.py), line 194)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/reader_tutor|learnloop_sidecar.handlers.reader_tutor]] — imports `module`; statically calls `build`, `enabled`, `omitted`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/confidence_events|learnloop.confidence_events]] — imports `module`; calls `safe_learner_events`
- [[Reference/Modules/learnloop/daily_plan/headline|learnloop.daily_plan.headline]] — imports `module`; calls `classify_learning_objects`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `module`; calls `PastWork`, `attempt_result`, `withheld_items`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/reader_tutor|learnloop_sidecar.handlers.reader_tutor]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_learner_blindness_relax.py](../../../../../tests/test_learner_blindness_relax.py) — direct import
  - `test_a_cold_administration_carries_no_learner_state_and_keeps_the_exclusions`
  - `test_the_reader_tutor_reads_the_learner_state_through_the_protection`
  - `test_the_state_carries_no_stored_answer_and_unreadable_protection_carries_nothing`
- [tests/test_learner_blindness_relax_codex_review.py](../../../../../tests/test_learner_blindness_relax_codex_review.py) — direct import
  - `test_a_cross_item_feedback_chain_carries_no_answer`
  - `test_a_later_turn_given_an_earlier_turn_from_a_passage_held_out_since_shows_no_answer`
  - `test_a_stored_answer_retrieved_from_a_passage_held_out_since_is_never_shown`
  - `test_a_stored_answer_whose_linked_passage_is_held_out_since_is_never_shown`
  - `test_an_earlier_feedback_turn_of_the_attempt_carries_no_answer`
  - `test_the_module_never_reads_stored_answer_text`
  - `test_with_both_rw1c_switches_off_a_bound_session_carries_no_learner_state`
  - `test_with_both_rw1c_switches_off_a_cold_bound_session_carries_none_as_cold`

## Modification guidance

- Make changes here when the responsibility remains reader learner state within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/reader_learner_state.py](../../../../../src/learnloop/reader_learner_state.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
