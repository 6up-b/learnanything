from __future__ import annotations

import json as jsonlib
import sys
import textwrap
import threading
import time
from dataclasses import asdict, is_dataclass
from typing import Any, Mapping, TextIO

import typer
from pydantic import BaseModel

from learnloop.content.authoring.practice_generation import DiagnosticPracticePlan

_INGEST_SPINNER_FRAMES = ("|", "/", "-", "\\")
_INGEST_PROGRESS_EVENT = "learnloop_ingest_progress"
_WRAP_WIDTH = 96

def _format_elapsed(seconds: float) -> str:
    total_seconds = max(0, int(seconds))
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"

def _json_ingest_progress(phase: str, details: dict[str, Any]) -> None:
    payload = {_INGEST_PROGRESS_EVENT: {"phase": phase, **details}}
    print(jsonlib.dumps(payload, sort_keys=True, separators=(",", ":")), file=sys.stderr, flush=True)

class _AsciiSpinner:
    def __init__(
        self,
        label: str,
        *,
        enabled: bool,
        stream: TextIO | None = None,
        interval: float = 0.2,
    ) -> None:
        self.label = label
        self.enabled = enabled
        self.stream = stream or sys.stderr
        self.interval = interval
        self._interactive = False
        self._last_width = 0
        self._started = 0.0
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def __enter__(self):
        if not self.enabled:
            return self
        self._started = time.monotonic()
        self._interactive = bool(getattr(self.stream, "isatty", lambda: False)())
        if not self._interactive:
            self._write(f"{self.label}... this can take around 200s.\n")
            return self
        self._thread = threading.Thread(target=self._spin, name="learnloop-ingest-spinner", daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, _exc, _traceback) -> bool:
        if not self.enabled:
            return False
        elapsed = _format_elapsed(time.monotonic() - self._started)
        status = "Failed" if exc_type else "Done"
        if self._interactive:
            self._stop.set()
            if self._thread is not None:
                self._thread.join(timeout=self.interval * 2)
            self._write_status(f"{status}: {self.label} in {elapsed}.")
            self._write("\n")
        else:
            self._write(f"{status}: {self.label} in {elapsed}.\n")
        return False

    def _spin(self) -> None:
        frame_index = 0
        while not self._stop.is_set():
            elapsed = _format_elapsed(time.monotonic() - self._started)
            frame = _INGEST_SPINNER_FRAMES[frame_index]
            self._write_status(f"{frame} {self.label} elapsed {elapsed} (usually around 200s)")
            frame_index = (frame_index + 1) % len(_INGEST_SPINNER_FRAMES)
            self._stop.wait(self.interval)

    def _write_status(self, line: str) -> None:
        padding = " " * max(0, self._last_width - len(line))
        self._write(f"\r{line}{padding}")
        self._last_width = len(line)

    def _write(self, text: str) -> None:
        try:
            self.stream.write(text)
            self.stream.flush()
        except OSError:
            self.enabled = False
            self._stop.set()

def _dump(value: object) -> str:
    value = _plain(value)
    return jsonlib.dumps(value, indent=2, sort_keys=True, default=str)

def _plain(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if is_dataclass(value) and not isinstance(value, type):
        return _plain(asdict(value))
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value

def _echo_practice_generation_plan(plan) -> None:
    if not plan.targets:
        typer.echo("No completed probe Learning Objects need more Practice Items.")
        return
    typer.echo(f"Targets: {len(plan.targets)} Learning Object(s), {plan.requested_new_items} requested Practice Item(s).")
    for target in plan.targets:
        typer.echo(
            f"- {target.learning_object_id}: existing={target.existing_practice_items} "
            f"new={target.requested_new_items} probe={target.probe_attempts_completed}/{target.probe_attempts_target}"
        )

def _echo_diagnostic_generation_plan(plan: DiagnosticPracticePlan) -> None:
    if not plan.targets:
        typer.echo("No pending intervention needs require diagnostic Practice Items.")
        return
    typer.echo(f"Targets: {len(plan.targets)} intervention need(s), {plan.requested_new_items} requested diagnostic item(s).")
    for target in plan.targets:
        typer.echo(
            f"- {target.need_id}: {target.learning_object_id} facets={','.join(target.target_facets)} "
            f"band={target.recommended_difficulty_band[0]:.2f}-{target.recommended_difficulty_band[1]:.2f}"
        )

def _echo_ingest_summary(result) -> None:
    reused = "Reused" if result.reused_existing else "Persisted"
    typer.echo(
        f"{reused} proposal {result.patch_id} from {result.source_note_id}: "
        f"auto_applied={result.auto_applied_count} "
        f"review_required={result.review_required_count} invalid={result.invalid_count}"
    )

def _wrap_text(text: str, *, indent: str = "  ") -> list[str]:
    lines: list[str] = []
    for paragraph in str(text).splitlines():
        if not paragraph.strip():
            continue
        lines.extend(
            textwrap.wrap(paragraph.strip(), width=_WRAP_WIDTH, initial_indent=indent, subsequent_indent=indent)
        )
    return lines

def _dim(text: object) -> str:
    return typer.style(str(text), fg=typer.colors.BRIGHT_BLACK)

def _echo_section(title: str) -> None:
    typer.echo("")
    typer.secho(f"── {title} " + "─" * max(2, _WRAP_WIDTH - len(title) - 4), fg=typer.colors.YELLOW)

def _echo_kv(label: str, value: object) -> None:
    if value is None or value == "" or value == [] or value == {}:
        return
    if isinstance(value, float):
        value = f"{value:.3f}"
    typer.echo(f"  {_dim(label + ':')} {value}")

__all__ = [name for name in globals() if not name.startswith("__")]
