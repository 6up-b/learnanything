---
title: "learnloop.substrate.compat"
type: "module-reference"
status: "current"
refactor_status: "COMPAT"
version: "1.0.0"
source_path: "src/learnloop/substrate/compat/__init__.py"
source_paths:
  - "src/learnloop/substrate/compat/__init__.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.substrate.compat"
layer: "domain"
concepts:
  - "Learning System"
  - "State and Persistence"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.substrate.compat module"
  - "src/learnloop/substrate/compat/__init__.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/compat"
  - "layer/domain"
  - "package/learnloop-substrate-compat"
---

# `learnloop.substrate.compat`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/compat/_package|learnloop.substrate.compat]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.compat` exists within [[Reference/Modules/learnloop/substrate/compat/_package|learnloop.substrate.compat]] to own the behavior summarized by its module contract: Frozen compatibility machinery for historical LearnLoop vaults.

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/compat/__init__.py](../../../../../../../src/learnloop/substrate/compat/__init__.py) |
| Source lines | 1 |
| Owning package | [[Reference/Modules/learnloop/substrate/compat/_package|learnloop.substrate.compat]] |
| Architecture layer | `domain` |
| Refactor status | `COMPAT` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

> [!warning] Frozen compatibility boundary
> This live module is retained for old vaults. It is green but not a target for new feature growth.

## Public API

No public top-level function or class definition is declared in this file.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

No live LearnLoop module directly imports this module in the static graph.

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: none imported directly
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

No live LearnLoop module imports it directly; its current reach is tests, repository tooling, dynamic registration, or explicit manual invocation where documented above.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No direct or one-hop consumer test was found by static import analysis.

> [!caution] Test gap signal
> Treat this as a navigation signal, not proof that behavior is untested: dynamic and higher-level coverage is outside this static map. Add focused coverage when changing isolated behavior here.

## Modification guidance

- Change this file when intentionally adding or removing a package-level re-export; keep implementation logic in the owning module.
- This is frozen old-vault compatibility code: do not extend it without an explicit compatibility decision and fixture-backed tests.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/compat/__init__.py](../../../../../../../src/learnloop/substrate/compat/__init__.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
