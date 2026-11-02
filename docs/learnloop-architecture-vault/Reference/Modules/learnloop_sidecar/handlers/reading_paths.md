---
title: "learnloop_sidecar.handlers.reading_paths"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/reading_paths.py"
source_paths:
  - "src/learnloop_sidecar/handlers/reading_paths.py"
source_commit: "7088c9b6814e570e8596c034d6faeef36b423656"
source_commit_timestamp: "2026-10-27T01:55:57-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.handlers.reading_paths module"
  - "src/learnloop_sidecar/handlers/reading_paths.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.reading_paths`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.reading_paths` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Reader workbench RW7a RPCs: the Guide's reading path (spec_reader_workbench_v1 §10.1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/reading_paths.py](../../../../../../src/learnloop_sidecar/handlers/reading_paths.py) |
| Source lines | 268 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `7088c9b6814e570e8596c034d6faeef36b423656` |
| Commit timestamp | `2026-10-27T01:55:57-04:00` |

## Public API

- `prompt_contract_fields(vault: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reading_paths.py), line 44) — What the Reader's prompt contract adds for RW7a (absent while off).
- `class ReadingPathInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reading_paths.py), line 214)
- `reader_reading_path(ctx: SidecarContext, params: ReadingPathInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reading_paths.py), line 224) — The Guide's reading path for this reading (at once; a judgment runs in the background).
- `class ReadingPathDepthInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reading_paths.py), line 231)
- `reader_reading_path_set_depth(ctx: SidecarContext, params: ReadingPathDepthInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reading_paths.py), line 237) — "How deep do you want to go?" for the source; DL2's intent is not written.
- `class ReadingPathOverrideInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reading_paths.py), line 248)
- `reader_reading_path_override(ctx: SidecarContext, params: ReadingPathOverrideInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reading_paths.py), line 257) — "Read it anyway" / "skip it": kept, and marks nothing as known.

### Module constants

- `LOG` ([src/learnloop_sidecar/handlers/reading_paths.py](../../../../../../src/learnloop_sidecar/handlers/reading_paths.py), line 34)
- `READING_PATH_RPCS` ([src/learnloop_sidecar/handlers/reading_paths.py](../../../../../../src/learnloop_sidecar/handlers/reading_paths.py), line 37)

### Explicit exports

`__all__` declares:

- `READING_PATH_RPCS`
- `prompt_contract_fields`

## Internal implementation anchors

- `_require(ctx: SidecarContext, extraction_id: str) -> tuple[Any, Any, str]` ([source](../../../../../../src/learnloop_sidecar/handlers/reading_paths.py), line 53)
- `class _Judgments` ([source](../../../../../../src/learnloop_sidecar/handlers/reading_paths.py), line 74) — Judgments in flight or failed, by (reading, depth, state key), in memory.
- `_judgments(ctx: SidecarContext) -> _Judgments` ([source](../../../../../../src/learnloop_sidecar/handlers/reading_paths.py), line 85)
- `_start(ctx: SidecarContext, vault: Any, repository: Any, extraction_id: str, depth: str, state_key: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/reading_paths.py), line 93)
- `_readmit(ctx: SidecarContext, vault: Any, repository: Any, state_key: tuple[str, str, str], current: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reading_paths.py), line 152) — An admission refusal (capped, unpriced, unrouted, models off) holds only while its condition does (Codex review F4): each read asks again, before any call, against today's envelope and the vault's config now.
- `_view(ctx: SidecarContext, vault: Any, repository: Any, extraction_id: str, *, judge: bool, retry: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reading_paths.py), line 178)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `prompt_contract_fields`; statically calls `prompt_contract_fields`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `record_model_calls`; calls `record_model_calls`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `note_unit`, `relay_hint`, `unit`, `unit_origin`, `unit_stamp`, `unit_token`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `module`; calls `reader_enabled`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `module`; calls `admission_problem`, `enabled`, `judge`, `override`, `path_inputs`, `path_view`, `reading_of`, `set_depth`
- [[Reference/Modules/learnloop_sidecar/background_jobs|learnloop_sidecar.background_jobs]] — imports `background_jobs`; calls `background_jobs`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `_require_source_reader`, `_source_id_for_extraction`; calls `_require_source_reader`, `_source_id_for_extraction`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `logging`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_the_pinned_rw7a_rpcs_are_all_of_them`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/reading_paths.py](../../../../../../src/learnloop_sidecar/handlers/reading_paths.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
