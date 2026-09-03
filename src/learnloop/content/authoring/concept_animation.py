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
import logging
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from learnloop.ai.transport import (
    STRUCTURED_COMPLETION,
    StructuredTransport,
    execute_structured_operation,
)
from learnloop.content.authoring.ai_contracts import (
    CONCEPT_ANIMATION_SCENE_SCAFFOLD,
    ConceptAnimationContext,
    ManimAnimation,
    concept_animation_prompt,
)
from learnloop.content.authoring.animation_media import probe_duration_seconds, remux_faststart

logger = logging.getLogger(__name__)

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
# manim quality flag -> (resolution, fps); the prompt cites these for layout.
_QUALITY_PRESETS: dict[str, tuple[str, int]] = {
    "ql": ("854x480", 15),
    "qm": ("1280x720", 30),
    "qh": ("1920x1080", 60),
}
# Static pacing tolerance above the configured maximum before the lint objects.
_PACING_OVER_SLACK_SECONDS = 15.0


def quality_preset(quality: str | None) -> tuple[str, int]:
    return _QUALITY_PRESETS.get((quality or "qm").lower(), _QUALITY_PRESETS["qm"])


class ConceptAnimationError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def author_concept_animation(
    client: StructuredTransport, context: ConceptAnimationContext
) -> ManimAnimation:
    """Author one animation candidate through the shared transport."""

    return execute_structured_operation(
        client,
        purpose="concept_animation",
        prompt=concept_animation_prompt(context),
        result_model=ManimAnimation,
    )


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


def _venv_python(venv_dir: Path) -> Path:
    """Path to the python interpreter inside a venv (platform-specific)."""

    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def provision_animation_venv(venv_dir: Path, *, package_spec: str = "manim") -> Path:
    """Create an isolated venv and install manim into it (blocking).

    Bootstraps a fresh virtualenv from the ambient interpreter and pip-installs
    manim, so model-authored scene code runs against a package set separate from
    the app's own environment. Returns the venv's python path. Raises on failure
    (callers fall back to the ambient interpreter)."""

    import venv as _venv

    _venv.EnvBuilder(with_pip=True, clear=False).create(str(venv_dir))
    py = _venv_python(venv_dir)
    subprocess.run(
        [str(py), "-m", "pip", "install", "--upgrade", "pip", package_spec],
        check=True,
        capture_output=True,
        timeout=1800,
    )
    return py


def resolve_manim_command(config: Any, vault_root: Path | None = None) -> list[str]:
    """Resolve the command prefix that runs manim, honoring animation config.

    Priority: an explicit ``manim_executable`` override → a dedicated animation
    venv (``venv_path``; isolates model-authored scene code from the app's own
    packages) → the ambient interpreter (``sys.executable``, i.e. the Python
    environment the app was launched from — conda/venv, per the sidecar's
    interpreter selection). Falls back to the ambient interpreter when a
    configured venv is missing and cannot be provisioned."""

    manim_executable = getattr(config, "manim_executable", None)
    if manim_executable:
        return [manim_executable]
    venv_path = getattr(config, "venv_path", None)
    if venv_path:
        venv_dir = Path(venv_path).expanduser()
        if vault_root is not None and not venv_dir.is_absolute():
            venv_dir = vault_root / venv_dir
        py = _venv_python(venv_dir)
        if not py.exists() and getattr(config, "auto_provision_venv", False):
            try:
                py = provision_animation_venv(venv_dir)
            except (OSError, subprocess.SubprocessError):
                py = None  # fall back to the ambient interpreter below
        if py is not None and py.exists():
            return [str(py), "-m", "manim"]
    return [sys.executable, "-m", "manim"]


def manim_runtime(
    manim_executable: str | None = None,
    *,
    manim_command: list[str] | None = None,
    run=subprocess.run,
) -> dict[str, Any]:
    """Probe whether manim is installed/renderable — cheap, no scene involved."""

    prefix = manim_command or _manim_command(manim_executable)
    command = [*prefix, "--version"]
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
                     "PATH", "LANG", "LC_", "PYTHON", "VIRTUAL_ENV", "CONDA", "FONTCONFIG")
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


def _sandboxed_command(command: list[str], workdir: Path, bwrap: str) -> list[str]:
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
    # command[0] is whatever interpreter/executable resolve_manim_command
    # picked (dedicated animation venv, conda env, explicit override) — mount
    # its install tree too, or the sandboxed exec fails.
    if command:
        prefixes |= _executable_mount_roots(command[0])
    for prefix in sorted(prefixes):
        if prefix and prefix != "/usr" and not prefix.startswith("/usr/"):
            args += ["--ro-bind-try", prefix, prefix]
    args += ["--bind", str(workdir), str(workdir), "--chdir", str(workdir)]
    return [*args, "--", *command]


def _combined_scene_videos(media_root: Path, scene_class: str) -> list[Path]:
    """The combined scene mp4(s) under manim's media dir, oldest first.

    Manim writes one fragment per ``self.play`` under ``partial_movie_files/``
    beside the combined ``<SceneClass>.mp4``. A plain ``sorted(glob)[-1]``
    returns a fragment (``partial_movie_files`` sorts after any capitalised
    class name), which is how animations used to be stored as their last
    fragment only. Fragments are excluded and the file named after the scene
    class is preferred over any other combined output."""

    candidates = [
        path
        for path in media_root.glob("videos/**/*.mp4")
        if "partial_movie_files" not in path.parts
    ]
    named = [path for path in candidates if path.stem == scene_class]
    return sorted(named or candidates, key=lambda path: path.stat().st_mtime)


# ---------------------------------------------------------------------------
# Static pacing estimate: the sum of self.play run_times and self.wait pauses
# in construct(), following helper methods and constant range() loops. Rough
# by design (rate functions and data-dependent loops are ignored); it exists
# to catch a 3-second "explainer", not to time a scene.
# ---------------------------------------------------------------------------


def _const_number(node: ast.AST, env: dict[str, float]) -> float | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return float(node.value)
    if isinstance(node, ast.Name):
        return env.get(node.id)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _const_number(node.operand, env)
        return -inner if inner is not None else None
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
        left = _const_number(node.left, env)
        right = _const_number(node.right, env)
        if left is None or right is None:
            return None
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        return left / right if right else None
    return None


def _scene_base_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _self_call_name(call: ast.Call) -> str | None:
    func = call.func
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "self":
        return func.attr
    return None


def estimate_scene_duration(code: str) -> float | None:
    """Seconds of animation implied by the Scene subclass's construct(), or None."""

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None
    scene = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            and any(_scene_base_name(base) in ALLOWED_SCENE_BASES for base in node.bases)
        ),
        None,
    )
    if scene is None:
        return None
    methods = {node.name: node for node in scene.body if isinstance(node, ast.FunctionDef)}
    if "construct" not in methods:
        return None

    def call_cost(call: ast.Call, env: dict[str, float], depth: int) -> float:
        name = _self_call_name(call)
        if name is None:
            return 0.0
        keywords = {kw.arg: kw.value for kw in call.keywords if kw.arg}
        if name == "wait":
            source = call.args[0] if call.args else keywords.get("duration")
            if source is None:
                return 1.0
            value = _const_number(source, env)
            return value if value is not None else 1.0
        if name == "play":
            if "run_time" not in keywords:
                return 1.0
            value = _const_number(keywords["run_time"], env)
            return value if value is not None else 1.0
        if name in methods and depth < 3:
            overrides = {
                key: value
                for key, node in keywords.items()
                if (value := _const_number(node, env)) is not None
            }
            return method_cost(name, overrides, depth + 1)
        return 0.0

    def statements_cost(statements: list[ast.stmt], env: dict[str, float], depth: int) -> float:
        total = 0.0
        for statement in statements:
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if isinstance(statement, ast.For):
                repeats = 1.0
                iterator = statement.iter
                if (
                    isinstance(iterator, ast.Call)
                    and isinstance(iterator.func, ast.Name)
                    and iterator.func.id == "range"
                    and iterator.args
                ):
                    bounds = [_const_number(arg, env) for arg in iterator.args[:2]]
                    if all(bound is not None for bound in bounds):
                        start = bounds[0] if len(bounds) == 2 else 0.0
                        repeats = max(0.0, float(bounds[-1]) - float(start))
                total += repeats * statements_cost(statement.body, env, depth)
                total += statements_cost(statement.orelse, env, depth)
                continue
            if isinstance(statement, (ast.While, ast.If)):
                total += statements_cost(statement.body, env, depth)
                total += statements_cost(statement.orelse, env, depth)
                continue
            if isinstance(statement, ast.With):
                total += statements_cost(statement.body, env, depth)
                continue
            if isinstance(statement, ast.Try):
                total += statements_cost(statement.body, env, depth)
                for handler in statement.handlers:
                    total += statements_cost(handler.body, env, depth)
                total += statements_cost(statement.finalbody, env, depth)
                continue
            for node in ast.walk(statement):
                if isinstance(node, ast.Call):
                    total += call_cost(node, env, depth)
        return total

    def method_cost(name: str, overrides: dict[str, float], depth: int) -> float:
        function = methods[name]
        env: dict[str, float] = {}
        positional = function.args.args[1:] if function.args.args else []
        defaults = function.args.defaults
        for param, default in zip(positional[len(positional) - len(defaults):], defaults):
            value = _const_number(default, env)
            if value is not None:
                env[param.arg] = value
        for param, default in zip(function.args.kwonlyargs, function.args.kw_defaults):
            if default is None:
                continue
            value = _const_number(default, env)
            if value is not None:
                env[param.arg] = value
        env.update(overrides)
        return statements_cost(function.body, env, depth)

    return round(method_cost("construct", {}, 0), 2)


def pacing_band(config: Any) -> tuple[int, int]:
    """The (min, max) running time the prompt targets and the lint enforces.

    A vault written before ``min_duration_seconds`` existed can carry a
    ``max_duration_seconds`` below the new default minimum; the minimum yields
    so the model is never asked for "between 30 and 25 seconds"."""

    minimum = int(config.min_duration_seconds)
    maximum = int(config.max_duration_seconds)
    if maximum > 0:
        minimum = min(minimum, maximum)
    return minimum, maximum


def lint_scene_pacing(code: str, *, min_seconds: float, max_seconds: float) -> list[str]:
    """Human-readable pacing violations for a repair round-trip (empty = fine)."""

    if min_seconds <= 0 and max_seconds <= 0:
        return []
    estimate = estimate_scene_duration(code)
    if estimate is None:
        return []
    if min_seconds > 0 and estimate < min_seconds:
        return [
            f"estimated running time {estimate:.0f}s is below the {min_seconds:.0f}s minimum: "
            "add beats and longer self.wait() pauses"
        ]
    if max_seconds > 0 and estimate > max_seconds + _PACING_OVER_SLACK_SECONDS:
        return [
            f"estimated running time {estimate:.0f}s exceeds the {max_seconds:.0f}s maximum: "
            "cut beats or shorten run_time/wait values"
        ]
    return []


def render_scene(
    scene_code: str,
    scene_class: str,
    *,
    quality: str = "ql",
    timeout_seconds: int = 300,
    manim_executable: str | None = None,
    manim_command: list[str] | None = None,
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

    prefix = manim_command or _manim_command(manim_executable)
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
            *prefix,
            "render",
            quality_flag,
            "--media_dir",
            str(workdir / "media"),
            str(scene_path),
            scene_class,
        ]
        env = _render_env()
        if bwrap is not None:
            command = _sandboxed_command(command, workdir, bwrap)
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
        videos = _combined_scene_videos(workdir / "media", scene_class)
        if not videos:
            return RenderResult(
                False,
                None,
                stderr_tail or "manim produced no combined mp4 (only partial movie files)",
                result.returncode,
            )
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

    from learnloop.content.authoring.ai_contracts import CONCEPT_ANIMATION_PROMPT_VERSION

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
        min_duration_seconds=pacing_band(config)[0],
        max_duration_seconds=pacing_band(config)[1],
        latex_available=config.latex_enabled,
        resolution=quality_preset(config.quality)[0],
        fps=quality_preset(config.quality)[1],
        scene_scaffold=CONCEPT_ANIMATION_SCENE_SCAFFOLD,
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
    # Resolve the manim interpreter once: explicit override → dedicated isolated
    # venv → the ambient env the app launched from (conda/venv). Passed to every
    # render call; test-injected renderers ignore it via **kwargs.
    manim_command = resolve_manim_command(config, vault.root)

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
        if not client.supports(STRUCTURED_COMPLETION):
            return _fail(
                "generation",
                "the configured provider does not support animation authoring",
            )
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
        animation = author_concept_animation(client, context)
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
        repaired_once = False
        if violations:
            repaired_once = True
            # One corrective round-trip naming the exact violations.
            repair_context = build_animation_context(
                vault,
                concept_id=row["concept_id"],
                learning_object_id=row.get("learning_object_id"),
                repair={"previous_code": animation.scene_code, "violations": violations},
            )
            animation = author_concept_animation(client, repair_context)
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

        # Pacing is a soft gate: a scene that comes in far too short gets one
        # round-trip (when no repair has been spent yet), then renders as is.
        # The round-trip can only improve things: a repaired scene that fails
        # the security validator is discarded and the original (valid) scene
        # renders instead of failing the job over pacing.
        min_seconds, max_seconds = pacing_band(config)
        pacing = lint_scene_pacing(animation.scene_code, min_seconds=min_seconds, max_seconds=max_seconds)
        if pacing and not repaired_once:
            repaired_once = True
            repository.update_concept_animation(animation_id, repair_attempted=1, clock=clock)
            repair_context = build_animation_context(
                vault,
                concept_id=row["concept_id"],
                learning_object_id=row.get("learning_object_id"),
                repair={"previous_code": animation.scene_code, "violations": pacing},
            )
            repaired = author_concept_animation(client, repair_context)
            repaired_class, violations = validate_scene_code(repaired.scene_code)
            if violations:
                logger.warning(
                    "pacing repair for animation %s produced an invalid scene (%s); rendering the original",
                    animation_id,
                    "; ".join(violations),
                )
            else:
                animation = repaired
                scene_class = repaired_class or repaired.scene_class
                repository.update_concept_animation(
                    animation_id,
                    scene_code=animation.scene_code,
                    scene_class=scene_class,
                    title=animation.title or None,
                    narration_md=animation.narration_md or None,
                    clock=clock,
                )

        repository.update_concept_animation(animation_id, status="rendering", clock=clock)
        result = render(
            animation.scene_code,
            scene_class,
            quality=config.quality,
            timeout_seconds=config.timeout_seconds,
            manim_executable=config.manim_executable,
            manim_command=manim_command,
        )
        if not result.ok and config.auto_repair:
            repository.update_concept_animation(animation_id, repair_attempted=1, clock=clock)
            repair_context = build_animation_context(
                vault,
                concept_id=row["concept_id"],
                learning_object_id=row.get("learning_object_id"),
                repair={"previous_code": animation.scene_code, "render_stderr": result.stderr_tail},
            )
            animation = author_concept_animation(client, repair_context)
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
                manim_command=manim_command,
            )
        if not result.ok:
            return _fail("render", "manim render failed", stderr=result.stderr_tail)

        # The hash names the STORED bytes: remuxed for streaming playback, so a
        # re-render of byte-identical manim output still dedupes.
        video_bytes = remux_faststart(result.video_bytes)
        digest = "sha256:" + hashlib.sha256(video_bytes).hexdigest()
        video_path = animation_video_path(vault.root, digest)
        if not video_path.is_file():
            video_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = video_path.with_name(video_path.name + ".tmp")
            tmp.write_bytes(video_bytes)
            tmp.replace(video_path)
        from learnloop.clock import utc_now_iso

        repository.update_concept_animation(
            animation_id,
            status="completed",
            video_hash=digest,
            video_file_name=video_path.name,
            duration_seconds=probe_duration_seconds(video_bytes),
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
