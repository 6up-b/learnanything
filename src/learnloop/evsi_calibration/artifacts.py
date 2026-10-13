"""Crash-safe writes for the study's artifacts (fits and reports).

A multisim report holds every stored episode of a run that takes the better
part of two hours; ``--reanalyze`` rewrites it in place. ``Path.write_text``
truncates the destination before writing, so an interruption or a full disk
mid-write would leave neither the old report nor the new one (Codex review
F5). :func:`write_text_atomic` writes a sibling temporary file, flushes and
fsyncs it, then atomically replaces the destination and fsyncs the directory:
a reader sees the old file or the new one, never a torn one.
"""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4


def write_text_atomic(path: Path, text: str) -> None:
    """Replace ``path`` with ``text`` (UTF-8) atomically and durably.

    On any failure the destination is left as it was and the temporary file
    is removed; the exception propagates."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


__all__ = ["write_text_atomic"]
