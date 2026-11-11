---
title: "learnloop.goals.goal_contracts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/goals/goal_contracts.py"
source_paths:
  - "src/learnloop/goals/goal_contracts.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.goals"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.goals.goal_contracts module"
  - "src/learnloop/goals/goal_contracts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-goals"
---

# `learnloop.goals.goal_contracts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.goals.goal_contracts` exists within [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] to own the behavior summarized by its module contract: Terminal-contract versioning + consumer pins (spec_p0_measurement_correctness §3.4).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/goals/goal_contracts.py](../../../../../../src/learnloop/goals/goal_contracts.py) |
| Source lines | 935 |
| Owning package | [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class DraftNotConfirmable(Exception)` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 46) — A pre-confirmation draft fails the confirmation gate (§3.4).
  - `__init__(self, reason: str)` (line 49; internal)
- `class NotConfirmed(Exception)` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 54) — A successor was requested for a goal that has no confirmed head.
  - `__init__(self, goal_id: str)` (line 57; internal)
- `class UseDepthSuccessor(Exception)` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 62) — A support edit that advances the depth milestone must go through ``append_authorized_depth_successor`` (§3.4).
  - `__init__(self, goal_id: str)` (line 66; internal)
- `class NoTargetPin(Exception)` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 73) — A goal-conditioned terminal claim was requested but the administration has no target pin (§7.3 "missing target pin -> no goal-conditioned terminal claim").
  - `__init__(self, administration_id: str)` (line 77; internal)
- `class ContractVersion` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 87)
  - `as_dict(self) -> dict[str, Any]` (line 102; public)
- `class Draft` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 107)
  - `as_dict(self) -> dict[str, Any]` (line 115; public)
- `class SupportComparison` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 120)
  - `as_dict(self) -> dict[str, Any]` (line 127; public)
- `class ConsumerPin` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 132)
  - `as_dict(self) -> dict[str, Any]` (line 139; public)
- `class CertificationCitation` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 144)
  - `as_dict(self) -> dict[str, Any]` (line 158; public)
- `class DriftReport` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 163)
  - `as_dict(self) -> dict[str, Any]` (line 170; public)
- `canonicalize_body(body: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 178) — Normalize a proposed contract body to the canonical Layer-5 shape (§2.1).
- `canonical_use_weight(value: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 236) — RO4 §8.5: ``{"dated": ω, "per_lo": {lo: ω_L}, "undated_density": c}`` with every number a float >= 0.
- `support_hash(body: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 303)
- `content_hash(body: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 307)
- `compute_change_class(prev: Mapping[str, Any], new: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 311) — Service-computed change class with most-invalidating-wins precedence (§2.2).
- `confirm_goal_contract(repository: Repository, *, goal_id: str, contract_body: Mapping[str, Any], author: str='learner', vault: LoadedVault | None=None, clock: Clock | None=None) -> ContractVersion` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 408) — Validate the draft (>=1 exemplar + reviewed blueprint) and mint v1 (§3.4).
- `set_use_weight(repository: Repository, *, goal_id: str, use_weight: Mapping[str, Any], author: str='learner', vault: LoadedVault | None=None, clock: Clock | None=None) -> ContractVersion` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 497) — RO4 §8.5: adjust a confirmed goal's use weights: a successor whose class is ``use_weight_change`` (the support hash unchanged).
- `append_successor(repository: Repository, *, goal_id: str, proposed_body: Mapping[str, Any], author: str='learner', reason: str | None=None, vault: LoadedVault | None=None, clock: Clock | None=None) -> ContractVersion` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 519) — Append a successor with a SERVICE-computed change class (§2.2).
- `append_authorized_depth_successor(repository: Repository, *, goal_id: str, proposed_body: Mapping[str, Any], progression_decision: Mapping[str, Any] | None, predecessor_version_id: str | None=None, author: str='controller', vault: LoadedVault | None=None, clock: Clock | None=None) -> ContractVersion | Draft` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 576) — Fail-closed one-edge authorized depth step (§3.4).
- `resolve_head(repository: Repository, goal_id: str) -> ContractVersion | None` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 732) — The current head (O(1) via ``goal_contract_heads``).
- `compare_support(repository: Repository, *, goal_id: str, pinned_version_id: str | None) -> SupportComparison` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 742) — Projection-time representativeness of a pinned version vs the current head.
- `list_consumer_pins(repository: Repository, goal_id: str) -> list[ConsumerPin]` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 770) — UNION projection of every consumer pin for the goal (§1.5) with a live representativeness flag from :func:`compare_support`.
- `certify_from_administration(repository: Repository, *, administration_id: str, goal_conditioned: bool=True) -> CertificationCitation` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 796) — Cite the exact assessed target version and label its representativeness (§3.4, §4.5, §9.4).
- `detect_contract_drift(vault: LoadedVault, repository: Repository, goal_id: str) -> DriftReport` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 886) — Detect divergence between a confirmed goal's live YAML draft fields and its confirmed head (§3).

### Module constants

- `CONTRACT_SCHEMA_VERSION` ([src/learnloop/goals/goal_contracts.py](../../../../../../src/learnloop/goals/goal_contracts.py), line 35)
- `DEPTH_ENVELOPE_SNAPSHOT_SCHEMA_VERSION` ([src/learnloop/goals/goal_contracts.py](../../../../../../src/learnloop/goals/goal_contracts.py), line 36)
- `CHANGE_CLASS_PARTITION_VERSION` ([src/learnloop/goals/goal_contracts.py](../../../../../../src/learnloop/goals/goal_contracts.py), line 37)
- `USE_WEIGHT_CHANGE` ([src/learnloop/goals/goal_contracts.py](../../../../../../src/learnloop/goals/goal_contracts.py), line 39)
- `_YAML_DRIFT_FIELDS` ([src/learnloop/goals/goal_contracts.py](../../../../../../src/learnloop/goals/goal_contracts.py), line 857)

## Internal implementation anchors

- `_use_weight_subset(body: Mapping[str, Any]) -> Any` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 259)
- `_exemplar_identities(body: Mapping[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 263)
- `_exemplar_weights(body: Mapping[str, Any]) -> list[list[Any]]` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 271)
- `_support_subset(body: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 275) — The SUPPORT-group projection whose hash is ``support_hash`` (§2.4).
- `_evaluation_subset(body: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 295)
- `_support_diff_touches_envelope(prev_body: Mapping[str, Any], new_body: Mapping[str, Any], envelope: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 327) — Does the support diff intersect the active envelope's reviewed-edge dimensions (M5, §3.4/§2.5)?
- `_envelope_version(body: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 371)
- `_row_to_version(row: Mapping[str, Any], *, minted: bool=True) -> ContractVersion` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 382)
- `_loads_json(value: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 400)
- `_with_use_weight(body: Mapping[str, Any], goal_id: str, vault: LoadedVault | None) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 475) — Router objective RO4 (§8.5): a contract confirmed at the tag carries the goal's use weights, the ones its goal was created with (else the config's, copied now).
- `_yaml_subset_from_goal(goal: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 860)
- `_yaml_subset_from_body(body: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 874)
- `_mirror_head_to_yaml(vault: LoadedVault, goal_id: str, head_version_id: str, head_content_hash: str) -> None` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 920) — The single controlled writer of the confirmed-head mirror into goals.yaml (§3).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/contracts|learnloop.cli.contracts]] — imports `module`; statically calls `append_successor`, `compute_change_class`, `detect_contract_drift`, `list_consumer_pins`, `resolve_head`
- [[Reference/Modules/learnloop/curriculum/depth_transition|learnloop.curriculum.depth_transition]] — imports `module`; statically calls `append_authorized_depth_successor`
- [[Reference/Modules/learnloop/curriculum/golden_path_assessment|learnloop.curriculum.golden_path_assessment]] — imports `module`; statically calls `certify_from_administration`
- [[Reference/Modules/learnloop/curriculum/golden_path_confirm|learnloop.curriculum.golden_path_confirm]] — imports `module`; statically calls `_envelope_version`, `canonicalize_body`, `content_hash`, `support_hash`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `resolve_head`; statically calls `resolve_head`
- [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]] — imports `resolve_head`; statically calls `resolve_head`
- [[Reference/Modules/learnloop/goals/use_weights|learnloop.goals.use_weights]] — imports `canonical_use_weight`; statically calls `canonical_use_weight`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `detect_contract_drift`; statically calls `detect_contract_drift`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `resolve_head`; statically calls `resolve_head`
- [[Reference/Modules/learnloop_sidecar/handlers/router_objective|learnloop_sidecar.handlers.router_objective]] — imports `module`; statically calls `canonical_use_weight`, `set_use_weight`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/goals/use_weights|learnloop.goals.use_weights]] — imports `COPIED`, `copy_at_creation`, `for_goal`; calls `copy_at_creation`, `for_goal`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `objective_on`; calls `objective_on`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_hash`, `canonical_json`; calls `canonical_hash`, `canonical_json`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] — imports `read_yaml`, `write_yaml`; calls `read_yaml`, `write_yaml`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/contracts|learnloop.cli.contracts]], [[Reference/Modules/learnloop/curriculum/depth_transition|learnloop.curriculum.depth_transition]], [[Reference/Modules/learnloop/curriculum/golden_path_assessment|learnloop.curriculum.golden_path_assessment]], [[Reference/Modules/learnloop/curriculum/golden_path_confirm|learnloop.curriculum.golden_path_confirm]], [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_assessment_enforcement.py](../../../../../../tests/test_assessment_enforcement.py) — direct import
  - `test_detect_contract_drift_and_doctor_surface`
- [tests/test_goal_contracts.py](../../../../../../tests/test_goal_contracts.py) — direct import
  - `test_append_successor_allows_ungoverned_support_change_with_envelope`
  - `test_append_successor_plain_support_change_without_envelope`
  - `test_append_successor_refuses_envelope_dimension_edit_without_milestone`
  - `test_append_successor_refuses_milestone_advance`
  - `test_append_successor_requires_confirmed_head`
  - `test_append_version_rejects_stale_predecessor`
  - `test_certification_cites_exact_assessed_version`
  - `test_certification_non_terminal_when_feedback_before_response`
  - `test_certification_terminal_when_observation_terminal`
  - `test_certify_missing_target_pin_raises`
  - `test_confirm_without_blueprint_raises`
  - `test_confirm_without_exemplar_raises_and_records_draft`
  - `test_deeper_successor_preserves_earlier_certification`
  - `test_depth_admin_condition_change_authorized_when_bounds_name_it`
  - `test_depth_edge_matching_but_flips_admin_condition_rejected`
  - `test_depth_insufficient_evidence_rejected`
  - `test_depth_multiple_edges_rejected`
  - `test_depth_predecessor_not_head_rejected`
  - `test_depth_rejections_become_nonpinnable_drafts`
  - `test_depth_stale_envelope_rejected`
  - `test_every_edit_appends_successor_prior_bytes_unchanged`
  - `test_list_consumer_pins_unions_reserve_and_admin`
  - `test_one_reviewed_in_envelope_edge_appends_one_authorized_depth_step`
  - `test_progression_reads_latest_head`
  - `test_support_change_flags_reserve_reweight_does_not`
- [tests/test_p2_acceptance.py](../../../../../../tests/test_p2_acceptance.py) — direct import
  - `test_event_replay_equivalence_after_full_walk`
- [tests/test_ro4_goals.py](../../../../../../tests/test_ro4_goals.py) — direct import
  - `test_a_body_without_use_weights_keeps_its_bytes_and_hash`
  - `test_the_contract_is_copied_at_confirmation_at_the_tag_and_adjustable`
  - `test_use_weights_are_in_the_content_hash_and_out_of_the_support_hash`

## Modification guidance

- Change goal contracts policy here when goals owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/goals/goal_contracts.py](../../../../../../src/learnloop/goals/goal_contracts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
