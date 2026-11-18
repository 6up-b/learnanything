---
title: "learnloop.db.stores.reader"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/reader.py"
source_paths:
  - "src/learnloop/db/stores/reader.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.db.stores.reader module"
  - "src/learnloop/db/stores/reader.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.reader`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.reader` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Reader annotations, source objects and reading progress.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/reader.py](../../../../../../../src/learnloop/db/stores/reader.py) |
| Source lines | 1593 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class ReaderStoreMixin` ([source](../../../../../../../src/learnloop/db/stores/reader.py), line 37)
  - `insert_source_exposure_event(self, event: Mapping[str, Any], *, clock: Clock | None=None) -> str` (line 39; public) — Record one Open-in-source view (§9.2).
  - `source_exposure_events(self, *, extraction_id: str | None=None, span_id: str | None=None, entity_type: str | None=None, entity_id: str | None=None, after: str | None=None, before: str | None=None, limit: int | None=None) -> list[dict[str, Any]]` (line 83; public)
  - `insert_render_view(self, view: Mapping[str, Any], *, clock: Clock | None=None) -> str` (line 137; public)
  - `get_render_view(self, render_view_id: str) -> dict[str, Any] | None` (line 177; public)
  - `render_view_by_request_hash(self, request_hash: str) -> dict[str, Any] | None` (line 184; public)
  - `insert_render_crosswalk_nodes(self, render_view_id: str, nodes: Sequence[Mapping[str, Any]], *, clock: Clock | None=None) -> None` (line 191; public)
  - `render_crosswalk(self, render_view_id: str) -> list[dict[str, Any]]` (line 225; public)
  - `upsert_block_health(self, health: Mapping[str, Any], *, clock: Clock | None=None) -> str` (line 236; public)
  - `block_health(self, extraction_id: str, span_id: str) -> dict[str, Any] | None` (line 272; public)
  - `block_health_for_extraction(self, extraction_id: str) -> list[dict[str, Any]]` (line 281; public)
  - `create_annotation(self, *, source_id: str, clock: Clock | None=None) -> str` (line 291; public)
  - `next_annotation_version_ordinal(self, annotation_id: str) -> int` (line 301; public)
  - `annotation_head(self, annotation_id: str) -> dict[str, Any] | None` (line 310; public) — Rebuildable annotation-head projection: the latest version + anchor + segments.
  - `annotations_for_source(self, source_id: str) -> list[dict[str, Any]]` (line 344; public) — Annotation heads for a source, omitting delete-intended annotations.
  - `standing_annotation_ids(self) -> set[str]` (line 362; public) — Every annotation the Reader lists (no standing delete intent): curriculum C2b's vault notes read the learner's annotations by this rule.
  - `withdraw_annotation_delete(self, *, annotation_id: str, delete_event_id: str, clock: Clock | None=None) -> tuple[str, str | None, bool]` (line 373; public) — Undo one delete intent of an annotation: checked and written in one immediate transaction, so no other write lands between the check and the undo.
  - `annotation_history(self, annotation_id: str) -> dict[str, Any]` (line 410; public)
  - `append_annotation_event(self, *, annotation_id: str, event_type: str, payload: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` (line 438; public)
  - `_write_annotation_version(self, connection: sqlite3.Connection, *, annotation_id: str, version_ordinal: int, version: Mapping[str, Any], now: str) -> str` (line 452; internal)
  - `_write_anchor_version(self, connection: sqlite3.Connection, *, annotation_id: str, version_ordinal: int, anchor: Mapping[str, Any], now: str) -> str` (line 480; internal)
  - `append_annotation_version(self, *, annotation_id: str, version: Mapping[str, Any], anchor: Mapping[str, Any], event_type: str='edit', event_payload: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, str]` (line 537; public)
  - `capture_by_client_key(self, client_idempotency_key: str) -> dict[str, Any] | None` (line 562; public)
  - `pending_capture_outbox(self, *, limit: int=100) -> list[dict[str, Any]]` (line 570; public)
  - `recoverable_capture_outbox(self, *, limit: int=100) -> list[dict[str, Any]]` (line 579; public) — Rows a drain may claim: `pending` plus stale `draining` rows left behind by a crash mid-drain.
  - `get_capture_outbox(self, outbox_id: str) -> dict[str, Any] | None` (line 592; public)
  - `mark_capture_outbox(self, outbox_id: str, *, state: str, target_ref: str | None=None, last_error: str | None=None, bump_attempts: bool=False, clock: Clock | None=None) -> None` (line 599; public)
  - `enqueue_reader_request(self, *, request_key: str, fields: Mapping[str, Any], revive_cancelled: bool=False, clock: Clock | None=None) -> dict[str, Any]` (line 626; public) — Idempotent enqueue keyed on ``request_key`` (§6.2): the same contract reuses the standing row; a material version change has a different key -> a new row.
  - `has_queued_reader_requests(self) -> bool` (line 715; public)
  - `reader_request_by_key(self, request_key: str) -> dict[str, Any] | None` (line 722; public)
  - `get_reader_request(self, request_id: str) -> dict[str, Any] | None` (line 729; public)
  - `reader_requests_for_source(self, source_id: str) -> list[dict[str, Any]]` (line 736; public)
  - `claim_next_reader_request(self, *, worker_id: str, now_iso: str, lease_expires_at: str, lease_cutoff_iso: str) -> dict[str, Any] | None` (line 745; public) — Claim the highest-priority runnable request under a fenced lease.
  - `resolve_reader_request(self, *, request_id: str, status: str, result: Mapping[str, Any] | None=None, error: Mapping[str, Any] | None=None, actual_input_tokens: int=0, actual_output_tokens: int=0, cache_hit: bool=False, expected_lease_epoch: int | None=None, clock: Clock | None=None) -> bool` (line 791; public) — Terminal/complete transition; releases the lease.
  - `cancel_reader_request(self, request_id: str, *, clock: Clock | None=None) -> dict[str, Any] | None` (line 823; public) — Request cancellation.
  - `reader_request_still_held(self, request_id: str, *, releasing_annotation_id: str) -> bool` (line 839; public) — Whether a synthesis request is still wanted once the capture ``releasing_annotation_id`` lets go of it (Codex re-review of RW1b, F15).
  - `reader_request_standing_holder(self, request_id: str, *, releasing_annotation_id: str) -> dict[str, Any] | None` (line 864; public) — The latest capture other than ``releasing_annotation_id`` whose outbox row converted onto this request and whose annotation has no standing delete: the capture a request is rebound to when the capture it is bound to is reverted while another still holds it (Codex final verify of…
  - `rebind_reader_request(self, request_id: str, *, annotation_id: str, commitment_id: str | None, clock: Clock | None=None) -> None` (line 883; public) — Bind a request to the capture it now serves (F16): the annotation whose instructions the model reads and the commitment its result maps to.
  - `rekey_reader_request(self, request_id: str, *, request_key: str, clock: Clock | None=None) -> str` (line 897; public) — Move a request to the key its own instructions give it, freeing the key it held for a capture asking something else (Codex verify of RW1b fix round 3, F16 legacy rows).
  - `append_reader_request_proposal(self, request_id: str, proposal: Mapping[str, Any]) -> None` (line 920; public) — Record one more proposal in a completed request's result: the commitment mapping a rebind adds when the result had none to move (Codex verify of RW1b fix round 3, F16).
  - `capture_reverted(self, annotation_id: str, *, reason: str) -> bool` (line 939; public) — Whether a delete of the annotation with this ``reason`` stands (one no undo names): the capture was reverted, so its outbox row converts to no work (Codex re-review of RW1b, F14).
  - `retry_reader_request(self, request_id: str, *, clock: Clock | None=None) -> dict[str, Any] | None` (line 955; public) — Reset a failed request to ``queued`` for another drain.
  - `insert_reader_authored_question(self, *, fields: Mapping[str, Any], clock: Clock | None=None) -> str` (line 976; public) — Insert one authored question.
  - `inquiry_reader_authored_question(self, *, inquiry_root_event_id: str, prompt_version: str) -> dict[str, Any] | None` (line 1055; public) — RW1a: the newest inquiry-scoped question for one root exchange and prompt version, any status -- its reuse key (a dismissed row suppresses re-authoring for its own key).
  - `selection_reader_authored_question(self, *, extraction_id: str, anchor_span_ids: list[str] | tuple[str, ...], question_style: str, prompt_version: str) -> dict[str, Any] | None` (line 1071; public) — RW1b: the selection-scoped question for one reuse key (extraction, anchor spans in reading order, style, prompt version), any status -- a dismissed row suppresses re-authoring for its own key.
  - `get_reader_authored_question(self, question_id: str) -> dict[str, Any] | None` (line 1087; public)
  - `upsert_reader_section_progress(self, *, extraction_id: str, section_id: str, spans_seen: int | None=None, span_count: int | None=None, revealed: bool=False, completed: bool=False, keep_ahead_request: bool=False, clock: Clock | None=None) -> dict[str, Any]` (line 1096; public) — Monotone upsert: spans_seen/span_count only grow; revealed_at / completed_at stamp once and never clear; generation_batch_id untouched.
  - `reader_section_progress_row(self, extraction_id: str, section_id: str) -> dict[str, Any] | None` (line 1151; public)
  - `reader_section_progress_for(self, extraction_id: str) -> list[dict[str, Any]]` (line 1159; public)
  - `carry_reader_section_progress(self, extraction_id: str, rows: Iterable[Mapping[str, Any]], *, clock: Clock | None=None) -> int` (line 1167; public) — Carry section progress onto a new reading of the same book (re-read safety, 2026-10-14).
  - `mark_section_generation(self, *, extraction_id: str, section_id: str, batch_id: str, clock: Clock | None=None) -> bool` (line 1210; public) — Stamp the generation batch id exactly once.
  - `set_section_generation_batch(self, *, extraction_id: str, section_id: str, batch_id: str, clock: Clock | None=None) -> None` (line 1228; public) — Unconditional stamp update (replaces the 'enqueuing' placeholder with the real batch id after a successful enqueue).
  - `swap_section_generation(self, *, extraction_id: str, section_id: str, from_batch_id: str, batch_id: str, clock: Clock | None=None) -> bool` (line 1245; public) — Mobile v2 D6: move a section's generation stamp from ``from_batch_id`` to ``batch_id``, once: False when the stamp is no longer ``from_batch_id`` (another process took it).
  - `deferred_section_generations(self, stamp: str, *, extraction_id: str | None=None) -> list[dict[str, Any]]` (line 1266; public) — Mobile v2 D6: the completed sections whose generation stamp is ``stamp`` (left for the primary by the phone host), oldest first.
  - `reader_authored_questions_for_extraction(self, extraction_id: str) -> list[dict[str, Any]]` (line 1280; public) — All authored questions for an extraction, newest first per section.
  - `latest_reader_authored_question(self, *, extraction_id: str, section_id: str) -> dict[str, Any] | None` (line 1296; public) — The newest authored question for one section, any status — the idempotency anchor: a dismissed row suppresses re-authoring.
  - `transition_reader_authored_question(self, *, question_id: str, status: str, response_md: str | None=None, practice_item_id: str | None=None, self_check: str | None=None, clock: Clock | None=None) -> bool` (line 1313; public) — Row-status transition (proposed -> answered | dismissed | escalated).
  - `create_source_object(self, *, source_id: str, clock: Clock | None=None) -> str` (line 1356; public)
  - `append_source_object_version(self, *, source_object_id: str, version: Mapping[str, Any], citations: list[Mapping[str, Any]] | None=None, clock: Clock | None=None) -> dict[str, Any]` (line 1366; public)
  - `source_object_head(self, source_object_id: str) -> dict[str, Any] | None` (line 1420; public)
  - `source_objects_for_source(self, source_id: str) -> list[dict[str, Any]]` (line 1448; public)
  - `create_source_object_relation(self, *, source_object_id: str, related_object_id: str | None, relation_type: str, learner_text: str | None=None, authorship: str='learner', review_status: str='proposed', clock: Clock | None=None, version_ordinal: int=1) -> str` (line 1456; public)
  - `source_object_relation(self, relation_id: str) -> dict[str, Any] | None` (line 1476; public)
  - `create_mapping_proposal(self, *, source_object_id: str | None=None, annotation_id: str | None=None, target_kind: str, target_ref: str | None=None, confidence: float | None=None, rationale: str | None=None, provenance: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` (line 1483; public)
  - `mapping_proposals(self, *, status: str | None=None, source_object_id: str | None=None) -> list[dict[str, Any]]` (line 1504; public)
  - `decide_mapping_proposal(self, *, proposal_id: str, status: str, clock: Clock | None=None) -> dict[str, Any] | None` (line 1523; public)
  - `repoint_mapping_proposal(self, proposal_id: str, *, target_ref: str) -> bool` (line 1539; public) — Point an undecided mapping proposal at another target: a completed synthesis request rebound to the capture that still holds it moves its commitment mapping to that capture's commitment (Codex verify of RW1b fix round 3, F16).
  - `set_source_object_status(self, *, source_object_id: str, status: str, clock: Clock | None=None) -> dict[str, Any]` (line 1553; public) — Append a status-only successor version carrying the head content forward.
  - `_set_source_object_status(self, *, source_object_id: str, status: str, clock: Clock | None=None) -> dict[str, Any]` (line 1566; internal)

### Module constants

- `_UNDO_OF` ([src/learnloop/db/stores/reader.py](../../../../../../../src/learnloop/db/stores/reader.py), line 19)
- `_STANDING_DELETE` ([src/learnloop/db/stores/reader.py](../../../../../../../src/learnloop/db/stores/reader.py), line 29)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `ReaderStoreMixin`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/row_serialization|learnloop.db.row_serialization]] — imports `_json`, `_loads`; calls `_json`, `_loads`
- [[Reference/Modules/learnloop/db/stores/router_objective|learnloop.db.stores.router_objective]] — imports `module`; calls `fill_receipt`, `split_receipt`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

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

1. Modify [src/learnloop/db/stores/reader.py](../../../../../../../src/learnloop/db/stores/reader.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
