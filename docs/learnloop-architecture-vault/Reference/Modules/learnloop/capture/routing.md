---
title: "learnloop.capture.routing"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/capture/routing.py"
source_paths:
  - "src/learnloop/capture/routing.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.capture"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
aliases:
  - "learnloop.capture.routing module"
  - "src/learnloop/capture/routing.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-capture"
---

# `learnloop.capture.routing`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/capture/_package|learnloop.capture]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.capture.routing` exists within [[Reference/Modules/learnloop/capture/_package|learnloop.capture]] to own the behavior summarized by its module contract: Durable desktop route intents, separate from destination commits.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/capture/routing.py](../../../../../../src/learnloop/capture/routing.py) |
| Source lines | 103 |
| Owning package | [[Reference/Modules/learnloop/capture/_package|learnloop.capture]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `read_route_intent(repo, capture_id: str, *, route: str, request_hash: str) -> dict | None` ([source](../../../../../../src/learnloop/capture/routing.py), line 25)
- `pending_route(repo, capture_id: str) -> dict | None` ([source](../../../../../../src/learnloop/capture/routing.py), line 44) — The unfinished intent of a still-new capture: route, request, destination.
- `begin_route(repo, capture_id: str, *, route: str, request_hash: str, request: dict | None=None, supersede: str | None=None) -> dict` ([source](../../../../../../src/learnloop/capture/routing.py), line 59) — Create (or return the identical) intent.
- `update_route_intent(repo, capture_id: str, **values) -> dict` ([source](../../../../../../src/learnloop/capture/routing.py), line 89)

### Module constants

- `_CONFLICT` ([src/learnloop/capture/routing.py](../../../../../../src/learnloop/capture/routing.py), line 21)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/capture|learnloop_sidecar.handlers.capture]] — imports `begin_route`, `pending_route`, `read_route_intent`, `update_route_intent`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `update_route_intent`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/capture/errors|learnloop.capture.errors]] — imports `CaptureError`; calls `CaptureError`
- [[Reference/Modules/learnloop/capture/inbox|learnloop.capture.inbox]] — imports `get_capture`; calls `get_capture`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/capture|learnloop_sidecar.handlers.capture]], [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_capture_desktop.py](../../../../../../tests/test_capture_desktop.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/capture|learnloop_sidecar.handlers.capture]]
- [tests/test_capture_route_recovery.py](../../../../../../tests/test_capture_route_recovery.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/capture|learnloop_sidecar.handlers.capture]]
- [tests/test_build_study_map_routing.py](../../../../../../tests/test_build_study_map_routing.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]]
- [tests/test_collection_append_units.py](../../../../../../tests/test_collection_append_units.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]]
- [tests/test_exam_protection_identity.py](../../../../../../tests/test_exam_protection_identity.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]]
- [tests/test_ingest_jobs.py](../../../../../../tests/test_ingest_jobs.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]]
- [tests/test_ingest_latency_journey.py](../../../../../../tests/test_ingest_latency_journey.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]]
- [tests/test_ingest_runner.py](../../../../../../tests/test_ingest_runner.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]]
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]]
- [tests/test_sidecar_quick_add.py](../../../../../../tests/test_sidecar_quick_add.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]]

## Modification guidance

- Make changes here when the responsibility remains routing within learnloop.capture; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/capture/routing.py](../../../../../../src/learnloop/capture/routing.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
