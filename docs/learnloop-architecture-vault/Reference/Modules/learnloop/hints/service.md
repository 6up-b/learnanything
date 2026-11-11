---
title: "learnloop.hints.service"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/hints/service.py"
source_paths:
  - "src/learnloop/hints/service.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.hints"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.hints.service module"
  - "src/learnloop/hints/service.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-hints"
---

# `learnloop.hints.service`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.hints.service` exists within [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] to own the behavior summarized by its module contract: Adaptive hints H2a: the hint service, ``request_hint`` (spec §4.1, §4.5-§4.7, §5, §6.2, §7, §9).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/hints/service.py](../../../../../../src/learnloop/hints/service.py) |
| Source lines | 1267 |
| Owning package | [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class HintRequestError(ValueError)` ([source](../../../../../../src/learnloop/hints/service.py), line 127) — A request the service refuses as malformed (``code`` names the field).
  - `__init__(self, code: str, message: str, *, field: str | None=None) -> None` (line 130; internal)
- `class HintRequestV1` ([source](../../../../../../src/learnloop/hints/service.py), line 137) — One hint request (§4.1).
- `class HintResultV1` ([source](../../../../../../src/learnloop/hints/service.py), line 164) — What the surface shows (§4.1, §4.8).
  - `as_dict(self) -> dict[str, Any]` (line 193; public)
- `adaptive_enabled(config: Any) -> bool` ([source](../../../../../../src/learnloop/hints/service.py), line 200) — Adaptive hints are on: their kill switch and the telemetry their rows need (a shown hint is counted at submit from its row).
- `hints_envelope(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> SharedDailyEnvelope` ([source](../../../../../../src/learnloop/hints/service.py), line 207) — ``hints.max_daily_cost_usd`` as RW4a/H1's durable daily cap (every process), counting the chooser's and writer's metered receipts at ``hints.price_per_million``; subscription receipts are ``estimated_only``.
- `default_chooser_client(vault: LoadedVault) -> Any | None` ([source](../../../../../../src/learnloop/hints/service.py), line 217) — The ready Decider of ``ai.routing.hint_chooser`` (never a chat fallback, never ``LEARNLOOP_AI_PROVIDER``), or None.
- `reveal_basis(kind: str, level: int) -> str` ([source](../../../../../../src/learnloop/hints/service.py), line 229) — The ``reveal_events`` basis of a hint shown on the practice screen (§5).
- `reveal_exempt(kind: str) -> bool` ([source](../../../../../../src/learnloop/hints/service.py), line 243) — Whether a delivered hint of ``kind`` writes no ``reveal_events`` row.
- `downgrade_allowed(target: Target, request: HintRequestV1) -> bool` ([source](../../../../../../src/learnloop/hints/service.py), line 574) — Whether §4.6's level-3 ``next_step`` downgrade may answer this request (review round 2, V2).
- `unplaced_work(output: HintWriterOutputV1, served_kind: str, target: Target, state: HintState, request: HintRequestV1) -> str | None` ([source](../../../../../../src/learnloop/hints/service.py), line 594) — What a checked answer on work the writer placed on no route and found not clearly valid (both flags false), with a map to place it on, becomes (§4.4; review F7, round 2 V3), or None when it is served as written.
- `request_hint(vault: LoadedVault, repository: Repository, request: HintRequestV1, *, writer_client: Any | None=None, chooser_client_factory: Callable[[], Any] | None=None, seed: str | None=None, clock: Clock | None=None, cancelled: Callable[[], bool] | None=None, claim_verifier: Any | None=None, figure_provider: Callable[[HintState], Mapping[str, Any] | None] | None=None) -> HintResultV1` ([source](../../../../../../src/learnloop/hints/service.py), line 653) — One hint request (§4.1).
- `authored_fallback_allowed(option_set: OptionSet, request: HintRequestV1) -> bool` ([source](../../../../../../src/learnloop/hints/service.py), line 793) — Whether an authored hint (level 3) may answer this request while the writer cannot run (review F5): "More" (levels 1-3 are offered), or a reply to a level-3 hint whose shortcut an authored hint can honour.
- `deliver_hint(repository: Repository, assist_id: str, *, clock: Clock | None=None, item: Any=_UNCHECKED) -> tuple[str, dict[str, Any] | None]` ([source](../../../../../../src/learnloop/hints/service.py), line 1087) — Show a prepared hint (the surface received it): ``shown = 1`` once, with its time, in one transaction with the check that its count is still open.
- `deliver(repository: Repository, assist_id: str, *, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/hints/service.py), line 1117) — :func:`deliver_hint`'s row when this call showed it, else None.
- `undelivered_result(assist_id: str, outcome: str) -> HintResultV1` ([source](../../../../../../src/learnloop/hints/service.py), line 1124) — What the surface receives for a ready hint that was not delivered: no hint text and nothing shown (H2a review F1).
- `reveal_amount(item: PracticeItem, text: str) -> float` ([source](../../../../../../src/learnloop/hints/service.py), line 1136) — How much of the item's answer a shown hint exposes (0..1), for its ``tutor_answer`` reveal (§5): the tutor's overlap measure, as the source spans' (which also measures a short answer), and a full reveal when the text states the exact key (worked help may; leak control keeps it o…
- `shown_text(item: PracticeItem, row: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/hints/service.py), line 1150) — The text a delivered row showed (an authored hint's from the item).
- `record_discriminate_answer(vault: LoadedVault, repository: Repository, *, practice_item_id: str, session_id: str, submission_id: str, question_assist_id: str, answer_md: str, clock: Clock | None=None, surface: str=SURFACE, workbench_session_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/hints/service.py), line 1161) — The learner's answer to a discriminating question (§4.2, §5): one ``help_assists`` row (``assist_kind = 'discriminate_answer'``, counted by neither), typed in the question's own box, never the answer draft.

### Module constants

- `LOG` ([src/learnloop/hints/service.py](../../../../../../src/learnloop/hints/service.py), line 103)
- `REQUEST_VERSION` ([src/learnloop/hints/service.py](../../../../../../src/learnloop/hints/service.py), line 105)
- `RESULT_VERSION` ([src/learnloop/hints/service.py](../../../../../../src/learnloop/hints/service.py), line 106)
- `ENVELOPE` ([src/learnloop/hints/service.py](../../../../../../src/learnloop/hints/service.py), line 108)
- `OWNER_KINDS` ([src/learnloop/hints/service.py](../../../../../../src/learnloop/hints/service.py), line 109)
- `FIT_TASK` ([src/learnloop/hints/service.py](../../../../../../src/learnloop/hints/service.py), line 111)
- `FIT_VERSION` ([src/learnloop/hints/service.py](../../../../../../src/learnloop/hints/service.py), line 112)
- `SURFACE` ([src/learnloop/hints/service.py](../../../../../../src/learnloop/hints/service.py), line 113)
- `SURFACES` ([src/learnloop/hints/service.py](../../../../../../src/learnloop/hints/service.py), line 116)
- `REVEAL_EXEMPT_KINDS` ([src/learnloop/hints/service.py](../../../../../../src/learnloop/hints/service.py), line 240)
- `UNPLACED_WORK` ([src/learnloop/hints/service.py](../../../../../../src/learnloop/hints/service.py), line 560)
- `UNPLACED_MESSAGE` ([src/learnloop/hints/service.py](../../../../../../src/learnloop/hints/service.py), line 561)
- `FROM_GIVENS_MESSAGE` ([src/learnloop/hints/service.py](../../../../../../src/learnloop/hints/service.py), line 562)
- `NO_FITTING_HINT_MESSAGE` ([src/learnloop/hints/service.py](../../../../../../src/learnloop/hints/service.py), line 564)
- `ROUTE_DIRECTED_KINDS` ([src/learnloop/hints/service.py](../../../../../../src/learnloop/hints/service.py), line 568)
- `REVEAL_NOT_RECORDED` ([src/learnloop/hints/service.py](../../../../../../src/learnloop/hints/service.py), line 1078)
- `ITEM_CHANGED` ([src/learnloop/hints/service.py](../../../../../../src/learnloop/hints/service.py), line 1081)
- `_UNCHECKED` ([src/learnloop/hints/service.py](../../../../../../src/learnloop/hints/service.py), line 1084)

### Explicit exports

`__all__` declares:

- `CANCELLED`
- `DISABLED`
- `ENVELOPE`
- `FIT_TASK`
- `HintRequestError`
- `HintRequestV1`
- `HintResultV1`
- `ITEM_CHANGED`
- `OWNER_KINDS`
- `NOT_DELIVERABLE`
- `READY`
- `REFUSED`
- `REQUEST_VERSION`
- `RESULT_VERSION`
- `REVEAL_NOT_RECORDED`
- `SHOWN`
- `SUBMISSION_COMPLETE`
- `UNAVAILABLE`
- `WITHHELD`
- `adaptive_enabled`
- `default_chooser_client`
- `deliver`
- `deliver_hint`
- `hints_envelope`
- `record_discriminate_answer`
- `request_hint`
- `reveal_amount`
- `REVEAL_EXEMPT_KINDS`
- `reveal_basis`
- `reveal_exempt`
- `shown_text`
- `undelivered_result`

## Internal implementation anchors

- `_active_item(vault: LoadedVault, item_id: str) -> PracticeItem` ([source](../../../../../../src/learnloop/hints/service.py), line 253)
- `_answered(state: HintState, request: HintRequestV1) -> EarlierHint | None` ([source](../../../../../../src/learnloop/hints/service.py), line 262)
- `_validate(request: HintRequestV1) -> None` ([source](../../../../../../src/learnloop/hints/service.py), line 277)
- `_validate_workbench(request: HintRequestV1) -> None` ([source](../../../../../../src/learnloop/hints/service.py), line 307) — H3: the ladder takes a rung (1-5) on every "More" request; a reply or a pick answers a shown hint at its own level (§5.2, G63).
- `class _Served` ([source](../../../../../../src/learnloop/hints/service.py), line 335) — What one request produced, before it is written.
- `_check_round(output: HintWriterOutputV1, target: Target, state: HintState, item: PracticeItem) -> tuple[Check, HintWriterOutputV1, str, dict[str, Any] | None]` ([source](../../../../../../src/learnloop/hints/service.py), line 359) — Check one writer answer; returns the check, the answer as served (a discriminating question's text), the served kind and, for ``discriminating``, its ranking.
- `_write(vault: LoadedVault, repository: Repository, item: PracticeItem, state: HintState, target: Target, writer: WriterRoute, *, request: HintRequestV1, assist_id: str, cancelled: Callable[[], bool], claim_verifier: Any | None=None, now_iso: str | None=None) -> _Served` ([source](../../../../../../src/learnloop/hints/service.py), line 411) — Ask, check, re-ask once naming the failure; then the level-3 ``next_step`` downgrade (§4.6), except where it would raise a fixed level (:func:`downgrade_allowed`: then nothing is served); a leak re-asked once, then withheld.
- `_authored(item: PracticeItem, state: HintState, *, index: int | None=None) -> _Served` ([source](../../../../../../src/learnloop/hints/service.py), line 623)
- `_append_fit(repository: Repository, answered: EarlierHint, request: HintRequestV1, *, clock: Clock | None) -> str` ([source](../../../../../../src/learnloop/hints/service.py), line 635) — A "doesn't connect" reply: one ``learner_card`` verdict ``different`` on ``hint_fit``, its subject the answered hint's row (which carries the surface).
- `_writer_down(item: PracticeItem, state: HintState, option_set: OptionSet, request: HintRequestV1, reason: str, message: str) -> _Served` ([source](../../../../../../src/learnloop/hints/service.py), line 779) — No hint can be written (D9's Codex refusal, a capped day, an unpriced or failing route): the item's authored hints serve while they last, saying why; worked help and a reply on a hint with none left get nothing.
- `_choose(vault: LoadedVault, repository: Repository, state: HintState, option_set: OptionSet, request: HintRequestV1, *, assist_id: str, seed: str | None, client_factory: Callable[[], Any] | None, envelope: SharedDailyEnvelope, clock: Clock | None) -> Choice | None` ([source](../../../../../../src/learnloop/hints/service.py), line 824)
- `_choose_workbench(vault: LoadedVault, repository: Repository, state: HintState, option_set: OptionSet, request: HintRequestV1, *, assist_id: str, seed: str | None, client_factory: Callable[[], Any] | None, envelope: SharedDailyEnvelope, clock: Clock | None) -> Choice | None` ([source](../../../../../../src/learnloop/hints/service.py), line 850) — H3: the kind on a rung the learner took (Reader §5.5, G63).
- `_horizon(state: HintState, served: _Served) -> int | None` ([source](../../../../../../src/learnloop/hints/service.py), line 889)
- `_json(value: Any) -> str | None` ([source](../../../../../../src/learnloop/hints/service.py), line 902)
- `_row(vault: LoadedVault, item: PracticeItem, state: HintState, request: HintRequestV1, option_set: OptionSet, choice: Choice | None, served: _Served, *, assist_id: str, requested_at: str, map_record: Mapping[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/hints/service.py), line 906)
- `_result(item: PracticeItem, state: HintState, option_set: OptionSet, choice: Choice | None, served: _Served, *, assist_id: str, fit_id: str | None) -> HintResultV1` ([source](../../../../../../src/learnloop/hints/service.py), line 1000)
- `_unavailable_message(reason: str | None) -> str` ([source](../../../../../../src/learnloop/hints/service.py), line 1056)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/hints/workbench|learnloop.hints.workbench]] — imports `module`; statically calls `deliver_hint`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `module`; statically calls `reveal_amount`
- [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] — imports `HintRequestError`, `HintRequestV1`, `adaptive_enabled`, `module`; statically calls `HintRequestV1`, `HintResultV1`, `adaptive_enabled`, `deliver_hint`, `record_discriminate_answer`, `request_hint`, `reveal_amount`, `reveal_basis`, `reveal_exempt`, `shown_text`, `undelivered_result`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]] — imports `HintRequestError`, `HintRequestV1`, `adaptive_enabled`, `module`; statically calls `HintRequestV1`, `HintResultV1`, `adaptive_enabled`, `default_chooser_client`, `hints_envelope`, `record_discriminate_answer`, `request_hint`, `reveal_amount`, `reveal_exempt`, `shown_text`, `undelivered_result`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `call_labels`, `content_key`; calls `call_labels`, `content_key`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `ready_client_for_task`; calls `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendLimitExceeded`, `spend_envelopes`; calls `spend_envelopes`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/confidence_events|learnloop.confidence_events]] — imports `module`; calls `safe_learner_events`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/help_assists|learnloop.db.stores.help_assists]] — imports `module`; calls `assist`, `count_closed`, `insert_assist`, `kept_draft`, `mark_shown`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/hints/chooser|learnloop.hints.chooser]] — imports `Choice`, `module`; calls `ask`, `fallback_choice`, `learner_pick_choice`, `policy_version`, `single_option_choice`
- [[Reference/Modules/learnloop/hints/contracts|learnloop.hints.contracts]] — imports `Check`, `Target`, `at_givens`, `check_output`, `leak_flags`, `reference_route_id`, `route_distance`; calls `Check`, `Target`, `at_givens`, `check_output`, `leak_flags`, `reference_route_id`, `route_distance`
- [[Reference/Modules/learnloop/hints/discriminating|learnloop.hints.discriminating]] — imports `WEIGHTS_BASIS`, `best_candidate`, `normalize_answer`, `rank_candidates`, `states_a_rival`; calls `best_candidate`, `normalize_answer`, `rank_candidates`, `states_a_rival`
- [[Reference/Modules/learnloop/hints/kinds|learnloop.hints.kinds]] — imports `AI_WRITTEN`, `FROM_THE_ITEM`, `GRAIN`, `KINDS`, `NO_SEPARATING_QUESTION`, `REQUESTS`, `SHORTCUTS`, `WITHHELD_MESSAGE`, `WORKED_LEVELS`, `labels_for`, `worked_help_picks`; calls `labels_for`, `worked_help_picks`
- [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]] — imports `current_map`; calls `current_map`
- [[Reference/Modules/learnloop/hints/maps|learnloop.hints.maps]] — imports `exact_key`, `gives_away`; calls `exact_key`, `gives_away`
- [[Reference/Modules/learnloop/hints/options|learnloop.hints.options]] — imports `FIGURE_KIND`, `OptionSet`, `build_options`; calls `build_options`
- [[Reference/Modules/learnloop/hints/state|learnloop.hints.state]] — imports `EarlierHint`, `HintState`, `assemble_state`, `rivals_payload`; calls `assemble_state`, `rivals_payload`
- [[Reference/Modules/learnloop/hints/workbench|learnloop.hints.workbench]] — imports `module`; calls `apply_context`, `check_steps`, `decider_extra`, `row_columns`, `style_of`, `suggestion_record`, `taken_choice`, `taken_options`, `verify_claims`
- [[Reference/Modules/learnloop/hints/writer|learnloop.hints.writer]] — imports `HintWriterOutputV1`, `PROMPT_VERSION`, `WriterRoute`, `WriterUnavailable`, `build_prompt`, `models_off`; calls `WriterRoute`, `build_prompt`, `models_off`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `SharedDailyEnvelope`, `midnight`; calls `SharedDailyEnvelope`, `midnight`
- [[Reference/Modules/learnloop/symbolic_view|learnloop.symbolic_view]] — imports `claims_view`, `live_switch`, `rounds_view`; calls `claims_view`, `live_switch`, `rounds_view`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `span_answer_overlap`; calls `span_answer_overlap`
- [[Reference/Modules/learnloop/vault/hashes|learnloop.vault.hashes]] — imports `practice_item_hash`; calls `practice_item_hash`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `logging`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/hints/workbench|learnloop.hints.workbench]], [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]], [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]], [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/hint_h2a_review_round2_helpers.py](../../../../../../tests/hint_h2a_review_round2_helpers.py) — direct import
- [tests/hint_service_helpers.py](../../../../../../tests/hint_service_helpers.py) — direct import
- [tests/test_approach_map_replay.py](../../../../../../tests/test_approach_map_replay.py) — direct import
- [tests/test_figures_help.py](../../../../../../tests/test_figures_help.py) — direct import
  - `test_explore_figure_is_offered_only_with_a_qualifying_figure_and_its_propensity_is_logged`
  - `test_with_no_provider_every_request_is_as_before`
  - `test_without_a_qualifying_figure_the_option_is_absent_and_named`
- [tests/test_figures_help_codex_review.py](../../../../../../tests/test_figures_help_codex_review.py) — direct import
  - `test_f5_a_chooser_figure_line_switched_off_before_delivery_is_not_shown`
- [tests/test_hint_contracts.py](../../../../../../tests/test_hint_contracts.py) — direct import
  - `test_a_broken_rule_is_caught_reasked_once_then_fixed`
  - `test_a_continuation_that_reaches_the_goal_is_caught`
  - `test_a_downgrade_that_fails_too_serves_nothing_written`
  - `test_a_leak_fixed_on_the_reask_is_served`
  - `test_a_leaking_hint_is_reasked_once_then_withheld`
  - `test_a_repeated_kind_and_strategy_after_a_reply_is_caught`
  - `test_a_rule_broken_twice_is_downgraded_to_a_level_3_next_step`
  - `test_a_worked_chunk_must_leave_a_gap_and_explain_each_piece`
  - `test_an_authored_hint_that_gives_the_answer_away_is_withheld_and_not_served_again`
  - `test_asking_again_on_the_same_work_calls_the_writer_again`
  - `test_no_waypoint_or_label_carries_a_leak_nodes_state`
  - `test_worked_help_is_not_withheld_for_showing_the_answer`
- [tests/test_hint_discriminating.py](../../../../../../tests/test_hint_discriminating.py) — direct import
  - `test_a_question_that_leaks_is_never_shown`
  - `test_an_answer_names_a_shown_discriminating_question_of_this_attempt`
  - `test_no_positive_eig_downgrades_and_says_why`
  - `test_on_new_work_a_new_discriminating_question_may_be_offered`
- [tests/test_hint_evidence.py](../../../../../../tests/test_hint_evidence.py) — direct import
  - `test_a_withheld_or_undelivered_hint_counts_nothing`
- [tests/test_hint_h2a_review.py](../../../../../../tests/test_hint_h2a_review.py) — direct import
  - `test_f2_the_service_serves_the_smaller_step_on_an_unchanged_draft`
  - `test_f5_a_level_3_reply_falls_back_only_where_the_shortcut_allows_an_authored_hint`
  - `test_f5_a_reply_to_a_level_2_hint_with_the_writer_down_is_not_served_at_level_3`
  - `test_f7_unplaceable_work_gets_a_checked_approach_question_not_a_next_step`
- [tests/test_hint_h2a_review_round2.py](../../../../../../tests/test_hint_h2a_review_round2.py) — direct import
  - `test_v2_a_fixed_level_3_reply_keeps_the_level_3_downgrade`
  - `test_v2_a_reply_or_pick_at_level_2_that_fails_twice_is_not_served_at_level_3`
  - `test_v2_more_keeps_the_section_4_6_downgrade`
  - `test_v3_a_reply_on_unplaceable_work_gets_the_approach_question`
  - `test_v3_the_books_way_on_unplaceable_work_starts_from_the_givens`
  - `test_v3_worked_help_taken_on_unplaceable_work_starts_from_the_givens`
- [tests/test_hint_h2a_review_round3.py](../../../../../../tests/test_hint_h2a_review_round3.py) — direct import
  - `test_w2_the_books_way_after_a_level_2_hint_with_the_draft_cleared_is_not_level_3`
  - `test_w3_a_walkthrough_at_the_givens_that_claims_work_stands_is_re_asked`
  - `test_w4_a_second_zero_eig_answer_from_the_givens_keeps_the_from_givens_contract`
- [tests/test_hint_h2a_review_round4.py](../../../../../../tests/test_hint_h2a_review_round4.py) — direct import
  - `test_r4_a_from_givens_re_ask_needs_the_route_and_a_target_on_it`
  - `test_r4_an_answer_at_the_givens_with_no_route_fails_the_strict_recheck`
- [tests/test_hint_replies.py](../../../../../../tests/test_hint_replies.py) — direct import
  - `test_a_reply_or_pick_names_a_shown_hint_of_this_attempt`
  - `test_a_smaller_step_answers_only_a_waypoint`
  - `test_not_where_stuck_never_repeats_the_earlier_localization`
  - `test_notation_keeps_the_kind_and_quotes_the_learners_symbols`
- [tests/test_hint_service.py](../../../../../../tests/test_hint_service.py) — direct import
  - `test_a_chatgpt_plan_writer_is_estimated_only`
  - `test_a_hint_press_never_serves_worked_help_and_only_a_pick_takes_it`
  - `test_a_metered_writer_inside_the_cap_writes_and_its_receipt_is_counted`
  - `test_the_fallback_serves_authored_hints_in_order_then_the_next_step`
  - `test_the_unset_writer_route_resolves_to_the_active_provider_and_refuses_codex`
  - `test_the_wording_lint_rejects_judging_words_in_every_learner_facing_string`
- [tests/test_workbench_assistance.py](../../../../../../tests/test_workbench_assistance.py) — direct import
  - `test_a_row_is_never_shown_once_its_submission_is_admitted`
- [tests/test_workbench_hint_service.py](../../../../../../tests/test_workbench_hint_service.py) — direct import
  - `test_a_workbench_request_without_its_steps_is_refused_and_a_practice_one_with_them_too`
  - `test_every_workbench_hint_comes_from_request_hint_and_the_suggestion_from_the_service`

## Modification guidance

- Make changes here when the responsibility remains service within learnloop.hints; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/hints/service.py](../../../../../../src/learnloop/hints/service.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
