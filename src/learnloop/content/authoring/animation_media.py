"""mp4 post-processing for stored concept animations.

Kept separate from ``concept_animation`` so a renderer that never runs manim
(a text-to-video model) can share it. Every helper is best-effort by design:
a probe failure must never fail a generation job that already has bytes.
"""

from __future__ import annotations

import io
import logging
import struct

logger = logging.getLogger(__name__)


def probe_duration_seconds(data: bytes) -> float | None:
    """Container duration in seconds via PyAV; ``None`` on any failure."""

    try:
        import av
    except ImportError:
        return None
    try:
        with av.open(io.BytesIO(data)) as container:
            if container.duration is None:
                return None
            return round(container.duration / av.time_base, 3)
    except Exception as exc:  # noqa: BLE001 — a probe failure never fails the job
        logger.warning("animation duration probe failed: %s", exc)
        return None


def top_level_atoms(data: bytes) -> list[str]:
    """Names of the top-level ISO-BMFF boxes in file order (ftyp, moov, mdat, ...)."""

    atoms: list[str] = []
    offset = 0
    while offset + 8 <= len(data):
        size, kind = struct.unpack(">I4s", data[offset : offset + 8])
        if size == 1:  # 64-bit "largesize" follows the header
            if offset + 16 > len(data):
                break
            size = struct.unpack(">Q", data[offset + 8 : offset + 16])[0]
        elif size == 0:  # box extends to the end of the file
            size = len(data) - offset
        atoms.append(kind.decode("latin-1"))
        offset += max(size, 8)
    return atoms


def is_faststart(data: bytes) -> bool:
    """True when ``moov`` precedes ``mdat``: the file plays without seeking back."""

    atoms = top_level_atoms(data)
    return "moov" in atoms and "mdat" in atoms and atoms.index("moov") < atoms.index("mdat")
