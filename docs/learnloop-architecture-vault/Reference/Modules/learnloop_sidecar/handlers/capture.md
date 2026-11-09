---
title: "learnloop_sidecar.handlers.capture"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/capture.py"
source_paths:
  - "src/learnloop_sidecar/handlers/capture.py"
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
  - "learnloop_sidecar.handlers.capture module"
  - "src/learnloop_sidecar/handlers/capture.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.capture`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.capture` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Desktop-only inbox operations; no mobile entrypoint dependencies.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/capture.py](../../../../../../src/learnloop_sidecar/handlers/capture.py) |
| Source lines | 182 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `class ListCaptureInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/capture.py), line 20)
- `class CaptureInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/capture.py), line 26)
- `capture_call(fn, *args, **kwargs)` ([source](../../../../../../src/learnloop_sidecar/handlers/capture.py), line 30)
- `record_route(repository, capture_id: str | None, route: str, result_refs: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/capture.py), line 37) — Call only after the destination's durable operation succeeds.
- `destination_committed(ctx, repository, route: str | None, destination_id: str) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/capture.py), line 49) — Whether an intent's destination exists.
- `route_intent(repository, params, route: str, *, create=True, ctx=None) -> dict | None` ([source](../../../../../../src/learnloop_sidecar/handlers/capture.py), line 67) — Read or begin this request's intent.
- `finish_route(ctx, repository, capture_id, route, refs, response, *, reload=False)` ([source](../../../../../../src/learnloop_sidecar/handlers/capture.py), line 99) — A failed projection/refresh cannot turn a committed destination into failure.
- `get_inbox_summary(ctx: SidecarContext, _params: ParamsModel) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/capture.py), line 124)
- `list_capture_inbox(ctx: SidecarContext, params: ListCaptureInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/capture.py), line 132)
- `dismiss_capture(ctx: SidecarContext, params: CaptureInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/capture.py), line 139)
- `get_capture_media(ctx: SidecarContext, params: CaptureInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/capture.py), line 145) — Bounded photo preview for manual routing; resolved from the stored hash only.
- `resume_capture_route(ctx: SidecarContext, params: CaptureInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/capture.py), line 153) — Finish a capture's unfinished save from its persisted request.
- `purge_capture(ctx: SidecarContext, params: CaptureInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/capture.py), line 180)

## Internal implementation anchors

- `_request_hash(params) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/capture.py), line 43)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `capture_call`, `finish_route`, `route_intent`; statically calls `capture_call`, `finish_route`, `route_intent`
- [[Reference/Modules/learnloop_sidecar/handlers/item_authoring|learnloop_sidecar.handlers.item_authoring]] — imports `finish_route`, `route_intent`; statically calls `finish_route`, `route_intent`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `capture_call`, `finish_route`, `route_intent`; statically calls `capture_call`, `finish_route`, `route_intent`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]] — imports `module`; calls `pinned_vault_info`
- [[Reference/Modules/learnloop/capture/routing|learnloop.capture.routing]] — imports `begin_route`, `pending_route`, `read_route_intent`, `update_route_intent`
- [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]] — imports `global_settings_path`; calls `global_settings_path`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/item_authoring|learnloop_sidecar.handlers.item_authoring]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `json`, `logging`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]], [[Reference/Modules/learnloop_sidecar/handlers/item_authoring|learnloop_sidecar.handlers.item_authoring]], [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_capture_desktop.py](../../../../../../tests/test_capture_desktop.py) — direct import
  - `test_card_route_after_success_only`
  - `test_desktop_photo_preview_rpc_reads_only_the_capture_original`
  - `test_image_capture_kind_matches_desktop_dto`
  - `test_summary_listing_banner_dismiss_purge_and_cli`
- [tests/test_capture_route_recovery.py](../../../../../../tests/test_capture_route_recovery.py) — direct import
  - `test_destination_retry_recovers_one_result`
  - `test_incomplete_tutor_event_is_not_duplicated`
  - `test_purge_erases_the_persisted_request`
  - `test_resume_finishes_an_unfinished_route_without_any_inputs`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/capture.py](../../../../../../src/learnloop_sidecar/handlers/capture.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
