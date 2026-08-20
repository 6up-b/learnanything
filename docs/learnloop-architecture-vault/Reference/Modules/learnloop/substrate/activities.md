---
title: "learnloop.substrate.activities"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/activities.py"
source_paths:
  - "src/learnloop/substrate/activities.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.substrate"
layer: "domain"
concepts:
  - "Learning System"
  - "State and Persistence"
workflows:
  - "Inspect Persistent State"
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.substrate.activities module"
  - "src/learnloop/substrate/activities.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.activities`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.activities` exists within [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] to own the behavior summarized by its module contract: Activity lineage substrate services (spec_p0_measurement_correctness §3.5-§3.8).

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/activities.py](../../../../../../src/learnloop/substrate/activities.py) |
| Source lines | 1253 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class SurfaceAlreadyReserved(Exception)` ([source](../../../../../../src/learnloop/substrate/activities.py), line 59) — Raised when a surface already has a live (uncancelled) reservation.
  - `__init__(self, surface_id: str)` (line 62; internal)
- `class ExposureCollisionAtRender(Exception)` ([source](../../../../../../src/learnloop/substrate/activities.py), line 67) — Raised when an assessment render collides with a prior exposure inside the burn lock (§4.5, §7.3 "exposure collision at render -> refuse ...
  - `__init__(self, surface_id: str, reason: str)` (line 72; internal)
- `canonical_json(payload: Any) -> str` ([source](../../../../../../src/learnloop/substrate/activities.py), line 78)
- `canonical_hash(payload: Any) -> str` ([source](../../../../../../src/learnloop/substrate/activities.py), line 88) — 32-char unprefixed sha256 over canonical JSON (matches ``assessment_contracts._content_hash`` for legacy->split hash continuity).
- `card_semantic_payload(contract: Mapping[str, Any], *, purpose: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/activities.py), line 107) — The semantic-claim partition of a compiled contract (§3.5 card_contract_hash).
- `surface_payload(contract: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/activities.py), line 172) — The exact-presentation partition of a compiled contract (§3.5 surface_hash).
- `fingerprint_of(contract: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/substrate/activities.py), line 183) — Shared-stimulus/near-clone key (§3.6 rule 2) from the evidence fingerprint.
- `card_contract_hash(contract: Mapping[str, Any], *, purpose: str) -> str` ([source](../../../../../../src/learnloop/substrate/activities.py), line 196)
- `surface_hash(contract: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/substrate/activities.py), line 200)
- `administration_snapshot_hash(payload: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/substrate/activities.py), line 204)
- `class ResolvedActivity` ([source](../../../../../../src/learnloop/substrate/activities.py), line 213)
  - `as_dict(self) -> dict[str, Any]` (line 224; public)
- `class Eligibility` ([source](../../../../../../src/learnloop/substrate/activities.py), line 229)
  - `as_dict(self) -> dict[str, Any]` (line 234; public)
- `class Reservation` ([source](../../../../../../src/learnloop/substrate/activities.py), line 239)
  - `as_dict(self) -> dict[str, Any]` (line 245; public)
- `class Administration` ([source](../../../../../../src/learnloop/substrate/activities.py), line 251)
  - `as_dict(self) -> dict[str, Any]` (line 260; public)
- `class RenderRefused` ([source](../../../../../../src/learnloop/substrate/activities.py), line 265) — No fresh eligible surface remained after an exposure collision (§4.5).
  - `as_dict(self) -> dict[str, Any]` (line 271; public)
- `resolve_legacy_item(vault: LoadedVault, repository: Repository, item: PracticeItem, *, purpose: str, rubric: Any | None=None, clock: Clock | None=None) -> ResolvedActivity` ([source](../../../../../../src/learnloop/substrate/activities.py), line 279) — Deterministic, idempotent legacy item -> family/card/surface resolution.
- `evaluate_held_out_eligibility(repository: Repository, *, surface: Mapping[str, Any], purpose: str) -> Eligibility` ([source](../../../../../../src/learnloop/substrate/activities.py), line 355) — The four §3.6 rules against ``activity_exposure_events`` (the ONE ledger).
- `reserve_surface(repository: Repository, *, surface_id: str, purpose: str, goal_id: str | None=None, target_contract_version_id: str | None=None, target_support_hash: str | None=None, clock: Clock | None=None) -> Reservation` ([source](../../../../../../src/learnloop/substrate/activities.py), line 396) — Reserve a surface from the pinned target's frozen distribution (§4.5).
- `cancel_reservation(repository: Repository, reservation_id: str, *, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/substrate/activities.py), line 443) — Cancel a reservation.
- `open_administration(repository: Repository, *, resolved: ResolvedActivity, reservation: Reservation | None=None, goal_id: str | None=None, target_contract_version_id: str | None=None, target_support_hash: str | None=None, grader_model_version_id: str | None=None, selection_policy_version_id: str | None=None, decision_params_hash: str | None=None, assistance: Mapping[str, Any] | None=None, feedback_condition: str | None=None, algorithm_version: str | None=None, head_support_hash: str | None=None, enforce_eligibility: bool | None=None, clock: Clock | None=None) -> Administration` ([source](../../../../../../src/learnloop/substrate/activities.py), line 492) — The atomic render/burn boundary (§4.5).
- `render_assessment_with_replacement(repository: Repository, *, candidates: list[ResolvedActivity], goal_id: str | None=None, target_contract_version_id: str | None=None, target_support_hash: str | None=None, head_support_hash: str | None=None, feedback_condition: str | None=None, algorithm_version: str | None=None, clock: Clock | None=None) -> Administration | RenderRefused` ([source](../../../../../../src/learnloop/substrate/activities.py), line 607) — Draw the next eligible surface from the pinned target's frozen distribution on an exposure collision (§4.5, §7.3 row 7).
- `append_practice_successor_proposal(repository: Repository, *, surface_id: str, administration_id: str | None=None, not_before: str | None=None, reason: str | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/substrate/activities.py), line 662) — Record a practice-successor PROPOSAL after a failed assessment with feedback (§4.5, §9.5 line 4).
- `append_exposure(repository: Repository, *, surface: Mapping[str, Any], administration_id: str | None, kind: str, purpose: str, consumes_unseen: bool | None=None, detail: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/substrate/activities.py), line 690)
- `append_feedback(repository: Repository, *, surface: Mapping[str, Any], administration_id: str | None, purpose: str, timing: str, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/substrate/activities.py), line 716) — Append a ``feedback_revealed`` exposure.
- `append_lifecycle(repository: Repository, *, surface_id: str, kind: str, reservation_id: str | None=None, administration_id: str | None=None, reason: str | None=None, detail: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/substrate/activities.py), line 742)
- `evidence_eligibility_for(*, purpose: str, feedback_condition: str | None) -> tuple[str, str]` ([source](../../../../../../src/learnloop/substrate/activities.py), line 764) — Purpose+feedback -> (evidence_eligibility, reason) for an observation (§3.6/§4.5).
- `append_observation(repository: Repository, *, administration_id: str, surface_id: str, purpose: str, feedback_condition: str | None=None, attempt_id: str | None=None, response_ref: str | None=None, algorithm_version: str | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/substrate/activities.py), line 784) — Record one response/attempt observation with its purpose-specific evidence eligibility, and anchor a ``response_appended`` measurement event (§3.5, §4.1).
- `retire_with_reason(repository: Repository, *, scope: str, reason: str, provenance: str, family_id: str | None=None, card_version_id: str | None=None, surface_id: str | None=None, replacement_proposal: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/substrate/activities.py), line 825) — Retire a family/card/surface (§3.7).
- `log_interaction_event(repository: Repository, *, kind: str, origin: str='learner', subject_type: str | None=None, subject_id: str | None=None, administration_id: str | None=None, surface_id: str | None=None, attempt_id: str | None=None, affect_tap_kind: str | None=None, attempt_duration_ms: int | None=None, payload: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/substrate/activities.py), line 906) — The single writer for the Layer-5 interaction envelope (§3.8).
- `log_attempt_duration(repository: Repository, *, administration_id: str | None, attempt_id: str | None, duration_ms: int, surface_id: str | None=None, origin: str='learner', clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/substrate/activities.py), line 949) — Log an attempt duration (§3.8, review-burden accounting / stop-mode cost).
- `log_affect_tap(repository: Repository, *, affect_tap_kind: str, subject_type: str | None=None, subject_id: str | None=None, administration_id: str | None=None, surface_id: str | None=None, attempt_id: str | None=None, origin: str='learner', payload: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/substrate/activities.py), line 973) — Capture an affect tap (§4.6).
- `class FamilyPurposeImmutable(Exception)` ([source](../../../../../../src/learnloop/substrate/activities.py), line 1028) — A family's authoring purpose cannot change in place; cross-purpose reuse must create a separately gated family (§1.1 invariant 2, §9.1).
  - `__init__(self, family_id: str, existing: str, requested: str)` (line 1032; internal)
- `class CrossPurposeIdentityReuse(Exception)` ([source](../../../../../../src/learnloop/substrate/activities.py), line 1042) — A cross-purpose link tried to reuse the same activity identity (§9.1).
- `class InvalidAuthoring(Exception)` ([source](../../../../../../src/learnloop/substrate/activities.py), line 1046) — Authoring input violated a closed vocabulary or contract.
- `author_family_version(repository: Repository, *, family_id: str, version: int, authoring_purpose: str, family_spec: Mapping[str, Any], pattern_version_id: str | None=None, progression_policy_version_id: str | None=None, commitment_id: str | None=None, commitment_target_version_id: str | None=None, goal_contract_version_id: str | None=None, depth_policy_version_id: str | None=None, depth_envelope_version_id: str | None=None, served_milestone_edges: Any | None=None, angle_inventory: Any | None=None, coverage_targets: Any | None=None, cross_purpose_links: Sequence[Mapping[str, Any]] | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/substrate/activities.py), line 1050) — Stage 1-3 of the §5.1 authoring transaction: resolve target + policy/pattern and create a DRAFT family version (idempotent on ``(family_id, version)``) plus its authoring side row.
- `activate_family_version(repository: Repository, *, family_version_id: str) -> None` ([source](../../../../../../src/learnloop/substrate/activities.py), line 1115) — Activate a drafted family version (§5.1 stage 6).
- `link_cross_purpose_families(repository: Repository, *, family_version_id: str, links: Sequence[Mapping[str, Any]], clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/activities.py), line 1150) — Attach typed cross-purpose family links (§3.6).
- `pin_card_authoring(repository: Repository, *, card_version_id: str, family_version_id: str | None=None, pattern_version_id: str | None=None, task_feature_schema_version_id: str | None=None, task_features: Mapping[str, Any] | None=None, capability: str | None=None, outcome_schema_id: str | None=None, outcome_schema_version: int | None=None, surface_policy: str | None=None, surface_variation_bounds: Mapping[str, Any] | None=None, angle_identity: Mapping[str, Any] | None=None, generator_version: str | None=None, gate_policy_version: str | None=None, expected_burden: Mapping[str, Any] | None=None, calibration_metadata: Mapping[str, Any] | None=None, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/substrate/activities.py), line 1174) — Pin the P1 card-version authoring contract (§3.7) as a side row keyed by the P0 immutable card version id.
- `resolve_progression_policy(repository: Repository, family_version_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/substrate/activities.py), line 1223) — Resolve the progression policy pinned on a family version (§3.6, §6).
- `inspect_angle_coverage(repository: Repository, family_version_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/activities.py), line 1241) — Inspect a family version's declared angle inventory and coverage targets (§5.4, §6 CLI parity).

### Module constants

- `_CONSUMING_PURPOSES` ([src/learnloop/substrate/activities.py](../../../../../../src/learnloop/substrate/activities.py), line 42)
- `_PURPOSE_TO_LEGACY_KIND` ([src/learnloop/substrate/activities.py](../../../../../../src/learnloop/substrate/activities.py), line 44)
- `_PROVENANCE_TO_ORIGIN` ([src/learnloop/substrate/activities.py](../../../../../../src/learnloop/substrate/activities.py), line 52)
- `_AUTHORING_PURPOSES` ([src/learnloop/substrate/activities.py](../../../../../../src/learnloop/substrate/activities.py), line 1015)
- `_CROSS_PURPOSE_LINK_KINDS` ([src/learnloop/substrate/activities.py](../../../../../../src/learnloop/substrate/activities.py), line 1019)
- `_P1_CAPABILITIES` ([src/learnloop/substrate/activities.py](../../../../../../src/learnloop/substrate/activities.py), line 1023)

## Internal implementation anchors

- `_loads(value: str | None, default: Any=None) -> Any` ([source](../../../../../../src/learnloop/substrate/activities.py), line 82)
- `_algorithm_version(explicit: str | None) -> str` ([source](../../../../../../src/learnloop/substrate/activities.py), line 95)
- `_validate_cross_purpose_links(repository: Repository, family_version_id: str, cross_purpose_links: Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/activities.py), line 1125)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `evidence_eligibility_for`; statically calls `evidence_eligibility_for`
- [[Reference/Modules/learnloop/attempts/calibration_streams|learnloop.attempts.calibration_streams]] — imports `canonical_json`; statically calls `canonical_json`
- [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]] — imports `append_observation`, `canonical_json`, `open_administration`, `resolve_legacy_item`; statically calls `append_observation`, `canonical_json`, `open_administration`, `resolve_legacy_item`
- [[Reference/Modules/learnloop/attempts/grader_calibration|learnloop.attempts.grader_calibration]] — imports `canonical_hash`, `canonical_json`; statically calls `canonical_hash`, `canonical_json`
- [[Reference/Modules/learnloop/attempts/outcome_schemas|learnloop.attempts.outcome_schemas]] — imports `canonical_hash`, `canonical_json`; statically calls `canonical_hash`, `canonical_json`
- [[Reference/Modules/learnloop/cli/surfaces|learnloop.cli.surfaces]] — imports `evaluate_held_out_eligibility`, `retire_with_reason`; statically calls `evaluate_held_out_eligibility`, `retire_with_reason`
- [[Reference/Modules/learnloop/content/authoring/item_authoring|learnloop.content.authoring.item_authoring]] — imports `retire_with_reason`; statically calls `retire_with_reason`
- [[Reference/Modules/learnloop/curriculum/commitment_arcs|learnloop.curriculum.commitment_arcs]] — imports `canonical_hash`, `canonical_json`; statically calls `canonical_hash`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `canonical_hash`, `canonical_json`; statically calls `canonical_hash`, `canonical_json`
- [[Reference/Modules/learnloop/curriculum/depth_edge_authoring|learnloop.curriculum.depth_edge_authoring]] — imports `canonical_hash`; statically calls `canonical_hash`
- [[Reference/Modules/learnloop/curriculum/depth_transition|learnloop.curriculum.depth_transition]] — imports `canonical_hash`, `canonical_json`; statically calls `canonical_hash`, `canonical_json`
- [[Reference/Modules/learnloop/curriculum/golden_path_assessment|learnloop.curriculum.golden_path_assessment]] — imports `Administration`, `ExposureCollisionAtRender`, `ResolvedActivity`, `append_feedback`, `append_observation`, `append_practice_successor_proposal`, `cancel_reservation`, `canonical_json`, `evaluate_held_out_eligibility`, `open_administration`; statically calls `ResolvedActivity`, `append_feedback`, `append_observation`, `append_practice_successor_proposal`, `cancel_reservation`, `canonical_json`, `evaluate_held_out_eligibility`, `open_administration`
- [[Reference/Modules/learnloop/curriculum/golden_path_confirm|learnloop.curriculum.golden_path_confirm]] — imports `canonical_hash`, `canonical_json`; statically calls `canonical_hash`, `canonical_json`
- [[Reference/Modules/learnloop/curriculum/golden_path_fixture|learnloop.curriculum.golden_path_fixture]] — imports `resolve_legacy_item`; statically calls `resolve_legacy_item`
- [[Reference/Modules/learnloop/curriculum/golden_path_restoration|learnloop.curriculum.golden_path_restoration]] — imports `canonical_json`; statically calls `canonical_json`
- [[Reference/Modules/learnloop/curriculum/golden_path_run|learnloop.curriculum.golden_path_run]] — imports `canonical_json`; statically calls `canonical_json`
- [[Reference/Modules/learnloop/curriculum/pattern_ladder|learnloop.curriculum.pattern_ladder]] — imports `canonical_json`; statically calls `canonical_json`
- [[Reference/Modules/learnloop/curriculum/task_blueprints|learnloop.curriculum.task_blueprints]] — imports `canonical_hash`, `canonical_json`; statically calls `canonical_hash`, `canonical_json`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_pack|learnloop.diagnosis.diagnostic_pack]] — imports `canonical_hash`, `canonical_json`; statically calls `canonical_hash`, `canonical_json`
- [[Reference/Modules/learnloop/diagnosis/failure_triage|learnloop.diagnosis.failure_triage]] — imports `canonical_json`; statically calls `canonical_json`
- [[Reference/Modules/learnloop/diagnosis/robust_composition|learnloop.diagnosis.robust_composition]] — imports `canonical_hash`; statically calls `canonical_hash`
- [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]] — imports `SurfaceAlreadyReserved`, `reserve_surface`, `resolve_legacy_item`; statically calls `reserve_surface`, `resolve_legacy_item`
- [[Reference/Modules/learnloop/goals/goal_contracts|learnloop.goals.goal_contracts]] — imports `canonical_hash`, `canonical_json`; statically calls `canonical_hash`, `canonical_json`
- [[Reference/Modules/learnloop/params/parameter_registry|learnloop.params.parameter_registry]] — imports `canonical_hash`; statically calls `canonical_hash`
- [[Reference/Modules/learnloop/params/sensitivity_certificates|learnloop.params.sensitivity_certificates]] — imports `canonical_hash`; statically calls `canonical_hash`
- [[Reference/Modules/learnloop/reader/reader_authoring|learnloop.reader.reader_authoring]] — imports `canonical_hash`, `canonical_json`, `log_interaction_event`; statically calls `canonical_hash`, `canonical_json`, `log_interaction_event`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `append_exposure`, `log_interaction_event`, `open_administration`, `reserve_surface`, `resolve_legacy_item`; statically calls `append_exposure`, `log_interaction_event`, `open_administration`, `reserve_surface`, `resolve_legacy_item`
- [[Reference/Modules/learnloop/reader/reader_restoration|learnloop.reader.reader_restoration]] — imports `log_interaction_event`; statically calls `log_interaction_event`
- [[Reference/Modules/learnloop/scheduling/action_loss|learnloop.scheduling.action_loss]] — imports `canonical_hash`; statically calls `canonical_hash`
- [[Reference/Modules/learnloop/scheduling/constraint_engine|learnloop.scheduling.constraint_engine]] — imports `canonical_hash`; statically calls `canonical_hash`
- [[Reference/Modules/learnloop/scheduling/controller_ownership|learnloop.scheduling.controller_ownership]] — imports `canonical_json`; statically calls `canonical_json`
- [[Reference/Modules/learnloop/scheduling/controller_snapshot|learnloop.scheduling.controller_snapshot]] — imports `canonical_hash`; statically calls `canonical_hash`
- [[Reference/Modules/learnloop/scheduling/controller_store|learnloop.scheduling.controller_store]] — imports `canonical_json`; statically calls `canonical_json`
- [[Reference/Modules/learnloop/scheduling/kinship_feature|learnloop.scheduling.kinship_feature]] — imports `canonical_hash`; statically calls `canonical_hash`
- [[Reference/Modules/learnloop/scheduling/predictive_targets|learnloop.scheduling.predictive_targets]] — imports `canonical_hash`; statically calls `canonical_hash`
- [[Reference/Modules/learnloop/scheduling/prequential|learnloop.scheduling.prequential]] — imports `canonical_hash`; statically calls `canonical_hash`
- [[Reference/Modules/learnloop/scheduling/progression|learnloop.scheduling.progression]] — imports `canonical_hash`, `canonical_json`, `resolve_progression_policy`; statically calls `canonical_hash`, `canonical_json`, `resolve_progression_policy`
- [[Reference/Modules/learnloop/scheduling/progression_policy|learnloop.scheduling.progression_policy]] — imports `canonical_hash`, `canonical_json`; statically calls `canonical_hash`, `canonical_json`
- [[Reference/Modules/learnloop/scheduling/shadow_components|learnloop.scheduling.shadow_components]] — imports `canonical_hash`; statically calls `canonical_hash`
- [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]] — imports `canonical_hash`; statically calls `canonical_hash`
- [[Reference/Modules/learnloop/substrate/activity_patterns|learnloop.substrate.activity_patterns]] — imports `canonical_hash`, `canonical_json`; statically calls `canonical_hash`, `canonical_json`
- [[Reference/Modules/learnloop/substrate/compat/activity_backfill|learnloop.substrate.compat.activity_backfill]] — imports `_CONSUMING_PURPOSES`, `_PURPOSE_TO_LEGACY_KIND`, `administration_snapshot_hash`, `canonical_hash`, `canonical_json`, `card_contract_hash`, `card_semantic_payload`, `fingerprint_of`, `resolve_legacy_item`, `surface_hash`, `surface_payload`; statically calls `administration_snapshot_hash`, `canonical_hash`, `canonical_json`, `card_contract_hash`, `card_semantic_payload`, `fingerprint_of`, `resolve_legacy_item`, `surface_hash`, `surface_payload`
- [[Reference/Modules/learnloop/substrate/compat/substrate_cutover|learnloop.substrate.compat.substrate_cutover]] — imports `module`; statically calls `canonical_hash`, `canonical_json`, `evidence_eligibility_for`
- [[Reference/Modules/learnloop/substrate/surface_mint|learnloop.substrate.surface_mint]] — imports `canonical_json`; statically calls `canonical_json`
- [[Reference/Modules/learnloop/substrate/surface_pool|learnloop.substrate.surface_pool]] — imports `Administration`, `ResolvedActivity`, `canonical_hash`, `canonical_json`, `open_administration`, `reserve_surface`; statically calls `canonical_hash`, `canonical_json`, `open_administration`, `reserve_surface`
- [[Reference/Modules/learnloop_sidecar/handlers/golden_path|learnloop_sidecar.handlers.golden_path]] — imports `resolve_legacy_item`; statically calls `resolve_legacy_item`
- [[Reference/Modules/learnloop_sidecar/handlers/ladder|learnloop_sidecar.handlers.ladder]] — imports `resolve_legacy_item`; statically calls `resolve_legacy_item`

### Repository tooling consumers

- [scripts/gen_goldenpath_fixtures.py](../../../../../../scripts/gen_goldenpath_fixtures.py); calls `resolve_legacy_item`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/salience_firewall|learnloop.attempts.salience_firewall]] — imports `READING_EVENT_KINDS`, `SALIENCE_ONLY`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `LearnLoopConfig`; calls `LearnLoopConfig`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `compile_assessment_contract`; calls `compile_assessment_contract`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/calibration_streams|learnloop.attempts.calibration_streams]], [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]], [[Reference/Modules/learnloop/attempts/grader_calibration|learnloop.attempts.grader_calibration]], [[Reference/Modules/learnloop/attempts/outcome_schemas|learnloop.attempts.outcome_schemas]] and 42 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_action_loss.py](../../../../../../tests/test_action_loss.py) — direct import
  - `test_durations_fall_back_to_logged_pooled_then_heuristic`
- [tests/test_activity_contract_extensions.py](../../../../../../tests/test_activity_contract_extensions.py) — direct import
  - `test_authoring_is_idempotent_and_starts_as_draft`
  - `test_cross_purpose_link_rejects_self_identity`
  - `test_cross_purpose_link_to_other_family`
  - `test_family_purpose_immutable_in_place`
  - `test_inspect_angle_coverage`
  - `test_pin_card_authoring`
  - `test_resolve_progression_policy`
- [tests/test_activity_substrate.py](../../../../../../tests/test_activity_substrate.py) — direct import
  - `test_cancel_after_render_does_not_restore_pristine`
  - `test_cancel_after_render_emits_no_release_unseen_lifecycle`
  - `test_concurrent_render_exposes_at_most_once`
  - `test_cross_purpose_exact_and_near_clone_block_unseen`
  - `test_feedback_before_response_yields_no_terminal_credit`
  - `test_interaction_event_written_for_attempt_duration`
  - `test_render_is_the_burn_boundary`
  - `test_reserve_then_cancel_before_render_releases_unseen`
  - `test_resolve_legacy_item_is_deterministic_and_idempotent`
  - `test_retire_with_reason_records_and_preserves_evidence`
  - `test_second_live_reservation_is_rejected`
- [tests/test_administration_adapters.py](../../../../../../tests/test_administration_adapters.py) — direct import
- [tests/test_assessment_enforcement.py](../../../../../../tests/test_assessment_enforcement.py) — direct import
  - `test_exposure_collision_at_render_refuses`
  - `test_failed_with_feedback_appends_practice_successor_proposal`
  - `test_regrade_never_reverses_burn`
  - `test_render_marks_unrepresentative_when_head_support_moved`
  - `test_render_with_replacement_refuses_when_exhausted`
  - `test_render_with_replacement_substitutes_fresh_surface`
  - `test_two_concurrent_renders_expose_once`
- [tests/test_card_lineage.py](../../../../../../tests/test_card_lineage.py) — direct import
- [tests/test_commitment_arcs.py](../../../../../../tests/test_commitment_arcs.py) — direct import
- [tests/test_controller_cutover.py](../../../../../../tests/test_controller_cutover.py) — direct import
  - `test_all_six_cutover_gates_pass_in_order`
- [tests/test_cross_seam_exposure.py](../../../../../../tests/test_cross_seam_exposure.py) — direct import
  - `test_near_clone_collision_loser_is_refused_not_double_exposed`
  - `test_same_surface_exactly_one_wins_via_shared_ledger`
  - `test_stale_ownership_still_prevents_double_administration`
- [tests/test_depth_transition.py](../../../../../../tests/test_depth_transition.py) — direct import
- [tests/test_event_sufficiency.py](../../../../../../tests/test_event_sufficiency.py) — direct import
- [tests/test_familiarity.py](../../../../../../tests/test_familiarity.py) — direct import
- [tests/test_goal_contracts.py](../../../../../../tests/test_goal_contracts.py) — direct import
  - `test_certification_non_terminal_when_feedback_before_response`
- [tests/test_golden_path_assessment.py](../../../../../../tests/test_golden_path_assessment.py) — direct import
  - `test_burned_surface_refuses_and_run_degrades`
- [tests/test_golden_path_confirm.py](../../../../../../tests/test_golden_path_confirm.py) — direct import
- [tests/test_golden_path_run.py](../../../../../../tests/test_golden_path_run.py) — direct import
- [tests/test_hot_path_eligibility_cutover.py](../../../../../../tests/test_hot_path_eligibility_cutover.py) — direct import
  - `test_first_ever_ineligible_observation_creates_no_memory_state`
  - `test_ineligible_observation_leaves_mvp08_scheduling_untouched_but_legacy_writes`
- [tests/test_journey6.py](../../../../../../tests/test_journey6.py) — direct import
  - `test_journey6_end_to_end_on_fresh_mvp08_vault`
- [tests/test_kinship_feature.py](../../../../../../tests/test_kinship_feature.py) — direct import
- [tests/test_laddered_stems.py](../../../../../../tests/test_laddered_stems.py) — direct import
- [tests/test_p2_acceptance.py](../../../../../../tests/test_p2_acceptance.py) — direct import
  - `test_golden_path_ten_step_fixture_journey`
- [tests/test_p2_leakage_suite.py](../../../../../../tests/test_p2_leakage_suite.py) — direct import
  - `test_diagnostic_exposure_consumes_cold_eligibility`
- [tests/test_p3_journeys.py](../../../../../../tests/test_p3_journeys.py) — direct import
  - `test_arc_and_salience_heads_rebuild_deterministically`
- [tests/test_progression.py](../../../../../../tests/test_progression.py) — direct import
- [tests/test_reader_authoring.py](../../../../../../tests/test_reader_authoring.py) — direct import
- [tests/test_reader_dialogue.py](../../../../../../tests/test_reader_dialogue.py) — direct import
  - `test_answer_not_quoting_reserve_leaves_it_eligible`
  - `test_answer_quoting_reserved_surface_burns_it_without_caller_id`
  - `test_ask_warms_and_invalidates_a_revealed_reserve`
  - `test_restore_source_during_cold_burns_eligibility`
- [tests/test_sidecar_golden_path_assessment.py](../../../../../../tests/test_sidecar_golden_path_assessment.py) — direct import
- [tests/test_sidecar_reader.py](../../../../../../tests/test_sidecar_reader.py) — direct import
  - `test_reader_ask_history_rpc_returns_durable_exchanges`
- [tests/test_substrate_cutover.py](../../../../../../tests/test_substrate_cutover.py) — direct import
- [tests/test_surface_mint.py](../../../../../../tests/test_surface_mint.py) — direct import
- [tests/test_surface_pool.py](../../../../../../tests/test_surface_pool.py) — direct import
  - `test_familiar_practice_is_never_reported_fresh`
  - `test_practice_exposure_invalidates_same_fingerprint_assessment_reserve`

## Modification guidance

- Change activities policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/activities.py](../../../../../../src/learnloop/substrate/activities.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
