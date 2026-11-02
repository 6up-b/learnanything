---
title: "learnloop.content.authoring.concept_animation"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/authoring/concept_animation.py"
source_paths:
  - "src/learnloop/content/authoring/concept_animation.py"
source_commit: "681d1a7b0139e6de859681267c821b3732f5b71d"
source_commit_timestamp: "2026-11-01T10:31:44-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
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
| Source lines | 1550 |
| Owning package | [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `681d1a7b0139e6de859681267c821b3732f5b71d` |
| Commit timestamp | `2026-11-01T10:31:44-05:00` |

## Public API

- `quality_preset(quality: str | None) -> tuple[str, int]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 94)
- `class ConceptAnimationError(ValueError)` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 98)
  - `__init__(self, code: str, message: str)` (line 99; internal)
- `author_concept_animation(client: StructuredTransport, context: ConceptAnimationContext) -> ManimAnimation` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 104) — Author one animation candidate through the shared transport.
- `author_video_storyboard(client: StructuredTransport, context: VideoStoryboardContext) -> VideoStoryboard` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 117) — Author the shot list a text-to-video model will be briefed with.
- `video_generation_readiness(config: Any, vault_root: Path) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 130) — Can ``[animation] renderer = "video_model"`` run?
- `validate_scene_code(code: str) -> tuple[str | None, list[str]]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 162) — AST-validate LLM scene code.
- `class RenderResult` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 204)
- `provision_animation_venv(venv_dir: Path, *, package_spec: str='manim') -> Path` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 225) — Create an isolated venv and install manim into it (blocking).
- `resolve_manim_command(config: Any, vault_root: Path | None=None) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 246) — Resolve the command prefix that runs manim, honoring animation config.
- `manim_runtime(manim_executable: str | None=None, *, manim_command: list[str] | None=None, run=subprocess.run) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 275) — Probe whether manim is installed/renderable — cheap, no scene involved.
- `sandbox_bwrap_path() -> str | None` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 325) — Public name of :func:`_sandbox_bwrap_path` (Reader RW5d P2b: the figure service asks whether the Manim tier can run here).
- `scope_session_env() -> dict[str, str]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 366) — The session variables the scope launcher needs, from this process's env.
- `capped_scope_prefix(*, memory_bytes: int=RENDER_MEMORY_MAX, cpu_quota: str=RENDER_CPU_QUOTA, tasks_max: int=RENDER_TASKS_MAX, background: bool=False, run=None) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 399) — The resource caps a sandboxed render runs under (Reader RW5d P2b, spec §9b.3): a ``systemd-run --user --scope`` with ``MemoryMax``, ``MemorySwapMax=0``, ``CPUQuota`` and ``TasksMax`` when a user scope can start here (the owner's test-run rule, for the same oomd reason), else ``p…
- `estimate_scene_duration(code: str) -> float | None` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 560) — Seconds of animation implied by the Scene subclass's construct(), or None.
- `pacing_band(config: Any) -> tuple[int, int]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 667) — The (min, max) running time the prompt targets and the lint enforces.
- `lint_scene_pacing(code: str, *, min_seconds: float, max_seconds: float) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 681) — Human-readable pacing violations for a repair round-trip (empty = fine).
- `render_launch(command: list[str], workdir: Path, bwrap: str | None, wrapper: list[str] | None) -> tuple[list[str], dict[str, str]]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 702) — The argv and env a render is launched with (Codex review F1: one path, the one :func:`_systemd_scope_works` probes): the render's minimal env; under bubblewrap, ``HOME`` and the caches in the scratch dir; under a ``systemd-run`` wrapper, the session variables the launcher needs…
- `terminate_process_tree(process: Any) -> None` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 755) — End a render and everything it started, on any platform (Codex re-review F12): the process group on POSIX (``SIGKILL``), the tree by ``taskkill /T`` on Windows; then, whatever that did (a tree kill that fails, a platform without it), the process itself, so the caller's ``wait()`…
- `class BoundedResult` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 778) — What :func:`bounded_run` returns: ``subprocess.CompletedProcess``'s fields with the output tails, and whether the output budget stopped it.
- `bounded_run(command: list[str], *, cwd: str | None=None, env: Mapping[str, str] | None=None, capture_output: bool=True, timeout: float | None=None, max_output_bytes: int=RENDER_MAX_OUTPUT_BYTES, tail_bytes: int=_STDERR_TAIL_CHARS) -> BoundedResult` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 789) — ``subprocess.run(capture_output=True)`` without unbounded buffers (Reader RW5d P2b, Codex review F3).
- `render_scene(scene_code: str, scene_class: str, *, quality: str='ql', timeout_seconds: int=300, manim_executable: str | None=None, manim_command: list[str] | None=None, sandbox: bool | None=None, run=None, wrapper: list[str] | None=None) -> RenderResult` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 857) — Render one validated scene to mp4 in a fresh temp cwd with a timeout.
- `request_concept_animation(vault: Any, repository: Any, *, concept_id: str, learning_object_id: str | None=None, consent: bool=False, clock: Any=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 954) — Insert a queued animation row.
- `build_video_storyboard_context(vault: Any, *, concept_id: str, learning_object_id: str | None, constraints: Any=None, video_model: str='', repair: dict | None=None) -> VideoStoryboardContext` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 1040) — Prompt context for the storyboard: concept material plus the video model's real duration constraints, so shots are asked for in lengths the model can produce.
- `clamped_shot_seconds(storyboard: VideoStoryboard, context: VideoStoryboardContext, constraints: Any) -> list[int | None]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 1082) — The per-shot lengths that will actually be requested from the model.
- `storyboard_violations(storyboard: VideoStoryboard, context: VideoStoryboardContext, *, constraints: Any=None) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 1095) — Deterministic checks a storyboard must pass before any shot is billed.
- `build_animation_context(vault: Any, *, concept_id: str, learning_object_id: str | None, repair: dict | None=None)` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 1125) — Pure prompt-context assembly: concept + a few LO excerpts, never raw source text.
- `class StoredVideo` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 1150)
- `store_video_bytes(vault_root: Path, video_bytes: bytes) -> StoredVideo` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 1156) — Remux for streaming and write content-addressed under ``media/animations/`` (the one store: the inspector's animations and, Reader RW5d P2b, Manim figures).
- `generate_concept_animation(root: Path, client: Any, *, animation_id: str, repository: Any=None, renderer: Any=None, clock: Any=None, video_client: Any=None, report: Callable[[str, str], None] | None=None, cancellation: tuple[type[BaseException], ...]=()) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 1199) — The durable-job body: generate -> validate -> render -> store.

### Module constants

- `ALLOWED_IMPORTS` ([src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 74)
- `ALLOWED_SCENE_BASES` ([src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 75)
- `_FORBIDDEN_NAMES` ([src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 76)
- `_STDERR_TAIL_CHARS` ([src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 83)
- `_QUALITY_PRESETS` ([src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 85)
- `_PACING_OVER_SLACK_SECONDS` ([src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 91)
- `HARDENED_BWRAP_FLAGS` ([src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 338)
- `RENDER_MEMORY_MAX` ([src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 343)
- `RENDER_CPU_QUOTA` ([src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 344)
- `RENDER_TASKS_MAX` ([src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 345)
- `SCOPE_SESSION_ENV` ([src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 353)
- `RENDER_MAX_OUTPUT_BYTES` ([src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 359)
- `RENDER_MAX_VIDEO_BYTES` ([src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 363)
- `_SCOPE_PROBE` ([src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 374)
- `_WINDOWS` ([src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 732)
- `_TASKKILL_SECONDS` ([src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 735)

## Internal implementation anchors

- `_manim_command(manim_executable: str | None) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 211)
- `_venv_python(venv_dir: Path) -> Path` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 217) — Path to the python interpreter inside a venv (platform-specific).
- `_render_env() -> dict[str, str]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 300) — A minimal env for the render subprocess: keep what Python/manim/ffmpeg need to start (PATH, system roots, temp), drop everything vault-shaped.
- `_sandbox_bwrap_path() -> str | None` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 317) — The bubblewrap binary to sandbox renders with, or None off-Linux.
- `_systemd_scope_works(run=None) -> bool` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 377) — Whether ``systemd-run --user --scope`` can start a scope here (a user manager on the session bus), probed once per process with ``true``, launched exactly as a render's scope is (Codex review F1): the render's minimal env plus :func:`scope_session_env`, nothing else inherited.
- `_executable_mount_roots(executable: str) -> set[str]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 426) — Install roots (``<root>/bin/exe`` → ``<root>``) for an executable and every hop of its symlink chain, so a venv python that links into e.g.
- `_sandboxed_command(command: list[str], workdir: Path, bwrap: str, *, hardened: bool=True, unset_env: tuple[str, ...]=()) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 446) — Wrap a render command in bubblewrap: every namespace unshared (so no network), system + interpreter mounts read-only, the scratch workdir as the only writable path, and the sandbox dying with the sidecar.
- `_combined_scene_videos(media_root: Path, scene_class: str) -> list[Path]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 495) — The combined scene mp4(s) under manim's media dir, oldest first.
- `_const_number(node: ast.AST, env: dict[str, float]) -> float | None` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 522)
- `_scene_base_name(node: ast.expr) -> str | None` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 545)
- `_self_call_name(call: ast.Call) -> str | None` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 553)
- `_session_kwargs() -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 738) — POSIX: the child leads a new session, so its process group is it and everything it starts.
- `_kill_windows_tree(pid: int) -> None` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 749)
- `_learning_object_excerpts(vault: Any, concept_id: str, learning_object_id: str | None, *, limit: int=4) -> list[dict[str, str]]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 1021) — Title + summary of a few learning objects — never raw source text.
- `_loads_json(raw: Any, default: Any) -> Any` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 1073)
- `_store_video(repository: Any, vault_root: Path, animation_id: str, video_bytes: bytes, clock: Any, **fields: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 1177) — Remux, content-address, write, and mark the row completed (shared by both renderers).
- `_generate_with_video_model(vault: Any, client: Any, video_client: Any, *, animation_id: str, row: dict[str, Any], repository: Any, config: Any, clock: Any, say: Callable[[str, str], None], fail: Callable[..., dict[str, Any]]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 1418) — Storyboard -> one text-to-video job per shot -> stitched mp4.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/pf_sandbox|learnloop.content.authoring.pf_sandbox]] — imports `_sandbox_bwrap_path`, `_sandboxed_command`; statically calls `_sandbox_bwrap_path`, `_sandboxed_command`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `ConceptAnimationError`, `generate_concept_animation`; statically calls `generate_concept_animation`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `capped_scope_prefix`, `lint_scene_pacing`, `manim_runtime`, `pacing_band`, `quality_preset`, `render_scene`, `resolve_manim_command`, `sandbox_bwrap_path`, `store_video_bytes`, `validate_scene_code`; statically calls `capped_scope_prefix`, `lint_scene_pacing`, `manim_runtime`, `pacing_band`, `quality_preset`, `resolve_manim_command`, `sandbox_bwrap_path`, `store_video_bytes`, `validate_scene_code`
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
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`, `animation_video_path`; calls `VaultPaths`, `animation_video_path`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `vault_repository`; calls `vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `ast`, `dataclasses`, `hashlib`, `importlib`, `json`, `logging`, `os`, `pathlib`, `shutil`, `signal`, `subprocess`, `sys`, `tempfile`, `threading`, `typing`, `venv`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/pf_sandbox|learnloop.content.authoring.pf_sandbox]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]], [[Reference/Modules/learnloop_sidecar/handlers/animation|learnloop_sidecar.handlers.animation]], [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/rich_fixtures.py](../../../../../../../tests/rich_fixtures.py) — direct import
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
- [tests/test_figure_rich_contract.py](../../../../../../../tests/test_figure_rich_contract.py) — direct import
  - `test_tiers_allowed_needs_the_switch_linux_bwrap_manim_and_the_standing_opt_in`
- [tests/test_manim_figure_checks.py](../../../../../../../tests/test_manim_figure_checks.py) — direct import
  - `test_the_scene_validator_refuses_the_hostile_imports_before_any_render`
- [tests/test_manim_sandbox_hostile.py](../../../../../../../tests/test_manim_sandbox_hostile.py) — direct import
  - `test_a_timeout_on_windows_ends_the_tree_and_reaps_the_renderer`
  - `test_a_video_past_the_cap_is_never_read`
  - `test_an_output_flood_on_windows_ends_the_tree_and_reaps_the_renderer`
  - `test_bounded_run_returns_the_output_tails_and_times_out`
  - `test_bounded_run_stops_a_flood_and_keeps_only_the_tails`
  - `test_render_scene_runs_bounded_by_default_and_fails_a_flood`
  - `test_render_scene_wraps_the_sandbox_in_the_capped_scope`
  - `test_the_capped_scope_prefix`
  - `test_the_profile_is_hardened_for_every_caller`
  - `test_the_real_capped_scope_launches_the_sandbox_without_the_session_bus`
  - `test_the_render_launch_gives_the_scope_the_session_bus_and_unsets_it_in_the_sandbox`
  - `test_the_scope_probe_launches_exactly_as_a_render_does`
  - `test_the_scope_probe_runs_once_and_fails_closed_to_prlimit`
  - `test_the_tree_kill_always_falls_back_to_killing_the_renderer`
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
