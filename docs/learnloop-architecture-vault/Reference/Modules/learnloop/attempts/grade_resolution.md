---
title: "learnloop.attempts.grade_resolution"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/grade_resolution.py"
source_paths:
  - "src/learnloop/attempts/grade_resolution.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.attempts.grade_resolution module"
  - "src/learnloop/attempts/grade_resolution.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.grade_resolution`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.grade_resolution` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: Grade resolution pipeline + dual-write (spec_p0_measurement_correctness §4.1, §4.4).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/grade_resolution.py](../../../../../../src/learnloop/attempts/grade_resolution.py) |
| Source lines | 1038 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class GradeResolution` ([source](../../../../../../src/learnloop/attempts/grade_resolution.py), line 59)
- `resolve_grade(vault: LoadedVault, repository: Repository, *, item: PracticeItem, purpose: str, grading_source: str, attempt_id: str, response_text: str | None, rubric_score: int | None, max_points: int, grader_confidence: float | None=None, has_fatal: bool=False, signature_matched: bool=False, criterion_points: Mapping[str, float] | None=None, criterion_max: Mapping[str, float] | None=None, raw_output: Mapping[str, Any] | None=None, criterion_evidence: Any=None, agent_run_id: str | None=None, role: str='primary', domain: str | None=None, declared_length_bucket: str | None=None, outcome_schema_slug: str=COARSE_RESPONSE_SLUG, observed_class_override: str | None=None, grader_model_revision: str | None=None, administration_id: str | None=None, observation_id: str | None=None, surface_id: str | None=None, feedback_condition: str | None=None, clock: Clock | None=None) -> GradeResolution` ([source](../../../../../../src/learnloop/attempts/grade_resolution.py), line 77) — The §4.1 pipeline for one graded response.
- `response_certainty_lcb(vault: LoadedVault, repository: Repository, *, item: PracticeItem, grading_source: str, rubric_score: int | None, max_points: int, grader_confidence: float | None, has_fatal: bool=False, response_text: str | None=None, domain: str | None=None, grader_model_revision: str | None=None, outcome_schema_slug: str=COARSE_RESPONSE_SLUG, clock: Clock | None=None) -> float` ([source](../../../../../../src/learnloop/attempts/grade_resolution.py), line 327) — The certainty LCB of this response's calibrated interpretation, computed WITHOUT persisting anything (P0.3 §4.4 mastery wiring).
- `response_soft_score(vault: LoadedVault, repository: Repository, *, item: PracticeItem, grading_source: str, rubric_score: int | None, max_points: int, grader_confidence: float | None, has_fatal: bool=False, response_text: str | None=None, domain: str | None=None, grader_model_revision: str | None=None, outcome_schema_slug: str=COARSE_RESPONSE_SLUG, clock: Clock | None=None) -> tuple[float, float]` ([source](../../../../../../src/learnloop/attempts/grade_resolution.py), line 395) — (E[s(Z)|E], Var[s(Z)|E]) of the calibrated true-score, without persisting.
- `ensure_administration_identity(vault: LoadedVault, repository: Repository, *, item: PracticeItem, purpose: str, attempt_id: str, feedback_condition: str | None=None, clock: Clock | None=None) -> tuple[str, str, str]` ([source](../../../../../../src/learnloop/attempts/grade_resolution.py), line 515) — Resolve (or reuse) the surface + administration and append the observation for one response (§4.1 steps 1-2).
- `record_grade_dual_write(vault: LoadedVault, repository: Repository, **kwargs: Any) -> GradeResolution | None` ([source](../../../../../../src/learnloop/attempts/grade_resolution.py), line 551) — Fail-safe dual-write wrapper (§7.3).
- `quarantine_observation(repository: Repository, *, observation_id: str, surface_id: str | None, reason: str, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/attempts/grade_resolution.py), line 628) — Immediately quarantine the observation's active interpretation (§4.4).
- `append_adjudication_evidence_revision(repository: Repository, *, attempt_id: str, resolved_fraction: float, adjudication_id: str, adjudicator_source: str, rationale: str | None, vault: 'LoadedVault | None'=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/grade_resolution.py), line 710) — Ruling A (2026-07-27): write the adjudicated DIRECTION into the ledger.
- `append_adjudication(repository: Repository, *, observation_id: str, administration_id: str, reviewed_raw_event_ids: Sequence[str], adjudicator_source: str, resolved_class: str | None=None, resolved_distribution: Mapping[str, float] | None=None, rationale: str | None=None, bounded_trust_weight: float | None=None, superseded_adjudication_id: str | None=None, vault: 'LoadedVault | None'=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/grade_resolution.py), line 842) — Append an adjudication + a NEW interpretation and repoint the head (§3.3/§4.4).

### Module constants

- `_LOGGER` ([src/learnloop/attempts/grade_resolution.py](../../../../../../src/learnloop/attempts/grade_resolution.py), line 42)
- `PROJECTION_ALGORITHM_VERSION` ([src/learnloop/attempts/grade_resolution.py](../../../../../../src/learnloop/attempts/grade_resolution.py), line 44)
- `REVIEW_CONFIDENCE_THRESHOLD` ([src/learnloop/attempts/grade_resolution.py](../../../../../../src/learnloop/attempts/grade_resolution.py), line 49)
- `INFLUENCE_CERTAINTY_FLOOR` ([src/learnloop/attempts/grade_resolution.py](../../../../../../src/learnloop/attempts/grade_resolution.py), line 52)
- `BOUNDED_TRUST_WEIGHT_DEFAULT` ([src/learnloop/attempts/grade_resolution.py](../../../../../../src/learnloop/attempts/grade_resolution.py), line 55)
- `ADJUDICATION_GRADER_TIER` ([src/learnloop/attempts/grade_resolution.py](../../../../../../src/learnloop/attempts/grade_resolution.py), line 707)

## Internal implementation anchors

- `_persist_fallback_model(repository: Repository, resolved_model: gc.ResolvedModel, schema_id: str, schema_version: int, *, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/attempts/grade_resolution.py), line 475) — The uniform fallback has no persisted model row; the interpretation FK still needs one.
- `_record_dual_write_degradation(repository: Repository, kwargs: Mapping[str, Any], exc: Exception) -> None` ([source](../../../../../../src/learnloop/attempts/grade_resolution.py), line 594)
- `_leading_class(posterior: Mapping[str, float]) -> str | None` ([source](../../../../../../src/learnloop/attempts/grade_resolution.py), line 688) — The unique argmax of a class posterior; ``None`` on empty or tied.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `record_grade_dual_write`, `response_soft_score`; statically calls `record_grade_dual_write`, `response_soft_score`
- [[Reference/Modules/learnloop/cli/grading|learnloop.cli.grading]] — imports `append_adjudication`; statically calls `append_adjudication`
- [[Reference/Modules/learnloop/curriculum/golden_path_assessment|learnloop.curriculum.golden_path_assessment]] — imports `PROJECTION_ALGORITHM_VERSION`, `resolve_grade`; statically calls `resolve_grade`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `record_grade_dual_write`; statically calls `record_grade_dual_write`
- [[Reference/Modules/learnloop/goals/exam_session|learnloop.goals.exam_session]] — imports `record_grade_dual_write`; statically calls `record_grade_dual_write`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/effective_observation|learnloop.attempts.effective_observation]] — imports `module`; calls `shared_certainty_lcb`
- [[Reference/Modules/learnloop/attempts/grade_classifier|learnloop.attempts.grade_classifier]] — imports `CRITERION_CLASSIFIER_VERSION`, `RESPONSE_CLASSIFIER_VERSION`, `bucket_confidence`, `classify_criteria`, `classify_response`, `length_bucket_for_text`, `schema_shape_from_row`; calls `bucket_confidence`, `classify_criteria`, `classify_response`, `length_bucket_for_text`, `schema_shape_from_row`
- [[Reference/Modules/learnloop/attempts/grader_calibration|learnloop.attempts.grader_calibration]] — imports `module`; calls `certainty`, `credible_interval`, `grader_identity_hash`, `posterior_over_true_class`, `resolve_calibration_model`
- [[Reference/Modules/learnloop/attempts/outcome_schemas|learnloop.attempts.outcome_schemas]] — imports `COARSE_RESPONSE_SLUG`, `ensure_builtin_schemas`, `resolve_schema_id`; calls `ensure_builtin_schemas`, `resolve_schema_id`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `P0_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `resolve_grader_channel_prior`; calls `resolve_grader_channel_prior`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `append_observation`, `canonical_json`, `open_administration`, `resolve_legacy_item`; calls `append_observation`, `canonical_json`, `open_administration`, `resolve_legacy_item`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/cli/grading|learnloop.cli.grading]], [[Reference/Modules/learnloop/curriculum/golden_path_assessment|learnloop.curriculum.golden_path_assessment]], [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]], [[Reference/Modules/learnloop/goals/exam_session|learnloop.goals.exam_session]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_effective_observation.py](../../../../../../tests/test_effective_observation.py) — direct import
  - `test_adjudicated_grade_has_higher_certainty_than_heuristic`
  - `test_quarantined_interpretation_contributes_zero`
  - `test_shared_certainty_lcb_agrees_across_mastery_and_certification`
- [tests/test_grade_resolution_pipeline.py](../../../../../../tests/test_grade_resolution_pipeline.py) — direct import
  - `test_adjudication_clamps_out_of_range_trust`
  - `test_adjudication_distribution_respects_bounded_trust_and_authority`
  - `test_dual_write_failure_never_breaks_legacy_path`
  - `test_dual_write_mint_failure_is_logged_not_silent`
  - `test_quarantine_appends_new_head_without_mutating_prior`
  - `test_same_grader_agreement_does_not_narrow_but_adjudication_does`
  - `test_signature_error_reachable_when_signature_matched_threaded`
- [tests/test_grading_cli.py](../../../../../../tests/test_grading_cli.py) — direct import
  - `test_reviews_lists_quarantined_then_adjudicate_clears_and_receipt`
- [tests/test_p0_projection_cutover.py](../../../../../../tests/test_p0_projection_cutover.py) — direct import
  - `test_adjudicating_up_raises_credit_and_unchanged_direction_skips`
  - `test_adjudication_reverses_projection_and_preserves_history`
  - `test_mvp08_mastery_reliability_sources_certainty_lcb`
  - `test_ruling_a_superseded_rows_inert_nonsuperseded_rows_authoritative`
- [tests/test_unresolved_cause_gate.py](../../../../../../tests/test_unresolved_cause_gate.py) — direct import

## Modification guidance

- Change grade resolution policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/grade_resolution.py](../../../../../../src/learnloop/attempts/grade_resolution.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
