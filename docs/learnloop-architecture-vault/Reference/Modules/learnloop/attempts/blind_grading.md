---
title: "learnloop.attempts.blind_grading"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/blind_grading.py"
source_paths:
  - "src/learnloop/attempts/blind_grading.py"
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
  - "learnloop.attempts.blind_grading module"
  - "src/learnloop/attempts/blind_grading.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.blind_grading`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.blind_grading` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: The learner-blind grading contract (Slice 1 §4).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/blind_grading.py](../../../../../../src/learnloop/attempts/blind_grading.py) |
| Source lines | 783 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `split_grading_active(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/attempts/blind_grading.py), line 75) — Does this vault grade NEW practice attempts blind (spec §6.2)?
- `class BlindGradingContext` ([source](../../../../../../src/learnloop/attempts/blind_grading.py), line 120) — Today's grading context WITHOUT ``diagnostic_history`` (§4.1).
- `blind_context_payload(context: 'BlindGradingContext') -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/blind_grading.py), line 155) — The context as rendered and hashed; an absent policy or prompt is omitted.
- `class BlindRepairedTrace(WireModel)` ([source](../../../../../../src/learnloop/attempts/blind_grading.py), line 166) — A minimal edit of THIS answer, with an id the diagnoser's repairs cite.
  - `validate_minimal_edit(self) -> 'BlindRepairedTrace'` (line 180; public)
- `class BlindErrorAttribution(WireModel)` ([source](../../../../../../src/learnloop/attempts/blind_grading.py), line 188) — Localization of one failure, without any causal claim (§4.2 "G" rows).
  - `validate_abstention(self) -> 'BlindErrorAttribution'` (line 206; public)
- `class BlindGradingProposal(WireModel)` ([source](../../../../../../src/learnloop/attempts/blind_grading.py), line 212) — §4.2 output.
- `class StuckBlindGradingProposal(BlindGradingProposal)` ([source](../../../../../../src/learnloop/attempts/blind_grading.py), line 232) — The blind wire model for a stuck answer: the shared fields, then the grader's :class:`StuckReading` LAST (it never moves a criterion).
  - `as_blind_proposal(self) -> BlindGradingProposal` (line 238; public)
- `blind_grading_context(vault: LoadedVault, item: PracticeItem, *, attempt_id: str, learner_answer_md: str, rubric: Rubric | None=None, assessment_contract: dict[str, Any] | None=None, verifier_observations: list[dict[str, Any]] | None=None, clarification_exchange: dict[str, str] | None=None) -> BlindGradingContext` ([source](../../../../../../src/learnloop/attempts/blind_grading.py), line 244) — Build the blind context from the item contract and this answer only.
- `blind_context_from_grading_context(context: GradingContext, *, verifier_observations: list[dict[str, Any]] | None=None, clarification_exchange: dict[str, str] | None=None, reference_policy: dict[str, Any] | None=None, answer_prompt: dict[str, Any] | None=None) -> BlindGradingContext` ([source](../../../../../../src/learnloop/attempts/blind_grading.py), line 277) — Copy every item-side field; ``diagnostic_history`` has nowhere to go.
- `blind_grading_context_hash(context: BlindGradingContext) -> str` ([source](../../../../../../src/learnloop/attempts/blind_grading.py), line 319) — Content address of exactly what the blind grader was shown.
- `blind_prompt_version(context: BlindGradingContext) -> str` ([source](../../../../../../src/learnloop/attempts/blind_grading.py), line 425) — mvp-2.0 without a reference policy; mvp-2.1 (PF-c) with one, plus ``+own-route-v1`` when the policy carries the own-route rules (mvp-0.20) or ``+own-route-v2`` when it carries the method-explicit successor's; any of them with the ``+stuck-v1`` suffix when the answer came from "I…
- `blind_grading_prompt(context: BlindGradingContext) -> str` ([source](../../../../../../src/learnloop/attempts/blind_grading.py), line 449) — Render the blind grading request (§4.3; PF-c rules when a policy is set, and the own-route rules when it carries them; the stuck-prompt rules when the answer came from "I'm stuck").
- `request_blind_grading_proposal(client: OperationClient, context: BlindGradingContext) -> BlindGradingProposal` ([source](../../../../../../src/learnloop/attempts/blind_grading.py), line 471) — Run the blind grading operation on a structured provider.
- `taxonomy_misconception_prior(vault: LoadedVault, error_type: str) -> bool` ([source](../../../../../../src/learnloop/attempts/blind_grading.py), line 519) — O2: at grade time ``is_misconception`` is the taxonomy prior only.
- `to_grading_proposal(proposal: BlindGradingProposal, *, vault: LoadedVault | None=None) -> GradingProposal` ([source](../../../../../../src/learnloop/attempts/blind_grading.py), line 526) — The §4.2 mapping onto the joint shape, with every causal field empty.
- `class ValidatedBlindGrade` ([source](../../../../../../src/learnloop/attempts/blind_grading.py), line 602) — A validated blind grade plus the blind-only fields the joint shape lacks.
  - `attributions(self) -> list[dict[str, Any]]` (line 617; public) — Grader-owned attribution fields only; no causal field exists here.
  - `as_record(self) -> dict[str, Any]` (line 652; public) — The persisted blind-grade record the diagnosis context reads.
- `validate_blind_grading_proposal(proposal: BlindGradingProposal, *, attempt_id: str, item: PracticeItem, vault: LoadedVault, learner_answer_md: str | None=None, rubric: Rubric | None=None) -> ValidatedBlindGrade` ([source](../../../../../../src/learnloop/attempts/blind_grading.py), line 687) — Validate through the joint validator, minus causal fields (§3).

### Module constants

- `BLIND_GRADING_PROMPT_VERSION` ([src/learnloop/attempts/blind_grading.py](../../../../../../src/learnloop/attempts/blind_grading.py), line 66)
- `BLIND_CALIBRATION_PROMPT_VERSION` ([src/learnloop/attempts/blind_grading.py](../../../../../../src/learnloop/attempts/blind_grading.py), line 70)
- `BLIND_GRADER_OUTPUT_SCHEMA_VERSION` ([src/learnloop/attempts/blind_grading.py](../../../../../../src/learnloop/attempts/blind_grading.py), line 71)
- `GRADER_MODE_BLIND` ([src/learnloop/attempts/blind_grading.py](../../../../../../src/learnloop/attempts/blind_grading.py), line 73)
- `VALIDITY_SCOPES` ([src/learnloop/attempts/blind_grading.py](../../../../../../src/learnloop/attempts/blind_grading.py), line 98)
- `_SCOPE_FOR_VALIDITY` ([src/learnloop/attempts/blind_grading.py](../../../../../../src/learnloop/attempts/blind_grading.py), line 109)
- `_BLIND_REPAIR_PRACTICE_MODE` ([src/learnloop/attempts/blind_grading.py](../../../../../../src/learnloop/attempts/blind_grading.py), line 116)
- `_BLIND_TASK` ([src/learnloop/attempts/blind_grading.py](../../../../../../src/learnloop/attempts/blind_grading.py), line 328)

### Explicit exports

`__all__` declares:

- `BLIND_CALIBRATION_PROMPT_VERSION`
- `BLIND_GRADER_OUTPUT_SCHEMA_VERSION`
- `BLIND_GRADING_PROMPT_VERSION`
- `GRADER_MODE_BLIND`
- `VALIDITY_SCOPES`
- `BlindErrorAttribution`
- `BlindGradingContext`
- `BlindGradingProposal`
- `BlindRepairedTrace`
- `StuckBlindGradingProposal`
- `ValidatedBlindGrade`
- `blind_context_from_grading_context`
- `blind_grading_context`
- `blind_grading_context_hash`
- `blind_context_payload`
- `blind_grading_prompt`
- `blind_prompt_version`
- `request_blind_grading_proposal`
- `split_grading_active`
- `taxonomy_misconception_prior`
- `to_grading_proposal`
- `validate_blind_grading_proposal`

## Internal implementation anchors

- `_cause_scope_for(validity_scope: str) -> str` ([source](../../../../../../src/learnloop/attempts/blind_grading.py), line 515)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `BLIND_CALIBRATION_PROMPT_VERSION`, `BLIND_GRADER_OUTPUT_SCHEMA_VERSION`, `blind_context_from_grading_context`, `blind_grading_context_hash`, `blind_grading_prompt`, `blind_prompt_version`, `split_grading_active`, `to_grading_proposal`, `validate_blind_grading_proposal`; statically calls `blind_context_from_grading_context`, `blind_grading_context_hash`, `blind_grading_prompt`, `blind_prompt_version`, `split_grading_active`, `to_grading_proposal`, `validate_blind_grading_proposal`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `BLIND_CALIBRATION_PROMPT_VERSION`, `BLIND_GRADER_OUTPUT_SCHEMA_VERSION`, `blind_context_from_grading_context`, `blind_grading_context_hash`, `blind_prompt_version`, `request_blind_grading_proposal`, `split_grading_active`, `to_grading_proposal`; statically calls `blind_context_from_grading_context`, `blind_grading_context_hash`, `blind_prompt_version`, `request_blind_grading_proposal`, `split_grading_active`, `to_grading_proposal`
- [[Reference/Modules/learnloop/attempts/grading_support|learnloop.attempts.grading_support]] — imports `BlindErrorAttribution`, `BlindGradingContext`, `BlindGradingProposal`, `BlindRepairedTrace`, `StuckBlindGradingProposal`, `blind_grading_prompt`, `blind_prompt_version`, `validate_blind_grading_proposal`; statically calls `blind_grading_prompt`, `blind_prompt_version`, `validate_blind_grading_proposal`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `BLIND_GRADER_OUTPUT_SCHEMA_VERSION`, `split_grading_active`, `validate_blind_grading_proposal`; statically calls `split_grading_active`, `validate_blind_grading_proposal`
- [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]] — imports `BlindGradingContext`, `blind_grading_context`, `blind_grading_context_hash`, `blind_grading_prompt`, `blind_prompt_version`, `request_blind_grading_proposal`, `validate_blind_grading_proposal`; statically calls `blind_grading_context`, `blind_grading_context_hash`, `blind_grading_prompt`, `blind_prompt_version`, `request_blind_grading_proposal`, `validate_blind_grading_proposal`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `split_grading_active`; statically calls `split_grading_active`
- [[Reference/Modules/learnloop/diagnosis/grading_hardcases|learnloop.diagnosis.grading_hardcases]] — imports `BlindGradingContext`, `blind_context_from_grading_context`, `blind_grading_prompt`, `blind_prompt_version`; statically calls `blind_context_from_grading_context`, `blind_grading_prompt`, `blind_prompt_version`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `BLIND_GRADING_PROMPT_VERSION`, `blind_grading_context`, `blind_grading_context_hash`, `blind_grading_prompt`, `request_blind_grading_proposal`, `validate_blind_grading_proposal`; statically calls `blind_grading_context`, `blind_grading_context_hash`, `blind_grading_prompt`, `request_blind_grading_proposal`, `validate_blind_grading_proposal`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `split_grading_active`; statically calls `split_grading_active`
- [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]] — imports `GRADER_MODE_BLIND`
- [[Reference/Modules/learnloop/diagnosis/split/pfc_report|learnloop.diagnosis.split.pfc_report]] — imports `BLIND_GRADING_PROMPT_VERSION`, `blind_grading_context`, `blind_grading_prompt`, `validate_blind_grading_proposal`; statically calls `blind_grading_context`, `blind_grading_prompt`, `validate_blind_grading_proposal`
- [[Reference/Modules/learnloop/diagnosis/taxonomy_regrade|learnloop.diagnosis.taxonomy_regrade]] — imports `BLIND_GRADING_PROMPT_VERSION`, `split_grading_active`; statically calls `split_grading_active`
- [[Reference/Modules/learnloop/ops/embedding_compare|learnloop.ops.embedding_compare]] — imports `BLIND_GRADING_PROMPT_VERSION`, `BlindGradingProposal`, `blind_grading_context`, `blind_grading_prompt`; statically calls `blind_grading_context`, `blind_grading_prompt`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `AttributionTargetRef`, `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `OperationClient`, `execute_structured_operation`, `render_structured_prompt`; calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `DIAGNOSIS_SPLIT_VERSIONS`
- [[Reference/Modules/learnloop/attempts/ai_contracts|learnloop.attempts.ai_contracts]] — imports `ClarificationRequest`, `CriterionEvidence`, `DiscriminationProfileMatch`, `ErrorAttribution`, `ErrorHuntReport`, `ExercisedFacetObservation`, `FacetContrast`, `FirstDivergence`, `GradingContext`, `GradingProposal`, `RepairSuggestion`, `RepairVerificationRequest`, `RepairedTrace`; calls `ErrorAttribution`, `GradingProposal`, `RepairSuggestion`, `RepairedTrace`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `GradingValidationError`, `ValidatedCodexGrade`, `build_grading_context`, `resolved_rubric`, `validate_codex_grading_proposal`; calls `GradingValidationError`, `build_grading_context`, `resolved_rubric`, `validate_codex_grading_proposal`
- [[Reference/Modules/learnloop/attempts/grading_support|learnloop.attempts.grading_support]] — imports `REFERENCE_POLICY_PROMPT_VERSION`, `REFERENCE_POLICY_RULES`, `blind_result_model`, `route_rules_suffix`, `route_rules_text`; calls `blind_result_model`, `route_rules_suffix`, `route_rules_text`
- [[Reference/Modules/learnloop/attempts/stuck|learnloop.attempts.stuck]] — imports `STUCK_PROMPT_RULES`, `STUCK_PROMPT_VERSION_SUFFIX`, `StuckReading`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`, `Rubric`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `json`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]], [[Reference/Modules/learnloop/attempts/grading_support|learnloop.attempts.grading_support]], [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]], [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]] and 8 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/diagnosis_fakes.py](../../../../../../tests/diagnosis_fakes.py) — direct import
- [tests/http_provider_double.py](../../../../../../tests/http_provider_double.py) — direct import
- [tests/route_rules_in_grader_helpers.py](../../../../../../tests/route_rules_in_grader_helpers.py) — direct import
- [tests/structured_ai.py](../../../../../../tests/structured_ai.py) — direct import
- [tests/teacher_fakes.py](../../../../../../tests/teacher_fakes.py) — direct import
- [tests/test_ai_compare.py](../../../../../../tests/test_ai_compare.py) — direct import
  - `test_grading_reads_the_contract_the_answer_was_graded_under`
- [tests/test_approach_map_boundaries.py](../../../../../../tests/test_approach_map_boundaries.py) — direct import
  - `test_grading_prompts_never_carry_or_read_a_stored_map`
- [tests/test_blind_grading_contract.py](../../../../../../tests/test_blind_grading_contract.py) — direct import
  - `test_a_joint_context_with_history_gives_a_blind_context_and_prompt_without_it`
  - `test_blind_context_has_no_history_capable_field`
  - `test_blind_prompt_drops_every_causal_instruction`
  - `test_dangling_repaired_trace_reference_is_dropped`
  - `test_field_mapping_onto_the_joint_shape`
  - `test_generation_order_is_local_analysis_then_traces_then_facets_last`
  - `test_rendered_blind_prompt_contains_no_prior_attempt_or_hypothesis`
  - `test_request_uses_the_blind_operation_and_hash_is_stable`
  - `test_shared_fakes_answer_the_blind_and_diagnosis_purposes`
  - `test_validator_accepts_reanchors_and_keeps_blind_fields`
  - `test_validator_rejects_unknown_criterion_and_duplicate_trace_ids`
- [tests/test_embedding_compare.py](../../../../../../tests/test_embedding_compare.py) — direct import
- [tests/test_forecast_receipts.py](../../../../../../tests/test_forecast_receipts.py) — direct import
- [tests/test_grading_support.py](../../../../../../tests/test_grading_support.py) — direct import
  - `test_grading_support_kill_switch_restores_the_mvp_2_0_blind_prompt`
  - `test_reference_policy_is_item_side_and_deterministic`
  - `test_request_blind_grading_run_samples_and_gates`
- [tests/test_held_grade_evidence.py](../../../../../../tests/test_held_grade_evidence.py) — direct import
- [tests/test_help_assist_work_md_migration.py](../../../../../../tests/test_help_assist_work_md_migration.py) — direct import
  - `test_a_served_hint_keeps_the_draft_it_answered_and_the_grader_never_sees_it`
- [tests/test_hint_blind.py](../../../../../../tests/test_hint_blind.py) — direct import
  - `test_the_blind_context_has_no_field_for_hints_or_learner_state`
  - `test_the_blind_prompt_of_a_hinted_attempt_carries_no_hint_map_placement_or_state`
- [tests/test_hint_discriminating.py](../../../../../../tests/test_hint_discriminating.py) — direct import
  - `test_the_answer_is_an_assist_row_that_moves_nothing_and_never_reaches_the_grader`
- [tests/test_learner_blindness_relax.py](../../../../../../tests/test_learner_blindness_relax.py) — direct import
  - `test_the_blind_graders_context_is_byte_identical_in_every_arm_and_switch_setting`
- [tests/test_learner_data_relax_2.py](../../../../../../tests/test_learner_data_relax_2.py) — direct import
  - `test_the_blind_grader_inputs_are_unchanged`
- [tests/test_method_explicit_upgrade.py](../../../../../../tests/test_method_explicit_upgrade.py) — direct import
  - `test_each_version_activates_exactly_its_features`
- [tests/test_mvp010_upgrade.py](../../../../../../tests/test_mvp010_upgrade.py) — direct import
  - `test_kill_switch_keeps_the_version_but_grades_joint`
  - `test_upgrade_flips_rebuilds_and_preserves_raw_history`
- [tests/test_mvp011_upgrade.py](../../../../../../tests/test_mvp011_upgrade.py) — direct import
  - `test_new_vaults_start_at_the_latest_version`
  - `test_split_and_placement_activate_at_the_right_versions`
  - `test_upgrade_from_mvp010_flips_rebuilds_and_preserves_history_and_open_episodes`
  - `test_upgrade_from_mvp09_chains_through_the_split`
- [tests/test_mvp013_upgrade.py](../../../../../../tests/test_mvp013_upgrade.py) — direct import
  - `test_kill_switch_keeps_the_version_and_every_predecessor`
  - `test_only_mvp013_offers_the_stuck_control`
  - `test_upgrade_from_mvp012_flips_rebuilds_and_preserves_raw_history`
- [tests/test_mvp014_upgrade.py](../../../../../../tests/test_mvp014_upgrade.py) — direct import
  - `test_the_plan_serves_only_at_the_successor_with_the_switch_on`
  - `test_upgrade_from_mvp013_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp015_upgrade.py](../../../../../../tests/test_mvp015_upgrade.py) — direct import
  - `test_each_version_activates_exactly_its_features`
- [tests/test_mvp016_upgrade.py](../../../../../../tests/test_mvp016_upgrade.py) — direct import
  - `test_each_version_activates_exactly_its_features`
- [tests/test_mvp017_upgrade.py](../../../../../../tests/test_mvp017_upgrade.py) — direct import
  - `test_each_version_activates_exactly_its_features`
- [tests/test_mvp020_upgrade.py](../../../../../../tests/test_mvp020_upgrade.py) — direct import
  - `test_each_version_activates_exactly_its_features`
- [tests/test_mvp021_upgrade.py](../../../../../../tests/test_mvp021_upgrade.py) — direct import
- [tests/test_pfc_unverified_unassessed.py](../../../../../../tests/test_pfc_unverified_unassessed.py) — direct import
  - `test_a_located_error_beside_an_unverified_criterion_still_counts`
- [tests/test_placement_split_grades.py](../../../../../../tests/test_placement_split_grades.py) — direct import
- [tests/test_reading_step_switch.py](../../../../../../tests/test_reading_step_switch.py) — direct import
  - `test_the_reading_step_acts_wherever_the_plan_acts_behind_its_switch`
- [tests/test_recurrence_commands.py](../../../../../../tests/test_recurrence_commands.py) — direct import
  - `test_the_upgrade_chains_from_each_predecessor`
- [tests/test_required_method_grading.py](../../../../../../tests/test_required_method_grading.py) — direct import
  - `test_a_quoted_wrong_step_in_the_method_still_counts`
  - `test_off_and_at_the_predecessor_the_prompt_is_the_predecessors_byte_for_byte`
  - `test_the_prompt_carries_the_required_method_and_names_v2`
- [tests/test_route_rules_in_grader.py](../../../../../../tests/test_route_rules_in_grader.py) — direct import
  - `test_the_prompt_carries_the_rules_and_names_them_only_at_the_successor`
- [tests/test_teach_back.py](../../../../../../tests/test_teach_back.py) — direct import
- [tests/test_teacher_te0_confidence_events.py](../../../../../../tests/test_teacher_te0_confidence_events.py) — direct import
  - `test_the_blind_grader_never_reads_a_tap_or_a_hedge_read`
- [tests/test_teacher_te2_landing_r1.py](../../../../../../tests/test_teacher_te2_landing_r1.py) — direct import
  - `test_a_lesson_probe_regraded_blind_after_split_is_switched_on_carries_the_blind_calibration`
  - `test_a_lesson_probe_regraded_blind_under_a_newer_prompt_carries_the_newer_calibration`
  - `test_an_ordinary_practice_regrade_already_carries_the_newer_calibration`
  - `test_fg1s_presentation_path_stamps_the_submissions_identity_and_its_regrade_the_replacements`
- [tests/test_teacher_te2_review_fixes.py](../../../../../../tests/test_teacher_te2_review_fixes.py) — direct import
  - `test_f7_a_blind_lesson_probe_grade_keeps_the_blind_calibration_identity`

## Modification guidance

- Change blind grading policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/blind_grading.py](../../../../../../src/learnloop/attempts/blind_grading.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
