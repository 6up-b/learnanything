---
title: "learnloop.diagnosis.probe_evidence"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/probe_evidence.py"
source_paths:
  - "src/learnloop/diagnosis/probe_evidence.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.diagnosis.probe_evidence module"
  - "src/learnloop/diagnosis/probe_evidence.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.probe_evidence`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.probe_evidence` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Record the evidence produced by probe answers and their grades.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/probe_evidence.py](../../../../../../src/learnloop/diagnosis/probe_evidence.py) |
| Source lines | 817 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `record_episode_evidence(vault: LoadedVault, repository: Repository, *, learning_object_id: str, attempt_id: str, practice_item_id: str, attempt_type: str, hints_used: int, probe_presentation_id: str | None, grading_source: str, tutor_contaminated: bool=False, ai_client: object | None=None, grade_held_for_review: bool=False, grader_identity: tuple[str, str] | None=None, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_evidence.py), line 54) — Post-persist accounting for one attempt on an in-episode LO.
- `record_presentation_activity_classification(vault: LoadedVault, repository: Repository, *, attempt_id: str, practice_item_id: str, attempt_type: str, hints_used: int, probe_presentation_id: str, grading_source: str, tutor_contaminated: bool=False, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_evidence.py), line 133) — Persist presentation-derived eligibility before canonical projection.
- `dual_write_presentationless_probe_grade(vault: LoadedVault, repository: Repository, *, practice_item_id: str, attempt_id: str, grading_source: str, grader_identity: tuple[str, str] | None=None, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_evidence.py), line 361) — The same fail-safe dual-write for a probe answer with no presentation and no instrument (teacher TE2's lesson probe, ``attempts.attempts._record_lesson_probe``): a raw grade event and calibrated interpretation on a diagnostic administration, so the canonical projection banks the…
- `dual_write_regraded_probe_grade(vault: LoadedVault, repository: Repository, *, attempt_id: str, grading_source: str, grader_identity: tuple[str, str] | None, fired_error_types: Iterable[str], held: bool, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_evidence.py), line 390) — A regrade's probe grade, published under the replacement grade's own identity (TE2 landing ruling R1).

## Internal implementation anchors

- `_presentation_contamination(*, attempt_type: str, hints_used: int, tutor_contaminated: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_evidence.py), line 184)
- `_record_presentation_activity_fact(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, presentation: ProbePresentationRecord, *, attempt_id: str, practice_item_id: str, attempt_type: str, hints_used: int, tutor_contaminated: bool, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_evidence.py), line 199)
- `_robust_observation_snapshot(repository: Repository, episode: ProbeEpisodeRecord, instrument: CompiledInstrument, slot_map: Mapping[str, str], posterior_before: Mapping[str, float], *, observed_outcome: str, grader_confidence: float | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_evidence.py), line 245) — The mvp-0.8 decision-time posterior snapshot for one observation (§4.2).
- `_dual_write_probe_grade(vault: LoadedVault, repository: Repository, *, instrument: CompiledInstrument | None=None, practice_item_id: str, attempt_id: str, grading_source: str, observed_outcome: str, grader_identity: tuple[str, str] | None=None, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_evidence.py), line 278) — P0.2 dual-write for probe submissions (§4.1, §7.2).
- `_record_presentation_observation(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, hypothesis_set: HypothesisSet, *, attempt_id: str, practice_item_id: str, attempt_type: str, hints_used: int, probe_presentation_id: str, grading_source: str, tutor_contaminated: bool, grade_held_for_review: bool=False, grader_identity: tuple[str, str] | None=None, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_evidence.py), line 473)
- `_attempt_rubric_score(repository: Repository, attempt_id: str) -> int | None` ([source](../../../../../../src/learnloop/diagnosis/probe_evidence.py), line 736)
- `_assess_longform_trace(vault: LoadedVault, repository: Repository, presentation: ProbePresentationRecord, instrument: CompiledInstrument, *, attempt_id: str, practice_item_id: str, attempt_type: str)` ([source](../../../../../../src/learnloop/diagnosis/probe_evidence.py), line 743) — Assess the §8.2 structured trace for a long-form response, or None when the presentation's card declares no obligations (microprobes).
- `_observation_features(repository: Repository, presentation: ProbePresentationRecord, *, attempt_id: str, structured_trace: Mapping[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_evidence.py), line 791) — Logged-only observation features (§7.1): answer confidence, latency (both submitted and derived from presentation timestamps), and the §8.2 structured trace.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `dual_write_presentationless_probe_grade`, `dual_write_regraded_probe_grade`, `record_episode_evidence`, `record_presentation_activity_classification`; statically calls `dual_write_presentationless_probe_grade`, `dual_write_regraded_probe_grade`, `record_episode_evidence`, `record_presentation_activity_classification`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]] — imports `record_grade_dual_write`; calls `record_grade_dual_write`
- [[Reference/Modules/learnloop/attempts/outcome_schemas|learnloop.attempts.outcome_schemas]] — imports `BUILTIN_SCHEMAS`, `COARSE_RESPONSE_SLUG`
- [[Reference/Modules/learnloop/causal_activity_policy|learnloop.causal_activity_policy]] — imports `LESSON_PROBE_EVIDENCE_ORIGIN`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `ProbeEpisodeRecord`, `ProbePresentationRecord`, `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_activity_policy|learnloop.diagnosis.causal_activity_policy]] — imports `near_clone_from_selection_components`; calls `near_clone_from_selection_components`
- [[Reference/Modules/learnloop/diagnosis/longform_trace|learnloop.diagnosis.longform_trace]] — imports `assess_trace`, `classify_trace_outcome`, `obligations_from_bindings`, `outcomes_from_grading_evidence`; calls `assess_trace`, `classify_trace_outcome`, `obligations_from_bindings`, `outcomes_from_grading_evidence`
- [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]] — imports `block_complete`, `end_diagnostic_block`; calls `block_complete`, `end_diagnostic_block`
- [[Reference/Modules/learnloop/diagnosis/probe_completion|learnloop.diagnosis.probe_completion]] — imports `close_diagnostic_segment`, `persist_episode_beliefs`; calls `close_diagnostic_segment`, `persist_episode_beliefs`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `_bayes_update`, `_entropy`, `_fired_error_types`, `_item_max_points`, `_resolved_slot_map_from_snapshot`, `episode_hypothesis_set`, `episode_posterior`; calls `_bayes_update`, `_entropy`, `_fired_error_types`, `_item_max_points`, `_resolved_slot_map_from_snapshot`, `episode_hypothesis_set`, `episode_posterior`
- [[Reference/Modules/learnloop/diagnosis/probe_families|learnloop.diagnosis.probe_families]] — imports `APPROVED_DIAGNOSTIC_GRADING_SOURCES`, `CompiledInstrument`, `InstrumentCard`, `classify_outcome`, `instrument_observation_likelihoods`, `record_real_observation_counts`; calls `classify_outcome`, `instrument_observation_likelihoods`, `record_real_observation_counts`
- [[Reference/Modules/learnloop/diagnosis/probe_outcome_mapping|learnloop.diagnosis.probe_outcome_mapping]] — imports `coarse_class_for_outcome`, `coarse_schema_slug`, `mapping_snapshot`; calls `coarse_class_for_outcome`, `coarse_schema_slug`, `mapping_snapshot`
- [[Reference/Modules/learnloop/diagnosis/probe_presentations|learnloop.diagnosis.probe_presentations]] — imports `validate_presentation_for_submission`; calls `validate_presentation_for_submission`
- [[Reference/Modules/learnloop/diagnosis/probe_robust|learnloop.diagnosis.probe_robust]] — imports `load_pinned_channel`, `pinned_decision_posterior`; calls `load_pinned_channel`, `pinned_decision_posterior`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `HypothesisSet`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `GRADE_HELD_FOR_REVIEW`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_grade_resolution_pipeline.py](../../../../../../tests/test_grade_resolution_pipeline.py) — direct import
  - `test_probe_dual_write_helper_records_diagnostic_grade`
- [tests/test_probe_episodes.py](../../../../../../tests/test_probe_episodes.py) — direct import
  - `test_retried_submission_is_idempotent`

## Modification guidance

- Change probe evidence policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/probe_evidence.py](../../../../../../src/learnloop/diagnosis/probe_evidence.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
