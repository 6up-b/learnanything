---
title: "learnloop.db.stores.retrieval_spaces"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/retrieval_spaces.py"
source_paths:
  - "src/learnloop/db/stores/retrieval_spaces.py"
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
  - "learnloop.db.stores.retrieval_spaces module"
  - "src/learnloop/db/stores/retrieval_spaces.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.retrieval_spaces`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.retrieval_spaces` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Embedding spaces, retrieval feedback and the fusion posterior (migration 220).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/retrieval_spaces.py](../../../../../../../src/learnloop/db/stores/retrieval_spaces.py) |
| Source lines | 213 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `has_tables(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/retrieval_spaces.py), line 32)
- `register_space(connection: sqlite3.Connection, *, space_id: str, name: str, kind: str, pins: Mapping[str, Any], status: str, reason: str | None=None, now: str | None=None) -> None` ([source](../../../../../../../src/learnloop/db/stores/retrieval_spaces.py), line 39) — Insert a space once; a known space keeps its row (its status changes only through :func:`set_space_status`).
- `set_space_status(connection: sqlite3.Connection, space_id: str, status: str, *, reason: str | None=None, now: str | None=None) -> None` ([source](../../../../../../../src/learnloop/db/stores/retrieval_spaces.py), line 54)
- `set_space_canaries(connection: sqlite3.Connection, space_id: str, canaries: Mapping[str, Any], *, now: str | None=None) -> None` ([source](../../../../../../../src/learnloop/db/stores/retrieval_spaces.py), line 65) — Store a space's canary vectors once (the first healthy batch's).
- `spaces(connection: sqlite3.Connection) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/retrieval_spaces.py), line 74)
- `append_feedback(connection: sqlite3.Connection, rows: Iterable[Mapping[str, Any]], *, now: str | None=None) -> int` ([source](../../../../../../../src/learnloop/db/stores/retrieval_spaces.py), line 87)
- `feedback_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/retrieval_spaces.py), line 105) — Every feedback row in insertion order (the replayer's input).
- `deliveries_for_owner(connection: sqlite3.Connection, *, consumer: str, owner_id: str, keys: Sequence[tuple[str, str]]) -> dict[tuple[str, str], dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/retrieval_spaces.py), line 118) — The newest delivery row of each span key for one consumer's owner id.
- `record_citation_signals(connection: sqlite3.Connection, *, consumer: str, owner_id: str, citations: Sequence[Mapping[str, Any]], now: str | None=None) -> int` ([source](../../../../../../../src/learnloop/db/stores/retrieval_spaces.py), line 137) — ``cited`` rows for validated citations of spans this owner's search delivered (the newest delivery of each span); 0 when none was logged.
- `delivery_for_receipt(connection: sqlite3.Connection, receipt_id: str, key: tuple[str, str]) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/retrieval_spaces.py), line 151)
- `replace_fusion_posteriors(connection: sqlite3.Connection, rows: Sequence[Mapping[str, Any]]) -> int` ([source](../../../../../../../src/learnloop/db/stores/retrieval_spaces.py), line 164) — Replace the whole projection (the replayer's and the refit's only write).
- `fusion_posteriors(connection: sqlite3.Connection) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/retrieval_spaces.py), line 180)

### Module constants

- `SPACE_STATUSES` ([src/learnloop/db/stores/retrieval_spaces.py](../../../../../../../src/learnloop/db/stores/retrieval_spaces.py), line 19)
- `FEEDBACK_EVENTS` ([src/learnloop/db/stores/retrieval_spaces.py](../../../../../../../src/learnloop/db/stores/retrieval_spaces.py), line 20)
- `SIGNAL_EVENTS` ([src/learnloop/db/stores/retrieval_spaces.py](../../../../../../../src/learnloop/db/stores/retrieval_spaces.py), line 21)

### Explicit exports

`__all__` declares:

- `FEEDBACK_EVENTS`
- `SIGNAL_EVENTS`
- `SPACE_STATUSES`
- `append_feedback`
- `deliveries_for_owner`
- `delivery_for_receipt`
- `feedback_rows`
- `fusion_posteriors`
- `has_tables`
- `record_citation_signals`
- `register_space`
- `replace_fusion_posteriors`
- `set_space_canaries`
- `set_space_status`
- `spaces`

## Internal implementation anchors

- `_now() -> str` ([source](../../../../../../../src/learnloop/db/stores/retrieval_spaces.py), line 24)
- `_json(value: Any) -> str` ([source](../../../../../../../src/learnloop/db/stores/retrieval_spaces.py), line 28)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/local_embeddings/fusion|learnloop.local_embeddings.fusion]] — imports `feedback_rows`, `has_tables`, `replace_fusion_posteriors`; statically calls `feedback_rows`, `has_tables`, `replace_fusion_posteriors`
- [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]] — imports `has_tables`, `register_space`; statically calls `has_tables`, `register_space`
- [[Reference/Modules/learnloop/source_retrieval/feedback|learnloop.source_retrieval.feedback]] — imports `append_feedback`, `delivery_for_receipt`, `has_tables`, `record_citation_signals`; statically calls `append_feedback`, `delivery_for_receipt`, `has_tables`, `record_citation_signals`
- [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]] — imports `register_space`, `set_space_canaries`, `set_space_status`, `spaces`; statically calls `register_space`, `set_space_canaries`, `set_space_status`, `spaces`
- [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]] — imports `spaces`; statically calls `spaces`
- [[Reference/Modules/learnloop/source_retrieval/spaces|learnloop.source_retrieval.spaces]] — imports `fusion_posteriors`, `spaces`; statically calls `fusion_posteriors`, `spaces`
- [[Reference/Modules/learnloop/source_retrieval/student_encoder|learnloop.source_retrieval.student_encoder]] — imports `feedback_rows`; statically calls `feedback_rows`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `has_tables`, `record_citation_signals`; statically calls `has_tables`, `record_citation_signals`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `json`, `sqlite3`, `typing`, `uuid`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/local_embeddings/fusion|learnloop.local_embeddings.fusion]], [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]], [[Reference/Modules/learnloop/source_retrieval/feedback|learnloop.source_retrieval.feedback]], [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]], [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_local_index.py](../../../../../../../tests/test_local_index.py) — direct import
  - `test_a_moved_canary_stores_nothing_and_marks_epoch_drift`
  - `test_a_worker_on_another_software_epoch_stores_nothing`
  - `test_the_index_job_caches_both_variants_and_registers_the_spaces`
- [tests/test_retrieval_spaces_migration.py](../../../../../../../tests/test_retrieval_spaces_migration.py) — direct import
  - `test_220_on_the_durability_lane`
  - `test_a_database_before_220_reads_as_empty`
  - `test_feedback_is_append_only_and_spaces_are_mutable`
  - `test_the_head_fixture_holds_220_in_rollback_mode`
- [tests/test_source_retrieval_tutor.py](../../../../../../../tests/test_source_retrieval_tutor.py) — direct import
  - `test_the_tutor_records_as_delivered_only_the_spans_it_was_given`
- [tests/test_source_space_resolver.py](../../../../../../../tests/test_source_space_resolver.py) — direct import
  - `test_a_challenger_learns_its_way_up_from_resolver_receipts`
  - `test_ordinary_use_completes_the_loop_opens_ask_citations_and_the_background_refit`
  - `test_signals_join_their_delivery_and_the_posterior_replays_byte_identically`
  - `test_the_local_space_reports_no_encoder_in_p1_and_serves_through_the_hook`
- [tests/test_voyage_fallback.py](../../../../../../../tests/test_voyage_fallback.py) — direct import
  - `test_the_hosted_space_is_registered_when_its_first_vectors_land`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/retrieval_spaces.py](../../../../../../../src/learnloop/db/stores/retrieval_spaces.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
