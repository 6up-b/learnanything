---
title: "learnloop_sidecar.handlers.settings"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/settings.py"
source_paths:
  - "src/learnloop_sidecar/handlers/settings.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-08-18"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
aliases:
  - "learnloop_sidecar.handlers.settings module"
  - "src/learnloop_sidecar/handlers/settings.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.settings`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.settings` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Settings tab RPCs: read and persist AI model routing, the OpenRouter API key, and (in later slices) ingestion preferences.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/settings.py](../../../../../../src/learnloop_sidecar/handlers/settings.py) |
| Source lines | 386 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `get_settings(ctx: SidecarContext, _params: EmptyParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 139)
- `class UseCaseChoice(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 143)
- `class UpdateAiSettingsParams(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 148)
- `update_ai_settings(ctx: SidecarContext, params: UpdateAiSettingsParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 161) — Persist provider/model choices to learnloop.toml and reload.
- `class UpdateIngestSettingsParams(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 238)
- `update_ingest_settings(ctx: SidecarContext, params: UpdateIngestSettingsParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 256)
- `class SetTranscriptionApiKeyParams(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 325)
- `set_transcription_api_key(ctx: SidecarContext, params: SetTranscriptionApiKeyParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 330) — Save the [ingest.audio] endpoint's API key — same machinery and rules as the OpenRouter key (global settings.env + direct os.environ write).
- `class SetOpenrouterApiKeyParams(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 357)
- `set_openrouter_api_key(ctx: SidecarContext, params: SetOpenrouterApiKeyParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 362)

### Module constants

- `OPENROUTER_KEY_ENV` ([src/learnloop_sidecar/handlers/settings.py](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 44)
- `_ROUTING_TASKS` ([src/learnloop_sidecar/handlers/settings.py](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 46)
- `TRANSCRIPTION_PROVIDERS` ([src/learnloop_sidecar/handlers/settings.py](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 252)

## Internal implementation anchors

- `_key_state(env_name: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 59)
- `_settings_payload(ctx: SidecarContext) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 67)
- `_ingest_provider_name(config) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 116) — The provider the build plan measures its ceilings against (§3.1).
- `_provider_limits(config) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 122) — `[ingest.providers.<routed>]` context/output limits.
- `_validate_model_slug(slug: str) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 153)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/runtime|learnloop.ai.runtime]] — imports `check_ai_runtime`; calls `check_ai_runtime`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `CODEX_PROVIDER_NAMES`, `global_ai_defaults_path`, `global_settings_path`; calls `global_ai_defaults_path`, `global_settings_path`
- [[Reference/Modules/learnloop/ops/settings_store|learnloop.ops.settings_store]] — imports `SettingsStoreError`, `USE_CASE_ROUTES`, `apply_config_updates`, `openrouter_profile_name`, `openrouter_task_profile_values`, `save_ai_settings_to`, `upsert_env_var`; calls `apply_config_updates`, `openrouter_profile_name`, `openrouter_task_profile_values`, `save_ai_settings_to`, `upsert_env_var`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`, `runtime_health`; calls `runtime_health`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `EmptyParams`, `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `BUDGET_BOUNDS`, `PLAN_BUDGET_FIELDS`, `validated_budget_overrides`; calls `validated_budget_overrides`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `logging`, `os`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_desktop_rpc_contract.py](../../../../../../tests/test_desktop_rpc_contract.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_dialogue_causal_join.py](../../../../../../tests/test_dialogue_causal_join.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_goal_scope_material.py](../../../../../../tests/test_goal_scope_material.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_graph_editor_reads.py](../../../../../../tests/test_graph_editor_reads.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_adjudication.py](../../../../../../tests/test_sidecar_adjudication.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_exams.py](../../../../../../tests/test_sidecar_exams.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_goals.py](../../../../../../tests/test_sidecar_goals.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_item_presentation.py](../../../../../../tests/test_sidecar_item_presentation.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_measurement.py](../../../../../../tests/test_sidecar_measurement.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_trace_and_clarification.py](../../../../../../tests/test_sidecar_trace_and_clarification.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/settings.py](../../../../../../src/learnloop_sidecar/handlers/settings.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
