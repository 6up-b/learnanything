---
title: "learnloop_sidecar.handlers.as_printed"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/as_printed.py"
source_paths:
  - "src/learnloop_sidecar/handlers/as_printed.py"
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
  - "learnloop_sidecar.handlers.as_printed module"
  - "src/learnloop_sidecar/handlers/as_printed.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.as_printed`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.as_printed` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Reader CA1: the problem as printed on the desktop (ux_reader_compare_ask_v1 §8, K15).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/as_printed.py](../../../../../../src/learnloop_sidecar/handlers/as_printed.py) |
| Source lines | 157 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `class AsPrintedInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/as_printed.py), line 42)
- `class TranscriptionReportInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/as_printed.py), line 47)
- `cold_now(vault: Any, repository: Any, practice_item_id: str) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/as_printed.py), line 63) — The item is administered on your own now (D46: nothing locates it): a due cold follow-up on it, an active diagnostic presentation of it, or DL2's due "Check once" served cold (F1: the first two need no commitment).
- `practice_as_printed(ctx: SidecarContext, params: AsPrintedInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/as_printed.py), line 111)
- `practice_report_transcription(ctx: SidecarContext, params: TranscriptionReportInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/as_printed.py), line 140)

### Module constants

- `AS_PRINTED_RPCS` ([src/learnloop_sidecar/handlers/as_printed.py](../../../../../../src/learnloop_sidecar/handlers/as_printed.py), line 35)
- `REPORT_NOTE_MAX_CHARS` ([src/learnloop_sidecar/handlers/as_printed.py](../../../../../../src/learnloop_sidecar/handlers/as_printed.py), line 39)

## Internal implementation anchors

- `_origin(repository: Any, item: Any) -> Any` ([source](../../../../../../src/learnloop_sidecar/handlers/as_printed.py), line 52) — The item's print with its solution guard's full reader (Astra batch review): every block's effective role, a solution region's body included.
- `_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/as_printed.py), line 59)
- `_source_title(repository: Any, source_id: str | None, extraction_id: str) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/as_printed.py), line 85) — The book's learner title (``add_source.learner_title``: its display title, else its file name in words), so a book imported without a title is named as the Library names it rather than "your book".

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/phone_reader|learnloop_sidecar.phone_reader]] — imports `cold_now`; statically calls `cold_now`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]] — imports `photo_for_practice_item`; calls `photo_for_practice_item`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `SystemClock`; calls `SystemClock`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `learner_title`; calls `learner_title`
- [[Reference/Modules/learnloop/intent/checks|learnloop.intent.checks]] — imports `cold_followup_duty`, `served_check`; calls `cold_followup_duty`, `served_check`
- [[Reference/Modules/learnloop/ops/maintenance_feed|learnloop.ops.maintenance_feed]] — imports `report_transcription_mismatch`; calls `report_transcription_mismatch`
- [[Reference/Modules/learnloop/reader/as_printed|learnloop.reader.as_printed]] — imports `item_as_printed`, `printed_origin`; calls `item_as_printed`, `printed_origin`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `block_roles`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/phone_reader|learnloop_sidecar.phone_reader]] — imports `phone_withheld`; calls `phone_withheld`
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

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/phone_reader|learnloop_sidecar.phone_reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_the_pinned_ca1_rpcs_are_all_of_them`
- [tests/test_mobile_v4_reader.py](../../../../../../tests/test_mobile_v4_reader.py) — direct import
  - `test_the_phones_ask_is_refused_while_its_check_on_your_own_is_open`
- [tests/test_reader_ca1_as_printed.py](../../../../../../tests/test_reader_ca1_as_printed.py) — direct import
  - `test_a_due_check_on_your_own_is_read_on_the_server`
- [tests/test_reader_ca1_astra_redesign.py](../../../../../../tests/test_reader_ca1_astra_redesign.py) — direct import

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/as_printed.py](../../../../../../src/learnloop_sidecar/handlers/as_printed.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
