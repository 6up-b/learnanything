---
title: "learnloop.adaptive_difficulty.reading_cache"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/reading_cache.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/reading_cache.py"
source_commit: "e820e0798856930f39b48cfeeeda9aa79f4ba8d2"
source_commit_timestamp: "2026-11-07T05:01:30-05:00"
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
| Source lines | 242 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e820e0798856930f39b48cfeeeda9aa79f4ba8d2` |
| Commit timestamp | `2026-11-07T05:01:30-05:00` |

## Public API

- `commit_version(repository: Any) -> tuple[Any, ...] | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 57) — The database's commit version as a read-only watcher sees it (``PRAGMA data_version``, which moves whenever another connection commits, and the watcher's own ``total_changes``; the pattern of ``objective_inputs.
- `held_on(config: Any) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 101) — ``[router_objective] held_reading_map`` at the follow-up batch's tag with the objective serving (router speed stage 2's Codex review F2): the map's values are the same either way, but held they cost less, so the objective job's input builds finish sooner and a deadline-bound ref…
- `vault_digest(vault: Any) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 123) — A digest of everything ``section_map.learning_objects_for_section_in_ir`` reads of ``vault``: every LO's id, status and provenance references, each facet of its blueprints' union with its canonical id and that facet's references, and every note's id and canonical source (``canon…
- `base_key(view: Any, vault: Any, repository: Any, extraction_id: str, *, vault_key: str | None) -> tuple[Any, ...] | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 152) — The key a reading's held values share in one map (see the module docstring), or None: nothing is held (the view is unavailable, the reading is withheld, or its rows or the vault cannot be digested).
- `still_current(view: Any, vault: Any, repository: Any, extraction_id: str, base: tuple[Any, ...] | None, *, full: bool) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 170) — Whether a value just computed under ``base`` may be held: its key read again now is still ``base``.
- `structure_key(repository: Any, digest: str | None, extraction_id: str, kind: str) -> tuple[Any, ...] | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 184) — The key of a value derived from a reading's stored structure alone (``MaterialView.section_spans``: no vault, no projection), or None when the reading has no digest (withheld, unavailable or unreadable).
- `held(key: Hashable | None, vault: Any) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 198) — The value held under ``key`` for this vault object (None: a value no vault is read for), or None.
- `hold(key: Hashable | None, vault: Any, value: Any) -> None` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 217) — Hold an immutable ``value`` under ``key`` for this vault object (weakly: a vault no longer loaded drops it; None: a value no vault is read for).
- `clear() -> None` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 235) — Drop every held mapping (tests; a held value is never stale, so production never needs it).

### Module constants

- `_HELD_LIMIT` ([src/learnloop/adaptive_difficulty/reading_cache.py](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 48)
- `_HELD` ([src/learnloop/adaptive_difficulty/reading_cache.py](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 49)
- `_LOCK` ([src/learnloop/adaptive_difficulty/reading_cache.py](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 50)
- `_WATCHERS` ([src/learnloop/adaptive_difficulty/reading_cache.py](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 53)
- `_WATCH_LOCK` ([src/learnloop/adaptive_difficulty/reading_cache.py](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 54)

### Explicit exports

`__all__` declares:

- `base_key`
- `clear`
- `commit_version`
- `held`
- `held_on`
- `hold`
- `still_current`
- `structure_key`
- `vault_digest`

## Internal implementation anchors

- `_extras(value: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 113)
- `_dump(ref: Any) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 118)
- `_owner(vault: Any) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 194)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `module`; statically calls `held`, `held_on`, `hold`, `structure_key`
- [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]] — imports `module`; statically calls `base_key`, `commit_version`, `held`, `held_on`, `hold`, `still_current`, `vault_digest`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `followup_on`; calls `followup_on`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `learning_object_facet_union`; calls `learning_object_facet_union`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `json`, `os`, `pathlib`, `sqlite3`, `threading`, `typing`, `weakref`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]], [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_rospeed2_connections.py](../../../../../../tests/test_rospeed2_connections.py) — direct import
  - `test_the_pool_and_the_held_map_follow_their_switches`
  - `test_the_pool_completes_more_draws_by_one_deadline_and_switched_off_is_mains`
- [tests/test_rospeed2_section_map.py](../../../../../../tests/test_rospeed2_section_map.py) — direct import
  - `test_a_failed_mapping_is_not_held`
  - `test_switched_off_the_map_is_mains_and_reads_nothing_of_the_hold`

## Modification guidance

- Make changes here when the responsibility remains reading cache within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/reading_cache.py](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
