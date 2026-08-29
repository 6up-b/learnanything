---
title: "learnloop.diagnosis.probe_instance_generation"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/probe_instance_generation.py"
source_paths:
  - "src/learnloop/diagnosis/probe_instance_generation.py"
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
  - "learnloop.diagnosis.probe_instance_generation module"
  - "src/learnloop/diagnosis/probe_instance_generation.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.probe_instance_generation`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.probe_instance_generation` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Parameterized instance generation from admitted family/card bindings (§10).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/probe_instance_generation.py](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py) |
| Source lines | 1427 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class InstanceGateRejection(ValueError)` ([source](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 105) — A generated instance failed the structural/grounding/conformance gate.
- `request_probe_instance_surfaces(client: StructuredTransport, context: ProbeInstanceContext) -> ProbeInstanceSurfaces` ([source](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 109) — Generate probe surfaces through the shared structured transport.
- `request_probe_family_trials(client: StructuredTransport, context: ProbeFamilyTrialsContext) -> ProbeFamilyTrials` ([source](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 122) — Generate planted family trials through the shared transport.
- `class GeneratedInstance` ([source](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 136)
- `class GenerationSummary` ([source](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 149)
  - `as_dict(self) -> dict[str, Any]` (line 157; public)
- `applicable_families(vault: LoadedVault, learning_object: LearningObject, repository: Repository | None=None) -> list[ProbeFamilyTemplate]` ([source](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 183) — Families whose bindings this LO can fill, best-first (§9.5 coverage: one direct/minimal instrument plus one contrast/perturbation instrument).
- `compositional_contrast_binding(vault: LoadedVault, repository: Repository, learning_object_id: str) -> tuple[str, str] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 230) — The (target_facet, confused_with_facet) pair of an active compositional misconception on this LO, if any (knowledge-model §10.2).
- `ensure_instrument_card(vault: LoadedVault, repository: Repository, learning_object_id: str, template: ProbeFamilyTemplate, *, clock: Clock | None=None) -> tuple[InstrumentCard, ProbeFamilyTemplate] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 318) — Resolve or mint the LO-bound card for one family template (§9.3).
- `parametric_instance_payloads(vault: LoadedVault, card: InstrumentCard, template: ProbeFamilyTemplate, *, count: int, seed: int, clock: Clock | None=None, surface_offset: int=0) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 619) — Deterministic surface-varied Item Instance payloads for one binding.
- `llm_instance_payloads(vault: LoadedVault, card: InstrumentCard, template: ProbeFamilyTemplate, *, count: int, ai_client: object, clock: Clock | None=None) -> list[dict[str, Any]] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 794) — LLM-generated surface payloads for one binding, or None when the provider lacks the capability or is unavailable (§9.2 fallback contract).
- `instance_gate_errors(vault: LoadedVault, payload: Mapping[str, Any], card: InstrumentCard, template: ProbeFamilyTemplate) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 885) — Cheap structural, grounding, duplication, and card-conformance checks.
- `generate_instances_for_episode(repository: Repository, vault: LoadedVault, episode_id: str, *, clock: Clock | None=None, instances_per_family: int | None=None, seed: int=0, ai_client: object | None=None) -> GenerationSummary` ([source](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 960) — Resolve a `pending_items` episode's generation needs through admitted family/card bindings (§10 steps 3–6).
- `mint_single_use_probe_surface(repository: Repository, vault: LoadedVault, episode_id: str, *, ai_client: object, clock: Clock | None=None, seed: int=0) -> GeneratedInstance | None` ([source](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 1117) — Mint ONE fresh single-use ``diagnostic_probe`` surface for an open episode.
- `approve_probe_instance(repository: Repository, vault: LoadedVault, practice_item_id: str, *, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 1292) — Reviewer approval for a pending instance: activate it and unpark its LO's episode when it now yields an eligible instrument.
- `run_llm_family_gate(vault: LoadedVault, repository: Repository, learning_object_id: str, template: ProbeFamilyTemplate, ai_client: object, *, trials_per_hypothesis: int=3, clock: Clock | None=None)` ([source](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 1329) — Run the §9.6 family admission gate with LLM planted-trial traces.
- `pending_review_instance_ids(repository: Repository) -> set[str]` ([source](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 1423) — Item ids parked behind instance review (consumed by state sync so a vault sync cannot force-reactivate them).

### Module constants

- `GENERATOR_ID` ([src/learnloop/diagnosis/probe_instance_generation.py](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 62)
- `GENERATOR_VERSION` ([src/learnloop/diagnosis/probe_instance_generation.py](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 63)
- `LLM_GENERATOR_ID` ([src/learnloop/diagnosis/probe_instance_generation.py](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 70)
- `LLM_GENERATOR_VERSION` ([src/learnloop/diagnosis/probe_instance_generation.py](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 71)
- `SIGNATURE_FATAL_ERRORS` ([src/learnloop/diagnosis/probe_instance_generation.py](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 77)
- `_SURFACE_TEMPLATES` ([src/learnloop/diagnosis/probe_instance_generation.py](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 438)
- `_LONGFORM_CRITERIA` ([src/learnloop/diagnosis/probe_instance_generation.py](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 598)
- `_FAMILY_MEASUREMENT_INTENT` ([src/learnloop/diagnosis/probe_instance_generation.py](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 736)

## Internal implementation anchors

- `_confusable_for(vault: LoadedVault, learning_object: LearningObject) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 259)
- `_target_facet_for(vault: LoadedVault, learning_object: LearningObject) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 272) — The LO's most evidence-weighted facet across its items (deterministic).
- `_misconception_error_types(vault: LoadedVault) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 290) — Error-type ids whose firing marks a confusable/misconception signature.
- `_instance_payload(learning_object: LearningObject, card: InstrumentCard, template: ProbeFamilyTemplate, *, prompt: str, expected_answer: str, surface_family: str, now: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 672) — One Item Instance payload: card/template own everything except the surface (prompt, expected answer, surface family).
- `_llm_prompt_version() -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 781)
- `_sanitized_surface_suffix(raw: str, index: int) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 787)
- `_grounding_tokens(text: str) -> set[str]` ([source](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py), line 875) — Content tokens for the grounding check: >3 chars, naive plural fold.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `applicable_families`, `generate_instances_for_episode`, `run_llm_family_gate`; statically calls `applicable_families`, `generate_instances_for_episode`, `run_llm_family_gate`
- [[Reference/Modules/learnloop/diagnosis/calibration_sessions|learnloop.diagnosis.calibration_sessions]] — imports `generate_instances_for_episode`; statically calls `generate_instances_for_episode`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_surface_supply|learnloop.diagnosis.diagnostic_surface_supply]] — imports `mint_single_use_probe_surface`; statically calls `mint_single_use_probe_surface`
- [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]] — imports `GENERATOR_ID`, `GENERATOR_VERSION`, `LLM_GENERATOR_ID`, `LLM_GENERATOR_VERSION`, `ensure_instrument_card`, `instance_gate_errors`, `parametric_instance_payloads`; statically calls `ensure_instrument_card`, `instance_gate_errors`, `parametric_instance_payloads`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `applicable_families`, `generate_instances_for_episode`; statically calls `applicable_families`, `generate_instances_for_episode`
- [[Reference/Modules/learnloop/sim/diagnostic_validation|learnloop.sim.diagnostic_validation]] — imports `generate_instances_for_episode`; statically calls `generate_instances_for_episode`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `pending_review_instance_ids`; statically calls `pending_review_instance_ids`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `pending_review_instance_ids`; statically calls `pending_review_instance_ids`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `StructuredTransport`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `ProbeGenerationNeedRecord`, `Repository`
- [[Reference/Modules/learnloop/diagnosis/ai_contracts|learnloop.diagnosis.ai_contracts]] — imports `PROBE_INSTANCE_PROMPT_VERSION`, `ProbeFamilyTrials`, `ProbeFamilyTrialsContext`, `ProbeInstanceContext`, `ProbeInstanceSurfaces`, `probe_family_trials_prompt`, `probe_instance_surfaces_prompt`; calls `ProbeFamilyTrialsContext`, `ProbeInstanceContext`, `probe_family_trials_prompt`, `probe_instance_surfaces_prompt`
- [[Reference/Modules/learnloop/diagnosis/error_taxonomy_map|learnloop.diagnosis.error_taxonomy_map]] — imports `MECHANISM_IS_MISCONCEPTION`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `administered_surface_exclusions`, `eligible_instruments`; calls `administered_surface_exclusions`, `eligible_instruments`
- [[Reference/Modules/learnloop/diagnosis/probe_families|learnloop.diagnosis.probe_families]] — imports `CONTRAST_CONFUSABLE_V1`, `DEFAULT_INSTRUCTIONAL_ACTIONS`, `DERIVATION_V1`, `DIALOGUE_MICROPROBE_V1`, `EXTENDED_CASE_V1`, `FAMILY_DEFAULT_ROWS`, `InstrumentCard`, `LONGFORM_FAMILY_IDS`, `LONGFORM_OBLIGATIONS`, `MINIMAL_COUNTEREXAMPLE_V1`, `MINIMAL_RECALL_V1`, `PERTURBATION_V1`, `PREDICTION_V1`, `PROOF_SKELETON_V1`, `PlantedTrial`, `ProbeFamilyTemplate`, `ensure_builtin_families`, `knowledge_type_tokens`, `run_family_admission_gate`, `validate_and_compile_card`; calls `InstrumentCard`, `PlantedTrial`, `ensure_builtin_families`, `knowledge_type_tokens`, `run_family_admission_gate`, `validate_and_compile_card`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `is_canonical_state_vault`; calls `is_canonical_state_vault`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LearningObject`, `LoadedVault`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `upsert_practice_item`; calls `upsert_practice_item`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `random`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/diagnosis/calibration_sessions|learnloop.diagnosis.calibration_sessions]], [[Reference/Modules/learnloop/diagnosis/diagnostic_surface_supply|learnloop.diagnosis.diagnostic_surface_supply]], [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]], [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_km4_taxonomy.py](../../../../../../tests/test_km4_taxonomy.py) — direct import
  - `test_compositional_record_parameterizes_contrast_probe`
- [tests/test_probe_coverage.py](../../../../../../tests/test_probe_coverage.py) — direct import
  - `test_direct_plus_shifted_bindings_cover_a_contrast`
- [tests/test_probe_instance_generation.py](../../../../../../tests/test_probe_instance_generation.py) — direct import
  - `test_generation_is_idempotent`
  - `test_provisional_family_instances_park_behind_review`
  - `test_trusted_family_generation_unparks_episode_with_provenance`
- [tests/test_probe_llm_instances.py](../../../../../../tests/test_probe_llm_instances.py) — direct import
  - `test_gate_rejected_llm_surfaces_fall_back_to_parametric`
  - `test_llm_family_gate_accepts_and_records_synthetic_calibration`
  - `test_llm_family_gate_rejects_indistinct_signatures`
  - `test_llm_family_gate_requires_capable_provider`
  - `test_llm_surfaces_config_disable`
  - `test_llm_surfaces_generate_with_provenance`
  - `test_provider_failure_falls_back_to_parametric`
- [tests/test_probe_longform_families.py](../../../../../../tests/test_probe_longform_families.py) — direct import
  - `test_derivation_card_declares_ordered_obligations`
  - `test_derivation_family_passes_admission_gate`
  - `test_generation_produces_derivation_instance_with_obligation_rubric`
  - `test_integrative_gap_clears_with_derivation_card`
  - `test_longform_observation_records_trace_and_bounded_mass`
  - `test_procedure_knowledge_type_gets_derivation_family`
- [tests/test_probe_surface_mint.py](../../../../../../tests/test_probe_surface_mint.py) — direct import
  - `test_mint_refuses_a_surface_group_the_learner_has_seen`
  - `test_minted_surface_serves_through_the_probe_branch_and_is_single_use`
- [tests/test_structured_transport_parity.py](../../../../../../tests/test_structured_transport_parity.py) — direct import

## Modification guidance

- Change probe instance generation policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/probe_instance_generation.py](../../../../../../src/learnloop/diagnosis/probe_instance_generation.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
