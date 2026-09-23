---
title: "learnloop.ai.providers.openrouter_catalog"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/providers/openrouter_catalog.py"
source_paths:
  - "src/learnloop/ai/providers/openrouter_catalog.py"
source_commit: "df36567be6701733d162bffc27ac2a72c43d872a"
source_commit_timestamp: "2026-09-03T10:49:58-07:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
package: "learnloop.ai.providers"
layer: "infrastructure"
concepts:
  - "AI Architecture"
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
  - "Process Model Output"
aliases:
  - "learnloop.ai.providers.openrouter_catalog module"
  - "src/learnloop/ai/providers/openrouter_catalog.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai-providers"
---

# `learnloop.ai.providers.openrouter_catalog`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.providers.openrouter_catalog` exists within [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] to own the behavior summarized by its module contract: OpenRouter model capability catalog.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/providers/openrouter_catalog.py](../../../../../../../src/learnloop/ai/providers/openrouter_catalog.py) |
| Source lines | 230 |
| Owning package | [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `df36567be6701733d162bffc27ac2a72c43d872a` |
| Commit timestamp | `2026-09-03T10:49:58-07:00` |

## Public API

- `class OpenRouterCatalogError(RuntimeError)` ([source](../../../../../../../src/learnloop/ai/providers/openrouter_catalog.py), line 47) — No catalog could be produced (no cache and the fetch failed or was disallowed).
- `class CatalogSnapshot` ([source](../../../../../../../src/learnloop/ai/providers/openrouter_catalog.py), line 52)
- `catalog_cache_path() -> Path` ([source](../../../../../../../src/learnloop/ai/providers/openrouter_catalog.py), line 61)
- `reduce_models_payload(payload: Mapping[str, Any]) -> dict[str, tuple[str, ...]]` ([source](../../../../../../../src/learnloop/ai/providers/openrouter_catalog.py), line 76) — ``{"data": [{"id", "architecture": {"input_modalities": [...]}}]}`` → slug → modalities.
- `load_catalog(*, refresh: bool=False, now: datetime | None=None, ttl_seconds: int=CATALOG_TTL_SECONDS, allow_network: bool=True, timeout: float=FETCH_TIMEOUT_SECONDS) -> CatalogSnapshot` ([source](../../../../../../../src/learnloop/ai/providers/openrouter_catalog.py), line 154) — Return the catalog, fetching only when the cache is missing/expired or ``refresh``.
- `model_input_modalities(snapshot: CatalogSnapshot, slug: str) -> tuple[str, ...] | None` ([source](../../../../../../../src/learnloop/ai/providers/openrouter_catalog.py), line 195) — Declared modalities for ``slug``; ``None`` when the catalog does not list it.
- `cached_catalog_state(*, now: datetime | None=None, ttl_seconds: int=CATALOG_TTL_SECONDS) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/ai/providers/openrouter_catalog.py), line 201) — Cache-only status for a settings payload; never touches the network, never raises.

### Module constants

- `OPENROUTER_MODELS_URL` ([src/learnloop/ai/providers/openrouter_catalog.py](../../../../../../../src/learnloop/ai/providers/openrouter_catalog.py), line 34)
- `CATALOG_TTL_SECONDS` ([src/learnloop/ai/providers/openrouter_catalog.py](../../../../../../../src/learnloop/ai/providers/openrouter_catalog.py), line 35)
- `FETCH_TIMEOUT_SECONDS` ([src/learnloop/ai/providers/openrouter_catalog.py](../../../../../../../src/learnloop/ai/providers/openrouter_catalog.py), line 36)
- `CATALOG_VERSION` ([src/learnloop/ai/providers/openrouter_catalog.py](../../../../../../../src/learnloop/ai/providers/openrouter_catalog.py), line 37)
- `MODALITY_BY_OPENROUTER_INPUT` ([src/learnloop/ai/providers/openrouter_catalog.py](../../../../../../../src/learnloop/ai/providers/openrouter_catalog.py), line 39)

### Explicit exports

`__all__` declares:

- `CATALOG_TTL_SECONDS`
- `CatalogSnapshot`
- `MODALITY_BY_OPENROUTER_INPUT`
- `OPENROUTER_MODELS_URL`
- `OpenRouterCatalogError`
- `cached_catalog_state`
- `catalog_cache_path`
- `load_catalog`
- `model_input_modalities`
- `reduce_models_payload`

## Internal implementation anchors

- `_fetch_models_payload(timeout: float) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/ai/providers/openrouter_catalog.py), line 65) — The raw models listing.
- `_parse_timestamp(value: str) -> datetime | None` ([source](../../../../../../../src/learnloop/ai/providers/openrouter_catalog.py), line 102)
- `_read_cache(path: Path) -> tuple[dict[str, tuple[str, ...]], str] | None` ([source](../../../../../../../src/learnloop/ai/providers/openrouter_catalog.py), line 110)
- `_write_cache(path: Path, models: Mapping[str, tuple[str, ...]], fetched_at: str) -> None` ([source](../../../../../../../src/learnloop/ai/providers/openrouter_catalog.py), line 129) — Atomic replace so a crash mid-write never leaves a truncated catalog.
- `_is_fresh(fetched_at: str, now: datetime, ttl_seconds: int) -> bool` ([source](../../../../../../../src/learnloop/ai/providers/openrouter_catalog.py), line 147)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]] — imports `OpenRouterCatalogError`, `cached_catalog_state`, `load_catalog`, `model_input_modalities`; statically calls `cached_catalog_state`, `load_catalog`, `model_input_modalities`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]] — imports `global_settings_path`; calls `global_settings_path`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `KNOWN_INPUT_MODALITIES`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `json`, `logging`, `os`, `pathlib`, `tempfile`, `typing`, `urllib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_openrouter_catalog.py](../../../../../../../tests/test_openrouter_catalog.py) — direct import
  - `test_corrupt_cache_is_ignored`
  - `test_expired_cache_refetches_and_refresh_forces_it`
  - `test_first_load_fetches_and_caches_atomically`
  - `test_fresh_cache_is_served_without_network`
  - `test_malformed_cache_values_are_ignored_and_never_crash_the_settings_read`
  - `test_naive_now_is_treated_as_utc`
  - `test_network_failure_serves_stale_cache`
  - `test_no_cache_and_no_network_is_typed`
  - `test_reduce_maps_openrouter_inputs_to_learnloop_modalities`
  - `test_unexpected_payload_shape_is_not_cached`
- [tests/test_settings_sidecar.py](../../../../../../../tests/test_settings_sidecar.py) — direct import
  - `test_detect_provider_capabilities_without_a_model_skips_the_network`
  - `test_update_ai_settings_openrouter_ingest_profile_uses_cached_catalog`
  - `test_update_ingest_settings_native_adopts_cached_catalog_modalities`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/providers/openrouter_catalog.py](../../../../../../../src/learnloop/ai/providers/openrouter_catalog.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
