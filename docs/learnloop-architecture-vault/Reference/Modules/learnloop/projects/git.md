---
title: "learnloop.projects.git"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/projects/git.py"
source_paths:
  - "src/learnloop/projects/git.py"
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
  - "learnloop.projects.git module"
  - "src/learnloop/projects/git.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-projects"
---

# `learnloop.projects.git`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.projects.git` exists within [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] to own the behavior summarized by its module contract: The only door to git: ``git -C <repo> ...`` with an argument list, no shell.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/projects/git.py](../../../../../../src/learnloop/projects/git.py) |
| Source lines | 141 |
| Owning package | [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class GitError(RuntimeError)` ([source](../../../../../../src/learnloop/projects/git.py), line 21) — A git command failed, timed out, or is unavailable.
- `run_git(repo: Path, args: Sequence[str], *, input_bytes: bytes | None=None, ok_codes: tuple[int, ...]=(0,), timeout: float=GIT_TIMEOUT_SECONDS) -> bytes` ([source](../../../../../../src/learnloop/projects/git.py), line 57) — Run ``git -C repo *args`` and return stdout bytes.
- `git_text(repo: Path, args: Sequence[str], **kwargs) -> str` ([source](../../../../../../src/learnloop/projects/git.py), line 93)
- `repo_toplevel(path: Path) -> Path` ([source](../../../../../../src/learnloop/projects/git.py), line 97) — The canonical work-tree root of the repo containing ``path``.
- `head_sha(repo: Path) -> str | None` ([source](../../../../../../src/learnloop/projects/git.py), line 108) — HEAD's commit id, or ``None`` for a repo without commits.
- `empty_tree_sha(repo: Path) -> str` ([source](../../../../../../src/learnloop/projects/git.py), line 117) — The empty tree's id in this repo's hash format (sha1 or sha256).
- `patch_id(repo: Path, diff_bytes: bytes) -> str | None` ([source](../../../../../../src/learnloop/projects/git.py), line 123) — ``git patch-id --stable`` of a diff: equal for rebased/cherry-picked copies.

### Module constants

- `GIT_TIMEOUT_SECONDS` ([src/learnloop/projects/git.py](../../../../../../src/learnloop/projects/git.py), line 16)
- `MAX_GIT_OUTPUT_BYTES` ([src/learnloop/projects/git.py](../../../../../../src/learnloop/projects/git.py), line 18)
- `_RETARGETING_VARIABLES` ([src/learnloop/projects/git.py](../../../../../../src/learnloop/projects/git.py), line 28)

### Explicit exports

`__all__` declares:

- `GIT_TIMEOUT_SECONDS`
- `GitError`
- `empty_tree_sha`
- `git_text`
- `head_sha`
- `patch_id`
- `repo_toplevel`
- `run_git`

## Internal implementation anchors

- `_environment() -> dict[str, str]` ([source](../../../../../../src/learnloop/projects/git.py), line 45)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/project|learnloop.cli.project]] — imports `GitError`, `repo_toplevel`; statically calls `repo_toplevel`
- [[Reference/Modules/learnloop/projects/capture|learnloop.projects.capture]] — imports `GitError`, `empty_tree_sha`, `git_text`, `head_sha`, `patch_id`, `repo_toplevel`, `run_git`; statically calls `GitError`, `empty_tree_sha`, `git_text`, `head_sha`, `patch_id`, `repo_toplevel`, `run_git`
- [[Reference/Modules/learnloop/projects/hooks|learnloop.projects.hooks]] — imports `GitError`, `git_text`; statically calls `git_text`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `os`, `pathlib`, `subprocess`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/project|learnloop.cli.project]], [[Reference/Modules/learnloop/projects/capture|learnloop.projects.capture]], [[Reference/Modules/learnloop/projects/hooks|learnloop.projects.hooks]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_project_cli.py](../../../../../../tests/test_project_cli.py) — imports consumer [[Reference/Modules/learnloop/cli/project|learnloop.cli.project]]
- [tests/test_project_experiment_store.py](../../../../../../tests/test_project_experiment_store.py) — imports consumer [[Reference/Modules/learnloop/cli/project|learnloop.cli.project]]
- [tests/test_project_atomicity.py](../../../../../../tests/test_project_atomicity.py) — imports consumer [[Reference/Modules/learnloop/projects/capture|learnloop.projects.capture]]
- [tests/test_project_blindness.py](../../../../../../tests/test_project_blindness.py) — imports consumer [[Reference/Modules/learnloop/projects/capture|learnloop.projects.capture]]
- [tests/test_project_capture.py](../../../../../../tests/test_project_capture.py) — imports consumer [[Reference/Modules/learnloop/projects/capture|learnloop.projects.capture]]
- [tests/test_project_hooks.py](../../../../../../tests/test_project_hooks.py) — imports consumer [[Reference/Modules/learnloop/projects/capture|learnloop.projects.capture]]
- [tests/test_project_probes.py](../../../../../../tests/test_project_probes.py) — imports consumer [[Reference/Modules/learnloop/projects/capture|learnloop.projects.capture]]
- [tests/test_project_redaction.py](../../../../../../tests/test_project_redaction.py) — imports consumer [[Reference/Modules/learnloop/projects/capture|learnloop.projects.capture]]
- [tests/test_project_report.py](../../../../../../tests/test_project_report.py) — imports consumer [[Reference/Modules/learnloop/projects/capture|learnloop.projects.capture]]
- [tests/test_t6_followup_review.py](../../../../../../tests/test_t6_followup_review.py) — imports consumer [[Reference/Modules/learnloop/projects/capture|learnloop.projects.capture]]

## Modification guidance

- Make changes here when the responsibility remains git within learnloop.projects; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/projects/git.py](../../../../../../src/learnloop/projects/git.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
