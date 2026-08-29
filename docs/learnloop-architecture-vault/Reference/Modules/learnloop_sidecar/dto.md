---
title: "learnloop_sidecar.dto"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/dto.py"
source_paths:
  - "src/learnloop_sidecar/dto.py"
source_commit: "4a28c9635f24945d78366fa26212db7488d82545"
source_commit_timestamp: "2026-05-28T11:36:12-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-08-18"
package: "learnloop_sidecar"
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
  - "learnloop_sidecar.dto module"
  - "src/learnloop_sidecar/dto.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar"
---

# `learnloop_sidecar.dto`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps dto behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]]. Its public surface centers on `camel_name`, `ParamsModel`, `EmptyParams`, `to_camel`, `versioned`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/dto.py](../../../../../src/learnloop_sidecar/dto.py) |
| Source lines | 43 |
| Owning package | [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `4a28c9635f24945d78366fa26212db7488d82545` |
| Commit timestamp | `2026-05-28T11:36:12-04:00` |

## Public API

- `camel_name(name: str) -> str` ([source](../../../../../src/learnloop_sidecar/dto.py), line 9)
- `class ParamsModel(BaseModel)` ([source](../../../../../src/learnloop_sidecar/dto.py), line 14)
- `class EmptyParams(ParamsModel)` ([source](../../../../../src/learnloop_sidecar/dto.py), line 22)
- `to_camel(value: Any) -> Any` ([source](../../../../../src/learnloop_sidecar/dto.py), line 26)
- `versioned(payload: Mapping[str, Any] | None=None, *, version: int=1) -> dict[str, Any]` ([source](../../../../../src/learnloop_sidecar/dto.py), line 38)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `to_camel`, `versioned`; statically calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/adjudication|learnloop_sidecar.handlers.adjudication]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/animation|learnloop_sidecar.handlers.animation]] — imports `EmptyParams`, `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/app|learnloop_sidecar.handlers.app]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/calibration|learnloop_sidecar.handlers.calibration]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/claims|learnloop_sidecar.handlers.claims]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/cli|learnloop_sidecar.handlers.cli]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/diagnostic|learnloop_sidecar.handlers.diagnostic]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]] — imports `EmptyParams`, `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/facet_detail|learnloop_sidecar.handlers.facet_detail]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/facets|learnloop_sidecar.handlers.facets]] — imports `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `ParamsModel`, `to_camel`, `versioned`; statically calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `EmptyParams`, `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/golden_path|learnloop_sidecar.handlers.golden_path]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/golden_path_assessment|learnloop_sidecar.handlers.golden_path_assessment]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/graph|learnloop_sidecar.handlers.graph]] — imports `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/graph_edit|learnloop_sidecar.handlers.graph_edit]] — imports `ParamsModel`, `to_camel`, `versioned`; statically calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `ParamsModel`, `camel_name`, `versioned`; statically calls `camel_name`, `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/inspector|learnloop_sidecar.handlers.inspector]] — imports `ParamsModel`, `to_camel`, `versioned`; statically calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/item_authoring|learnloop_sidecar.handlers.item_authoring]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_model|learnloop_sidecar.handlers.knowledge_model]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/ladder|learnloop_sidecar.handlers.ladder]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/library|learnloop_sidecar.handlers.library]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `EmptyParams`, `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `ParamsModel`, `to_camel`, `versioned`; statically calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/proposals|learnloop_sidecar.handlers.proposals]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/provenance|learnloop_sidecar.handlers.provenance]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/registry|learnloop_sidecar.handlers.registry]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/remediation|learnloop_sidecar.handlers.remediation]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/review|learnloop_sidecar.handlers.review]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `to_camel`, `versioned`; statically calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]] — imports `EmptyParams`, `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/sqlite_admin|learnloop_sidecar.handlers.sqlite_admin]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/vault|learnloop_sidecar.handlers.vault]] — imports `EmptyParams`, `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `EmptyParams`, `ParamsModel`

### Repository tooling consumers

- [scripts/gen_goldenpath_fixtures.py](../../../../../scripts/gen_goldenpath_fixtures.py); calls `to_camel`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]], [[Reference/Modules/learnloop_sidecar/handlers/adjudication|learnloop_sidecar.handlers.adjudication]], [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]], [[Reference/Modules/learnloop_sidecar/handlers/animation|learnloop_sidecar.handlers.animation]], [[Reference/Modules/learnloop_sidecar/handlers/app|learnloop_sidecar.handlers.app]] and 37 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ingest_latency_journey.py](../../../../../tests/test_ingest_latency_journey.py) — direct import
  - `test_synthetic_markdown_import_reaches_ready_library_and_outline`
- [tests/test_sidecar_item_presentation.py](../../../../../tests/test_sidecar_item_presentation.py) — direct import
- [tests/test_sidecar_serializer_snapshot.py](../../../../../tests/test_sidecar_serializer_snapshot.py) — direct import
  - `test_queue_practice_and_reader_wire_snapshots`
- [tests/test_sidecar_transport.py](../../../../../tests/test_sidecar_transport.py) — direct import
  - `test_duplicate_method_registration_fails_loudly`
  - `test_unexpected_handler_failure_marks_the_commit_outcome_unknown`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/dto.py](../../../../../src/learnloop_sidecar/dto.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
