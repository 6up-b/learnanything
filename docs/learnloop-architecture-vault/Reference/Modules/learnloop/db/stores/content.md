---
title: "learnloop.db.stores.content"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/content.py"
source_paths:
  - "src/learnloop/db/stores/content.py"
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
  - "learnloop.db.stores.content module"
  - "src/learnloop/db/stores/content.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.content`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.content` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Content proposals, apply intents, generation and agent runs.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/content.py](../../../../../../../src/learnloop/db/stores/content.py) |
| Source lines | 1847 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class ContentStoreMixin` ([source](../../../../../../../src/learnloop/db/stores/content.py), line 97)
  - `_record_text_provenance(connection: Any, kind: str, record_id: str, text: Any, record: Any, writer: str, clock: Clock | None) -> None` (line 100; internal) — One write-time provenance row for a text this transaction writes (diagnosis input provenance), when its writer passed a record.
  - `queue_revision(self) -> dict[str, Any]` (line 114; public)
  - `bump_queue_revision(self, *, clock: Clock | None=None) -> int` (line 124; public)
  - `insert_rung_variant_request(self, request: Mapping[str, Any], *, clock: Clock | None=None) -> str` (line 145; public)
  - `rung_variant_request(self, request_id: str) -> dict[str, Any] | None` (line 182; public)
  - `rung_variant_request_for_attempt(self, attempt_id: str) -> dict[str, Any] | None` (line 189; public) — The request whose evidence package is this attempt (the row's ``attempt_id``), if any.
  - `rung_variant_requests(self, request_ids: Iterable[str]) -> dict[str, dict[str, Any]]` (line 199; public) — Bulk-load rung requests used by ingest progress views.
  - `update_rung_variant_request(self, request_id: str, *, clock: Clock | None=None, **fields: Any) -> bool` (line 215; public)
  - `retry_failed_rung_variant_request(self, request_id: str, *, clock: Clock | None=None) -> bool` (line 234; public) — Return one failed generation request to its pre-generation state.
  - `pending_rung_variant_requests(self, source_practice_item_id: str) -> list[dict[str, Any]]` (line 260; public) — Non-terminal requests for one item — the per-item request lock.
  - `insert_concept_animation(self, row: Mapping[str, Any], *, clock: Clock | None=None) -> str` (line 286; public)
  - `concept_animation(self, animation_id: str) -> dict[str, Any] | None` (line 330; public)
  - `update_concept_animation(self, animation_id: str, *, clock: Clock | None=None, **fields: Any) -> bool` (line 337; public)
  - `concept_animations_for_concept(self, concept_id: str, limit: int=10) -> list[dict[str, Any]]` (line 352; public)
  - `pending_concept_animations(self, concept_id: str) -> list[dict[str, Any]]` (line 365; public) — Non-terminal animations for one concept — the per-concept lock.
  - `upsert_synthesis_generation_need(self, *, subject_id: str, need_kind: str, target_key: str, missing_capability: str, facet_ids: list[str] | None=None, source_set_id: str | None=None, synthesis_run_id: str | None=None, detail: str | None=None, clock: Clock | None=None) -> str` (line 381; public) — Record one deduplicated synthesis-time generation/coarsen need.
  - `synthesis_generation_needs(self, *, subject_id: str | None=None, status: str | None=None, need_kind: str | None=None) -> list[dict[str, Any]]` (line 434; public)
  - `resolve_synthesis_generation_need(self, need_id: str, *, status: str='resolved', clock: Clock | None=None) -> None` (line 475; public)
  - `insert_agent_run(self, run: Mapping[str, Any]) -> str` (line 486; public)
  - `complete_agent_run(self, run_id: str, *, status: str='completed', error_message: str | None=None, usage: TokenUsage | None=None, clock: Clock | None=None) -> bool` (line 526; public) — Finalize a run, optionally recording what the provider charged for it.
  - `add_agent_run_usage(self, run_id: str, usage: TokenUsage) -> bool` (line 578; public) — Add tokens to a run that was already finalized (A7).
  - `completed_agent_run_by_context(self, purpose: str, input_context_hash: str) -> dict[str, Any] | None` (line 608; public)
  - `agent_run(self, run_id: str) -> dict[str, Any] | None` (line 621; public)
  - `proposal_batch_for_agent_run(self, agent_run_id: str) -> dict[str, Any] | None` (line 629; public)
  - `proposal_batch(self, patch_id: str) -> dict[str, Any] | None` (line 642; public)
  - `persist_proposal_batch(self, batch: Mapping[str, Any], items: Iterable[Mapping[str, Any]], *, join_pending: Mapping[str, Any] | None=None) -> str` (line 650; public) — Write one proposal batch and its items.
  - `proposal_item_dependencies(self, item_id: str) -> list[str]` (line 837; public) — DB ids this proposal item depends on (source-ingestion §10.2).
  - `set_proposal_item_dependency_status(self, item_id: str, *, dependency_status: str, block_reason: Mapping[str, Any] | None=None) -> None` (line 852; public)
  - `insert_vault_epigraphs(self, *, subject_id: str, source_set_id: str | None, synthesis_run_id: str | None, mode: str, epigraphs: Sequence[Mapping[str, Any]], prompt_version: str, provider: str | None, model: str | None, clock: Clock | None=None) -> list[str]` (line 880; public) — Persist one synthesis's batch.
  - `recent_vault_epigraphs(self, *, subject_id: str | None=None, limit: int=12) -> list[dict[str, Any]]` (line 927; public) — Newest first; ``subject_id=None`` spans the whole vault.
  - `proposal_batches(self) -> list[dict[str, Any]]` (line 943; public)
  - `proposal_items(self, patch_id: str) -> list[dict[str, Any]]` (line 950; public)
  - `persona_gate_audit_rows(self, *, since: str | None=None) -> list[dict[str, Any]]` (line 962; public) — Every proposal item carrying a §3.0 persona-gate audit (plan item 5.3).
  - `proposal_item(self, item_id: str) -> dict[str, Any] | None` (line 998; public)
  - `proposal_items_by_client_id(self, client_item_id: str) -> list[dict[str, Any]]` (line 1006; public) — All proposal items sharing a ``client_item_id`` (used to dedupe re-proposals).
  - `pending_invalid_proposal_items(self) -> list[dict[str, Any]]` (line 1016; public)
  - `update_proposal_item_edited_payload(self, item_id: str, *, edited_payload: Mapping[str, Any], validation_status: str, validation_errors: list[str], clock: Clock | None=None) -> bool` (line 1027; public)
  - `update_proposal_item_validation(self, item_id: str, *, validation_status: str, validation_errors: list[str], clock: Clock | None=None) -> bool` (line 1058; public)
  - `pending_proposal_items(self, patch_id: str, item_ids: list[str] | None=None) -> list[dict[str, Any]]` (line 1087; public)
  - `record_applied_proposal_item(self, *, proposal_item_id: str, change_batch: Mapping[str, Any], content_events: Iterable[Mapping[str, Any]], clock: Clock | None=None) -> None` (line 1105; public)
  - `record_content_events(self, events: Iterable[Mapping[str, Any]]) -> int` (line 1173; public)
  - `content_events_for_entity(self, entity_type: str, entity_id: str) -> list[dict[str, Any]]` (line 1202; public)
  - `active_source_events_for_entity(self, entity_type: str, entity_id: str) -> list[dict[str, Any]]` (line 1214; public)
  - `reject_applied_proposal_item(self, proposal_item_id: str, *, content_event: Mapping[str, Any], decided_by: str='learner', clock: Clock | None=None) -> bool` (line 1252; public)
  - `set_proposal_item_decision(self, patch_id: str, decision: str, item_ids: list[str] | None=None, *, decided_by: str='learner', clock: Clock | None=None) -> int` (line 1307; public)
  - `delete_proposal_item(self, item_id: str, *, clock: Clock | None=None) -> bool` (line 1336; public) — Permanently remove a proposal item row, refreshing its batch status.
  - `reset_proposal_item_decision(self, patch_id: str, item_ids: list[str] | None=None, *, clock: Clock | None=None) -> int` (line 1355; public) — Reset a decided item back to ``pending`` — the inbox "undo" action.
  - `_refresh_proposal_status(self, connection: sqlite3.Connection, patch_id: str, *, updated_at: str) -> None` (line 1393; internal)
  - `insert_synthesis_manifest(self, manifest: Mapping[str, Any]) -> str` (line 1427; public) — Persist an immutable synthesis manifest (§8.4).
  - `synthesis_manifest(self, manifest_id: str) -> dict[str, Any] | None` (line 1485; public)
  - `synthesis_manifest_by_hash(self, manifest_hash: str) -> dict[str, Any] | None` (line 1493; public)
  - `completed_synthesis_manifests(self, source_set_id: str) -> list[dict[str, Any]]` (line 1501; public) — The manifest of each completed synthesis run of a source set, oldest first, with the run's ``proposal_id`` beside it.
  - `insert_synthesis_run(self, *, manifest_id: str, mode: str, agent_run_id: str | None=None, proposal_id: str | None=None, span_request: Any=None, status: str='created', run_id: str | None=None, clock: Clock | None=None) -> str` (line 1517; public)
  - `complete_synthesis_run(self, run_id: str, *, status: str, proposal_id: str | None=None, resolved_span_hashes: Any=None, coverage_decisions: Any=None, actual_usage: Any=None, clock: Clock | None=None) -> None` (line 1559; public)
  - `synthesis_run(self, run_id: str) -> dict[str, Any] | None` (line 1594; public)
  - `synthesis_run_for_agent_run(self, agent_run_id: str) -> dict[str, Any] | None` (line 1601; public)
  - `save_synthesis_candidate(self, run_id: str, candidate: Mapping[str, Any]) -> None` (line 1609; public) — Stage model output before gates and proposal persistence.
  - `save_synthesis_shard_result(self, *, shard_key: str, shard_ordinal: int, shard_count: int, result: Mapping[str, Any], manifest_hash: str | None=None, clock: Clock | None=None) -> None` (line 1619; public) — Persist one completed synthesis shard's model output (durable checkpoint).
  - `synthesis_shard_result(self, shard_key: str) -> dict[str, Any] | None` (line 1659; public)
  - `discard_synthesis_shard_result(self, shard_key: str, *, output: Mapping[str, Any] | None=None) -> None` (line 1670; public) — Delete one shard's saved output, so the next synthesis pays for a fresh answer instead of replaying one the quality gates rejected.
  - `finalize_stale_synthesis_runs(self, *, before_iso: str, clock: Clock | None=None) -> list[str]` (line 1689; public) — Mark abandoned non-terminal synthesis runs failed (startup hygiene).
  - `synthesis_run_introducing_entity(self, entity_type: str, entity_id: str) -> dict[str, Any] | None` (line 1719; public) — The synthesis run whose proposal introduced an entity (patch -> run -> manifest lineage, §9.2).
  - `insert_apply_intent(self, *, proposed_patch_id: str, item_ids: list[str], targets: list[Mapping[str, Any]], db_plan: list[Mapping[str, Any]], intent_id: str | None=None, clock: Clock | None=None) -> str` (line 1748; public) — Durably commit the write-ahead apply intent BEFORE any YAML is staged (§10.2).
  - `mark_apply_intent_applied(self, intent_id: str, *, clock: Clock | None=None) -> None` (line 1783; public)
  - `pending_apply_intents(self) -> list[dict[str, Any]]` (line 1791; public)
  - `outstanding_apply_intents(self) -> list[dict[str, Any]]` (line 1798; public) — Intents that refuse the next accept: ``pending`` (mid-flight) and ``conflicted`` (K3.5).
  - `apply_intent(self, intent_id: str) -> dict[str, Any] | None` (line 1810; public)
  - `mark_apply_intent_conflicted(self, intent_id: str, conflicts: list[Mapping[str, Any]], *, clock: Clock | None=None) -> None` (line 1815; public) — Recovery found target files changed since the intent (K3.5): nothing was written.
  - `mark_apply_intent_rolled_back(self, intent_id: str, *, clock: Clock | None=None) -> None` (line 1828; public) — The accept stopped before writing any file (K3.5: a target changed under it).
  - `mark_apply_intent_set_aside(self, intent_id: str, *, clock: Clock | None=None) -> bool` (line 1838; public) — The owner kept the files as they are (K3.5); True when a conflicted intent was settled.

## Internal implementation anchors

- `_proposal_item_identity(client_item_id: Any, payload: Any, edited_payload: Any) -> str` ([source](../../../../../../../src/learnloop/db/stores/content.py), line 18) — What a proposal item would create: the edited payload's ``id`` when it was edited, else the payload's, else its client id (no ``id`` in either).
- `_non_negative_tokens(value: Any) -> int` ([source](../../../../../../../src/learnloop/db/stores/content.py), line 28) — Coerce a token count for a NOT NULL DEFAULT 0 column (migration 131).
- `_decode_synthesis_manifest(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/content.py), line 45)
- `_decode_synthesis_run(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/content.py), line 63)
- `_decode_apply_intent(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/content.py), line 76)
- `_content_event_has_source_grounding(row: sqlite3.Row) -> bool` ([source](../../../../../../../src/learnloop/db/stores/content.py), line 86)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `ContentStoreMixin`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/usage|learnloop.ai.usage]] — imports `TokenUsage`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/records|learnloop.db.records]] — imports `_decode_proposal_batch`, `_decode_proposal_item`; calls `_decode_proposal_batch`, `_decode_proposal_item`
- [[Reference/Modules/learnloop/db/row_serialization|learnloop.db.row_serialization]] — imports `_json`, `_loads`; calls `_json`, `_loads`
- [[Reference/Modules/learnloop/db/stores/write_provenance|learnloop.db.stores.write_provenance]] — imports `record_text_write`; calls `record_text_write`
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

1. Modify [src/learnloop/db/stores/content.py](../../../../../../../src/learnloop/db/stores/content.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
