---
title: "learnloop.bootstrap"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/bootstrap.py"
source_paths:
  - "src/learnloop/bootstrap.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop"
layer: "coordination"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.bootstrap module"
  - "src/learnloop/bootstrap.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/coordination"
  - "package/learnloop"
---

# `learnloop.bootstrap`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.bootstrap` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: Application-level vault creation shared by the CLI and sidecar.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/bootstrap.py](../../../../../src/learnloop/bootstrap.py) |
| Source lines | 186 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `coordination` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class BootstrapError(ValueError)` ([source](../../../../../src/learnloop/bootstrap.py), line 30) — A validated vault-creation refusal with a stable adapter-facing code.
  - `__init__(self, code: str, message: str) -> None` (line 33; internal)
- `class CreateVaultResult` ([source](../../../../../src/learnloop/bootstrap.py), line 39)
- `create_vault(root: Path | str, *, subject: str | None=None, starting_level: str | None=None, level_note: str | None=None, inherit_ai_from: Path | None=None, force: bool=False, clock: Clock | None=None) -> CreateVaultResult` ([source](../../../../../src/learnloop/bootstrap.py), line 53) — Create or complete a vault after validating every input.

## Internal implementation anchors

- `class _ValidatedRequest` ([source](../../../../../src/learnloop/bootstrap.py), line 45)
- `_validate_request(root: Path | str, *, subject: str | None, starting_level: str | None, force: bool) -> _ValidatedRequest` ([source](../../../../../src/learnloop/bootstrap.py), line 108)
- `_inherit_ai_settings(root: Path, *, inherit_ai_from: Path | None) -> None` ([source](../../../../../src/learnloop/bootstrap.py), line 167)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `BootstrapError`, `create_vault`; statically calls `create_vault`
- [[Reference/Modules/learnloop_sidecar/handlers/vault|learnloop_sidecar.handlers.vault]] — imports `BootstrapError`, `create_vault`; statically calls `create_vault`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `global_ai_defaults_path`, `load_config`; calls `global_ai_defaults_path`, `load_config`
- [[Reference/Modules/learnloop/content/synthesis/brief|learnloop.content.synthesis.brief]] — imports `STARTING_LEVELS`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `kebab_case`; calls `kebab_case`
- [[Reference/Modules/learnloop/learner/learner_profile|learnloop.learner.learner_profile]] — imports `seed_global_learner_claim`, `write_learner_profile`; calls `seed_global_learner_claim`, `write_learner_profile`
- [[Reference/Modules/learnloop/ops/settings_store|learnloop.ops.settings_store]] — imports `SettingsStoreError`, `copy_ai_settings`; calls `copy_ai_settings`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `add_subject`, `init_vault`; calls `add_subject`, `init_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `open_vault_repository`; calls `open_vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `logging`, `pathlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop_sidecar/handlers/vault|learnloop_sidecar.handlers.vault]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_init.py](../../../../../tests/test_init.py) — direct import
  - `test_bootstrap_completes_partial_vault_without_touching_config`
  - `test_bootstrap_seeds_subject_and_starting_level`
  - `test_bootstrap_validates_request_before_writing`

## Modification guidance

- Make changes here when the responsibility remains bootstrap within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/bootstrap.py](../../../../../src/learnloop/bootstrap.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
