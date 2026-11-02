---
title: "learnloop.reader.reader_inquiry"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/reader_inquiry.py"
source_paths:
  - "src/learnloop/reader/reader_inquiry.py"
source_commit: "e6d3c96710df3cbdb228f505cada139d72f82cda"
source_commit_timestamp: "2026-11-01T19:56:33-05:00"
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
  - "learnloop.reader.reader_inquiry module"
  - "src/learnloop/reader/reader_inquiry.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.reader_inquiry`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.reader_inquiry` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Reader workbench RW1a: inquiry status, reconnect, and reader activity.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/reader_inquiry.py](../../../../../../src/learnloop/reader/reader_inquiry.py) |
| Source lines | 421 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e6d3c96710df3cbdb228f505cada139d72f82cda` |
| Commit timestamp | `2026-11-01T19:56:33-05:00` |

## Public API

- `class InquiryError(ValueError)` ([source](../../../../../../src/learnloop/reader/reader_inquiry.py), line 175) — A refused inquiry or activity request (nothing was written).
- `resolve_inquiry_root(repository: Repository, *, extraction_id: str, exchange_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_inquiry.py), line 183) — The root exchange of the inquiry ``exchange_id`` belongs to.
- `set_inquiry_status(repository: Repository, *, extraction_id: str, exchange_id: str, resolution: str, trigger: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_inquiry.py), line 210) — Set an inquiry's status on its root question (open | resolved | dismissed).
- `answer_reconnect(repository: Repository, *, extraction_id: str, exchange_id: str, answer: str, via: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_inquiry.py), line 261) — Record the learner's answer to the reconnect line.
- `record_activity(repository: Repository, events: Sequence[Mapping[str, Any]], *, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/reader/reader_inquiry.py), line 370) — Record a batch of Reader activity events; all-or-nothing validation.

### Module constants

- `RESOLUTIONS` ([src/learnloop/reader/reader_inquiry.py](../../../../../../src/learnloop/reader/reader_inquiry.py), line 40)
- `STATUS_TRIGGERS` ([src/learnloop/reader/reader_inquiry.py](../../../../../../src/learnloop/reader/reader_inquiry.py), line 41)
- `RECONNECT_ANSWERS` ([src/learnloop/reader/reader_inquiry.py](../../../../../../src/learnloop/reader/reader_inquiry.py), line 42)
- `RECONNECT_PLACEMENTS` ([src/learnloop/reader/reader_inquiry.py](../../../../../../src/learnloop/reader/reader_inquiry.py), line 43)
- `CLIENT_ACTION_EVENTS` ([src/learnloop/reader/reader_inquiry.py](../../../../../../src/learnloop/reader/reader_inquiry.py), line 47)
- `SERVER_ACTION_EVENTS` ([src/learnloop/reader/reader_inquiry.py](../../../../../../src/learnloop/reader/reader_inquiry.py), line 82)
- `RW1B_SERVER_EVENTS` ([src/learnloop/reader/reader_inquiry.py](../../../../../../src/learnloop/reader/reader_inquiry.py), line 90)
- `RW4A_SERVER_EVENTS` ([src/learnloop/reader/reader_inquiry.py](../../../../../../src/learnloop/reader/reader_inquiry.py), line 101)
- `RW5A_SERVER_EVENTS` ([src/learnloop/reader/reader_inquiry.py](../../../../../../src/learnloop/reader/reader_inquiry.py), line 111)
- `RW5D_SERVER_EVENTS` ([src/learnloop/reader/reader_inquiry.py](../../../../../../src/learnloop/reader/reader_inquiry.py), line 121)
- `INQUIRY_EVENTS` ([src/learnloop/reader/reader_inquiry.py](../../../../../../src/learnloop/reader/reader_inquiry.py), line 130)
- `CLIENT_ACTIVITY_KINDS` ([src/learnloop/reader/reader_inquiry.py](../../../../../../src/learnloop/reader/reader_inquiry.py), line 133)
- `ACTIVITY_FIELDS` ([src/learnloop/reader/reader_inquiry.py](../../../../../../src/learnloop/reader/reader_inquiry.py), line 144)
- `WAIT_ACTIVITY_FIELDS` ([src/learnloop/reader/reader_inquiry.py](../../../../../../src/learnloop/reader/reader_inquiry.py), line 170)
- `MAX_FIELD_CHARS` ([src/learnloop/reader/reader_inquiry.py](../../../../../../src/learnloop/reader/reader_inquiry.py), line 171)
- `MAX_EVENTS_PER_CALL` ([src/learnloop/reader/reader_inquiry.py](../../../../../../src/learnloop/reader/reader_inquiry.py), line 172)
- `_CAMEL` ([src/learnloop/reader/reader_inquiry.py](../../../../../../src/learnloop/reader/reader_inquiry.py), line 317)

### Explicit exports

`__all__` declares:

- `CLIENT_ACTION_EVENTS`
- `RW1B_SERVER_EVENTS`
- `RW4A_SERVER_EVENTS`
- `RW5A_SERVER_EVENTS`
- `RW5D_SERVER_EVENTS`
- `CLIENT_ACTIVITY_KINDS`
- `INQUIRY_EVENTS`
- `InquiryError`
- `MAX_FIELD_CHARS`
- `RECONNECT_ANSWERS`
- `SERVER_ACTION_EVENTS`
- `answer_reconnect`
- `record_activity`
- `resolve_inquiry_root`
- `set_inquiry_status`

## Internal implementation anchors

- `_snake(key: str) -> str` ([source](../../../../../../src/learnloop/reader/reader_inquiry.py), line 320)
- `_clean_value(value: Any) -> Any` ([source](../../../../../../src/learnloop/reader/reader_inquiry.py), line 324)
- `_clean_payload(payload: Mapping[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_inquiry.py), line 334)
- `_validate(entry: Mapping[str, Any]) -> tuple[str, str | None, dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/reader_inquiry.py), line 353)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `answer_reconnect`, `record_activity`, `resolve_inquiry_root`, `set_inquiry_status`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/salience_firewall|learnloop.attempts.salience_firewall]] — imports `salience_payload`; calls `salience_payload`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `module`; calls `ask_history`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `log_interaction_event`; calls `log_interaction_event`
- [[Reference/Modules/learnloop/tutor/question_queue|learnloop.tutor.question_queue]] — imports `module`; calls `set_question_resolution`

### Platform and third-party dependencies

- Standard library: `__future__`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/recap_fixtures.py](../../../../../../tests/recap_fixtures.py) — direct import
- [tests/test_figure_rich_rpc.py](../../../../../../tests/test_figure_rich_rpc.py) — direct import
  - `test_rich_build_cancelled_is_a_salience_only_event_without_words`
- [tests/test_figures_rpc.py](../../../../../../tests/test_figures_rpc.py) — direct import
  - `test_server_events_are_salience_only`
- [tests/test_figures_show_me.py](../../../../../../tests/test_figures_show_me.py) — direct import
  - `test_show_me_requested_is_a_salience_only_event_without_the_words`
  - `test_the_intent_boxs_figure_action_is_show_me_while_on`
- [tests/test_library_ask.py](../../../../../../tests/test_library_ask.py) — direct import
  - `test_every_rw4a_event_is_salience_only_refused_as_evidence_and_never_client_recorded`
- [tests/test_reader_activity.py](../../../../../../tests/test_reader_activity.py) — direct import
  - `test_activity_keeps_only_known_fields_and_no_learner_text`
  - `test_activity_on_a_transcript_records_like_any_source`
  - `test_every_client_event_is_salience_only_and_never_evidence`
  - `test_every_server_event_is_salience_only_and_never_evidence`
  - `test_the_vocabulary_is_the_spec_list_plus_the_funnels_rows`
  - `test_unknown_or_server_owned_events_are_refused_whole`
- [tests/test_reader_ca5_also_in_books.py](../../../../../../tests/test_reader_ca5_also_in_books.py) — direct import
  - `test_peeked_and_opened_are_salience_only_client_events_with_ids_only`
- [tests/test_reader_ca6_side_by_side.py](../../../../../../tests/test_reader_ca6_side_by_side.py) — direct import
  - `test_a_side_by_side_session_keeps_its_id_and_minutes_for_the_evaluation`
  - `test_each_ca6_event_is_salience_only_keeps_ids_and_drops_words`
  - `test_one_definition_of_each_correspondence_event_and_field`
  - `test_the_ca6_events_are_client_events_and_server_owned_ones_stay_refused`
- [tests/test_reader_cues.py](../../../../../../tests/test_reader_cues.py) — direct import
  - `test_the_client_records_cue_impressions_and_cannot_forge_a_tap`
  - `test_the_report_counts_marks_shown_taps_and_choices_against_marks_shown`
- [tests/test_reader_inquiry_status.py](../../../../../../tests/test_reader_inquiry_status.py) — direct import
  - `test_inquiries_work_on_every_source_kind`
  - `test_invalid_status_requests_are_refused_before_any_write`
  - `test_status_flips_write_no_evidence`
  - `test_status_lives_on_the_root_question_and_reopen_is_accepted`
- [tests/test_reader_reconnect.py](../../../../../../tests/test_reader_reconnect.py) — direct import
  - `test_migration_185_and_the_inquiry_check_under_production_sqlite`
  - `test_reconnect_and_its_check_on_every_source_kind`
  - `test_reconnect_refuses_unknown_answers`
  - `test_reconnect_still_unclear_only_records_the_answer`
  - `test_reconnect_yes_resolves_the_root_as_a_self_report`
- [tests/test_reader_reconstruct.py](../../../../../../tests/test_reader_reconstruct.py) — direct import
  - `test_every_rw1b_event_is_salience_only_refused_as_evidence_and_never_client_recorded`
- [tests/test_reader_report.py](../../../../../../tests/test_reader_report.py) — direct import
- [tests/test_reader_tutor_offers.py](../../../../../../tests/test_reader_tutor_offers.py) — direct import
  - `test_a_press_is_a_salience_only_reader_event_counted_by_the_report`
- [tests/test_salience_firewall.py](../../../../../../tests/test_salience_firewall.py) — direct import
  - `test_rw3b_cue_events_are_salience_only_server_events_the_client_cannot_record`
- [tests/test_sketch_service.py](../../../../../../tests/test_sketch_service.py) — direct import
  - `test_sketch_events_are_salience_only_client_events`

## Modification guidance

- Change reader inquiry policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/reader_inquiry.py](../../../../../../src/learnloop/reader/reader_inquiry.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
