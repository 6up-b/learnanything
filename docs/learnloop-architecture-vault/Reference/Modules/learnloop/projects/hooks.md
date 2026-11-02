---
title: "learnloop.projects.hooks"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/projects/hooks.py"
source_paths:
  - "src/learnloop/projects/hooks.py"
source_commit: "23ce6c39392057fe9b7ea2a8c22e6ae91a201597"
source_commit_timestamp: "2026-10-12T02:08:47-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.projects"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.projects.hooks module"
  - "src/learnloop/projects/hooks.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-projects"
---

# `learnloop.projects.hooks`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.projects.hooks` exists within [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] to own the behavior summarized by its module contract: The optional append-only ``post-commit`` hook (spec §3.1–3.2, P1, gate G1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/projects/hooks.py](../../../../../../src/learnloop/projects/hooks.py) |
| Source lines | 157 |
| Owning package | [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `23ce6c39392057fe9b7ea2a8c22e6ae91a201597` |
| Commit timestamp | `2026-10-12T02:08:47-04:00` |

## Public API

- `class HookError(RuntimeError)` ([source](../../../../../../src/learnloop/projects/hooks.py), line 45) — The hook cannot be installed or removed safely.
- `hook_markers(repo_id: str) -> tuple[str, str]` ([source](../../../../../../src/learnloop/projects/hooks.py), line 49)
- `hook_block(vault_root: Path, repo_id: str, work_tree: Path) -> str` ([source](../../../../../../src/learnloop/projects/hooks.py), line 56)
- `install_hook(vault_root: Path, store: ProjectStore, repo_row: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/projects/hooks.py), line 106)
- `uninstall_hook(store: ProjectStore, repo_row: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/projects/hooks.py), line 136)

### Module constants

- `HOOK_NAME` ([src/learnloop/projects/hooks.py](../../../../../../src/learnloop/projects/hooks.py), line 31)
- `HOOK_BEGIN` ([src/learnloop/projects/hooks.py](../../../../../../src/learnloop/projects/hooks.py), line 34)
- `HOOK_END` ([src/learnloop/projects/hooks.py](../../../../../../src/learnloop/projects/hooks.py), line 35)
- `_LEGACY_MARKERS` ([src/learnloop/projects/hooks.py](../../../../../../src/learnloop/projects/hooks.py), line 37)
- `_SHELL_SHEBANG` ([src/learnloop/projects/hooks.py](../../../../../../src/learnloop/projects/hooks.py), line 41)
- `_REPO_ID` ([src/learnloop/projects/hooks.py](../../../../../../src/learnloop/projects/hooks.py), line 42)

### Explicit exports

`__all__` declares:

- `HOOK_BEGIN`
- `HOOK_END`
- `HookError`
- `hook_block`
- `hook_markers`
- `install_hook`
- `uninstall_hook`

## Internal implementation anchors

- `_hooks_dir(repo: Path) -> Path` ([source](../../../../../../src/learnloop/projects/hooks.py), line 78)
- `_strip_block(text: str, repo_id: str) -> str` ([source](../../../../../../src/learnloop/projects/hooks.py), line 93) — Remove this registration's block (and a legacy unguarded one); keep the rest.
- `_has_block(text: str, repo_id: str) -> bool` ([source](../../../../../../src/learnloop/projects/hooks.py), line 102)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/project|learnloop.cli.project]] — imports `HookError`, `install_hook`, `uninstall_hook`; statically calls `install_hook`, `uninstall_hook`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/projects/experiment_store|learnloop.projects.experiment_store]] — imports `ProjectStore`, `pending_path`; calls `pending_path`
- [[Reference/Modules/learnloop/projects/git|learnloop.projects.git]] — imports `GitError`, `git_text`; calls `git_text`

### Platform and third-party dependencies

- Standard library: `__future__`, `os`, `pathlib`, `re`, `shlex`, `stat`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/project|learnloop.cli.project]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_project_hooks.py](../../../../../../tests/test_project_hooks.py) — direct import
  - `test_a_first_build_unguarded_block_is_replaced`
  - `test_existing_shell_hook_is_preserved_and_restored`
  - `test_hook_exits_zero_under_injected_failures`
  - `test_installed_hook_appends_one_line_per_commit`
  - `test_linked_worktrees_sharing_a_hook_each_log_their_own_commits`
  - `test_non_shell_hook_and_shared_hooks_path_are_refused`
  - `test_our_own_hook_is_removed_entirely`

## Modification guidance

- Make changes here when the responsibility remains hooks within learnloop.projects; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/projects/hooks.py](../../../../../../src/learnloop/projects/hooks.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
