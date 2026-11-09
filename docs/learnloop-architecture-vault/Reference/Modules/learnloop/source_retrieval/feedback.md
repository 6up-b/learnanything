---
title: "learnloop.source_retrieval.feedback"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/feedback.py"
source_paths:
  - "src/learnloop/source_retrieval/feedback.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.source_retrieval"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.source_retrieval.feedback module"
  - "src/learnloop/source_retrieval/feedback.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.feedback`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.feedback` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: Retrieval feedback: deliveries, signals and the fusion posterior's refit (spec §9.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/feedback.py](../../../../../../src/learnloop/source_retrieval/feedback.py) |
| Source lines | 227 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `new_receipt_id() -> str` ([source](../../../../../../src/learnloop/source_retrieval/feedback.py), line 53)
- `log_search(repository: Repository, *, receipt_id: str, consumer: str, query_kind: str, owner_id: str, resolution: Mapping[str, Any], hits: Sequence[Any], space_ranks: Mapping[str, Mapping[str, int]], lists_available: Sequence[str]=(), queried: Sequence[str]=(), query_propensity: Mapping[str, float] | None=None, query_set_propensity: float | None=None) -> int` ([source](../../../../../../src/learnloop/source_retrieval/feedback.py), line 57) — The one ``query`` row of a search, its candidates' ranks included; returns rows written (0 on failure).
- `deliver(vault: Any, repository: Repository, search: Any, keys: Sequence[tuple[str, str]]) -> list[int]` ([source](../../../../../../src/learnloop/source_retrieval/feedback.py), line 82) — Record what a consumer finally delivers from ``search`` (Codex review F9).
- `record_citations(repository: Repository, *, consumer: str, owner_id: str, citations: Sequence[Mapping[str, Any]]) -> int` ([source](../../../../../../src/learnloop/source_retrieval/feedback.py), line 132) — ``cited`` rows for validated citations of spans this owner's search delivered.
- `record_receipt_citations(repository: Repository, *, receipt_ids: Sequence[str], citations: Sequence[Mapping[str, Any]]) -> int` ([source](../../../../../../src/learnloop/source_retrieval/feedback.py), line 146) — ``cited`` rows for validated citations of spans one of ``receipt_ids`` delivered (a library ask's tutor answer cites the ask's own retrieval); returns rows written, 0 when none was delivered or on failure.
- `refresh_due(repository: Repository, *, last_refit: Any | None, now: Any) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/feedback.py), line 181) — Whether the background refit should run: receipts newer than the stored posterior, and this host has not refitted within ``REFIT_EVERY_HOURS``.
- `record_open(repository: Repository, *, receipt_id: str, extraction_id: str, span_id: str) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/feedback.py), line 198) — An ``opened`` row when the learner opens a span that ``receipt_id`` delivered.
- `feedback_summary(repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/feedback.py), line 216)

### Module constants

- `REFIT_EVERY_HOURS` ([src/learnloop/source_retrieval/feedback.py](../../../../../../src/learnloop/source_retrieval/feedback.py), line 178)

### Explicit exports

`__all__` declares:

- `REFIT_EVERY_HOURS`
- `deliver`
- `feedback_summary`
- `log_search`
- `new_receipt_id`
- `record_citations`
- `record_open`
- `record_receipt_citations`
- `refit_posteriors`
- `refresh_due`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `refresh_due`; statically calls `refresh_due`
- [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]] — imports `deliver`; statically calls `deliver`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `deliver`; statically calls `deliver`
- [[Reference/Modules/learnloop/source_retrieval/library|learnloop.source_retrieval.library]] — imports `deliver`; statically calls `deliver`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `record_receipt_citations`; statically calls `record_receipt_citations`
- [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]] — imports `module`; statically calls `log_search`, `new_receipt_id`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `deliver`; statically calls `deliver`
- [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]] — imports `feedback_summary`; statically calls `feedback_summary`
- [[Reference/Modules/learnloop/source_retrieval/tutor|learnloop.source_retrieval.tutor]] — imports `deliver`; statically calls `deliver`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `record_open`; statically calls `record_open`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/retrieval_spaces|learnloop.db.stores.retrieval_spaces]] — imports `append_feedback`, `delivery_for_receipt`, `feedback_rows`, `has_tables`, `record_citation_signals`; calls `append_feedback`, `delivery_for_receipt`, `has_tables`, `record_citation_signals`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/local_embeddings/fusion|learnloop.local_embeddings.fusion]] — imports `module`, `refit_posteriors`; calls `explore`, `feature_row`, `rng_seed`
- [[Reference/Modules/learnloop/source_retrieval/recipes|learnloop.source_retrieval.recipes]] — imports `block_record_id`; calls `block_record_id`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `datetime`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]], [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]], [[Reference/Modules/learnloop/source_retrieval/library|learnloop.source_retrieval.library]], [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_section_coverage_review.py](../../../../../../tests/test_section_coverage_review.py) — direct import
  - `test_f7_the_search_fallback_embeds_and_logs_nothing`
- [tests/test_source_space_resolver.py](../../../../../../tests/test_source_space_resolver.py) — direct import
  - `test_a_challenger_learns_its_way_up_from_resolver_receipts`
  - `test_exploration_is_its_own_switch_and_logs_its_delivered_propensities`
  - `test_ordinary_use_completes_the_loop_opens_ask_citations_and_the_background_refit`
  - `test_signals_join_their_delivery_and_the_posterior_replays_byte_identically`
  - `test_the_fallback_serves_a_source_qwen_does_not_cover`
  - `test_the_logged_selection_probability_is_the_resolvers_joint_one`
  - `test_the_tutor_citation_hook_does_nothing_with_the_switches_off_and_joins_its_delivery_when_on`

## Modification guidance

- Make changes here when the responsibility remains feedback within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/feedback.py](../../../../../../src/learnloop/source_retrieval/feedback.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
