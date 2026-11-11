---
title: "learnloop.adaptive_difficulty.projection"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/projection.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/projection.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.adaptive_difficulty.projection module"
  - "src/learnloop/adaptive_difficulty/projection.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.projection`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.projection` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: The projected vault and repository an AD operation hands its readers (the AD23 redesign).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/projection.py](../../../../../../src/learnloop/adaptive_difficulty/projection.py) |
| Source lines | 58 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ProjectedRepository` ([source](../../../../../../src/learnloop/adaptive_difficulty/projection.py), line 16) — The raw repository, with its document-IR loader read through the operation's view.
  - `__init__(self, repository: Any, view: Any) -> None` (line 21; internal)
  - `__getattr__(self, name: str) -> Any` (line 25; internal)
  - `__setattr__(self, name: str, value: Any) -> None` (line 28; internal)
  - `projection_key(self) -> str` (line 32; public) — What a cache of IR-derived results keys this repository's reads by: its operation's protection epoch (``span_aliases``' memo; the AD23 redesign).
  - `__repr__(self) -> str` (line 40; internal)
  - `load_document_ir(self, extraction_id: str) -> Any` (line 43; public)
  - `span_reanchors_between(self, from_extraction_id: str, to_extraction_id: str) -> list[dict[str, Any]]` (line 46; public)
- `project_vault(view: Any) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/projection.py), line 50)
- `project_repository(repository: Any, view: Any) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/projection.py), line 54)

### Explicit exports

`__all__` declares:

- `ProjectedRepository`
- `project_repository`
- `project_vault`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `project_repository`; statically calls `project_repository`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `project_repository`, `project_vault`; statically calls `project_repository`, `project_vault`
- [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]] — imports `project_repository`; statically calls `project_repository`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `epoch_of`; calls `epoch_of`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]], [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]], [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/ad23_contract_helpers.py](../../../../../../tests/ad23_contract_helpers.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]]
- [tests/ad23_fakes.py](../../../../../../tests/ad23_fakes.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]]
- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]]
- [tests/test_ad23_fix_r7.py](../../../../../../tests/test_ad23_fix_r7.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]]
- [tests/test_ad23_fix_r8.py](../../../../../../tests/test_ad23_fix_r8.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]]
- [tests/test_ad23_fix_r9.py](../../../../../../tests/test_ad23_fix_r9.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]]
- [tests/test_ad23_fix_review.py](../../../../../../tests/test_ad23_fix_review.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]]
- [tests/test_ad23_inversion.py](../../../../../../tests/test_ad23_inversion.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]]
- [tests/test_ad2_serving.py](../../../../../../tests/test_ad2_serving.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]]
- [tests/test_ad3_subject_view.py](../../../../../../tests/test_ad3_subject_view.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]]
- [tests/test_ad_epoch.py](../../../../../../tests/test_ad_epoch.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]]
- [tests/test_ad_guard.py](../../../../../../tests/test_ad_guard.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]]

## Modification guidance

- Make changes here when the responsibility remains projection within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/projection.py](../../../../../../src/learnloop/adaptive_difficulty/projection.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
