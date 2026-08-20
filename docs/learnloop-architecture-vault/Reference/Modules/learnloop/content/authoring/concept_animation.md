---
title: "learnloop.content.authoring.concept_animation"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/authoring/concept_animation.py"
source_paths:
  - "src/learnloop/content/authoring/concept_animation.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
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
| Source lines | 626 |
| Owning package | [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ConceptAnimationError(ValueError)` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 57)
  - `__init__(self, code: str, message: str)` (line 58; internal)
- `author_concept_animation(client: StructuredTransport, context: ConceptAnimationContext) -> ManimAnimation` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 63) — Author one animation candidate through the shared transport.
- `validate_scene_code(code: str) -> tuple[str | None, list[str]]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 76) — AST-validate LLM scene code.
- `class RenderResult` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 118)
- `provision_animation_venv(venv_dir: Path, *, package_spec: str='manim') -> Path` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 139) — Create an isolated venv and install manim into it (blocking).
- `resolve_manim_command(config: Any, vault_root: Path | None=None) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 160) — Resolve the command prefix that runs manim, honoring animation config.
- `manim_runtime(manim_executable: str | None=None, *, manim_command: list[str] | None=None, run=subprocess.run) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 189) — Probe whether manim is installed/renderable — cheap, no scene involved.
- `render_scene(scene_code: str, scene_class: str, *, quality: str='ql', timeout_seconds: int=300, manim_executable: str | None=None, manim_command: list[str] | None=None, sandbox: bool | None=None, run=subprocess.run) -> RenderResult` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 296) — Render one validated scene to mp4 in a fresh temp cwd with a timeout.
- `request_concept_animation(vault: Any, repository: Any, *, concept_id: str, learning_object_id: str | None=None, consent: bool=False, clock: Any=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 379) — Insert a queued animation row.
- `build_animation_context(vault: Any, *, concept_id: str, learning_object_id: str | None, repair: dict | None=None)` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 436) — Pure prompt-context assembly: concept + a few LO excerpts, never raw source text.
- `generate_concept_animation(root: Path, client: Any, *, animation_id: str, repository: Any=None, renderer: Any=None, clock: Any=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 466) — The durable-job body: generate -> validate -> render -> store.

### Module constants

- `ALLOWED_IMPORTS` ([src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 45)
- `ALLOWED_SCENE_BASES` ([src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 46)
- `_FORBIDDEN_NAMES` ([src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 47)
- `_STDERR_TAIL_CHARS` ([src/learnloop/content/authoring/concept_animation.py](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 54)

## Internal implementation anchors

- `_manim_command(manim_executable: str | None) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 125)
- `_venv_python(venv_dir: Path) -> Path` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 131) — Path to the python interpreter inside a venv (platform-specific).
- `_render_env() -> dict[str, str]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 214) — A minimal env for the render subprocess: keep what Python/manim/ffmpeg need to start (PATH, system roots, temp), drop everything vault-shaped.
- `_sandbox_bwrap_path() -> str | None` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 231) — The bubblewrap binary to sandbox renders with, or None off-Linux.
- `_executable_mount_roots(executable: str) -> set[str]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 239) — Install roots (``<root>/bin/exe`` → ``<root>``) for an executable and every hop of its symlink chain, so a venv python that links into e.g.
- `_sandboxed_command(command: list[str], workdir: Path, bwrap: str) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/concept_animation.py), line 259) — Wrap a render command in bubblewrap: every namespace unshared (so no network), system + interpreter mounts read-only, the scratch workdir as the only writable path, and the sandbox dying with the sidecar.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `ConceptAnimationError`, `generate_concept_animation`; statically calls `generate_concept_animation`
- [[Reference/Modules/learnloop_sidecar/handlers/animation|learnloop_sidecar.handlers.animation]] — imports `ConceptAnimationError`, `manim_runtime`, `request_concept_animation`, `resolve_manim_command`; statically calls `manim_runtime`, `request_concept_animation`, `resolve_manim_command`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `STRUCTURED_COMPLETION`, `StructuredTransport`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/authoring/ai_contracts|learnloop.content.authoring.ai_contracts]] — imports `CONCEPT_ANIMATION_PROMPT_VERSION`, `ConceptAnimationContext`, `ManimAnimation`, `concept_animation_prompt`; calls `ConceptAnimationContext`, `concept_animation_prompt`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`; calls `Repository`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`, `animation_video_path`; calls `VaultPaths`, `animation_video_path`

### Platform and third-party dependencies

- Standard library: `__future__`, `ast`, `dataclasses`, `hashlib`, `os`, `pathlib`, `shutil`, `subprocess`, `sys`, `tempfile`, `typing`, `venv`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop_sidecar/handlers/animation|learnloop_sidecar.handlers.animation]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_concept_animation_service.py](../../../../../../../tests/test_concept_animation_service.py) — direct import
  - `test_generate_happy_path_stores_content_addressed_mp4`
  - `test_generate_provider_without_method_fails_typed`
  - `test_generate_render_failure_gets_stderr_repair_then_fails`
  - `test_generate_render_repair_recovers`
  - `test_generate_unexpected_exception_never_wedges_the_row`
  - `test_generate_validator_violation_gets_one_repair_then_fails`
  - `test_request_pending_lock_and_dead_batch_reconciliation`
  - `test_request_requires_consent_enabled_and_known_concept`
  - `test_runner_handler_drives_generation_through_the_queue`
- [tests/test_concept_animation_validator.py](../../../../../../../tests/test_concept_animation_validator.py) — direct import
  - `test_manim_runtime_probe_found_and_missing`
  - `test_render_result_is_plain_dataclass`
  - `test_render_scene_failure_captures_stderr_tail`
  - `test_render_scene_off_linux_runs_direct_without_bwrap`
  - `test_render_scene_requires_bwrap_on_linux`
  - `test_render_scene_sandboxes_with_bwrap`
  - `test_render_scene_success_reads_mp4_and_cleans_temp`
  - `test_render_scene_timeout_is_typed`
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
