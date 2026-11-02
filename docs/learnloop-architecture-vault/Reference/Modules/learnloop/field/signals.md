---
title: "learnloop.field.signals"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/field/signals.py"
source_paths:
  - "src/learnloop/field/signals.py"
source_commit: "363fc7c1bd806d2f144610c830b8c3fac35e2170"
source_commit_timestamp: "2026-10-25T22:07:58-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.field"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.field.signals module"
  - "src/learnloop/field/signals.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-field"
---

# `learnloop.field.signals`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/field/_package|learnloop.field]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.field.signals` exists within [[Reference/Modules/learnloop/field/_package|learnloop.field]] to own the behavior summarized by its module contract: Read-only interaction derivation.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/field/signals.py](../../../../../../src/learnloop/field/signals.py) |
| Source lines | 624 |
| Owning package | [[Reference/Modules/learnloop/field/_package|learnloop.field]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `363fc7c1bd806d2f144610c830b8c3fac35e2170` |
| Commit timestamp | `2026-10-25T22:07:58-04:00` |

## Public API

- `instant(value: str) -> datetime` ([source](../../../../../../src/learnloop/field/signals.py), line 67) — Normalize ISO timestamps, including legacy naive UTC values.
- `normalize_question(event: Mapping[str, Any], *, reader: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/field/signals.py), line 82) — Flatten logged reader payloads without inventing a type or LO mapping.
- `classification_input(event: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/field/signals.py), line 118) — Whitelist question-time inputs; never include tutor answers/later grades.
- `input_hash(event: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/field/signals.py), line 143)
- `derive_interaction_signals(question_events: Iterable[Mapping[str, Any]], interaction_events: Iterable[Mapping[str, Any]], attempts: Iterable[AttemptRow], *, facet_to_lo: Mapping[str, str | tuple[str, ...]], cached_classifications: Iterable[Mapping[str, Any]]=(), daily_mass_cap: float=DAILY_SIGNAL_MASS_CAP, lo_to_subject: Mapping[str, str] | None=None, diagnostics: dict[str, Any] | None=None, stuck_confusions: Iterable[Mapping[str, Any]]=(), learner_gaps: Iterable[Mapping[str, Any]]=()) -> tuple[SignalRow, ...]` ([source](../../../../../../src/learnloop/field/signals.py), line 152) — Derive immutable rows using logged data and already-paid classifications.
- `load_interaction_signals(connection: Any, vault: Any, attempts: Iterable[AttemptRow], *, diagnostics: dict[str, Any] | None=None, include_workbench: bool=True) -> tuple[SignalRow, ...]` ([source](../../../../../../src/learnloop/field/signals.py), line 407) — Read logged mappings and paid outputs, never today's authored model.
- `learner_gap_targets(connection: Any, vault: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/field/signals.py), line 454) — Prerequisite gap targets the pipeline persisted, read at mvp-0.16 or later.
- `enrich_attempts(attempts: Iterable[AttemptRow], signals: Iterable[SignalRow]) -> tuple[AttemptRow, ...]` ([source](../../../../../../src/learnloop/field/signals.py), line 564) — Add predictor-only covariates without future-question leakage.
- `blocks_fast_track(signal: SignalRow) -> bool` ([source](../../../../../../src/learnloop/field/signals.py), line 604) — The one report-2 blocking rule, shared by the harness and the helper below.
- `confusion_blocks_fast_track(signals: Iterable[SignalRow], *, lo_id: str, as_of: str, subject_id: str='default', self_report_known: bool=False) -> bool` ([source](../../../../../../src/learnloop/field/signals.py), line 612) — Pure report-2 eligibility only; does not implement or mutate F2 routing.

### Module constants

- `SIGNAL_VERSION` ([src/learnloop/field/signals.py](../../../../../../src/learnloop/field/signals.py), line 46)
- `DAILY_SIGNAL_MASS_CAP` ([src/learnloop/field/signals.py](../../../../../../src/learnloop/field/signals.py), line 47)
- `LEARNER_GAP_SIGNAL_MASS` ([src/learnloop/field/signals.py](../../../../../../src/learnloop/field/signals.py), line 50)
- `QUESTION_TYPES` ([src/learnloop/field/signals.py](../../../../../../src/learnloop/field/signals.py), line 51)
- `ATTEMPT_PROGRESS_NO_WORK` ([src/learnloop/field/signals.py](../../../../../../src/learnloop/field/signals.py), line 58)
- `STUCK_CONFUSION_SIGNAL` ([src/learnloop/field/signals.py](../../../../../../src/learnloop/field/signals.py), line 60)
- `BOUND_QUESTION_SIGNAL` ([src/learnloop/field/signals.py](../../../../../../src/learnloop/field/signals.py), line 63)
- `FAST_TRACK_BLOCKING_TYPES` ([src/learnloop/field/signals.py](../../../../../../src/learnloop/field/signals.py), line 598)

## Internal implementation anchors

- `_list(value: Any) -> list[str]` ([source](../../../../../../src/learnloop/field/signals.py), line 73)
- `_question_time_targets(row: Mapping[str, Any], facets: Iterable[str]) -> list[str]` ([source](../../../../../../src/learnloop/field/signals.py), line 112) — LOs a logged facet mapped to when the question was asked (sorted).
- `_facet_los(mapping: Mapping[str, Any], facet: str) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/field/signals.py), line 147)
- `_logged_no_work_yet(event: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/field/signals.py), line 378) — A practice question logged as asked before any work (spec §3.1).
- `_target_subject(event: Mapping[str, Any], lo: str, attempt: AttemptRow | None) -> str` ([source](../../../../../../src/learnloop/field/signals.py), line 389) — A mapped target keeps its own subject, not the asking item's (review F11).
- `_link_practice_questions(connection: Any, questions: list[dict[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/field/signals.py), line 500) — Link a practice-screen question to the attempt it preceded (review F5).
- `_available_for_attempt(signal: SignalRow, attempt: AttemptRow) -> bool` ([source](../../../../../../src/learnloop/field/signals.py), line 555) — At tied timestamps only linked, logged practice assistance precedes the result.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/field_classification|learnloop.cli.field_classification]] — imports `classification_input`; statically calls `classification_input`
- [[Reference/Modules/learnloop/field/classification|learnloop.field.classification]] — imports `QUESTION_TYPES`, `classification_input`, `input_hash`; statically calls `classification_input`, `input_hash`
- [[Reference/Modules/learnloop/field/decider|learnloop.field.decider]] — imports `QUESTION_TYPES`
- [[Reference/Modules/learnloop/field/evaluation|learnloop.field.evaluation]] — imports `blocks_fast_track`; statically calls `blocks_fast_track`
- [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]] — imports `enrich_attempts`, `load_interaction_signals`; statically calls `enrich_attempts`, `load_interaction_signals`
- [[Reference/Modules/learnloop/placement/signals|learnloop.placement.signals]] — imports `blocks_fast_track`, `load_interaction_signals`; statically calls `blocks_fast_track`, `load_interaction_signals`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `LEARNER_TEXT_GAP_VERSIONS`
- [[Reference/Modules/learnloop/attempts/stuck|learnloop.attempts.stuck]] — imports `stuck_answers`; calls `stuck_answers`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/contract|learnloop.diagnosis.text_gaps.contract]] — imports `NON_SERVING_SOURCE_KINDS`
- [[Reference/Modules/learnloop/field/types|learnloop.field.types]] — imports `AttemptRow`, `SignalRow`; calls `SignalRow`
- [[Reference/Modules/learnloop/field/workbench_signals|learnloop.field.workbench_signals]] — imports `is_workbench_signal`, `load_workbench_signals`; calls `is_workbench_signal`, `load_workbench_signals`
- [[Reference/Modules/learnloop/hint_window|learnloop.hint_window]] — imports `ITEM_WINDOW_QUESTION_CONTEXTS`, `following_attempt`, `workbench_bound`; calls `following_attempt`, `workbench_bound`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `hashlib`, `json`, `logging`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/field_classification|learnloop.cli.field_classification]], [[Reference/Modules/learnloop/field/classification|learnloop.field.classification]], [[Reference/Modules/learnloop/field/decider|learnloop.field.decider]], [[Reference/Modules/learnloop/field/evaluation|learnloop.field.evaluation]], [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_eval_harness.py](../../../../../../tests/test_eval_harness.py) — direct import
  - `test_report2_shares_the_confusion_blocking_predicate`
- [tests/test_field_workbench_signals.py](../../../../../../tests/test_field_workbench_signals.py) — direct import
  - `test_a_stuck_step_with_text_is_one_zero_mass_confusion_row_per_chain`
  - `test_enrich_attempts_ignores_workbench_rows`
  - `test_help_before_the_first_step_comes_only_from_the_logged_snapshot`
  - `test_rereview_f3_the_subject_is_the_one_frozen_with_the_contract`
  - `test_review_f2_a_stuck_answer_keeps_the_step_time_row_through_delete_submit_and_grading`
- [tests/test_interaction_signals.py](../../../../../../tests/test_interaction_signals.py) — direct import
  - `test_cached_reader_classification_is_missing_only_and_not_backdated`
  - `test_curiosity_is_never_negative`
  - `test_daily_cap_is_chronological_utc_and_per_lo`
  - `test_explicit_and_paid_targets_override_facet_membership`
  - `test_late_classification_does_not_delay_logged_leak_or_help`
  - `test_later_feedback_cannot_change_earlier_attempt_or_prediction`
  - `test_loader_current_lo_edits_cannot_retarget_history`
  - `test_loader_logged_reader_mapping_not_current_span_provenance`
  - `test_loader_paid_mapping_is_available_only_at_classification_time`
  - `test_loader_without_optional_classification_table_is_read_only`
  - `test_prerequisite_mapping_not_item_fallback_and_leak_non_cold`
  - `test_tied_assistance_requires_linked_practice_phase`
  - `test_tied_linked_practice_assistance_independent_flags`
  - `test_tied_paid_classification_does_not_backdate_help`
  - `test_typed_questions_hint_depth_and_g13_pure_inputs`
- [tests/test_learner_text_gaps.py](../../../../../../tests/test_learner_text_gaps.py) — direct import
  - `test_a_matched_target_is_the_questions_weak_signal_with_its_subject`
  - `test_without_a_reading_nothing_is_targeted_and_the_grounded_rule_stays`
- [tests/test_learner_text_gaps_composition.py](../../../../../../tests/test_learner_text_gaps_composition.py) — direct import
  - `test_a_stuck_answer_keeps_its_confusion_signal_and_adds_one_gap_observation`
  - `test_the_gap_signal_changes_serving_only_at_mvp016_with_its_switch`
- [tests/test_learner_text_gaps_rereview.py](../../../../../../tests/test_learner_text_gaps_rereview.py) — direct import
- [tests/test_learner_text_gaps_review.py](../../../../../../tests/test_learner_text_gaps_review.py) — direct import
  - `test_f14_a_stuck_answer_and_its_diagnosis_give_one_observation`
  - `test_f5_a_match_on_the_items_own_lo_is_no_prerequisite_target`
  - `test_f6_a_question_retargeted_by_a_later_reading_is_observed_at_the_reading`
- [tests/test_placement_signals.py](../../../../../../tests/test_placement_signals.py) — direct import
  - `test_suspected_leak_makes_the_answer_non_cold_for_fast_track`
- [tests/test_reader_rw1b_review.py](../../../../../../tests/test_reader_rw1b_review.py) — direct import
  - `test_f1_a_formative_gap_is_not_a_weak_prerequisite_signal`
- [tests/test_reader_rw1c_review.py](../../../../../../tests/test_reader_rw1c_review.py) — direct import
  - `test_a_bound_question_precedes_the_next_attempt_in_the_field`
  - `test_a_mapped_lo_does_not_suppress_the_attribution`
- [tests/test_stuck_prompt.py](../../../../../../tests/test_stuck_prompt.py) — direct import
  - `test_a_regrade_appends_a_superseding_stuck_judgment`
  - `test_a_stuck_attempt_without_confusion_writes_no_signal`
  - `test_confusion_is_read_and_signalled_in_both_grading_modes`
  - `test_confusion_text_is_marked_and_becomes_a_fast_track_blocking_signal`
- [tests/test_stuck_prompt_replay.py](../../../../../../tests/test_stuck_prompt_replay.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains signals within learnloop.field; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/field/signals.py](../../../../../../src/learnloop/field/signals.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
