---
title: "learnloop.content.authoring.practice_leakage"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/authoring/practice_leakage.py"
source_paths:
  - "src/learnloop/content/authoring/practice_leakage.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.authoring"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.authoring.practice_leakage module"
  - "src/learnloop/content/authoring/practice_leakage.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-authoring"
---

# `learnloop.content.authoring.practice_leakage`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.authoring.practice_leakage` exists within [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] to own the behavior summarized by its module contract: ING M8 — cross-source practice generation leakage controls (spec §8.5, §14).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/authoring/practice_leakage.py](../../../../../../../src/learnloop/content/authoring/practice_leakage.py) |
| Source lines | 352 |
| Owning package | [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class HeldOutInventory` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 44) — Deterministic fingerprint of held-out exam text (§8.5).
  - `empty(self) -> bool` (line 53; public)
- `class CrossSourceSpan` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 58)
  - `as_dict(self) -> dict[str, Any]` (line 67; public)
- `build_held_out_inventory(vault: LoadedVault, repository: Repository, *, subject_ids: list[str] | None=None, shingle_n: int=DEFAULT_SHINGLE_N) -> HeldOutInventory` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 168) — Fingerprint every held-out exam span text vault-wide (§8.5).
- `check_leakage(text: str, inventory: HeldOutInventory) -> list[dict[str, str]]` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 195) — Deterministic overlap findings between ``text`` and held-out material.
- `screen_practice_payload(payload: dict[str, Any], inventory: HeldOutInventory) -> list[dict[str, str]]` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 237) — Leakage findings for one generated practice-item payload (§14).
- `build_cross_source_spans(vault: LoadedVault, repository: Repository, learning_object_id: str, *, max_spans_per_item: int=4) -> list[CrossSourceSpan]` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 286) — Bounded multi-source grounding spans for one learning object (§8.5).

### Module constants

- `DEFAULT_SHINGLE_N` ([src/learnloop/content/authoring/practice_leakage.py](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 32)
- `_SEMANTIC_RELATION_PRIORITY` ([src/learnloop/content/authoring/practice_leakage.py](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 36)
- `_SPAN_TEXT_CAP` ([src/learnloop/content/authoring/practice_leakage.py](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 40)

## Internal implementation anchors

- `_normalize_tokens(text: str) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 82)
- `_shingles(tokens: list[str], n: int) -> set[str]` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 86)
- `_numeric_literals(text: str) -> set[str]` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 94) — Distinctive numeric literals: multi-digit integers, decimals, fractions, or percentages.
- `_held_out_span_texts(vault: LoadedVault, repository: Repository, *, subject_ids: set[str] | None) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 114) — Resolve the text of every held-out exam span vault-wide (§4.2 use modes).
- `_payload_surfaces(payload: dict[str, Any]) -> str` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 212) — Concatenate the learner-visible surfaces of a practice-item payload.
- `_lo_facet_ids(vault: LoadedVault, learning_object) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 246) — Canonical facet ids a learning object teaches: blueprint recipe components plus its practice items' evidence facets.
- `_span_text(repository: Repository, extraction_id: str, span_id: str) -> str | None` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 263)
- `_span_id_from_locator(locator: str | None) -> str | None` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 274)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `build_cross_source_spans`, `build_held_out_inventory`, `screen_practice_payload`; statically calls `build_cross_source_spans`, `build_held_out_inventory`, `screen_practice_payload`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `build_cross_source_spans`; statically calls `build_cross_source_spans`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `parse_block_span`; calls `parse_block_span`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]], [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_practice_leakage.py](../../../../../../../tests/test_practice_leakage.py) — direct import
  - `test_cross_source_context_is_bounded_and_authority_first`
  - `test_held_out_inventory_flags_planted_phrase_and_passes_fresh_text`
  - `test_screen_practice_payload_catches_expected_answer_leak`

## Modification guidance

- Change practice leakage policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/authoring/practice_leakage.py](../../../../../../../src/learnloop/content/authoring/practice_leakage.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
