---
title: "learnloop.adaptive_difficulty.reading_cache"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/reading_cache.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/reading_cache.py"
source_commit: "e5c7bc73864aee15147b54032d776cc85f5cdc80"
source_commit_timestamp: "2026-11-07T02:07:26-05:00"
source_worktree_state: "clean"
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
  - "learnloop.adaptive_difficulty.reading_cache module"
  - "src/learnloop/adaptive_difficulty/reading_cache.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.reading_cache`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.reading_cache` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: Router speed stage 2, item 1: AD's section → LO map held across calls (no successor: every value is the map's).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/reading_cache.py](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py) |
| Source lines | 176 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e5c7bc73864aee15147b54032d776cc85f5cdc80` |
| Commit timestamp | `2026-11-07T02:07:26-05:00` |

## Public API

- `vault_digest(vault: Any) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 57) — A digest of everything ``section_map.learning_objects_for_section_in_ir`` reads of ``vault``: every LO's id, status and provenance references, each facet of its blueprints' union with its canonical id and that facet's references, and every note's id and canonical source (``canon…
- `base_key(view: Any, vault: Any, repository: Any, extraction_id: str, *, vault_key: str | None) -> tuple[Any, ...] | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 86) — The key a reading's held values share in one map (see the module docstring), or None: nothing is held (the view is unavailable, the reading is withheld, or its rows or the vault cannot be digested).
- `still_current(view: Any, vault: Any, repository: Any, extraction_id: str, base: tuple[Any, ...] | None, *, full: bool) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 104) — Whether a value just computed under ``base`` may be held: its key read again now is still ``base``.
- `structure_key(repository: Any, digest: str | None, extraction_id: str, kind: str) -> tuple[Any, ...] | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 118) — The key of a value derived from a reading's stored structure alone (``MaterialView.section_spans``: no vault, no projection), or None when the reading has no digest (withheld, unavailable or unreadable).
- `held(key: Hashable | None, vault: Any) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 132) — The value held under ``key`` for this vault object (None: a value no vault is read for), or None.
- `hold(key: Hashable | None, vault: Any, value: Any) -> None` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 151) — Hold an immutable ``value`` under ``key`` for this vault object (weakly: a vault no longer loaded drops it; None: a value no vault is read for).
- `clear() -> None` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 169) — Drop every held mapping (tests; a held value is never stale, so production never needs it).

### Module constants

- `_HELD_LIMIT` ([src/learnloop/adaptive_difficulty/reading_cache.py](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 42)
- `_HELD` ([src/learnloop/adaptive_difficulty/reading_cache.py](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 43)
- `_LOCK` ([src/learnloop/adaptive_difficulty/reading_cache.py](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 44)

### Explicit exports

`__all__` declares:

- `base_key`
- `clear`
- `held`
- `hold`
- `still_current`
- `structure_key`
- `vault_digest`

## Internal implementation anchors

- `_extras(value: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 47)
- `_dump(ref: Any) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 52)
- `_owner(vault: Any) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 128)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `module`; statically calls `held`, `hold`, `structure_key`
- [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]] — imports `module`; statically calls `base_key`, `held`, `hold`, `still_current`, `vault_digest`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `learning_object_facet_union`; calls `learning_object_facet_union`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `json`, `pathlib`, `threading`, `typing`, `weakref`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]], [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_rospeed2_section_map.py](../../../../../../tests/test_rospeed2_section_map.py) — direct import
  - `test_a_failed_mapping_is_not_held`

## Modification guidance

- Make changes here when the responsibility remains reading cache within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/reading_cache.py](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
