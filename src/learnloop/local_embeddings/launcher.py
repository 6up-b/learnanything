"""Launching the local worker: its own capped scope, the locks, the meter (spec §7.2).

* **Scopes, always.** The worker runs as ``systemd-run --user --scope -p
  MemoryMax=12G -p MemorySwapMax=0 -- <env>/bin/python -I worker.py ...``
  and itself refuses to load outside a scope whose ``memory.max`` is at most
  the plan's (``worker.start_problems``).
* **Locks.** Every big GPU job holds the exclusive GPU lock
  (``$XDG_RUNTIME_DIR/learnloop-gpu.lock``) and the full-suite lock
  (``/tmp/learnloop-fullsuite.lock``), so a 12G worker and a 5G full pytest
  gate are never co-resident. Locks are taken non-blocking: a held lock is
  ``waiting_for_gpu`` for the job, never broken and never waited on in a
  request thread.
* **Environment.** ``env -i``-like: PATH, an empty private HOME, what
  ``systemd-run --user`` needs. No key and no app setting reaches the worker.
"""
from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
from typing import Any

from learnloop.local_embeddings import pins
from learnloop.local_embeddings import worker as worker_module
from learnloop.local_embeddings.gpu_meter import GpuMeter, supervise

FULL_SUITE_LOCK = Path("/tmp/learnloop-fullsuite.lock")


class LocksBusy(RuntimeError):
    """Another big GPU job (or a full test gate) holds a lock: wait, never break it."""


def gpu_lock_path() -> Path:
    runtime = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    return Path(runtime) / "learnloop-gpu.lock"


@contextmanager
def gpu_locks(paths: tuple[Path, ...] | None = None) -> Iterator[None]:
    """Hold every lock non-blocking for the block, or raise :class:`LocksBusy`."""

    handles = []
    try:
        for path in paths or (gpu_lock_path(), FULL_SUITE_LOCK):
            path.parent.mkdir(parents=True, exist_ok=True)
            handle = open(path, "a+")  # noqa: SIM115 - closed below
            handles.append(handle)
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise LocksBusy(f"{path} is held by another GPU job or a full test run") from None
        yield
    finally:
        for handle in reversed(handles):
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            finally:
                handle.close()


def scope_command(env_python: Path, job: Path, out: Path, heartbeat: Path, *, unit: str) -> list[str]:
    """The worker inside its own transient scope with the memory caps (keep)."""

    return ["systemd-run", "--user", "--scope", "--quiet", f"--unit={unit}",
            "-p", f"MemoryMax={pins.SCOPE_MEMORY_MAX}", "-p", f"MemorySwapMax={pins.SCOPE_SWAP_MAX}", "--",
            str(env_python), "-I", str(Path(worker_module.__file__).resolve()),
            "--job", str(job), "--out", str(out), "--heartbeat", str(heartbeat)]


def launch_environment(home: Path) -> dict[str, str]:
    home.mkdir(parents=True, exist_ok=True)
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(home), "LANG": "C.UTF-8"}
    for name in ("XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS"):
        if os.environ.get(name):
            env[name] = os.environ[name]
    return env


class ScopedLauncher:
    """The real launcher: the private job file, the scoped worker under the meter, its output."""

    def __init__(self, env_python: Path, *, popen: Callable[..., Any] | None = None) -> None:
        self.env_python = Path(env_python)
        self.popen = popen

    def __call__(self, job: dict[str, Any], workdir: Path, *, meter: GpuMeter, plan_id: str) -> dict[str, Any]:
        workdir.mkdir(parents=True, exist_ok=True)
        os.chmod(workdir, 0o700)
        job_path, out_path, heartbeat = workdir / "job.json", workdir / "out.json", workdir / "heartbeat.json"
        out_path.unlink(missing_ok=True)

        def write_job(deadline: float | None) -> None:
            job["limits"]["deadline_unix"] = deadline
            job_path.write_text(json.dumps(job), encoding="utf-8")
            os.chmod(job_path, 0o600)

        unit = f"learnloop-local-index-{workdir.name}".replace("_", "-")
        kwargs: dict[str, Any] = {} if self.popen is None else {"popen": self.popen}
        supervised = supervise(scope_command(self.env_python, job_path, out_path, heartbeat, unit=unit),
                               meter=meter, plan_id=plan_id, label=workdir.name, heartbeat=heartbeat,
                               env=launch_environment(workdir / "home"), on_open=write_job,
                               log=workdir / "worker.stderr.log", **kwargs)
        output = (json.loads(out_path.read_text(encoding="utf-8")) if out_path.is_file()
                  else {"status": "no_output", "reason": f"the worker wrote no output ({supervised['status']})",
                        "documents": {}, "queries": {}})
        output["supervised"] = supervised
        # The job file carries book text: it never outlives the run.
        job_path.unlink(missing_ok=True)
        return output


__all__ = ["FULL_SUITE_LOCK", "LocksBusy", "ScopedLauncher", "gpu_lock_path", "gpu_locks", "launch_environment",
           "scope_command"]
