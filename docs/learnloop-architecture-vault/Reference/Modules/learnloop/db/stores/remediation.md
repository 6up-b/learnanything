---
title: "learnloop.db.stores.remediation"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/remediation.py"
source_paths:
  - "src/learnloop/db/stores/remediation.py"
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
  - "learnloop.db.stores.remediation module"
  - "src/learnloop/db/stores/remediation.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.remediation`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.remediation` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Remediation episodes and follow-up work.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/remediation.py](../../../../../../../src/learnloop/db/stores/remediation.py) |
| Source lines | 999 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class RemediationStoreMixin` ([source](../../../../../../../src/learnloop/db/stores/remediation.py), line 32)
  - `pending_followup_practice_item_ids(self, *, clock: Clock | None=None) -> list[str]` (line 34; public) — Return queued follow-up item ids that have not yet been attempted.
  - `pending_followup_practice_items(self, *, clock: Clock | None=None) -> list[dict[str, str]]` (line 42; public) — Return queued follow-ups that have not yet been attempted.
  - `create_remediation_episode(self, *, case_kind: str, case_ref: str, passages_shown: Sequence[Mapping[str, Any]]=(), state: str='diagnosis', clock: Clock | None=None) -> dict[str, Any]` (line 100; public)
  - `remediation_episode(self, episode_id: str) -> dict[str, Any] | None` (line 126; public)
  - `get_or_create_open_remediation_episode(self, *, case_kind: str, case_ref: str, states: Sequence[str], clock: Clock | None=None) -> dict[str, Any]` (line 133; public) — The newest episode for the case in one of ``states``, else a new one.
  - `update_remediation_episode(self, episode_id: str, *, clock: Clock | None=None, **changes: Any) -> dict[str, Any] | None` (line 185; public)
  - `open_remediation_episode_for_case(self, *, case_kind: str, case_ref: str) -> dict[str, Any] | None` (line 212; public) — The newest episode for the case that has not yet recorded a primed attempt.
  - `open_remediation_episode_for_primed_item(self, practice_item_id: str) -> dict[str, Any] | None` (line 235; public)
  - `open_remediation_episodes_for_item(self, practice_item_id: str) -> list[dict[str, Any]]` (line 248; public) — Live episodes that bound this item as their primed or cold surface.
  - `create_followup_task(self, *, kind: str, case_kind: str, case_ref: str, not_before: str, selected_item_id: str | None, source_attempt_id: str | None=None, remediation_episode_id: str | None=None, expires_at: str | None=None, context: Mapping[str, Any] | None=None, learning_object_id: str | None=None, measurement_opportunity_id: str | None=None, measurement_decision_reason: str | None=None, measurement_candidate_summary: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` (line 272; public) — Schedule one delayed follow-up.
  - `get_or_create_cold_measurement_opportunity(self, *, lane: str, trigger_kind: str, trigger_ref: str, policy_version: str, learning_object_id: str | None=None, case_kind: str | None=None, case_ref: str | None=None, remediation_episode_id: str | None=None, source_attempt_id: str | None=None, certificate_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` (line 361; public) — Create the denominator row before candidate selection.
  - `cold_measurement_opportunity(self, opportunity_id: str) -> dict[str, Any] | None` (line 422; public)
  - `record_cold_measurement_opportunity_decision(self, *, measurement_opportunity_id: str, decision: str, reason: str, followup_task_id: str | None=None, selected_item_id: str | None=None, candidate_summary: Mapping[str, Any] | None=None, scheduled_not_before: str | None=None, scheduled_expires_at: str | None=None, clock: Clock | None=None) -> dict[str, Any]` (line 432; public) — Settle an opportunity once, preserving the first terminal decision.
  - `_decode_cold_measurement_opportunity_decision(row: Any) -> dict[str, Any]` (line 482; internal)
  - `cold_measurement_opportunity_decision(self, measurement_opportunity_id: str) -> dict[str, Any] | None` (line 491; public)
  - `followup_task(self, task_id: str) -> dict[str, Any] | None` (line 508; public)
  - `attach_followup_task_measurement_opportunity(self, task_id: str, measurement_opportunity_id: str, *, clock: Clock | None=None) -> dict[str, Any] | None` (line 513; public) — Prospectively attach lineage to a pre-151 task, without replacing it.
  - `due_followup_tasks(self, *, clock: Clock | None=None) -> list[dict[str, Any]]` (line 530; public) — The due tasks, each marked served, and the expired ones marked so.
  - `active_followup_task_for_item(self, practice_item_id: str, *, kind: str | None=None, at: str | None=None) -> dict[str, Any] | None` (line 578; public) — The due, unconsumed follow-up task selecting ``practice_item_id``.
  - `followup_task_for_case(self, *, kind: str, case_ref: str) -> dict[str, Any] | None` (line 609; public) — Any task of ``kind`` for ``case_ref``, whatever its status.
  - `_release_cold_reservation(connection: Any, episode_id: str, now: str) -> bool` (line 630; internal) — End a ``cold_scheduled`` episode whose cold retry has no open task left, so its cold item stops being reserved.
  - `untaken_remediation_episodes(self) -> list[dict[str, Any]]` (line 647; public) — Episodes in ``prescribed`` or ``treatment`` whose primed attempt was never taken, oldest first.
  - `abandon_untaken_remediation_episode(self, episode_id: str, *, clock: Clock | None=None) -> bool` (line 660; public) — End an untaken episode as ``abandoned``, which frees its cold item as a withdrawn retry's release does.
  - `release_cold_reservation(self, episode_id: str, *, clock: Clock | None=None) -> bool` (line 681; public) — :meth:`_release_cold_reservation` for the caller that ended the retry (a withdrawal).
  - `_remediation_cold_item_ids(self, *, awaiting_primed: bool) -> set[str]` (line 689; internal) — Cold items of live remediation episodes: those with a cold retry open, and (``awaiting_primed``) those still waiting for the primed attempt, before any task exists.
  - `open_remediation_cold_item_ids(self) -> set[str]` (line 709; public) — The wider reservation, for the learner-initiated selectors and the tutor (``find_practice``, the quick check, practice admission, AD's slot check, ``cold_administration_open``, protection): the cold item is held from the moment the episode chooses it, while its primed attempt is…
  - `pending_remediation_cold_item_ids(self) -> set[str]` (line 716; public) — The narrower reservation Today's routine queue honours below ``mvp-0.64``: only an open cold retry.
  - `open_followup_tasks_of_kind(self, kind: str, *, learning_object_id: str | None=None) -> list[dict[str, Any]]` (line 724; public) — Tasks of ``kind`` still awaiting an attempt (``pending`` or ``served``).
  - `open_followup_tasks_for_item(self, practice_item_id: str) -> list[dict[str, Any]]` (line 744; public) — Every task of any kind still awaiting an attempt on this item, in ``active_followup_task_for_item``'s order (``serve_eligibility`` judges them all: the first due one is the task submit answers).
  - `followup_tasks_of_kind(self, kind: str) -> list[dict[str, Any]]` (line 760; public) — Every task of ``kind``, any status — the metric's denominator read.
  - `expire_followup_task(self, task_id: str, *, clock: Clock | None=None) -> dict[str, Any] | None` (line 773; public) — Retire an un-taken task.
  - `defer_followup_task(self, task_id: str, *, not_before: str, clock: Clock | None=None) -> dict[str, Any] | None` (line 794; public) — Push an un-taken task's ``not_before`` later.
  - `consume_followup_task(self, task_id: str, attempt_id: str, *, clock: Clock | None=None) -> dict[str, Any] | None` (line 821; public)
  - `followup_source_attempt(self, attempt_id: str) -> str | None` (line 837; public) — Gate-decision attempt whose queued follow-up this attempt answered.
  - `upsert_followup_rating(self, *, attempt_id: str, gate_attempt_id: str | None, useful: bool, source: str='user', clock: Clock | None=None) -> None` (line 886; public)
  - `followup_rating(self, attempt_id: str) -> dict[str, Any] | None` (line 911; public)
  - `remediation_episodes_created_between(self, *, after: str, before: str) -> list[dict[str, Any]]` (line 923; public) — Episodes CREATED inside the interval, for the prepared-passages scan.
  - `remediation_episodes_for_case_refs(self, case_refs: Sequence[str]) -> list[dict[str, Any]]` (line 946; public) — Remediation episodes (any state) whose case_ref is in ``case_refs``.
  - `consumed_followup_task_for_attempt(self, attempt_id: str, *, kind: str | None=None) -> dict[str, Any] | None` (line 971; public) — The delayed task this attempt discharged, with its carried context.

## Internal implementation anchors

- `_queued_followup_action(action: Any) -> tuple[str, str] | None` ([source](../../../../../../../src/learnloop/db/stores/remediation.py), line 16)
- `_decode_remediation_episode(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/remediation.py), line 26)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `RemediationStoreMixin`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/records|learnloop.db.records]] — imports `_decode_followup_task`; calls `_decode_followup_task`
- [[Reference/Modules/learnloop/db/row_serialization|learnloop.db.row_serialization]] — imports `_json`, `_loads`; calls `_json`, `_loads`
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

1. Modify [src/learnloop/db/stores/remediation.py](../../../../../../../src/learnloop/db/stores/remediation.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
