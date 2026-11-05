---
title: "learnloop.diagnosis.remediation"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/remediation.py"
source_paths:
  - "src/learnloop/diagnosis/remediation.py"
source_commit: "workspace/uncommitted @ HEAD 4a801f1afce0faaf0246a9bd404a8ed73abf2dfb"
source_commit_timestamp: "2026-11-04T19:32:38-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.remediation module"
  - "src/learnloop/diagnosis/remediation.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.remediation`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.remediation` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Durable misconception-repair episode lifecycle and cold retries.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/remediation.py](../../../../../../src/learnloop/diagnosis/remediation.py) |
| Source lines | 1484 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 4a801f1afce0faaf0246a9bd404a8ed73abf2dfb` |
| Commit timestamp | `2026-11-04T19:32:38-05:00` |

## Public API

- `class RemediationError(ValueError)` ([source](../../../../../../src/learnloop/diagnosis/remediation.py), line 59)
- `class RemediationBlocked(RemediationError)` ([source](../../../../../../src/learnloop/diagnosis/remediation.py), line 63) — A repair that the causal state holds back, with its typed status.
  - `__init__(self, status: Any) -> None` (line 71; internal)
  - `status(self) -> str` (line 76; public)
- `open_episode_for_practice_item(repository: Repository, practice_item_id: str | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/remediation.py), line 80) — The live repair episode a reveal on ``practice_item_id`` belongs to.
- `episode_reveal_spend(repository: Repository, episode_id: str | None) -> float` ([source](../../../../../../src/learnloop/diagnosis/remediation.py), line 109) — How much answer this repair episode has already handed over (0..1+).
- `start_remediation_episode(repository: Repository, misconception_id: str, *, vault: LoadedVault | None=None, session_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/remediation.py), line 131) — Start the repair episode, or raise the typed causal hold.
- `episode_case(repository: Repository, episode: dict[str, Any]) -> Any | None` ([source](../../../../../../src/learnloop/diagnosis/remediation.py), line 168)
- `case_value(case: Any, key: str, default: Any=None) -> Any` ([source](../../../../../../src/learnloop/diagnosis/remediation.py), line 174)
- `prescribe_remediation(vault: LoadedVault, repository: Repository, episode_id: str, *, clock: Clock | None=None, passage_provider: Any | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/remediation.py), line 180) — Prescribe the passages a repair overlay shows.
- `record_prescription_delivery(repository: Repository, episode: Mapping[str, Any], *, clock: Clock | None=None, exposure_fields: Mapping[str, Any] | None=None) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/remediation.py), line 282) — Record that this episode's prescribed passages were delivered for render.
- `item_step_checkpoint_ids(target_refs) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/diagnosis/remediation.py), line 352)
- `item_checkpoints(item: Any) -> set[str]` ([source](../../../../../../src/learnloop/diagnosis/remediation.py), line 426)
- `start_remediation_treatment(vault: LoadedVault, repository: Repository, episode_id: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/remediation.py), line 526)
- `record_remediation_attempt(repository: Repository, attempt: dict[str, Any], *, clock: Clock | None=None, vault: LoadedVault | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/remediation.py), line 819) — Link treatment attempts and consume delayed tasks exactly once.
- `reschedule_cold_after_assist_active(vault: Any) -> bool` ([source](../../../../../../src/learnloop/diagnosis/remediation.py), line 1113) — The cold-retry reschedule (``COLD_RETRY_RESCHEDULE_ALGORITHM_VERSION``, ``mvp-0.38``): at that tag or later with ``practice.reschedule_cold_after_assist`` on, and with Reader CA2's rule on (``serve_eligibility.help_converts_active``: without it submit refuses an assisted attempt…
- `reschedule_assisted_cold_retry(vault: LoadedVault | None, repository: Repository, attempt: Mapping[str, Any], *, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/remediation.py), line 1137) — Help taken on a due repair cold retry: end it and schedule ONE fresh cold retry for the same repair (owner decision 2026-10-25, Reader CA2 follow-up Q4; ``mvp-0.38``).
- `assisted_attempt(attempt: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/diagnosis/remediation.py), line 1349) — Did the attempt take help (hints, a hinted type) or see its answer (primed)?
- `withdraw_cold_measurement(vault: LoadedVault | None, repository: Repository, task_id: str, *, reason: str, reveal_event_ids: tuple[str, ...] | list[str]=(), decision: Mapping[str, Any] | None=None, stage: str='serve', clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/remediation.py), line 1370) — Withdraw an open cold measurement its selected surface can no longer give a cold reading (the one eligibility decision, ``mvp-0.27``; Codex review F2): the item's answer was shown with no lapse (submit primes it until an attempt, and an attempt on it is a hard exposure of the co…
- `misconception_status_history(repository: Repository, misconception_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/remediation.py), line 1477)

### Module constants

- `REPAIR_COLD_OPPORTUNITY_POLICY_VERSION` ([src/learnloop/diagnosis/remediation.py](../../../../../../src/learnloop/diagnosis/remediation.py), line 20)
- `COLD_RETRIEVAL_DELAY` ([src/learnloop/diagnosis/remediation.py](../../../../../../src/learnloop/diagnosis/remediation.py), line 31)
- `COLD_RETRY_WINDOW` ([src/learnloop/diagnosis/remediation.py](../../../../../../src/learnloop/diagnosis/remediation.py), line 37)
- `EPISODE_REVEAL_BUDGET` ([src/learnloop/diagnosis/remediation.py](../../../../../../src/learnloop/diagnosis/remediation.py), line 56)
- `REMEDIATION_DELIVERY_CONTEXT` ([src/learnloop/diagnosis/remediation.py](../../../../../../src/learnloop/diagnosis/remediation.py), line 274)
- `REMEDIATION_DELIVERY_ENTITY_TYPE` ([src/learnloop/diagnosis/remediation.py](../../../../../../src/learnloop/diagnosis/remediation.py), line 279)
- `RECENT_ATTEMPT_WINDOW` ([src/learnloop/diagnosis/remediation.py](../../../../../../src/learnloop/diagnosis/remediation.py), line 349)
- `ASSISTED_RESCHEDULE_CONTEXT_KEY` ([src/learnloop/diagnosis/remediation.py](../../../../../../src/learnloop/diagnosis/remediation.py), line 1105)
- `ASSISTED_RESCHEDULE_TRIGGER` ([src/learnloop/diagnosis/remediation.py](../../../../../../src/learnloop/diagnosis/remediation.py), line 1110)
- `WITHDRAWN_COLD_RETRY_OUTCOME` ([src/learnloop/diagnosis/remediation.py](../../../../../../src/learnloop/diagnosis/remediation.py), line 1367)

## Internal implementation anchors

- `_case_target_checkpoint_ids(repository: Repository, misconception, *, case_kind: str='misconception', case_ref: str | None=None) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/diagnosis/remediation.py), line 364) — The checkpoint ids the case's selected repair class targets, if known.
- `_rank_items(vault: LoadedVault, repository: Repository, misconception, *, target_checkpoint_ids: tuple[str, ...]=(), clock: Clock | None=None) -> tuple[list[Any], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/diagnosis/remediation.py), line 437) — The repair's candidate items best-first, plus the servability skips.
- `_independent_cold_item(vault: LoadedVault, repository: Repository, candidates: list[Any], *, excluded_surfaces: set[str | None]) -> Any | None` ([source](../../../../../../src/learnloop/diagnosis/remediation.py), line 671) — The best-ranked candidate on a surface group outside ``excluded_surfaces`` whose own material the learner was not shown (exam protection: ``exposed_items`` with held-out material), or None.
- `_independent_cold_candidates(vault: LoadedVault, repository: Repository, candidates: list[Any], *, excluded_surfaces: set[str | None]) -> list[Any]` ([source](../../../../../../src/learnloop/diagnosis/remediation.py), line 692) — Every candidate :func:`_independent_cold_item` accepts, in rank order.
- `_record_unbound_primed_disposition(repository: Repository, attempt: dict[str, Any], *, vault: LoadedVault | None=None, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/remediation.py), line 708) — Typed §4.3 disposition for a primed repair attempt with NO episode.
- `_repair_forecast(vault: LoadedVault | None, repository: Repository, attempt: Mapping[str, Any], *, repair_class_id: str | None, hypothesis_ids: list[str] | tuple[str, ...]=(), episode: Mapping[str, Any] | None=None, task: Mapping[str, Any] | None=None, censor_reason: str | None=None, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/remediation.py), line 792) — Saved diagnosis forecasts: the repair's predicted cold outcome, in the primed attempt's transaction (bound to its cold task, or censored at birth with the reason none was scheduled).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `record_remediation_attempt`; statically calls `record_remediation_attempt`
- [[Reference/Modules/learnloop/attempts/coldness_receipt|learnloop.attempts.coldness_receipt]] — imports `REMEDIATION_DELIVERY_CONTEXT`, `REMEDIATION_DELIVERY_ENTITY_TYPE`
- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `open_episode_for_practice_item`; statically calls `open_episode_for_practice_item`
- [[Reference/Modules/learnloop/daily_plan/slot_facts|learnloop.daily_plan.slot_facts]] — imports `COLD_RETRIEVAL_DELAY`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `EPISODE_REVEAL_BUDGET`, `episode_reveal_spend`; statically calls `episode_reveal_spend`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `COLD_RETRIEVAL_DELAY`
- [[Reference/Modules/learnloop/diagnosis/guided_redo|learnloop.diagnosis.guided_redo]] — imports `RemediationError`, `_rank_items`, `episode_case`, `start_remediation_episode`; statically calls `_rank_items`, `episode_case`, `start_remediation_episode`
- [[Reference/Modules/learnloop/diagnosis/quick_check|learnloop.diagnosis.quick_check]] — imports `COLD_RETRIEVAL_DELAY`
- [[Reference/Modules/learnloop/instructional/exposure|learnloop.instructional.exposure]] — imports `COLD_RETRIEVAL_DELAY`
- [[Reference/Modules/learnloop/learner/learner_review_feed|learnloop.learner.learner_review_feed]] — imports `misconception_status_history`; statically calls `misconception_status_history`
- [[Reference/Modules/learnloop/practice_index/admission|learnloop.practice_index.admission]] — imports `COLD_RETRIEVAL_DELAY`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `COLD_RETRIEVAL_DELAY`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `COLD_RETRIEVAL_DELAY`, `withdraw_cold_measurement`; statically calls `withdraw_cold_measurement`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `RECENT_ATTEMPT_WINDOW`, `item_checkpoints`; statically calls `item_checkpoints`
- [[Reference/Modules/learnloop_sidecar/handlers/remediation|learnloop_sidecar.handlers.remediation]] — imports `RemediationBlocked`, `RemediationError`, `case_value`, `episode_case`, `misconception_status_history`, `prescribe_remediation`, `record_prescription_delivery`, `start_remediation_episode`, `start_remediation_treatment`; statically calls `case_value`, `episode_case`, `misconception_status_history`, `prescribe_remediation`, `record_prescription_delivery`, `start_remediation_episode`, `start_remediation_treatment`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `COLD_RETRY_RESCHEDULE_VERSIONS`
- [[Reference/Modules/learnloop/attempts/coldness_receipt|learnloop.attempts.coldness_receipt]] — imports `LANE_REPAIR_COLD_RETRY`, `evaluate_final_coldness`, `record_final_receipt`, `record_schedule_refusal_receipt`, `repair_surface_hard_contamination`; calls `evaluate_final_coldness`, `record_final_receipt`, `record_schedule_refusal_receipt`, `repair_surface_hard_contamination`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`; calls `SystemClock`, `parse_utc`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `exam_material`, `exposed_items`; calls `exam_material`, `exposed_items`
- [[Reference/Modules/learnloop/content/sources/provenance|learnloop.content.sources.provenance]] — imports `get_entity_provenance`; calls `get_entity_provenance`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `CausalRepairError`, `causal_repair_status`, `cold_verification_context`; calls `causal_repair_status`, `cold_verification_context`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `record_causal_cold_outcome`; calls `record_causal_cold_outcome`
- [[Reference/Modules/learnloop/diagnosis/forecast_receipts|learnloop.diagnosis.forecast_receipts]] — imports `record_repair_expectation`; calls `record_repair_expectation`
- [[Reference/Modules/learnloop/diagnosis/guided_redo|learnloop.diagnosis.guided_redo]] — imports `diagnosis_receipt`, `selected_repair`; calls `diagnosis_receipt`, `selected_repair`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `parse_block_span`; calls `parse_block_span`
- [[Reference/Modules/learnloop/reader/span_view|learnloop.reader.span_view]] — imports `SpanViewError`, `build_span_view`; calls `build_span_view`
- [[Reference/Modules/learnloop/serve_eligibility|learnloop.serve_eligibility]] — imports `COLD_CHECK_HELP_TAKEN`, `module`; calls `help_converts_active`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `surface_group_id`; calls `surface_group_id`
- [[Reference/Modules/learnloop/substrate/instrument_serving|learnloop.substrate.instrument_serving]] — imports `unservable_refusal`; calls `unservable_refusal`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/coldness_receipt|learnloop.attempts.coldness_receipt]], [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]], [[Reference/Modules/learnloop/daily_plan/slot_facts|learnloop.daily_plan.slot_facts]], [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] and 10 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_attribution_p0.py](../../../../../../tests/test_causal_attribution_p0.py) — direct import
  - `test_provisional_belief_can_open_remediation`
- [tests/test_causal_attribution_p2.py](../../../../../../tests/test_causal_attribution_p2.py) — direct import
  - `test_repair_class_divergence_locks_existing_hypothesis_set_with_other`
- [tests/test_causal_cold_outcomes.py](../../../../../../tests/test_causal_cold_outcomes.py) — direct import
- [tests/test_causal_factor_deferral.py](../../../../../../tests/test_causal_factor_deferral.py) — direct import
  - `test_diagnosis_case_ranks_checkpoint_covering_item_first`
  - `test_diagnosis_case_without_repair_class_falls_back_to_facets`
- [tests/test_causal_orchestrator.py](../../../../../../tests/test_causal_orchestrator.py) — direct import
  - `test_cold_verification_is_carried_through_the_followup_task`
  - `test_unmapped_hypothesis_defers_the_repair_behind_a_machine_check`
- [tests/test_causal_p2_acceptance.py](../../../../../../tests/test_causal_p2_acceptance.py) — direct import
  - `test_causal_disambiguation_end_to_end_acceptance`
- [tests/test_cold_retry_reschedule.py](../../../../../../tests/test_cold_retry_reschedule.py) — direct import
  - `test_a_shadow_rebuild_is_zero_with_the_fresh_retries_present`
  - `test_help_on_a_due_cold_retry_schedules_one_fresh_retry_on_another_surface`
  - `test_help_on_the_fresh_retry_too_ends_it_and_spawns_nothing`
  - `test_the_fresh_retry_is_invisible_until_due_then_measures_the_repair_cold`
  - `test_the_fresh_retry_records_its_own_repair_forecast_which_resolves_when_it_is_measured`
  - `test_the_gate_is_the_tag_its_switch_and_ca2s_rule`
- [tests/test_coldness_receipt.py](../../../../../../tests/test_coldness_receipt.py) — direct import
  - `test_delivered_passage_on_the_cold_items_own_source_span_is_hard`
  - `test_delivered_passages_in_interval_are_typed_exposure_not_indeterminate`
  - `test_delivery_outside_the_interval_is_observed_silence_not_indeterminate`
  - `test_min_cold_delay_mirrors_the_lane_scheduling_constant`
  - `test_prescribe_handler_records_the_delivery`
  - `test_unrelated_remediation_is_counted_but_does_not_change_coldness`
- [tests/test_curriculum_c0b_landing.py](../../../../../../tests/test_curriculum_c0b_landing.py) — direct import
  - `test_iii_check_once_commitments_are_never_touched_by_the_cold_retry_reschedule`
- [tests/test_exam_protection.py](../../../../../../tests/test_exam_protection.py) — direct import
  - `test_a_repair_never_teaches_from_an_exam_passage`
  - `test_a_revealed_item_is_never_the_cold_retry`
- [tests/test_exam_protection_review.py](../../../../../../tests/test_exam_protection_review.py) — direct import
  - `test_with_the_switch_off_the_cold_retry_is_the_predecessor_s`
- [tests/test_forecast_receipts.py](../../../../../../tests/test_forecast_receipts.py) — direct import
  - `test_replay_neither_reads_nor_writes_forecast_receipts`
- [tests/test_guided_redo.py](../../../../../../tests/test_guided_redo.py) — direct import
  - `test_guided_redo_binds_open_episode_and_closes_the_funnel`
  - `test_guided_redo_never_steals_a_sibling_committed_episode`
  - `test_guided_redo_reports_case_unresolvable`
  - `test_rank_items_deprioritizes_recently_attempted_item`
  - `test_rank_items_prefers_checkpoint_covering_item`
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — direct import
  - `test_a_repair_whose_only_items_are_instruments_now_prescribes_one`
  - `test_remediation_treatment_skips_nothing_for_servability`
- [tests/test_misconception_transitions_intake.py](../../../../../../tests/test_misconception_transitions_intake.py) — direct import
  - `test_reactivation_wipes_resolved_at_but_returned_stays_derivable`
- [tests/test_pfc_unassessed_readers.py](../../../../../../tests/test_pfc_unassessed_readers.py) — direct import
  - `test_a_cold_retry_with_nothing_assessed_neither_confirms_nor_fails_the_repair`
- [tests/test_prescription_passages.py](../../../../../../tests/test_prescription_passages.py) — direct import
  - `test_ranked_and_verified_passages_replace_the_first_linked_span`
  - `test_switch_off_keeps_todays_prescription_byte_identical`
  - `test_verification_unavailable_falls_back_byte_identically`
- [tests/test_probe_remint.py](../../../../../../tests/test_probe_remint.py) — direct import
  - `test_remediation_cold_pick_rejects_remint_as_same_surface_as_probe_group`
- [tests/test_reader_ca2_one_ask.py](../../../../../../tests/test_reader_ca2_one_ask.py) — direct import
  - `test_an_assisted_attempt_is_recognised`
- [tests/test_reader_rw6b_landing.py](../../../../../../tests/test_reader_rw6b_landing.py) — direct import
- [tests/test_remediation_cold_retry.py](../../../../../../tests/test_remediation_cold_retry.py) — direct import
  - `test_an_episode_within_budget_says_so`
  - `test_misconception_cold_context_carries_repair_class_from_fresh_receipt`
  - `test_over_budget_episode_stamps_the_fact_on_the_cold_context`
  - `test_repair_status_reports_episode_reveal_spend_against_the_budget`
  - `test_starting_the_same_repair_twice_reuses_one_episode`
- [tests/test_reveal_ledger.py](../../../../../../tests/test_reveal_ledger.py) — direct import
- [tests/test_serve_eligibility.py](../../../../../../tests/test_serve_eligibility.py) — direct import
  - `test_the_cold_delay_is_the_remediation_delay_and_the_constants_are_one`
- [tests/test_serve_eligibility_review.py](../../../../../../tests/test_serve_eligibility_review.py) — direct import
  - `test_f5_a_withdrawal_racing_a_consume_leaves_the_consume_time_disposition_free`
- [tests/test_sidecar_remediation_surfaces.py](../../../../../../tests/test_sidecar_remediation_surfaces.py) — direct import
  - `test_the_primed_repair_attempt_gets_no_cold_check_result`
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_f1_the_routine_display_horizon_is_the_cold_retrieval_delay`

## Modification guidance

- Change remediation policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/remediation.py](../../../../../../src/learnloop/diagnosis/remediation.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
