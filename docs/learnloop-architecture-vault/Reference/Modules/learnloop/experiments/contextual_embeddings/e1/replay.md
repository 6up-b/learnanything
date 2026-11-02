---
title: "learnloop.experiments.contextual_embeddings.e1.replay"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/e1/replay.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/e1/replay.py"
source_commit: "4cca60c985c6f3fe497bb7be9a5ba6ae56be75e3"
source_commit_timestamp: "2026-10-23T22:55:30-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.experiments.contextual_embeddings.e1"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.experiments.contextual_embeddings.e1.replay module"
  - "src/learnloop/experiments/contextual_embeddings/e1/replay.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings-e1"
---

# `learnloop.experiments.contextual_embeddings.e1.replay`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.e1.replay` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] to own the behavior summarized by its module contract: E1 consumes E0 by path: import (copies), replay (no call) and verification.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/e1/replay.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py) |
| Source lines | 513 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `4cca60c985c6f3fe497bb7be9a5ba6ae56be75e3` |
| Commit timestamp | `2026-10-23T22:55:30-04:00` |

## Public API

- `class ReplayMiss(RuntimeError)` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py), line 65) — A result E0 never recorded: replay cannot stand in for a call.
- `class ImportRefused(ValueError)` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py), line 69) — E0's run is not finished, or its outputs are not where they should be.
- `class ImportLayout` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py), line 84) — Where an import keeps each part (all under E1's fixtures-local).
  - `manifest_path(self) -> Path` (line 90; public)
  - `manifest(self) -> dict[str, Any]` (line 93; public)
  - `frozen(self) -> Path` (line 97; public)
  - `plan(self) -> dict[str, Any]` (line 100; public)
  - `vault(self, label: str) -> Path` (line 103; public)
  - `store(self, label: str) -> Path` (line 106; public)
  - `results(self, label: str) -> dict[str, Any]` (line 109; public)
  - `pools(self, label: str) -> dict[str, list[str]]` (line 112; public)
  - `labels(self) -> list[str]` (line 116; public)
- `e0_run_state(e0_run_dir: Path) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py), line 120) — What an E0 run directory holds, read-only: its frozen plan, each copy's results (or their absence) and where its stores live.
- `import_e0(e0_run_dir: Path, vaults_dir: Path, destination: Path) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py), line 142) — Copy a FINISHED E0 run's outputs into E1's fixtures-local (see the module docstring).
- `label_pools_from_records(records: Path, work: Path) -> dict[str, list[str]]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py), line 189) — ``{query_id: [unit ids]}``: every unit a label pass of THIS rubric version judged, from a backup copy of E0's experiment records.
- `verify_import(layout: ImportLayout) -> list[str]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py), line 206) — Each imported part still hashes to its manifest digest.
- `class ReplayRoleCaller(LiveRoleCaller)` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py), line 226) — E0's role calls answered from E0's checkpoints only (never sent).
  - `__init__(self, handle: CopyHandle, checkpoints: Checkpoints, scratch: Path) -> None` (line 229; internal)
  - `call(self, role: str, *, prompt: str, result_model: Any, arm: str | None=None) -> Any` (line 236; public)
- `class QwenReplayClient` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py), line 262) — The production OpenRouter embedding client's IDENTITY (the Qwen adapter's space ids hash it), without a key and without ``embed``.
  - `__init__(self, config: Any) -> None` (line 268; internal)
  - `embed(self, *_args: Any, **_kwargs: Any) -> Any` (line 279; public)
- `class RefusingTransport` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py), line 283)
  - `post(self, *_args: Any, **_kwargs: Any) -> Any` (line 284; public)
- `zero_ledger(scratch: Path) -> E0Ledger` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py), line 288) — A ledger that admits nothing: any request is refused before it is sent.
- `class Replayed` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py), line 297)
  - `all_questions(self) -> list[BankQuestion]` (line 311; public)
- `replay_labels(snapshot: CorpusSnapshot, questions: Sequence[BankQuestion], pools: Mapping[str, Sequence[str]], caller: Any, gaps: dict[str, Any]) -> dict[str, QuestionLabels]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py), line 315) — E0's ``paid.label_all`` with E0's own pools, from checkpoints: a stop or a question failure ends or skips exactly as it did in E0.
- `representation_rankings(snapshot: CorpusSnapshot, questions: Sequence[BankQuestion], headers: Mapping[str, str], *, store: Any, config: Any, scratch: Path, gaps: dict[str, Any], arms: Sequence[str]=e1_pins.E0_REPRESENTATION_ARMS, adapters: dict[str, Any] | None=None) -> dict[str, dict[str, list[str]]]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py), line 364) — Every E0 representation arm ranked from E0's stored vectors only.
- `replay_copy(layout: ImportLayout, label: str, *, scratch: Path, store: Any=None) -> Replayed` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py), line 392) — One copy's E0 run, replayed (see the module docstring).
- `e0_strata(plan: Mapping[str, Any], label: str) -> dict[str, int]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py), line 426) — A copy's frozen development strata IN E0's ORDER.
- `rebuild_copy(layout: ImportLayout, label: str) -> tuple[CopyHandle, CorpusSnapshot, dict[str, int]]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py), line 442) — One imported copy rebuilt under E0's frozen plan: E0's pins, its reserve share and strata, and its family splits must all hold (the run-wide run id is checked over every copy by :func:`run_identity`).
- `run_identity(layout: ImportLayout) -> str` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py), line 463) — E0's run id rebuilt over every imported copy (must equal E0's plan).
- `verify_replay(replayed: Replayed) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py), line 476) — The replay must reproduce E0's published slices for every representation arm it ranked, and E0's label κ.
- `question_texts(replayed: Replayed) -> dict[str, str]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py), line 510)

### Module constants

- `IMPORT_MANIFEST` ([src/learnloop/experiments/contextual_embeddings/e1/replay.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py), line 57)
- `_SKIPPED_SUFFIXES` ([src/learnloop/experiments/contextual_embeddings/e1/replay.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py), line 59)
- `VERIFIED_SLICES` ([src/learnloop/experiments/contextual_embeddings/e1/replay.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py), line 61)
- `VERIFIED_TOLERANCE` ([src/learnloop/experiments/contextual_embeddings/e1/replay.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py), line 62)

## Internal implementation anchors

- `_sha(value: Any) -> str` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py), line 73)
- `_ignore(_directory: str, names: list[str]) -> set[str]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py), line 77)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/experiments|learnloop.cli.experiments]] — imports `ImportLayout`, `import_e0`; statically calls `ImportLayout`, `import_e0`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/plan|learnloop.experiments.contextual_embeddings.e1.plan]] — imports `e0_run_state`, `question_texts`; statically calls `e0_run_state`, `question_texts`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]] — imports `ImportLayout`, `Replayed`, `question_texts`, `replay_copy`, `run_identity`, `verify_import`, `verify_replay`; statically calls `ImportLayout`, `question_texts`, `replay_copy`, `run_identity`, `verify_import`, `verify_replay`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/providers/openai_embedding|learnloop.ai.providers.openai_embedding]] — imports `DEFAULT_BASE_URL`, `DEFAULT_MODEL`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `DEFAULT_EMBEDDING_PROVIDER`
- [[Reference/Modules/learnloop/db/copies|learnloop.db.copies]] — imports `copy_tree_with_databases`; calls `copy_tree_with_databases`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/adapters|learnloop.experiments.contextual_embeddings.adapters]] — imports `AdapterError`, `Receipts`, `VectorStore`; calls `Receipts`, `VectorStore`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/bank|learnloop.experiments.contextual_embeddings.bank]] — imports `BankQuestion`, `LABEL_VERSION`, `QuestionLabels`, `accept_agreed`, `adjudicate`, `audit_plan`, `evidence_sets_from_labels`, `freeze_context`, `label_question`, `logged_questions`, `plan_seeds`, `smoke_bank`, `write_questions`; calls `accept_agreed`, `adjudicate`, `audit_plan`, `evidence_sets_from_labels`, `freeze_context`, `label_question`, `logged_questions`, `plan_seeds`, `smoke_bank`, `write_questions`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/budget|learnloop.experiments.contextual_embeddings.budget]] — imports `E0Ledger`, `E0ProviderFailure`, `E0Stop`; calls `E0Ledger`, `E0ProviderFailure`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/callers|learnloop.experiments.contextual_embeddings.callers]] — imports `Checkpoints`, `LiveRoleCaller`, `checkpoint_key`; calls `Checkpoints`, `checkpoint_key`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]] — imports `CopyHandle`, `CorpusSnapshot`, `_inside_local_root`, `build_snapshot`, `open_copy`, `to_rollback_journal`; calls `_inside_local_root`, `build_snapshot`, `open_copy`, `to_rollback_journal`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/pins|learnloop.experiments.contextual_embeddings.e1.pins]] — imports `module`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/evaluate|learnloop.experiments.contextual_embeddings.evaluate]] — imports `agreement`, `question_rows`; calls `agreement`, `question_rows`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]] — imports `PlanMismatch`; calls `PlanMismatch`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/paid|learnloop.experiments.contextual_embeddings.paid]] — imports `QUESTION_FAILURES`, `effective_query`, `make_adapter`, `rank_arm`, `slice_summaries`; calls `effective_query`, `make_adapter`, `rank_arm`, `slice_summaries`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/pins|learnloop.experiments.contextual_embeddings.pins]] — imports `module`; calls `pins_fingerprint`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/records|learnloop.experiments.contextual_embeddings.records]] — imports `ExperimentRecords`; calls `ExperimentRecords`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/retrieval|learnloop.experiments.contextual_embeddings.retrieval]] — imports `generate_contexts`; calls `generate_contexts`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/runner|learnloop.experiments.contextual_embeddings.runner]] — imports `plan_identity`, `tree_digest`; calls `plan_identity`, `tree_digest`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/experiments|learnloop.cli.experiments]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/plan|learnloop.experiments.contextual_embeddings.e1.plan]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e1_harness.py](../../../../../../../../tests/test_e1_harness.py) — direct import
  - `test_an_unfinished_e0_run_is_not_imported_and_the_manifest_plan_is_provisional`
  - `test_the_replay_caller_serves_checkpoints_reproduces_failures_and_never_sends`
  - `test_the_replay_restores_e0s_strata_order_from_the_sorted_json_plan`

## Modification guidance

- Make changes here when the responsibility remains replay within learnloop.experiments.contextual_embeddings.e1; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/e1/replay.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/replay.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
