---
title: "learnloop_sidecar.handlers.companion_ask"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/companion_ask.py"
source_paths:
  - "src/learnloop_sidecar/handlers/companion_ask.py"
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
  - "learnloop_sidecar.handlers.companion_ask module"
  - "src/learnloop_sidecar/handlers/companion_ask.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.companion_ask`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.companion_ask` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Reader workbench v2 RPCs: ``companion.ask``, ``companion.ask_job`` and ``companion.ask_cancel`` (spec §3.4, §8.6): the companion's question as a polled job.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/companion_ask.py](../../../../../../src/learnloop_sidecar/handlers/companion_ask.py) |
| Source lines | 190 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `class CompanionAskInput(ReaderAskInput)` ([source](../../../../../../src/learnloop_sidecar/handlers/companion_ask.py), line 61)
- `class CompanionAskJobInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/companion_ask.py), line 70)
- `companion_ask(ctx: SidecarContext, params: CompanionAskInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/companion_ask.py), line 126) — Ask the companion; answers at once with the job (see the module docstring).
- `companion_ask_job(ctx: SidecarContext, params: CompanionAskJobInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/companion_ask.py), line 161) — The job's state, at once (never a wait on the request path).
- `companion_ask_cancel(ctx: SidecarContext, params: CompanionAskJobInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/companion_ask.py), line 176) — Cancel the job: its next model request is refused; a finished job keeps its outcome.

### Module constants

- `LOG` ([src/learnloop_sidecar/handlers/companion_ask.py](../../../../../../src/learnloop_sidecar/handlers/companion_ask.py), line 51)
- `COMPANION_ASK_RPCS` ([src/learnloop_sidecar/handlers/companion_ask.py](../../../../../../src/learnloop_sidecar/handlers/companion_ask.py), line 54)
- `KIND` ([src/learnloop_sidecar/handlers/companion_ask.py](../../../../../../src/learnloop_sidecar/handlers/companion_ask.py), line 55)
- `_REGISTRY` ([src/learnloop_sidecar/handlers/companion_ask.py](../../../../../../src/learnloop_sidecar/handlers/companion_ask.py), line 56)
- `NOT_FOUND_MESSAGE` ([src/learnloop_sidecar/handlers/companion_ask.py](../../../../../../src/learnloop_sidecar/handlers/companion_ask.py), line 57)

### Explicit exports

`__all__` declares:

- `COMPANION_ASK_RPCS`
- `CompanionAskInput`

## Internal implementation anchors

- `_jobs(ctx: SidecarContext) -> PJ.PolledJobs` ([source](../../../../../../src/learnloop_sidecar/handlers/companion_ask.py), line 74)
- `_request_key(params: CompanionAskInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/companion_ask.py), line 78) — What a repeat of the request id must ask again to be the same request (compared in memory only).
- `_reader_params(params: CompanionAskInput) -> ReaderAskInput` ([source](../../../../../../src/learnloop_sidecar/handlers/companion_ask.py), line 84)
- `_payload(request_id: str, state: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/companion_ask.py), line 88)
- `_job_payload(job: PJ.PolledJob) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/companion_ask.py), line 110)
- `_receipt_payload(receipt: PJ.Receipt) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/companion_ask.py), line 119)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `relay_job_offer`
- [[Reference/Modules/learnloop/companion/asks|learnloop.companion.asks]] — imports `CompanionAskError`, `MAX_PAD_BLOCKS`, `ask_context`; calls `ask_context`
- [[Reference/Modules/learnloop/companion/history|learnloop.companion.history]] — imports `record_exchange_context`; calls `record_exchange_context`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `ReaderAskInput`, `generate_reader_answer`, `prepare_reader_ask`, `reader_ask_reply`; calls `generate_reader_answer`, `prepare_reader_ask`, `reader_ask_reply`
- [[Reference/Modules/learnloop_sidecar/polled_jobs|learnloop_sidecar.polled_jobs]] — imports `module`; calls `registry`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `logging`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_the_pinned_rd3a_rpcs_are_all_of_them`
- [tests/test_reader_rd3a_companion_ask.py](../../../../../../tests/test_reader_rd3a_companion_ask.py) — direct import
  - `test_the_rpcs_are_registered_desktop_only_and_refuse_extra_fields`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/companion_ask.py](../../../../../../src/learnloop_sidecar/handlers/companion_ask.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
