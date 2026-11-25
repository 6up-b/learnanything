---
title: "learnloop.learner.mastery_seed"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/mastery_seed.py"
source_paths:
  - "src/learnloop/learner/mastery_seed.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.learner"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Inspect Persistent State"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.learner.mastery_seed module"
  - "src/learnloop/learner/mastery_seed.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.mastery_seed`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.mastery_seed` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: Which seed a learning object's mastery starts from (mvp-0.67, the mastery seed a topic started from is recorded and replayed).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/mastery_seed.py](../../../../../../src/learnloop/learner/mastery_seed.py) |
| Source lines | 120 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `reconstructing_legacy_mastery_seeds() -> Iterator[dict[str, MasterySeedInputs]]` ([source](../../../../../../src/learnloop/learner/mastery_seed.py), line 44) — Collect, while the block runs, the seed the rebuild gives every learning object without a record (the first seed of each).
- `note_rebuilt_seed(learning_object_id: str, seed: MasterySeed) -> bool` ([source](../../../../../../src/learnloop/learner/mastery_seed.py), line 56) — Hand a rebuild's seed of an unrecorded learning object to the observation pass; whether one is running.
- `recorded_seed_for_replay(vault: LoadedVault, repository: Repository, learning_object_id: str) -> MasterySeedInputs | None` ([source](../../../../../../src/learnloop/learner/mastery_seed.py), line 69) — The seed recorded for a replayed learning object (None below the tag, or where none was recorded).
- `materialize_mastery(vault: LoadedVault, repository: Repository, learning_object_id: str, now_iso: str) -> bool` ([source](../../../../../../src/learnloop/learner/mastery_seed.py), line 77) — Vault sync's first persistence of a learning object's mastery at the tag; whether it wrote a row.
- `attempt_seed_capture(vault: LoadedVault, learning_object_id: str, seed: MasterySeed | None, *, replay: bool, now_iso: str) -> MasterySeedInputs | None` ([source](../../../../../../src/learnloop/learner/mastery_seed.py), line 99) — The seed record an attempt's own write carries: the seed its prior was built from when its learning object had no row (a live application at the tag); None otherwise.

### Module constants

- `_RECONSTRUCTING` ([src/learnloop/learner/mastery_seed.py](../../../../../../src/learnloop/learner/mastery_seed.py), line 40)

### Explicit exports

`__all__` declares:

- `attempt_seed_capture`
- `materialize_mastery`
- `note_rebuilt_seed`
- `reconstructing_legacy_mastery_seeds`
- `recorded_seed_for_replay`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `attempt_seed_capture`; statically calls `attempt_seed_capture`
- [[Reference/Modules/learnloop/ops/upgrades|learnloop.ops.upgrades]] — imports `reconstructing_legacy_mastery_seeds`; statically calls `reconstructing_legacy_mastery_seeds`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `note_rebuilt_seed`, `recorded_seed_for_replay`; statically calls `note_rebuilt_seed`, `recorded_seed_for_replay`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `note_rebuilt_seed`, `recorded_seed_for_replay`; statically calls `note_rebuilt_seed`, `recorded_seed_for_replay`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `materialize_mastery`; statically calls `materialize_mastery`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `mastery_seed_on`; calls `mastery_seed_on`
- [[Reference/Modules/learnloop/db/mastery_seed_inputs|learnloop.db.mastery_seed_inputs]] — imports `BASIS_LEGACY_RECONSTRUCTED`, `MasterySeedInputs`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `MasterySeed`, `live_seed_inputs`, `recorded_seed_state`, `seed_for_learning_object`; calls `live_seed_inputs`, `recorded_seed_state`, `seed_for_learning_object`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `contextvars`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/ops/upgrades|learnloop.ops.upgrades]], [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]], [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]], [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/helpers.py](../../../../../../tests/helpers.py) — direct import

## Modification guidance

- Change mastery seed policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/mastery_seed.py](../../../../../../src/learnloop/learner/mastery_seed.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
