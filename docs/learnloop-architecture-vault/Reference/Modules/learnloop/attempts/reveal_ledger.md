---
title: "learnloop.attempts.reveal_ledger"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/reveal_ledger.py"
source_paths:
  - "src/learnloop/attempts/reveal_ledger.py"
source_commit: "3f7be0a9042a6625d8c1f2d027e87accf4635c63"
source_commit_timestamp: "2026-10-20T02:13:08-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.attempts.reveal_ledger module"
  - "src/learnloop/attempts/reveal_ledger.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.reveal_ledger`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.reveal_ledger` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: The cross-channel answer-reveal ledger (migration 154).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/reveal_ledger.py](../../../../../../src/learnloop/attempts/reveal_ledger.py) |
| Source lines | 661 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `3f7be0a9042a6625d8c1f2d027e87accf4635c63` |
| Commit timestamp | `2026-10-20T02:13:08-04:00` |

## Public API

- `is_routine_answer_display(row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 93) — Is this ledger row one of the plain surface's routine full-answer displays?
- `routine_display_lapsed_before(at: str | None) -> str | None` ([source](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 99) — The instant (ledger timestamp format) before which a routine display no longer counts against a production at ``at`` (its coverage has ended); None when ``at`` is unknown (nothing lapses: fail closed).
- `frozen_trace_hash(answer_md: str, explanation_md: str | None) -> str` ([source](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 120) — The identity of the trace a plain self-grade froze before it showed the key.
- `disclosure_basis(submission_id: str, frozen_hash: str, display_id: str | None=None) -> str` ([source](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 128) — The basis of a plain self-grade's disclosure row: a versioned, canonical JSON identity (its retry key, the hash of the trace it froze and, for a display row, the display id).
- `reveal_episode_id(repository: Repository, practice_item_id: str | None, *, strict: bool=False) -> str | None` ([source](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 153) — The live repair episode an exposure on this item belongs to, if any.
- `record_reveal(repository: Repository, *, practice_item_id: str, source_kind: str, amount: float, learning_object_id: str | None=None, remediation_episode_id: str | None=None, basis: str | None=None, question_event_id: str | None=None, attempt_id: str | None=None, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 173) — Append one reveal.
- `record_reveal_strict(repository: Repository, *, practice_item_id: str, source_kind: str, amount: float, learning_object_id: str | None=None, remediation_episode_id: str | None=None, basis: str | None=None, question_event_id: str | None=None, attempt_id: str | None=None, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 207) — :func:`record_reveal` for a caller whose action must not stand without its reveal: a failed write raises (inside the caller's transaction, so the action rolls back with it).
- `class ProductionAdmissibility` ([source](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 243) — Whether a learner production counts as INDEPENDENT evidence.
- `production_admissibility(repository: Repository, *, practice_item_id: str | None, learning_object_id: str | None=None, produced_at: str | None, since: str | None=None, strict: bool=False, production_id: str | None=None, clock: Clock | None=None) -> ProductionAdmissibility` ([source](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 259) — Admit a learner production unless a reveal preceded it in its window.
- `repair_display_amounts(repair_suggestions: Sequence[Mapping[str, Any]] | None) -> list[tuple[str, float]]` ([source](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 366) — (repair id, declared reveal budget) for suggestions that reveal anything.
- `record_repair_display_reveals(repository: Repository, *, attempt_id: str, practice_item_id: str | None, learning_object_id: str | None=None, repair_suggestions: Sequence[Mapping[str, Any]] | None=None, clock: Clock | None=None) -> int` ([source](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 390) — Debit the ledger for repair suggestions shown on a feedback screen.
- `record_answer_display_reveal(repository: Repository, *, attempt_id: str, practice_item_id: str, learning_object_id: str | None=None, basis: str, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 430) — Debit the ledger for the full expected answer shown after an attempt.
- `class DisplayReceipt` ([source](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 475) — A routine display row the ledger holds: its id, its stamp (ledger format), and whether it was already there (a retry of the same display).
- `class DisplayNotRecorded(Exception)` ([source](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 484) — The display row could not be written: the screen must not show the answer on its strength, and retries under the same display id.
- `record_feedback_answer_display_reveal(repository: Repository, *, attempt_id: str, practice_item_id: str, display_id: str, learning_object_id: str | None=None, surface: str='desktop', clock: Clock | None=None) -> DisplayReceipt` ([source](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 535) — Record one display of the full answer on a feedback screen.
- `record_self_grade_disclosure_display(repository: Repository, *, practice_item_id: str, submission_id: str, frozen_hash: str, display_id: str, learning_object_id: str | None=None, clock: Clock | None=None) -> DisplayReceipt` ([source](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 569) — Record one display of the key on a pending plain self-grade (round 3 F1).
- `record_self_grade_disclosure_reveal(repository: Repository, *, practice_item_id: str, submission_id: str, frozen_hash: str, learning_object_id: str | None=None, attempt_id: str | None=None, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 600) — Debit the ledger for the full answer a plain self-grade showed.

### Module constants

- `REVEAL_SOURCE_KINDS` ([src/learnloop/attempts/reveal_ledger.py](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 48)
- `POST_ATTEMPT_REVEAL_KINDS` ([src/learnloop/attempts/reveal_ledger.py](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 56)
- `FEEDBACK_FULL_ANSWER_BASIS` ([src/learnloop/attempts/reveal_ledger.py](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 63)
- `SELF_GRADE_DISCLOSURE_BASIS` ([src/learnloop/attempts/reveal_ledger.py](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 64)
- `ROUTINE_ANSWER_DISPLAY_BASES` ([src/learnloop/attempts/reveal_ledger.py](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 73)
- `ROUTINE_ANSWER_DISPLAY_HORIZON` ([src/learnloop/attempts/reveal_ledger.py](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 83)
- `ROUTINE_ANSWER_DISPLAY_COVERAGE` ([src/learnloop/attempts/reveal_ledger.py](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 90)
- `DISCLOSURE_IDENTITY_VERSION` ([src/learnloop/attempts/reveal_ledger.py](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 114)
- `_DISCLOSURE_PREFIX` ([src/learnloop/attempts/reveal_ledger.py](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 115)

## Internal implementation anchors

- `_lapsed_routine_display(row: Mapping[str, Any], cutoff: str | None) -> bool` ([source](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 143) — A routine row whose coverage no longer reaches the read (the one convention, ``reveal_coverage``: covered when stamped at or after ``cutoff``, inclusive).
- `_production_trace(repository: Repository, production_id: str | None, practice_item_id: str | None) -> tuple[str | None, str | None]` ([source](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 356) — (retry key, trace) of the attempt ``production_id`` names on this item, the identity its own disclosure rows must match exactly; (None, None) without an id: no exemption (``serve_eligibility.attempt_submission``).
- `_record_routine_display(repository: Repository, *, basis: str, practice_item_id: str, learning_object_id: str | None, attempt_id: str | None, clock: Clock | None) -> DisplayReceipt` ([source](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 489) — Write one routine display row, or find it already written; raise :class:`DisplayNotRecorded` on any failure (round 3 F1).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `POST_ATTEMPT_REVEAL_KINDS`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `production_admissibility`; statically calls `production_admissibility`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `ProductionAdmissibility`, `production_admissibility`; statically calls `ProductionAdmissibility`, `production_admissibility`
- [[Reference/Modules/learnloop/diagnosis/split/card|learnloop.diagnosis.split.card]] — imports `record_repair_display_reveals`; statically calls `record_repair_display_reveals`
- [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]] — imports `production_admissibility`; statically calls `production_admissibility`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `production_admissibility`; statically calls `production_admissibility`
- [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]] — imports `record_reveal`; statically calls `record_reveal`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `record_reveal`; statically calls `record_reveal`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `record_reveal_strict`; statically calls `record_reveal_strict`
- [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]] — imports `record_answer_display_reveal`; statically calls `record_answer_display_reveal`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `record_reveal`, `reveal_episode_id`; statically calls `record_reveal`, `reveal_episode_id`
- [[Reference/Modules/learnloop/workbench/compare_methods|learnloop.workbench.compare_methods]] — imports `reveal_episode_id`; statically calls `reveal_episode_id`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `DisplayNotRecorded`, `record_feedback_answer_display_reveal`, `record_repair_display_reveals`; statically calls `record_feedback_answer_display_reveal`, `record_repair_display_reveals`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `record_reveal_strict`, `reveal_episode_id`; statically calls `record_reveal_strict`, `reveal_episode_id`
- [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] — imports `record_reveal_strict`, `reveal_episode_id`; statically calls `record_reveal_strict`, `reveal_episode_id`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `DisplayNotRecorded`, `frozen_trace_hash`, `record_self_grade_disclosure_display`; statically calls `frozen_trace_hash`, `record_self_grade_disclosure_display`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `frozen_trace_hash`, `record_self_grade_disclosure_reveal`; statically calls `frozen_trace_hash`, `record_self_grade_disclosure_reveal`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]] — imports `record_reveal_strict`, `reveal_episode_id`; statically calls `record_reveal_strict`, `reveal_episode_id`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/trace_evidence|learnloop.attempts.trace_evidence]] — imports `compose_learner_trace`; calls `compose_learner_trace`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `open_episode_for_practice_item`; calls `open_episode_for_practice_item`
- [[Reference/Modules/learnloop/reveal_coverage|learnloop.reveal_coverage]] — imports `ROUTINE_DISPLAY_BASES`, `ROUTINE_DISPLAY_COVERAGE`, `ROUTINE_DISPLAY_HORIZON`, `ROUTINE_DISPLAY_RENEWAL_GRACE`, `is_routine_display`, `routine_covered_from`; calls `is_routine_display`, `routine_covered_from`
- [[Reference/Modules/learnloop/serve_eligibility|learnloop.serve_eligibility]] — imports `module`; calls `attempt_submission`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]], [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]], [[Reference/Modules/learnloop/diagnosis/split/card|learnloop.diagnosis.split.card]], [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]] and 13 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_assumed_known.py](../../../../../../tests/test_assumed_known.py) — direct import
  - `test_a_post_reveal_answer_cannot_pass_the_check`
  - `test_a_post_reveal_answer_never_counts_toward_fast_track`
- [tests/test_causal_p2_acceptance.py](../../../../../../tests/test_causal_p2_acceptance.py) — direct import
  - `test_a_probe_answered_after_a_reveal_is_not_independent_evidence`
- [tests/test_daily_plan_composition.py](../../../../../../tests/test_daily_plan_composition.py) — direct import
  - `test_a_tutor_reveal_during_a_plan_item_leaves_the_item_flow_alone`
- [tests/test_dialogue_causal_join.py](../../../../../../tests/test_dialogue_causal_join.py) — direct import
  - `test_a_production_after_a_reveal_is_not_independent`
  - `test_a_reveal_on_a_sibling_item_of_the_same_lo_still_contaminates`
  - `test_an_eliciting_response_after_a_reveal_is_recorded_but_not_independent`
  - `test_an_embedded_prediction_stays_admissible_after_a_reveal`
- [tests/test_family_memory_projection.py](../../../../../../tests/test_family_memory_projection.py) — direct import
  - `test_reveal_read_failure_is_not_reported_as_cold`
- [tests/test_hint_h2a_review_round2.py](../../../../../../tests/test_hint_h2a_review_round2.py) — direct import
  - `test_v4_record_reveal_keeps_swallowing_for_its_existing_callers`
- [tests/test_library_exercises.py](../../../../../../tests/test_library_exercises.py) — direct import
  - `test_r3_verify_f11_admission_reads_the_bound_items_own_exposure_and_says_practice_only`
- [tests/test_serve_eligibility.py](../../../../../../tests/test_serve_eligibility.py) — direct import
  - `test_submit_exposure_is_the_sql_total_row_for_row`
  - `test_the_cold_delay_is_the_remediation_delay_and_the_constants_are_one`
- [tests/test_serve_eligibility_review.py](../../../../../../tests/test_serve_eligibility_review.py) — direct import
  - `test_a_cold_check_on_a_direct_open_is_withdrawn_when_its_item_can_no_longer_take_it_cold`
- [tests/test_stuck_prompt.py](../../../../../../tests/test_stuck_prompt.py) — direct import
  - `test_a_worked_answer_shown_in_the_attempts_own_second_still_primes_the_retry`
  - `test_migration_179_widens_the_reveal_kinds_and_keeps_the_ledger`
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_f1_a_production_after_the_cold_delay_is_independent_again`
  - `test_f1_a_review_after_the_cold_delay_is_recorded_unprimed_a_retry_before_it_primed`
  - `test_f1_other_reveals_keep_their_window`
  - `test_f1_the_full_answer_shown_on_feedback_is_charged_once_to_the_reveal_ledger`
  - `test_f1_the_routine_display_horizon_is_the_cold_retrieval_delay`
  - `test_f1g_a_pending_self_grade_disclosure_is_an_exposure_for_every_other_production`
  - `test_f1g_every_committed_display_row_counts_until_its_coverage_ends`
  - `test_f1g_the_screen_and_the_ledger_share_one_exposure_contract`
  - `test_f1i_a_display_after_a_production_does_not_count_against_it`
  - `test_f1i_a_display_stamped_ahead_of_the_clock_still_covers`
  - `test_f1i_only_the_commit_itself_is_exempt_never_another_response_in_its_second`
  - `test_f1j_a_key_that_ends_in_a_trace_hash_never_exempts_another_draft`
  - `test_f1j_a_legacy_row_whose_display_id_is_the_hash_gets_no_exemption`
  - `test_f1k_a_malformed_identity_exempts_nothing`
  - `test_f1r_a_display_that_lapses_never_stands_in_for_one_that_does_not`
  - `test_f1r_feedback_reopened_after_the_cold_delay_is_a_fresh_exposure`
- [tests/test_ux_phase4_landing.py](../../../../../../tests/test_ux_phase4_landing.py) — direct import
  - `test_a_cold_check_on_a_direct_open_is_served_as_on_main_unless_a_routine_display_covers_it`
  - `test_a_routine_display_marks_a_later_question_solution_seen_beyond_its_coverage`

## Modification guidance

- Change reveal ledger policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/reveal_ledger.py](../../../../../../src/learnloop/attempts/reveal_ledger.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
