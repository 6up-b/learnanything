---
title: "learnloop.ai.providers.openrouter_video"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/providers/openrouter_video.py"
source_paths:
  - "src/learnloop/ai/providers/openrouter_video.py"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
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
  - "learnloop.ai.providers.openrouter_video module"
  - "src/learnloop/ai/providers/openrouter_video.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai-providers"
---

# `learnloop.ai.providers.openrouter_video`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.providers.openrouter_video` exists within [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] to own the behavior summarized by its module contract: OpenRouter text-to-video client (``POST /api/v1/videos``).

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/providers/openrouter_video.py](../../../../../../../src/learnloop/ai/providers/openrouter_video.py) |
| Source lines | 334 |
| Owning package | [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `589b35df8e5e3ce56849cbdab681c6bc12737419` |
| Commit timestamp | `2026-09-03T10:26:28-07:00` |

## Public API

- `class VideoGenerationRequest` ([source](../../../../../../../src/learnloop/ai/providers/openrouter_video.py), line 44)
- `class VideoJob` ([source](../../../../../../../src/learnloop/ai/providers/openrouter_video.py), line 54)
- `class VideoJobStatus` ([source](../../../../../../../src/learnloop/ai/providers/openrouter_video.py), line 61)
- `class VideoModelConstraints` ([source](../../../../../../../src/learnloop/ai/providers/openrouter_video.py), line 70)
- `clamp_duration(requested: int | None, *, max_seconds: int, constraints: VideoModelConstraints | None) -> int | None` ([source](../../../../../../../src/learnloop/ai/providers/openrouter_video.py), line 106) — The shot length to ask for: the largest supported value under the caps.
- `clamp_resolution(preferred: str | None, constraints: VideoModelConstraints | None) -> str | None` ([source](../../../../../../../src/learnloop/ai/providers/openrouter_video.py), line 128) — The preferred resolution when the model lists it (or lists nothing), else its first.
- `clamp_aspect_ratio(preferred: str | None, constraints: VideoModelConstraints | None) -> str | None` ([source](../../../../../../../src/learnloop/ai/providers/openrouter_video.py), line 134) — Same rule for aspect ratios: an off-list value is a 400 from OpenRouter.
- `class OpenRouterVideoClient` ([source](../../../../../../../src/learnloop/ai/providers/openrouter_video.py), line 140)
  - `__init__(self, provider_name: str, profile: AIProviderConfig, *, http: HttpTransport | None=None, sleep: Callable[[float], None]=time.sleep, clock: Callable[[], float]=time.monotonic) -> None` (line 143; internal)
  - `supports(self, capability: str) -> bool` (line 179; public)
  - `_request(self, method: str, url: str, payload: Any=None, *, timeout: float) -> tuple[int, Any]` (line 184; internal)
  - `model_constraints(self) -> VideoModelConstraints | None` (line 193; public) — Supported durations/resolutions for this model; None when unknown.
  - `submit(self, request: VideoGenerationRequest) -> VideoJob` (line 216; public) — Submit one generation job.
  - `poll(self, job_id: str) -> VideoJobStatus` (line 237; public)
  - `download(self, job_id: str, index: int=0) -> bytes` (line 264; public)
  - `wait_all(self, job_ids: Sequence[str], *, max_wait_seconds: float, poll_interval_seconds: float=DEFAULT_POLL_INTERVAL_SECONDS, first_delay_seconds: float=FIRST_POLL_DELAY_SECONDS, checkpoint: Callable[[list[VideoJobStatus], float], None] | None=None) -> list[VideoJobStatus]` (line 274; public) — Poll every job until all complete.

### Module constants

- `DEFAULT_POLL_INTERVAL_SECONDS` ([src/learnloop/ai/providers/openrouter_video.py](../../../../../../../src/learnloop/ai/providers/openrouter_video.py), line 28)
- `FIRST_POLL_DELAY_SECONDS` ([src/learnloop/ai/providers/openrouter_video.py](../../../../../../../src/learnloop/ai/providers/openrouter_video.py), line 29)
- `SUBMIT_TIMEOUT_SECONDS` ([src/learnloop/ai/providers/openrouter_video.py](../../../../../../../src/learnloop/ai/providers/openrouter_video.py), line 30)
- `POLL_TIMEOUT_SECONDS` ([src/learnloop/ai/providers/openrouter_video.py](../../../../../../../src/learnloop/ai/providers/openrouter_video.py), line 31)
- `DOWNLOAD_TIMEOUT_SECONDS` ([src/learnloop/ai/providers/openrouter_video.py](../../../../../../../src/learnloop/ai/providers/openrouter_video.py), line 32)
- `POLL_ATTEMPTS` ([src/learnloop/ai/providers/openrouter_video.py](../../../../../../../src/learnloop/ai/providers/openrouter_video.py), line 35)
- `POLL_RETRY_DELAY_SECONDS` ([src/learnloop/ai/providers/openrouter_video.py](../../../../../../../src/learnloop/ai/providers/openrouter_video.py), line 36)
- `TERMINAL_FAILURE_STATES` ([src/learnloop/ai/providers/openrouter_video.py](../../../../../../../src/learnloop/ai/providers/openrouter_video.py), line 37)

### Explicit exports

`__all__` declares:

- `DEFAULT_POLL_INTERVAL_SECONDS`
- `FIRST_POLL_DELAY_SECONDS`
- `HttpTransport`
- `OpenRouterVideoClient`
- `VideoGenerationRequest`
- `VideoJob`
- `VideoJobStatus`
- `VideoModelConstraints`
- `clamp_aspect_ratio`
- `clamp_duration`
- `clamp_resolution`

## Internal implementation anchors

- `_urllib_transport(method: str, url: str, headers: Mapping[str, str], body: bytes | None, timeout: float) -> tuple[int, Mapping[str, str], bytes]` ([source](../../../../../../../src/learnloop/ai/providers/openrouter_video.py), line 76)
- `_error_text(payload: Any) -> str` ([source](../../../../../../../src/learnloop/ai/providers/openrouter_video.py), line 94)
- `_clamp_choice(preferred: str | None, supported: Sequence[str]) -> str | None` ([source](../../../../../../../src/learnloop/ai/providers/openrouter_video.py), line 120)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `OpenRouterVideoClient`; statically calls `OpenRouterVideoClient`
- [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]] — imports `VideoGenerationRequest`, `clamp_aspect_ratio`, `clamp_duration`, `clamp_resolution`; statically calls `VideoGenerationRequest`, `clamp_aspect_ratio`, `clamp_duration`, `clamp_resolution`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIProviderUnavailable`, `VideoGenerationFailed`, `VideoGenerationTimeout`; calls `AIProviderUnavailable`, `VideoGenerationFailed`, `VideoGenerationTimeout`
- [[Reference/Modules/learnloop/ai/providers/openrouter|learnloop.ai.providers.openrouter]] — imports `OPENROUTER_API_KEY_ENV`, `OPENROUTER_BASE_URL`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `VIDEO_GENERATION`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `AIProviderConfig`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `http`, `json`, `os`, `time`, `typing`, `urllib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]], [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_concept_animation_service.py](../../../../../../../tests/test_concept_animation_service.py) — direct import
  - `test_generate_video_model_clamps_aspect_ratio_and_resumes_from_persisted_jobs`
  - `test_storyboard_total_is_checked_on_the_clamped_durations`
- [tests/test_openrouter_video_client.py](../../../../../../../tests/test_openrouter_video_client.py) — direct import
  - `test_clamp_aspect_ratio_follows_the_model_listing`
  - `test_clamp_helpers`
  - `test_factory_requires_an_openrouter_profile`
  - `test_missing_key_and_model_are_typed`
  - `test_model_constraints_parse_and_cache`
  - `test_poll_retries_transport_errors_a_few_times_with_a_pause`
  - `test_submit_accepts_any_2xx_that_names_a_job`
  - `test_submit_posts_model_prompt_and_options_with_bearer`
  - `test_submit_rejection_is_typed_and_never_retried`
  - `test_transport_maps_socket_errors_to_provider_unavailable`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/providers/openrouter_video.py](../../../../../../../src/learnloop/ai/providers/openrouter_video.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
