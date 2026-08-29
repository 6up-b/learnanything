---
title: "learnloop.diagnosis.probe_families"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/probe_families.py"
source_paths:
  - "src/learnloop/diagnosis/probe_families.py"
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
  - "learnloop.diagnosis.probe_families module"
  - "src/learnloop/diagnosis/probe_families.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.probe_families`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.probe_families` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Probe Family Templates and Instrument Cards (spec_probe_eig_redesign.md §9).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py) |
| Source lines | 1797 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `knowledge_type_tokens(knowledge_type: str | None) -> set[str]` ([source](../../../../../../src/learnloop/diagnosis/probe_families.py), line 41) — Tokens of a possibly-compound knowledge type.
- `class CardValidationError(ValueError)` ([source](../../../../../../src/learnloop/diagnosis/probe_families.py), line 68) — A family/card failed schema, vocabulary, or normalization validation.
- `class FamilyGateRejection(ValueError)` ([source](../../../../../../src/learnloop/diagnosis/probe_families.py), line 72) — A family/card version failed the admission gate (§9.6).
- `class ProbeFamilyTemplate` ([source](../../../../../../src/learnloop/diagnosis/probe_families.py), line 77) — Versioned reusable measurement pattern (§9.2).
  - `as_dict(self) -> dict[str, Any]` (line 105; public)
  - `from_dict(cls, payload: Mapping[str, Any]) -> 'ProbeFamilyTemplate'` (line 127; public)
  - `schema_hash(self) -> str` (line 148; public)
- `class InstrumentCard` ([source](../../../../../../src/learnloop/diagnosis/probe_families.py), line 155) — LO-bound executable binding of a family template (§9.3).
  - `as_dict(self) -> dict[str, Any]` (line 179; public)
  - `from_dict(cls, payload: Mapping[str, Any]) -> 'InstrumentCard'` (line 201; public)
- `class CompiledInstrument` ([source](../../../../../../src/learnloop/diagnosis/probe_families.py), line 228) — Executable conditional model shared by selection and replay (§7.2).
  - `compiled_likelihood_hash(self) -> str` (line 253; public)
  - `snapshot(self) -> dict[str, Any]` (line 267; public) — Persistable resolved snapshot for a committed presentation (§9.3).
  - `from_snapshot(cls, payload: Mapping[str, Any]) -> 'CompiledInstrument'` (line 292; public)
- `validate_and_compile_card(card: InstrumentCard, template: ProbeFamilyTemplate, *, calibration_counts: Mapping[str, Mapping[str, float]] | None=None) -> CompiledInstrument` ([source](../../../../../../src/learnloop/diagnosis/probe_families.py), line 314) — Validate a card against its template and compile executable rows (§9.3).
- `grader_channel_matrix(grader_policy: str, alphabet: tuple[str, ...], *, reliability: float | None=None) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/diagnosis/probe_families.py), line 411) — ``P(observed_grade | true_response)`` per outcome class.
- `compose_with_grader_channel(rows: Mapping[str, Mapping[str, float]], channel: Mapping[str, Mapping[str, float]]) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/diagnosis/probe_families.py), line 433) — ``P(observed | h) = Σ_true P(observed | true) P(true | h)`` (§7.6).
- `instrument_conditionals(instrument: CompiledInstrument, *, grader_reliability: float | None=None) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/diagnosis/probe_families.py), line 454) — The grader-composed observed-outcome conditionals used everywhere (§7.2).
- `instrument_expected_information_gain(posterior: Mapping[str, float], instrument: CompiledInstrument, slot_map: Mapping[str, str], *, grader_reliability: float | None=None) -> float` ([source](../../../../../../src/learnloop/diagnosis/probe_families.py), line 467) — Actual hypothesis EIG in nats over the grader-composed conditionals (§7.2).
- `instrument_observation_likelihoods(instrument: CompiledInstrument, slot_map: Mapping[str, str], observed_outcome: str, *, grader_reliability: float | None=None) -> dict[str, float]` ([source](../../../../../../src/learnloop/diagnosis/probe_families.py), line 509) — ``P(observed_outcome | hypothesis)`` per episode label — the same grader-composed conditionals candidate EIG scores with (§7.2).
- `class PredictiveInstrumentEig` ([source](../../../../../../src/learnloop/diagnosis/probe_families.py), line 527) — Predictive EIG of one candidate over held-out target instruments (§7.4).
- `instrument_predictive_information_gain(posterior: Mapping[str, float], candidate: CompiledInstrument, candidate_slot_map: Mapping[str, str], targets: list[tuple[CompiledInstrument, Mapping[str, str]]], *, grader_reliability: float | None=None) -> PredictiveInstrumentEig` ([source](../../../../../../src/learnloop/diagnosis/probe_families.py), line 536) — How much observing the candidate's response is expected to sharpen predictions of the learner's responses to the held-out target instruments (§7.4, Adaptive Elicitation view).
- `information_rate(eig_nats: float, expected_seconds: float, *, overhead_seconds: float) -> float` ([source](../../../../../../src/learnloop/diagnosis/probe_families.py), line 621) — Information per expected second with a conservative fixed overhead (§7.5).
- `map_episode_labels_to_slots(instrument: CompiledInstrument, episode_labels: list[str], *, bindings: Mapping[str, Any] | None=None) -> dict[str, str] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_families.py), line 627) — Episode hypothesis label -> card slot, or None when the card cannot model the episode's locked set (the card must then abstain, §9.4).
- `classify_outcome(instrument: CompiledInstrument, *, rubric_score: int | None, attempt_type: str, fired_error_types: list[str], max_points: int=4) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_families.py), line 720) — Map one graded attempt onto the instrument's outcome alphabet.
- `builtin_family_templates() -> list[ProbeFamilyTemplate]` ([source](../../../../../../src/learnloop/diagnosis/probe_families.py), line 1474)
- `ensure_builtin_families(repository: Repository, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_families.py), line 1488) — Persist built-in family template versions as provisional (idempotent).
- `class PlantedTrial` ([source](../../../../../../src/learnloop/diagnosis/probe_families.py), line 1508) — One synthetic response trace: which hypothesis was planted, and the outcome the real signature matcher recovered from the generated response.
- `class FamilyGateResult` ([source](../../../../../../src/learnloop/diagnosis/probe_families.py), line 1518)
- `run_family_admission_gate(card: InstrumentCard, template: ProbeFamilyTemplate, trials: list[PlantedTrial], *, minimum_reverse_match: float=0.6, minimum_pair_separation: float=0.25, repository: Repository | None=None, clock: Clock | None=None) -> FamilyGateResult` ([source](../../../../../../src/learnloop/diagnosis/probe_families.py), line 1525) — Admission gate for one family/card version (§9.6).
- `record_real_observation_counts(repository: Repository, *, family_template_id: str, family_template_version: int, posterior_after: Mapping[str, float], slot_map: Mapping[str, str], observed_outcome: str, grader_version: str | None=None, practice_item_id: str | None=None, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_families.py), line 1631) — Fold one real observation into the family-version Dirichlet posterior.
- `real_calibration_counts(repository: Repository, family_template_id: str, family_template_version: int, *, grader_version: str | None=None) -> dict[str, dict[str, float]] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_families.py), line 1722)
- `shrunk_item_calibration_counts(repository: Repository, family_template_id: str, family_template_version: int, *, practice_item_id: str, grader_version: str | None=None, item_shrinkage_pseudo_count: float=25.0) -> dict[str, dict[str, float]] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_families.py), line 1741) — Item-level Dirichlet counts shrunk toward the family posterior (§9.7).

### Module constants

- `ORDINAL_VOCABULARY` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 29)
- `DEFAULT_CONDITIONAL_PSEUDO_COUNT` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 36)
- `SIGNATURE_MATCHER_VERSION` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 38)
- `SELECTION_POLICY_VERSION` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 54)
- `GRADER_CHANNEL_RELIABILITY` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 59)
- `APPROVED_DIAGNOSTIC_GRADING_SOURCES` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 65)
- `CONTRAST_CONFUSABLE_V1` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 798)
- `CONTRAST_CONFUSABLE_DEFAULT_ROWS` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 827)
- `MINIMAL_RECALL_V1` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 876)
- `MINIMAL_RECALL_DEFAULT_ROWS` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 902)
- `PREDICTION_V1` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 926)
- `PREDICTION_DEFAULT_ROWS` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 955)
- `PERTURBATION_V1` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 990)
- `PERTURBATION_DEFAULT_ROWS` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 1015)
- `MINIMAL_COUNTEREXAMPLE_V1` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 1050)
- `MINIMAL_COUNTEREXAMPLE_DEFAULT_ROWS` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 1079)
- `DIALOGUE_MICROPROBE_V1` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 1114)
- `DIALOGUE_MICROPROBE_DEFAULT_ROWS` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 1146)
- `PROOF_SKELETON_V1` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 1199)
- `PROOF_SKELETON_DEFAULT_ROWS` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 1228)
- `DERIVATION_V1` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 1271)
- `DERIVATION_DEFAULT_ROWS` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 1304)
- `EXTENDED_CASE_V1` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 1347)
- `EXTENDED_CASE_DEFAULT_ROWS` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 1378)
- `LONGFORM_FAMILY_IDS` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 1421)
- `LONGFORM_OBLIGATIONS` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 1427)
- `DEFAULT_INSTRUCTIONAL_ACTIONS` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 1449)
- `FAMILY_DEFAULT_ROWS` ([src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py), line 1461)

## Internal implementation anchors

- `_entropy(distribution: Mapping[str, float]) -> float` ([source](../../../../../../src/learnloop/diagnosis/probe_families.py), line 450)
- `_first_present(alphabet: tuple[str, ...], preferences: tuple[str, ...]) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_families.py), line 789)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/grader_calibration|learnloop.attempts.grader_calibration]] — imports `GRADER_CHANNEL_RELIABILITY`
- [[Reference/Modules/learnloop/diagnosis/probe_audit|learnloop.diagnosis.probe_audit]] — imports `CompiledInstrument`, `classify_outcome`; statically calls `classify_outcome`
- [[Reference/Modules/learnloop/diagnosis/probe_coverage|learnloop.diagnosis.probe_coverage]] — imports `InstrumentCard`, `ProbeFamilyTemplate`, `knowledge_type_tokens`, `map_episode_labels_to_slots`, `validate_and_compile_card`; statically calls `knowledge_type_tokens`, `map_episode_labels_to_slots`, `validate_and_compile_card`
- [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]] — imports `DIALOGUE_MICROPROBE_V1`, `map_episode_labels_to_slots`, `real_calibration_counts`, `validate_and_compile_card`; statically calls `map_episode_labels_to_slots`, `real_calibration_counts`, `validate_and_compile_card`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `APPROVED_DIAGNOSTIC_GRADING_SOURCES`, `CompiledInstrument`, `InstrumentCard`, `ProbeFamilyTemplate`, `SELECTION_POLICY_VERSION`, `classify_outcome`, `ensure_builtin_families`, `information_rate`, `instrument_expected_information_gain`, `instrument_observation_likelihoods`, `instrument_predictive_information_gain`, `map_episode_labels_to_slots`, `record_real_observation_counts`, `shrunk_item_calibration_counts`, `validate_and_compile_card`; statically calls `CompiledInstrument`, `classify_outcome`, `ensure_builtin_families`, `information_rate`, `instrument_expected_information_gain`, `instrument_observation_likelihoods`, `instrument_predictive_information_gain`, `map_episode_labels_to_slots`, `record_real_observation_counts`, `shrunk_item_calibration_counts`, `validate_and_compile_card`
- [[Reference/Modules/learnloop/diagnosis/probe_hypotheses|learnloop.diagnosis.probe_hypotheses]] — imports `knowledge_type_tokens`; statically calls `knowledge_type_tokens`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `CONTRAST_CONFUSABLE_V1`, `DEFAULT_INSTRUCTIONAL_ACTIONS`, `DERIVATION_V1`, `DIALOGUE_MICROPROBE_V1`, `EXTENDED_CASE_V1`, `FAMILY_DEFAULT_ROWS`, `InstrumentCard`, `LONGFORM_FAMILY_IDS`, `LONGFORM_OBLIGATIONS`, `MINIMAL_COUNTEREXAMPLE_V1`, `MINIMAL_RECALL_V1`, `PERTURBATION_V1`, `PREDICTION_V1`, `PROOF_SKELETON_V1`, `PlantedTrial`, `ProbeFamilyTemplate`, `ensure_builtin_families`, `knowledge_type_tokens`, `run_family_admission_gate`, `validate_and_compile_card`; statically calls `InstrumentCard`, `PlantedTrial`, `ensure_builtin_families`, `knowledge_type_tokens`, `run_family_admission_gate`, `validate_and_compile_card`
- [[Reference/Modules/learnloop/diagnosis/probe_lifecycle|learnloop.diagnosis.probe_lifecycle]] — imports `ProbeFamilyTemplate`
- [[Reference/Modules/learnloop/diagnosis/probe_outcome_mapping|learnloop.diagnosis.probe_outcome_mapping]] — imports `CompiledInstrument`
- [[Reference/Modules/learnloop/diagnosis/probe_robust|learnloop.diagnosis.probe_robust]] — imports `CompiledInstrument`
- [[Reference/Modules/learnloop/sim/diagnostic_validation|learnloop.sim.diagnostic_validation]] — imports `CompiledInstrument`, `DEFAULT_INSTRUCTIONAL_ACTIONS`, `builtin_family_templates`; statically calls `builtin_family_templates`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/probe_hypotheses|learnloop.diagnosis.probe_hypotheses]] — imports `CONFUSES_PREFIX`, `MISCONCEPTION_PREFIX`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `json`, `math`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/grader_calibration|learnloop.attempts.grader_calibration]], [[Reference/Modules/learnloop/diagnosis/probe_audit|learnloop.diagnosis.probe_audit]], [[Reference/Modules/learnloop/diagnosis/probe_coverage|learnloop.diagnosis.probe_coverage]], [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]], [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] and 6 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/helpers.py](../../../../../../tests/helpers.py) — direct import
- [tests/test_calibration_sessions.py](../../../../../../tests/test_calibration_sessions.py) — direct import
- [tests/test_characterization_grader_channel.py](../../../../../../tests/test_characterization_grader_channel.py) — direct import
  - `test_calibration_posterior_mean_uses_pseudo_count_eight`
  - `test_channel_is_symmetric_overcall_equals_undercall`
  - `test_channel_matrix_five_class_spread`
  - `test_compiled_card_defaults_to_pseudo_count_eight_and_normalized_ordinal_rows`
  - `test_compose_mixed_true_row`
  - `test_compose_point_mass_recovers_channel_column`
  - `test_default_conditional_pseudo_count_is_eight`
  - `test_direct_compiled_instrument_uses_grader_policy_reliability`
  - `test_explicit_reliability_override_beats_policy_constant`
  - `test_grader_channel_reliability_constants`
  - `test_grader_reliability_override_flows_into_composed_likelihoods`
  - `test_instrument_conditionals_compose_prior_rows_through_microprobe_channel`
  - `test_longform_channel_matrix_binary_alphabet`
  - `test_microprobe_channel_matrix_binary_alphabet`
  - `test_observation_likelihoods_are_symmetric_over_over_and_undercall`
  - `test_ordinal_vocabulary_table_exact_values`
  - `test_unknown_policy_falls_back_to_reliability_point_nine`
- [tests/test_characterization_probe_family_em.py](../../../../../../tests/test_characterization_probe_family_em.py) — direct import
  - `test_labels_sharing_a_slot_are_summed_and_negatives_clamped`
  - `test_posterior_weight_is_folded_as_fractional_real_learner_count`
  - `test_real_learner_write_does_not_promote_or_touch_synthetic_gate`
  - `test_repeated_observations_accumulate_fractional_counts`
- [tests/test_characterization_probe_replay.py](../../../../../../tests/test_characterization_probe_replay.py) — direct import
  - `test_replay_rebuilds_from_current_grader_policy_not_a_pinned_snapshot`
- [tests/test_characterization_probe_submission.py](../../../../../../tests/test_characterization_probe_submission.py) — direct import
  - `test_composition_and_update_signatures_omit_grader_confidence`
  - `test_exact_posterior_update_for_uniform_prior`
  - `test_exact_posterior_update_with_weight_damping`
  - `test_posterior_delta_identical_across_grader_confidence_values`
- [tests/test_graph_correction.py](../../../../../../tests/test_graph_correction.py) — direct import
  - `test_calibration_ordering_reverts_to_plain_rate`
- [tests/test_km4_taxonomy.py](../../../../../../tests/test_km4_taxonomy.py) — direct import
  - `test_compositional_record_parameterizes_contrast_probe`
- [tests/test_p2_acceptance.py](../../../../../../tests/test_p2_acceptance.py) — direct import
- [tests/test_p2_leakage_suite.py](../../../../../../tests/test_p2_leakage_suite.py) — direct import
- [tests/test_probe_coverage.py](../../../../../../tests/test_probe_coverage.py) — direct import
  - `test_direct_plus_shifted_bindings_cover_a_contrast`
- [tests/test_probe_episodes.py](../../../../../../tests/test_probe_episodes.py) — direct import
  - `test_card_with_incomplete_row_is_rejected`
  - `test_card_with_numeric_conditionals_is_rejected`
  - `test_compiled_rows_carry_pseudo_counts_and_normalize`
  - `test_family_gate_accepts_reproducible_signatures`
  - `test_family_gate_rejects_failed_reverse_matching`
  - `test_family_gate_rejects_overapplied_misconception`
  - `test_hypothesis_independent_item_receives_zero_eig`
  - `test_labels_map_through_open_set_abstention`
  - `test_lower_grader_reliability_lowers_eig`
  - `test_multi_confusable_set_keeps_instrument_eligible`
- [tests/test_probe_hierarchy.py](../../../../../../tests/test_probe_hierarchy.py) — direct import
  - `test_item_evidence_outgrows_family_shrinkage`
  - `test_sparse_item_inherits_family_posterior`
- [tests/test_probe_instance_generation.py](../../../../../../tests/test_probe_instance_generation.py) — direct import
- [tests/test_probe_lifecycle.py](../../../../../../tests/test_probe_lifecycle.py) — direct import
- [tests/test_probe_llm_instances.py](../../../../../../tests/test_probe_llm_instances.py) — direct import
  - `test_llm_family_gate_accepts_and_records_synthetic_calibration`
  - `test_llm_family_gate_rejects_indistinct_signatures`
  - `test_llm_family_gate_requires_capable_provider`
- [tests/test_probe_longform_families.py](../../../../../../tests/test_probe_longform_families.py) — direct import
  - `test_derivation_card_declares_ordered_obligations`
  - `test_derivation_family_passes_admission_gate`
  - `test_derivation_separates_procedure_without_selection`
  - `test_generation_produces_derivation_instance_with_obligation_rubric`
  - `test_integrative_gap_clears_with_derivation_card`
  - `test_longform_observation_records_trace_and_bounded_mass`
  - `test_longform_templates_registered_as_builtins`
  - `test_procedure_knowledge_type_gets_derivation_family`
- [tests/test_probe_predictive_eig.py](../../../../../../tests/test_probe_predictive_eig.py) — direct import
  - `test_hypothesis_independent_candidate_has_zero_predictive_eig`
  - `test_predictive_eig_requires_held_out_targets`
- [tests/test_probe_robust_cutover.py](../../../../../../tests/test_probe_robust_cutover.py) — direct import
  - `test_robust_selection_abstains_on_indistinguishable_candidates`
- [tests/test_probe_surface_mint.py](../../../../../../tests/test_probe_surface_mint.py) — direct import

## Modification guidance

- Change probe families policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/probe_families.py](../../../../../../src/learnloop/diagnosis/probe_families.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
