---
title: "learnloop.ingest.block_roles"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/block_roles.py"
source_paths:
  - "src/learnloop/ingest/block_roles.py"
source_commit: "5ce697ea8f4fd05519152bfa2f9f7b9e53cf14fa"
source_commit_timestamp: "2026-07-13T21:17:38-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-08-18"
package: "learnloop.ingest"
layer: "infrastructure"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
aliases:
  - "learnloop.ingest.block_roles module"
  - "src/learnloop/ingest/block_roles.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ingest"
---

# `learnloop.ingest.block_roles`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ingest.block_roles` exists within [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] to own the behavior summarized by its module contract: Deterministic block-role hints (spec_source_ingestion_v2 §2.6).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py) |
| Source lines | 111 |
| Owning package | [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `5ce697ea8f4fd05519152bfa2f9f7b9e53cf14fa` |
| Commit timestamp | `2026-07-13T21:17:38-04:00` |

## Public API

- `classify_block_role(block_type: str, section_path: list[str] | None, text: str) -> str` ([source](../../../../../../src/learnloop/ingest/block_roles.py), line 80) — Return the most likely pedagogical role for a block (§2.6).

### Module constants

- `ROLES` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 14)
- `_BLOCK_TYPE_ROLES` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 30)
- `_CUES` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 46)
- `_WORKED_LEAD_RE` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 60)
- `_LEAD_RE` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 61)
- `_LEAD_ROLE` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 65)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ingest/extractors/marker|learnloop.ingest.extractors.marker]] — imports `classify_block_role`; statically calls `classify_block_role`
- [[Reference/Modules/learnloop/ingest/extractors/normalizers|learnloop.ingest.extractors.normalizers]] — imports `classify_block_role`; statically calls `classify_block_role`
- [[Reference/Modules/learnloop/ingest/extractors/pypdf|learnloop.ingest.extractors.pypdf]] — imports `classify_block_role`; statically calls `classify_block_role`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `re`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]

Static participation evidence comes from [[Reference/Modules/learnloop/ingest/extractors/marker|learnloop.ingest.extractors.marker]], [[Reference/Modules/learnloop/ingest/extractors/normalizers|learnloop.ingest.extractors.normalizers]], [[Reference/Modules/learnloop/ingest/extractors/pypdf|learnloop.ingest.extractors.pypdf]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_document_ir.py](../../../../../../tests/test_document_ir.py) — direct import
  - `test_block_role_classifier_recognizes_structures`

## Modification guidance

- Change acquisition or extraction mechanics here; keep source-library and downstream learning-content policy in `learnloop.content`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
