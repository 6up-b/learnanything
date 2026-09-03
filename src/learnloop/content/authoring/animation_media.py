"""mp4 post-processing for stored concept animations.

Kept separate from ``concept_animation`` so a renderer that never runs manim
(a text-to-video model) can share it. Every helper is best-effort by design:
a probe failure must never fail a generation job that already has bytes.
"""

from __future__ import annotations

import io
import logging
import shutil
import struct
import tempfile
from pathlib import Path

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


def remux_faststart(data: bytes) -> bytes:
    """Stream-copy remux so ``moov`` precedes ``mdat``.

    A player that receives the file over a custom URI scheme (the desktop
    ``llmedia://`` store) cannot seek back for a trailing ``moov``; manim and
    most encoders write it last. Returns the input unchanged when it is
    already faststart, PyAV is missing, or the remux fails — storing the
    original is always better than storing nothing."""

    if is_faststart(data):
        return data
    try:
        import av
    except ImportError:
        logger.warning("PyAV is not installed; storing animation without faststart")
        return data
    # The mov muxer needs a real path: faststart writes a sidecar temp file
    # next to the output, so an in-memory target is not an option.
    workdir = Path(tempfile.mkdtemp(prefix="learnloop-remux-"))
    try:
        source_path = workdir / "in.mp4"
        target_path = workdir / "out.mp4"
        source_path.write_bytes(data)
        with av.open(str(source_path)) as source, av.open(
            str(target_path), mode="w", format="mp4", options={"movflags": "+faststart"}
        ) as target:
            streams = [stream for stream in source.streams if stream.type in ("video", "audio")]
            if not streams:
                return data
            add_from_template = getattr(target, "add_stream_from_template", None)  # PyAV >= 14
            mapping = {
                stream.index: (
                    add_from_template(stream) if add_from_template else target.add_stream(template=stream)
                )
                for stream in streams
            }
            for packet in source.demux(*streams):
                if packet.dts is None:  # demuxer flush marker
                    continue
                packet.stream = mapping[packet.stream.index]
                target.mux(packet)
        remuxed = target_path.read_bytes()
        return remuxed if is_faststart(remuxed) else data
    except Exception as exc:  # noqa: BLE001 — never lose a rendered video over a remux
        logger.warning("faststart remux failed; storing the original bytes: %s", exc)
        return data
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
