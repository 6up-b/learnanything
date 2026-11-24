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

`learnloop.pads.ink_transcribe` exists within [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] to own the behavior summarized by its module contract: Reading the learner's ink (spec §10.10 "Transcription"): one image of an owner's standing strokes, read by GLM-OCR, the text recognition ingest uses for page images, and kept as GLM-OCR returns it.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/pads/ink_transcribe.py](../../../../../../src/learnloop/pads/ink_transcribe.py) |
| Source lines | 230 |
| Owning package | [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class InkUnavailable(Exception)` ([source](../../../../../../src/learnloop/pads/ink_transcribe.py), line 63) — Nothing was read and nothing was sent.
  - `__init__(self, reason: str, message: str) -> None` (line 67; internal)
- `class Prepared` ([source](../../../../../../src/learnloop/pads/ink_transcribe.py), line 74) — What one reading reads: an owner's standing strokes, their hash and the resolution they were drawn at.
  - `key(self) -> str` (line 84; public)
- `prepare(repository: Repository, ink_id: str) -> Prepared` ([source](../../../../../../src/learnloop/pads/ink_transcribe.py), line 88) — The strokes ``ink_id``'s owner holds now (every save of that owner, not only this one), or ``InkError``.
- `stored(repository: Repository, prepared: Prepared) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/pads/ink_transcribe.py), line 108)
- `render(prepared: Prepared) -> bytes` ([source](../../../../../../src/learnloop/pads/ink_transcribe.py), line 114)
- `class InkReader` ([source](../../../../../../src/learnloop/pads/ink_transcribe.py), line 119) — GLM-OCR as ingest would run it for a page image now: the backend it selects, and its admission.
  - `__init__(self, vault: Any) -> None` (line 122; internal)
  - `read(self, image: bytes) -> str` (line 130; public) — The text GLM-OCR recognises in ``image``, unchanged.
  - `provider(self) -> str | None` (line 149; public)
  - `version(self) -> str` (line 153; public) — What read it, on the kept row (``prompt_version``: a reader's version; no prompt is sent).
- `transcribe(vault: Any, repository: Repository, prepared: Prepared, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/ink_transcribe.py), line 198) — Read the strokes (or return their reading, spending nothing) and keep it.

### Module constants

- `TASK` ([src/learnloop/pads/ink_transcribe.py](../../../../../../src/learnloop/pads/ink_transcribe.py), line 46)
- `SERVER_CLIENT_ID` ([src/learnloop/pads/ink_transcribe.py](../../../../../../src/learnloop/pads/ink_transcribe.py), line 49)
- `UPLOAD_FLOW` ([src/learnloop/pads/ink_transcribe.py](../../../../../../src/learnloop/pads/ink_transcribe.py), line 51)
- `TURN_ON_MESSAGE` ([src/learnloop/pads/ink_transcribe.py](../../../../../../src/learnloop/pads/ink_transcribe.py), line 53)
- `NEEDS_OK_MESSAGE` ([src/learnloop/pads/ink_transcribe.py](../../../../../../src/learnloop/pads/ink_transcribe.py), line 57)

### Explicit exports

`__all__` declares:

- `InkReader`
- `InkUnavailable`
- `MAY_BE_WRONG`
- `NEEDS_OK_MESSAGE`
- `NOTHING_READ`
- `Prepared`
- `TASK`
- `TURN_ON_MESSAGE`
- `UPLOAD_FLOW`
- `prepare`
- `render`
- `stored`
- `transcribe`

## Internal implementation anchors

- `_result(connection: Any, row: dict[str, Any], *, applied: bool | None=None, reason: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/ink_transcribe.py), line 161)
- `_apply_to_block(connection: Any, row: dict[str, Any], now: str) -> tuple[bool, str | None]` ([source](../../../../../../src/learnloop/pads/ink_transcribe.py), line 178) — Write the reading as the block's next version, or say why not (the caller's transaction).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/ink|learnloop_sidecar.handlers.ink]] — imports `module`; statically calls `prepare`, `stored`, `transcribe`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/model_use|learnloop.ai.model_use]] — imports `module`; calls `require`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `file_upload_allowed`; calls `file_upload_allowed`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/ink_strokes|learnloop.db.stores.ink_strokes]] — imports `module`; calls `annotation_exists`, `insert_reading`, `owner_saves`, `reading_for`
- [[Reference/Modules/learnloop/db/stores/pad_reads|learnloop.db.stores.pad_reads]] — imports `module`; calls `head`
- [[Reference/Modules/learnloop/db/stores/pads|learnloop.db.stores.pads]] — imports `module`; calls `insert_version`, `touch_pad`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ingest/extractors/glm_ocr|learnloop.ingest.extractors.glm_ocr]] — imports `GlmOcrDocumentExtractor`, `LAYOUT_MODEL`, `RECOGNITION_MODEL`, `selected_backend`; calls `GlmOcrDocumentExtractor`, `selected_backend`
- [[Reference/Modules/learnloop/pads/ink|learnloop.pads.ink]] — imports `module`; calls `InkError`, `owner_of`, `reading_decision`, `standing`, `strokes_hash`
- [[Reference/Modules/learnloop/pads/ink_render|learnloop.pads.ink_render]] — imports `module`; calls `render_png`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/ink|learnloop_sidecar.handlers.ink]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_ink_glm_ocr.py](../../../../../../tests/test_reader_ink_glm_ocr.py) — direct import
  - `test_a_local_backend_that_does_not_answer_is_not_available`
  - `test_hosted_glm_ocr_reads_the_image_of_the_strokes_and_nothing_else`
  - `test_hosted_without_the_learners_ok_for_z_ai_sends_nothing`
  - `test_without_glm_ocr_nothing_is_sent_and_the_line_says_how_to_turn_it_on`
- [tests/test_reader_rd8a_fix.py](../../../../../../tests/test_reader_rd8a_fix.py) — direct import
  - `test_a_cached_reading_beside_the_learners_correction_keeps_its_reason`
  - `test_a_partial_erase_leaves_the_words_until_the_line_is_read_again`
  - `test_a_reading_of_strokes_that_changed_meanwhile_is_kept_but_never_replaces_the_newer_one`
  - `test_erasing_handwriting_keeps_the_learners_own_words`
  - `test_erasing_handwriting_takes_its_automatic_transcription_and_what_was_read_from_it`
  - `test_lifting_an_ink_line_out_keeps_its_handwriting_and_its_reading`
- [tests/test_reader_rd8a_fix_rpcs.py](../../../../../../tests/test_reader_rd8a_fix_rpcs.py) — direct import
  - `test_a_reading_finishing_after_its_context_moved_on_keeps_its_facts_but_wakes_no_worker`
  - `test_the_listed_reading_beside_the_learners_correction_says_why_it_is_not_the_words`
- [tests/test_reader_rd8a_transcribe.py](../../../../../../tests/test_reader_rd8a_transcribe.py) — direct import
  - `test_a_removed_blocks_ink_is_not_read`
  - `test_ink_on_a_page_is_never_read_nor_learner_text`
  - `test_one_image_of_the_standing_strokes_is_sent_alone`

## Modification guidance

- Make changes here when the responsibility remains ink transcribe within learnloop.pads; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/pads/ink_transcribe.py](../../../../../../src/learnloop/pads/ink_transcribe.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
