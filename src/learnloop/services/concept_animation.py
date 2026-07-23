"""AI-generated Manim explainer animations (spec_fork_features §2).

Pipeline: an LLM (routed ``animation`` task — Codex or any OpenRouter model)
authors one Manim CE scene for a concept; the scene code is validated against
a deterministic AST allowlist and rendered by a local ``manim`` subprocess in
a temp directory with a timeout; the mp4 lands content-addressed under
``media/animations/`` and plays inline in the concept inspector.

SECURITY POSTURE, stated honestly: the AST allowlist below is best-effort
hardening against accidents and lazy exfiltration attempts — it is NOT a
sandbox, and a determined adversary-shaped model output could in principle
reach the OS through library internals. The boundaries are (1) the per-run
learner consent click (server-side re-checked before any model call), (2) on
Linux, a mandatory bubblewrap sandbox around the render subprocess — no
network, read-only system/venv mounts, the scratch dir as the only writable
path — and (3) the subprocess constraints everywhere (fresh temp cwd, no
vault paths in the environment, hard timeout). On Linux without ``bwrap``
installed, rendering refuses rather than silently degrading; macOS/Windows
have no bubblewrap and keep the unsandboxed constraints under the same
consent copy.
"""

from __future__ import annotations

import ast
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ALLOWED_IMPORTS = frozenset({"manim", "numpy", "math"})
ALLOWED_SCENE_BASES = {"Scene", "MovingCameraScene", "ThreeDScene", "ZoomedScene"}
_FORBIDDEN_NAMES = frozenset(
    {
        "open", "exec", "eval", "compile", "__import__", "getattr", "setattr",
        "delattr", "globals", "locals", "vars", "input", "breakpoint", "exit",
        "quit", "memoryview",
    }
)
_STDERR_TAIL_CHARS = 8000


class ConceptAnimationError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def validate_scene_code(code: str) -> tuple[str | None, list[str]]:
    """AST-validate LLM scene code. Returns (scene_class_name, violations).

    Best-effort hardening (see module docstring): import allowlist, dangerous
    builtins, dunder attribute access, and a required Scene subclass."""

    violations: list[str] = []
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return None, [f"syntax error: {exc}"]

    scene_class: str | None = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in ALLOWED_IMPORTS:
                    violations.append(f"import of {alias.name!r} is not allowed (only manim, numpy, math)")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if node.level or root not in ALLOWED_IMPORTS:
                violations.append(f"import from {node.module!r} is not allowed (only manim, numpy, math)")
        elif isinstance(node, ast.Name) and node.id in _FORBIDDEN_NAMES:
            violations.append(f"use of {node.id!r} is not allowed")
        elif isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            violations.append(f"dunder attribute access {node.attr!r} is not allowed")
        elif isinstance(node, ast.ClassDef) and scene_class is None:
            for base in node.bases:
                base_name = base.id if isinstance(base, ast.Name) else getattr(base, "attr", "")
                if base_name in ALLOWED_SCENE_BASES:
                    scene_class = node.name
                    break

    if scene_class is None:
        violations.append(
            "no Scene subclass found (need one class deriving from Scene/MovingCameraScene/ThreeDScene)"
        )
    return scene_class, violations


@dataclass(frozen=True)
class RenderResult:
    ok: bool
    video_bytes: bytes | None
    stderr_tail: str
    returncode: int | None


def _manim_command(manim_executable: str | None) -> list[str]:
    if manim_executable:
        return [manim_executable]
    return [sys.executable, "-m", "manim"]


def manim_runtime(manim_executable: str | None = None, *, run=subprocess.run) -> dict[str, Any]:
    """Probe whether manim is installed/renderable — cheap, no scene involved."""

    command = [*_manim_command(manim_executable), "--version"]
    try:
        result = run(command, capture_output=True, timeout=15)
    except FileNotFoundError:
        return {"available": False, "version": None, "reason": "manim executable not found"}
    except subprocess.TimeoutExpired:
        return {"available": False, "version": None, "reason": "manim --version timed out"}
    except OSError as exc:
        return {"available": False, "version": None, "reason": str(exc)}
    if result.returncode != 0:
        stderr = (result.stderr or b"").decode("utf-8", errors="replace").strip()
        return {"available": False, "version": None, "reason": stderr or f"exit {result.returncode}"}
    version = (result.stdout or b"").decode("utf-8", errors="replace").strip() or None
    return {"available": True, "version": version, "reason": None}


def _render_env() -> dict[str, str]:
    """A minimal env for the render subprocess: keep what Python/manim/ffmpeg
    need to start (PATH, system roots, temp), drop everything vault-shaped."""

    import os

    keep_prefixes = ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP", "TMPDIR",
                     "HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "PROGRAMDATA",
                     "PATH", "LANG", "LC_", "PYTHON", "VIRTUAL_ENV", "FONTCONFIG")
    env = {
        key: value
        for key, value in os.environ.items()
        if key.upper().startswith(keep_prefixes) and not key.upper().startswith("LEARNLOOP")
    }
    return env


def _sandbox_bwrap_path() -> str | None:
    """The bubblewrap binary to sandbox renders with, or None off-Linux."""

    if sys.platform != "linux":
        return None
    return shutil.which("bwrap")


def _executable_mount_roots(executable: str) -> set[str]:
    """Install roots (``<root>/bin/exe`` → ``<root>``) for an executable and
    every hop of its symlink chain, so a venv python that links into e.g. a
    uv-managed interpreter tree stays runnable inside the sandbox."""

    import os

    roots: set[str] = set()
    path = Path(executable)
    for _ in range(10):
        if len(path.parents) >= 2:
            roots.add(str(path.parents[1]))
        try:
            target = Path(os.readlink(path))
        except OSError:
            break
        path = target if target.is_absolute() else path.parent / target
    return roots


def _sandboxed_command(
    command: list[str], workdir: Path, bwrap: str, manim_executable: str | None
) -> list[str]:
    """Wrap a render command in bubblewrap: every namespace unshared (so no
    network), system + interpreter mounts read-only, the scratch workdir as
    the only writable path, and the sandbox dying with the sidecar."""

    args = [
        bwrap,
        "--die-with-parent",
        "--new-session",
        "--unshare-all",
        "--proc", "/proc",
        "--dev", "/dev",
        "--tmpfs", "/tmp",
        "--ro-bind", "/usr", "/usr",
        "--ro-bind-try", "/lib", "/lib",
        "--ro-bind-try", "/lib64", "/lib64",
        "--ro-bind-try", "/bin", "/bin",
        "--ro-bind-try", "/sbin", "/sbin",
        # Font/loader config manim + its ffmpeg need; nothing else from /etc.
        "--ro-bind-try", "/etc/fonts", "/etc/fonts",
        "--ro-bind-try", "/etc/alternatives", "/etc/alternatives",
        "--ro-bind-try", "/etc/ld.so.cache", "/etc/ld.so.cache",
    ]
    prefixes = {sys.prefix, sys.base_prefix}
    prefixes |= _executable_mount_roots(sys.executable)
    if manim_executable:
        prefixes |= _executable_mount_roots(manim_executable)
    for prefix in sorted(prefixes):
        if prefix and prefix != "/usr" and not prefix.startswith("/usr/"):
            args += ["--ro-bind-try", prefix, prefix]
    args += ["--bind", str(workdir), str(workdir), "--chdir", str(workdir)]
    return [*args, "--", *command]


def render_scene(
    scene_code: str,
    scene_class: str,
    *,
    quality: str = "ql",
    timeout_seconds: int = 300,
    manim_executable: str | None = None,
    sandbox: bool | None = None,
    run=subprocess.run,
) -> RenderResult:
    """Render one validated scene to mp4 in a fresh temp cwd with a timeout.

    ``sandbox=None`` (the default) requires bubblewrap on Linux — a Linux
    machine without ``bwrap`` gets a typed failure telling the user to install
    it — and runs direct elsewhere (bubblewrap is Linux-only). ``True`` forces
    the requirement on any platform; ``False`` opts out (tests only).

    The ``run`` parameter is the offline-test seam (a fake writes an mp4 into
    the expected media glob). The temp directory is always cleaned."""

    quality_flag = f"-q{quality[-1].lower()}" if quality else "-ql"
    bwrap = None
    if sandbox is not False:
        bwrap = _sandbox_bwrap_path()
        if bwrap is None and (sandbox is True or sys.platform == "linux"):
            return RenderResult(
                False,
                None,
                "sandboxed rendering requires bubblewrap; install it (e.g. "
                "apt install bubblewrap) and retry",
                None,
            )
    workdir = Path(tempfile.mkdtemp(prefix="learnloop-manim-"))
    try:
        scene_path = workdir / "scene.py"
        scene_path.write_text(scene_code, encoding="utf-8")
        command = [
            *_manim_command(manim_executable),
            "render",
            quality_flag,
            "--media_dir",
            str(workdir / "media"),
            str(scene_path),
            scene_class,
        ]
        env = _render_env()
        if bwrap is not None:
            command = _sandboxed_command(command, workdir, bwrap, manim_executable)
            # Caches (matplotlib, fontconfig, manim) land in the scratch dir,
            # the sandbox's only writable path.
            env["HOME"] = str(workdir)
            env["XDG_CACHE_HOME"] = str(workdir / ".cache")
        try:
            result = run(
                command,
                cwd=str(workdir),
                env=env,
                capture_output=True,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            return RenderResult(False, None, f"render timed out after {timeout_seconds}s", None)
        except FileNotFoundError:
            return RenderResult(False, None, "manim executable not found", None)
        stderr_tail = (result.stderr or b"").decode("utf-8", errors="replace")[-_STDERR_TAIL_CHARS:]
        if result.returncode != 0:
            return RenderResult(False, None, stderr_tail, result.returncode)
        videos = sorted((workdir / "media").glob("videos/**/*.mp4"))
        if not videos:
            return RenderResult(False, None, stderr_tail or "manim produced no mp4", result.returncode)
        return RenderResult(True, videos[-1].read_bytes(), stderr_tail, result.returncode)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Request + generation pipeline (rung-variant shaped: sync request row +
# durable job; the service owns every terminal status)
# ---------------------------------------------------------------------------


def request_concept_animation(
    vault: Any,
    repository: Any,
    *,
    concept_id: str,
    learning_object_id: str | None = None,
    consent: bool = False,
    clock: Any = None,
) -> dict[str, Any]:
    """Insert a queued animation row. Fail-closed, no model call, no evidence
    writes — requesting an animation says nothing about mastery."""

    from learnloop.codex.prompts import CONCEPT_ANIMATION_PROMPT_VERSION

    config = vault.config.animation
    if not config.enabled:
        raise ConceptAnimationError("animation_disabled", "[animation] enabled is false in learnloop.toml.")
    if not consent:
        # The UI checkbox is not trusted alone; this server-side re-check is
        # the actual consent gate before any code generation happens.
        raise ConceptAnimationError(
            "consent_required",
            "Generating an animation runs AI-written code locally; explicit consent is required.",
        )
    if concept_id not in vault.concepts:
        raise ConceptAnimationError("concept_not_found", f"Concept {concept_id!r} does not exist.")

    pending = repository.pending_concept_animations(concept_id)
    live = [row for row in pending if not repository.concept_animation_batch_dead(row.get("batch_id"))]
    for row in pending:
        if row not in live:
            # The generating batch died (crash/cancel/restart): free the lock.
            repository.update_concept_animation(
                row["id"],
                status="failed",
                failure_stage=row.get("failure_stage") or "generation",
                failure_reason=row.get("failure_reason") or "generation batch did not complete",
                clock=clock,
            )
    if live:
        raise ConceptAnimationError(
            "animation_pending", f"An animation for {concept_id!r} is already being generated."
        )

    animation_id = repository.insert_concept_animation(
        {
            "concept_id": concept_id,
            "learning_object_id": learning_object_id,
            "status": "queued",
            "prompt_version": CONCEPT_ANIMATION_PROMPT_VERSION,
            "quality": config.quality,
        },
        clock=clock,
    )
    return {"animation_id": animation_id, "concept_id": concept_id, "status": "queued"}


def build_animation_context(
    vault: Any, *, concept_id: str, learning_object_id: str | None, repair: dict | None = None
):
    """Pure prompt-context assembly: concept + a few LO excerpts, never raw
    source text."""

    from learnloop.codex.client import ConceptAnimationContext

    concept = vault.concepts[concept_id]
    config = vault.config.animation
    learning_objects = []
    for lo_id, lo in sorted(getattr(vault, "learning_objects", {}).items()):
        if getattr(lo, "concept", None) != concept_id:
            continue
        if learning_object_id and lo_id != learning_object_id:
            continue
        learning_objects.append(
            {"title": getattr(lo, "title", lo_id), "summary": getattr(lo, "summary", "") or ""}
        )
        if len(learning_objects) >= 4:
            break
    return ConceptAnimationContext(
        concept_id=concept_id,
        concept_title=getattr(concept, "title", concept_id),
        concept_description=getattr(concept, "description", "") or "",
        learning_objects=learning_objects,
        max_duration_seconds=config.max_duration_seconds,
        latex_available=config.latex_enabled,
        repair=repair,
    )


def generate_concept_animation(
    root: Path,
    client: Any,
    *,
    animation_id: str,
    repository: Any = None,
    renderer: Any = None,
    clock: Any = None,
) -> dict[str, Any]:
    """The durable-job body: generate -> validate -> render -> store.

    One corrective LLM round-trip on validator violations, one stderr repair
    round-trip on render failure (when [animation] auto_repair). Any
    unexpected exception marks the row failed before re-raising — a row never
    wedges in a non-terminal state."""

    import hashlib

    from learnloop.db.repositories import Repository
    from learnloop.vault.loader import load_vault
    from learnloop.vault.paths import VaultPaths, animation_video_path

    vault = load_vault(root)
    repository = repository or Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    row = repository.concept_animation(animation_id)
    if row is None:
        raise ConceptAnimationError("animation_not_found", f"Animation {animation_id!r} does not exist.")
    if row["status"] not in ("queued", "generating"):
        return row  # idempotent re-entry after a crash/retry

    config = vault.config.animation
    render = renderer or render_scene

    def _fail(
        stage: str, reason: str, *, stderr: str | None = None, repair_attempted: bool | None = None
    ) -> dict[str, Any]:
        fields: dict[str, Any] = {
            "status": "failed",
            "failure_stage": stage,
            "failure_reason": reason[:2000],
        }
        if stderr is not None:
            fields["render_stderr"] = stderr[-_STDERR_TAIL_CHARS:]
        if repair_attempted is not None:
            fields["repair_attempted"] = int(repair_attempted)
        repository.update_concept_animation(animation_id, clock=clock, **fields)
        return repository.concept_animation(animation_id)

    try:
        run_animation = getattr(client, "run_concept_animation", None)
        if run_animation is None:
            return _fail("generation", "the configured provider does not support animation authoring")

        repository.update_concept_animation(
            animation_id,
            status="generating",
            provider=getattr(client, "provider_name", None),
            model=getattr(client, "model", None),
            clock=clock,
        )
        context = build_animation_context(
            vault, concept_id=row["concept_id"], learning_object_id=row.get("learning_object_id")
        )
        animation = run_animation(context)
        repository.update_concept_animation(
            animation_id,
            scene_code=animation.scene_code,
            scene_class=animation.scene_class,
            title=animation.title,
            narration_md=animation.narration_md,
            status="validating",
            clock=clock,
        )

        scene_class, violations = validate_scene_code(animation.scene_code)
        if violations:
            # One corrective round-trip naming the exact violations.
            repair_context = build_animation_context(
                vault,
                concept_id=row["concept_id"],
                learning_object_id=row.get("learning_object_id"),
                repair={"previous_code": animation.scene_code, "violations": violations},
            )
            animation = run_animation(repair_context)
            repository.update_concept_animation(
                animation_id,
                scene_code=animation.scene_code,
                scene_class=animation.scene_class,
                title=animation.title or None,
                narration_md=animation.narration_md or None,
                clock=clock,
            )
            scene_class, violations = validate_scene_code(animation.scene_code)
            if violations:
                return _fail("validation", "; ".join(violations))
        scene_class = scene_class or animation.scene_class

        repository.update_concept_animation(animation_id, status="rendering", clock=clock)
        result = render(
            animation.scene_code,
            scene_class,
            quality=config.quality,
            timeout_seconds=config.timeout_seconds,
            manim_executable=config.manim_executable,
        )
        if not result.ok and config.auto_repair:
            repository.update_concept_animation(animation_id, repair_attempted=1, clock=clock)
            repair_context = build_animation_context(
                vault,
                concept_id=row["concept_id"],
                learning_object_id=row.get("learning_object_id"),
                repair={"previous_code": animation.scene_code, "render_stderr": result.stderr_tail},
            )
            animation = run_animation(repair_context)
            scene_class, violations = validate_scene_code(animation.scene_code)
            if violations:
                return _fail("validation", "; ".join(violations), repair_attempted=True)
            repository.update_concept_animation(
                animation_id, scene_code=animation.scene_code, scene_class=scene_class, clock=clock
            )
            result = render(
                animation.scene_code,
                scene_class or animation.scene_class,
                quality=config.quality,
                timeout_seconds=config.timeout_seconds,
                manim_executable=config.manim_executable,
            )
        if not result.ok:
            return _fail("render", "manim render failed", stderr=result.stderr_tail)

        digest = "sha256:" + hashlib.sha256(result.video_bytes).hexdigest()
        video_path = animation_video_path(vault.root, digest)
        if not video_path.is_file():
            video_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = video_path.with_name(video_path.name + ".tmp")
            tmp.write_bytes(result.video_bytes)
            tmp.replace(video_path)
        from learnloop.clock import utc_now_iso

        repository.update_concept_animation(
            animation_id,
            status="completed",
            video_hash=digest,
            video_file_name=video_path.name,
            render_stderr=None,
            completed_at=utc_now_iso(clock),
            clock=clock,
        )
        return repository.concept_animation(animation_id)
    except ConceptAnimationError:
        raise
    except Exception as exc:  # noqa: BLE001 — never leave the row wedged
        _fail("generation", str(exc))
        raise
