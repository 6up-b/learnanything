---
title: "learnloop.held_grades"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/held_grades.py"
source_paths:
  - "src/learnloop/held_grades.py"
source_commit: "35a648918814189370398d63681da08d45e07151"
source_commit_timestamp: "2026-11-03T13:26:16-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.held_grades module"
  - "src/learnloop/held_grades.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.held_grades`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.held_grades` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: THE held-grade predicate over the ledger (held-grade-evidence).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/held_grades.py](../../../../../src/learnloop/held_grades.py) |
| Source lines | 284 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `35a648918814189370398d63681da08d45e07151` |
| Commit timestamp | `2026-11-03T13:26:16-05:00` |

## Public API

- `held_for_review_attempts(connection: Any, attempt_ids: Iterable[str] | None=None) -> frozenset[str]` ([source](../../../../../src/learnloop/held_grades.py), line 62) — The attempts (of ``attempt_ids``; ``None`` reads every one) whose grade is held for review NOW, on ``connection``: a route-rule hold (the latest blind record AND the current evidence), or a current grading epoch whose contract is unrecorded (the reason replay records at ``mvp-0.…
- `contract_unrecorded_attempts(connection: Any, attempt_ids: Iterable[str] | None=None) -> frozenset[str]` ([source](../../../../../src/learnloop/held_grades.py), line 132) — The attempts (of ``attempt_ids``; ``None`` reads every one) whose current grading epoch replay held because its contract is unrecorded (``GRADE_CONTRACT_UNRECORDED``, written only by replay at ``mvp-0.26``): the canonical projection leaves them out as replay does.
- `record_held_for_review(blind_record: Mapping[str, Any] | None) -> bool` ([source](../../../../../src/learnloop/held_grades.py), line 160) — The RECORD half of the hold for one persisted blind grade record row (``outcome_contract.grade_held_for_review`` of its grading support): what replay hands the attempt step, which evaluates the evidence half.
- `held_attempt_ids(repository: Any, attempt_ids: Iterable[str] | None=None) -> frozenset[str]` ([source](../../../../../src/learnloop/held_grades.py), line 169) — :func:`held_for_review_attempts` through a repository's connection (no read at all for an empty id list).
- `attempt_grade_held(repository: Any, attempt_id: str | None) -> bool` ([source](../../../../../src/learnloop/held_grades.py), line 181) — Is this one persisted attempt's grade held for review now?
- `mark_held_attempts(repository: Any, rows: Iterable[Mapping[str, Any]], *, key: str='id') -> list[dict[str, Any]]` ([source](../../../../../src/learnloop/held_grades.py), line 187) — ``rows`` (copies) with :data:`HELD_ROW_KEY` set on each attempt the predicate holds, in one query.
- `effective_probe_observation_rows(connection: Any, rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../src/learnloop/held_grades.py), line 202) — Probe observation rows (``probe_observations_for_episode``'s shape: the observation record under ``"observation"`` plus its attempt's joined columns) as every reader takes them NOW (review F3).
- `pfc_assessment(attributions: Iterable[Any]) -> str | None` ([source](../../../../../src/learnloop/held_grades.py), line 240) — One attempt's PF-c assessment state from its current evidence rows' ``attribution_json`` values: ``None`` unless a row was written under the unassessed rule, else partially or nothing assessed (``outcome_contract``).
- `pfc_assessments(connection: Any, attempt_ids: Iterable[str]) -> dict[str, str]` ([source](../../../../../src/learnloop/held_grades.py), line 251) — ``pfc_assessment`` for each of ``attempt_ids`` that has one, read from the current (non-superseded) grading evidence on ``connection``.

### Module constants

- `_HELD_RECORD_MARK` ([src/learnloop/held_grades.py](../../../../../src/learnloop/held_grades.py), line 59)

### Explicit exports

`__all__` declares:

- `HELD_ROW_KEY`
- `attempt_grade_held`
- `contract_unrecorded_attempts`
- `effective_probe_observation_rows`
- `held_attempt_ids`
- `held_for_review_attempts`
- `mark_held_attempts`
- `pfc_assessment`
- `pfc_assessments`
- `record_held_for_review`

## Internal implementation anchors

- `_contract_unrecorded_in(connection: Any, chunks: list[list[str] | None]) -> frozenset[str]` ([source](../../../../../src/learnloop/held_grades.py), line 144)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `held_for_review_attempts`; statically calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `held_attempt_ids`, `record_held_for_review`; statically calls `held_attempt_ids`, `record_held_for_review`
- [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]] — imports `attempt_grade_held`; statically calls `attempt_grade_held`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `attempt_grade_held`; statically calls `attempt_grade_held`
- [[Reference/Modules/learnloop/curriculum/graph_edit_proposals|learnloop.curriculum.graph_edit_proposals]] — imports `held_attempt_ids`; statically calls `held_attempt_ids`
- [[Reference/Modules/learnloop/daily_plan/router_teach_back|learnloop.daily_plan.router_teach_back]] — imports `attempt_grade_held`, `held_for_review_attempts`; statically calls `attempt_grade_held`, `held_for_review_attempts`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `effective_probe_observation_rows`, `held_for_review_attempts`; statically calls `effective_probe_observation_rows`, `held_for_review_attempts`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `attempt_grade_held`; statically calls `attempt_grade_held`
- [[Reference/Modules/learnloop/diagnosis/contrast_pairs|learnloop.diagnosis.contrast_pairs]] — imports `mark_held_attempts`; statically calls `mark_held_attempts`
- [[Reference/Modules/learnloop/diagnosis/error_hunt|learnloop.diagnosis.error_hunt]] — imports `mark_held_attempts`; statically calls `mark_held_attempts`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `mark_held_attempts`; statically calls `mark_held_attempts`
- [[Reference/Modules/learnloop/diagnosis/forecast_receipts|learnloop.diagnosis.forecast_receipts]] — imports `held_for_review_attempts`; statically calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `held_for_review_attempts`; statically calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/diagnosis/probe_audit|learnloop.diagnosis.probe_audit]] — imports `held_attempt_ids`; statically calls `held_attempt_ids`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `held_attempt_ids`; statically calls `held_attempt_ids`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `held_attempt_ids`; statically calls `held_attempt_ids`
- [[Reference/Modules/learnloop/diagnosis/recurrence/report|learnloop.diagnosis.recurrence.report]] — imports `held_attempt_ids`; statically calls `held_attempt_ids`
- [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]] — imports `held_attempt_ids`, `held_for_review_attempts`, `pfc_assessments`; statically calls `held_attempt_ids`, `held_for_review_attempts`, `pfc_assessments`
- [[Reference/Modules/learnloop/evsi_calibration/forecast_report|learnloop.evsi_calibration.forecast_report]] — imports `held_for_review_attempts`; statically calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/goals/certification_cold_probe|learnloop.goals.certification_cold_probe]] — imports `held_attempt_ids`; statically calls `held_attempt_ids`
- [[Reference/Modules/learnloop/goals/exam_calibration|learnloop.goals.exam_calibration]] — imports `held_attempt_ids`; statically calls `held_attempt_ids`
- [[Reference/Modules/learnloop/goals/forecast_ledger|learnloop.goals.forecast_ledger]] — imports `held_attempt_ids`; statically calls `held_attempt_ids`
- [[Reference/Modules/learnloop/hints/map_seeds|learnloop.hints.map_seeds]] — imports `held_for_review_attempts`; statically calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/instructional/policy|learnloop.instructional.policy]] — imports `held_for_review_attempts`; statically calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/instructional/valuation|learnloop.instructional.valuation]] — imports `held_for_review_attempts`; statically calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/learner/calibration|learnloop.learner.calibration]] — imports `held_attempt_ids`; statically calls `held_attempt_ids`
- [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]] — imports `contract_unrecorded_attempts`; statically calls `contract_unrecorded_attempts`
- [[Reference/Modules/learnloop/learner/lesson_weight|learnloop.learner.lesson_weight]] — imports `held_for_review_attempts`; statically calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/learner/recall_coverage|learnloop.learner.recall_coverage]] — imports `mark_held_attempts`; statically calls `mark_held_attempts`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `module`; statically calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]] — imports `held_for_review_attempts`, `pfc_assessments`; statically calls `held_for_review_attempts`, `pfc_assessments`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `held_for_review_attempts`; statically calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/reader/reader_report|learnloop.reader.reader_report]] — imports `held_for_review_attempts`; statically calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/regrade_contract_upgrade|learnloop.regrade_contract_upgrade]] — imports `contract_unrecorded_attempts`; statically calls `contract_unrecorded_attempts`
- [[Reference/Modules/learnloop/remote/views|learnloop.remote.views]] — imports `held_for_review_attempts`; statically calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/scheduling/evaluation|learnloop.scheduling.evaluation]] — imports `held_attempt_ids`; statically calls `held_attempt_ids`
- [[Reference/Modules/learnloop/scheduling/intent/recall_targets|learnloop.scheduling.intent.recall_targets]] — imports `held_for_review_attempts`; statically calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/scheduling/review_log|learnloop.scheduling.review_log]] — imports `held_attempt_ids`; statically calls `held_attempt_ids`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `held_attempt_ids`; statically calls `held_attempt_ids`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `HELD_ROW_KEY`, `attempt_grade_held`, `contract_unrecorded_attempts`, `held_attempt_ids`, `held_for_review_attempts`, `mark_held_attempts`, `pfc_assessment`, `pfc_assessments`; statically calls `contract_unrecorded_attempts`
- [[Reference/Modules/learnloop/substrate/data_quality|learnloop.substrate.data_quality]] — imports `held_for_review_attempts`; statically calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/substrate/dataset|learnloop.substrate.dataset]] — imports `held_for_review_attempts`; statically calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/substrate/intervention_outcomes|learnloop.substrate.intervention_outcomes]] — imports `held_for_review_attempts`; statically calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/tutor/question_signal|learnloop.tutor.question_signal]] — imports `held_attempt_ids`; statically calls `held_attempt_ids`
- [[Reference/Modules/learnloop/workbench/compare_methods|learnloop.workbench.compare_methods]] — imports `held_for_review_attempts`; statically calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/workbench/help_outcomes|learnloop.workbench.help_outcomes]] — imports `held_for_review_attempts`; statically calls `held_for_review_attempts`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `held_attempt_ids`; statically calls `held_attempt_ids`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `attempt_grade_held`; statically calls `attempt_grade_held`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `held_attempt_ids`; statically calls `held_attempt_ids`

### Repository tooling consumers

- [scripts/voi_cap_report.py](../../../../../scripts/voi_cap_report.py); calls `held_for_review_attempts`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `GRADE_CONTRACT_UNRECORDED`, `HELD_ROW_KEY`, `PFC_NOTHING_ASSESSED`, `PFC_PARTIALLY_ASSESSED`, `grade_held_for_review`, `grade_is_held`, `unassessed_evidence_row`; calls `grade_held_for_review`, `grade_is_held`, `unassessed_evidence_row`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]], [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]], [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]], [[Reference/Modules/learnloop/curriculum/graph_edit_proposals|learnloop.curriculum.graph_edit_proposals]] and 44 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/mcp_world.py](../../../../../tests/mcp_world.py) — direct import
- [tests/test_ad2_model.py](../../../../../tests/test_ad2_model.py) — direct import
  - `test_held_grade_excluded`
- [tests/test_forecast_receipts.py](../../../../../tests/test_forecast_receipts.py) — direct import
  - `test_f3_a_cold_success_whose_grade_is_now_held_is_not_measured`
- [tests/test_held_grade_evidence.py](../../../../../tests/test_held_grade_evidence.py) — direct import
  - `test_the_predicate_is_the_record_and_the_current_evidence`
- [tests/test_mvp017_route_check_replay.py](../../../../../tests/test_mvp017_route_check_replay.py) — direct import
- [tests/test_reader_recap_review_r3.py](../../../../../tests/test_reader_recap_review_r3.py) — direct import
  - `test_f1_r3_a_hold_released_after_the_cutoff_still_holds_at_the_cutoff`
- [tests/test_regrade_contract_successor.py](../../../../../tests/test_regrade_contract_successor.py) — direct import
  - `test_a_held_unrecorded_grade_is_no_evidence`
  - `test_a_regrade_in_its_pre_contract_grades_second_is_held_not_read_as_its_only_grade`
  - `test_a_route_rule_hold_is_released_by_a_successor_regrade_under_its_contract`
  - `test_a_successor_regrade_releases_an_unrecorded_hold`
  - `test_an_adjudication_releases_an_unrecorded_hold_under_the_contract_it_cites`
  - `test_an_uncited_regrade_epoch_is_held_with_the_maximum_recorded_with_it`
  - `test_an_unrecorded_joint_regrade_keeps_the_correctness_it_carries_and_never_fails_a_rebuild`
  - `test_the_timeline_banks_exactly_what_the_projection_banks_at_the_successor`
- [tests/test_regrade_contract_upgrade.py](../../../../../tests/test_regrade_contract_upgrade.py) — direct import
  - `test_a_failed_activation_leaves_the_predecessor_exactly_as_it_was`
  - `test_upgrade_holds_exactly_the_unrecorded_epochs_and_rewrites_no_evidence`
- [tests/test_router_card.py](../../../../../tests/test_router_card.py) — direct import
- [tests/test_router_r2c_teach_back.py](../../../../../tests/test_router_r2c_teach_back.py) — direct import
  - `test_a_held_teach_back_is_never_summarized`
- [tests/test_rw2c_fix_round2.py](../../../../../tests/test_rw2c_fix_round2.py) — direct import
  - `test_fr2_5_the_s5_historical_read_leaves_current_behaviour_alone`
- [tests/test_sources_merge_composition.py](../../../../../tests/test_sources_merge_composition.py) — direct import
- [tests/test_teacher_te0_confidence_events.py](../../../../../tests/test_teacher_te0_confidence_events.py) — direct import
  - `test_a_held_grade_reads_held_for_review_in_the_events`
- [tests/test_ux_phase4_feedback.py](../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_f4_a_shared_facet_credits_only_the_topic_whose_answer_earned_it`
- [tests/test_ux_phase4_landing.py](../../../../../tests/test_ux_phase4_landing.py) — direct import
  - `test_a_contest_the_regrade_does_not_uphold_is_flagged_never_held`

## Modification guidance

- Make changes here when the responsibility remains held grades within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/held_grades.py](../../../../../src/learnloop/held_grades.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
