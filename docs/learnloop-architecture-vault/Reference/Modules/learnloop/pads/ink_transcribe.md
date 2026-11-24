---
title: "learnloop.pads.ink_transcribe"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/pads/ink_transcribe.py"
source_paths:
  - "src/learnloop/pads/ink_transcribe.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.pads"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.pads.ink_transcribe module"
  - "src/learnloop/pads/ink_transcribe.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-pads"
---

# `learnloop.pads.ink_transcribe`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.pads.ink_transcribe` exists within [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] to own the behavior summarized by its module contract: Reading the learner's ink (spec §10.10 "Transcription"): one image of an owner's standing strokes, sent to the model routed for ``ink_transcription``, read as Markdown with LaTeX.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/pads/ink_transcribe.py](../../../../../../src/learnloop/pads/ink_transcribe.py) |
| Source lines | 276 |
| Owning package | [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class InkTranscriptionV1(WireModel)` ([source](../../../../../../src/learnloop/pads/ink_transcribe.py), line 67)
- `build_prompt(image_sha256: str) -> str` ([source](../../../../../../src/learnloop/pads/ink_transcribe.py), line 72)
- `class InkUnavailable(Exception)` ([source](../../../../../../src/learnloop/pads/ink_transcribe.py), line 80) — Nothing was read.
  - `__init__(self, reason: str, message: str) -> None` (line 84; internal)
- `class Prepared` ([source](../../../../../../src/learnloop/pads/ink_transcribe.py), line 91) — What one reading reads: an owner's standing strokes, their hash and the resolution they were drawn at.
  - `key(self) -> str` (line 101; public)
- `prepare(repository: Repository, ink_id: str) -> Prepared` ([source](../../../../../../src/learnloop/pads/ink_transcribe.py), line 105) — The strokes ``ink_id``'s owner holds now (every save of that owner, not only this one), or ``InkError``.
- `stored(repository: Repository, prepared: Prepared) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/pads/ink_transcribe.py), line 125)
- `render(prepared: Prepared) -> bytes` ([source](../../../../../../src/learnloop/pads/ink_transcribe.py), line 131)
- `class InkRoute` ([source](../../../../../../src/learnloop/pads/ink_transcribe.py), line 136) — The reading's pinned route for one request (the step check's pattern: ``workbench.check.CheckRoute``).
  - `__init__(self, vault: Any, repository: Repository, *, client: Any | None, envelope: Any, owner_id: str) -> None` (line 139; internal)
  - `subscription(self) -> bool` (line 150; public)
  - `problem(self) -> InkUnavailable | None` (line 153; public)
  - `ask(self, prompt: str, image: bytes) -> InkTranscriptionV1` (line 166; public)
  - `model(self) -> str | None` (line 191; public)
- `transcribe(vault: Any, repository: Repository, prepared: Prepared, *, client: Any | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/ink_transcribe.py), line 241) — Read the strokes (or return their reading, spending nothing) and keep it.

### Module constants

- `ROUTE_TASK` ([src/learnloop/pads/ink_transcribe.py](../../../../../../src/learnloop/pads/ink_transcribe.py), line 51)
- `OWNER_KIND` ([src/learnloop/pads/ink_transcribe.py](../../../../../../src/learnloop/pads/ink_transcribe.py), line 52)
- `PROMPT_VERSION` ([src/learnloop/pads/ink_transcribe.py](../../../../../../src/learnloop/pads/ink_transcribe.py), line 53)
- `SERVER_CLIENT_ID` ([src/learnloop/pads/ink_transcribe.py](../../../../../../src/learnloop/pads/ink_transcribe.py), line 56)
- `INSTRUCTIONS` ([src/learnloop/pads/ink_transcribe.py](../../../../../../src/learnloop/pads/ink_transcribe.py), line 58)

### Explicit exports

`__all__` declares:

- `INSTRUCTIONS`
- `InkRoute`
- `InkTranscriptionV1`
- `InkUnavailable`
- `MAY_BE_WRONG`
- `NOTHING_READ`
- `OWNER_KIND`
- `PROMPT_VERSION`
- `Prepared`
- `ROUTE_TASK`
- `build_prompt`
- `prepare`
- `render`
- `stored`
- `transcribe`

## Internal implementation anchors

- `_result(connection: Any, row: dict[str, Any], *, applied: bool | None=None, reason: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/ink_transcribe.py), line 197)
- `_apply_to_block(connection: Any, row: dict[str, Any], now: str) -> tuple[bool, str | None]` ([source](../../../../../../src/learnloop/pads/ink_transcribe.py), line 214) — Write the reading as the block's next version, or say why not (the caller's transaction).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/ink|learnloop_sidecar.handlers.ink]] — imports `module`; statically calls `prepare`, `stored`, `transcribe`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `call_labels`; calls `call_labels`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `spend_envelopes`; calls `SpendBudget`, `SpendCaps`, `spend_envelopes`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `IMAGE_INPUT`, `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/ink_strokes|learnloop.db.stores.ink_strokes]] — imports `module`; calls `annotation_exists`, `insert_reading`, `owner_saves`, `reading_for`
- [[Reference/Modules/learnloop/db/stores/pad_reads|learnloop.db.stores.pad_reads]] — imports `module`; calls `head`
- [[Reference/Modules/learnloop/db/stores/pads|learnloop.db.stores.pads]] — imports `module`; calls `insert_version`, `touch_pad`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/pads/ink|learnloop.pads.ink]] — imports `module`; calls `InkError`, `owner_of`, `standing`, `strokes_hash`
- [[Reference/Modules/learnloop/pads/ink_render|learnloop.pads.ink_render]] — imports `module`; calls `render_png`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `PaidCalls`, `PaidRoute`, `plan_route`, `resolve_client`; calls `PaidCalls`, `plan_route`, `resolve_client`
- [[Reference/Modules/learnloop/workbench/check|learnloop.workbench.check]] — imports `module`; calls `daily_envelope`, `models_off`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/ink|learnloop_sidecar.handlers.ink]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/identity_pins_helpers.py](../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/ink_helpers.py](../../../../../../tests/ink_helpers.py) — direct import
- [tests/test_reader_rd8a_transcribe.py](../../../../../../tests/test_reader_rd8a_transcribe.py) — direct import
  - `test_a_model_that_cannot_read_images_is_refused_before_anything_is_sent`
  - `test_a_removed_blocks_ink_is_not_read`
  - `test_ink_on_a_page_is_never_read_nor_learner_text`
  - `test_one_image_of_the_standing_strokes_is_sent_alone_and_named_in_the_prompt`
  - `test_the_reading_becomes_the_blocks_next_version_and_is_kept_with_its_provenance`
  - `test_the_render_digest_and_the_prompt_are_stable`
  - `test_with_models_off_and_no_client_nothing_is_reached`

## Modification guidance

- Make changes here when the responsibility remains ink transcribe within learnloop.pads; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/pads/ink_transcribe.py](../../../../../../src/learnloop/pads/ink_transcribe.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
