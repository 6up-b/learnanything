---
title: "learnloop.goals.goal_contracts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/goals/goal_contracts.py"
source_paths:
  - "src/learnloop/goals/goal_contracts.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.goals.goal_contracts` exists within [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] to own the behavior summarized by its module contract: Terminal-contract versioning + consumer pins (spec_p0_measurement_correctness §3.4).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/goals/goal_contracts.py](../../../../../../src/learnloop/goals/goal_contracts.py) |
| Source lines | 853 |
| Owning package | [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class DraftNotConfirmable(Exception)` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 44) — A pre-confirmation draft fails the confirmation gate (§3.4).
  - `__init__(self, reason: str)` (line 47; internal)
- `class NotConfirmed(Exception)` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 52) — A successor was requested for a goal that has no confirmed head.
  - `__init__(self, goal_id: str)` (line 55; internal)
- `class UseDepthSuccessor(Exception)` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 60) — A support edit that advances the depth milestone must go through ``append_authorized_depth_successor`` (§3.4).
  - `__init__(self, goal_id: str)` (line 64; internal)
- `class NoTargetPin(Exception)` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 71) — A goal-conditioned terminal claim was requested but the administration has no target pin (§7.3 "missing target pin -> no goal-conditioned terminal claim").
  - `__init__(self, administration_id: str)` (line 75; internal)
- `class ContractVersion` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 85)
  - `as_dict(self) -> dict[str, Any]` (line 100; public)
- `class Draft` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 105)
  - `as_dict(self) -> dict[str, Any]` (line 113; public)
- `class SupportComparison` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 118)
  - `as_dict(self) -> dict[str, Any]` (line 125; public)
- `class ConsumerPin` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 130)
  - `as_dict(self) -> dict[str, Any]` (line 137; public)
- `class CertificationCitation` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 142)
  - `as_dict(self) -> dict[str, Any]` (line 156; public)
- `class DriftReport` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 161)
  - `as_dict(self) -> dict[str, Any]` (line 168; public)
- `canonicalize_body(body: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 176) — Normalize a proposed contract body to the canonical Layer-5 shape (§2.1).
- `support_hash(body: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 269)
- `content_hash(body: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 273)
- `compute_change_class(prev: Mapping[str, Any], new: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 277) — Service-computed change class with most-invalidating-wins precedence (§2.2).
- `confirm_goal_contract(repository: Repository, *, goal_id: str, contract_body: Mapping[str, Any], author: str='learner', vault: LoadedVault | None=None, clock: Clock | None=None) -> ContractVersion` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 370) — Validate the draft (>=1 exemplar + reviewed blueprint) and mint v1 (§3.4).
- `append_successor(repository: Repository, *, goal_id: str, proposed_body: Mapping[str, Any], author: str='learner', reason: str | None=None, vault: LoadedVault | None=None, clock: Clock | None=None) -> ContractVersion` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 437) — Append a successor with a SERVICE-computed change class (§2.2).
- `append_authorized_depth_successor(repository: Repository, *, goal_id: str, proposed_body: Mapping[str, Any], progression_decision: Mapping[str, Any] | None, predecessor_version_id: str | None=None, author: str='controller', vault: LoadedVault | None=None, clock: Clock | None=None) -> ContractVersion | Draft` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 494) — Fail-closed one-edge authorized depth step (§3.4).
- `resolve_head(repository: Repository, goal_id: str) -> ContractVersion | None` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 650) — The current head (O(1) via ``goal_contract_heads``).
- `compare_support(repository: Repository, *, goal_id: str, pinned_version_id: str | None) -> SupportComparison` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 660) — Projection-time representativeness of a pinned version vs the current head.
- `list_consumer_pins(repository: Repository, goal_id: str) -> list[ConsumerPin]` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 688) — UNION projection of every consumer pin for the goal (§1.5) with a live representativeness flag from :func:`compare_support`.
- `certify_from_administration(repository: Repository, *, administration_id: str, goal_conditioned: bool=True) -> CertificationCitation` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 714) — Cite the exact assessed target version and label its representativeness (§3.4, §4.5, §9.4).
- `detect_contract_drift(vault: LoadedVault, repository: Repository, goal_id: str) -> DriftReport` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 804) — Detect divergence between a confirmed goal's live YAML draft fields and its confirmed head (§3).

### Module constants

- `CONTRACT_SCHEMA_VERSION` ([src/learnloop/goals/goal_contracts.py](../../../../../../src/learnloop/goals/goal_contracts.py), line 35)
- `DEPTH_ENVELOPE_SNAPSHOT_SCHEMA_VERSION` ([src/learnloop/goals/goal_contracts.py](../../../../../../src/learnloop/goals/goal_contracts.py), line 36)
- `CHANGE_CLASS_PARTITION_VERSION` ([src/learnloop/goals/goal_contracts.py](../../../../../../src/learnloop/goals/goal_contracts.py), line 37)
- `_YAML_DRIFT_FIELDS` ([src/learnloop/goals/goal_contracts.py](../../../../../../src/learnloop/goals/goal_contracts.py), line 775)

## Internal implementation anchors

- `_exemplar_identities(body: Mapping[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 229)
- `_exemplar_weights(body: Mapping[str, Any]) -> list[list[Any]]` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 237)
- `_support_subset(body: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 241) — The SUPPORT-group projection whose hash is ``support_hash`` (§2.4).
- `_evaluation_subset(body: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 261)
- `_support_diff_touches_envelope(prev_body: Mapping[str, Any], new_body: Mapping[str, Any], envelope: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 289) — Does the support diff intersect the active envelope's reviewed-edge dimensions (M5, §3.4/§2.5)?
- `_envelope_version(body: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 333)
- `_row_to_version(row: Mapping[str, Any], *, minted: bool=True) -> ContractVersion` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 344)
- `_loads_json(value: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 362)
- `_yaml_subset_from_goal(goal: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 778)
- `_yaml_subset_from_body(body: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 792)
- `_mirror_head_to_yaml(vault: LoadedVault, goal_id: str, head_version_id: str, head_content_hash: str) -> None` ([source](../../../../../../src/learnloop/goals/goal_contracts.py), line 838) — The single controlled writer of the confirmed-head mirror into goals.yaml (§3).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/contracts|learnloop.cli.contracts]] — imports `module`; statically calls `append_successor`, `compute_change_class`, `detect_contract_drift`, `list_consumer_pins`, `resolve_head`
- [[Reference/Modules/learnloop/curriculum/depth_transition|learnloop.curriculum.depth_transition]] — imports `module`; statically calls `append_authorized_depth_successor`
- [[Reference/Modules/learnloop/curriculum/golden_path_assessment|learnloop.curriculum.golden_path_assessment]] — imports `module`; statically calls `certify_from_administration`
- [[Reference/Modules/learnloop/curriculum/golden_path_confirm|learnloop.curriculum.golden_path_confirm]] — imports `module`; statically calls `_envelope_version`, `canonicalize_body`, `content_hash`, `support_hash`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `resolve_head`; statically calls `resolve_head`
- [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]] — imports `resolve_head`; statically calls `resolve_head`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `detect_contract_drift`; statically calls `detect_contract_drift`
- [[Reference/Modules/learnloop/scheduling/reentry_adapter|learnloop.scheduling.reentry_adapter]] — imports `module`; statically calls `resolve_head`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `resolve_head`; statically calls `resolve_head`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
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

Static participation evidence comes from [[Reference/Modules/learnloop/cli/contracts|learnloop.cli.contracts]], [[Reference/Modules/learnloop/curriculum/depth_transition|learnloop.curriculum.depth_transition]], [[Reference/Modules/learnloop/curriculum/golden_path_assessment|learnloop.curriculum.golden_path_assessment]], [[Reference/Modules/learnloop/curriculum/golden_path_confirm|learnloop.curriculum.golden_path_confirm]], [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] and 4 more.

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

## Modification guidance

- Change goal contracts policy here when goals owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/goals/goal_contracts.py](../../../../../../src/learnloop/goals/goal_contracts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
