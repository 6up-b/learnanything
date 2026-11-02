---
title: "learnloop.config.loader"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/config/loader.py"
source_paths:
  - "src/learnloop/config/loader.py"
source_commit: "f09025d6030d92da795398ff7dba042d44faef93"
source_commit_timestamp: "2026-10-12T15:32:17-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
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
| Source lines | 172 |
| Owning package | [[Reference/Modules/learnloop/config/_package|learnloop.config]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `f09025d6030d92da795398ff7dba042d44faef93` |
| Commit timestamp | `2026-10-12T15:32:17-04:00` |

## Public API

- `class ConfigLoadError(ValueError)` ([source](../../../../../../src/learnloop/config/loader.py), line 26)
  - `__init__(self, path: Path, message: str)` (line 27; internal)
- `global_settings_path() -> Path` ([source](../../../../../../src/learnloop/config/loader.py), line 32) — Return the machine-global LearnLoop settings environment file.
- `global_ai_defaults_path() -> Path` ([source](../../../../../../src/learnloop/config/loader.py), line 45) — Return the machine-global default AI provider selection file.
- `load_config(path: Path, *, load_environment: bool=True) -> LearnLoopConfig` ([source](../../../../../../src/learnloop/config/loader.py), line 51) — Load TOML, optionally without dotenv files or machine-specific overlays.
- `load_dotenv(path: Path) -> None` ([source](../../../../../../src/learnloop/config/loader.py), line 73) — Load environment variables without overriding the current process.

### Module constants

- `ENV_KEY_RE` ([src/learnloop/config/loader.py](../../../../../../src/learnloop/config/loader.py), line 22)
- `CODEX_CHECKOUT_ENV` ([src/learnloop/config/loader.py](../../../../../../src/learnloop/config/loader.py), line 23)

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

- `_apply_global_overrides(config: LearnLoopConfig) -> LearnLoopConfig` ([source](../../../../../../src/learnloop/config/loader.py), line 93) — Overlay per-machine settings after the vault model is validated.
- `_format_toml_error(path: Path, exc: tomllib.TOMLDecodeError) -> str` ([source](../../../../../../src/learnloop/config/loader.py), line 109)
- `_windows_path_hint(path: Path, exc: tomllib.TOMLDecodeError) -> str | None` ([source](../../../../../../src/learnloop/config/loader.py), line 115)
- `_line_number_from_toml_error(message: str) -> int | None` ([source](../../../../../../src/learnloop/config/loader.py), line 140)
- `_line_at(text: str, line_number: int | None) -> str | None` ([source](../../../../../../src/learnloop/config/loader.py), line 145)
- `_parse_dotenv_value(value: str) -> str` ([source](../../../../../../src/learnloop/config/loader.py), line 154)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/chatgpt_plan/store|learnloop.ai.chatgpt_plan.store]] — imports `global_settings_path`; statically calls `global_settings_path`
- [[Reference/Modules/learnloop/ai/providers/openrouter_catalog|learnloop.ai.providers.openrouter_catalog]] — imports `global_settings_path`; statically calls `global_settings_path`
- [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]] — imports `load_config`; statically calls `load_config`
- [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]] — imports `global_settings_path`, `load_dotenv`; statically calls `global_settings_path`, `load_dotenv`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `module`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `load_config`; statically calls `load_config`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `load_config`; statically calls `load_config`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `load_config`; statically calls `load_config`
- [[Reference/Modules/learnloop/remote/runtime|learnloop.remote.runtime]] — imports `load_config`; statically calls `load_config`
- [[Reference/Modules/learnloop/symbolic_view|learnloop.symbolic_view]] — imports `load_config`; statically calls `load_config`
- [[Reference/Modules/learnloop/tui/minutes_memory|learnloop.tui.minutes_memory]] — imports `global_settings_path`; statically calls `global_settings_path`
- [[Reference/Modules/learnloop_sidecar/handlers/capture|learnloop_sidecar.handlers.capture]] — imports `global_settings_path`; statically calls `global_settings_path`

### Repository tooling consumers

- [scripts/s0_landing.py](../../../../../../scripts/s0_landing.py); calls `load_config`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/compat|learnloop.config.compat]] — imports `normalize_config_input`; calls `normalize_config_input`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `CODEX_LOW_PROVIDER`, `CODEX_LUNA_PROVIDER`, `CODEX_MEDIUM_PROVIDER`, `CodexHTTPProviderConfig`, `CodexSDKProviderConfig`, `LearnLoopConfig`
- [[Reference/Modules/learnloop/config/template|learnloop.config.template]] — imports `write_default_config`

### Platform and third-party dependencies

- Standard library: `__future__`, `os`, `pathlib`, `re`, `tomllib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/chatgpt_plan/store|learnloop.ai.chatgpt_plan.store]], [[Reference/Modules/learnloop/ai/providers/openrouter_catalog|learnloop.ai.providers.openrouter_catalog]], [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]], [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]], [[Reference/Modules/learnloop/config/__init__|learnloop.config]] and 7 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_config_refactor.py](../../../../../../tests/test_config_refactor.py) — direct import
  - `test_config_responsibilities_have_canonical_module_owners`
  - `test_loader_orchestrates_compatibility_before_validation`
- [tests/test_coverage_on_extract.py](../../../../../../tests/test_coverage_on_extract.py) — direct import
  - `test_an_extraction_queues_the_job_only_while_both_switches_are_on`
  - `test_one_live_job_at_a_time`
- [tests/test_deliverable_codex_review.py](../../../../../../tests/test_deliverable_codex_review.py) — direct import
  - `test_f7_a_running_job_does_not_swallow_a_new_extraction`
- [tests/test_e0_review_round6.py](../../../../../../tests/test_e0_review_round6.py) — direct import
  - `test_m1_no_e0_vault_load_reads_settings_env_or_a_copy_dotenv`
- [tests/test_field_config.py](../../../../../../tests/test_field_config.py) — direct import
  - `test_offline_config_never_opens_dotenv_or_global_settings`
- [tests/test_local_index.py](../../../../../../tests/test_local_index.py) — direct import
  - `test_an_index_obligation_that_cannot_be_queued_fails_the_extraction_retryably`
  - `test_extraction_queues_the_index_jobs_only_while_their_switches_are_on`
- [tests/test_notes_vault_search.py](../../../../../../tests/test_notes_vault_search.py) — direct import
  - `test_a_legacy_tend_table_in_an_existing_config_is_ignored`
- [tests/test_success_head_cli.py](../../../../../../tests/test_success_head_cli.py) — direct import
- [tests/test_voyage_fallback.py](../../../../../../tests/test_voyage_fallback.py) — direct import
  - `test_every_ai_task_refuses_the_fallback_profile`

## Modification guidance

- Change configuration behavior in the schema, loader, compatibility normalizer, or template owner that matches the concern; preserve one-way legacy normalization.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/config/loader.py](../../../../../../src/learnloop/config/loader.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
