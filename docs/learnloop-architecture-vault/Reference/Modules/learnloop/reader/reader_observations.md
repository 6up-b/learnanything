---
title: "learnloop.reader.reader_observations"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/reader_observations.py"
source_paths:
  - "src/learnloop/reader/reader_observations.py"
source_commit: "c89c84851bd6efb2023a8365288d63d797f70a63"
source_commit_timestamp: "2026-10-17T15:04:44-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.reader_observations module"
  - "src/learnloop/reader/reader_observations.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.reader_observations`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.reader_observations` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Reader workbench RW6a: the session's formative records (spec_reader_workbench_v1 §9.1, ``ReaderObservationV1``; restored rows 58 and 68; gate G50).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/reader_observations.py](../../../../../../src/learnloop/reader/reader_observations.py) |
| Source lines | 316 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `c89c84851bd6efb2023a8365288d63d797f70a63` |
| Commit timestamp | `2026-10-17T15:04:44-04:00` |

## Public API

- `class ReaderObservationV1` ([source](../../../../../../src/learnloop/reader/reader_observations.py), line 58) — One routing-only formative record (spec §9.1).
  - `__post_init__(self) -> None` (line 75; internal)
  - `as_dict(self) -> dict[str, Any]` (line 81; public)
- `named_gaps(repository: Any, question_event_ids: Sequence[str], *, source_kind: str='tutor_question') -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/reader/reader_observations.py), line 133) — Gaps learner-text gaps named from these reader questions, by question (``source_kind = 'reader_formative'``: from RW1b's missed formative answers, by authored question).
- `still_unclear_observations(vault: Any, repository: Any, *, extraction_id: str, session: ReaderSession, exchanges: Sequence[Mapping[str, Any]] | None=None) -> list[ReaderObservationV1]` ([source](../../../../../../src/learnloop/reader/reader_observations.py), line 168) — RW1a: each reconnect *still unclear* answer in the session, one record.
- `formative_answers(repository: Any, *, extraction_id: str, session: ReaderSession) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/reader_observations.py), line 217) — RW1b's answered next-step, why-step and assumption questions in the session.
- `formative_answer_observations(repository: Any, *, extraction_id: str, session: ReaderSession, vault: Any | None=None) -> list[ReaderObservationV1]` ([source](../../../../../../src/learnloop/reader/reader_observations.py), line 237) — RW1b: the missed (``partly`` / ``no``) formative answers, one record each, with the gaps learner-text gaps named from them as hypotheses.
- `prediction_observations(repository: Any, *, extraction_id: str, session: ReaderSession) -> list[ReaderObservationV1]` ([source](../../../../../../src/learnloop/reader/reader_observations.py), line 266) — RW5a: missed figure predictions.
- `observations_for_session(vault: Any, repository: Any, *, extraction_id: str, session: ReaderSession, exchanges: Sequence[Mapping[str, Any]] | None=None) -> list[ReaderObservationV1]` ([source](../../../../../../src/learnloop/reader/reader_observations.py), line 290) — Every formative record of one session, in time order (deterministic).

### Module constants

- `ROUTING_ONLY` ([src/learnloop/reader/reader_observations.py](../../../../../../src/learnloop/reader/reader_observations.py), line 38)
- `RECORD_VERSION` ([src/learnloop/reader/reader_observations.py](../../../../../../src/learnloop/reader/reader_observations.py), line 39)
- `OBSERVATION_KINDS` ([src/learnloop/reader/reader_observations.py](../../../../../../src/learnloop/reader/reader_observations.py), line 42)
- `FORMATIVE_STYLE_KINDS` ([src/learnloop/reader/reader_observations.py](../../../../../../src/learnloop/reader/reader_observations.py), line 47)
- `MISSED_SELF_CHECKS` ([src/learnloop/reader/reader_observations.py](../../../../../../src/learnloop/reader/reader_observations.py), line 52)
- `UNNAMED_GAP_KINDS` ([src/learnloop/reader/reader_observations.py](../../../../../../src/learnloop/reader/reader_observations.py), line 54)

### Explicit exports

`__all__` declares:

- `FORMATIVE_STYLE_KINDS`
- `OBSERVATION_KINDS`
- `ROUTING_ONLY`
- `ReaderObservationV1`
- `formative_answer_observations`
- `formative_answers`
- `named_gaps`
- `observations_for_session`
- `prediction_observations`
- `still_unclear_observations`

## Internal implementation anchors

- `_payload(raw: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_observations.py), line 99)
- `_span_list(raw: Any) -> list[str]` ([source](../../../../../../src/learnloop/reader/reader_observations.py), line 109)
- `_has_table(repository: Any, name: str) -> bool` ([source](../../../../../../src/learnloop/reader/reader_observations.py), line 117)
- `_span_learning_objects(vault: Any, repository: Any, extraction_id: str, span_ids: Sequence[str]) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/reader/reader_observations.py), line 124)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/reader/recap|learnloop.reader.recap]] — imports `module`; statically calls `formative_answers`, `named_gaps`, `observations_for_session`
- [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]] — imports `named_gaps`; statically calls `named_gaps`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `module`; calls `ask_history`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `learning_objects_for_span`; calls `learning_objects_for_span`
- [[Reference/Modules/learnloop/reader/reader_sessions|learnloop.reader.reader_sessions]] — imports `ReaderSession`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/reader/recap|learnloop.reader.recap]], [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figure_predictions.py](../../../../../../tests/test_figure_predictions.py) — direct import
  - `test_rw6a_lists_a_missed_prediction_as_worth_a_second_look`
- [tests/test_reader_formative_texts.py](../../../../../../tests/test_reader_formative_texts.py) — direct import
  - `test_reading_it_writes_only_gap_rows_and_names_the_observations_hypothesis`
- [tests/test_reader_observation_records.py](../../../../../../tests/test_reader_observation_records.py) — direct import
  - `test_a_record_outside_its_session_is_not_its_sessions`
  - `test_building_the_records_writes_nothing`
  - `test_records_are_deterministic_and_only_of_the_spec_kinds`
  - `test_still_unclear_becomes_one_routing_only_record`
  - `test_the_formative_builders_for_later_phases_read_nothing_today`

## Modification guidance

- Change reader observations policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/reader_observations.py](../../../../../../src/learnloop/reader/reader_observations.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
