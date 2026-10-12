"""The PF-b sandbox for LLM-written Python (Slice 2 §5.3, P7).

Generator programs and LLM-written sympy equivalence checks run unattended, so
the boundary is mandatory everywhere: generation **fails closed** wherever
bubblewrap is unavailable (macOS and Windows included). Unlike animation
rendering there is no consent-gated direct fallback, and ``python -I`` alone is
not a sandbox.

The command is wrapped by ``concept_animation._sandboxed_command``: every
namespace unshared (no network), read-only system and interpreter mounts, a
fresh tmpfs ``/tmp``, the scratch directory as the only writable path and
``--die-with-parent``. On top of that this module sets CPU, address-space,
file-size and core rlimits, a wall-clock timeout that kills the whole tree, an
environment with no vault paths or API keys, and a bounded output size.

Two harness protocols run inside it:

* ``pf-generator-v1``: the program defines ``generate(seed) -> dict`` returning
  ``parameters``, ``stem``, ``solution``, ``final_answer`` and ``checkpoints``,
  and ``check(draw, answer) -> bool`` that verifies an answer by sympy or exact
  evaluation. ``test`` mode draws and self-checks (with negative controls);
  ``check`` mode verifies other answers (panel solves) against draws.
* ``pf-equivalence-v1``: each program defines ``check(reference, answer) ->
  bool``; ``equivalence`` mode runs every (program, reference, answer) pair.

Both report a sympy normal form of each final answer where it parses, computed
inside the sandbox (parsing model text with sympy evaluates it).
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Callable, Mapping

from learnloop.content.authoring.concept_animation import _sandbox_bwrap_path, _sandboxed_command

GENERATOR_PROTOCOL = "pf-generator-v1"
EQUIVALENCE_PROTOCOL = "pf-equivalence-v1"
_OUTPUT_MARKER = "@@PF-SANDBOX-RESULT@@"


class SandboxUnavailable(RuntimeError):
    """Bubblewrap is missing: PF generation refuses rather than running unsandboxed."""


@dataclass(frozen=True)
class SandboxLimits:
    cpu_seconds: int = 20
    memory_mb: int = 2048
    wall_seconds: int = 60
    max_output_bytes: int = 2_000_000
    max_file_bytes: int = 16 * 1024 * 1024

    @classmethod
    def from_config(cls, pf_config: Any) -> SandboxLimits:
        return cls(
            cpu_seconds=pf_config.sandbox_cpu_seconds,
            memory_mb=pf_config.sandbox_memory_mb,
            wall_seconds=pf_config.sandbox_wall_seconds,
        )


@dataclass(frozen=True)
class SandboxResult:
    ok: bool
    output: Any = None
    error: str | None = None
    returncode: int | None = None
    timed_out: bool = False
    stderr_tail: str = ""
    limits: dict[str, int] = field(default_factory=dict)


def sandbox_available() -> bool:
    return _sandbox_bwrap_path() is not None


def require_sandbox() -> str:
    bwrap = _sandbox_bwrap_path()
    if bwrap is None:
        raise SandboxUnavailable(
            "PF generation requires the bubblewrap sandbox (Linux `bwrap`); it is "
            "unavailable here, so generation refuses rather than running model-written "
            "code unsandboxed. Install bubblewrap (e.g. apt install bubblewrap)."
        )
    return bwrap


def _environment(workdir: Path) -> dict[str, str]:
    # Explicit and minimal: no vault paths, no API keys, no PYTHON* variables
    # (``-I`` ignores them anyway), caches inside the scratch directory.
    return {
        "PATH": "/usr/bin:/bin",
        "HOME": str(workdir),
        "TMPDIR": "/tmp",
        "LANG": "C.UTF-8",
        "XDG_CACHE_HOME": str(workdir / ".cache"),
        "PYTHONDONTWRITEBYTECODE": "1",
        "MPLCONFIGDIR": str(workdir / ".cache"),
    }


def _limit_resources(limits: SandboxLimits) -> Callable[[], None]:
    def apply() -> None:  # pragma: no cover - runs in the forked child
        resource.setrlimit(resource.RLIMIT_CPU, (limits.cpu_seconds, limits.cpu_seconds + 1))
        memory = limits.memory_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
        resource.setrlimit(resource.RLIMIT_FSIZE, (limits.max_file_bytes, limits.max_file_bytes))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

    return apply


def run_sandboxed_python(
    harness: str, payload: Mapping[str, Any], *, modules: Mapping[str, str] | None = None,
    limits: SandboxLimits | None = None, run: Callable[..., Any] = subprocess.run,
) -> SandboxResult:
    """Run ``harness`` (Python source) on JSON ``payload`` inside bubblewrap.

    ``modules`` are extra source files (name -> code) written beside it. The
    harness prints one JSON result after ``_OUTPUT_MARKER`` on stdout.
    """
    limits = limits or SandboxLimits()
    bwrap = require_sandbox()
    workdir = Path(tempfile.mkdtemp(prefix="learnloop-pf-"))
    try:
        (workdir / "harness.py").write_text(harness, encoding="utf-8")
        for name, code in (modules or {}).items():
            if not name.isidentifier():
                raise ValueError(f"Invalid sandbox module name: {name!r}")
            (workdir / f"{name}.py").write_text(code, encoding="utf-8")
        (workdir / "input.json").write_text(json.dumps(dict(payload), sort_keys=True), encoding="utf-8")
        command = _sandboxed_command(
            [sys.executable, "-I", "-B", str(workdir / "harness.py"), str(workdir)], workdir, bwrap,
        )
        # Unattended code: also make the sandbox's own root read-only, so even
        # ephemeral writes outside scratch (and the private /tmp) fail.
        separator = command.index("--")
        command[separator:separator] = ["--remount-ro", "/"]
        try:
            completed = run(
                command, cwd=str(workdir), env=_environment(workdir), capture_output=True,
                timeout=limits.wall_seconds, preexec_fn=_limit_resources(limits),
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(False, error=f"timed out after {limits.wall_seconds}s",
                                 timed_out=True, limits=_limit_dict(limits))
        stdout = completed.stdout or b""
        stderr = (completed.stderr or b"").decode("utf-8", errors="replace")[-2000:]
        if len(stdout) > limits.max_output_bytes:
            return SandboxResult(False, error="output exceeds the sandbox limit",
                                 returncode=completed.returncode, stderr_tail=stderr,
                                 limits=_limit_dict(limits))
        text = stdout.decode("utf-8", errors="replace")
        if completed.returncode != 0 or _OUTPUT_MARKER not in text:
            return SandboxResult(False, error=f"exit {completed.returncode}",
                                 returncode=completed.returncode, stderr_tail=stderr,
                                 limits=_limit_dict(limits))
        try:
            output = json.loads(text.rsplit(_OUTPUT_MARKER, 1)[1])
        except ValueError:
            return SandboxResult(False, error="unparseable sandbox output",
                                 returncode=completed.returncode, stderr_tail=stderr,
                                 limits=_limit_dict(limits))
        return SandboxResult(True, output=output, returncode=completed.returncode,
                             stderr_tail=stderr, limits=_limit_dict(limits))
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def _limit_dict(limits: SandboxLimits) -> dict[str, int]:
    return {"cpu_seconds": limits.cpu_seconds, "memory_mb": limits.memory_mb,
            "wall_seconds": limits.wall_seconds}


# The harness itself is fixed code; only the program modules are model-written.
_HARNESS = r'''
import importlib, json, signal, sys
workdir = sys.argv[1]
sys.path.insert(0, workdir)
MARKER = "@@PF-SANDBOX-RESULT@@"


def emit(value):
    sys.stdout.write(MARKER + json.dumps(value, sort_keys=True, default=str))
    sys.stdout.flush()


class _Timeout(Exception):
    pass


def _alarm(_signum, _frame):
    raise _Timeout()


signal.signal(signal.SIGALRM, _alarm)


def bounded(seconds, function, *args):
    signal.alarm(seconds)
    try:
        return function(*args)
    finally:
        signal.alarm(0)


def normal_form(answer):
    try:
        import sympy
        return bounded(2, lambda text: sympy.srepr(sympy.simplify(sympy.sympify(text))), str(answer))
    except BaseException:
        return None


def describe(exc):
    return type(exc).__name__ + ": " + str(exc)[:300]


with open(workdir + "/input.json", encoding="utf-8") as handle:
    payload = json.load(handle)
mode = payload["mode"]
result = {"mode": mode}
if mode in ("test", "check"):
    try:
        program = importlib.import_module("program")
    except BaseException as exc:
        emit({"mode": mode, "import_error": describe(exc)})
        sys.exit(0)
    if mode == "test":
        draws = []
        for seed in payload["seeds"]:
            entry = {"seed": seed}
            try:
                draw = bounded(payload.get("per_call_seconds", 5), program.generate, seed)
                if not isinstance(draw, dict):
                    raise TypeError("generate must return a dict")
                draw = json.loads(json.dumps(draw, default=str))
                for key, kind in (("stem", str), ("solution", str), ("final_answer", str),
                                  ("checkpoints", list), ("parameters", dict)):
                    if not isinstance(draw.get(key), kind):
                        raise TypeError("draw field %s must be %s" % (key, kind.__name__))
                entry["draw"] = draw
                entry["self_check"] = bool(bounded(payload.get("per_call_seconds", 5),
                                                   program.check, draw, draw["final_answer"]))
                controls = []
                for wrong in payload.get("negative_controls", []):
                    try:
                        controls.append(bool(bounded(payload.get("per_call_seconds", 5),
                                                     program.check, draw, wrong)))
                    except BaseException:
                        controls.append(False)
                entry["negative_controls_rejected"] = not any(controls)
                entry["normal_form"] = normal_form(draw["final_answer"])
            except BaseException as exc:
                entry["error"] = describe(exc)
            draws.append(entry)
        result["draws"] = draws
    else:
        checks = []
        for pair in payload["pairs"]:
            try:
                checks.append(bool(bounded(payload.get("per_call_seconds", 5),
                                           program.check, pair["draw"], pair["answer"])))
            except BaseException as exc:
                checks.append(None)
        result["checks"] = checks
elif mode == "equivalence":
    loaded, errors = {}, {}
    for name in payload["programs"]:
        try:
            loaded[name] = importlib.import_module(name)
        except BaseException as exc:
            errors[name] = describe(exc)
    checks = []
    for pair in payload["pairs"]:
        module = loaded.get(pair["program"])
        if module is None:
            checks.append(None)
            continue
        try:
            checks.append(bool(bounded(payload.get("per_call_seconds", 5), module.check,
                                       pair["reference"], pair["answer"])))
        except BaseException:
            checks.append(None)
    result["checks"] = checks
    result["import_errors"] = errors
    result["normal_forms"] = {key: normal_form(value)
                              for key, value in payload.get("normal_forms", {}).items()}
else:
    result["error"] = "unknown mode"
emit(result)
'''

NEGATIVE_CONTROLS = ("", "zzz_not_an_answer", "-987654321.123")


def run_generator_tests(
    code: str, *, seeds: list[int], limits: SandboxLimits | None = None,
    run: Callable[..., Any] = subprocess.run,
) -> SandboxResult:
    """Draw ``seeds`` and self-check each draw, with negative controls."""
    return run_sandboxed_python(
        _HARNESS, {"mode": "test", "seeds": seeds, "negative_controls": list(NEGATIVE_CONTROLS)},
        modules={"program": code}, limits=limits, run=run,
    )


def check_generator_answers(
    code: str, pairs: list[dict[str, Any]], *, limits: SandboxLimits | None = None,
    run: Callable[..., Any] = subprocess.run,
) -> SandboxResult:
    """Verify each ``{"draw", "answer"}`` pair with the program's own ``check``."""
    return run_sandboxed_python(
        _HARNESS, {"mode": "check", "pairs": pairs}, modules={"program": code},
        limits=limits, run=run,
    )


def run_equivalence_checks(
    programs: Mapping[str, str], pairs: list[dict[str, str]], *,
    normal_forms: Mapping[str, str] | None = None, limits: SandboxLimits | None = None,
    run: Callable[..., Any] = subprocess.run,
) -> SandboxResult:
    """Run LLM-written ``check(reference, answer)`` programs on their pairs."""
    names = {name: f"equivalence_{index}" for index, name in enumerate(sorted(programs))}
    return run_sandboxed_python(
        _HARNESS, {
            "mode": "equivalence", "programs": sorted(names.values()),
            "pairs": [{**pair, "program": names[pair["program"]]} for pair in pairs],
            "normal_forms": dict(normal_forms or {}),
        },
        modules={names[name]: code for name, code in programs.items()}, limits=limits, run=run,
    )


__all__ = [
    "EQUIVALENCE_PROTOCOL", "GENERATOR_PROTOCOL", "NEGATIVE_CONTROLS", "SandboxLimits",
    "SandboxResult", "SandboxUnavailable", "check_generator_answers", "require_sandbox",
    "run_equivalence_checks", "run_sandboxed_python", "sandbox_available",
    "run_generator_tests",
]
