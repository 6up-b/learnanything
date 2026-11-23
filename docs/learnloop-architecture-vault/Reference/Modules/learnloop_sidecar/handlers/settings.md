---
title: "learnloop_sidecar.handlers.settings"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/settings.py"
source_paths:
  - "src/learnloop_sidecar/handlers/settings.py"
generated: true
generated_at: "2026-11-02"
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
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.settings` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Settings tab RPCs: read and persist AI model routing, the OpenRouter API key, and (in later slices) ingestion preferences.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/settings.py](../../../../../../src/learnloop_sidecar/handlers/settings.py) |
| Source lines | 831 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `get_settings(ctx: SidecarContext, _params: EmptyParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 245)
- `class UseCaseChoice(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 249)
- `class UpdateAiSettingsParams(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 254)
- `update_ai_settings(ctx: SidecarContext, params: UpdateAiSettingsParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 267) — Persist provider/model choices to learnloop.toml and reload.
- `class UpdateIngestSettingsParams(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 435)
- `update_ingest_settings(ctx: SidecarContext, params: UpdateIngestSettingsParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 459)
- `class DetectProviderCapabilitiesParams(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 554)
- `detect_provider_capabilities(ctx: SidecarContext, params: DetectProviderCapabilitiesParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 561) — Look an OpenRouter profile's model up in the public model catalog.
- `class UpdateProviderModalitiesParams(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 634)
- `update_provider_modalities(ctx: SidecarContext, params: UpdateProviderModalitiesParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 640) — Record the media modalities a chat provider profile accepts natively.
- `class SetTranscriptionApiKeyParams(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 674)
- `set_transcription_api_key(ctx: SidecarContext, params: SetTranscriptionApiKeyParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 679) — Save the [ingest.audio] endpoint's API key — same machinery and rules as the OpenRouter key (global settings.env + direct os.environ write).
- `class SetTextRecognitionApiKeyParams(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 706)
- `set_text_recognition_api_key(ctx: SidecarContext, params: SetTextRecognitionApiKeyParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 711) — Save the z.ai key GLM-OCR text recognition uses ([ingest.pdf.glm_ocr] api_key_env) — same machinery and rules as the OpenRouter key (global settings.env + direct os.environ write).
- `class SetOpenrouterApiKeyParams(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 740)
- `set_openrouter_api_key(ctx: SidecarContext, params: SetOpenrouterApiKeyParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 745)
- `class UpdateAnimationSettingsParams(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 772)
- `update_animation_settings(ctx: SidecarContext, params: UpdateAnimationSettingsParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 781) — Persist [animation] render quality / pacing cap / timeout and reload.

### Module constants

- `OPENROUTER_KEY_ENV` ([src/learnloop_sidecar/handlers/settings.py](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 57)
- `ANIMATION_QUALITY_OPTIONS` ([src/learnloop_sidecar/handlers/settings.py](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 60)
- `ANIMATION_RENDERER_OPTIONS` ([src/learnloop_sidecar/handlers/settings.py](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 61)
- `ANIMATION_SHOT_BOUNDS` ([src/learnloop_sidecar/handlers/settings.py](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 62)
- `ANIMATION_DURATION_BOUNDS` ([src/learnloop_sidecar/handlers/settings.py](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 63)
- `ANIMATION_TIMEOUT_BOUNDS` ([src/learnloop_sidecar/handlers/settings.py](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 64)
- `_ROUTING_TASKS` ([src/learnloop_sidecar/handlers/settings.py](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 66)
- `NATIVE_LIMIT_BOUNDS_MB` ([src/learnloop_sidecar/handlers/settings.py](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 432)
- `TRANSCRIPTION_PROVIDERS` ([src/learnloop_sidecar/handlers/settings.py](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 455)

## Internal implementation anchors

- `_route_display(value: Any) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 88) — A route as the Settings tab shows it; a panel list reads as one string.
- `_key_state(env_name: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 96)
- `_text_recognition_state(config) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 104) — GLM-OCR (Settings → Ingestion): the z.ai key's state and which backend would read a document now.
- `_settings_payload(ctx: SidecarContext) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 122)
- `_ingest_provider_name(config) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 222) — The provider the build plan measures its ceilings against (§3.1).
- `_provider_limits(config) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 228) — `[ingest.providers.<routed>]` context/output limits.
- `_validate_model_slug(slug: str) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 259)
- `_cached_catalog_modalities(model: str | None) -> list[str] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 363) — Declared modalities for an OpenRouter model from the on-disk catalog only.
- `_ordered_modalities(values: set[str]) -> list[str]` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 376) — Known modalities in vocabulary order; anything else declared by hand is kept after them.
- `_provider_modality_updates(provider_name: str, profile: Any, input_modalities: list[str]) -> dict[tuple[str, ...], Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 383) — Config writes that declare ``input_modalities`` on a provider profile.
- `_adopt_cached_modalities(ctx: SidecarContext, modalities: tuple[str, ...]) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/settings.py), line 404) — When a modality is routed natively to an OpenRouter profile that does not declare it but the cached catalog says its model accepts it, record the union on the profile.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/disclosures|learnloop.ai.disclosures]] — imports `judge_route_disclosures`; calls `judge_route_disclosures`
- [[Reference/Modules/learnloop/ai/native_media|learnloop.ai.native_media]] — imports `NATIVE_MODALITIES`, `native_modality_readiness`; calls `native_modality_readiness`
- [[Reference/Modules/learnloop/ai/providers/openrouter_catalog|learnloop.ai.providers.openrouter_catalog]] — imports `OpenRouterCatalogError`, `cached_catalog_state`, `load_catalog`, `model_input_modalities`; calls `cached_catalog_state`, `load_catalog`, `model_input_modalities`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `is_generation_profile`, `runtime_for_provider`; calls `is_generation_profile`, `runtime_for_provider`
- [[Reference/Modules/learnloop/ai/runtime|learnloop.ai.runtime]] — imports `check_ai_runtime`; calls `check_ai_runtime`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `CODEX_PROVIDER_NAMES`, `global_ai_defaults_path`, `global_settings_path`; calls `global_ai_defaults_path`, `global_settings_path`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `KNOWN_INPUT_MODALITIES`
- [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]] — imports `video_generation_readiness`; calls `video_generation_readiness`
- [[Reference/Modules/learnloop/ingest/extractors/glm_ocr|learnloop.ingest.extractors.glm_ocr]] — imports `glm_api_key`, `selected_backend`; calls `glm_api_key`, `selected_backend`
- [[Reference/Modules/learnloop/ops/settings_store|learnloop.ops.settings_store]] — imports `SettingsStoreError`, `USE_CASE_ROUTES`, `apply_config_updates`, `openrouter_profile_name`, `openrouter_task_profile_values`, `save_ai_settings_to`, `upsert_env_var`; calls `apply_config_updates`, `openrouter_profile_name`, `openrouter_task_profile_values`, `save_ai_settings_to`, `upsert_env_var`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`, `runtime_health`; calls `runtime_health`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `EmptyParams`, `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/chatgpt_plan|learnloop_sidecar.handlers.chatgpt_plan]] — imports `chatgpt_plan_payload`; calls `chatgpt_plan_payload`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `BUDGET_BOUNDS`, `PLAN_BUDGET_FIELDS`, `pdf_engines_refusing_page_ranges`, `validated_budget_overrides`; calls `pdf_engines_refusing_page_ranges`, `validated_budget_overrides`
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

- [tests/test_chatgpt_plan_sidecar.py](../../../../../../tests/test_chatgpt_plan_sidecar.py) — direct import
  - `test_settings_payload_lists_plan_profiles_and_their_routes`
- [tests/test_pf_cli.py](../../../../../../tests/test_pf_cli.py) — direct import
  - `test_sidecar_settings_show_a_panel_list_as_text`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/settings.py](../../../../../../src/learnloop_sidecar/handlers/settings.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
