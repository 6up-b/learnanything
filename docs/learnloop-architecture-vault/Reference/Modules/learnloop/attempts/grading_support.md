---
title: "learnloop.attempts.grading_support"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/grading_support.py"
source_paths:
  - "src/learnloop/attempts/grading_support.py"
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
  - "learnloop.attempts.grading_support module"
  - "src/learnloop/attempts/grading_support.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.grading_support`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.grading_support` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: PF-c grading support for the learner-blind grader (Slice 2 §5.5, at S1.1).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py) |
| Source lines | 1272 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `route_rules_text(version: str) -> str` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 217) — The prompt text of an own-route rules version (``own-route-v1``/``-v2``).
- `route_rules_suffix(version: str) -> str` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 223) — The prompt and calibration identity suffix of a rules version.
- `route_rules_active(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 244) — Does this vault grade NEW blind answers under the own-route rules?
- `method_rules_active(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 260) — Does this vault grade NEW blind answers under the required-method rules?
- `route_rules_version(vault: LoadedVault) -> str | None` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 275) — The own-route rules version new blind answers are graded under, if any.
- `required_method_policy(item: PracticeItem, rubric_criterion_ids: Sequence[str] | None=None, *, required_method: Mapping[str, Any] | None | Any=ITEM_REQUIRED_METHOD) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 298) — The required method as the grader's policy shows it, or None.
- `policy_method_criteria(policy: Mapping[str, Any] | None) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 336) — The criterion ids a policy's required method grades on use of the method.
- `class RouteCheck(WireModel)` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 345)
- `class ReferencePolicyBlindGradingProposal(WireModel)` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 351) — The mvp-2.1 wire model: PF-c fields in generation order around the shared blind fields (solve-first BEFORE the analysis; the route check right after it).
  - `as_blind_proposal(self) -> BlindGradingProposal` (line 375; public)
- `class StuckReferencePolicyBlindGradingProposal(ReferencePolicyBlindGradingProposal)` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 388) — mvp-2.1 for a stuck answer (``mvp-0.13``): the reading comes LAST.
- `blind_result_model(context: BlindGradingContext) -> type[WireModel]` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 394) — The wire model one blind grading call returns for this context.
- `reference_policy(item: PracticeItem, learner_answer_md: str, *, route_rules: bool | str=False, rubric_criterion_ids: Sequence[str] | None=None, required_method: Mapping[str, Any] | None | Any=ITEM_REQUIRED_METHOD) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 406) — The PF-c policy block for one answer (item-side + this answer only).
- `class GateOutcome` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 473)
- `apply_valid_alternative_gate(proposal: BlindGradingProposal, *, rubric: Rubric, learner_answer_md: str, policy: Mapping[str, Any] | None, declared_unverified: Sequence[str]=(), method_criterion_ids: Sequence[str]=()) -> GateOutcome` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 484) — Record unlocated failures on a verifying answer as unverified.
- `class RouteRuleOutcome` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 582)
  - `applied(self) -> bool` (line 606; public)
- `apply_route_rule(proposal: BlindGradingProposal, *, rubric: Rubric, learner_answer_md: str, final_answer_status: str | None, divergent_route: bool, unverified_before: Sequence[str]=(), declared_unverified: Sequence[str]=(), clarification_answer_md: str | None=None, method_criterion_ids: Sequence[str]=()) -> RouteRuleOutcome` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 610) — P1 on the grader's own output: no located error, no mark-down.
- `record_route_rule_judgment(connection: Any, *, attempt_id: str, grading_support: Mapping[str, Any], judge_model: str | None, prompt_version: str, input_hash: str, created_at: str) -> str | None` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 769) — Append the grade's own-route verdict to ``judgment_ledger`` (review F4).
- `revalidated_support(grading_support: Mapping[str, Any], record: Mapping[str, Any], rubric: Rubric) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 859) — ``assessed_shortfall`` recomputed over the VALIDATED grade (held-grade-evidence F1).
- `criterion_outcomes(proposal: BlindGradingProposal, rubric: Rubric) -> dict[str, str]` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 921)
- `sample_fingerprint(proposal: BlindGradingProposal, rubric: Rubric) -> str` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 932) — §4.4 split-mode fingerprint: (abstained, anchor, criterion outcomes).
- `modal_sample(proposals: Sequence[BlindGradingProposal], rubric: Rubric) -> tuple[int, dict[str, Any]]` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 945) — (index of the modal sample, the shadow sampling log).
- `family_key(vault: LoadedVault, item: PracticeItem) -> str` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 979) — The family a variant belongs to: PF-a's ``family_id`` once it exists, else the independent-surface group (one code path, augmentation §8).
- `grade_uncertainty_signal(*, score_fraction: float, grader_confidence: float, prior_fractions: Sequence[float], family: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 989) — Shadow only: never an input to the grader, never read by routing.
- `class BlindGradingRun` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 1025)
- `gated_review_reason(run: BlindGradingRun, *, attempt_id: str, item: PracticeItem, vault: LoadedVault, learner_answer_md: str, rubric: Rubric) -> str | None` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 1038) — The attempt's manual-review reason when the PF-c gate applied, else None.
- `request_blind_grading_run(client: OperationClient, context: BlindGradingContext, *, rubric: Rubric, sample_count: int=1) -> BlindGradingRun` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 1084) — k isolated blind grading calls (k=1 by default), modal choice, PF-c gate.

### Module constants

- `REFERENCE_POLICY_PROMPT_VERSION` ([src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py), line 127)
- `REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION` ([src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py), line 128)
- `GRADING_SUPPORT_VERSION` ([src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py), line 129)
- `UNVERIFIED_REVIEW_REASON` ([src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py), line 134)
- `UNASSESSED_CRITERION_LABEL` ([src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py), line 137)
- `REFERENCE_POLICY_RULES` ([src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py), line 139)
- `ROUTE_RULES_VERSION` ([src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py), line 168)
- `ROUTE_RULES_SUFFIX` ([src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py), line 169)
- `ROUTE_RULES` ([src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py), line 170)
- `METHOD_ROUTE_RULES_VERSION` ([src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py), line 193)
- `METHOD_ROUTE_RULES_SUFFIX` ([src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py), line 194)
- `REQUIRED_METHOD_RULES` ([src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py), line 195)
- `ROUTE_RULES_V2` ([src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py), line 209)
- `ROUTE_RULES_TEXT` ([src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py), line 211)
- `ROUTE_RULE_SUPPORT_KEY` ([src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py), line 234)
- `ROUTE_RULE_RECORD_VERSION` ([src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py), line 235)
- `HELD_REVIEW_REASON` ([src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py), line 238)
- `DIFFERS_FROM_REFERENCE` ([src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py), line 240)
- `MATCHES_REFERENCE` ([src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py), line 241)
- `ITEM_REQUIRED_METHOD` ([src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py), line 295)
- `_WS` ([src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py), line 448)
- `_UNLOCATED_NOTE` ([src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py), line 577)
- `_DECLARED_NOTE` ([src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py), line 578)
- `ROUTE_RULE_JUDGMENT_TASK` ([src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py), line 748)
- `LEGACY_ROUTE_CHECK_JUDGMENT_TASK` ([src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py), line 752)
- `NOT_CHECKED_VERDICT` ([src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py), line 756)

### Explicit exports

`__all__` declares:

- `BlindGradingRun`
- `GRADING_SUPPORT_VERSION`
- `GateOutcome`
- `HELD_REVIEW_REASON`
- `ITEM_REQUIRED_METHOD`
- `LEGACY_ROUTE_CHECK_JUDGMENT_TASK`
- `METHOD_ROUTE_RULES_SUFFIX`
- `METHOD_ROUTE_RULES_VERSION`
- `NOT_CHECKED_VERDICT`
- `REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION`
- `REFERENCE_POLICY_PROMPT_VERSION`
- `REFERENCE_POLICY_RULES`
- `REQUIRED_METHOD_RULES`
- `ROUTE_RULES`
- `ROUTE_RULES_TEXT`
- `ROUTE_RULES_V2`
- `ROUTE_RULES_SUFFIX`
- `ROUTE_RULES_VERSION`
- `ROUTE_RULE_JUDGMENT_TASK`
- `ROUTE_RULE_RECORD_VERSION`
- `ROUTE_RULE_SUPPORT_KEY`
- `ReferencePolicyBlindGradingProposal`
- `RouteCheck`
- `RouteRuleOutcome`
- `StuckReferencePolicyBlindGradingProposal`
- `UNASSESSED_CRITERION_LABEL`
- `UNVERIFIED_REVIEW_REASON`
- `apply_route_rule`
- `apply_valid_alternative_gate`
- `blind_result_model`
- `criterion_outcomes`
- `family_key`
- `gated_review_reason`
- `grade_uncertainty_signal`
- `method_rules_active`
- `modal_sample`
- `policy_method_criteria`
- `record_route_rule_judgment`
- `reference_policy`
- `request_blind_grading_run`
- `required_method_policy`
- `revalidated_support`
- `route_rules_active`
- `route_rules_suffix`
- `route_rules_text`
- `route_rules_version`
- `sample_fingerprint`

## Internal implementation anchors

- `class _ItemRequiredMethod` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 285) — :func:`reference_policy`'s default source: the item's current required method.
- `_squash(text: str) -> str` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 451)
- `_attribution_criteria(attribution: BlindErrorAttribution) -> set[str]` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 455)
- `_located(attribution: BlindErrorAttribution, answer: str) -> bool` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 466)
- `_named_criteria(attribution: BlindErrorAttribution, rubric_ids: Sequence[str] | set[str]) -> set[str]` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 550) — The rubric criteria an attribution names (held-grade-evidence F1).
- `_located_in_force(attribution: BlindErrorAttribution, texts: Sequence[str]) -> bool` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 564) — A concrete error in the learner's words, still in force (P1).
- `_current_route_judgment(connection: Any, task: str, attempt_id: str) -> Any` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 759)
- `_anchor_key(proposal: BlindGradingProposal) -> str | None` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 899)
- `_abstained(proposal: BlindGradingProposal) -> bool` ([source](../../../../../../src/learnloop/attempts/grading_support.py), line 916)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `ITEM_REQUIRED_METHOD`, `REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION`, `family_key`, `gated_review_reason`, `grade_uncertainty_signal`, `method_rules_active`, `record_route_rule_judgment`, `reference_policy`, `request_blind_grading_run`, `revalidated_support`, `route_rules_suffix`, `route_rules_version`; statically calls `family_key`, `gated_review_reason`, `grade_uncertainty_signal`, `method_rules_active`, `record_route_rule_judgment`, `reference_policy`, `request_blind_grading_run`, `revalidated_support`, `route_rules_suffix`, `route_rules_version`
- [[Reference/Modules/learnloop/attempts/blind_grading|learnloop.attempts.blind_grading]] — imports `REFERENCE_POLICY_PROMPT_VERSION`, `REFERENCE_POLICY_RULES`, `blind_result_model`, `route_rules_suffix`, `route_rules_text`; statically calls `blind_result_model`, `route_rules_suffix`, `route_rules_text`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `gated_review_reason`, `record_route_rule_judgment`, `request_blind_grading_run`, `revalidated_support`; statically calls `gated_review_reason`, `record_route_rule_judgment`, `request_blind_grading_run`, `revalidated_support`
- [[Reference/Modules/learnloop/diagnosis/grading_hardcases|learnloop.diagnosis.grading_hardcases]] — imports `METHOD_ROUTE_RULES_VERSION`, `apply_route_rule`, `apply_valid_alternative_gate`, `blind_result_model`, `policy_method_criteria`, `reference_policy`; statically calls `apply_route_rule`, `apply_valid_alternative_gate`, `blind_result_model`, `policy_method_criteria`, `reference_policy`
- [[Reference/Modules/learnloop/diagnosis/split/pfc_report|learnloop.diagnosis.split.pfc_report]] — imports `REFERENCE_POLICY_PROMPT_VERSION`, `reference_policy`, `request_blind_grading_run`; statically calls `reference_policy`, `request_blind_grading_run`
- [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]] — imports `UNASSESSED_CRITERION_LABEL`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `UNASSESSED_CRITERION_LABEL`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `OperationClient`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `METHOD_EXPLICIT_VERSIONS`, `ROUTE_RULES_VERSIONS`
- [[Reference/Modules/learnloop/attempts/ai_contracts|learnloop.attempts.ai_contracts]] — imports `ClarificationRequest`, `CriterionEvidence`, `DiscriminationProfileMatch`, `ErrorHuntReport`, `ExercisedFacetObservation`
- [[Reference/Modules/learnloop/attempts/answer_check|learnloop.attempts.answer_check]] — imports `final_answer_check`; calls `final_answer_check`
- [[Reference/Modules/learnloop/attempts/blind_grading|learnloop.attempts.blind_grading]] — imports `BlindErrorAttribution`, `BlindGradingContext`, `BlindGradingProposal`, `BlindRepairedTrace`, `StuckBlindGradingProposal`, `blind_grading_prompt`, `blind_prompt_version`, `validate_blind_grading_proposal`; calls `blind_grading_prompt`, `blind_prompt_version`, `validate_blind_grading_proposal`
- [[Reference/Modules/learnloop/attempts/grading_admission|learnloop.attempts.grading_admission]] — imports `admit_grading_call`; calls `admit_grading_call`
- [[Reference/Modules/learnloop/attempts/stuck|learnloop.attempts.stuck]] — imports `StuckReading`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `GRADE_HELD_FOR_REVIEW`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `UNASSESSED_INTERPRETATION`, `UNVERIFIED_CRITERION_BLOCK`, `UNVERIFIED_INTERPRETATION_KEY`, `surface_group_id`; calls `surface_group_id`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`, `Rubric`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `re`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/blind_grading|learnloop.attempts.blind_grading]], [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]], [[Reference/Modules/learnloop/diagnosis/grading_hardcases|learnloop.diagnosis.grading_hardcases]], [[Reference/Modules/learnloop/diagnosis/split/pfc_report|learnloop.diagnosis.split.pfc_report]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/pfc_unassessed_readers_helpers.py](../../../../../../tests/pfc_unassessed_readers_helpers.py) — direct import
- [tests/route_rules_in_grader_helpers.py](../../../../../../tests/route_rules_in_grader_helpers.py) — direct import
- [tests/structured_ai.py](../../../../../../tests/structured_ai.py) — direct import
- [tests/test_grading_support.py](../../../../../../tests/test_grading_support.py) — direct import
  - `test_an_unverified_criterion_writes_no_negative_evidence_even_without_an_attribution`
  - `test_gate_keeps_a_located_error_and_never_fires_on_a_wrong_final_answer`
  - `test_gate_records_unlocated_failures_on_a_verifying_answer_as_unverified`
  - `test_live_blind_grade_records_grading_support_and_its_calibration_identity`
  - `test_reference_policy_is_item_side_and_deterministic`
  - `test_request_blind_grading_run_samples_and_gates`
  - `test_split_mode_fingerprint_and_asymmetric_shadow_log`
  - `test_uncertainty_signal_is_shadow_and_within_family`
- [tests/test_held_grade_evidence.py](../../../../../../tests/test_held_grade_evidence.py) — direct import
  - `test_f1_a_blank_or_unknown_criterion_id_names_no_criterion`
  - `test_f1_the_shortfall_is_recomputed_over_the_validated_grade`
  - `test_f2_a_regrade_that_validates_nothing_keeps_the_hold`
- [tests/test_method_explicit_upgrade.py](../../../../../../tests/test_method_explicit_upgrade.py) — direct import
  - `test_each_version_activates_exactly_its_features`
  - `test_new_vaults_start_at_the_successor`
  - `test_upgrade_from_mvp024_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp011_upgrade.py](../../../../../../tests/test_mvp011_upgrade.py) — direct import
  - `test_new_vaults_start_at_the_latest_version`
- [tests/test_mvp017_upgrade.py](../../../../../../tests/test_mvp017_upgrade.py) — direct import
  - `test_each_version_activates_exactly_its_features`
- [tests/test_mvp018_upgrade.py](../../../../../../tests/test_mvp018_upgrade.py) — direct import
  - `test_each_version_keeps_its_predecessors_and_grades_as_mvp016`
  - `test_upgrade_from_mvp017_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp020_upgrade.py](../../../../../../tests/test_mvp020_upgrade.py) — direct import
  - `test_an_earlier_vault_goes_through_mvp012s_guard_when_it_is_required`
  - `test_each_version_activates_exactly_its_features`
  - `test_new_vaults_start_at_a_successor_with_the_route_rules`
  - `test_upgrade_from_mvp019_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp021_upgrade.py](../../../../../../tests/test_mvp021_upgrade.py) — direct import
- [tests/test_pfc_unassessed_readers.py](../../../../../../tests/test_pfc_unassessed_readers.py) — direct import
  - `test_retention_exclusions_distinguish_the_review_reasons`
  - `test_the_pfc_flag_is_the_reason_only_when_it_is_the_sole_concern`
- [tests/test_pfc_unverified_unassessed.py](../../../../../../tests/test_pfc_unverified_unassessed.py) — direct import
  - `test_a_complement_route_is_graded_on_its_assessed_criteria_only`
  - `test_a_located_error_beside_an_unverified_criterion_still_counts`
  - `test_a_regrade_applies_the_same_rule`
  - `test_feedback_shows_an_unverified_criterion_as_not_assessed`
  - `test_the_stamped_block_is_read_from_text_or_mapping`
- [tests/test_reader_recap_review_r2.py](../../../../../../tests/test_reader_recap_review_r2.py) — direct import
- [tests/test_required_method_authority.py](../../../../../../tests/test_required_method_authority.py) — direct import
  - `test_an_import_keeps_the_field_exactly_when_the_one_time_judgment_says_requires`
  - `test_grading_reads_only_the_frozen_field`
  - `test_no_grading_entry_point_takes_the_prompt_to_decide`
- [tests/test_required_method_grading.py](../../../../../../tests/test_required_method_grading.py) — direct import
  - `test_active_only_at_the_successor_with_both_switches_on`
  - `test_off_and_at_the_predecessor_the_prompt_is_the_predecessors_byte_for_byte`
  - `test_pfc_gate_never_unassesses_a_method_criterion_on_a_divergent_route`
  - `test_the_kill_switch_grades_exactly_as_the_predecessor`
  - `test_the_prompt_carries_the_required_method_and_names_v2`
- [tests/test_route_rules_in_grader.py](../../../../../../tests/test_route_rules_in_grader.py) — direct import
  - `test_a_ruled_grade_is_calibrated_under_the_rules_identity_and_so_is_its_regrade`
  - `test_active_only_at_the_successor_with_the_switch_on`
  - `test_cli_dry_run_plans_one_grading_call`
  - `test_f1_live_an_incomplete_grade_with_nothing_located_is_held`
  - `test_f1_live_an_incomplete_regrade_keeps_an_existing_hold`
  - `test_f4_the_graders_route_verdict_reaches_the_judgment_ledger_and_regrades_supersede_it`
  - `test_f5_a_regrade_with_the_rule_switched_off_supersedes_the_held_verdict`
  - `test_live_an_unlocated_mark_down_on_a_divergent_route_is_unassessed`
  - `test_live_nothing_located_and_nothing_validated_is_held`
  - `test_the_kill_switch_and_mvp017_grade_exactly_as_mvp016`
  - `test_the_prompt_carries_the_rules_and_names_them_only_at_the_successor`
- [tests/test_stuck_prompt_composition.py](../../../../../../tests/test_stuck_prompt_composition.py) — direct import
  - `test_a_stuck_answers_pfc_unverified_criteria_are_unassessed`
- [tests/test_teacher_te2_landing_r1.py](../../../../../../tests/test_teacher_te2_landing_r1.py) — direct import

## Modification guidance

- Change grading support policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/grading_support.py](../../../../../../src/learnloop/attempts/grading_support.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
