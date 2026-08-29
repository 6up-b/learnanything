---
title: "learnloop.ops.settings_store"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/settings_store.py"
source_paths:
  - "src/learnloop/ops/settings_store.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.ops"
layer: "domain"
concepts:
  - "State and Persistence"
  - "Configuration"
workflows:
  - "Configure AI Providers"
aliases:
  - "learnloop.ops.settings_store module"
  - "src/learnloop/ops/settings_store.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops"
---

# `learnloop.ops.settings_store`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ops.settings_store` exists within [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] to own the behavior summarized by its module contract: Persistence for the Settings tab.

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/settings_store.py](../../../../../../src/learnloop/ops/settings_store.py) |
| Source lines | 294 |
| Owning package | [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class SettingsStoreError(ValueError)` ([source](../../../../../../src/learnloop/ops/settings_store.py), line 30)
  - `__init__(self, code: str, message: str)` (line 31; internal)
- `openrouter_profile_name(use_case: str) -> str` ([source](../../../../../../src/learnloop/ops/settings_store.py), line 46)
- `openrouter_task_profile_values(base: AIProviderConfig, model: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/settings_store.py), line 50) — Concrete keys for a per-use-case OpenRouter profile cloned from ``base``.
- `apply_config_updates(config_path: Path, updates: Mapping[tuple[str, ...], Any]) -> None` ([source](../../../../../../src/learnloop/ops/settings_store.py), line 75) — Set dotted key-paths in ``learnloop.toml``, preserving comments/layout.
- `remove_config_paths(config_path: Path, key_paths: tuple[tuple[str, ...], ...]) -> tuple[tuple[str, ...], ...]` ([source](../../../../../../src/learnloop/ops/settings_store.py), line 118) — Remove retired config keys/tables with atomic, comment-preserving edits.
- `copy_ai_settings(source_path: Path, target_path: Path) -> bool` ([source](../../../../../../src/learnloop/ops/settings_store.py), line 168) — Copy the persisted ``[ai]`` provider selection from one vault's ``learnloop.toml`` into another's.
- `save_ai_settings_to(source_path: Path, target_path: Path) -> bool` ([source](../../../../../../src/learnloop/ops/settings_store.py), line 222) — Mirror a vault's ``[ai]`` selection into ``target_path``, creating the target (and its parent dir) if absent.
- `upsert_env_var(path: Path, key: str, value: str | None) -> None` ([source](../../../../../../src/learnloop/ops/settings_store.py), line 246) — Set (or remove, when ``value`` is None) ``KEY=value`` in a dotenv file.

### Module constants

- `USE_CASE_ROUTES` ([src/learnloop/ops/settings_store.py](../../../../../../src/learnloop/ops/settings_store.py), line 38)

## Internal implementation anchors

- `_flatten_into_updates(prefix: tuple[str, ...], table: Mapping[str, Any], updates: dict[tuple[str, ...], Any]) -> None` ([source](../../../../../../src/learnloop/ops/settings_store.py), line 236)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/bootstrap|learnloop.bootstrap]] — imports `SettingsStoreError`, `copy_ai_settings`; statically calls `copy_ai_settings`
- [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]] — imports `SettingsStoreError`, `USE_CASE_ROUTES`, `apply_config_updates`, `openrouter_profile_name`, `openrouter_task_profile_values`, `save_ai_settings_to`, `upsert_env_var`; statically calls `apply_config_updates`, `openrouter_profile_name`, `openrouter_task_profile_values`, `save_ai_settings_to`, `upsert_env_var`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `AIProviderConfig`, `CODEX_PROVIDER_NAMES`, `ENV_KEY_RE`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `os`, `pathlib`, `tomllib`, `typing`
- Third party: `tomlkit`

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]

Static participation evidence comes from [[Reference/Modules/learnloop/bootstrap|learnloop.bootstrap]], [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ingest_runner.py](../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_default_synthesis_client_resolves_openrouter_in_inherited_new_vault`
  - `test_explicit_transcription_route_uses_named_profile_without_legacy_switch`
  - `test_native_route_takes_precedence_over_openrouter_transcription_setting`
  - `test_routed_transcription_keeps_the_chat_upload_size_cap`
  - `test_transcription_route_never_falls_back_to_an_unconsented_provider`
- [tests/test_settings_store.py](../../../../../../tests/test_settings_store.py) — direct import
  - `test_apply_config_updates_creates_missing_tables`
  - `test_apply_config_updates_is_atomic_on_parse_failure`
  - `test_apply_config_updates_missing_file`
  - `test_apply_config_updates_preserves_comments_and_unrelated_lines`
  - `test_copy_ai_settings_copies_routing_and_materialized_profiles`
  - `test_copy_ai_settings_default_source_is_semantic_noop`
  - `test_copy_ai_settings_errors_on_missing_or_invalid_source`
  - `test_openrouter_task_profile_values_round_trip`
  - `test_remove_config_paths_removes_retired_table_and_is_idempotent`
  - `test_save_ai_settings_to_creates_target_and_seeds_new_vault`
  - `test_upsert_env_var_appends_and_replaces_preserving_other_lines`
  - `test_upsert_env_var_rejects_bad_names_and_newlines`
  - `test_upsert_env_var_removes_key_on_none_and_creates_parents`
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — direct import
  - `test_update_ingest_settings_transcription_provider_switch`

## Modification guidance

- Make changes here when the responsibility remains settings store within learnloop.ops; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/settings_store.py](../../../../../../src/learnloop/ops/settings_store.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
