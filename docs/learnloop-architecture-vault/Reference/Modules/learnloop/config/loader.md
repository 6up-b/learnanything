---
title: "learnloop.config.loader"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/config/loader.py"
source_paths:
  - "src/learnloop/config/loader.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.config"
layer: "infrastructure"
concepts:
  - "Configuration"
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.config.loader module"
  - "src/learnloop/config/loader.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-config"
---

# `learnloop.config.loader`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/config/_package|learnloop.config]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.config.loader` exists within [[Reference/Modules/learnloop/config/_package|learnloop.config]] to own the behavior summarized by its module contract: TOML, dotenv, and environment-backed configuration loading.

The authoritative system-level explanation remains in [[Configuration]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/config/loader.py](../../../../../../src/learnloop/config/loader.py) |
| Source lines | 166 |
| Owning package | [[Reference/Modules/learnloop/config/_package|learnloop.config]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ConfigLoadError(ValueError)` ([source](../../../../../../src/learnloop/config/loader.py), line 25)
  - `__init__(self, path: Path, message: str)` (line 26; internal)
- `global_settings_path() -> Path` ([source](../../../../../../src/learnloop/config/loader.py), line 31) — Return the machine-global LearnLoop settings environment file.
- `global_ai_defaults_path() -> Path` ([source](../../../../../../src/learnloop/config/loader.py), line 44) — Return the machine-global default AI provider selection file.
- `load_config(path: Path) -> LearnLoopConfig` ([source](../../../../../../src/learnloop/config/loader.py), line 50) — Load, compatibility-normalize, validate, and environment-overlay TOML.
- `load_dotenv(path: Path) -> None` ([source](../../../../../../src/learnloop/config/loader.py), line 67) — Load environment variables without overriding the current process.

### Module constants

- `ENV_KEY_RE` ([src/learnloop/config/loader.py](../../../../../../src/learnloop/config/loader.py), line 21)
- `CODEX_CHECKOUT_ENV` ([src/learnloop/config/loader.py](../../../../../../src/learnloop/config/loader.py), line 22)

### Explicit exports

`__all__` declares:

- `CODEX_CHECKOUT_ENV`
- `ConfigLoadError`
- `ENV_KEY_RE`
- `global_ai_defaults_path`
- `global_settings_path`
- `load_config`
- `load_dotenv`
- `write_default_config`

## Internal implementation anchors

- `_apply_global_overrides(config: LearnLoopConfig) -> LearnLoopConfig` ([source](../../../../../../src/learnloop/config/loader.py), line 87) — Overlay per-machine settings after the vault model is validated.
- `_format_toml_error(path: Path, exc: tomllib.TOMLDecodeError) -> str` ([source](../../../../../../src/learnloop/config/loader.py), line 103)
- `_windows_path_hint(path: Path, exc: tomllib.TOMLDecodeError) -> str | None` ([source](../../../../../../src/learnloop/config/loader.py), line 109)
- `_line_number_from_toml_error(message: str) -> int | None` ([source](../../../../../../src/learnloop/config/loader.py), line 134)
- `_line_at(text: str, line_number: int | None) -> str | None` ([source](../../../../../../src/learnloop/config/loader.py), line 139)
- `_parse_dotenv_value(value: str) -> str` ([source](../../../../../../src/learnloop/config/loader.py), line 148)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/compat|learnloop.config.compat]] — imports `normalize_config_input`; calls `normalize_config_input`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `CODEX_LOW_PROVIDER`, `CODEX_MEDIUM_PROVIDER`, `CodexHTTPProviderConfig`, `CodexSDKProviderConfig`, `LearnLoopConfig`
- [[Reference/Modules/learnloop/config/template|learnloop.config.template]] — imports `write_default_config`

### Platform and third-party dependencies

- Standard library: `__future__`, `os`, `pathlib`, `re`, `tomllib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/config/__init__|learnloop.config]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_config_refactor.py](../../../../../../tests/test_config_refactor.py) — direct import
  - `test_config_responsibilities_have_canonical_module_owners`
  - `test_loader_orchestrates_compatibility_before_validation`

## Modification guidance

- Change configuration behavior in the schema, loader, compatibility normalizer, or template owner that matches the concern; preserve one-way legacy normalization.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/config/loader.py](../../../../../../src/learnloop/config/loader.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
