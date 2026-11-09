---
title: "learnloop.reader.reader_dialogue"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/reader_dialogue.py"
source_paths:
  - "src/learnloop/reader/reader_dialogue.py"
source_commit: "38ccfa65f8d3889cdb161cd5db0cea3a5d0582f0"
source_commit_timestamp: "2026-11-09T06:12:48-05:00"
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
  - "learnloop.reader.reader_dialogue module"
  - "src/learnloop/reader/reader_dialogue.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.reader_dialogue`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.reader_dialogue` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: P2 step B.11 -- minimal bidirectional reader dialogue (U-033, spec §7.6).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py) |
| Source lines | 1467 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `38ccfa65f8d3889cdb161cd5db0cea3a5d0582f0` |
| Commit timestamp | `2026-11-09T06:12:48-05:00` |

## Public API

- `class ReaderDialogueError(ValueError)` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 146)
- `inquiry_enabled(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 150) — RW1a's kill switch (``reader_inquiry.enabled``, default on).
- `reader_enabled(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 160) — Launch default OFF (§12.3.2): the golden path completes without the reader.
- `reader_prompt_contract(*, branches: bool=False, learner_state: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 173) — The owner-reviewable ``reader`` prompt/manifest contract (design A.2).
- `build_reader_manifest(repository: Repository, *, extraction_id: str, span_id: str, question_md: str, answer_mode: str, goal_invariants: Mapping[str, Any] | None=None, selection_span_ids: Sequence[str]=(), selection_quote_md: str | None=None, prior_exchanges: Sequence[Mapping[str, Any]] | None=None, withheld: Any=None, budget_tokens: int | None=None, resolve_references: bool=True, expanded_delivery: bool=True) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 245) — The exact bounded context handed to the reader tutor (design A.2).
- `set_answer_mode(repository: Repository, *, extraction_id: str, span_id: str, answer_mode: str, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 369) — Log the per-ask answer-mode toggle (``reader_answer_mode_set``).
- `set_mode(repository: Repository, *, mode: str, extraction_id: str | None=None, session_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 392) — Set the reading mode (skim/anchor/incremental, §5.1).
- `question_control(repository: Repository, *, control: str, administration_id: str | None=None, subject_id: str | None=None, subject_type: str='reader_span', clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 421) — Record a per-question control (§5.1).
- `surface_statement_text(surface_row: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 479) — The reserved surface text the reveal floor compares an answer against.
- `lexical_reserve_reveal(answer_md: str, surface_row: Mapping[str, Any], *, citations: Sequence[Mapping[str, Any]]=()) -> tuple[bool, float]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 485) — The lexical reveal floor for one reserved surface: (hit, bigram overlap).
- `ask(vault: LoadedVault, repository: Repository, client: Any, *, extraction_id: str, span_id: str, question_md: str, answer_mode: str=READER_ANSWER_MODE_DEFAULT, target_key: str | None=None, goal_invariants: Mapping[str, Any] | None=None, revealed_surface_ids: Sequence[str]=(), selection_span_ids: Sequence[str]=(), selection_quote_md: str | None=None, parent_exchange_id: str | None=None, selection_source_quote_md: str | None=None, cold_active: bool=False, cold_attempt_id: str | None=None, learning_object_suggester: Any | None=None, tool_request_handler: Any | None=None, source_span_provider: Any | None=None, reader_tutor: Any | None=None, reader_caller: Mapping[str, Any] | None=None, reader_binding: Any | None=None, learner_state: Any | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 537) — Answer a span-grounded reader question (§7.6).
- `ask_history(repository: Repository, *, extraction_id: str, branches: bool=True, tutor_views: bool=False) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 903) — Return every completed Reader Ask for one extraction, newest first.
- `ask_provenance(repository: Repository, *, extraction_id: str) -> dict[str, list[tuple[str, str]]]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 977) — Every ``(reading, span)`` each completed Reader Ask of one extraction names, by its event id.
- `administer_reading_question(vault: LoadedVault, repository: Repository, item: Any, *, reading_phase: str, goal_id: str | None=None, target_contract_version_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 1078) — Render an owner-placed reading question as an instructional administration (§7.6): ``source_visible=true`` + a ``reading_phase``, no new activity kind.
- `skip_reading_question(repository: Repository, *, administration_id: str, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 1148) — A skip is an interaction-policy signal, NEVER low-ability evidence (§7.6).
- `submit_reading_question(repository: Repository, *, administration_id: str, response_md: str | None=None, target_key: str | None=None, outcome_class: str='unknown', clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 1168) — Record an answer to an owner-placed reading question (source_visible instructional; primes/scaffolds, never cold evidence).
- `choose_disposition(vault: LoadedVault, repository: Repository, *, disposition: str, subject_id: str, subject_type: str='reader_span', commitment_target: Mapping[str, Any] | None=None, goal_id: str | None=None, client_idempotency_key: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 1202) — Apply one of the four reading dispositions -- and nothing else (§7.6).
- `restore_source(repository: Repository, *, extraction_id: str, span_id: str, cold_surface_id: str | None=None, cold_administration_id: str | None=None, clock: Clock | None=None, exposure_fields: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 1271) — Restore a source span during reading.
- `routing_prior_projection_v1(repository: Repository, *, target_key: str, as_of: str | None=None, cold_observation_at: str | None=None, halflife_days: float | None=None, max_weight: float | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 1329) — Fold ``reader_answer_submitted`` events for ``target_key`` into a bounded, replay-derived routing prior (design A.1 / spec §7.6 evidence semantics).
- `class StubReaderClient` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 1431) — A deterministic ``reader`` tutor client (U-034 stub).
  - `__init__(self, *, answer_md: str='Grounded in the span in view.') -> None` (line 1439; internal)
  - `supports(self, capability: str) -> bool` (line 1443; public)
  - `complete(self, request: StructuredRequest[Any]) -> TutorAnswer` (line 1446; public)

### Module constants

- `READER_MODES` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 66)
- `READER_QUESTION_CONTROLS` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 71)
- `ROUTING_PRIOR_HALFLIFE_DAYS` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 79)
- `ROUTING_PRIOR_MAX_WEIGHT` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 80)
- `READER_QUESTION_DENSITY_TARGET` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 83)
- `READER_REVEAL_OVERLAP_THRESHOLD` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 88)
- `READER_ANSWER_MODES` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 90)
- `READER_ANSWER_MODE_DEFAULT` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 91)
- `READER_DISPOSITIONS` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 95)
- `READER_EVENT_KINDS` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 103)
- `READING_PHASES` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 114)
- `READER_PROMPT_CONTRACT_VERSION` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 116)
- `READER_BRANCHES_CONTRACT_VERSION` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 120)
- `READER_BRANCH_PROMPT_ANCESTORS` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 123)
- `READER_LEARNER_STATE_CONTRACT_SUFFIX` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 127)
- `READER_MANIFEST_EXCLUDED` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 130)
- `READER_MANIFEST_EXCLUDED_WITH_STATE` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 131)

## Internal implementation anchors

- `_base_prompt_contract(*, branches: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 207)
- `_with_learner_state(manifest: dict[str, Any], learner_state: Any) -> None` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 321) — The manifest of a question whose tutor context carries the learner state (learner-blindness relax): its version suffix, the exclusions that still hold, and what was given (the state's manifest view).
- `_branch_ancestors(repository: Repository, *, extraction_id: str, span_id: str, parent_exchange_id: str | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 335) — Resolve completed exchange IDs in this vault; never trust caller history.
- `_normalize_tokens(text: str) -> list[str]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 450)
- `_bigrams(tokens: Sequence[str]) -> set[tuple[str, str]]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 454)
- `_verbatim_overlap(answer_md: str, statement: str) -> float` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 458) — Cheap word-bigram overlap: the share of a reserved statement's bigrams that appear in the answer (no LLM, L3).
- `_surface_statement_text(surface_row: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 469)
- `_detect_revealed_reserves(repository: Repository, *, answer_md: str, citations: Sequence[Mapping[str, Any]], caller_supplied: Sequence[str]) -> list[str]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 508) — Server-side reveal detection (L3): map the answer's text + validated citations against every LIVE assessment reserve by surface_hash / fingerprint / verbatim overlap (>= ``READER_REVEAL_OVERLAP_THRESHOLD``).
- `_record_cold_hint_equivalent(repository: Repository, *, cold_attempt_id: str, question_md: str, answer_md: str | None, span_key: str, clock: Clock | None, question_event_id: str | None=None, counts: bool=True, question_type: str | None=None) -> str | None` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 1023) — Record the cold reader Ask as a hint-equivalent PRACTICE question_event tied to the cold attempt's (item, session), so the practice evidence path counts it (L6).
- `_days_between(start_iso: str, end_iso: str) -> float` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 1421)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/router_reader|learnloop.daily_plan.router_reader]] — imports `module`; statically calls `ask_history`
- [[Reference/Modules/learnloop/ops/contamination/detectors|learnloop.ops.contamination.detectors]] — imports `lexical_reserve_reveal`, `surface_statement_text`; statically calls `lexical_reserve_reveal`, `surface_statement_text`
- [[Reference/Modules/learnloop/ops/contamination/recipes|learnloop.ops.contamination.recipes]] — imports `surface_statement_text`; statically calls `surface_statement_text`
- [[Reference/Modules/learnloop/reader/phone_media|learnloop.reader.phone_media]] — imports `module`; statically calls `reader_enabled`
- [[Reference/Modules/learnloop/reader/reader_inquiry|learnloop.reader.reader_inquiry]] — imports `module`; statically calls `ask_history`
- [[Reference/Modules/learnloop/reader/reader_observations|learnloop.reader.reader_observations]] — imports `module`; statically calls `ask_history`
- [[Reference/Modules/learnloop/reader/reader_restoration|learnloop.reader.reader_restoration]] — imports `module`; statically calls `restore_source`
- [[Reference/Modules/learnloop/reader/recap|learnloop.reader.recap]] — imports `module`; statically calls `ask_history`
- [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]] — imports `module`; statically calls `reader_enabled`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `module`; statically calls `reader_enabled`
- [[Reference/Modules/learnloop_sidecar/handlers/deliverables|learnloop_sidecar.handlers.deliverables]] — imports `module`; statically calls `reader_enabled`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `module`; statically calls `ask`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `administer_reading_question`, `ask`, `ask_history`, `ask_provenance`, `choose_disposition`, `inquiry_enabled`, `question_control`, `reader_enabled`, `reader_prompt_contract`, `restore_source`, `routing_prior_projection_v1`, `set_answer_mode`, `set_mode`, `skip_reading_question`, `submit_reading_question`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_intent|learnloop_sidecar.handlers.reader_intent]] — imports `module`; statically calls `inquiry_enabled`, `reader_enabled`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_tutor|learnloop_sidecar.handlers.reader_tutor]] — imports `module`; statically calls `ask_history`, `inquiry_enabled`
- [[Reference/Modules/learnloop_sidecar/handlers/reading_paths|learnloop_sidecar.handlers.reading_paths]] — imports `module`; statically calls `reader_enabled`
- [[Reference/Modules/learnloop_sidecar/handlers/recap|learnloop_sidecar.handlers.recap]] — imports `module`; statically calls `inquiry_enabled`, `reader_enabled`
- [[Reference/Modules/learnloop_sidecar/handlers/side_by_side|learnloop_sidecar.handlers.side_by_side]] — imports `module`; statically calls `reader_enabled`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `module`; statically calls `reader_enabled`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `STRUCTURED_COMPLETION`, `StructuredRequest`
- [[Reference/Modules/learnloop/attempts/salience_firewall|learnloop.attempts.salience_firewall]] — imports `salience_payload`; calls `salience_payload`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `held_out_among`, `held_out_material`, `held_out_refusal`; calls `held_out_among`, `held_out_material`, `held_out_refusal`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `create_commitment`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/learner/familiarity|learnloop.learner.familiarity]] — imports `module`; calls `propagate_tutor_exposure`
- [[Reference/Modules/learnloop/reader/span_view|learnloop.reader.span_view]] — imports `SpanViewError`, `build_span_view`; calls `build_span_view`
- [[Reference/Modules/learnloop/serve_eligibility|learnloop.serve_eligibility]] — imports `help_converts_active`; calls `help_converts_active`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `append_exposure`, `log_interaction_event`, `open_administration`, `reserve_surface`, `resolve_legacy_item`; calls `append_exposure`, `log_interaction_event`, `open_administration`, `reserve_surface`, `resolve_legacy_item`
- [[Reference/Modules/learnloop/substrate/administration_adapters|learnloop.substrate.administration_adapters]] — imports `module`; calls `resolve_adapter`
- [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]] — imports `ReaderTutorQAContext`, `TutorAnswer`, `TutorCitation`, `TutorQAContext`; calls `TutorAnswer`, `TutorCitation`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `module`; calls `HeldOutMaterialRefused`, `_reader_source_spans`, `ask_question`, `delivered_answer_md`, `reader_span_key`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/router_reader|learnloop.daily_plan.router_reader]], [[Reference/Modules/learnloop/ops/contamination/detectors|learnloop.ops.contamination.detectors]], [[Reference/Modules/learnloop/ops/contamination/recipes|learnloop.ops.contamination.recipes]], [[Reference/Modules/learnloop/reader/phone_media|learnloop.reader.phone_media]], [[Reference/Modules/learnloop/reader/reader_inquiry|learnloop.reader.reader_inquiry]] and 14 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/recap_fixtures.py](../../../../../../tests/recap_fixtures.py) — direct import
- [tests/test_ad1_fix_round4.py](../../../../../../tests/test_ad1_fix_round4.py) — direct import
  - `test_a_reader_tutor_exchange_is_recorded_under_its_answer_mode`
- [tests/test_ad1_reading_opportunities.py](../../../../../../tests/test_ad1_reading_opportunities.py) — direct import
  - `test_reading_opportunities_frozen_and_ordered_by_source_time`
- [tests/test_exam_protection.py](../../../../../../tests/test_exam_protection.py) — direct import
  - `test_a_reader_question_about_held_out_material_is_refused_before_anything_is_sent`
- [tests/test_learner_blindness_relax.py](../../../../../../tests/test_learner_blindness_relax.py) — direct import
  - `test_the_prompt_contract_names_the_learner_state_only_while_on`
- [tests/test_library_ask_review.py](../../../../../../tests/test_library_ask_review.py) — direct import
  - `test_pinned_passages_are_held_to_the_tutors_context_budget`
  - `test_the_pinned_tutor_burns_a_reserve_it_reproduces_and_joins_history_and_gaps`
- [tests/test_mobile_v4_codex_review.py](../../../../../../tests/test_mobile_v4_codex_review.py) — direct import
  - `test_f4_reopened_a_fresh_answer_is_judged_on_what_it_stored_before_the_phone_is_sent_it`
- [tests/test_p3_journeys.py](../../../../../../tests/test_p3_journeys.py) — direct import
  - `test_journey1_reading_first_session`
  - `test_journey7_tutor_exchange_to_durable`
- [tests/test_plan_first_transport.py](../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_fix_l1_the_rpc_gates_of_priced_features_offer_and_honour_no_grant_their_job_would_refuse`
- [tests/test_reader_activity.py](../../../../../../tests/test_reader_activity.py) — direct import
  - `test_every_server_event_is_salience_only_and_never_evidence`
- [tests/test_reader_branches.py](../../../../../../tests/test_reader_branches.py) — direct import
  - `test_an_edited_capture_keeps_the_sources_wording_apart_from_the_learners`
  - `test_branch_keeps_citation_allowlist_and_evidence_isolation`
  - `test_branch_rpc_roundtrip_uses_parent_id_and_persists_on_reinitialize`
  - `test_branches_restore_after_restart_and_inherit_selection_without_siblings`
  - `test_branches_work_on_a_transcript_and_on_text_notes`
  - `test_deep_branch_bounds_prompt_history_without_losing_saved_links`
  - `test_failed_followup_does_not_become_a_branch_or_pollute_retry`
  - `test_followup_refuses_an_unresolvable_source_anchor`
  - `test_invalid_parents_fail_before_model_call_or_event_write`
  - `test_legacy_flat_exchange_remains_root_and_can_be_followed`
  - `test_with_the_switch_off_an_edited_capture_changes_nothing`
- [tests/test_reader_dialogue.py](../../../../../../tests/test_reader_dialogue.py) — direct import
  - `test_answer_not_quoting_reserve_leaves_it_eligible`
  - `test_answer_quoting_reserved_surface_burns_it_without_caller_id`
  - `test_ask_answers_logs_new_kinds_and_persists_the_exchange`
  - `test_ask_is_never_ability_evidence`
  - `test_ask_warms_and_invalidates_a_revealed_reserve`
  - `test_cold_active_ask_links_a_hint_equivalent_into_attempt_accounting`
  - `test_each_disposition_produces_its_mechanism_and_nothing_else`
  - `test_golden_path_completes_with_reader_never_invoked`
  - `test_manifest_carries_full_multiblock_selection`
  - `test_manifest_carries_span_and_mode_but_never_ability_or_reserved`
  - `test_owner_placed_question_is_instructional_source_visible_reading_phase`
  - `test_prompt_contract_is_deterministic_and_walls_off_ability`
  - `test_reader_answer_writes_no_posterior_or_fsrs`
  - `test_real_reader_writes_carry_the_salience_firewall_stamp`
  - `test_restore_source_during_cold_burns_eligibility`
  - `test_routing_prior_decays_with_elapsed_time`
  - `test_routing_prior_is_heuristic_decision_aid`
  - `test_routing_prior_superseded_by_cold_observation_before_the_reading_answer`
  - `test_routing_prior_superseded_by_first_cold_observation`
  - `test_skip_is_interaction_policy_not_low_ability`
- [tests/test_reader_guidance.py](../../../../../../tests/test_reader_guidance.py) — direct import
  - `test_dont_bring_this_back_suppresses_the_exact_reviewed_placement`
- [tests/test_reader_inquiry_kill_switch.py](../../../../../../tests/test_reader_inquiry_kill_switch.py) — direct import
  - `test_history_on_carries_status_and_selection_for_each_exchange`
  - `test_rpcs_off_answer_exactly_as_before`
  - `test_rpcs_on_add_only_the_branch_fields`
  - `test_service_off_is_the_flat_same_span_thread`
  - `test_service_off_refuses_a_parent_before_any_write`
- [tests/test_reader_inquiry_status.py](../../../../../../tests/test_reader_inquiry_status.py) — direct import
  - `test_status_lives_on_the_root_question_and_reopen_is_accepted`
  - `test_status_rpc_and_its_kill_switch`
- [tests/test_reader_intent.py](../../../../../../tests/test_reader_intent.py) — direct import
- [tests/test_reader_passage_check.py](../../../../../../tests/test_reader_passage_check.py) — direct import
- [tests/test_reader_reconnect.py](../../../../../../tests/test_reader_reconnect.py) — direct import
  - `test_a_landed_inquiry_check_names_its_model_and_prompt_version`
  - `test_inquiry_question_action_rpc_records_the_self_check`
  - `test_reconnect_rpcs_round_trip`
  - `test_the_quick_check_read_reports_its_durable_jobs_state`
- [tests/test_reader_report.py](../../../../../../tests/test_reader_report.py) — direct import
  - `test_the_passage_quick_check_is_a_model_backed_action_in_the_funnel`
  - `test_transcript_inquiries_count_like_any_other`
- [tests/test_reader_rw1c_review.py](../../../../../../tests/test_reader_rw1c_review.py) — direct import
  - `test_switching_both_off_restores_the_base_history_projection`
- [tests/test_reader_source_identity_guard.py](../../../../../../tests/test_reader_source_identity_guard.py) — direct import
- [tests/test_reading_paths.py](../../../../../../tests/test_reading_paths.py) — direct import
- [tests/test_sidecar_serializer_snapshot.py](../../../../../../tests/test_sidecar_serializer_snapshot.py) — direct import
  - `test_queue_practice_and_reader_wire_snapshots`
- [tests/test_tutor_delivery_fixes.py](../../../../../../tests/test_tutor_delivery_fixes.py) — direct import
  - `test_the_reader_manifest_records_what_the_tutor_was_given`
- [tests/test_ux_phase1_landing.py](../../../../../../tests/test_ux_phase1_landing.py) — direct import
  - `test_a_book_with_the_retired_keep_local_gets_its_passage_check_when_asked`

## Modification guidance

- Change reader dialogue policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
