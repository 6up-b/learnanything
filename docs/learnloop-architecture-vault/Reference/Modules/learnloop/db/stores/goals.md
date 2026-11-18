---
title: "learnloop.db.stores.goals"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/goals.py"
source_paths:
  - "src/learnloop/db/stores/goals.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.db.stores.goals module"
  - "src/learnloop/db/stores/goals.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.goals`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.goals` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Commitments, goal contracts, exams and forecasts.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/goals.py](../../../../../../../src/learnloop/db/stores/goals.py) |
| Source lines | 1355 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class StaleContractHead(Exception)` ([source](../../../../../../../src/learnloop/db/stores/goals.py), line 17) — The predecessor a successor was built against is no longer the head (L3, §3.4).
  - `__init__(self, goal_id: str, *, expected: str | None, actual: str | None)` (line 22; internal)
- `class GoalStoreMixin` ([source](../../../../../../../src/learnloop/db/stores/goals.py), line 57)
  - `insert_forecast(self, values: Mapping[str, Any]) -> dict[str, Any]` (line 61; public)
  - `forecast(self, forecast_id: str) -> dict[str, Any] | None` (line 96; public)
  - `due_forecasts(self, at: str) -> list[dict[str, Any]]` (line 101; public)
  - `update_forecast_resolution(self, forecast_id: str, *, status: str, resolved_at: str, resolved_value: float | None=None, projection_drift: float | None=None) -> dict[str, Any] | None` (line 113; public)
  - `list_forecasts(self, goal_id: str | None=None) -> list[dict[str, Any]]` (line 134; public)
  - `open_forecasts(self, goal_id: str) -> list[dict[str, Any]]` (line 147; public) — Read-only: open (unresolved) forecast rows for a goal, oldest first.
  - `append_goal_contract_version(self, *, goal_id: str, version: int, predecessor_version_id: str | None, contract_json: str, content_hash: str, support_hash: str, contract_schema_version: int, change_class: str, envelope_version: str | None=None, predecessor_milestone: str | None=None, activated_edge_id: str | None=None, evidence_receipt_json: str | None=None, burden_delta_json: str | None=None, author: str, reason: str | None=None, head_envelope_version: str | None=None, clock: Clock | None=None) -> dict[str, Any]` (line 172; public) — Append an immutable version row and rewrite the head projection in one transaction.
  - `fetch_goal_contract_head(self, goal_id: str) -> dict[str, Any] | None` (line 290; public)
  - `fetch_goal_contract_version(self, version_id: str) -> dict[str, Any] | None` (line 297; public)
  - `goal_contract_versions_for_goal(self, goal_id: str) -> list[dict[str, Any]]` (line 304; public)
  - `insert_goal_contract_draft(self, *, goal_id: str, predecessor_version_id: str | None, proposed_contract_json: str, proposed_change_class: str | None, rejection_reason: str, requires: str, author: str, evidence_receipt_json: str | None=None, clock: Clock | None=None) -> str` (line 312; public)
  - `goal_contract_drafts_for_goal(self, goal_id: str) -> list[dict[str, Any]]` (line 345; public)
  - `create_commitment_arc(self, *, commitment_id: str, source_id: str | None=None, clock: Clock | None=None) -> str` (line 357; public)
  - `append_commitment_arc_version(self, *, arc_id: str, version: Mapping[str, Any], clock: Clock | None=None) -> dict[str, Any]` (line 370; public)
  - `append_commitment_arc_event(self, *, arc_id: str, kind: str, detail: Mapping[str, Any] | None=None, receipt_key: str | None=None, clock: Clock | None=None) -> dict[str, Any]` (line 413; public) — Append an arc event.
  - `commitment_arc_head_version(self, arc_id: str) -> dict[str, Any] | None` (line 455; public)
  - `commitment_arc(self, arc_id: str) -> dict[str, Any] | None` (line 464; public)
  - `commitment_arc_events(self, arc_id: str) -> list[dict[str, Any]]` (line 471; public)
  - `arcs_for_commitment(self, commitment_id: str) -> list[str]` (line 479; public)
  - `reserved_exam_pool_items(self, goal_id: str) -> list[dict[str, Any]]` (line 487; public) — Unreleased pool reservations for a goal, in reservation order.
  - `reserved_exam_pool_item_ids(self) -> set[str]` (line 501; public) — All practice item ids currently reserved (unreleased) across goals.
  - `insert_exam_pool_items(self, rows: Iterable[Mapping[str, Any]]) -> None` (line 510; public)
  - `release_exam_pool(self, goal_id: str, *, clock: Clock | None=None) -> list[str]` (line 533; public) — Release every unreleased reservation for a goal; return the item ids.
  - `release_exam_pool_items(self, goal_id: str, practice_item_ids: Iterable[str], *, clock: Clock | None=None) -> list[str]` (line 550; public) — Release some of a goal's unreleased reservations (the rows stay, with ``released_at``); return the item ids released.
  - `insert_exam_session(self, session: Mapping[str, Any]) -> None` (line 579; public)
  - `exam_session(self, session_id: str) -> dict[str, Any] | None` (line 602; public)
  - `exam_session_in_progress_for_goal(self, goal_id: str) -> dict[str, Any] | None` (line 610; public)
  - `latest_completed_exam_session(self, goal_id: str) -> dict[str, Any] | None` (line 623; public)
  - `update_exam_session(self, session_id: str, *, status: str | None=None, report: Any | None=None, completed_at: str | None=None, clock: Clock | None=None) -> None` (line 636; public)
  - `insert_exam_predictions(self, rows: Iterable[Mapping[str, Any]]) -> None` (line 665; public)
  - `exam_predictions(self, session_id: str) -> list[dict[str, Any]]` (line 689; public)
  - `all_exam_predictions(self) -> list[dict[str, Any]]` (line 697; public)
  - `upsert_exam_answer(self, answer: Mapping[str, Any], *, clock: Clock | None=None) -> None` (line 704; public)
  - `set_exam_answer_attempt_id(self, session_id: str, practice_item_id: str, attempt_id: str) -> None` (line 737; public)
  - `exam_answer(self, session_id: str, practice_item_id: str) -> dict[str, Any] | None` (line 745; public)
  - `exam_answers(self, session_id: str) -> list[dict[str, Any]]` (line 758; public)
  - `ensure_depth_policy_version(self, *, policy: str, body_json: str, content_hash: str, clock: Clock | None=None) -> str` (line 770; public) — Immutable, content-addressed depth policy version (idempotent on hash).
  - `ensure_depth_envelope_version(self, *, envelope_version: str, bounds_json: str, reviewed_edges_json: str, content_hash: str, clock: Clock | None=None) -> str` (line 792; public)
  - `depth_policy_version(self, policy_version_id: str) -> dict[str, Any] | None` (line 823; public)
  - `depth_envelope_version(self, envelope_version_id: str) -> dict[str, Any] | None` (line 830; public)
  - `insert_depth_edge_template(self, *, template_slug: str, domain_scope: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` (line 839; public)
  - `depth_edge_template_by_slug(self, template_slug: str) -> dict[str, Any] | None` (line 852; public)
  - `depth_edge_templates(self) -> list[dict[str, Any]]` (line 859; public)
  - `insert_depth_edge_template_version(self, *, template_id: str, version: int, body_json: str, content_hash: str, status: str='draft', clock: Clock | None=None) -> str` (line 866; public)
  - `depth_edge_template_version(self, version_id: str) -> dict[str, Any] | None` (line 889; public)
  - `depth_edge_template_versions_for(self, template_id: str) -> list[dict[str, Any]]` (line 896; public)
  - `review_depth_edge_template_version(self, version_id: str, *, status: str, reviewed_by: str, clock: Clock | None=None) -> bool` (line 904; public)
  - `insert_depth_edge_instance(self, instance: Mapping[str, Any], *, clock: Clock | None=None) -> str` (line 916; public)
  - `depth_edge_instance(self, instance_id: str) -> dict[str, Any] | None` (line 955; public)
  - `depth_edge_instances_for(self, commitment_id: str, *, status: str | None=None) -> list[dict[str, Any]]` (line 962; public)
  - `update_depth_edge_instance_status(self, instance_id: str, *, status: str, admission_report_json: str | None=None, pinned_envelope_version_id: str | None=None, clock: Clock | None=None) -> bool` (line 975; public)
  - `depth_milestone_version_for(self, envelope_version_id: str, milestone_slug: str) -> dict[str, Any] | None` (line 999; public) — Latest milestone version for (envelope version, slug) — the rung projection seam (``learnloop.curriculum.depth_rungs``).
  - `insert_depth_milestone_version(self, *, envelope_version_id: str, milestone_slug: str, task_contract_json: str, entry_evidence_json: str | None=None, exit_evidence_json: str | None=None, fresh_proof_json: str | None=None, expected_burden_json: str | None=None, content_hash: str, clock: Clock | None=None) -> str` (line 1016; public)
  - `_insert_commitment_version_rows(self, connection: sqlite3.Connection, *, commitment_id: str, predecessor_version_id: str | None, version: int, version_fields: Mapping[str, Any], targets: Sequence[Mapping[str, Any]], author: str, change_reason: str | None, events: Sequence[Mapping[str, Any]], now: str) -> str` (line 1049; internal)
  - `create_commitment(self, *, learner_id: str, created_action: str, idempotency_key: str | None, version_fields: Mapping[str, Any], targets: Sequence[Mapping[str, Any]], author: str, change_reason: str | None, clock: Clock | None=None) -> tuple[str, bool]` (line 1117; public) — Atomically insert the stable commitment, its v1 version, target rows, and the ``created`` event in one transaction.
  - `append_commitment_version(self, *, commitment_id: str, predecessor_version_id: str | None, version: int, version_fields: Mapping[str, Any], targets: Sequence[Mapping[str, Any]], author: str, change_reason: str | None, events: Sequence[Mapping[str, Any]], clock: Clock | None=None) -> str` (line 1192; public)
  - `append_commitment_event(self, *, commitment_id: str, commitment_version_id: str | None, kind: str, detail_json: str | None, clock: Clock | None=None) -> str` (line 1230; public)
  - `commitment(self, commitment_id: str) -> dict[str, Any] | None` (line 1253; public)
  - `commitment_head(self, commitment_id: str) -> dict[str, Any] | None` (line 1260; public)
  - `commitment_versions_for(self, commitment_id: str) -> list[dict[str, Any]]` (line 1272; public)
  - `commitment_targets_for_version(self, commitment_version_id: str) -> list[dict[str, Any]]` (line 1280; public)
  - `commitment_events_for(self, commitment_id: str) -> list[dict[str, Any]]` (line 1291; public)
  - `commitments_targeting(self, target_ref: str) -> list[str]` (line 1302; public) — Commitment ids whose HEAD version carries a target with this ref (any target kind).
  - `find_commitment_by_idempotency(self, *, learner_id: str, created_action: str, target_set_hash: str, idempotency_key: str) -> dict[str, Any] | None` (line 1323; public)
  - `find_commitment_candidate(self, *, learner_id: str, created_action: str, target_set_hash: str) -> dict[str, Any] | None` (line 1340; public)

## Internal implementation anchors

- `_decode_forecast(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/goals.py), line 32)
- `_decode_exam_session(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/goals.py), line 38)
- `_decode_exam_prediction(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/goals.py), line 45)
- `_decode_exam_answer(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/goals.py), line 51)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `GoalStoreMixin`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/row_serialization|learnloop.db.row_serialization]] — imports `_json`, `_loads`; calls `_json`, `_loads`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_goal_contracts.py](../../../../../../../tests/test_goal_contracts.py) — direct import
  - `test_append_version_rejects_stale_predecessor`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/goals.py](../../../../../../../src/learnloop/db/stores/goals.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
