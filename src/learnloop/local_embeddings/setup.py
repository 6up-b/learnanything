"""The owner-run setup of the local space (spec §10 P1a, §11, Q11).

``learnloop embeddings local setup`` creates the SEPARATE environment (Python
3.12 with E1's exact pins: the app's transformers 4.57.6 cannot load the
model), downloads the pinned revision (33.6 GB, public and ungated) and
verifies every file by size and SHA-256, then records the environment's
software epoch (torch, transformers, CUDA). Only this command creates the
production paths under ``~/.local/share/learnloop/`` (``pins.data_root``).

``--adopt-model-dir`` / ``--adopt-env-python`` record existing artefacts
(for example E1's, which must not be moved or deleted) after the same
verification, with no download. Every process this runs goes through the
injectable ``run`` (the tests pass fakes; the stage runs no setup).
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

from learnloop.local_embeddings import pins
from learnloop.local_embeddings.worker import model_dir_problems

GIB = 1024 ** 3
Runner = Callable[..., Any]

_DOWNLOAD = (
    "import sys\n"
    "from huggingface_hub import snapshot_download\n"
    "snapshot_download(repo_id=sys.argv[1], revision=sys.argv[2], local_dir=sys.argv[3])\n"
)
_INSTALLED = (
    "import json, sys\n"
    "from importlib import metadata\n"
    "found = {}\n"
    "for name in sys.argv[1:]:\n"
    "    try:\n"
    "        found[name] = metadata.version(name)\n"
    "    except metadata.PackageNotFoundError:\n"
    "        found[name] = None\n"
    "print(json.dumps(found))\n"
)
_EPOCH = (
    "import json, torch, transformers\n"
    "print(json.dumps({'torch': torch.__version__, 'transformers': transformers.__version__,"
    " 'cuda': torch.version.cuda or 'none'}))\n"
)


def _run(run: Runner, command: Sequence[str], *, env: dict[str, str] | None = None) -> str:
    completed = run(list(command), capture_output=True, text=True, check=False, env=env)
    if completed.returncode != 0:
        raise RuntimeError(f"`{Path(command[0]).name} ...` failed (exit {completed.returncode})")
    return completed.stdout or ""


def setup_plan(root: Path | None = None) -> dict[str, Any]:
    """What setup would do, measured now (no process started, nothing written)."""

    root = root or pins.data_root()
    env = pins.env_dir(root)
    model = pins.model_dir(root)
    probe = root if root.exists() else next((parent for parent in root.parents if parent.exists()), Path("/"))
    return {"data_root": str(root), "env_dir": str(env), "env_python": str(env / "bin" / "python"),
            "model_dir": str(model), "manifest": str(pins.manifest_path(root)),
            "requirements": [f"python=={pins.LOCAL_PYTHON}", *pins.LOCAL_REQUIREMENTS],
            "model": {"repo": pins.MODEL_REPO, "revision": pins.MODEL_REVISION, "files": len(pins.MODEL_FILES),
                      "bytes": pins.MODEL_DISK_BYTES},
            "disk_free_gib": round(shutil.disk_usage(probe).free / GIB, 1),
            "disk_needed_gib": pins.DOWNLOAD_FREE_DISK_GIB,
            "present": {"env": (env / "bin" / "python").exists(), "model": model.is_dir(),
                        "manifest": pins.manifest_path(root).is_file()}}


def _pinned_requirements() -> dict[str, str]:
    return {requirement.split("==", 1)[0]: requirement.split("==", 1)[1] for requirement in pins.LOCAL_REQUIREMENTS}


def requirement_problems(run: Runner, env_python: Path, env: dict[str, str]) -> list[str]:
    """What the environment lacks against the pins, asked of its own
    interpreter (a path that exists is not an installed environment: an
    interrupted install leaves the interpreter behind; Codex review F16).
    A local version label (``2.14.0+cu130``) satisfies ``==2.14.0`` (PEP 440)."""

    pinned = _pinned_requirements()
    if not Path(env_python).exists():
        return ["the environment's interpreter is missing"]
    try:
        output = _run(run, [str(env_python), "-I", "-c", _INSTALLED, *pinned], env=env)
        installed = json.loads(output.strip().splitlines()[-1])
    except (RuntimeError, ValueError, IndexError):
        return ["the environment's interpreter cannot report its packages"]
    problems = []
    for name, version in sorted(pinned.items()):
        found = installed.get(name) if isinstance(installed, dict) else None
        if found is None:
            problems.append(f"{name}: not installed")
        elif str(found).split("+", 1)[0] != version:
            problems.append(f"{name}: {found} is not the pinned {version}")
    return problems


def _owed_bytes(model: Path) -> int:
    """The pinned bytes a (partial) model directory still lacks (missing or wrong-sized files)."""

    owed = 0
    for name, (size, _digest) in pins.MODEL_FILES.items():
        path = model / name
        if not path.is_file() or path.stat().st_size != int(size):
            owed += int(size)
    return owed


def run_setup(*, root: Path | None = None, run: Runner = subprocess.run, adopt_model_dir: Path | None = None,
              adopt_env_python: Path | None = None, verify_weights: bool = True,
              disk_free: Callable[[Path], int] | None = None) -> dict[str, Any]:
    """Create (or adopt) the environment and the model, verify them, write the manifest.

    Resumable (Codex review F16): completion is judged by what is verified,
    never by a path existing. An environment whose packages do not match the
    pins is installed into again (``uv pip install`` is idempotent); a model
    directory with missing or wrong-sized files is downloaded again (the
    pinned snapshot download resumes what it has). Adopted artefacts are
    checked the same way but never changed: a mismatch is refused."""

    root = root or pins.data_root()
    root.mkdir(parents=True, exist_ok=True)
    plan = setup_plan(root)
    env_python = Path(adopt_env_python) if adopt_env_python else Path(plan["env_python"])
    model = Path(adopt_model_dir) if adopt_model_dir else Path(plan["model_dir"])
    steps: list[str] = []
    clean = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(root / "home"),
             "HF_HUB_DISABLE_TELEMETRY": "1"}
    download_owed = adopt_model_dir is None and (
        not model.is_dir() or bool(model_dir_problems(model, pins.MODEL_FILES, pins.REMOTE_CODE_FILES)))
    if download_owed:
        owed = _owed_bytes(model) if model.is_dir() else pins.MODEL_DISK_BYTES
        # The guardrail scales with what is still owed (a resumed download needs less room).
        needed = pins.DOWNLOAD_FREE_DISK_GIB * GIB * owed / max(pins.MODEL_DISK_BYTES, 1)
        free = (disk_free or (lambda path: shutil.disk_usage(path).free))(root)
        if free < needed:
            raise RuntimeError(f"{free / GIB:.1f} GiB free under {root}; the download needs "
                               f"{needed / GIB:.0f} GiB")
    if adopt_env_python is None:
        if not env_python.exists():
            _run(run, ["uv", "venv", "--python", pins.LOCAL_PYTHON, str(pins.env_dir(root))])
            steps.append("environment created")
        if requirement_problems(run, env_python, clean):
            _run(run, ["uv", "pip", "install", "--python", str(env_python), *pins.LOCAL_REQUIREMENTS])
            steps.append("dependencies installed")
    missing = requirement_problems(run, env_python, clean)
    if missing:
        raise RuntimeError("the environment does not match the pins: " + "; ".join(missing[:5]))
    if download_owed:
        model.parent.mkdir(parents=True, exist_ok=True)
        _run(run, [str(env_python), "-I", "-c", _DOWNLOAD, pins.MODEL_REPO, pins.MODEL_REVISION, str(model)],
             env=clean)
        steps.append("model downloaded")
    problems = model_dir_problems(model, pins.MODEL_FILES, pins.REMOTE_CODE_FILES, verify_digests=verify_weights)
    if problems:
        raise RuntimeError("the model directory does not match the pins: " + "; ".join(problems[:5]))
    epoch = json.loads(_run(run, [str(env_python), "-I", "-c", _EPOCH], env=clean).strip().splitlines()[-1])
    if not {"torch", "transformers", "cuda"} <= set(epoch):
        raise RuntimeError("the environment did not report its software epoch")
    manifest = {"version": 1, "model_dir": str(model), "env_python": str(env_python),
                "repo": pins.MODEL_REPO, "revision": pins.MODEL_REVISION,
                "requirements": list(pins.LOCAL_REQUIREMENTS),
                "software_epoch": {key: str(epoch[key]) for key in ("torch", "transformers", "cuda")},
                "weights_verified": bool(verify_weights), "adopted": {"model": adopt_model_dir is not None,
                                                                      "env": adopt_env_python is not None},
                "recorded_at": datetime.now(timezone.utc).isoformat()}
    path = pins.manifest_path(root)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(manifest, sort_keys=True, indent=1) + "\n", encoding="utf-8")
    os.replace(temporary, path)
    return {"status": "ready", "steps": steps or ["already present"], "manifest": str(path), **manifest}


def load_manifest(root: Path | None = None) -> tuple[dict[str, Any] | None, str | None]:
    """``(manifest, None)`` when setup ran and its artefacts exist, else ``(None, why)``."""

    path = pins.manifest_path(root)
    if not path.is_file():
        return None, "the local model is not set up (run `learnloop embeddings local setup`)"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, "the local setup record cannot be read (rerun `learnloop embeddings local setup`)"
    if manifest.get("revision") != pins.MODEL_REVISION or manifest.get("repo") != pins.MODEL_REPO:
        return None, "the local setup record names another model revision (a new space: rerun setup)"
    if not Path(str(manifest.get("env_python"))).exists() or not Path(str(manifest.get("model_dir"))).is_dir():
        return None, "the local environment or model directory recorded by setup is missing"
    return manifest, None


__all__ = ["load_manifest", "requirement_problems", "run_setup", "setup_plan"]
