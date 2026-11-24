---
title: "learnloop.source_retrieval.jobs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/jobs.py"
source_paths:
  - "src/learnloop/source_retrieval/jobs.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.source_retrieval"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.source_retrieval.jobs module"
  - "src/learnloop/source_retrieval/jobs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.jobs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.jobs` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: Retrieval's derived-index job types: the source embedding backfill, the local index, the fallback backfill and the coverage pass after an extraction, and the obligations a completed extraction queues for them.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/jobs.py](../../../../../../src/learnloop/source_retrieval/jobs.py) |
| Source lines | 321 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `queue_source_vectors(ctx: JobContext, extraction_id: str, *, title: str | None=None) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/jobs.py), line 20) — Queue the source-block embedding backfill a completed extraction owes.
- `queue_coverage_on_extract(ctx: JobContext, config: Any, extraction_id: str) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/jobs.py), line 69) — Deliverable curriculum C0b (spec §6.3): a completed extraction queues one ``curriculum_coverage_on_extract`` job, which judges the already-covered LOs again so the new reading's sections join their coverage (quiet: the plan only).
- `queue_contextual_indexes(ctx: JobContext, config: Any, extraction_id: str, *, title: str | None=None) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/jobs.py), line 101) — Local contextual retrieval P1a/P1b (spec §4.1, §8): a completed extraction queues the local index job and the Voyage fallback backfill.
- `handle_local_source_index(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/jobs.py), line 161) — local_source_index: index every owed window in one 9B worker batch.
- `handle_source_fallback_backfill(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/jobs.py), line 187) — source_fallback_backfill: the Voyage fallback space's windows for one source (capped, receipted; an aggregate report, never block text).
- `handle_curriculum_coverage_on_extract(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/jobs.py), line 225) — curriculum_coverage_on_extract: judge the covered LOs again after an extraction (C0b, §6.3).
- `handle_source_embedding_backfill(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/jobs.py), line 242) — source_embedding_backfill: embed a source's current extraction's blocks.

### Module constants

- `_LOCAL_INDEX_DONE` ([src/learnloop/source_retrieval/jobs.py](../../../../../../src/learnloop/source_retrieval/jobs.py), line 157)
- `_SOURCE_VECTORS_DONE` ([src/learnloop/source_retrieval/jobs.py](../../../../../../src/learnloop/source_retrieval/jobs.py), line 222)

## Internal implementation anchors

- `_source_vectors_failure(status: str, report: Mapping[str, Any]) -> IngestRunnerError` ([source](../../../../../../src/learnloop/source_retrieval/jobs.py), line 287) — The workflow failure for an unsuccessful source backfill (Codex review F4).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/import_jobs|learnloop.content.pipeline.import_jobs]] — imports `queue_source_vectors`; statically calls `queue_source_vectors`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]] — imports `load_config`; calls `load_config`
- [[Reference/Modules/learnloop/content/pipeline/job_contracts|learnloop.content.pipeline.job_contracts]] — imports `IngestRunnerError`, `JobCancelled`, `JobSpec`; calls `IngestRunnerError`, `JobCancelled`, `JobSpec`
- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `JobContext`
- [[Reference/Modules/learnloop/source_retrieval/dense|learnloop.source_retrieval.dense]] — imports `clear_cache`; calls `clear_cache`
- [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]] — imports `FALLBACK_JOB`, `backfill_fallback_vectors`, `fallback_reason`; calls `backfill_fallback_vectors`, `fallback_reason`
- [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]] — imports `INDEX_JOB`, `run_local_index`; calls `run_local_index`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `ON_EXTRACT_JOB`, `covered_learning_objects`, `module`, `on_extract_reason`; calls `covered_learning_objects`, `on_extract_reason`, `rejudge_on_extract`
- [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]] — imports `LIVE_JOB_STATUSES`, `SOURCE_VECTORS_JOB`, `auto_backfill_reason`, `backfill_owed`, `backfill_source_vectors`, `target_extraction`; calls `auto_backfill_reason`, `backfill_owed`, `backfill_source_vectors`, `target_extraction`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`

### Platform and third-party dependencies

- Standard library: `__future__`, `logging`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/import_jobs|learnloop.content.pipeline.import_jobs]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_coverage_on_extract.py](../../../../../../tests/test_coverage_on_extract.py) — direct import
  - `test_an_extraction_queues_the_job_only_while_both_switches_are_on`
  - `test_one_live_job_at_a_time`
  - `test_the_handler_is_registered_and_known`
- [tests/test_deliverable_codex_review.py](../../../../../../tests/test_deliverable_codex_review.py) — direct import
  - `test_f7_a_running_job_does_not_swallow_a_new_extraction`
- [tests/test_job_types.py](../../../../../../tests/test_job_types.py) — direct import
  - `test_the_job_contracts_are_one_set_of_objects_through_every_path`
- [tests/test_local_index.py](../../../../../../tests/test_local_index.py) — direct import
  - `test_an_index_obligation_that_cannot_be_queued_fails_the_extraction_retryably`
  - `test_extraction_queues_the_index_jobs_only_while_their_switches_are_on`

## Modification guidance

- Make changes here when the responsibility remains jobs within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/jobs.py](../../../../../../src/learnloop/source_retrieval/jobs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
