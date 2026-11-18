---
title: "learnloop.db.stores.facet_projection"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/facet_projection.py"
source_paths:
  - "src/learnloop/db/stores/facet_projection.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.stores.facet_projection module"
  - "src/learnloop/db/stores/facet_projection.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.facet_projection`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.facet_projection` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Facet belief projections, merge lookups and rebuild receipts.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/facet_projection.py](../../../../../../../src/learnloop/db/stores/facet_projection.py) |
| Source lines | 1120 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class FacetRecallState` ([source](../../../../../../../src/learnloop/db/stores/facet_projection.py), line 164)
- `class CanonicalFacetRecallState` ([source](../../../../../../../src/learnloop/db/stores/facet_projection.py), line 184) — Canonical shared facet belief (KM2 §7.1), keyed on the post-merge facet id and observed capability.
- `class FacetCapabilityEvidence` ([source](../../../../../../../src/learnloop/db/stores/facet_projection.py), line 207) — Capability-sliced certification ledger (KM2 §7.1).
- `class FacetProjectionStoreMixin` ([source](../../../../../../../src/learnloop/db/stores/facet_projection.py), line 349)
  - `facet_ids_with_recall_evidence(self) -> set[str]` (line 351; public) — Facet ids with legacy per-LO recall evidence (mvp-0.6 first-touch lock).
  - `facet_recall_state(self, learning_object_id: str, facet_id: str, practice_item_id: str | None=None) -> FacetRecallState | None` (line 366; public)
  - `canonical_facet_recall_states(self) -> list[CanonicalFacetRecallState]` (line 397; public)
  - `canonical_facet_recall_state(self, facet_id: str, capability_key: str='shared', practice_item_id: str | None=None) -> CanonicalFacetRecallState | None` (line 404; public)
  - `facet_capability_evidence(self, facet_id: str, capability: str) -> FacetCapabilityEvidence | None` (line 429; public)
  - `facet_capability_evidence_all(self) -> list[FacetCapabilityEvidence]` (line 439; public)
  - `facet_capability_evidence_for_facet(self, facet_id: str) -> list[FacetCapabilityEvidence]` (line 446; public)
  - `facet_independence_evidence(self, facet_id: str) -> tuple[int, float]` (line 456; public) — (#distinct direct surface/correlation groups, independent mass) for the independence-gated lock trigger (§3.4).
  - `canonical_observation_ledger(self) -> list[dict[str, Any]]` (line 474; public) — Every graded attempt in global chronological order with its non-superseded grading evidence (KM2 projection input).
  - `canonical_observation_ledger_v2(self) -> list[dict[str, Any]]` (line 494; public) — P0.3 (§4.3) authoritative-events ledger.
  - `replace_canonical_facet_state(self, *, recall_rows: Iterable[Mapping[str, Any]], capability_rows: Iterable[Mapping[str, Any]], algorithm_version: str, clock: Clock | None=None) -> None` (line 510; public) — Make the canonical belief cache equal a derived projection.
  - `replace_capability_residual_state(self, *, rows: Iterable[Mapping[str, Any]], algorithm_version: str, clock: Clock | None=None) -> None` (line 598; public) — Make the derived capability-residual activation state equal a projection (§4.2).
  - `capability_residual_states(self) -> list[dict[str, Any]]` (line 645; public)
  - `capability_residual_state(self, facet_id: str, capability: str) -> dict[str, Any] | None` (line 652; public)
  - `identifiability_watermark(self, subject_id: str) -> dict[str, Any] | None` (line 664; public)
  - `upsert_identifiability_watermark(self, *, subject_id: str, registry_hash: str, finding_count: int, clock: Clock | None=None) -> None` (line 679; public)
  - `facet_merge_map(self, *, include_in_flight: bool=False) -> dict[str, str]` (line 705; public) — The settled merge map, retired facet -> survivor.
  - `resolve_facet_merge(self, facet_id: str, merge_map: Mapping[str, str] | None=None) -> str` (line 722; public) — Resolve a facet id transitively to its terminal survivor (§7.1).
  - `insert_facet_merge(self, *, retired_facet_id: str, surviving_facet_id: str, proposal_item_id: str | None=None, rationale: str | None=None, clock: Clock | None=None) -> None` (line 728; public) — Record a pre-lock reviewed merge; reject a row that creates a cycle.
  - `facet_recall_states(self, learning_object_id: str | None=None) -> list[FacetRecallState]` (line 768; public)
  - `facet_uncertainty_state(self, learning_object_id: str, facet_id: str) -> FacetUncertaintyState | None` (line 785; public)
  - `facet_uncertainty_states(self, learning_object_id: str | None=None, *, statuses: Iterable[str] | None=None) -> list[FacetUncertaintyState]` (line 800; public)
  - `upsert_facet_uncertainty_state(self, state: Mapping[str, Any]) -> None` (line 826; public)
  - `latest_whole_vault_rebuild(self) -> dict[str, Any] | None` (line 831; public) — The latest rebuild that replayed every learning object (scope ``all``), or None.
  - `record_derived_state_rebuild(self, *, scope: str, learning_object_ids: list[str], algorithm_version: str, rebuilt_learning_objects: int, replayed_attempts: int, canonical_projection_version: str | None=None, coverage_denominator_version: str | None=None, projection_switches: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` (line 840; public)
  - `latest_derived_state_rebuild(self) -> dict[str, Any] | None` (line 886; public)
  - `has_whole_vault_rebuild(self, *, algorithm_version: str) -> bool` (line 897; public) — Whether a whole-vault rebuild (scope ``all``) ran under ``algorithm_version``.
  - `latest_canonical_projection_rebuild(self) -> dict[str, Any] | None` (line 911; public) — Latest rebuild that explicitly names its projection semantics.
  - `_upsert_facet_uncertainty_state(self, connection: sqlite3.Connection, state: Mapping[str, Any]) -> None` (line 933; internal)
  - `derived_state_rebuild_version_changes(self) -> list[dict[str, Any]]` (line 1002; public) — Recalibration boundaries: each derived-state rebuild whose ``algorithm_version`` OR ``canonical_projection_version`` differs from the immediately preceding rebuild.

## Internal implementation anchors

- `class _ProjectionChanges` ([source](../../../../../../../src/learnloop/db/stores/facet_projection.py), line 32)
- `_projection_changes(connection: sqlite3.Connection, table: _ProjectionTable, cells: Sequence[Mapping[str, Any]]) -> _ProjectionChanges` ([source](../../../../../../../src/learnloop/db/stores/facet_projection.py), line 41) — Compare a projection with the stored rows, cell by cell.
- `_apply_projection_changes(connection: sqlite3.Connection, table: _ProjectionTable, changes: _ProjectionChanges, *, now: str) -> None` ([source](../../../../../../../src/learnloop/db/stores/facet_projection.py), line 85)
- `_write_projection_on_change(connection: sqlite3.Connection, projections: Sequence[tuple[_ProjectionTable, Sequence[Mapping[str, Any]]]], *, now: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/facet_projection.py), line 121) — Persist whole projections, writing only the cells that changed.
- `_facet_recall_state(row: sqlite3.Row) -> FacetRecallState` ([source](../../../../../../../src/learnloop/db/stores/facet_projection.py), line 233)
- `_canonical_facet_recall_state(row: sqlite3.Row) -> CanonicalFacetRecallState` ([source](../../../../../../../src/learnloop/db/stores/facet_projection.py), line 254)
- `_facet_capability_evidence(row: sqlite3.Row) -> FacetCapabilityEvidence` ([source](../../../../../../../src/learnloop/db/stores/facet_projection.py), line 275)
- `_capability_residual_row(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/facet_projection.py), line 294)
- `_resolve_merge(facet_id: str, merge_map: Mapping[str, str]) -> str` ([source](../../../../../../../src/learnloop/db/stores/facet_projection.py), line 316) — Follow retired->surviving edges to the terminal survivor.
- `_reaches(start: str, target: str, merge_map: Mapping[str, str]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/facet_projection.py), line 330)
- `_decode_derived_state_rebuild(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/facet_projection.py), line 341)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `FacetRecallState`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `FacetProjectionStoreMixin`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `FacetRecallState`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `FacetRecallState`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `CanonicalFacetRecallState`, `FacetRecallState`; statically calls `FacetRecallState`
- [[Reference/Modules/learnloop/scheduling/selection_rewards|learnloop.scheduling.selection_rewards]] — imports `FacetRecallState`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/records|learnloop.db.records]] — imports `FacetUncertaintyState`, `_CAPABILITY_RESIDUAL_PROJECTION`, `_FACET_CAPABILITY_PROJECTION`, `_FACET_RECALL_PROJECTION`, `_ProjectionTable`, `_facet_uncertainty_state`, `_projection_id`; calls `_facet_uncertainty_state`, `_projection_id`
- [[Reference/Modules/learnloop/db/row_serialization|learnloop.db.row_serialization]] — imports `_json`, `_loads`; calls `_json`, `_loads`
- [[Reference/Modules/learnloop/db/stores/facet_identity|learnloop.db.stores.facet_identity]] — imports `settled_merge_rows`; calls `settled_merge_rows`
- [[Reference/Modules/learnloop/db/stores/observation_ledger|learnloop.db.stores.observation_ledger]] — imports `load_authoritative_observation_ledger`, `load_canonical_observation_ledger`; calls `load_authoritative_observation_ledger`, `load_canonical_observation_ledger`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]], [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]], [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/ad23_contract_helpers.py](../../../../../../../tests/ad23_contract_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/ad23_fakes.py](../../../../../../../tests/ad23_fakes.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/assumed_known_helpers.py](../../../../../../../tests/assumed_known_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/causal_cold_outcomes_helpers.py](../../../../../../../tests/causal_cold_outcomes_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/causal_factor_deferral_helpers.py](../../../../../../../tests/causal_factor_deferral_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/causal_p2_acceptance_helpers.py](../../../../../../../tests/causal_p2_acceptance_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/certification_cold_probe_helpers.py](../../../../../../../tests/certification_cold_probe_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/cold_retry_reschedule_helpers.py](../../../../../../../tests/cold_retry_reschedule_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/diagnosis_journey_helpers.py](../../../../../../../tests/diagnosis_journey_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/diagnosis_split_helpers.py](../../../../../../../tests/diagnosis_split_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/diagnostic_augmentation_helpers.py](../../../../../../../tests/diagnostic_augmentation_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/diagnostic_probe_single_use_helpers.py](../../../../../../../tests/diagnostic_probe_single_use_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/facet_projection.py](../../../../../../../src/learnloop/db/stores/facet_projection.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
