---
title: "learnloop.goals.exam_pool"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/goals/exam_pool.py"
source_paths:
  - "src/learnloop/goals/exam_pool.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.goals"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.goals.exam_pool module"
  - "src/learnloop/goals/exam_pool.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-goals"
---

# `learnloop.goals.exam_pool`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.goals.exam_pool` exists within [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] to own the behavior summarized by its module contract: Exam pool: reserve existing items for a goal's held-out practice exam.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/goals/exam_pool.py](../../../../../../src/learnloop/goals/exam_pool.py) |
| Source lines | 484 |
| Owning package | [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ExamPoolReport` ([source](../../../../../../src/learnloop/goals/exam_pool.py), line 83)
  - `as_dict(self) -> dict[str, Any]` (line 98; public)
- `reserved_item_ids(repository: Repository) -> set[str]` ([source](../../../../../../src/learnloop/goals/exam_pool.py), line 113) — All practice item ids currently reserved (unreleased) across all goals.
- `release_exam_pool(repository: Repository, goal_id: str, *, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/goals/exam_pool.py), line 123) — Release every unreleased reservation for ``goal_id``.
- `reserve_exam_pool(vault: LoadedVault, repository: Repository, goal: Goal, *, item_count: int | None=None, defer_if_insufficient: bool=False, practice_floor: int=PRACTICE_FLOOR, clock: Clock | None=None) -> ExamPoolReport` ([source](../../../../../../src/learnloop/goals/exam_pool.py), line 133) — Reserve up to ``item_count`` held-out items covering the goal's scope.

### Module constants

- `_DIFFICULTY_STRATA` ([src/learnloop/goals/exam_pool.py](../../../../../../src/learnloop/goals/exam_pool.py), line 42)
- `PRACTICE_FLOOR` ([src/learnloop/goals/exam_pool.py](../../../../../../src/learnloop/goals/exam_pool.py), line 79)

## Internal implementation anchors

- `_difficulty_stratum(item: PracticeItem) -> str` ([source](../../../../../../src/learnloop/goals/exam_pool.py), line 45)
- `class _Candidate` ([source](../../../../../../src/learnloop/goals/exam_pool.py), line 57)
- `_candidates(vault: LoadedVault, repository: Repository, scope: dict[str, set[str]], own_reserved_ids: set[str]) -> list[_Candidate]` ([source](../../../../../../src/learnloop/goals/exam_pool.py), line 294) — Reservable items: active, never attempted, not reserved elsewhere.
- `_item_components(vault: LoadedVault, item: PracticeItem, covered: set[str]) -> frozenset[tuple[str, str]]` ([source](../../../../../../src/learnloop/goals/exam_pool.py), line 353) — The (facet, capability) blueprint components ``item`` can testify to.
- `_practiced_surface_families(vault: LoadedVault, attempted: set[str]) -> set[str]` ([source](../../../../../../src/learnloop/goals/exam_pool.py), line 414) — Independent-evidence groups the learner has already been served.
- `_select(candidates: list[_Candidate], item_count: int) -> list[_Candidate]` ([source](../../../../../../src/learnloop/goals/exam_pool.py), line 437) — Greedy blueprint-coverage selection with stratification + surface novelty.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `reserve_exam_pool`
- [[Reference/Modules/learnloop/goals/exam_session|learnloop.goals.exam_session]] — imports `release_exam_pool`; statically calls `release_exam_pool`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `reserved_item_ids`; statically calls `reserved_item_ids`
- [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]] — imports `reserve_exam_pool`; statically calls `reserve_exam_pool`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `utc_now_iso`; calls `SystemClock`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/goals/goal_contracts|learnloop.goals.goal_contracts]] — imports `resolve_head`; calls `resolve_head`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `resolve_goal_scope`; calls `resolve_goal_scope`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `compile_criterion_targets`, `default_capability_for`, `is_valid_capability`; calls `compile_criterion_targets`, `default_capability_for`, `is_valid_capability`
- [[Reference/Modules/learnloop/scheduling/controller_ownership|learnloop.scheduling.controller_ownership]] — imports `ExamReservationOwnershipConflict`, `module`, `staged_owned_practice_item_ids`; calls `ExamReservationOwnershipConflict`, `staged_owned_practice_item_ids`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `SurfaceAlreadyReserved`, `reserve_surface`, `resolve_legacy_item`; calls `reserve_surface`, `resolve_legacy_item`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `surface_group_id`; calls `surface_group_id`
- [[Reference/Modules/learnloop/substrate/instrument_serving|learnloop.substrate.instrument_serving]] — imports `unservable_reason`; calls `unservable_reason`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `Goal`, `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/goals/exam_session|learnloop.goals.exam_session]], [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]], [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_characterization_assessment_exam.py](../../../../../../tests/test_characterization_assessment_exam.py) — direct import
  - `test_finish_releases_pool_and_reservation_is_blocked_only_by_attempt_history`
  - `test_predictions_are_not_refrozen_on_restart`
  - `test_predictions_frozen_at_start_with_snapshot_fields`
  - `test_release_alone_makes_an_unattempted_item_reservable_again`
  - `test_reservation_row_shape_keyed_by_goal_no_contract_version`
- [tests/test_cli_generate_practice.py](../../../../../../tests/test_cli_generate_practice.py) — direct import
- [tests/test_conjunctive_instruments.py](../../../../../../tests/test_conjunctive_instruments.py) — direct import
  - `test_a_supporting_only_facet_contributes_no_reachable_cell`
  - `test_item_components_reads_authored_primary_targets_at_both_capabilities`
  - `test_item_components_without_authored_targets_is_unchanged`
- [tests/test_dual_authority_administration.py](../../../../../../tests/test_dual_authority_administration.py) — direct import
  - `test_assign_refused_when_item_already_exam_reserved`
  - `test_staged_owned_item_not_reservable_into_exam_pool`
- [tests/test_exam_pool.py](../../../../../../tests/test_exam_pool.py) — direct import
  - `test_item_in_at_most_one_unreleased_pool`
  - `test_only_never_attempted_items_are_reservable`
  - `test_release_frees_items`
  - `test_reservation_covers_scope_facets_and_strata`
  - `test_reservation_is_idempotent_per_goal`
  - `test_scheduler_skips_reserved_items`
  - `test_uncovered_facets_reported_when_no_item_tests_a_facet`
- [tests/test_exam_session.py](../../../../../../tests/test_exam_session.py) — direct import
  - `test_availability_open_ended_goal_never_in_window_but_startable`
  - `test_exam_answers_certify_facet_evidence_on_canonical_vault`
  - `test_finish_releases_the_exam_pool`
- [tests/test_goal_scope_material.py](../../../../../../tests/test_goal_scope_material.py) — direct import
  - `test_a_thin_pool_defers_instead_of_holding_everything_out`
  - `test_an_explicit_ask_is_never_deferred`
- [tests/test_grade_resolution_pipeline.py](../../../../../../tests/test_grade_resolution_pipeline.py) — direct import
  - `test_exam_answer_dual_writes_assessment_grade`
- [tests/test_independent_group_counting.py](../../../../../../tests/test_independent_group_counting.py) — direct import
  - `test_exam_practiced_surfaces_are_groups`
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — direct import
  - `test_exam_reservation_may_reserve_an_instrument`
- [tests/test_post_attempt_pipeline.py](../../../../../../tests/test_post_attempt_pipeline.py) — direct import
- [tests/test_sidecar_exams.py](../../../../../../tests/test_sidecar_exams.py) — direct import
  - `test_exam_submit_advances_before_background_grade_finishes`
  - `test_finished_report_carries_per_item_feedback_and_repairs`

## Modification guidance

- Change exam pool policy here when goals owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/goals/exam_pool.py](../../../../../../src/learnloop/goals/exam_pool.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
