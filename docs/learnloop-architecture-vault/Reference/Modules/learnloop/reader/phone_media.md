---
title: "learnloop.reader.phone_media"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/phone_media.py"
source_paths:
  - "src/learnloop/reader/phone_media.py"
source_commit: "a36b01c4629514878246d72d5902ad86a1a5e09c"
source_commit_timestamp: "2026-11-07T07:19:14-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.phone_media module"
  - "src/learnloop/reader/phone_media.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.phone_media`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.phone_media` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Mobile v2 stage V4: what of a reading, a page or a stored image the phone may be sent (spec §2.3, §3.3).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/phone_media.py](../../../../../../src/learnloop/reader/phone_media.py) |
| Source lines | 250 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `a36b01c4629514878246d72d5902ad86a1a5e09c` |
| Commit timestamp | `2026-11-07T07:19:14-05:00` |

## Public API

- `class PhoneWithheld` ([source](../../../../../../src/learnloop/reader/phone_media.py), line 36) — What of one reading the phone may not be sent.
  - `covers(self, span_id: str | None) -> bool` (line 46; public)
  - `any(self, span_ids: Iterable[str | None]) -> bool` (line 49; public)
  - `as_protection(self, desktop: dict[str, Any] | None) -> dict[str, Any]` (line 52; public) — The ``protection`` key a phone reads: the desktop's held-out partition widened to every passage withheld here, so a selection on any of them offers no model action.
- `phone_withheld(vault_or_sets: Any, repository: Any, extraction_id: str, span_ids: Iterable[str | None]=()) -> PhoneWithheld` ([source](../../../../../../src/learnloop/reader/phone_media.py), line 64) — What exam material (rules 1-4, the held-out partition included) covers of ``extraction_id``, among ``span_ids``.
- `class MediaRefusal` ([source](../../../../../../src/learnloop/reader/phone_media.py), line 84) — Why the host does not serve a page or an image: its HTTP status, stable code and plain line.
- `readings_of_file(repository: Any, digest: str) -> list[str]` ([source](../../../../../../src/learnloop/reader/phone_media.py), line 99) — Every completed reading of the stored file ``digest`` (``sha256:<hex>``), whatever source it belongs to.
- `digest_of_reading(repository: Any, extraction_id: str) -> str | None` ([source](../../../../../../src/learnloop/reader/phone_media.py), line 110) — The stored file a completed reading was made from (``sha256:<hex>``), or None.
- `page_refusal(vault: Any, repository: Any, digest: str, page: int) -> MediaRefusal | None` ([source](../../../../../../src/learnloop/reader/phone_media.py), line 126) — Why page ``page`` (zero-based) of the stored PDF ``digest`` is not served to the phone, or None.
- `asset_refusal(vault: Any, repository: Any, digest: str) -> MediaRefusal | None` ([source](../../../../../../src/learnloop/reader/phone_media.py), line 166) — Why the stored image ``digest`` is not served to the phone, or None.
- `media_predicate(vault: Any, repository: Any=None) -> Any` ([source](../../../../../../src/learnloop/reader/phone_media.py), line 219) — The phone eligibility's "does the host serve this target" (``scheduling.device_eligibility.MediaPredicate``): exactly the page and asset endpoints' refusals, over ``repository`` (or the vault's database, opened read only at the first question).

### Module constants

- `LOG` ([src/learnloop/reader/phone_media.py](../../../../../../src/learnloop/reader/phone_media.py), line 29)
- `MAX_ASSET_BYTES` ([src/learnloop/reader/phone_media.py](../../../../../../src/learnloop/reader/phone_media.py), line 32)
- `NOT_FOUND` ([src/learnloop/reader/phone_media.py](../../../../../../src/learnloop/reader/phone_media.py), line 92)

### Explicit exports

`__all__` declares:

- `MAX_ASSET_BYTES`
- `media_predicate`
- `MediaRefusal`
- `PhoneWithheld`
- `asset_refusal`
- `digest_of_reading`
- `page_refusal`
- `phone_withheld`
- `readings_of_file`

## Internal implementation anchors

- `_held_out(withheld: PhoneWithheld) -> MediaRefusal` ([source](../../../../../../src/learnloop/reader/phone_media.py), line 95)
- `_reader_source_ok(repository: Any, source_id: Any) -> bool` ([source](../../../../../../src/learnloop/reader/phone_media.py), line 121)
- `_repository_for(vault: Any) -> Any` ([source](../../../../../../src/learnloop/reader/phone_media.py), line 202) — The vault's database, read only, for a check asked without one; None when it can't be named.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/phone_reader|learnloop_sidecar.phone_reader]] — imports `PhoneWithheld`, `phone_withheld`; statically calls `phone_withheld`
- [[Reference/Modules/learnloop_sidecar/serving|learnloop_sidecar.serving]] — imports `media_predicate`; statically calls `media_predicate`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `HELD_OUT_REFUSAL`, `exam_material`, `held_out_refusal`; calls `exam_material`, `held_out_refusal`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ingest/originals|learnloop.ingest.originals]] — imports `is_pdf_file`, `stored_original_path`; calls `is_pdf_file`, `stored_original_path`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `module`; calls `reader_enabled`
- [[Reference/Modules/learnloop/scheduling/device_eligibility|learnloop.scheduling.device_eligibility]] — imports `image_kind`; calls `image_kind`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `logging`, `typing`
- Third party: `pypdfium2`

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/phone_reader|learnloop_sidecar.phone_reader]], [[Reference/Modules/learnloop_sidecar/serving|learnloop_sidecar.serving]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mobile_v4_codex_review.py](../../../../../../tests/test_mobile_v4_codex_review.py) — direct import
- [tests/test_mobile_v4_eligibility.py](../../../../../../tests/test_mobile_v4_eligibility.py) — direct import

## Modification guidance

- Change phone media policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/phone_media.py](../../../../../../src/learnloop/reader/phone_media.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
