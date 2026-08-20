---
title: "learnloop.attempts.grading"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/grading.py"
source_paths:
  - "src/learnloop/attempts/grading.py"
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
  - "learnloop.attempts.grading module"
  - "src/learnloop/attempts/grading.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.grading`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps grading behavior inside its owning package, [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]]. Its public surface centers on `request_grading_proposal`, `QuoteAnchorResolution`, `resolve_quote_anchor`, `is_canonical_state_vault`, `builtin_error_type_defaults`, `confidence_to_grader_confidence`, `GradingValidationError`, `deterministic_recognition_grade` and 11 more public symbols.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/grading.py](../../../../../../src/learnloop/attempts/grading.py) |
| Source lines | 1911 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `request_grading_proposal(client: OperationClient, context: GradingContext) -> GradingProposal` ([source](../../../../../../src/learnloop/attempts/grading.py), line 59) — Run the feature-owned grading operation on a structured provider.
- `class QuoteAnchorResolution` ([source](../../../../../../src/learnloop/attempts/grading.py), line 76)
- `resolve_quote_anchor(learner_answer: str, quote: str, *, hint_start: int | None=None, hint_end: int | None=None) -> QuoteAnchorResolution` ([source](../../../../../../src/learnloop/attempts/grading.py), line 128) — Locate ``quote`` in ``learner_answer`` and derive offsets server-side.
- `is_canonical_state_vault(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/attempts/grading.py), line 180) — Whether the vault reads/writes canonical (mvp-0.7) state.
- `builtin_error_type_defaults(vault: LoadedVault) -> dict[str, float]` ([source](../../../../../../src/learnloop/attempts/grading.py), line 261) — Version-branched builtin error-type severity defaults.
- `confidence_to_grader_confidence(confidence: int) -> float` ([source](../../../../../../src/learnloop/attempts/grading.py), line 274)
- `class GradingValidationError(ValueError)` ([source](../../../../../../src/learnloop/attempts/grading.py), line 281)
- `deterministic_recognition_grade(item, rubric, learner_answer_md: str, *, attempt_id: str) -> GradingProposal | None` ([source](../../../../../../src/learnloop/attempts/grading.py), line 296) — Exact option-letter grading for recognition/multiple-choice items.
- `class ValidatedCriterionEvidence` ([source](../../../../../../src/learnloop/attempts/grading.py), line 354)
- `class ValidatedErrorAttribution` ([source](../../../../../../src/learnloop/attempts/grading.py), line 363)
- `class ValidatedExercisedFacet` ([source](../../../../../../src/learnloop/attempts/grading.py), line 400) — One accepted A6 trace observation (Meas §3.A6).
- `class ValidatedCodexGrade` ([source](../../../../../../src/learnloop/attempts/grading.py), line 417)
- `enforce_passed_target_firewall(item: PracticeItem, rubric: Rubric, *, criterion_points: Mapping[str, float], error_attributions: Iterable[Any], repair_suggestions: Iterable[Mapping[str, Any]]=(), vault: LoadedVault | None=None) -> tuple[list[Any], list[dict[str, Any]], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/attempts/grading.py), line 512) — Strip negative/repair targets protected by raw criterion outcomes.
- `build_grading_context(vault: LoadedVault, item: PracticeItem, *, attempt_id: str, learner_answer_md: str, rubric: Rubric | None=None, assessment_contract: dict[str, Any] | None=None) -> GradingContext` ([source](../../../../../../src/learnloop/attempts/grading.py), line 674)
- `evidence_coverage(item: PracticeItem, criterion_points: dict[str, float], *, rubric: Rubric | None=None, attempt_type: str='independent_attempt', hints_used: int=0, learner_answer_md: str='__engaged_answer__', evidence: EvidenceConfig | None=None) -> float` ([source](../../../../../../src/learnloop/attempts/grading.py), line 755) — Compatibility wrapper for score-independent coverage resolution.
- `grading_context_hash(context: GradingContext) -> str` ([source](../../../../../../src/learnloop/attempts/grading.py), line 783)
- `validate_codex_grading_proposal(proposal: GradingProposal, *, attempt_id: str, item: PracticeItem, vault: LoadedVault, learner_answer_md: str | None=None, rubric: Rubric | None=None) -> ValidatedCodexGrade` ([source](../../../../../../src/learnloop/attempts/grading.py), line 806)
- `resolved_rubric(vault: LoadedVault, item: PracticeItem) -> Rubric` ([source](../../../../../../src/learnloop/attempts/grading.py), line 1713)
- `causal_attribution_audit_report(repository: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/grading.py), line 1737) — CLI-facing fill/abstention/firewall telemetry grouped by prompt+model.

### Module constants

- `ANCHOR_BASES` ([src/learnloop/attempts/grading.py](../../../../../../src/learnloop/attempts/grading.py), line 50)
- `CANONICAL_ERROR_TYPES` ([src/learnloop/attempts/grading.py](../../../../../../src/learnloop/attempts/grading.py), line 195)
- `BUILTIN_ERROR_TYPE_DEFAULTS` ([src/learnloop/attempts/grading.py](../../../../../../src/learnloop/attempts/grading.py), line 249)
- `MECHANISM_ERROR_TYPE_DEFAULTS` ([src/learnloop/attempts/grading.py](../../../../../../src/learnloop/attempts/grading.py), line 258)
- `_OPTION_LETTER` ([src/learnloop/attempts/grading.py](../../../../../../src/learnloop/attempts/grading.py), line 285)
- `_OPTION_LINE` ([src/learnloop/attempts/grading.py](../../../../../../src/learnloop/attempts/grading.py), line 286)
- `FIREWALL_CLEAN_PASS_FRACTION` ([src/learnloop/attempts/grading.py](../../../../../../src/learnloop/attempts/grading.py), line 446)
- `FIREWALL_FRACTION_EPSILON` ([src/learnloop/attempts/grading.py](../../../../../../src/learnloop/attempts/grading.py), line 447)
- `MAX_EXERCISED_FACETS_PER_ATTEMPT` ([src/learnloop/attempts/grading.py](../../../../../../src/learnloop/attempts/grading.py), line 1542)
- `PROVISIONAL_PENDING_CLARIFICATION` ([src/learnloop/attempts/grading.py](../../../../../../src/learnloop/attempts/grading.py), line 1615)
- `CLARIFICATION_CONFIDENCE_CEILING` ([src/learnloop/attempts/grading.py](../../../../../../src/learnloop/attempts/grading.py), line 1621)
- `_RECALL_FAILURE_PATTERN` ([src/learnloop/attempts/grading.py](../../../../../../src/learnloop/attempts/grading.py), line 1904)

## Internal implementation anchors

- `_collapse_whitespace_with_map(text: str) -> tuple[str, list[int]]` ([source](../../../../../../src/learnloop/attempts/grading.py), line 82) — Collapse whitespace runs to single spaces, keeping original indices.
- `_pick_occurrence(starts: list[int], hint_start: int | None) -> tuple[int, str]` ([source](../../../../../../src/learnloop/attempts/grading.py), line 108)
- `_all_occurrences(haystack: str, needle: str) -> list[int]` ([source](../../../../../../src/learnloop/attempts/grading.py), line 119)
- `_option_letter(text: str | None) -> str | None` ([source](../../../../../../src/learnloop/attempts/grading.py), line 289)
- `_criterion_outcome_state(rubric: Rubric, criterion_points: Mapping[str, float]) -> tuple[set[str], set[str]]` ([source](../../../../../../src/learnloop/attempts/grading.py), line 450) — Raw, dependency-localized criterion outcomes used by the P0 firewall.
- `_direct_criteria_by_facet(item: PracticeItem, rubric: Rubric, *, vault: LoadedVault | None=None) -> dict[str, set[str]]` ([source](../../../../../../src/learnloop/attempts/grading.py), line 476) — Criterion links eligible to protect a facet at the write barrier.
- `_grading_facet_registry(vault: LoadedVault, item: PracticeItem) -> list[dict[str, str]]` ([source](../../../../../../src/learnloop/attempts/grading.py), line 726) — Facets A6 may report as exercised, with the claim each one names.
- `_validated_exercised_facets(vault: LoadedVault, item: PracticeItem, rubric: Rubric, proposal: Any) -> list[ValidatedExercisedFacet]` ([source](../../../../../../src/learnloop/attempts/grading.py), line 1545) — Accept A6 trace observations that name a registered facet with a citation.
- `_validated_clarification(proposal: Any, validated_evidence: list[ValidatedCriterionEvidence], validated_errors: list[ValidatedErrorAttribution], rubric: Rubric | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/attempts/grading.py), line 1624) — Accept a clarification request only against a grade that is already unsure.
- `_resolved_error_severity(vault: LoadedVault, error_type: str, severity: float | None) -> float` ([source](../../../../../../src/learnloop/attempts/grading.py), line 1722)
- `_canonical_learner_confidence(value: str | None) -> str | None` ([source](../../../../../../src/learnloop/attempts/grading.py), line 1731)
- `_grading_error_taxonomy(vault: LoadedVault) -> dict[str, object]` ([source](../../../../../../src/learnloop/attempts/grading.py), line 1820)
- `_normalized_recall_error_type(vault: LoadedVault, error_type: str, *, evidence: str, learner_answer_md: str | None, is_misconception: bool) -> str` ([source](../../../../../../src/learnloop/attempts/grading.py), line 1869)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempt_trace|learnloop.attempts.attempt_trace]] — imports `resolved_rubric`; statically calls `resolved_rubric`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `GradingValidationError`, `ValidatedCodexGrade`, `ValidatedCriterionEvidence`, `ValidatedErrorAttribution`, `build_grading_context`, `confidence_to_grader_confidence`, `deterministic_recognition_grade`, `enforce_passed_target_firewall`, `evidence_coverage`, `grading_context_hash`, `resolved_rubric`, `validate_codex_grading_proposal`; statically calls `build_grading_context`, `confidence_to_grader_confidence`, `deterministic_recognition_grade`, `enforce_passed_target_firewall`, `evidence_coverage`, `grading_context_hash`, `resolved_rubric`, `validate_codex_grading_proposal`
- [[Reference/Modules/learnloop/attempts/clarification|learnloop.attempts.clarification]] — imports `PROVISIONAL_PENDING_CLARIFICATION`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `GradingValidationError`, `ValidatedCodexGrade`, `build_grading_context`, `grading_context_hash`, `request_grading_proposal`, `resolved_rubric`, `validate_codex_grading_proposal`; statically calls `build_grading_context`, `grading_context_hash`, `request_grading_proposal`, `resolved_rubric`, `validate_codex_grading_proposal`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `causal_attribution_audit_report`; statically calls `causal_attribution_audit_report`
- [[Reference/Modules/learnloop/cli/exam|learnloop.cli.exam]] — imports `GradingValidationError`, `build_grading_context`, `request_grading_proposal`, `validate_codex_grading_proposal`; statically calls `build_grading_context`, `request_grading_proposal`, `validate_codex_grading_proposal`
- [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] — imports `resolved_rubric`; statically calls `resolved_rubric`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_augmentation|learnloop.diagnosis.diagnostic_augmentation]] — imports `build_grading_context`, `request_grading_proposal`, `resolved_rubric`; statically calls `build_grading_context`, `request_grading_proposal`, `resolved_rubric`
- [[Reference/Modules/learnloop/diagnosis/error_taxonomy|learnloop.diagnosis.error_taxonomy]] — imports `ValidatedErrorAttribution`
- [[Reference/Modules/learnloop/diagnosis/probe_audit|learnloop.diagnosis.probe_audit]] — imports `build_grading_context`, `request_grading_proposal`, `validate_codex_grading_proposal`; statically calls `build_grading_context`, `request_grading_proposal`, `validate_codex_grading_proposal`
- [[Reference/Modules/learnloop/diagnosis/repair_splice|learnloop.diagnosis.repair_splice]] — imports `resolve_quote_anchor`; statically calls `resolve_quote_anchor`
- [[Reference/Modules/learnloop/diagnosis/taxonomy_regrade|learnloop.diagnosis.taxonomy_regrade]] — imports `build_grading_context`, `request_grading_proposal`, `validate_codex_grading_proposal`; statically calls `build_grading_context`, `request_grading_proposal`, `validate_codex_grading_proposal`
- [[Reference/Modules/learnloop/goals/exam_seeding|learnloop.goals.exam_seeding]] — imports `resolved_rubric`; statically calls `resolved_rubric`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `resolved_rubric`; statically calls `resolved_rubric`
- [[Reference/Modules/learnloop/sim/diagnostic_validation|learnloop.sim.diagnostic_validation]] — imports `resolved_rubric`; statically calls `resolved_rubric`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `resolved_rubric`; statically calls `resolved_rubric`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `GradingValidationError`, `build_grading_context`, `request_grading_proposal`, `resolved_rubric`, `validate_codex_grading_proposal`; statically calls `build_grading_context`, `request_grading_proposal`, `resolved_rubric`, `validate_codex_grading_proposal`
- [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]] — imports `GradingValidationError`, `build_grading_context`, `request_grading_proposal`, `validate_codex_grading_proposal`; statically calls `build_grading_context`, `request_grading_proposal`, `validate_codex_grading_proposal`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `resolved_rubric`; statically calls `resolved_rubric`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `OperationClient`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/attempts/ai_contracts|learnloop.attempts.ai_contracts]] — imports `CriterionEvidence`, `GradingContext`, `GradingProposal`, `grading_prompt`; calls `CriterionEvidence`, `GradingContext`, `GradingProposal`, `grading_prompt`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `EvidenceConfig`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `validate_repair_candidate`; calls `validate_repair_candidate`
- [[Reference/Modules/learnloop/diagnosis/discrimination_profiles|learnloop.diagnosis.discrimination_profiles]] — imports `ProfileMatchOutcome`, `item_profiles`, `profile_prior_payload`, `validate_profile_match`; calls `item_profiles`, `profile_prior_payload`, `validate_profile_match`
- [[Reference/Modules/learnloop/diagnosis/error_hunt|learnloop.diagnosis.error_hunt]] — imports `suppress_facet_failures_on_clean_solution`, `validate_error_hunt_report`; calls `suppress_facet_failures_on_clean_solution`, `validate_error_hunt_report`
- [[Reference/Modules/learnloop/diagnosis/error_taxonomy_map|learnloop.diagnosis.error_taxonomy_map]] — imports `MECHANISM_SEVERITY_DEFAULT`, `MECHANISM_TAXONOMY_CARD_JSON`, `map_legacy_error_type`; calls `map_legacy_error_type`
- [[Reference/Modules/learnloop/diagnosis/repair_splice|learnloop.diagnosis.repair_splice]] — imports `is_end_append`, `preserved_prefix_from_refs`, `splice_repaired_answer`; calls `is_end_append`, `preserved_prefix_from_refs`, `splice_repaired_answer`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `CriterionOutcome`, `localize_criterion_outcomes`; calls `CriterionOutcome`, `localize_criterion_outcomes`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `is_canonical_state_vault`; calls `is_canonical_state_vault`
- [[Reference/Modules/learnloop/learner/recall_coverage|learnloop.learner.recall_coverage]] — imports `criterion_facet_weights_for_item`, `resolve_coverage`; calls `criterion_facet_weights_for_item`, `resolve_coverage`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`, `Rubric`, `learning_object_facet_union`; calls `learning_object_facet_union`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `json`, `re`, `typing`, `unicodedata`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempt_trace|learnloop.attempts.attempt_trace]], [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/clarification|learnloop.attempts.clarification]], [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]], [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] and 14 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_agent_run_tokens.py](../../../../../../tests/test_agent_run_tokens.py) — direct import
  - `test_chat_client_accumulates_usage_across_calls_and_resets_on_consume`
  - `test_chat_client_counts_tokens_of_a_call_whose_body_is_unusable`
  - `test_chat_client_survives_a_response_with_no_usage`
- [tests/test_anchor_resolution.py](../../../../../../tests/test_anchor_resolution.py) — direct import
  - `test_absent_quote_degrades_to_unanchored`
  - `test_bases_are_the_closed_vocabulary`
  - `test_empty_inputs_are_unanchored`
  - `test_latex_escaped_content_matches_exactly`
  - `test_multiple_occurrences_pick_nearest_to_hint`
  - `test_multiple_occurrences_without_hint_take_first`
  - `test_nfc_mismatch_resolves_when_answer_is_nfc_normal`
  - `test_resolver_is_deterministic`
  - `test_unique_exact_match_uses_exact_offsets`
  - `test_whitespace_run_mismatch_resolves_normalized`
- [tests/test_causal_attribution_p0.py](../../../../../../tests/test_causal_attribution_p0.py) — direct import
  - `test_missing_step_divergence_must_reference_authored_checkpoint`
  - `test_partial_credit_is_positive_projection_evidence_but_not_firewall_protection`
  - `test_passed_facet_and_repair_targets_are_blocked`
  - `test_passed_typed_target_is_blocked_and_resolution_reopens`
- [tests/test_codex_grading_validation.py](../../../../../../tests/test_codex_grading_validation.py) — direct import
  - `test_codex_error_attribution_does_not_expand_target_criterion_to_facet`
  - `test_codex_error_attribution_passes_through_misconception_fields`
  - `test_codex_error_attribution_preserves_target_evidence_families`
  - `test_codex_error_attribution_unknown_target_family_routes_to_manual_review`
  - `test_codex_error_severity_defaults_from_taxonomy`
  - `test_codex_grade_rejects_mismatched_attempt_and_item`
  - `test_codex_grade_rejects_unknown_or_excess_criterion_and_derives_fatal_cap`
  - `test_codex_misconception_without_statement_does_not_hard_fail`
  - `test_codex_score_and_max_are_derived_from_criterion_points`
  - `test_explicit_recall_wording_normalizes_to_recall_failure`
  - `test_low_codex_grader_confidence_routes_to_manual_review`
  - `test_recall_normalization_does_not_scan_unrelated_answer_text`
  - `test_repair_suggestion_target_families_are_canonicalized`
  - `test_unanchored_known_facet_requests_review_instead_of_failing_grade`
  - `test_unknown_codex_error_type_routes_to_manual_review`
  - `test_unknown_repair_suggestion_target_family_routes_to_manual_review`
  - `test_unknown_target_criterion_routes_to_manual_review`
  - `test_valid_codex_grade_validates`
- [tests/test_codex_http_client.py](../../../../../../tests/test_codex_http_client.py) — direct import
  - `test_http_codex_client_health_and_grading_round_trip`
- [tests/test_cold_start_revision.py](../../../../../../tests/test_cold_start_revision.py) — direct import
  - `test_correct_selection_full_credit`
  - `test_free_text_defers_to_model_grader`
  - `test_non_recognition_mode_defers`
  - `test_prompt_without_options_defers`
  - `test_wrong_selection_zero`
- [tests/test_conjunctive_instruments.py](../../../../../../tests/test_conjunctive_instruments.py) — direct import
  - `test_more_than_the_per_attempt_cap_is_truncated`
- [tests/test_discrimination_profiles.py](../../../../../../tests/test_discrimination_profiles.py) — direct import
  - `test_an_item_with_no_profiles_offers_the_grader_nothing`
  - `test_no_profile_applies_is_recorded_and_reaches_the_audit_report`
  - `test_the_grading_prior_withholds_the_criteria_the_author_expects_to_fail`
  - `test_the_telemetry_survives_a_derived_state_rebuild`
- [tests/test_grading_context.py](../../../../../../tests/test_grading_context.py) — direct import
  - `test_grading_context_is_deterministic_and_hashable`
  - `test_grading_context_uses_default_rubric_when_inline_rubric_is_omitted`
  - `test_legacy_evidence_coverage_wrapper_is_score_independent`
- [tests/test_km4_taxonomy.py](../../../../../../tests/test_km4_taxonomy.py) — direct import
  - `test_mvp07_grader_taxonomy_emits_mechanism_vocabulary`
  - `test_retrieval_boundary_is_mechanism_based_and_domain_neutral`
- [tests/test_openai_chat_client.py](../../../../../../tests/test_openai_chat_client.py) — direct import
  - `test_chat_does_not_retry_non_retryable_errors`
  - `test_chat_retries_rate_limited_requests_with_backoff`
  - `test_json_schema_response_format_sends_strict_per_request_schema`
  - `test_openai_chat_client_repairs_invalid_json_once`
  - `test_openai_chat_client_sends_deepseek_json_request`
- [tests/test_openrouter_client.py](../../../../../../tests/test_openrouter_client.py) — direct import
  - `test_openrouter_attribution_headers_configurable`
  - `test_openrouter_defaults_base_url_key_env_and_title_header`
  - `test_openrouter_profile_base_url_overrides_default`
  - `test_openrouter_reasoning_effort_maps_to_unified_body`
  - `test_openrouter_thinking_disabled_sends_no_reasoning`
- [tests/test_repair_splice.py](../../../../../../tests/test_repair_splice.py) — direct import
- [tests/test_structured_transport_parity.py](../../../../../../tests/test_structured_transport_parity.py) — direct import
- [tests/test_teach_back.py](../../../../../../tests/test_teach_back.py) — direct import
  - `test_repaired_answer_is_composed_from_verbatim_prefix_and_regenerated_work`
  - `test_repaired_answer_without_regenerated_work_still_requires_exact_prefix`

## Modification guidance

- Change grading policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/grading.py](../../../../../../src/learnloop/attempts/grading.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
