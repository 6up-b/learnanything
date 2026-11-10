---
title: "learnloop.placement.decisions"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/placement/decisions.py"
source_paths:
  - "src/learnloop/placement/decisions.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.placement"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.placement.decisions module"
  - "src/learnloop/placement/decisions.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-placement"
---

# `learnloop.placement.decisions`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.placement.decisions` exists within [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] to own the behavior summarized by its module contract: Assumed-known decisions (learner field §5.2): receipts, never evidence.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/placement/decisions.py](../../../../../../src/learnloop/placement/decisions.py) |
| Source lines | 753 |
| Owning package | [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class PlacementInactive(RuntimeError)` ([source](../../../../../../src/learnloop/placement/decisions.py), line 73) — Placement is off (pre-mvp-0.11 vault or ``placement.enabled = false``).
- `record_self_report(vault: LoadedVault, repository: Repository, *, learning_object_ids: Iterable[str], report: str, trigger_ref: str | None=None, checkpoint: tuple[str, str] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/placement/decisions.py), line 198) — "I know this" / "too easy" (assume known) or "I don't know this" (return).
- `fast_track_inputs(answers: Sequence[AnswerFacts], blocking: Sequence[str], *, min_correct: int, q: float, known: float) -> dict[str, Any]` ([source](../../../../../../src/learnloop/placement/decisions.py), line 310)
- `reconcile_fast_track(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/placement/decisions.py), line 322) — Mark LOs assumed whose first answers pass the fast-track rule.
- `reconcile_predictor_assumptions(vault: LoadedVault, repository: Repository, predictor: LearnerPredictor, *, clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/placement/decisions.py), line 443) — The ``predictor`` source: confident before any attempt.
- `quick_check_split(vault: LoadedVault, predictor: LearnerPredictor, *, scope: Sequence[str], answers_by_lo: Mapping[str, Sequence[AnswerFacts]], blocking: Mapping[str, Sequence[str]], state: PlacementState) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/placement/decisions.py), line 492) — Per-LO quick-check verdict: ``assumed``, ``learning`` or ``undecided``.
- `quick_check_window_end(calibration: ProbeCalibrationSessionRecord) -> str` ([source](../../../../../../src/learnloop/placement/decisions.py), line 534) — The check's boundary: its budget's end, or its stop/expiry if earlier.
- `quick_check_presentations(connection: Any, calibration_session_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/placement/decisions.py), line 546)
- `bind_quick_check_answers(connection: Any, record: Mapping[str, Any], *, window_end: str) -> int` ([source](../../../../../../src/learnloop/placement/decisions.py), line 555) — Associate each presentation with its submission, once.
- `quick_check_answers(connection: Any, *, calibration_session_id: str, scope: Sequence[str]) -> dict[str, tuple[AnswerFacts, ...]]` ([source](../../../../../../src/learnloop/placement/decisions.py), line 584) — The check's own answers: the submissions bound to its presentations, with their independence facts (the same window as fast-track's).
- `quick_check_record(repository: Repository, calibration_session_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/placement/decisions.py), line 620)
- `finish_quick_check_split(vault: LoadedVault, repository: Repository, *, calibration_session_id: str, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/placement/decisions.py), line 625) — Feed a finished quick check's results into the assumed/learning split.
- `finalize_stale_quick_checks(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/placement/decisions.py), line 721) — Feed the results of quick checks that ended while nobody was looking.

### Module constants

- `SELF_REPORTS` ([src/learnloop/placement/decisions.py](../../../../../../src/learnloop/placement/decisions.py), line 66)
- `RETURN_REPORTS` ([src/learnloop/placement/decisions.py](../../../../../../src/learnloop/placement/decisions.py), line 67)
- `PLACEMENT_OVERRIDE_TASK` ([src/learnloop/placement/decisions.py](../../../../../../src/learnloop/placement/decisions.py), line 69)
- `PLACEMENT_OVERRIDE_VERSION` ([src/learnloop/placement/decisions.py](../../../../../../src/learnloop/placement/decisions.py), line 70)

## Internal implementation anchors

- `_config(vault: LoadedVault) -> dict[str, Any]` ([source](../../../../../../src/learnloop/placement/decisions.py), line 77)
- `_due(now_iso: str, days: int) -> str` ([source](../../../../../../src/learnloop/placement/decisions.py), line 85)
- `_region_dict(region: RegionEstimate | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/placement/decisions.py), line 91)
- `_decision_row(vault: LoadedVault, predictor: LearnerPredictor, *, learning_object_id: str, source: str, trigger_kind: str, trigger_ref: str | None, region: RegionEstimate | None, inputs: Mapping[str, Any], now_iso: str, quick_check_session_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/placement/decisions.py), line 97)
- `_open_assumption_id(connection: Any, vault: LoadedVault, learning_object_id: str, *, now_iso: str) -> str | None` ([source](../../../../../../src/learnloop/placement/decisions.py), line 134)
- `_latest_override_id(connection: Any, learning_object_id: str) -> str | None` ([source](../../../../../../src/learnloop/placement/decisions.py), line 142)
- `_append_override(connection: Any, vault: LoadedVault, *, learning_object_id: str, report: str, status: str, trigger_ref: str | None, receipt_table: str | None, receipt_id: str | None, now_iso: str) -> str` ([source](../../../../../../src/learnloop/placement/decisions.py), line 151) — The learner's placement verdict as an owner judgment (Slice A §3 rule 3).
- `_quick_check_scopes(connection: Any) -> set[str]` ([source](../../../../../../src/learnloop/placement/decisions.py), line 300)
- `_fast_track_receipt(vault: LoadedVault, connection: Any, lo: str, answers: Sequence[AnswerFacts], region: RegionEstimate | None, verdict: Any, *, now_iso: str, blocking: Sequence[str], predecessor_blocking: Sequence[str]) -> None` ([source](../../../../../../src/learnloop/placement/decisions.py), line 414) — RW2d: the old rule's verdict on the predecessor's blocking signals, beside this one's.
- `_bind_finished_window(repository: Repository, record: Mapping[str, Any]) -> None` ([source](../../../../../../src/learnloop/placement/decisions.py), line 601)
- `_quick_check_record(connection: Any, calibration_session_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/placement/decisions.py), line 610)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/item_authoring|learnloop.content.authoring.item_authoring]] — imports `record_self_report`; statically calls `record_self_report`
- [[Reference/Modules/learnloop/diagnosis/quick_check|learnloop.diagnosis.quick_check]] — imports `bind_quick_check_answers`, `finish_quick_check_split`, `quick_check_answers`, `quick_check_presentations`, `quick_check_record`, `quick_check_split`, `quick_check_window_end`; statically calls `bind_quick_check_answers`, `finish_quick_check_split`, `quick_check_answers`, `quick_check_presentations`, `quick_check_record`, `quick_check_split`, `quick_check_window_end`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `reconcile_fast_track`; statically calls `reconcile_fast_track`
- [[Reference/Modules/learnloop_sidecar/handlers/placement|learnloop_sidecar.handlers.placement]] — imports `PlacementInactive`, `record_self_report`; statically calls `record_self_report`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `ProbeCalibrationSessionRecord`, `Repository`
- [[Reference/Modules/learnloop/db/stores/field_signal_receipts|learnloop.db.stores.field_signal_receipts]] — imports `module`; calls `insert_receipt`, `table_present`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/db/stores/placement|learnloop.db.stores.placement]] — imports `bind_quick_check_item`, `finish_quick_check`, `insert_assumption_decision`, `insert_assumption_return`; calls `bind_quick_check_item`, `finish_quick_check`, `insert_assumption_decision`, `insert_assumption_return`
- [[Reference/Modules/learnloop/field/types|learnloop.field.types]] — imports `LearnerPredictor`, `RegionEstimate`; calls `RegionEstimate`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/placement/field_receipts|learnloop.placement.field_receipts]] — imports `fast_track_side`, `receipt_row`; calls `fast_track_side`, `receipt_row`
- [[Reference/Modules/learnloop/placement/predictor|learnloop.placement.predictor]] — imports `active_predictor`; calls `active_predictor`
- [[Reference/Modules/learnloop/placement/rules|learnloop.placement.rules]] — imports `AnswerFacts`, `RULES_VERSION`, `fast_track_verdict`, `interval_80`, `known_probability`, `theta_known`; calls `fast_track_verdict`, `interval_80`, `known_probability`, `theta_known`
- [[Reference/Modules/learnloop/placement/signals|learnloop.placement.signals]] — imports `blocking_with_predecessor`; calls `blocking_with_predecessor`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `INTENT_MAINTENANCE`, `PlacementState`, `diagnosis_can_arrive`, `evaluate_independence`, `load_answers`, `load_placement_state_from_connection`, `placement_active`; calls `diagnosis_can_arrive`, `evaluate_independence`, `load_answers`, `load_placement_state_from_connection`, `placement_active`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/item_authoring|learnloop.content.authoring.item_authoring]], [[Reference/Modules/learnloop/diagnosis/quick_check|learnloop.diagnosis.quick_check]], [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]], [[Reference/Modules/learnloop_sidecar/handlers/placement|learnloop_sidecar.handlers.placement]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_assumed_known.py](../../../../../../tests/test_assumed_known.py) — direct import
  - `test_a_failed_ledger_append_rolls_back_the_receipt`
  - `test_a_final_receipt_that_does_not_qualify_as_cold_retrieval_cannot_pass_the_check`
  - `test_a_passed_check_keeps_the_remaining_learning_items_withheld`
  - `test_a_post_reveal_answer_cannot_pass_the_check`
  - `test_a_post_reveal_answer_never_counts_toward_fast_track`
  - `test_a_qualified_final_receipt_still_lets_the_check_pass`
  - `test_a_return_in_the_same_second_as_i_know_this_still_returns_the_lo`
  - `test_an_early_miss_still_returns_the_lo_to_learning`
  - `test_answers_in_the_same_second_as_a_decision_or_return_keep_their_order`
  - `test_check_item_choice_is_deterministic`
  - `test_failed_first_review_quietly_returns_the_lo_to_learning`
  - `test_fast_track_blocked_by_any_unclean_first_answer`
  - `test_fast_track_check_waits_for_its_review_interval`
  - `test_fast_track_default_threshold_is_not_met_by_two_answers`
  - `test_fast_track_needs_min_clean_answers_and_the_threshold`
  - `test_fast_track_receipt_recomputes_its_decision`
  - `test_i_dont_know_this_after_a_pass_returns_the_lo_to_learning`
  - `test_i_dont_know_this_on_a_practised_unassumed_lo_admits_its_new_items`
  - `test_i_dont_know_this_returns_an_assumed_lo_to_learning_immediately`
  - `test_i_know_this_in_the_same_second_as_a_return_supersedes_it`
  - `test_kill_switch_ignores_assumptions_made_while_on`
  - `test_learner_placement_verdicts_append_to_the_judgment_ledger`
  - `test_passed_first_review_keeps_the_lo_in_maintenance`
  - `test_placement_receipts_survive_rebuild_with_zero_model_calls`
  - `test_predictor_assumption_is_impossible_under_the_incumbent`
  - `test_self_report_is_idempotent_while_open_and_refused_when_placement_is_off`
  - `test_self_report_marks_assumed_withholds_new_items_and_schedules_the_check`
  - `test_the_check_item_skips_a_reserved_cold_check`
- [tests/test_daily_plan_composition.py](../../../../../../tests/test_daily_plan_composition.py) — direct import
  - `test_a_check_miss_awaiting_its_diagnosis_stays_assumed_and_is_not_rechecked`
- [tests/test_field_workbench_signals.py](../../../../../../tests/test_field_workbench_signals.py) — direct import
  - `test_a_stuck_step_or_early_help_never_lowers_the_record`
  - `test_a_workbench_signal_withholds_fast_track_and_the_receipt_says_the_old_rule_fired`
- [tests/test_learner_text_gaps_flow.py](../../../../../../tests/test_learner_text_gaps_flow.py) — direct import
  - `test_a_gap_brings_an_assumed_los_check_forward_and_the_switch_restores_the_predecessor`
  - `test_a_gap_on_a_maintenance_lo_brings_its_next_review_forward_until_answered`
  - `test_the_switch_off_queue_equals_the_predecessor_version`
- [tests/test_lp_claim_fixes_rereview.py](../../../../../../tests/test_lp_claim_fixes_rereview.py) — direct import
  - `test_f9_a_miss_the_diagnosis_timeout_decides_carries_its_line_reopened_after_the_deadline`
- [tests/test_lp_claim_fixes_review.py](../../../../../../tests/test_lp_claim_fixes_review.py) — direct import
- [tests/test_placement_diagnosis_decides.py](../../../../../../tests/test_placement_diagnosis_decides.py) — direct import
  - `test_i_dont_know_this_does_not_wait_on_a_pending_diagnosis`
- [tests/test_placement_report.py](../../../../../../tests/test_placement_report.py) — direct import
  - `test_placement_status_lists_open_assumptions`
  - `test_report3_counts_each_learning_obligation_once`
  - `test_report3_orders_same_second_practice_after_the_decision`
- [tests/test_placement_signals.py](../../../../../../tests/test_placement_signals.py) — direct import
  - `test_asking_never_changes_the_record_only_routing`
  - `test_curiosity_carries_no_negative_signal`
  - `test_help_before_starting_blocks_fast_track`
  - `test_reader_confusion_blocks_fast_track_and_teaches_the_lo_first`
  - `test_suspected_leak_makes_the_answer_non_cold_for_fast_track`
- [tests/test_placement_split_grades.py](../../../../../../tests/test_placement_split_grades.py) — direct import
- [tests/test_quick_check.py](../../../../../../tests/test_quick_check.py) — direct import
  - `test_an_abandoned_check_ignores_later_practice_in_the_same_session`
  - `test_an_abandoned_quick_check_still_feeds_the_split_after_its_budget`
  - `test_fast_track_waits_for_an_open_quick_check`
- [tests/test_reader_rw1b_review.py](../../../../../../tests/test_reader_rw1b_review.py) — direct import
  - `test_f1_a_formative_gap_brings_no_check_forward`
- [tests/test_router_offer_log.py](../../../../../../tests/test_router_offer_log.py) — direct import
  - `test_placement_components_and_exclusions_are_in_the_candidate_set`
- [tests/test_slate_record.py](../../../../../../tests/test_slate_record.py) — direct import
  - `test_a_placement_check_records_why_its_lo_items_were_not_candidates`
- [tests/test_stuck_prompt_composition.py](../../../../../../tests/test_stuck_prompt_composition.py) — direct import
- [tests/test_today_headline.py](../../../../../../tests/test_today_headline.py) — direct import
  - `test_assumed_comes_first_and_is_omitted_before_placement`

## Modification guidance

- Make changes here when the responsibility remains decisions within learnloop.placement; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/placement/decisions.py](../../../../../../src/learnloop/placement/decisions.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
