---
title: "learnloop.db.stores.practice_index"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/practice_index.py"
source_paths:
  - "src/learnloop/db/stores/practice_index.py"
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
  - "learnloop.db.stores.practice_index module"
  - "src/learnloop/db/stores/practice_index.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.practice_index`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.practice_index` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: SQL for the practice index (Slice 2 §5.9): paid outputs and receipts only.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/practice_index.py](../../../../../../../src/learnloop/db/stores/practice_index.py) |
| Source lines | 381 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `table_exists(connection: sqlite3.Connection, name: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/practice_index.py), line 15)
- `class DossierRow` ([source](../../../../../../../src/learnloop/db/stores/practice_index.py), line 25)
  - `field(self, name: str) -> str` (line 38; public)
- `dossier_exists(connection: sqlite3.Connection, *, facet_id: str, facet_content_hash: str, source_hash: str, model_id: str, prompt_version: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/practice_index.py), line 49)
- `insert_dossier(connection: sqlite3.Connection, *, id: str, facet_id: str, facet_content_hash: str, source_hash: str, model_id: str, prompt_version: str, scope: str, moves: str, errors: str, contrast: str, draft: Mapping[str, Any], grounding: Mapping[str, Any], input_hash: str, provider: str | None, billing: str, run_id: str, created_at: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/practice_index.py), line 60) — Insert once per key, preserving the first paid result.
- `dossier_candidates(connection: sqlite3.Connection, facet_hashes: Mapping[str, str]) -> dict[str, list[DossierRow]]` ([source](../../../../../../../src/learnloop/db/stores/practice_index.py), line 80) — Every dossier written for each facet's CURRENT content, oldest first.
- `dossier_count(connection: sqlite3.Connection) -> int` ([source](../../../../../../../src/learnloop/db/stores/practice_index.py), line 101)
- `insert_proposal(connection: sqlite3.Connection, *, id: str, created_at: str, origin: str, query_id: str, query_text: str, constraints: Mapping[str, Any], path: str, path_reason: str, signals: Mapping[str, Any], reranked: bool, rerank_status: str, rerank_model: str | None, proposed: list[Mapping[str, Any]], exclusions: Mapping[str, Any], manifest: Mapping[str, Any], algorithm_version: str, caller: str | None=None, caller_ref: str | None=None, intent: str | None=None, valuation: Mapping[str, Any] | None=None, provisional: Mapping[str, Any] | None=None) -> None` ([source](../../../../../../../src/learnloop/db/stores/practice_index.py), line 110) — One receipt per call.
- `proposal(connection: sqlite3.Connection, proposal_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/practice_index.py), line 164)
- `proposals(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/practice_index.py), line 173)
- `eval_queries(connection: sqlite3.Connection, prompt_versions: Collection[str]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/practice_index.py), line 184)
- `insert_eval_query(connection: sqlite3.Connection, *, id: str, query_text: str, seed_kind: str, seed_id: str, model_id: str | None, prompt_version: str, input_hash: str, run_id: str | None, created_at: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/practice_index.py), line 196)
- `insert_evaluation(connection: sqlite3.Connection, *, id: str, created_at: str, winner: str, reason: str, manifest_hash: str, manifest: Mapping[str, Any], metrics: Mapping[str, Any], run_id: str) -> None` ([source](../../../../../../../src/learnloop/db/stores/practice_index.py), line 210)
- `latest_evaluation(connection: sqlite3.Connection, manifest_hash: str | None=None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/practice_index.py), line 222) — The newest evaluation, optionally only one made on this manifest.
- `checkpointed_keys(connection: sqlite3.Connection, keys: Collection[str]) -> set[str]` ([source](../../../../../../../src/learnloop/db/stores/practice_index.py), line 243) — Which of these request identities already have a checkpointed answer.
- `checkpoints_for_purpose(connection: sqlite3.Connection, *, prefix: str, purpose: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/practice_index.py), line 258) — Checkpointed answers of one paid role, oldest first (crash recovery).
- `completed_root_receipts(connection: sqlite3.Connection, *, purpose: str, prompt_hash: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/practice_index.py), line 270) — Completed root receipts of one paid role that kept their answer, newest first.
- `judgments_by_ids(connection: sqlite3.Connection, ids: Collection[str]) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/practice_index.py), line 308)
- `judgments_for_task(connection: sqlite3.Connection, task: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/practice_index.py), line 324)
- `attempts_after(connection: sqlite3.Connection, *, practice_item_ids: Collection[str], since: str, until: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/practice_index.py), line 332) — Attempts on these items in [since, until], oldest first (usage join).
- `items_revealed_between(connection: sqlite3.Connection, *, since: str, until: str, exclude_ids: Iterable[str] | None=None) -> set[str]` ([source](../../../../../../../src/learnloop/db/stores/practice_index.py), line 346) — Items whose answer the reveal ledger recorded in (since, until]; a routine full-answer display by its coverage instead: from the renewal grace before ``since``, and also when stamped after ``until`` (the clock went back), ``learnloop.reveal_coverage`` (UX Phase 4 round 4).
- `stored_vector_hashes(connection: sqlite3.Connection, *, record_kind: str, field: str, model_id: str, task_prefix: str) -> dict[str, set[str]]` ([source](../../../../../../../src/learnloop/db/stores/practice_index.py), line 369) — Content hashes stored per record for one recipe view (completeness checks).

### Module constants

- `_DOSSIER_COLUMNS` ([src/learnloop/db/stores/practice_index.py](../../../../../../../src/learnloop/db/stores/practice_index.py), line 43)

## Internal implementation anchors

- `_proposal(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/practice_index.py), line 151)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/practice_index|learnloop.cli.practice_index]] — imports `latest_evaluation`; statically calls `latest_evaluation`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `judgments_by_ids`; statically calls `judgments_by_ids`
- [[Reference/Modules/learnloop/instructional/interventions|learnloop.instructional.interventions]] — imports `proposal`; statically calls `proposal`
- [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]] — imports `judgments_by_ids`, `proposal`; statically calls `judgments_by_ids`, `proposal`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `judgments_by_ids`; statically calls `judgments_by_ids`
- [[Reference/Modules/learnloop/instructional/screen|learnloop.instructional.screen]] — imports `judgments_by_ids`; statically calls `judgments_by_ids`
- [[Reference/Modules/learnloop/practice_index/dossiers|learnloop.practice_index.dossiers]] — imports `DossierRow`, `checkpointed_keys`, `dossier_candidates`, `dossier_exists`, `insert_dossier`; statically calls `checkpointed_keys`, `dossier_candidates`, `dossier_exists`, `insert_dossier`
- [[Reference/Modules/learnloop/practice_index/evaluation|learnloop.practice_index.evaluation]] — imports `checkpointed_keys`, `checkpoints_for_purpose`, `eval_queries`, `insert_eval_query`, `insert_evaluation`, `judgments_by_ids`, `proposals`; statically calls `checkpointed_keys`, `checkpoints_for_purpose`, `eval_queries`, `insert_eval_query`, `insert_evaluation`, `judgments_by_ids`, `proposals`
- [[Reference/Modules/learnloop/practice_index/listwise|learnloop.practice_index.listwise]] — imports `judgments_by_ids`; statically calls `judgments_by_ids`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `completed_root_receipts`; statically calls `completed_root_receipts`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `DossierRow`, `checkpointed_keys`, `insert_proposal`, `judgments_by_ids`, `latest_evaluation`, `stored_vector_hashes`; statically calls `checkpointed_keys`, `insert_proposal`, `judgments_by_ids`, `latest_evaluation`, `stored_vector_hashes`
- [[Reference/Modules/learnloop/practice_index/usage|learnloop.practice_index.usage]] — imports `attempts_after`, `judgments_by_ids`, `judgments_for_task`, `proposal`, `proposals`; statically calls `attempts_after`, `judgments_by_ids`, `judgments_for_task`, `proposal`, `proposals`
- [[Reference/Modules/learnloop/scheduling/serving_exclusions|learnloop.scheduling.serving_exclusions]] — imports `items_revealed_between`; statically calls `items_revealed_between`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `judgments_by_ids`; statically calls `judgments_by_ids`
- [[Reference/Modules/learnloop/vault/embedding_recipes|learnloop.vault.embedding_recipes]] — imports `dossier_candidates`; statically calls `dossier_candidates`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `judgments_by_ids`; statically calls `judgments_by_ids`
- [[Reference/Modules/learnloop_sidecar/handlers/library_exercises|learnloop_sidecar.handlers.library_exercises]] — imports `proposal`; statically calls `proposal`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/reveal_coverage|learnloop.reveal_coverage]] — imports `routine_coverage_sql`, `routine_window_start`; calls `routine_coverage_sql`, `routine_window_start`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/practice_index|learnloop.cli.practice_index]], [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]], [[Reference/Modules/learnloop/instructional/interventions|learnloop.instructional.interventions]], [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]], [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] and 12 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/learner_pick_proposal_helpers.py](../../../../../../../tests/learner_pick_proposal_helpers.py) — direct import
- [tests/test_discriminating_search.py](../../../../../../../tests/test_discriminating_search.py) — direct import
  - `test_a_pick_with_an_unjudged_worked_example_is_served_as_labelled_practice`
- [tests/test_learner_pick_proposal.py](../../../../../../../tests/test_learner_pick_proposal.py) — direct import
- [tests/test_practice_index_dossiers.py](../../../../../../../tests/test_practice_index_dossiers.py) — direct import
  - `test_select_dossier_prefers_current_sources_then_the_intended_model`
- [tests/test_practice_index_evaluation.py](../../../../../../../tests/test_practice_index_evaluation.py) — direct import
  - `test_duplicate_queries_cannot_manufacture_a_winning_evaluation`
- [tests/test_practice_index_find.py](../../../../../../../tests/test_practice_index_find.py) — direct import
- [tests/test_router_r2a_serving.py](../../../../../../../tests/test_router_r2a_serving.py) — direct import
  - `test_an_unplanned_proposal_pick_delivers_with_its_blocks_decision`
- [tests/test_source_exercise_rpcs.py](../../../../../../../tests/test_source_exercise_rpcs.py) — direct import
- [tests/test_valuation_calibration_fields.py](../../../../../../../tests/test_valuation_calibration_fields.py) — direct import
  - `test_a_studied_worked_example_records_the_seconds_since_exposure`
  - `test_exposure_age_is_measured_at_delivery_not_at_valuation`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/practice_index.py](../../../../../../../src/learnloop/db/stores/practice_index.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
