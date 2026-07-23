from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method


class RunCliCommandInput(ParamsModel):
    argv: list[str]


@method("run_cli_command", RunCliCommandInput)
def run_cli_command(ctx: SidecarContext, params: RunCliCommandInput) -> dict[str, Any]:
    vault, _repository = ctx.require_vault()
    argv = [str(arg) for arg in params.argv if str(arg)]
    if not argv:
        raise SidecarError("validation_error", "CLI command is empty.")

    normalized = [arg for arg in argv if arg != "learnloop"]
    if not normalized:
        raise SidecarError("validation_error", "CLI command is empty.")

    # This command must execute inside the long-lived sidecar process: a spawned
    # CLI process cannot reach the SDK turn handle owned by an ingest worker.
    if normalized[0] == "kill-codex":
        if len(normalized) > 2:
            return _cli_result(normalized, 2, "", "usage: kill-codex [job_id]\n")
        try:
            result = ctx.ingest_jobs.interrupt_codex(normalized[1] if len(normalized) == 2 else None)
        except ValueError as exc:
            return _cli_result(normalized, 1, "", f"{exc}\n")
        return _cli_result(
            normalized,
            0,
            (
                f"Interrupted Codex call for {result['job_type']} job {result['job_id']} "
                f"(batch {result['batch_id']}). The batch can be resumed from Ingest.\n"
            ),
            "",
        )

    cli_argv = [*normalized]
    if _should_inject_vault(cli_argv):
        cli_argv.extend(["--vault", str(vault.root)])

    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    source_root = str(Path(__file__).resolve().parents[2])
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        source_root
        if not existing_pythonpath
        else source_root + os.pathsep + existing_pythonpath
    )
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "learnloop", *cli_argv],
            cwd=str(vault.root),
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        raise SidecarError("cli_spawn_failed", f"Could not run learnloop CLI: {exc}") from exc

    if completed.returncode == 0:
        ctx.reload()

    return versioned(
        {
            "argv": ["learnloop", *cli_argv],
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    )


def _cli_result(argv: list[str], exit_code: int, stdout: str, stderr: str) -> dict[str, Any]:
    return versioned(
        {
            "argv": ["learnloop", *argv],
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
        }
    )


def _should_inject_vault(argv: list[str]) -> bool:
    if not argv or argv[0].startswith("-") or argv[0] in {"init", "today"}:
        return False
    for index, arg in enumerate(argv):
        if arg == "--vault" and index + 1 < len(argv):
            return False
        if arg.startswith("--vault="):
            return False
    return True
