---
title: "learnloop.content.synthesis.append_neighborhood"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/append_neighborhood.py"
source_paths:
  - "src/learnloop/content/synthesis/append_neighborhood.py"
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
  - "learnloop.content.synthesis.append_neighborhood module"
  - "src/learnloop/content/synthesis/append_neighborhood.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-synthesis"
---

# `learnloop.content.synthesis.append_neighborhood`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.append_neighborhood` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: Deterministic, reviewable affected-neighborhood selection for append (ING M7).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/append_neighborhood.py](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py) |
| Source lines | 472 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class MatchReason` ([source](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 65)
- `class Neighborhood` ([source](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 72) — The bounded existing-map neighborhood sent to append reconciliation.
  - `as_context(self) -> dict[str, Any]` (line 94; public) — The compact dict placed in the reconciliation prompt context.
  - `as_manifest_record(self) -> dict[str, Any]` (line 110; public)
  - `entity_refs(self) -> set[str]` (line 120; public)
- `extract_new_signals(new_inventories: list[dict[str, Any]], *, source_ids: Iterable[str]=(), revision_ids: Iterable[str]=()) -> _NewSignals` ([source](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 143) — Pull the deterministic match signals out of the new/changed inventories.
- `select_neighborhood(vault: LoadedVault, repository: Repository, new_inventories: list[dict[str, Any]], *, budget_tokens: int, source_ids: Iterable[str]=(), revision_ids: Iterable[str]=(), fingerprint_threshold: float=0.25, loose_threshold: float=0.12) -> Neighborhood` ([source](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 195) — Select the bounded affected-map neighborhood (deterministic, §10.1/§3.2).

### Module constants

- `_TOKEN_RE` ([src/learnloop/content/synthesis/append_neighborhood.py](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 36)
- `_STOPWORDS` ([src/learnloop/content/synthesis/append_neighborhood.py](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 37)

## Internal implementation anchors

- `_tokens(text: str) -> set[str]` ([source](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 46)
- `_jaccard(left: set[str], right: set[str]) -> float` ([source](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 50)
- `_estimate_tokens(obj: Any) -> int` ([source](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 57)
- `class _NewSignals` ([source](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 128)
- `_hash_entity(payload: dict[str, Any]) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 190)
- `_provenance_matched_entities(repository: Repository, signals: _NewSignals) -> dict[str, MatchReason]` ([source](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 274)
- `_unresolved_candidates(signals: _NewSignals, scored: dict[str, tuple[float, list[MatchReason]]]) -> list[str]` ([source](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 294) — Concept names in the new inventory that matched no existing entity yet.
- `_materialize(vault: LoadedVault, repository: Repository, ordered: list[tuple[str, tuple[float, list[MatchReason]]]], *, budget_tokens: int, rounds: int) -> Neighborhood` ([source](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 304)
- `_facet_contract(facet: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 460)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `Neighborhood`, `select_neighborhood`; statically calls `select_neighborhood`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/curriculum/curriculum_locks|learnloop.curriculum.curriculum_locks]] — imports `identity_locks`; calls `identity_locks`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `json`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_source_append.py](../../../../../../../tests/test_source_append.py) — direct import
  - `test_append_context_bounded_by_neighborhood`
  - `test_planted_full_map_resend_fails_scaling_gate`

## Modification guidance

- Change append neighborhood policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/append_neighborhood.py](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
