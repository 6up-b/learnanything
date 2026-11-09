---
title: "learnloop.reader.source_identity"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/source_identity.py"
source_paths:
  - "src/learnloop/reader/source_identity.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.source_identity module"
  - "src/learnloop/reader/source_identity.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.source_identity`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.source_identity` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: One guard for every persisting Reader request that names passages (Reader CA6b fix round 5, structural).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/source_identity.py](../../../../../../src/learnloop/reader/source_identity.py) |
| Source lines | 307 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class SpanExtractionMismatch(ValueError)` ([source](../../../../../../src/learnloop/reader/source_identity.py), line 31) — The passages named are not the named reading's (or the reading is not the named source's or revision's).
  - `__init__(self, message: str, *, extraction_id: str | None, reason: str, span_ids: Sequence[str]=()) -> None` (line 37; internal)
  - `details(self) -> dict[str, Any]` (line 44; public)
- `selection_span_ids(raw_selection: Mapping[str, Any] | None) -> list[str]` ([source](../../../../../../src/learnloop/reader/source_identity.py), line 48) — The span ids a raw display selection names (its nodes, and a region's span).
- `selection_readings(raw_selection: Mapping[str, Any] | None) -> list[str]` ([source](../../../../../../src/learnloop/reader/source_identity.py), line 69) — Reader CA6b fix round 6: the readings a raw selection says its nodes are passages of (each node's ``extractionId``, and the selection's own).
- `require_selection_provenance(repository: Any, *, extraction_id: str, raw_selection: Mapping[str, Any] | None, render_view_id: str | None) -> None` ([source](../../../../../../src/learnloop/reader/source_identity.py), line 95) — Reader CA6b fix round 6 (verify finding 1): a selection's provenance is the request's reading.
- `require_annotation_source(repository: Any, *, annotation_id: str | None, extraction_id: str) -> None` ([source](../../../../../../src/learnloop/reader/source_identity.py), line 121) — Reader CA6b fix round 6 (verify finding 2): an annotation is re-anchored only onto a reading of its own source (an earlier or later reading, or another revision, of the same book), never onto another book's.
- `subject_span_id(subject_id: str | None, extraction_id: str) -> list[str]` ([source](../../../../../../src/learnloop/reader/source_identity.py), line 149) — A preset's subject: a bare span id of the reading, or a ``span:{extraction}/{span}`` locator (one naming another reading is a mismatch on its own).
- `require_source_identity(repository: Any, *, extraction_id: str, span_ids: Iterable[str | None]=(), source_id: str | None=None, revision_id: str | None=None) -> None` ([source](../../../../../../src/learnloop/reader/source_identity.py), line 167) — Refuse (``SpanExtractionMismatch``) unless every span id is a block of ``extraction_id``, and the reading is ``revision_id``'s and ``source_id``'s when they are named.
- `require_span_keys(repository: Any, keys: Iterable[str]) -> None` ([source](../../../../../../src/learnloop/reader/source_identity.py), line 213) — Library pins: each ``extraction:span`` key's span is a block of the reading the key names.
- `require_reading_span_keys(repository: Any, *, extraction_id: str, span_keys: Iterable[str] | None, span_ids: Iterable[str | None]=()) -> None` ([source](../../../../../../src/learnloop/reader/source_identity.py), line 227) — Reader follow-ups Nov 1 (CA6b open item 1): the reading-only RPCs' passages, extraction-qualified.
- `require_exchange_in_extraction(repository: Any, *, extraction_id: str, exchange_id: str | None) -> None` ([source](../../../../../../src/learnloop/reader/source_identity.py), line 272) — A Reader exchange named with a reading must have been asked in it.

### Module constants

- `MISMATCH_CODE` ([src/learnloop/reader/source_identity.py](../../../../../../src/learnloop/reader/source_identity.py), line 28)

### Explicit exports

`__all__` declares:

- `MISMATCH_CODE`
- `require_annotation_source`
- `require_selection_provenance`
- `selection_readings`
- `SpanExtractionMismatch`
- `require_exchange_in_extraction`
- `require_reading_span_keys`
- `require_source_identity`
- `require_span_keys`
- `selection_span_ids`
- `subject_span_id`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `MISMATCH_CODE`
- [[Reference/Modules/learnloop_sidecar/source_identity|learnloop_sidecar.source_identity]] — imports `module`; statically calls `require_annotation_source`, `require_exchange_in_extraction`, `require_reading_span_keys`, `require_selection_provenance`, `require_source_identity`, `require_span_keys`, `selection_span_ids`, `subject_span_id`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]], [[Reference/Modules/learnloop_sidecar/source_identity|learnloop_sidecar.source_identity]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_qualified_span_keys.py](../../../../../../tests/test_reader_qualified_span_keys.py) — direct import
  - `test_ca6b_open1_the_helper_refuses_another_readings_key_and_an_unkeyed_id`
- [tests/test_reader_source_identity_guard.py](../../../../../../tests/test_reader_source_identity_guard.py) — direct import
  - `test_the_helper_passes_a_readings_own_passages_and_refuses_anothers`

## Modification guidance

- Change source identity policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/source_identity.py](../../../../../../src/learnloop/reader/source_identity.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
