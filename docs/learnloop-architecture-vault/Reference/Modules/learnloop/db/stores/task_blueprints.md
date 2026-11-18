---
title: "learnloop.db.stores.task_blueprints"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/task_blueprints.py"
source_paths:
  - "src/learnloop/db/stores/task_blueprints.py"
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
  - "learnloop.db.stores.task_blueprints module"
  - "src/learnloop/db/stores/task_blueprints.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.task_blueprints`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.task_blueprints` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Task blueprints and golden-path planning records.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/task_blueprints.py](../../../../../../../src/learnloop/db/stores/task_blueprints.py) |
| Source lines | 732 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class TaskBlueprintStoreMixin` ([source](../../../../../../../src/learnloop/db/stores/task_blueprints.py), line 15)
  - `ensure_task_blueprint(self, *, blueprint_slug: str, source_rev: str, unit_id: str, family_key: str, clock: Clock | None=None) -> str` (line 21; public)
  - `register_task_blueprint_version(self, *, blueprint_id: str, spec_json: str, content_hash: str, canonical_hash: str, authoring_version: str, model_version: str | None, provenance_version: str, exemplars: Sequence[Mapping[str, Any]], detail_json: str | None=None, author: str='owner', clock: Clock | None=None) -> dict[str, Any]` (line 50; public) — Register an immutable, content-addressed draft blueprint version + its exemplar link rows + a ``registered`` review event, all in one transaction.
  - `transition_task_blueprint_version(self, *, blueprint_version_id: str, status: str, event_kind: str, detail_json: str | None=None, author: str='owner', clock: Clock | None=None) -> dict[str, Any]` (line 137; public) — Advance a blueprint version's status (reviewed/active/retired) and append the matching review event atomically.
  - `append_task_blueprint_review_event(self, *, blueprint_version_id: str, kind: str, detail_json: str | None=None, author: str='owner', clock: Clock | None=None) -> str` (line 181; public)
  - `task_blueprint_version(self, blueprint_version_id: str) -> dict[str, Any] | None` (line 204; public)
  - `task_blueprint_versions_for(self, blueprint_id: str) -> list[dict[str, Any]]` (line 211; public)
  - `target_exemplars_for(self, blueprint_version_id: str) -> list[dict[str, Any]]` (line 219; public)
  - `task_blueprint_review_events_for(self, blueprint_version_id: str) -> list[dict[str, Any]]` (line 227; public)
  - `reviewed_reading_question_placements(self, *, source_revs: Sequence[str], unit_ids: Sequence[str], blueprint_version_ids: Sequence[str]=()) -> list[dict[str, Any]]` (line 235; public) — Return the reviewed blueprint artifacts that can appear in a Reader.
  - `golden_path_run(self, run_id: str) -> dict[str, Any] | None` (line 300; public)
  - `golden_path_run_for_goal(self, goal_id: str) -> dict[str, Any] | None` (line 307; public) — The earliest golden-path run for a goal (the golden path is one run per goal).
  - `golden_path_run_events_for(self, run_id: str) -> list[dict[str, Any]]` (line 319; public)
  - `append_golden_path_run_event(self, *, run_id: str, to_state: str, reason: str, expected_head_event_id: str | None=None, idempotency_key: str | None=None, feasible_alternatives_json: str | None=None, evidence_ids_json: str | None=None, goal_contract_head_version_id: str | None=None, depth_policy_version_id: str | None=None, depth_envelope_version_id: str | None=None, predecessor_milestone: str | None=None, successor_milestone: str | None=None, selected_activity_json: str | None=None, policy_calibration_json: str | None=None, burden_json: str | None=None, clock: Clock | None=None) -> dict[str, Any]` (line 327; public) — Append one transition event and update the run's cached head state, in one transaction.
  - `active_ladder_policy(self, policy_slug: str) -> dict[str, Any] | None` (line 423; public)
  - `ladder_stages_for_policy(self, policy_id: str) -> list[dict[str, Any]]` (line 432; public)
  - `ensure_practice_pool(self, *, pool_slug: str, blueprint_version_id: str, content_hash: str, clock: Clock | None=None) -> dict[str, Any]` (line 445; public) — Register/return the stable practice pool row.
  - `register_practice_pool_surface(self, *, pool_id: str, surface_slug: str, angle: str, content_hash: str, provenance: str='llm_within_bounds', surface_id: str | None=None, clock: Clock | None=None) -> str` (line 489; public) — Register a candidate practice surface.
  - `set_practice_pool_surface_admission(self, *, pool_id: str, surface_slug: str, admission_status: str, surface_id: str | None=None, detail_json: str | None=None, author: str='owner', clock: Clock | None=None) -> None` (line 525; public)
  - `transition_practice_pool(self, *, pool_id: str, status: str, kind: str, detail_json: str | None=None, author: str='owner', clock: Clock | None=None) -> None` (line 562; public)
  - `append_practice_pool_event(self, *, pool_id: str, kind: str, surface_slug: str | None=None, detail_json: str | None=None, author: str='system', clock: Clock | None=None) -> str` (line 588; public) — Append one pool ledger event (§7.3 audit) -- e.g.
  - `practice_pool(self, pool_id: str) -> dict[str, Any] | None` (line 616; public)
  - `practice_pools_for_blueprint(self, blueprint_version_id: str) -> list[dict[str, Any]]` (line 623; public)
  - `practice_pool_surfaces_for(self, pool_id: str) -> list[dict[str, Any]]` (line 631; public)
  - `practice_pool_events_for(self, pool_id: str) -> list[dict[str, Any]]` (line 639; public)
  - `append_golden_path_artifact(self, *, run_id: str, kind: str, payload_json: str, idempotency_key: str | None=None, administration_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` (line 647; public) — Append one inspectable run artifact (§8.4).
  - `golden_path_artifacts_for(self, run_id: str, *, kind: str | None=None) -> list[dict[str, Any]]` (line 707; public)
  - `latest_golden_path_artifact(self, run_id: str, *, kind: str) -> dict[str, Any] | None` (line 723; public)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `TaskBlueprintStoreMixin`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/row_serialization|learnloop.db.row_serialization]] — imports `_json`; calls `_json`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/ad1_codex_rereview_fixes_helpers.py](../../../../../../../tests/ad1_codex_rereview_fixes_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad1_reading_opportunities_helpers.py](../../../../../../../tests/ad1_reading_opportunities_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad23_contract_helpers.py](../../../../../../../tests/ad23_contract_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad23_fakes.py](../../../../../../../tests/ad23_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad23_fix_r8_helpers.py](../../../../../../../tests/ad23_fix_r8_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad2_serving_helpers.py](../../../../../../../tests/ad2_serving_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad_ingest_fakes.py](../../../../../../../tests/ad_ingest_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad_projection_helpers.py](../../../../../../../tests/ad_projection_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/apply_write_ahead_helpers.py](../../../../../../../tests/apply_write_ahead_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/approach_map_fakes.py](../../../../../../../tests/approach_map_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/assumed_known_helpers.py](../../../../../../../tests/assumed_known_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/canonical_facet_helpers.py](../../../../../../../tests/canonical_facet_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/task_blueprints.py](../../../../../../../src/learnloop/db/stores/task_blueprints.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
