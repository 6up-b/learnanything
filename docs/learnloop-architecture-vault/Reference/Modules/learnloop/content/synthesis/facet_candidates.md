---
title: "learnloop.content.synthesis.facet_candidates"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/facet_candidates.py"
source_paths:
  - "src/learnloop/content/synthesis/facet_candidates.py"
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
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.synthesis.facet_candidates module"
  - "src/learnloop/content/synthesis/facet_candidates.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-synthesis"
---

# `learnloop.content.synthesis.facet_candidates`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.facet_candidates` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: Candidate facet harvesting (knowledge-model §3.3).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/facet_candidates.py](../../../../../../../src/learnloop/content/synthesis/facet_candidates.py) |
| Source lines | 169 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class FacetCandidate` ([source](../../../../../../../src/learnloop/content/synthesis/facet_candidates.py), line 27)
- `class ReviewPair` ([source](../../../../../../../src/learnloop/content/synthesis/facet_candidates.py), line 36)
- `harvest_facet_candidates(vault: LoadedVault, repository=None) -> dict[str, object]` ([source](../../../../../../../src/learnloop/content/synthesis/facet_candidates.py), line 156) — Harvest candidates and lexical review pairs (§3.3).

### Module constants

- `_TOKEN` ([src/learnloop/content/synthesis/facet_candidates.py](../../../../../../../src/learnloop/content/synthesis/facet_candidates.py), line 20)
- `REVIEW_THRESHOLD` ([src/learnloop/content/synthesis/facet_candidates.py](../../../../../../../src/learnloop/content/synthesis/facet_candidates.py), line 22)
- `_MINHASH_PERMUTATIONS` ([src/learnloop/content/synthesis/facet_candidates.py](../../../../../../../src/learnloop/content/synthesis/facet_candidates.py), line 23)

## Internal implementation anchors

- `_tokens(text: str) -> set[str]` ([source](../../../../../../../src/learnloop/content/synthesis/facet_candidates.py), line 43)
- `_suggest_id(text: str) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/facet_candidates.py), line 47)
- `_minhash_signature(tokens: set[str]) -> tuple[int, ...]` ([source](../../../../../../../src/learnloop/content/synthesis/facet_candidates.py), line 52) — Deterministic MinHash signature of a token set (no external deps).
- `_minhash_similarity(left: tuple[int, ...], right: tuple[int, ...]) -> float` ([source](../../../../../../../src/learnloop/content/synthesis/facet_candidates.py), line 72)
- `_harvest(vault: LoadedVault, repository=None) -> list[FacetCandidate]` ([source](../../../../../../../src/learnloop/content/synthesis/facet_candidates.py), line 79)
- `_review_pairs(candidates: list[FacetCandidate]) -> list[ReviewPair]` ([source](../../../../../../../src/learnloop/content/synthesis/facet_candidates.py), line 136)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `harvest_facet_candidates`; statically calls `harvest_facet_candidates`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `snake_case`; calls `snake_case`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `re`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_facet_candidates.py](../../../../../../../tests/test_facet_candidates.py) — direct import
  - `test_harvest_is_deterministic`
  - `test_harvests_candidates_from_multiple_sources`
  - `test_harvests_candidates_from_unit_inventories`
  - `test_similarity_pair_is_review_proposal_only`

## Modification guidance

- Change facet candidates policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/facet_candidates.py](../../../../../../../src/learnloop/content/synthesis/facet_candidates.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
