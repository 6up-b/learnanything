---
title: "learnloop.curriculum.golden_path_assessment"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/curriculum/golden_path_assessment.py"
source_paths:
  - "src/learnloop/curriculum/golden_path_assessment.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.curriculum"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Build a Study Map"
aliases:
  - "learnloop.curriculum.golden_path_assessment module"
  - "src/learnloop/curriculum/golden_path_assessment.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-curriculum"
---

# `learnloop.curriculum.golden_path_assessment`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.curriculum.golden_path_assessment` exists within [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] to own the behavior summarized by its module contract: P2 step B.8 -- the fresh held-out cold assessment + burn (spec_p2_narrow_golden_path §8.1, §8.2, §8.3; §12.5; migration 087 for the result artifact only -- the assessment substrate itself is landed P0).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/curriculum/golden_path_assessment.py](../../../../../../src/learnloop/curriculum/golden_path_assessment.py) |
| Source lines | 436 |
| Owning package | [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class PracticeOnlyNoAssessment(Exception)` ([source](../../../../../../src/learnloop/curriculum/golden_path_assessment.py), line 66) — A ``practice_only`` run has no reserved fresh assessment and never certifies (§1.1).
  - `__init__(self, run_id: str)` (line 71; internal)
- `class ReserveStatus` ([source](../../../../../../src/learnloop/curriculum/golden_path_assessment.py), line 77) — Result of the atomic reserve revalidation before render (§8.1).
  - `as_dict(self) -> dict[str, Any]` (line 86; public)
- `class AssessmentResult` ([source](../../../../../../src/learnloop/curriculum/golden_path_assessment.py), line 91) — The reliability-aware cold-assessment result DTO (§8.2 / P0 read-DTO rule).
  - `as_dict(self) -> dict[str, Any]` (line 116; public)
- `validate_reserve(repository: Repository, *, run_id: str, clock: Clock | None=None) -> ReserveStatus` ([source](../../../../../../src/learnloop/curriculum/golden_path_assessment.py), line 141) — Atomically recheck the reserved assessment surface against the global exposure ledger before render (§8.1).
- `open_assessment(repository: Repository, *, run_id: str, idempotency_key: str, feedback_condition: str | None=None, clock: Clock | None=None) -> Administration` ([source](../../../../../../src/learnloop/curriculum/golden_path_assessment.py), line 173) — Enter the assessment stage and open the cold administration at the burn boundary (§8.2).
- `class ReserveInvalid(Exception)` ([source](../../../../../../src/learnloop/curriculum/golden_path_assessment.py), line 232) — The reserved assessment surface collided before render; a fresh replacement is required (§8.1).
  - `__init__(self, run_id: str, status: ReserveStatus)` (line 236; internal)
- `submit_assessment(vault: Any, repository: Repository, *, run_id: str, administration_id: str, item: Any, surface_id: str, rubric_score: int, max_points: int, attempt_id: str, response_text: str | None=None, grader_confidence: float | None=None, has_fatal: bool=False, grading_source: str='human', feedback_condition: str | None=None, reveal_feedback: bool=True, idempotency_key: str | None=None, clock: Clock | None=None) -> AssessmentResult` ([source](../../../../../../src/learnloop/curriculum/golden_path_assessment.py), line 246) — Submit the cold response, grade it through the live P0.2/P0.3 pipeline, cite the pinned target version, and record the reliability-aware result artifact (§8.2).
- `assessment_result(repository: Repository, *, run_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/curriculum/golden_path_assessment.py), line 428) — The latest persisted cold-assessment result artifact for the run (§8.2).

### Module constants

- `ASSESSMENT_SNAPSHOT_SCHEMA_VERSION` ([src/learnloop/curriculum/golden_path_assessment.py](../../../../../../src/learnloop/curriculum/golden_path_assessment.py), line 51)
- `DEMONSTRATED_CLAIM_CERTAINTY` ([src/learnloop/curriculum/golden_path_assessment.py](../../../../../../src/learnloop/curriculum/golden_path_assessment.py), line 60)
- `SUCCESS_CLASSES` ([src/learnloop/curriculum/golden_path_assessment.py](../../../../../../src/learnloop/curriculum/golden_path_assessment.py), line 63)

## Internal implementation anchors

- `_resolved_reserved_surface(repository: Repository, surface_id: str) -> ResolvedActivity` ([source](../../../../../../src/learnloop/curriculum/golden_path_assessment.py), line 124)
- `_coverage_from_blueprint(repository: Repository, run: Mapping[str, Any] | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/curriculum/golden_path_assessment.py), line 399) — The blueprint recipe facet x capability cells the cold assessment covers (§8.2 coverage field).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/curriculum/golden_path_restoration|learnloop.curriculum.golden_path_restoration]] — imports `DEMONSTRATED_CLAIM_CERTAINTY`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_pack|learnloop.diagnosis.diagnostic_pack]] — imports `DEMONSTRATED_CLAIM_CERTAINTY`
- [[Reference/Modules/learnloop_sidecar/handlers/golden_path_assessment|learnloop_sidecar.handlers.golden_path_assessment]] — imports `module`; statically calls `assessment_result`, `open_assessment`, `submit_assessment`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]] — imports `PROJECTION_ALGORITHM_VERSION`, `resolve_grade`; calls `resolve_grade`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/curriculum/golden_path_run|learnloop.curriculum.golden_path_run]] — imports `module`; calls `advance`, `project_run`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/goals/goal_contracts|learnloop.goals.goal_contracts]] — imports `module`; calls `certify_from_administration`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `Administration`, `ExposureCollisionAtRender`, `ResolvedActivity`, `append_feedback`, `append_observation`, `append_practice_successor_proposal`, `cancel_reservation`, `canonical_json`, `evaluate_held_out_eligibility`, `open_administration`; calls `ResolvedActivity`, `append_feedback`, `append_observation`, `append_practice_successor_proposal`, `cancel_reservation`, `canonical_json`, `evaluate_held_out_eligibility`, `open_administration`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/curriculum/golden_path_restoration|learnloop.curriculum.golden_path_restoration]], [[Reference/Modules/learnloop/diagnosis/diagnostic_pack|learnloop.diagnosis.diagnostic_pack]], [[Reference/Modules/learnloop_sidecar/handlers/golden_path_assessment|learnloop_sidecar.handlers.golden_path_assessment]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_golden_path_assessment.py](../../../../../../tests/test_golden_path_assessment.py) — direct import
  - `test_burned_surface_refuses_and_run_degrades`
  - `test_cold_assessment_success_certifies_the_pinned_version`
  - `test_failed_assessment_seeds_only_a_practice_successor`
  - `test_feedback_before_response_yields_zero_terminal_credit`
  - `test_practice_only_run_mints_no_certification`
- [tests/test_p2_acceptance.py](../../../../../../tests/test_p2_acceptance.py) — direct import
  - `test_event_replay_equivalence_after_full_walk`
  - `test_golden_path_ten_step_fixture_journey`

## Modification guidance

- Change golden path assessment policy here when curriculum owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/curriculum/golden_path_assessment.py](../../../../../../src/learnloop/curriculum/golden_path_assessment.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
