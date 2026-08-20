---
title: "learnloop.content.synthesis.facet_doctor"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/facet_doctor.py"
source_paths:
  - "src/learnloop/content/synthesis/facet_doctor.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.synthesis"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.content.synthesis.facet_doctor module"
  - "src/learnloop/content/synthesis/facet_doctor.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-synthesis"
---

# `learnloop.content.synthesis.facet_doctor`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.facet_doctor` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: Post-append near-duplicate facet doctor pass (source-ingestion §12/§14).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/facet_doctor.py](../../../../../../../src/learnloop/content/synthesis/facet_doctor.py) |
| Source lines | 85 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class MergeReviewProposal` ([source](../../../../../../../src/learnloop/content/synthesis/facet_doctor.py), line 41)
  - `as_dict(self) -> dict[str, Any]` (line 47; public)
- `near_duplicate_facet_review(vault: LoadedVault, *, threshold: float=DEFAULT_THRESHOLD) -> list[MergeReviewProposal]` ([source](../../../../../../../src/learnloop/content/synthesis/facet_doctor.py), line 57) — Deterministic pairwise near-duplicate detection over the facet registry.

### Module constants

- `_TOKEN_RE` ([src/learnloop/content/synthesis/facet_doctor.py](../../../../../../../src/learnloop/content/synthesis/facet_doctor.py), line 19)
- `DEFAULT_THRESHOLD` ([src/learnloop/content/synthesis/facet_doctor.py](../../../../../../../src/learnloop/content/synthesis/facet_doctor.py), line 20)

## Internal implementation anchors

- `_facet_tokens(facet: Any) -> set[str]` ([source](../../../../../../../src/learnloop/content/synthesis/facet_doctor.py), line 23)
- `_jaccard(left: set[str], right: set[str]) -> float` ([source](../../../../../../../src/learnloop/content/synthesis/facet_doctor.py), line 33)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `near_duplicate_facet_review`; statically calls `near_duplicate_facet_review`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `near_duplicate_facet_review`; statically calls `near_duplicate_facet_review`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]], [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_source_append.py](../../../../../../../tests/test_source_append.py) — direct import
  - `test_post_append_near_duplicate_is_aliased_at_mint_and_never_auto_merged`

## Modification guidance

- Change facet doctor policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/facet_doctor.py](../../../../../../../src/learnloop/content/synthesis/facet_doctor.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
