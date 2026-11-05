---
title: "learnloop.diagnosis.split.live"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/split/live.py"
source_paths:
  - "src/learnloop/diagnosis/split/live.py"
source_commit: "workspace/uncommitted @ HEAD 4a801f1afce0faaf0246a9bd404a8ed73abf2dfb"
source_commit_timestamp: "2026-11-04T19:32:38-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.split"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.split.live module"
  - "src/learnloop/diagnosis/split/live.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-split"
---

# `learnloop.diagnosis.split.live`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.split.live` exists within [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] to own the behavior summarized by its module contract: The live split's read paths and settings (Slice 1 M2, spec §6.3, §11, §12).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/split/live.py](../../../../../../../src/learnloop/diagnosis/split/live.py) |
| Source lines | 499 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 4a801f1afce0faaf0246a9bd404a8ed73abf2dfb` |
| Commit timestamp | `2026-11-04T19:32:38-05:00` |

## Public API

- `settings_from_config(vault: LoadedVault) -> DiagnosisSettings` ([source](../../../../../../../src/learnloop/diagnosis/split/live.py), line 69)
- `live_history_store(vault: LoadedVault, repository: Repository) -> VaultHistoryStore` ([source](../../../../../../../src/learnloop/diagnosis/split/live.py), line 87) — M1's store with every persisted blind grade as the overlay.
- `joint_grade_record(vault: LoadedVault, repository: Repository, attempt: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/live.py), line 107) — A stored JOINT grade in the blind-record shape, causal fields stripped.
- `current_attempt_for(vault: LoadedVault, attempt: Mapping[str, Any], record: Mapping[str, Any], repository: Any=None) -> CurrentAttempt | None` ([source](../../../../../../../src/learnloop/diagnosis/split/live.py), line 163) — The attempt to diagnose; with ``repository``, its question is the one its graded contract froze (method-explicit-3 review F3).
- `current_confidence(repository: Any, attempt: Mapping[str, Any], record: Mapping[str, Any], *, vault: Any=None, vault_grade: bool=True) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/split/live.py), line 218) — Teacher TE0 (spec_teacher_v1 §15.2): the diagnosed attempt's confidence event (its tap, and the hedge read of the grade the diagnoser is shown: the blind record's own, else, with ``vault_grade``, the current grading evidence's) with the stated limit on the taps up to and includi…
- `confidence_for_offline_target(vault: Any, repository: Any, *, attempt_id: str, completed_at: str, record: Mapping[str, Any], planted: bool) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/split/live.py), line 268) — Review F4: the confidence block an offline diagnosis arm is given, the same assembly as live (:func:`current_confidence`) over the arm's own blind record.
- `needs_diagnosis(record: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/split/live.py), line 293) — §5.1: a non-pass criterion, a fatal error, or an error attribution.
- `sampled_correct_answer(attempt_id: str, rate: float) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/split/live.py), line 324) — Deterministic shadow sample of correct answers (§5.1, O5).
- `build_causal_view(*, diagnosis_id: str, proposal: Mapping[str, Any], record: Mapping[str, Any], error_events: Sequence[Mapping[str, Any]], agent_run_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/live.py), line 369) — The §4.2 reverse mapping of one validated diagnosis (computed once).
- `diagnosis_for_attempt(repository: Repository, attempt_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/split/live.py), line 456) — The diagnosis every reader uses: live, else a joint legacy view, else None.
- `grader_mode_for(repository: Repository, attempt_id: str) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/live.py), line 484)

### Module constants

- `CAUSAL_VIEW_VERSION` ([src/learnloop/diagnosis/split/live.py](../../../../../../../src/learnloop/diagnosis/split/live.py), line 34)
- `_SCOPE_FOR_VALIDITY` ([src/learnloop/diagnosis/split/live.py](../../../../../../../src/learnloop/diagnosis/split/live.py), line 37)
- `_REPAIR_FIELDS` ([src/learnloop/diagnosis/split/live.py](../../../../../../../src/learnloop/diagnosis/split/live.py), line 43)
- `_TRACE_FIELDS` ([src/learnloop/diagnosis/split/live.py](../../../../../../../src/learnloop/diagnosis/split/live.py), line 58)

### Explicit exports

`__all__` declares:

- `CAUSAL_VIEW_VERSION`
- `build_causal_view`
- `current_attempt_for`
- `diagnosis_for_attempt`
- `grader_mode_for`
- `joint_grade_record`
- `live_history_store`
- `needs_diagnosis`
- `sampled_correct_answer`
- `settings_from_config`

## Internal implementation anchors

- `_present(value: Any) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/split/live.py), line 335)
- `_event_ids_by_index(record: Mapping[str, Any], events: Sequence[Mapping[str, Any]]) -> dict[int, str]` ([source](../../../../../../../src/learnloop/diagnosis/split/live.py), line 339) — Blind attribution index -> raw error-event id.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]] — imports `current_attempt_for`, `joint_grade_record`, `live_history_store`, `needs_diagnosis`, `settings_from_config`; statically calls `current_attempt_for`, `joint_grade_record`, `live_history_store`, `needs_diagnosis`, `settings_from_config`
- [[Reference/Modules/learnloop/cli/diagnose|learnloop.cli.diagnose]] — imports `needs_diagnosis`; statically calls `needs_diagnosis`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `joint_grade_record`, `needs_diagnosis`; statically calls `joint_grade_record`, `needs_diagnosis`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `confidence_for_offline_target`; statically calls `confidence_for_offline_target`
- [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]] — imports `settings_from_config`; statically calls `settings_from_config`
- [[Reference/Modules/learnloop/diagnosis/recurrence/upgrade|learnloop.diagnosis.recurrence.upgrade]] — imports `settings_from_config`; statically calls `settings_from_config`
- [[Reference/Modules/learnloop/diagnosis/split/embeddings|learnloop.diagnosis.split.embeddings]] — imports `live_history_store`; statically calls `live_history_store`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `build_causal_view`, `current_attempt_for`, `joint_grade_record`, `live_history_store`, `needs_diagnosis`, `sampled_correct_answer`, `settings_from_config`; statically calls `build_causal_view`, `current_attempt_for`, `joint_grade_record`, `live_history_store`, `needs_diagnosis`, `sampled_correct_answer`, `settings_from_config`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/blind_grading|learnloop.attempts.blind_grading]] — imports `GRADER_MODE_BLIND`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `resolved_rubric`; calls `resolved_rubric`
- [[Reference/Modules/learnloop/confidence_events|learnloop.confidence_events]] — imports `module`; calls `Reading`, `current_block`, `enabled`, `hedge_from_record`, `read_hedges`, `result_class`, `taps_before`, `valid_tap`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/answered_contracts|learnloop.db.stores.answered_contracts]] — imports `answered_contracts`; calls `answered_contracts`
- [[Reference/Modules/learnloop/db/stores/diagnoses|learnloop.db.stores.diagnoses]] — imports `latest_blind_grade_rows`; calls `latest_blind_grade_rows`
- [[Reference/Modules/learnloop/db/stores/write_provenance|learnloop.db.stores.write_provenance]] — imports `grading_marks`, `read_snapshot`; calls `grading_marks`, `read_snapshot`
- [[Reference/Modules/learnloop/diagnosis/split/context|learnloop.diagnosis.split.context]] — imports `CurrentAttempt`, `current_attempt_from`; calls `current_attempt_from`
- [[Reference/Modules/learnloop/diagnosis/split/figure_trace|learnloop.diagnosis.split.figure_trace]] — imports `figure_trace_for_attempt`; calls `figure_trace_for_attempt`
- [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]] — imports `VaultHistoryStore`; calls `VaultHistoryStore`
- [[Reference/Modules/learnloop/diagnosis/split/legacy_view|learnloop.diagnosis.split.legacy_view]] — imports `LEGACY_VIEW_MODE`, `stored_legacy_view`; calls `stored_legacy_view`
- [[Reference/Modules/learnloop/diagnosis/split/settings|learnloop.diagnosis.split.settings]] — imports `DiagnosisSettings`; calls `DiagnosisSettings`
- [[Reference/Modules/learnloop/diagnosis/split/workbench_trace|learnloop.diagnosis.split.workbench_trace]] — imports `trace_for_attempt`; calls `trace_for_attempt`
- [[Reference/Modules/learnloop/followup_serve/gates|learnloop.followup_serve.gates]] — imports `hypothesis_marks_on`; calls `hypothesis_marks_on`
- [[Reference/Modules/learnloop/followup_serve/marks|learnloop.followup_serve.marks]] — imports `attempt_marks`, `marked_causes`, `opinion_block`; calls `attempt_marks`, `marked_causes`, `opinion_block`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `held_attempts`; calls `held_attempts`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `grade_held_for_review`; calls `grade_held_for_review`
- [[Reference/Modules/learnloop/symbolic_view|learnloop.symbolic_view]] — imports `switch_now`; calls `switch_now`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]], [[Reference/Modules/learnloop/cli/diagnose|learnloop.cli.diagnose]], [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]], [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]], [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ai_compare.py](../../../../../../../tests/test_ai_compare.py) — direct import
  - `test_grading_reads_the_contract_the_answer_was_graded_under`
- [tests/test_diagnosis_input_provenance.py](../../../../../../../tests/test_diagnosis_input_provenance.py) — direct import
  - `test_a_regrade_keeps_the_ids_a_belief_lists_resolvable`
  - `test_f3_a_grading_replaced_after_the_history_was_read_is_unaccountable`
  - `test_f4_a_regrade_to_no_errors_keeps_the_retired_events_answer`
  - `test_rereview_f3_a_payload_its_caller_supplied_is_never_certified`
  - `test_rereview_f3_the_overlay_s_payload_is_validated_by_the_identity_captured_with_it`
- [tests/test_diagnosis_pipeline.py](../../../../../../../tests/test_diagnosis_pipeline.py) — direct import
  - `test_the_accessor_and_the_overlays_agree_on_the_diagnosis_in_force`
- [tests/test_diagnosis_replay.py](../../../../../../../tests/test_diagnosis_replay.py) — direct import
  - `test_joint_reads_are_untouched_by_the_overlay`
- [tests/test_followup_fg1c_codex_review.py](../../../../../../../tests/test_followup_fg1c_codex_review.py) — direct import
  - `test_f1_a_rediagnosis_records_the_cause_it_was_shown_through_a_mark`
- [tests/test_hypothesis_marks_context.py](../../../../../../../tests/test_hypothesis_marks_context.py) — direct import
  - `test_a_rediagnosis_reads_the_marks_on_its_own_attempt`
- [tests/test_pfc_unassessed_readers.py](../../../../../../../tests/test_pfc_unassessed_readers.py) — direct import
  - `test_a_later_diagnosis_cannot_cite_an_unassessed_shortfall_as_a_recurrence`
- [tests/test_pfc_unverified_unassessed.py](../../../../../../../tests/test_pfc_unverified_unassessed.py) — direct import
  - `test_a_located_error_beside_an_unverified_criterion_still_counts`
- [tests/test_reader_rw2b_fix11.py](../../../../../../../tests/test_reader_rw2b_fix11.py) — direct import
  - `test_item1_the_diagnosers_trace_reads_a_stored_checked_verdict_as_the_models_when_off`
- [tests/test_reader_rw2b_fix14.py](../../../../../../../tests/test_reader_rw2b_fix14.py) — direct import
  - `test_items_2_3_a_row_stored_checked_reads_as_the_models_everywhere_once_the_switch_is_off`
- [tests/test_reader_rw2b_fix15.py](../../../../../../../tests/test_reader_rw2b_fix15.py) — direct import
  - `test_item2_a_switch_off_during_context_assembly_masks_the_rendered_trace`
- [tests/test_required_method_round3_review.py](../../../../../../../tests/test_required_method_round3_review.py) — direct import
  - `test_f3_the_diagnosers_history_and_current_attempt_read_the_question_given`
- [tests/test_teacher_te0_confidence_events.py](../../../../../../../tests/test_teacher_te0_confidence_events.py) — direct import
  - `test_the_diagnosers_history_and_current_attempt_carry_the_events`
  - `test_with_no_confidence_data_the_diagnosers_current_attempt_renders_as_before`
- [tests/test_teacher_te0_fix_round2.py](../../../../../../../tests/test_teacher_te0_fix_round2.py) — direct import
  - `test_the_live_history_keeps_the_ledgers_hold`
- [tests/test_teacher_te0_review_fixes.py](../../../../../../../tests/test_teacher_te0_review_fixes.py) — direct import
  - `test_a_held_current_attempt_reads_held_for_review_never_wrong`
  - `test_offline_and_live_diagnosis_share_the_confidence_block`
  - `test_switched_off_every_reader_gets_its_predecessor_context`
- [tests/test_workbench_trace.py](../../../../../../../tests/test_workbench_trace.py) — direct import
  - `test_a_workbench_attempt_carries_its_trace_under_the_suffix_and_never_a_map`
  - `test_every_other_attempt_renders_exactly_as_before`

## Modification guidance

- Change live policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/split/live.py](../../../../../../../src/learnloop/diagnosis/split/live.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
