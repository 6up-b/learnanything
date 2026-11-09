---
title: "learnloop.reader.recap"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/recap.py"
source_paths:
  - "src/learnloop/reader/recap.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.recap module"
  - "src/learnloop/reader/recap.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.recap`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.recap` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Reader workbench RW6a: "Last time here", the typed session summary and Wrap up (spec_reader_workbench_v1 §9.1; UX §4.8, S10, S11; gates G25, G31, G50).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/recap.py](../../../../../../src/learnloop/reader/recap.py) |
| Source lines | 916 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class RecapError(ValueError)` ([source](../../../../../../src/learnloop/reader/recap.py), line 76) — A refused recap request (nothing was written).
- `recap_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/reader/recap.py), line 84) — RW6a's card switch (``recap.enabled``, default on).
- `wrap_up_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/reader/recap.py), line 90) — Wrap up's switch (``recap.wrap_up_enabled``, default on).
- `excerpt(text: str | None, limit: int=EXCERPT_CHARS) -> str` ([source](../../../../../../src/learnloop/reader/recap.py), line 100)
- `help_line(*, book_counted: bool, carried: int) -> str` ([source](../../../../../../src/learnloop/reader/recap.py), line 135) — "help so far: the book" -- what a problem has used, in plain words.
- `window(session: RS.ReaderSession | None, *, until: str | None=None) -> RS.ReaderSession` ([source](../../../../../../src/learnloop/reader/recap.py), line 144) — A session-shaped window over all history up to ``until`` (or the session's end).
- `session_summary(vault: Any, repository: Any, *, extraction_id: str, session: RS.ReaderSession, now: datetime) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/recap.py), line 238) — ``ReaderSessionSummaryV1`` for one reader session (a pure read).
- `demonstrated_since(vault: Any, repository: Any, learning_object_ids: Sequence[str], *, after: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/recap.py), line 498) — The LOs demonstrated now that became so after ``after`` (a pure read).
- `source_learning_objects(vault: Any, repository: Any, extraction_id: str) -> list[str]` ([source](../../../../../../src/learnloop/reader/recap.py), line 563) — The Learning Objects this source teaches (provenance-linked to a section).
- `since_last_time(vault: Any, repository: Any, *, extraction_id: str, after: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/recap.py), line 572) — :func:`demonstrated_since` over the real ledger for this source's LOs.
- `retired_checks(repository: Any, *, extraction_id: str, after: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/recap.py), line 578) — Checks retired since as no longer needed (RW6b's re-valuation writes them: a ``retired`` commitment event whose detail names the reason ``no_longer_needed`` and this source), with how the question was answered (``answered_by``: a solve on ``solved_at``, or the rivals settled).
- `build_recap(vault: Any, repository: Any, *, extraction_id: str, current_visit_id: str | None, now: datetime) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/recap.py), line 629) — The returning card for a source, or ``{"recap": None}`` (a pure read).
- `build_wrap_up(vault: Any, repository: Any, *, extraction_id: str, current_visit_id: str | None, now: datetime) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/recap.py), line 744) — The session's three lists: resolved, still open, worth reinforcing.
- `wrap_up_offer(vault: Any, repository: Any, *, now: datetime) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/reader/recap.py), line 852) — The offer where the learner lands (S11): the most recent reader session had activity and no ``wrap_up_opened`` followed its start.
- `record_recap_event(repository: Any, *, extraction_id: str, event: str, visit_id: str | None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/reader/recap.py), line 877) — One salience-only ``reader_action_invoked`` with payload ``event``.

### Module constants

- `RECAP_VERSION` ([src/learnloop/reader/recap.py](../../../../../../src/learnloop/reader/recap.py), line 52)
- `SUMMARY_VERSION` ([src/learnloop/reader/recap.py](../../../../../../src/learnloop/reader/recap.py), line 53)
- `WRAP_UP_VERSION` ([src/learnloop/reader/recap.py](../../../../../../src/learnloop/reader/recap.py), line 54)
- `CARD_EVENTS` ([src/learnloop/reader/recap.py](../../../../../../src/learnloop/reader/recap.py), line 57)
- `WRAP_UP_EVENTS` ([src/learnloop/reader/recap.py](../../../../../../src/learnloop/reader/recap.py), line 58)
- `RECAP_EVENTS` ([src/learnloop/reader/recap.py](../../../../../../src/learnloop/reader/recap.py), line 59)
- `CUE_OPEN_EVENTS` ([src/learnloop/reader/recap.py](../../../../../../src/learnloop/reader/recap.py), line 62)
- `CUE_NOT_RELEVANT_EVENT` ([src/learnloop/reader/recap.py](../../../../../../src/learnloop/reader/recap.py), line 63)
- `CUE_NOT_RELEVANT_UNDONE` ([src/learnloop/reader/recap.py](../../../../../../src/learnloop/reader/recap.py), line 64)
- `EXCERPT_CHARS` ([src/learnloop/reader/recap.py](../../../../../../src/learnloop/reader/recap.py), line 66)
- `TITLE_CHARS` ([src/learnloop/reader/recap.py](../../../../../../src/learnloop/reader/recap.py), line 67)
- `_EPOCH` ([src/learnloop/reader/recap.py](../../../../../../src/learnloop/reader/recap.py), line 69)
- `MARK_WITH_HELP` ([src/learnloop/reader/recap.py](../../../../../../src/learnloop/reader/recap.py), line 72)
- `MARK_DEMONSTRATED` ([src/learnloop/reader/recap.py](../../../../../../src/learnloop/reader/recap.py), line 73)

### Explicit exports

`__all__` declares:

- `CARD_EVENTS`
- `RECAP_EVENTS`
- `RECAP_VERSION`
- `RecapError`
- `SUMMARY_VERSION`
- `WRAP_UP_EVENTS`
- `build_recap`
- `build_wrap_up`
- `demonstrated_since`
- `help_line`
- `recap_enabled`
- `record_recap_event`
- `retired_checks`
- `session_summary`
- `since_last_time`
- `source_learning_objects`
- `wrap_up_enabled`
- `wrap_up_offer`

## Internal implementation anchors

- `_payload(raw: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/recap.py), line 105)
- `_json_list(raw: Any) -> list[Any]` ([source](../../../../../../src/learnloop/reader/recap.py), line 115)
- `_later(left: str | None, right: str | None) -> bool` ([source](../../../../../../src/learnloop/reader/recap.py), line 123)
- `_when(value: str | None) -> datetime | None` ([source](../../../../../../src/learnloop/reader/recap.py), line 128)
- `_inquiry_roots(history: Sequence[Mapping[str, Any]]) -> dict[str, str]` ([source](../../../../../../src/learnloop/reader/recap.py), line 155) — Each exchange's root exchange id (walks the durable parent links).
- `_action_events(repository: Any, events: Iterable[str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/recap.py), line 172)
- `_workbench_rows(repository: Any, extraction_id: str) -> tuple[list[dict[str, Any]], dict[str, list[str]]]` ([source](../../../../../../src/learnloop/reader/recap.py), line 180)
- `_attempts(repository: Any, attempt_ids: Sequence[str]) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/recap.py), line 198)
- `_canonical_facets(vault: Any, raw: Any) -> list[str]` ([source](../../../../../../src/learnloop/reader/recap.py), line 209)
- `_sections(repository: Any, extraction_id: str) -> dict[str, str]` ([source](../../../../../../src/learnloop/reader/recap.py), line 218)
- `_section_progress(repository: Any, extraction_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/recap.py), line 226)
- `_touched_roots(in_session: Sequence[Mapping[str, Any]], roots: Mapping[str, str]) -> list[str]` ([source](../../../../../../src/learnloop/reader/recap.py), line 380) — The inquiries (roots) an exchange of the session belongs to, first seen first.
- `_status_roots(repository: Any, extraction_id: str, window: RS.ReaderSession, by_id: Mapping[str, Any], *, resolution: str | None=None) -> list[str]` ([source](../../../../../../src/learnloop/reader/recap.py), line 391) — Roots whose status was set in ``window`` (to ``resolution`` when given).
- `_sections_read(repository: Any, extraction_id: str, session: RS.ReaderSession) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/recap.py), line 408)
- `_claims(vault: Any, repository: Any, session: RS.ReaderSession, worked: Sequence[Mapping[str, Any]], attempts: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/recap.py), line 417) — Facets the session's work was assisted on, with no unassisted success since.
- `_effective_success_since(points: Sequence[Any], since: str) -> bool` ([source](../../../../../../src/learnloop/reader/recap.py), line 464) — Some attempt made at or after ``since`` whose latest point still banks unassisted, unprimed credit (the attempt's effective grading, after the embedded-share cap: what it adds to certification credit now, against the cells' final totals).
- `_capabilities_at(points: Sequence[Any], moment: str) -> set[str]` ([source](../../../../../../src/learnloop/reader/recap.py), line 486) — The capabilities a facet had demonstrated credit at, as of ``moment`` (its curve's last point at or before it; every cell as the ledger banks it).
- `_dismissed(repository: Any, extraction_id: str, since: str) -> bool` ([source](../../../../../../src/learnloop/reader/recap.py), line 610)
- `_continue_at(repository: Any, extraction_id: str, session: RS.ReaderSession) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/reader/recap.py), line 617)
- `_status_action(action: str, extraction_id: str, root_id: str, resolution: str, trigger: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/recap.py), line 738)
- `_source_id(repository: Any, extraction_id: str) -> str | None` ([source](../../../../../../src/learnloop/reader/recap.py), line 844)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `source_learning_objects`; statically calls `source_learning_objects`
- [[Reference/Modules/learnloop/daily_plan/router_reader|learnloop.daily_plan.router_reader]] — imports `module`; statically calls `_action_events`, `_continue_at`, `_effective_success_since`
- [[Reference/Modules/learnloop/instructional/reader_digest|learnloop.instructional.reader_digest]] — imports `module`; statically calls `_sections`, `session_summary`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `module`; statically calls `_source_id`, `session_summary`
- [[Reference/Modules/learnloop/intent/control|learnloop.intent.control]] — imports `source_learning_objects`; statically calls `source_learning_objects`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `session_summary`, `source_learning_objects`; statically calls `session_summary`, `source_learning_objects`
- [[Reference/Modules/learnloop_sidecar/handlers/recap|learnloop_sidecar.handlers.recap]] — imports `module`; statically calls `build_recap`, `build_wrap_up`, `recap_enabled`, `record_recap_event`, `wrap_up_enabled`, `wrap_up_offer`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/salience_firewall|learnloop.attempts.salience_firewall]] — imports `salience_payload`; calls `salience_payload`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/goals/certification|learnloop.goals.certification]] — imports `is_demonstrated_credit`; calls `is_demonstrated_credit`
- [[Reference/Modules/learnloop/goals/goal_certification|learnloop.goals.goal_certification]] — imports `lo_certification`; calls `lo_certification`
- [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]] — imports `facet_evidence_timelines`, `vault_timeline_snapshot`; calls `facet_evidence_timelines`, `vault_timeline_snapshot`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `module`; calls `ask_history`
- [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]] — imports `extraction_sections`; calls `extraction_sections`
- [[Reference/Modules/learnloop/reader/reader_observations|learnloop.reader.reader_observations]] — imports `module`; calls `formative_answers`, `named_gaps`, `observations_for_session`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `learning_objects_by_section`, `learning_objects_for_span`; calls `learning_objects_by_section`, `learning_objects_for_span`
- [[Reference/Modules/learnloop/reader/reader_sessions|learnloop.reader.reader_sessions]] — imports `module`; calls `ReaderSession`, `all_sessions`, `iso_seconds`, `sessions_for_source`, `split_sessions`
- [[Reference/Modules/learnloop/reader/workbench|learnloop.reader.workbench]] — imports `module`; calls `book_counted`, `carried_hints`, `open_session_days`, `session_hints`, `session_row`, `sessions_for_source`, `statement_cleared`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `log_interaction_event`; calls `log_interaction_event`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `learning_object_facet_union`; calls `learning_object_facet_union`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/router_reader|learnloop.daily_plan.router_reader]], [[Reference/Modules/learnloop/instructional/reader_digest|learnloop.instructional.reader_digest]], [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]], [[Reference/Modules/learnloop/intent/control|learnloop.intent.control]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_inversion.py](../../../../../../tests/test_ad23_inversion.py) — direct import
- [tests/test_intent_codex_review.py](../../../../../../tests/test_intent_codex_review.py) — direct import
- [tests/test_reader_followups.py](../../../../../../tests/test_reader_followups.py) — direct import
  - `test_a_claim_needing_an_independent_check_is_a_retention_question`
  - `test_revaluation_retires_a_follow_up_answered_since_with_its_reason`
  - `test_the_cards_good_news_names_how_the_question_was_answered_and_drops_a_restored_check`
- [tests/test_reader_followups_review.py](../../../../../../tests/test_reader_followups_review.py) — direct import
  - `test_f7_an_open_causal_factor_with_competing_repairs_is_a_decision_question`
- [tests/test_reader_observation_records.py](../../../../../../tests/test_reader_observation_records.py) — direct import
  - `test_building_the_records_writes_nothing`
  - `test_still_unclear_becomes_one_routing_only_record`
- [tests/test_reader_recap.py](../../../../../../tests/test_reader_recap.py) — direct import
  - `test_claims_needing_an_independent_check_are_assisted_only_facets`
  - `test_dismiss_hides_the_card_until_the_next_session`
  - `test_no_card_on_a_first_visit_or_within_the_same_session`
  - `test_since_last_time_reads_the_real_ledger_without_inventing_a_gain`
  - `test_the_card_reads_still_open_unfinished_and_worth_a_second_look`
  - `test_the_kill_switches_default_on_and_the_config_dto_names_them`
  - `test_the_summary_keeps_to_its_session`
  - `test_the_typed_summary_is_deterministic_from_the_ledgers`
- [tests/test_reader_recap_review.py](../../../../../../tests/test_reader_recap_review.py) — direct import
  - `test_f4_an_old_inquiry_resolved_and_undone_in_the_reader_stays_listed`
  - `test_f4_resolving_at_the_destination_moves_the_inquiry_to_resolved_with_undo`
  - `test_f8_an_abandoned_problem_is_in_the_recap_with_a_reopen`
- [tests/test_reader_recap_review_r2.py](../../../../../../tests/test_reader_recap_review_r2.py) — direct import
  - `test_f1_r2_a_later_regrade_does_not_rewrite_the_credit_banked_before_the_cutoff`
- [tests/test_reader_recap_review_r3.py](../../../../../../tests/test_reader_recap_review_r3.py) — direct import
  - `test_f1_r3_a_hold_released_after_the_cutoff_still_holds_at_the_cutoff`
- [tests/test_reader_wrap_up.py](../../../../../../tests/test_reader_wrap_up.py) — direct import
  - `test_an_inquiry_or_a_workbench_session_is_activity`
  - `test_scrolling_highlights_and_cue_taps_alone_are_not_activity`
  - `test_the_footer_offer_follows_the_current_session_only`
  - `test_the_offer_appears_where_the_learner_lands_until_wrap_up_is_opened`
  - `test_the_offer_reads_the_most_recent_session_only`
  - `test_wrap_up_lists_resolved_still_open_and_worth_reinforcing`
- [tests/test_router_reader_activity.py](../../../../../../tests/test_router_reader_activity.py) — direct import
  - `test_a_narrative_written_after_the_cutoff_is_not_shown_at_it`
  - `test_a_real_missed_prediction_reaches_the_section_through_its_figure`
  - `test_a_session_that_touched_the_lo_only_through_a_figure_is_kept_for_its_prediction`

## Modification guidance

- Change recap policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/recap.py](../../../../../../src/learnloop/reader/recap.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
