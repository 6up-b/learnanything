---
title: "learnloop.curriculum.golden_path_compose"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/curriculum/golden_path_compose.py"
source_paths:
  - "src/learnloop/curriculum/golden_path_compose.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.curriculum"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Build a Study Map"
aliases:
  - "learnloop.curriculum.golden_path_compose module"
  - "src/learnloop/curriculum/golden_path_compose.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-curriculum"
---

# `learnloop.curriculum.golden_path_compose`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.curriculum.golden_path_compose` exists within [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] to own the behavior summarized by its module contract: Compose a real, registrable golden-path blueprint draft from vault items.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/curriculum/golden_path_compose.py](../../../../../../src/learnloop/curriculum/golden_path_compose.py) |
| Source lines | 214 |
| Owning package | [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ComposeError(ValueError)` ([source](../../../../../../src/learnloop/curriculum/golden_path_compose.py), line 25) — The picker selection cannot compose into a valid single-unit blueprint.
- `discover_exemplar_pool(vault: LoadedVault, repository: Repository, *, learning_object_id: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/curriculum/golden_path_compose.py), line 29) — The picker data: learning objects with their active items and freshness.
- `compose_blueprint_draft(vault: LoadedVault, repository: Repository, *, learning_object_id: str, anchor_item_ids: Sequence[str], held_out_item_id: str, title: str | None=None, source_rev: str | None=None, unit_id: str | None=None, family_key: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/golden_path_compose.py), line 73) — Project a picker selection into ``{spec, contract_body, ...}`` ready for ``register_blueprint_version`` + ``confirm_exemplar_and_start``.

### Module constants

- `DEFAULT_ADMINISTRATION` ([src/learnloop/curriculum/golden_path_compose.py](../../../../../../src/learnloop/curriculum/golden_path_compose.py), line 22)

## Internal implementation anchors

- `_rubric_for(item: PracticeItem) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/golden_path_compose.py), line 207)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/golden_path|learnloop_sidecar.handlers.golden_path]] — imports `module`; statically calls `compose_blueprint_draft`, `discover_exemplar_pool`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/golden_path|learnloop_sidecar.handlers.golden_path]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No direct or one-hop consumer test was found by static import analysis.

> [!caution] Test gap signal
> Treat this as a navigation signal, not proof that behavior is untested: dynamic and higher-level coverage is outside this static map. Add focused coverage when changing isolated behavior here.

## Modification guidance

- Change golden path compose policy here when curriculum owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/curriculum/golden_path_compose.py](../../../../../../src/learnloop/curriculum/golden_path_compose.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
