---
title: "learnloop.attempts.ai_contracts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/ai_contracts.py"
source_paths:
  - "src/learnloop/attempts/ai_contracts.py"
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
  - "learnloop.attempts.ai_contracts module"
  - "src/learnloop/attempts/ai_contracts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.ai_contracts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.ai_contracts` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: Feature-owned structured grading contract.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/ai_contracts.py](../../../../../../src/learnloop/attempts/ai_contracts.py) |
| Source lines | 577 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class CriterionEvidence(WireModel)` ([source](../../../../../../src/learnloop/attempts/ai_contracts.py), line 13)
- `class FirstDivergence(WireModel)` ([source](../../../../../../src/learnloop/attempts/ai_contracts.py), line 23)
  - `validate_offsets(self) -> 'FirstDivergence'` (line 34; public)
- `class FacetContrast(WireModel)` ([source](../../../../../../src/learnloop/attempts/ai_contracts.py), line 50)
  - `validate_contrast(self) -> 'FacetContrast'` (line 56; public)
- `class PostdictiveClaim(WireModel)` ([source](../../../../../../src/learnloop/attempts/ai_contracts.py), line 66)
- `class RepairedTrace(WireModel)` ([source](../../../../../../src/learnloop/attempts/ai_contracts.py), line 71) — A minimal, auditable edit of the learner's displayed reasoning.
  - `validate_minimal_edit(self) -> 'RepairedTrace'` (line 83; public)
- `class RepairVerificationRequest(WireModel)` ([source](../../../../../../src/learnloop/attempts/ai_contracts.py), line 91) — A request for a backend verifier, never a model-supplied verdict.
- `class ErrorAttribution(WireModel)` ([source](../../../../../../src/learnloop/attempts/ai_contracts.py), line 105)
  - `validate_abstention(self) -> 'ErrorAttribution'` (line 142; public)
- `class RepairSuggestion(WireModel)` ([source](../../../../../../src/learnloop/attempts/ai_contracts.py), line 154)
  - `validate_eliciting(self) -> 'RepairSuggestion'` (line 183; public) — Structural only.
- `class ExercisedFacetObservation(WireModel)` ([source](../../../../../../src/learnloop/attempts/ai_contracts.py), line 207) — One facet the grader saw *exercised* in the trace (Meas §3.A6).
- `class ClarificationRequest(WireModel)` ([source](../../../../../../src/learnloop/attempts/ai_contracts.py), line 235) — One question to the learner that would resolve a hedged grade (Meas §3.A8).
- `class DiscriminationProfileMatch(WireModel)` ([source](../../../../../../src/learnloop/attempts/ai_contracts.py), line 265) — Which authored candidate profile the trace matches -- or none (Meas §3.A5).
  - `validate_match(self) -> 'DiscriminationProfileMatch'` (line 296; public)
- `class ReportedError(WireModel)` ([source](../../../../../../src/learnloop/attempts/ai_contracts.py), line 302) — One error the learner claims to have found in an A3 worked solution.
- `class ErrorHuntReport(WireModel)` ([source](../../../../../../src/learnloop/attempts/ai_contracts.py), line 334) — What the learner found and repaired in an A3 item (Meas §3.A3).
- `class GradingContext` ([source](../../../../../../src/learnloop/attempts/ai_contracts.py), line 347)
- `class GradingProposal(WireModel)` ([source](../../../../../../src/learnloop/attempts/ai_contracts.py), line 367)
- `grading_prompt(context: GradingContext) -> str` ([source](../../../../../../src/learnloop/attempts/ai_contracts.py), line 390) — Render the grading request owned by the attempts domain.

### Module constants

- `ELICITING_REVEAL_BUDGET_DEFAULT` ([src/learnloop/attempts/ai_contracts.py](../../../../../../src/learnloop/attempts/ai_contracts.py), line 151)
- `GRADING_PROMPT_VERSION` ([src/learnloop/attempts/ai_contracts.py](../../../../../../src/learnloop/attempts/ai_contracts.py), line 385)

### Explicit exports

`__all__` declares:

- `GRADING_PROMPT_VERSION`
- `GradingContext`
- `GradingProposal`
- `grading_prompt`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `GRADING_PROMPT_VERSION`, `GradingProposal`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `CriterionEvidence`, `GradingContext`, `GradingProposal`, `grading_prompt`; statically calls `CriterionEvidence`, `GradingContext`, `GradingProposal`, `grading_prompt`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `GRADING_PROMPT_VERSION`
- [[Reference/Modules/learnloop/diagnosis/ai_contracts|learnloop.diagnosis.ai_contracts]] — imports `GRADING_PROMPT_VERSION`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_augmentation|learnloop.diagnosis.diagnostic_augmentation]] — imports `GRADING_PROMPT_VERSION`, `GradingContext`, `GradingProposal`
- [[Reference/Modules/learnloop/diagnosis/missing_vocabulary|learnloop.diagnosis.missing_vocabulary]] — imports `GRADING_PROMPT_VERSION`
- [[Reference/Modules/learnloop/diagnosis/taxonomy_regrade|learnloop.diagnosis.taxonomy_regrade]] — imports `GRADING_PROMPT_VERSION`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `CriterionEvidence`, `GradingContext`, `GradingProposal`; statically calls `CriterionEvidence`, `GradingContext`, `GradingProposal`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `AttributionTargetRef`, `CandidateCause`, `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]], [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]], [[Reference/Modules/learnloop/diagnosis/ai_contracts|learnloop.diagnosis.ai_contracts]], [[Reference/Modules/learnloop/diagnosis/diagnostic_augmentation|learnloop.diagnosis.diagnostic_augmentation]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/structured_ai.py](../../../../../../tests/structured_ai.py) — direct import
- [tests/test_agent_run_tokens.py](../../../../../../tests/test_agent_run_tokens.py) — direct import
- [tests/test_anchor_resolution.py](../../../../../../tests/test_anchor_resolution.py) — direct import
- [tests/test_attempt_ai_flow.py](../../../../../../tests/test_attempt_ai_flow.py) — direct import
- [tests/test_causal_attribution_p0.py](../../../../../../tests/test_causal_attribution_p0.py) — direct import
  - `test_grading_schema_is_prose_first`
  - `test_missing_step_divergence_must_reference_authored_checkpoint`
  - `test_partial_credit_is_positive_projection_evidence_but_not_firewall_protection`
  - `test_passed_facet_and_repair_targets_are_blocked`
  - `test_passed_typed_target_is_blocked_and_resolution_reopens`
- [tests/test_codex_attempt_flow.py](../../../../../../tests/test_codex_attempt_flow.py) — direct import
  - `test_codex_attempt_uses_highest_severity_error_for_observed_joint`
  - `test_codex_blank_attempt_is_flagged_for_manual_review`
  - `test_codex_graded_attempt_proposes_unknown_error_type`
  - `test_codex_graded_attempt_uses_same_update_path_with_tier_three_evidence`
  - `test_codex_recall_wording_uses_recall_failure_not_new_error_type`
- [tests/test_codex_grading_validation.py](../../../../../../tests/test_codex_grading_validation.py) — direct import
  - `test_codex_score_and_max_are_derived_from_criterion_points`
  - `test_repair_suggestion_target_families_are_canonicalized`
  - `test_unknown_repair_suggestion_target_family_routes_to_manual_review`
- [tests/test_codex_http_client.py](../../../../../../tests/test_codex_http_client.py) — direct import
  - `test_http_codex_client_health_and_grading_round_trip`
- [tests/test_codex_output_schema.py](../../../../../../tests/test_codex_output_schema.py) — direct import
  - `test_codex_grading_schema_is_strict_response_format_compatible`
  - `test_discriminated_target_ref_is_a_flat_nullable_any_of`
  - `test_discriminated_target_ref_still_round_trips_after_sanitizing`
- [tests/test_deferred_regrade.py](../../../../../../tests/test_deferred_regrade.py) — direct import
  - `test_deferred_regrade_replays_targeted_error_attribution_facets`
- [tests/test_diagnostic_augmentation.py](../../../../../../tests/test_diagnostic_augmentation.py) — direct import
  - `test_c3_disagreement_becomes_unresolved_cause_set_and_real_support`
- [tests/test_dialogue_causal_join.py](../../../../../../tests/test_dialogue_causal_join.py) — direct import
  - `test_candidate_cause_round_trips_new_fields_and_accepts_legacy_payloads`
  - `test_eliciting_operator_validation_is_structural_only`
  - `test_grading_proposal_accepts_a_candidate_set_with_weights`
  - `test_question_join_records_prediction_and_appends_a_dialogue_hypothesis`
- [tests/test_discrimination_profiles.py](../../../../../../tests/test_discrimination_profiles.py) — direct import
  - `test_a_match_naming_an_unknown_profile_is_not_coerced_onto_the_nearest`
  - `test_a_match_without_a_trace_citation_is_refused`
  - `test_no_profile_applies_is_recorded_and_reaches_the_audit_report`
  - `test_no_profile_applies_is_representable_in_the_wire_schema`
  - `test_the_four_outcome_arms_are_total_over_one_attempt`
  - `test_the_telemetry_survives_a_derived_state_rebuild`
- [tests/test_e2e_codex_mock.py](../../../../../../tests/test_e2e_codex_mock.py) — direct import
- [tests/test_error_hunt_items.py](../../../../../../tests/test_error_hunt_items.py) — direct import
  - `test_a_repeated_false_positive_increments_the_same_candidate`
  - `test_a_seeded_error_hunt_still_writes_ordinary_facet_evidence`
  - `test_a_wrong_repair_is_not_credited_as_a_repair`
  - `test_clean_solution_false_positive_writes_a_candidate_not_a_facet_failure`
  - `test_repeats_on_one_solution_stay_one_observation_and_do_not_promote`
  - `test_the_repair_is_required_not_the_flag`
- [tests/test_km4_taxonomy.py](../../../../../../tests/test_km4_taxonomy.py) — direct import
  - `test_grader_prompt_version_bumped`
- [tests/test_learner_review_system_entries.py](../../../../../../tests/test_learner_review_system_entries.py) — direct import
- [tests/test_openai_chat_client.py](../../../../../../tests/test_openai_chat_client.py) — direct import
- [tests/test_openrouter_client.py](../../../../../../tests/test_openrouter_client.py) — direct import
- [tests/test_probe_audit.py](../../../../../../tests/test_probe_audit.py) — direct import
- [tests/test_repair_splice.py](../../../../../../tests/test_repair_splice.py) — direct import
- [tests/test_structured_transport_parity.py](../../../../../../tests/test_structured_transport_parity.py) — direct import
- [tests/test_teach_back.py](../../../../../../tests/test_teach_back.py) — direct import
  - `test_repaired_answer_is_composed_from_verbatim_prefix_and_regenerated_work`
  - `test_repaired_answer_without_regenerated_work_still_requires_exact_prefix`

## Modification guidance

- Change feature context, prompt assembly, result models, and operation purposes here; keep provider mechanics in `learnloop.ai`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/ai_contracts.py](../../../../../../src/learnloop/attempts/ai_contracts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
