---
title: "learnloop.diagnosis.diagnostic_augmentation"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/diagnostic_augmentation.py"
source_paths:
  - "src/learnloop/diagnosis/diagnostic_augmentation.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.diagnostic_augmentation module"
  - "src/learnloop/diagnosis/diagnostic_augmentation.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.diagnostic_augmentation`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.diagnostic_augmentation` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Stage 7 diagnostic evaluation and Phase-C diagnosis augmentation.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/diagnostic_augmentation.py](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py) |
| Source lines | 1240 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `normalize_semantic_key(value: Any) -> str` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 147)
- `model_family(provider: str | None, model: str | None) -> str` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 151) — Conservative B3 family identity.
- `class PlantedDiagnosticCase` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 184)
  - `__post_init__(self) -> None` (line 199; internal)
- `class DiagnosisSample` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 215)
- `class DiagnosisConsensus` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 225) — One live diagnosis, plus whatever agreement (if any) was measured.
  - `disagreed(self) -> bool` (line 244; public)
  - `receipt_agreement_support(self) -> float` (line 248; public) — The receipt column's non-null float (migration 144 is NOT NULL).
  - `as_dict(self) -> dict[str, Any]` (line 258; public)
- `class DiagnosticEvalReport` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 281)
  - `as_dict(self) -> dict[str, Any]` (line 292; public)
- `diagnostic_verifier_observations(learner_answer_md: str, expected_answer: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 307) — C2 verifier instrument over the submitted answer.
- `diagnostic_history_context(vault: LoadedVault, repository: Repository, item: PracticeItem, *, limit: int=DEFAULT_HISTORY_LIMIT) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 331) — C4 raw prior traces on the same facet and surface family.
- `augment_grading_context(vault: LoadedVault, repository: Repository, item: PracticeItem, context: GradingContext, *, history_limit: int=DEFAULT_HISTORY_LIMIT) -> GradingContext` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 382) — Attach C2/C4 evidence before the model call.
- `run_diagnosis_samples(client: Any, context: GradingContext, *, sample_count: int=DEFAULT_DIAGNOSIS_SAMPLES) -> DiagnosisConsensus` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 503) — C3 k independent calls, modal answer, and a disagreement cause set.
- `cases_from_discrimination_profiles(vault: LoadedVault) -> list[PlantedDiagnosticCase]` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 610) — Turn A5 profiles into authored ground truth, without a model labeler.
- `planted_cases_from_manifest(payload: Any) -> list[PlantedDiagnosticCase]` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 652) — Parse the explicit JSON boundary used by the commissioning CLI.
- `run_planted_diagnostic_evaluation(vault: LoadedVault, repository: Repository, *, generator_client: Any, diagnostician_client: Any, cases: Sequence[PlantedDiagnosticCase] | None=None, sample_count: int=EVAL_DIAGNOSIS_SAMPLES, personas_pre_generated: bool=False, clock: Clock | None=None) -> DiagnosticEvalReport` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 896) — B1/B3 live-path evaluation, blind to the planted cause.
- `commission_planted_diagnostic_evaluation(vault: LoadedVault, repository: Repository, *, generator_client: Any, diagnostician_client: Any, cases: Sequence[PlantedDiagnosticCase] | None=None, real_traces: Sequence[str] | None=None, sample_count: int=EVAL_DIAGNOSIS_SAMPLES, separation_threshold: float=0.7, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 1074) — Generate once, run B2 on those exact traces, then score them in B1.
- `record_phase_c_receipt(repository: Repository, *, attempt_id: str, context: GradingContext, consensus: DiagnosisConsensus, grader_provider: str | None, grader_model: str | None, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 1165) — Append the hypothesis/revert manifest for one live augmented diagnosis.
- `diagnostic_augmentation_report(repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 1203) — Read-only Stage-7 report, grouped by the version pins persisted at source.

### Module constants

- `DIAGNOSTIC_EVAL_HARNESS_VERSION` ([src/learnloop/diagnosis/diagnostic_augmentation.py](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 50)
- `PHASE_C_VERSION` ([src/learnloop/diagnosis/diagnostic_augmentation.py](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 51)
- `DEFAULT_DIAGNOSIS_SAMPLES` ([src/learnloop/diagnosis/diagnostic_augmentation.py](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 55)
- `EVAL_DIAGNOSIS_SAMPLES` ([src/learnloop/diagnosis/diagnostic_augmentation.py](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 59)
- `DEFAULT_HISTORY_LIMIT` ([src/learnloop/diagnosis/diagnostic_augmentation.py](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 60)
- `SINGLE_SAMPLE_BASIS` ([src/learnloop/diagnosis/diagnostic_augmentation.py](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 66)
- `SAMPLE_AGREEMENT_BASIS` ([src/learnloop/diagnosis/diagnostic_augmentation.py](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 67)
- `CAUSE_SCOPES` ([src/learnloop/diagnosis/diagnostic_augmentation.py](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 72)
- `LEARNER_DERIVED_CAUSE_SCOPE` ([src/learnloop/diagnosis/diagnostic_augmentation.py](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 101)
- `UNATTRIBUTED_CAUSE_SCOPE` ([src/learnloop/diagnosis/diagnostic_augmentation.py](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 108)
- `REGRESSION_SHAPES` ([src/learnloop/diagnosis/diagnostic_augmentation.py](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 110)
- `PLANTED_CASE_SOURCES` ([src/learnloop/diagnosis/diagnostic_augmentation.py](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 126)
- `PHASE_C_HYPOTHESES` ([src/learnloop/diagnosis/diagnostic_augmentation.py](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 130)
- `PHASE_C_REVERT_CRITERIA` ([src/learnloop/diagnosis/diagnostic_augmentation.py](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 137)
- `_NORMALIZE_RE` ([src/learnloop/diagnosis/diagnostic_augmentation.py](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 144)

## Internal implementation anchors

- `_primary_attribution(proposal: GradingProposal) -> Any | None` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 403)
- `_disagreement_cause_scope(attribution: Any | None) -> str` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 415) — Scope for one disagreement arm (see ``LEARNER_DERIVED_CAUSE_SCOPE``).
- `_repair_equivalence(proposal: GradingProposal) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 432)
- `_proposal_keys(proposal: GradingProposal) -> tuple[str, str | None, str | None]` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 442)
- `_sample(proposal: GradingProposal, index: int) -> DiagnosisSample` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 461)
- `_disagreement_cause(sample: DiagnosisSample, votes: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 481) — One C3 disagreement arm, carrying its own scope and target.
- `_system_abstained(proposal: GradingProposal) -> bool` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 601)
- `_generated_trace(generator_client: Any, case: PlantedDiagnosticCase, item: PracticeItem) -> str` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 744) — Use the generator model when available; never ask it to label the cause.
- `_case_result(case: PlantedDiagnosticCase, proposal: GradingProposal, consensus: DiagnosisConsensus) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 777)
- `_rate(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 840)
- `_eval_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py), line 850)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `DEFAULT_DIAGNOSIS_SAMPLES`, `DEFAULT_HISTORY_LIMIT`, `augment_grading_context`, `record_phase_c_receipt`, `run_diagnosis_samples`; statically calls `augment_grading_context`, `record_phase_c_receipt`, `run_diagnosis_samples`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `commission_planted_diagnostic_evaluation`, `diagnostic_augmentation_report`, `model_family`, `planted_cases_from_manifest`; statically calls `commission_planted_diagnostic_evaluation`, `diagnostic_augmentation_report`, `model_family`, `planted_cases_from_manifest`
- [[Reference/Modules/learnloop/content/authoring/persona_gate|learnloop.content.authoring.persona_gate]] — imports `model_family`; statically calls `model_family`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `CandidateCause`; calls `CandidateCause`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `STRUCTURED_COMPLETION`
- [[Reference/Modules/learnloop/attempts/ai_contracts|learnloop.attempts.ai_contracts]] — imports `GRADING_PROMPT_VERSION`, `GradingContext`, `GradingProposal`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `build_grading_context`, `request_grading_proposal`, `resolved_rubric`; calls `build_grading_context`, `request_grading_proposal`, `resolved_rubric`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/content/authoring/persona_realism|learnloop.content.authoring.persona_realism]] — imports `latest_realism_license`, `match_persona_realism`, `trace_corpus_hash`; calls `latest_realism_license`, `match_persona_realism`, `trace_corpus_hash`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `SympyVerifierAdapter`, `repair_equivalence_id`; calls `SympyVerifierAdapter`, `repair_equivalence_id`
- [[Reference/Modules/learnloop/diagnosis/diagnosis_adjudication|learnloop.diagnosis.diagnosis_adjudication]] — imports `anchor_key`; calls `anchor_key`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_gate|learnloop.diagnosis.diagnostic_gate]] — imports `request_diagnostic_trials`; calls `request_diagnostic_trials`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/authoring/persona_gate|learnloop.content.authoring.persona_gate]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_diagnostic_augmentation.py](../../../../../../tests/test_diagnostic_augmentation.py) — direct import
  - `test_b2_license_cannot_be_reused_for_a_different_b1_corpus`
  - `test_c3_arm_from_a_sample_with_no_attribution_stays_unknown`
  - `test_c3_default_is_one_call_and_claims_no_agreement`
  - `test_c3_disagreement_becomes_unresolved_cause_set_and_real_support`
  - `test_c3_explicit_non_learner_scope_is_preserved_on_disagreement_arms`
  - `test_c3_unscoped_disagreement_arm_defaults_to_learner_state`
  - `test_commissioning_rejects_same_family_before_persona_generation`
  - `test_licensed_b1_runs_blind_and_never_writes_a_learner_attempt`
  - `test_model_family_cannot_be_hidden_behind_a_provider_alias`
  - `test_planted_case_manifest_is_strict_and_carries_history`
  - `test_same_model_family_invalidates_b1_without_running_diagnostician`
- [tests/test_persona_gate.py](../../../../../../tests/test_persona_gate.py) — direct import
  - `test_b2_license_from_another_generator_family_stays_advisory`
  - `test_b2_license_promotes_plain_practice_advisory_failure_to_hard`

## Modification guidance

- Change diagnostic augmentation policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/diagnostic_augmentation.py](../../../../../../src/learnloop/diagnosis/diagnostic_augmentation.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
