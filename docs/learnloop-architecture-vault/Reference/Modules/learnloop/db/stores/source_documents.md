---
title: "learnloop.db.stores.source_documents"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/source_documents.py"
source_paths:
  - "src/learnloop/db/stores/source_documents.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.db.stores.source_documents module"
  - "src/learnloop/db/stores/source_documents.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.source_documents`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.source_documents` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Source documents, extraction runs and entity links.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/source_documents.py](../../../../../../../src/learnloop/db/stores/source_documents.py) |
| Source lines | 1371 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class SourceDocumentStoreMixin` ([source](../../../../../../../src/learnloop/db/stores/source_documents.py), line 102)
  - `search_source_blocks(self, *, query: str, extraction_ids: Sequence[str], limit: int=80) -> list[dict[str, Any]]` (line 104; public) — Case-insensitive substring search over document blocks of the given extractions (no FTS index exists; ``instr`` over ``text`` is adequate at local-vault scale).
  - `upsert_source_artifact(self, *, id: str, acquisition_kind: str, canonical_uri: str | None=None, work_id: str | None=None, current_revision_id: str | None=None, display_title: str | None=None, reader_enabled: bool | None=None, clock: Clock | None=None) -> None` (line 131; public)
  - `set_source_reader_enabled(self, source_id: str, enabled: bool, *, clock: Clock | None=None) -> None` (line 171; public)
  - `sources_with_retired_keep_local(self) -> list[str]` (line 181; public) — Books that still carry the retired "Keep this book on this computer" (``source_artifacts.keep_local``, migration 198; retired by the owner 2026-10-13): nothing consults the column now (generic ``SELECT *`` reads still fetch it), ``learnloop doctor`` names them.
  - `get_source_artifact(self, source_id: str) -> dict[str, Any] | None` (line 193; public)
  - `source_artifact_by_uri(self, acquisition_kind: str, canonical_uri: str) -> dict[str, Any] | None` (line 200; public)
  - `set_source_current_revision(self, source_id: str, revision_id: str, *, clock: Clock | None=None) -> None` (line 208; public)
  - `insert_source_revision(self, *, id: str, source_id: str, asset_hash: str, note_id: str | None=None, original_uri: str | None=None, retrieved_at: str | None=None, supersedes_revision_id: str | None=None, clock: Clock | None=None) -> None` (line 218; public)
  - `get_source_revision(self, revision_id: str) -> dict[str, Any] | None` (line 252; public)
  - `source_revision_by_asset_hash(self, source_id: str, asset_hash: str) -> dict[str, Any] | None` (line 259; public)
  - `source_revisions_for(self, source_id: str) -> list[dict[str, Any]]` (line 267; public)
  - `all_source_artifacts(self) -> list[dict[str, Any]]` (line 275; public)
  - `extraction_runs_for_revision(self, revision_id: str) -> list[dict[str, Any]]` (line 282; public)
  - `document_ir_counts(self, extraction_id: str) -> dict[str, int]` (line 290; public)
  - `insert_extraction_run(self, *, id: str, revision_id: str, extractor: str, extractor_version: str, extraction_request_hash: str, ir_schema_version: str, model_versions: Mapping[str, str] | None=None, config: Mapping[str, Any] | None=None, page_selection: Iterable[int] | None=None, parent_extraction_id: str | None=None, status: str='queued', clock: Clock | None=None) -> None` (line 302; public)
  - `get_extraction_run(self, extraction_id: str) -> dict[str, Any] | None` (line 346; public)
  - `extraction_run_by_request_hash(self, revision_id: str, extraction_request_hash: str) -> dict[str, Any] | None` (line 353; public)
  - `complete_extraction_run(self, extraction_id: str, *, extraction_result_hash: str, status: str='completed', health: Mapping[str, Any] | None=None, clock: Clock | None=None) -> None` (line 363; public)
  - `persist_document_ir(self, extraction_id: str, ir: DocumentIR) -> None` (line 390; public)
  - `block_content_hashes(self, extraction_id: str) -> dict[str, str]` (line 483; public) — ``{span_id: content_hash}`` of a reading's blocks in reading order, without loading its IR (the Reader asks on every annotation refresh).
  - `document_blocks(self, extraction_id: str, span_ids: Sequence[str]) -> list[DocumentBlock]` (line 494; public) — The named blocks of one extraction in reading order (ordinal), without loading its IR; ids it lacks are left out (Reader CA1, the problem as printed).
  - `document_blocks_on_pages(self, extraction_id: str, pages: Sequence[int]) -> list[DocumentBlock]` (line 510; public) — Every block of one extraction on the given pages, in reading order.
  - `load_document_ir(self, extraction_id: str) -> DocumentIR | None` (line 525; public)
  - `insert_span_reanchor(self, *, from_extraction_id: str, from_span_id: str, to_extraction_id: str, to_span_id: str, match_kind: str, confidence: float | None=None, clock: Clock | None=None) -> None` (line 554; public)
  - `span_reanchors_from(self, from_extraction_id: str) -> list[dict[str, Any]]` (line 586; public)
  - `record_span_reanchors(self, from_extraction_id: str, to_extraction_id: str, aliases: Iterable[tuple[str, str, str, float | None]], *, clock: Clock | None=None) -> int` (line 594; public) — Persist one re-read's span aliases ``(from span, to span, match kind, confidence)`` in one transaction.
  - `span_reanchors_between(self, from_extraction_id: str, to_extraction_id: str) -> list[dict[str, Any]]` (line 628; public)
  - `span_reanchor_origins(self, to_extraction_id: str) -> list[str]` (line 637; public) — The readings with recorded aliases into ``to_extraction_id``, the most recently recorded first.
  - `backfill_locator_schemes(self, locators: Iterable[str], *, clock: Clock | None=None) -> dict[str, str]` (line 649; public) — Shape-detect and stamp a declared scheme onto each existing ref.
  - `locator_scheme(self, locator: str) -> str | None` (line 677; public)
  - `upsert_unit_selection(self, *, extraction_id: str, source_id: str | None, revision_id: str | None, selected_unit_ids: list[str], boundary_overrides: list[dict] | None=None, needs_review: list[str] | None=None, exam_use_modes: Mapping[str, str] | None=None, exam_paper_metadata: Mapping[str, Any] | None=None, role_override: str | None=None, clock: Clock | None=None) -> None` (line 691; public)
  - `get_unit_selection(self, extraction_id: str) -> dict[str, Any] | None` (line 755; public)
  - `insert_unit_inventory(self, *, id: str, source_revision_id: str, extraction_id: str, unit_id: str, unit_semantic_hash: str, inventory_profile: str, inventory_schema_version: int, prompt_version: str, provider: str, model: str, inventory: Mapping[str, Any], usage: Mapping[str, Any] | None=None, made_as_role: str | None=None, reused_from_inventory_id: str | None=None, clock: Clock | None=None) -> str` (line 766; public) — Write one cached inventory (§7) and, for a model run on ``extraction_id`` (not a reuse), its held-out signals into the append-only ``source_held_out_signal_marks`` ledger, in one transaction (exam protection by extraction identity).
  - `held_out_signal_marks(self) -> list[dict[str, Any]]` (line 870; public) — Every row of the held-out signal ledger (exam protection by extraction identity), with its book's source id, oldest first.
  - `reusable_unit_inventories(self, *, source_revision_id: str, unit_id: str, unit_semantic_hash: str, inventory_schema_version: int, prompt_version: str, provider: str, model: str, request_key: str) -> list[dict[str, Any]]` (line 881; public) — Cached rows sharing the non-profile semantic identity (§7).
  - `get_unit_inventory(self, inventory_id: str) -> dict[str, Any] | None` (line 933; public)
  - `unit_inventories_for_extraction(self, extraction_id: str) -> list[dict[str, Any]]` (line 940; public)
  - `unit_inventories_for_revision(self, revision_id: str) -> list[dict[str, Any]]` (line 948; public)
  - `source_unit_inventory_claims(self) -> list[dict[str, Any]]` (line 956; public) — Facet-candidate harvesting seam (knowledge-model §3.3).
  - `upsert_exam_profile(self, *, id: str, scope_kind: str, scope_id: str, profile_hash: str, profile: Mapping[str, Any], clock: Clock | None=None) -> None` (line 989; public)
  - `get_exam_profile(self, scope_kind: str, scope_id: str) -> dict[str, Any] | None` (line 1014; public)
  - `insert_entity_source_link(self, *, entity_type: str, entity_id: str, locator: str, relation: str, source_id: str | None=None, revision_id: str | None=None, locator_scheme: str | None=None, extraction_id: str | None=None, asset_hash: str | None=None, span_hash: str | None=None, patch_id: str | None=None, status: str='current', link_id: str | None=None, created_at: str | None=None, clock: Clock | None=None) -> str` (line 1031; public) — Insert an entity_source_links row (§9.1).
  - `entity_source_links(self, entity_type: str, entity_id: str) -> list[dict[str, Any]]` (line 1087; public)
  - `entity_source_links_for_revision(self, revision_id: str) -> list[dict[str, Any]]` (line 1101; public)
  - `insert_notation_mapping(self, *, entity_type: str, entity_id: str, canonical_notation: str, alternate_notation: str, subject_id: str | None=None, context: str | None=None, source_id: str | None=None, revision_id: str | None=None, locator: str | None=None, patch_id: str | None=None, status: str='active', mapping_id: str | None=None, clock: Clock | None=None) -> str` (line 1109; public)
  - `notation_mappings_for_entity(self, entity_type: str, entity_id: str) -> list[dict[str, Any]]` (line 1156; public)
  - `insert_source_conflict(self, *, entity_type: str, entity_id: str, statement: str, subject_id: str | None=None, left_source_id: str | None=None, left_revision_id: str | None=None, left_locator: str | None=None, right_source_id: str | None=None, right_revision_id: str | None=None, right_locator: str | None=None, status: str='open', resolution: Any=None, patch_id: str | None=None, conflict_id: str | None=None, clock: Clock | None=None) -> str` (line 1170; public)
  - `source_conflicts_for_entity(self, entity_type: str, entity_id: str) -> list[dict[str, Any]]` (line 1223; public)
  - `entity_source_links_for_sources(self, source_ids: list[str]) -> list[dict[str, Any]]` (line 1237; public) — All entity_source_links whose ``source_id`` is in ``source_ids``.
  - `stale_entity_source_links(self, statuses: tuple[str, ...]=('stale', 'needs_reanchor')) -> list[dict[str, Any]]` (line 1255; public) — Links whose spans went stale / need re-anchoring (§10.4 revision refresh).
  - `mark_entity_source_link_status(self, link_id: str, *, status: str, superseded_by_link_id: str | None=None, clock: Clock | None=None) -> None` (line 1268; public)
  - `all_notation_mappings(self, status: str | None='active') -> list[dict[str, Any]]` (line 1292; public)
  - `source_conflict(self, conflict_id: str) -> dict[str, Any] | None` (line 1303; public)
  - `source_conflicts_by_status(self, status: str='open') -> list[dict[str, Any]]` (line 1310; public)
  - `resolve_source_conflict(self, conflict_id: str, *, status: str, resolution: Any, resolution_kind: str, actor: str | None=None, rationale: str | None=None, clock: Clock | None=None) -> str` (line 1318; public) — Persist a conflict resolution + an immutable audit row (§10.2).
  - `source_conflict_resolutions(self, conflict_id: str) -> list[dict[str, Any]]` (line 1357; public)

## Internal implementation anchors

- `_decode_source_conflict(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/source_documents.py), line 20)
- `_decode_extraction_run(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/source_documents.py), line 26)
- `_decode_unit_selection(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/source_documents.py), line 35)
- `_decode_unit_inventory(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/source_documents.py), line 45)
- `_decode_exam_profile(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/source_documents.py), line 52)
- `_decode_document_block(row: sqlite3.Row) -> DocumentBlock` ([source](../../../../../../../src/learnloop/db/stores/source_documents.py), line 58)
- `_decode_document_unit(row: sqlite3.Row) -> DocumentUnit` ([source](../../../../../../../src/learnloop/db/stores/source_documents.py), line 75)
- `_decode_document_asset(row: sqlite3.Row) -> DocumentAsset` ([source](../../../../../../../src/learnloop/db/stores/source_documents.py), line 89)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `SourceDocumentStoreMixin`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/row_serialization|learnloop.db.row_serialization]] — imports `_json`, `_loads`; calls `_json`, `_loads`
- [[Reference/Modules/learnloop/db/stores/held_out_signals|learnloop.db.stores.held_out_signals]] — imports `is_exam_role`, `qualify_unrecorded_signals`; calls `is_exam_role`, `qualify_unrecorded_signals`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ingest/ir|learnloop.ingest.ir]] — imports `DocumentAsset`, `DocumentBlock`, `DocumentIR`, `DocumentUnit`, `ExtractionHealth`; calls `DocumentAsset`, `DocumentBlock`, `DocumentIR`, `DocumentUnit`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `detect_locator_scheme`; calls `detect_locator_scheme`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

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

1. Modify [src/learnloop/db/stores/source_documents.py](../../../../../../../src/learnloop/db/stores/source_documents.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
