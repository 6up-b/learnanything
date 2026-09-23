---
title: "learnloop.content.authoring.concept_animation"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/authoring/concept_animation.py"
source_paths:
  - "src/learnloop/content/authoring/concept_animation.py"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
package: "learnloop.content.authoring"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.authoring.concept_animation module"
  - "src/learnloop/content/authoring/concept_animation.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-authoring"
---

# `learnloop.content.authoring.concept_animation`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.authoring.concept_animation` exists within [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] to own the behavior summarized by its module contract: AI-generated Manim explainer animations (spec_fork_features §2).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py) |
| Source lines | 1251 |
| Owning package | [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `589b35df8e5e3ce56849cbdab681c6bc12737419` |
| Commit timestamp | `2026-09-03T10:26:28-07:00` |

## Public API

- `quality_preset(quality: str | None) -> tuple[str, int]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 88)
- `class ConceptAnimationError(ValueError)` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 92)
  - `__init__(self, code: str, message: str)` (line 93; internal)
- `author_concept_animation(client: StructuredTransport, context: ConceptAnimationContext) -> ManimAnimation` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 98) — Author one animation candidate through the shared transport.
- `author_video_storyboard(client: StructuredTransport, context: VideoStoryboardContext) -> VideoStoryboard` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 111) — Author the shot list a text-to-video model will be briefed with.
- `video_generation_readiness(config: Any, vault_root: Path) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 124) — Can ``[animation] renderer = "video_model"`` run?
- `validate_scene_code(code: str) -> tuple[str | None, list[str]]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 156) — AST-validate LLM scene code.
- `class RenderResult` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 198)
- `provision_animation_venv(venv_dir: Path, *, package_spec: str='manim') -> Path` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 219) — Create an isolated venv and install manim into it (blocking).
- `resolve_manim_command(config: Any, vault_root: Path | None=None) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 240) — Resolve the command prefix that runs manim, honoring animation config.
- `manim_runtime(manim_executable: str | None=None, *, manim_command: list[str] | None=None, run=subprocess.run) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 269) — Probe whether manim is installed/renderable — cheap, no scene involved.
- `estimate_scene_duration(code: str) -> float | None` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 441) — Seconds of animation implied by the Scene subclass's construct(), or None.
- `pacing_band(config: Any) -> tuple[int, int]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 548) — The (min, max) running time the prompt targets and the lint enforces.
- `lint_scene_pacing(code: str, *, min_seconds: float, max_seconds: float) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 562) — Human-readable pacing violations for a repair round-trip (empty = fine).
- `render_scene(scene_code: str, scene_class: str, *, quality: str='ql', timeout_seconds: int=300, manim_executable: str | None=None, manim_command: list[str] | None=None, sandbox: bool | None=None, run=subprocess.run) -> RenderResult` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 583) — Render one validated scene to mp4 in a fresh temp cwd with a timeout.
- `request_concept_animation(vault: Any, repository: Any, *, concept_id: str, learning_object_id: str | None=None, consent: bool=False, clock: Any=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 671) — Insert a queued animation row.
- `build_video_storyboard_context(vault: Any, *, concept_id: str, learning_object_id: str | None, constraints: Any=None, video_model: str='', repair: dict | None=None) -> VideoStoryboardContext` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 757) — Prompt context for the storyboard: concept material plus the video model's real duration constraints, so shots are asked for in lengths the model can produce.
- `clamped_shot_seconds(storyboard: VideoStoryboard, context: VideoStoryboardContext, constraints: Any) -> list[int | None]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 799) — The per-shot lengths that will actually be requested from the model.
- `storyboard_violations(storyboard: VideoStoryboard, context: VideoStoryboardContext, *, constraints: Any=None) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 812) — Deterministic checks a storyboard must pass before any shot is billed.
- `build_animation_context(vault: Any, *, concept_id: str, learning_object_id: str | None, repair: dict | None=None)` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 842) — Pure prompt-context assembly: concept + a few LO excerpts, never raw source text.
- `generate_concept_animation(root: Path, client: Any, *, animation_id: str, repository: Any=None, renderer: Any=None, clock: Any=None, video_client: Any=None, report: Callable[[str, str], None] | None=None, cancellation: tuple[type[BaseException], ...]=()) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 900) — The durable-job body: generate -> validate -> render -> store.

### Module constants

- `ALLOWED_IMPORTS` ([src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 68)
- `ALLOWED_SCENE_BASES` ([src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 69)
- `_FORBIDDEN_NAMES` ([src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 70)
- `_STDERR_TAIL_CHARS` ([src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 77)
- `_QUALITY_PRESETS` ([src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 79)
- `_PACING_OVER_SLACK_SECONDS` ([src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 85)

## Internal implementation anchors

- `_manim_command(manim_executable: str | None) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 205)
- `_venv_python(venv_dir: Path) -> Path` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 211) — Path to the python interpreter inside a venv (platform-specific).
- `_render_env() -> dict[str, str]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 294) — A minimal env for the render subprocess: keep what Python/manim/ffmpeg need to start (PATH, system roots, temp), drop everything vault-shaped.
- `_sandbox_bwrap_path() -> str | None` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 311) — The bubblewrap binary to sandbox renders with, or None off-Linux.
- `_executable_mount_roots(executable: str) -> set[str]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 319) — Install roots (``<root>/bin/exe`` → ``<root>``) for an executable and every hop of its symlink chain, so a venv python that links into e.g.
- `_sandboxed_command(command: list[str], workdir: Path, bwrap: str) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 339) — Wrap a render command in bubblewrap: every namespace unshared (so no network), system + interpreter mounts read-only, the scratch workdir as the only writable path, and the sandbox dying with the sidecar.
- `_combined_scene_videos(media_root: Path, scene_class: str) -> list[Path]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 376) — The combined scene mp4(s) under manim's media dir, oldest first.
- `_const_number(node: ast.AST, env: dict[str, float]) -> float | None` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 403)
- `_scene_base_name(node: ast.expr) -> str | None` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 426)
- `_self_call_name(call: ast.Call) -> str | None` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 434)
- `_learning_object_excerpts(vault: Any, concept_id: str, learning_object_id: str | None, *, limit: int=4) -> list[dict[str, str]]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 738) — Title + summary of a few learning objects — never raw source text.
- `_loads_json(raw: Any, default: Any) -> Any` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 790)
- `_store_video(repository: Any, vault_root: Path, animation_id: str, video_bytes: bytes, clock: Any, **fields: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 866) — Remux, content-address, write, and mark the row completed (shared by both renderers).
- `_generate_with_video_model(vault: Any, client: Any, video_client: Any, *, animation_id: str, row: dict[str, Any], repository: Any, config: Any, clock: Any, say: Callable[[str, str], None], fail: Callable[..., dict[str, Any]]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 1119) — Storyboard -> one text-to-video job per shot -> stitched mp4.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `ConceptAnimationError`, `generate_concept_animation`; statically calls `generate_concept_animation`
- [[Reference/Modules/learnloop_sidecar/handlers/animation|learnloop_sidecar.handlers.animation]] — imports `ConceptAnimationError`, `manim_runtime`, `request_concept_animation`, `resolve_manim_command`, `video_generation_readiness`; statically calls `manim_runtime`, `request_concept_animation`, `resolve_manim_command`, `video_generation_readiness`
- [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]] — imports `video_generation_readiness`; statically calls `video_generation_readiness`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIProviderUnavailable`, `VideoGenerationFailed`, `VideoGenerationTimeout`
- [[Reference/Modules/learnloop/ai/providers/openrouter_video|learnloop.ai.providers.openrouter_video]] — imports `VideoGenerationRequest`, `clamp_aspect_ratio`, `clamp_duration`, `clamp_resolution`; calls `VideoGenerationRequest`, `clamp_aspect_ratio`, `clamp_duration`, `clamp_resolution`
- [[Reference/Modules/learnloop/ai/runtime|learnloop.ai.runtime]] — imports `check_ai_runtime`; calls `check_ai_runtime`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `STRUCTURED_COMPLETION`, `StructuredTransport`, `VIDEO_GENERATION`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/authoring/ai_contracts|learnloop.content.authoring.ai_contracts]] — imports `CONCEPT_ANIMATION_PROMPT_VERSION`, `CONCEPT_ANIMATION_SCENE_SCAFFOLD`, `ConceptAnimationContext`, `ManimAnimation`, `VIDEO_STORYBOARD_PROMPT_VERSION`, `VideoStoryboard`, `VideoStoryboardContext`, `concept_animation_prompt`, `video_storyboard_prompt`; calls `ConceptAnimationContext`, `VideoStoryboardContext`, `concept_animation_prompt`, `video_storyboard_prompt`
- [[Reference/Modules/learnloop/content/authoring/animation_media|learnloop.content.authoring.animation_media]] — imports `concat_clips`, `probe_duration_seconds`, `remux_faststart`; calls `concat_clips`, `probe_duration_seconds`, `remux_faststart`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`; calls `Repository`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`, `animation_video_path`; calls `VaultPaths`, `animation_video_path`

### Platform and third-party dependencies

- Standard library: `__future__`, `ast`, `dataclasses`, `hashlib`, `importlib`, `json`, `logging`, `os`, `pathlib`, `shutil`, `subprocess`, `sys`, `tempfile`, `typing`, `venv`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop_sidecar/handlers/animation|learnloop_sidecar.handlers.animation]], [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_concept_animation_service.py](../../../../../../../tests/test_concept_animation_service.py) — direct import
  - `test_generate_happy_path_stores_content_addressed_mp4`
  - `test_generate_provider_without_method_fails_typed`
  - `test_generate_records_duration_of_a_real_clip`
  - `test_generate_render_failure_gets_stderr_repair_then_fails`
  - `test_generate_render_repair_recovers`
  - `test_generate_short_scene_gets_one_pacing_repair_then_renders`
  - `test_generate_stores_faststart_remuxed_bytes_and_hashes_them`
  - `test_generate_unexpected_exception_never_wedges_the_row`
  - `test_generate_validator_violation_gets_one_repair_then_fails`
  - `test_generate_video_model_cancellation_marks_the_row_cancelled`
  - `test_generate_video_model_clamps_aspect_ratio_and_resumes_from_persisted_jobs`
  - `test_generate_video_model_path_stores_stitched_clip_and_provenance`
  - `test_generate_video_model_shot_failure_and_submit_rejection_are_typed`
  - `test_generate_video_model_storyboard_gets_one_repair_then_fails_typed`
  - `test_generate_video_model_without_client_fails_typed`
  - `test_generate_video_model_without_pyav_is_not_ready`
  - `test_request_pending_lock_and_dead_batch_reconciliation`
  - `test_request_requires_consent_enabled_and_known_concept`
  - `test_request_video_model_requires_a_ready_route`
  - `test_runner_handler_drives_generation_through_the_queue`
  - `test_storyboard_total_is_checked_on_the_clamped_durations`
- [tests/test_concept_animation_validator.py](../../../../../../../tests/test_concept_animation_validator.py) — direct import
  - `test_estimate_follows_loops_defaults_and_helpers`
  - `test_manim_runtime_probe_found_and_missing`
  - `test_render_result_is_plain_dataclass`
  - `test_render_scene_failure_captures_stderr_tail`
  - `test_render_scene_ignores_partial_movie_files_when_only_partials_exist`
  - `test_render_scene_off_linux_runs_direct_without_bwrap`
  - `test_render_scene_prefers_scene_class_named_file`
  - `test_render_scene_requires_bwrap_on_linux`
  - `test_render_scene_sandboxes_with_bwrap`
  - `test_render_scene_success_reads_mp4_and_cleans_temp`
  - `test_render_scene_timeout_is_typed`
  - `test_scaffold_passes_validator`
  - `test_scaffold_with_four_beats_estimates_within_the_band`
  - `test_short_and_overlong_scenes_are_flagged_by_pacing_lint`
  - `test_valid_scene_passes_and_names_class`
  - `test_validator_rejects_malicious_samples`
  - `test_validator_requires_scene_subclass_and_reports_syntax_errors`
- [tests/test_sidecar_animation.py](../../../../../../../tests/test_sidecar_animation.py) — direct import
  - `test_request_generates_and_status_reports_completed`
- [tests/test_structured_transport_parity.py](../../../../../../../tests/test_structured_transport_parity.py) — direct import

## Modification guidance

- Change concept animation policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
