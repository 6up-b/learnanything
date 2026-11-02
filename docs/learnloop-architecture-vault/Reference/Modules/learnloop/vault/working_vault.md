---
title: "learnloop.vault.working_vault"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/vault/working_vault.py"
source_paths:
  - "src/learnloop/vault/working_vault.py"
source_commit: "fcfe9df917fd00f4935ff5fb5b4ad65a32424627"
source_commit_timestamp: "2026-10-25T02:47:46-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.vault"
layer: "infrastructure"
concepts:
  - "State and Persistence"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.vault.working_vault module"
  - "src/learnloop/vault/working_vault.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-vault"
---

# `learnloop.vault.working_vault`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.vault.working_vault` exists within [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] to own the behavior summarized by its module contract: An explicit mark on the owner's live working vaults (storage S0).

The authoritative system-level explanation remains in [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/vault/working_vault.py](../../../../../../src/learnloop/vault/working_vault.py) |
| Source lines | 73 |
| Owning package | [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `fcfe9df917fd00f4935ff5fb5b4ad65a32424627` |
| Commit timestamp | `2026-10-25T02:47:46-04:00` |

## Public API

- `marker_path(root: Path) -> Path` ([source](../../../../../../src/learnloop/vault/working_vault.py), line 28)
- `mark_working_vault(root: Path, *, reason: str) -> Path` ([source](../../../../../../src/learnloop/vault/working_vault.py), line 32) — Mark ``root`` as a live working vault (idempotent; rewrites the identity).
- `working_vault_marker_reason(root: Path) -> str | None` ([source](../../../../../../src/learnloop/vault/working_vault.py), line 53) — Why ``root`` is a marked live working vault, or None (no mark, or a copy's).

### Module constants

- `MARKER_PARTS` ([src/learnloop/vault/working_vault.py](../../../../../../src/learnloop/vault/working_vault.py), line 25)

### Explicit exports

`__all__` declares:

- `MARKER_PARTS`
- `mark_working_vault`
- `marker_path`
- `working_vault_marker_reason`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]] — imports `working_vault_marker_reason`; statically calls `working_vault_marker_reason`

### Repository tooling consumers

- [scripts/s0_landing.py](../../../../../../scripts/s0_landing.py); calls `mark_working_vault`, `working_vault_marker_reason`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `json`, `os`, `pathlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ai_compare.py](../../../../../../tests/test_ai_compare.py) — direct import
  - `test_a_live_vault_moved_out_of_git_is_still_refused_and_its_copy_is_compared`
  - `test_an_unreadable_working_vault_mark_refuses`
- [tests/test_s0_landing.py](../../../../../../tests/test_s0_landing.py) — direct import
  - `test_the_full_procedure_passes_and_never_changes_the_sources_before_the_move`

## Modification guidance

- Make changes here when the responsibility remains working vault within learnloop.vault; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/vault/working_vault.py](../../../../../../src/learnloop/vault/working_vault.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
