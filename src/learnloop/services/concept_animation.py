"""AI-generated Manim explainer animations (spec_fork_features §2).

Pipeline: an LLM (routed ``animation`` task — Codex or any OpenRouter model)
authors one Manim CE scene for a concept; the scene code is validated against
a deterministic AST allowlist and rendered by a local ``manim`` subprocess in
a temp directory with a timeout; the mp4 lands content-addressed under
``media/animations/`` and plays inline in the concept inspector.

SECURITY POSTURE, stated honestly: the AST allowlist below is best-effort
hardening against accidents and lazy exfiltration attempts — it is NOT a
sandbox, and a determined adversary-shaped model output could in principle
reach the OS through library internals. The actual boundary is the per-run
learner consent click (server-side re-checked before any model call) plus the
subprocess constraints (fresh temp cwd, no vault paths in the environment,
hard timeout).
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


def render_scene(
    scene_code: str,
    scene_class: str,
    *,
    quality: str = "ql",
    timeout_seconds: int = 300,
    manim_executable: str | None = None,
    run=subprocess.run,
) -> RenderResult:
    """Render one validated scene to mp4 in a fresh temp cwd with a timeout.

    The ``run`` parameter is the offline-test seam (a fake writes an mp4 into
    the expected media glob). The temp directory is always cleaned."""

    quality_flag = f"-q{quality[-1].lower()}" if quality else "-ql"
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
        try:
            result = run(
                command,
                cwd=str(workdir),
                env=_render_env(),
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
