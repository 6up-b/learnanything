---
title: "learnloop.ingest.extractors.base"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/extractors/base.py"
source_paths:
  - "src/learnloop/ingest/extractors/base.py"
source_commit: "f0052f7260eb63224bd103193929a03fd54660d6"
source_commit_timestamp: "2026-07-21T15:03:22-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-08-18"
package: "learnloop.ingest.extractors"
layer: "infrastructure"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
aliases:
  - "learnloop.ingest.extractors.base module"
  - "src/learnloop/ingest/extractors/base.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ingest-extractors"
---

# `learnloop.ingest.extractors.base`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ingest.extractors.base` exists within [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] to own the behavior summarized by its module contract: The versioned extractor-provider boundary (spec_source_ingestion_v2 §2.9).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ingest/extractors/base.py](../../../../../../../src/learnloop/ingest/extractors/base.py) |
| Source lines | 167 |
| Owning package | [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `f0052f7260eb63224bd103193929a03fd54660d6` |
| Commit timestamp | `2026-07-21T15:03:22-04:00` |

## Public API

- `class ExtractionContext` ([source](../../../../../../../src/learnloop/ingest/extractors/base.py), line 19) — Everything a run needs beyond the raw bytes (feeds the request hash).
- `class DocumentExtractor(Protocol)` ([source](../../../../../../../src/learnloop/ingest/extractors/base.py), line 30) — A provider that turns raw bytes into the LearnLoop Document IR.
  - `version(self) -> str` (line 35; public) — Provider/package version — participates in the request hash (§2.2).
  - `model_versions(self) -> dict[str, str]` (line 38; public) — Best-effort model-artifact versions (may be empty).
  - `extract(self, raw_bytes: bytes, context: ExtractionContext)` (line 41; public) — Return a :class:`DocumentIR` for ``raw_bytes``.
- `assign_span_semantic_hash(blocks: list[DocumentBlock]) -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/base.py), line 45) — Convenience wrapper so extractors compute unit hashes consistently.
- `units_from_toc_entries(entries: list[dict[str, Any]], blocks: list[DocumentBlock], *, document_title: str | None=None, locator_scheme: str='toc', drop_empty: bool=False) -> list[DocumentUnit]` ([source](../../../../../../../src/learnloop/ingest/extractors/base.py), line 51) — Hierarchical units from ordered ToC-shaped entries (§2.3).
- `single_unit_from_blocks(blocks: list[DocumentBlock], *, label: str, unit_id: str='u1', locator: dict | None=None) -> DocumentUnit` ([source](../../../../../../../src/learnloop/ingest/extractors/base.py), line 146) — Build one whole-document unit — the honest trivial case for non-paged or ToC-less sources (§2.3).

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `ExtractionContext`; statically calls `ExtractionContext`
- [[Reference/Modules/learnloop/ingest/extractors/__init__|learnloop.ingest.extractors]] — imports `DocumentExtractor`, `ExtractionContext`, `single_unit_from_blocks`, `units_from_toc_entries`
- [[Reference/Modules/learnloop/ingest/extractors/datalab|learnloop.ingest.extractors.datalab]] — imports `ExtractionContext`
- [[Reference/Modules/learnloop/ingest/extractors/marker|learnloop.ingest.extractors.marker]] — imports `ExtractionContext`, `units_from_toc_entries`; statically calls `units_from_toc_entries`
- [[Reference/Modules/learnloop/ingest/extractors/pypdf|learnloop.ingest.extractors.pypdf]] — imports `ExtractionContext`, `single_unit_from_blocks`, `units_from_toc_entries`; statically calls `single_unit_from_blocks`, `units_from_toc_entries`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ingest/hashing|learnloop.ingest.hashing]] — imports `semantic_hash`; calls `semantic_hash`
- [[Reference/Modules/learnloop/ingest/ir|learnloop.ingest.ir]] — imports `DocumentBlock`, `DocumentUnit`; calls `DocumentUnit`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/ingest/extractors/__init__|learnloop.ingest.extractors]], [[Reference/Modules/learnloop/ingest/extractors/datalab|learnloop.ingest.extractors.datalab]], [[Reference/Modules/learnloop/ingest/extractors/marker|learnloop.ingest.extractors.marker]], [[Reference/Modules/learnloop/ingest/extractors/pypdf|learnloop.ingest.extractors.pypdf]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_document_ir.py](../../../../../../../tests/test_document_ir.py) — direct import
  - `test_pypdf_extractor_builds_units_from_embedded_outline`
  - `test_units_from_toc_entries_drops_empty_and_reparents`

## Modification guidance

- Change acquisition or extraction mechanics here; keep source-library and downstream learning-content policy in `learnloop.content`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ingest/extractors/base.py](../../../../../../../src/learnloop/ingest/extractors/base.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
