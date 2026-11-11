---
title: "learnloop.config.compat"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/config/compat.py"
source_paths:
  - "src/learnloop/config/compat.py"
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
  - "learnloop.config.compat module"
  - "src/learnloop/config/compat.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-config"
---

# `learnloop.config.compat`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/config/_package|learnloop.config]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.config.compat` exists within [[Reference/Modules/learnloop/config/_package|learnloop.config]] to own the behavior summarized by its module contract: One-way normalization of legacy configuration.

The authoritative system-level explanation remains in [[Configuration]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/config/compat.py](../../../../../../src/learnloop/config/compat.py) |
| Source lines | 282 |
| Owning package | [[Reference/Modules/learnloop/config/_package|learnloop.config]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `discard_retired_provider_settings(data: Any) -> Any` ([source](../../../../../../src/learnloop/config/compat.py), line 54) — Drop provider keys that were parsed historically but never consumed.
- `normalize_provider_profile(value: Any) -> Any` ([source](../../../../../../src/learnloop/config/compat.py), line 64) — Canonicalize provider type aliases before union discrimination.
- `normalize_ai_input(data: Any) -> Any` ([source](../../../../../../src/learnloop/config/compat.py), line 77) — Normalize every named provider while preserving non-mapping inputs.
- `normalize_config_input(data: Any) -> Any` ([source](../../../../../../src/learnloop/config/compat.py), line 92) — Translate accepted legacy shapes into the canonical schema input.
- `codex_profile_value(config: Any, field: str) -> Any` ([source](../../../../../../src/learnloop/config/compat.py), line 203) — The ``codex`` profile's ``field``, or the old runtime view's default for it.

### Module constants

- `_PROVIDER_TYPE_ALIASES` ([src/learnloop/config/compat.py](../../../../../../src/learnloop/config/compat.py), line 18)
- `_LEGACY_CODEX_TABLE_DEFAULTS` ([src/learnloop/config/compat.py](../../../../../../src/learnloop/config/compat.py), line 29)

### Explicit exports

`__all__` declares:

- `codex_profile_value`
- `discard_retired_provider_settings`
- `normalize_ai_input`
- `normalize_config_input`
- `normalize_provider_profile`

## Internal implementation anchors

- `_provider_profile_from_legacy_codex(value: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/config/compat.py), line 215)
- `_profile_from_legacy_openrouter_audio(audio: dict[str, Any], providers: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/config/compat.py), line 223)
- `_normalize_codex_aliases(ai: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/config/compat.py), line 246)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `codex_profile_value`; statically calls `codex_profile_value`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `module`
- [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]] — imports `normalize_config_input`; statically calls `normalize_config_input`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `discard_retired_provider_settings`, `normalize_ai_input`, `normalize_config_input`; statically calls `discard_retired_provider_settings`, `normalize_ai_input`, `normalize_config_input`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `codex_profile_value`; statically calls `codex_profile_value`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `codex_profile_value`; statically calls `codex_profile_value`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `AIProviderConfig`, `AudioIngestConfig`, `DEFAULT_CODEX_MODEL`, `DEFAULT_CODEX_REASONING_EFFORT`, `LEGACY_CODEX_MODEL`, `LEGACY_CODEX_TASK_ROUTES`, `OPENROUTER_TRANSCRIPTION_PROVIDER`, `openrouter_provider`; calls `AudioIngestConfig`, `openrouter_provider`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/config/__init__|learnloop.config]], [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]], [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]], [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ai_config.py](../../../../../../tests/test_ai_config.py) — direct import
  - `test_codex_checkout_path_env_override_applies_to_codex_and_ai_provider`
  - `test_codex_checkout_path_loaded_from_global_settings_file`
  - `test_default_config_contains_ai_codex_profile`
  - `test_default_config_ships_blank_codex_checkout_path`
  - `test_in_memory_defaults_match_persisted_algorithm_and_codex_profile`
  - `test_legacy_codex_routes_upgrade_to_workload_specific_effort_profiles`
  - `test_shell_env_wins_over_global_settings_file`
- [tests/test_config_refactor.py](../../../../../../tests/test_config_refactor.py) — direct import
  - `test_config_responsibilities_have_canonical_module_owners`
  - `test_legacy_codex_is_input_only_and_sidecar_does_not_reexport_it`

## Modification guidance

- Change configuration behavior in the schema, loader, compatibility normalizer, or template owner that matches the concern; preserve one-way legacy normalization.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/config/compat.py](../../../../../../src/learnloop/config/compat.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
