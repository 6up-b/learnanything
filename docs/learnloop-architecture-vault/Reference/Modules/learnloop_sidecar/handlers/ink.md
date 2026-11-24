---
title: "learnloop_sidecar.handlers.ink"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/ink.py"
source_paths:
  - "src/learnloop_sidecar/handlers/ink.py"
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
  - "learnloop_sidecar.handlers.ink module"
  - "src/learnloop_sidecar/handlers/ink.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.ink`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.ink` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Reader workbench v2 RPCs: pen and ink (spec §3.4, §10.10).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/ink.py](../../../../../../src/learnloop_sidecar/handlers/ink.py) |
| Source lines | 300 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `class InkSaveInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ink.py), line 52)
  - `_distinct_ids(cls, strokes: list[ink_core.InkStroke]) -> list[ink_core.InkStroke]` (line 62; internal)
- `class InkEraseInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ink.py), line 69)
- `class InkListInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ink.py), line 77)
  - `_exactly_one(self) -> 'InkListInput'` (line 82; internal)
- `class InkTranscribeInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ink.py), line 88)
- `class InkJobInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ink.py), line 92)
- `ink_save(ctx: SidecarContext, params: InkSaveInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ink.py), line 97) — One save of strokes to one owner: ``{applied_seq, ink_id, results: [ok{duplicate} | refused{code}]}``.
- `ink_erase(ctx: SidecarContext, params: InkEraseInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ink.py), line 110) — The barrel over an annotation's or a reading's ink: ``{applied_seq, erase_id, results: [ok{duplicate} | refused{code}]}`` (a block's ink is erased in its pad batch).
- `ink_list(ctx: SidecarContext, params: InkListInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ink.py), line 124) — The ink of a pad's standing ink blocks, or of a source's listed annotations: per owner its standing strokes, their hash and its latest reading (``current`` when it read exactly these strokes).
- `ink_transcribe(ctx: SidecarContext, params: InkTranscribeInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ink.py), line 225) — Read the strokes ``ink_id``'s owner holds now: ``{job_id, status, done, result, error}`` at once.
- `ink_transcribe_job(ctx: SidecarContext, params: InkJobInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ink.py), line 287) — The reading's state, at once (never a wait on the request path).
- `ink_transcribe_cancel(ctx: SidecarContext, params: InkJobInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ink.py), line 294) — Cancel the reading: its next model request is refused; a finished reading keeps its outcome.

### Module constants

- `LOG` ([src/learnloop_sidecar/handlers/ink.py](../../../../../../src/learnloop_sidecar/handlers/ink.py), line 43)
- `INK_RPCS` ([src/learnloop_sidecar/handlers/ink.py](../../../../../../src/learnloop_sidecar/handlers/ink.py), line 46)
- `KIND` ([src/learnloop_sidecar/handlers/ink.py](../../../../../../src/learnloop_sidecar/handlers/ink.py), line 47)
- `NOT_FOUND_MESSAGE` ([src/learnloop_sidecar/handlers/ink.py](../../../../../../src/learnloop_sidecar/handlers/ink.py), line 48)
- `_REGISTRY` ([src/learnloop_sidecar/handlers/ink.py](../../../../../../src/learnloop_sidecar/handlers/ink.py), line 140)
- `_WAIT_STEP_SECONDS` ([src/learnloop_sidecar/handlers/ink.py](../../../../../../src/learnloop_sidecar/handlers/ink.py), line 143)
- `_READING_LOCK` ([src/learnloop_sidecar/handlers/ink.py](../../../../../../src/learnloop_sidecar/handlers/ink.py), line 144)

### Explicit exports

`__all__` declares:

- `INK_RPCS`
- `InkSaveInput`

## Internal implementation anchors

- `_jobs(ctx: SidecarContext) -> PJ.PolledJobs` ([source](../../../../../../src/learnloop_sidecar/handlers/ink.py), line 147) — The context's reading jobs (by vault and id; a vault switch interrupts that vault's).
- `_error(error: SidecarError | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/ink.py), line 153)
- `_payload(job_id: str | None, status: str, *, finished: bool, result: dict[str, Any] | None, error: SidecarError | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ink.py), line 159)
- `_job_payload(job: PJ.PolledJob) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ink.py), line 165)
- `_receipt_payload(receipt: PJ.Receipt) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ink.py), line 177)
- `_after_reading(ctx: SidecarContext, vault: Any, repository: Any, result: dict[str, Any], live: Callable[[], bool]) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/ink.py), line 182) — A reading written into its block is committed learner text: emitted and given its proposals, as a pad batch's blocks are.
- `_as_sidecar_error(exc: Exception) -> SidecarError` ([source](../../../../../../src/learnloop_sidecar/handlers/ink.py), line 203)
- `_find(ctx: SidecarContext, job_id: str, *, cancel: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ink.py), line 273)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIProviderUnavailable`; calls `AIInterrupted`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `relay_job_offer`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/desks/protocol|learnloop.desks.protocol]] — imports `ProtocolError`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/pads/emission|learnloop.pads.emission]] — imports `module`; calls `settle_blocks`
- [[Reference/Modules/learnloop/pads/ink|learnloop.pads.ink]] — imports `module`; calls `erase_ink`, `ink_for_pad`, `ink_for_source`, `save_ink`
- [[Reference/Modules/learnloop/pads/ink_render|learnloop.pads.ink_render]] — imports `InkTooLarge`
- [[Reference/Modules/learnloop/pads/ink_transcribe|learnloop.pads.ink_transcribe]] — imports `module`; calls `prepare`, `stored`, `transcribe`
- [[Reference/Modules/learnloop/pads/proposals|learnloop.pads.proposals]] — imports `module`; calls `propose_for_blocks`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/desks|learnloop_sidecar.handlers.desks]] — imports `protocol_error`; calls `protocol_error`
- [[Reference/Modules/learnloop_sidecar/polled_jobs|learnloop_sidecar.polled_jobs]] — imports `module`; calls `registry`, `vault_key`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `logging`, `threading`, `typing`
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
  - `test_the_pinned_rd8a_rpcs_are_all_of_them`
- [tests/test_reader_rd8a_fix_rpcs.py](../../../../../../tests/test_reader_rd8a_fix_rpcs.py) — direct import
  - `test_a_reading_finishing_after_its_context_moved_on_keeps_its_facts_but_wakes_no_worker`
- [tests/test_reader_rd8a_rpcs.py](../../../../../../tests/test_reader_rd8a_rpcs.py) — direct import
  - `test_the_rpcs_are_registered_and_desktop_only`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/ink.py](../../../../../../src/learnloop_sidecar/handlers/ink.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
