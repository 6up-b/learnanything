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
from fractions import Fraction
from pathlib import Path
from typing import Sequence

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


def concat_clips(clips: Sequence[bytes], *, fps: int = 30) -> bytes:
    """Join mp4 clips into one faststart H.264 file by re-encoding.

    Re-encoding (rather than a stream copy) is deliberate: clips from a video
    model can differ in encoder settings, and one uniform stream is what every
    player handles. Frames keep their source timing; the first clip's size is
    the output size and other clips are scaled to it. Audio is dropped."""

    if not clips:
        raise ValueError("concat_clips needs at least one clip")
    if len(clips) == 1:
        return remux_faststart(clips[0])
    import av

    workdir = Path(tempfile.mkdtemp(prefix="learnloop-concat-"))
    try:
        inputs = []
        for index, data in enumerate(clips):
            path = workdir / f"in{index}.mp4"
            path.write_bytes(data)
            inputs.append(path)
        with av.open(str(inputs[0])) as first:
            first_video = next(stream for stream in first.streams if stream.type == "video")
            width, height = first_video.width, first_video.height
        output_path = workdir / "out.mp4"
        time_base = Fraction(1, fps)
        with av.open(str(output_path), mode="w", format="mp4", options={"movflags": "+faststart"}) as target:
            encoder = target.add_stream("libx264", rate=fps)
            encoder.width = width
            encoder.height = height
            encoder.pix_fmt = "yuv420p"
            offset = 0.0
            last_pts = -1
            for path in inputs:
                with av.open(str(path)) as source:
                    video = next(stream for stream in source.streams if stream.type == "video")
                    clip_seconds = (source.duration / av.time_base) if source.duration else None
                    last_seen = 0.0
                    for frame in source.decode(video):
                        if frame.pts is not None and frame.time_base is not None:
                            seconds = float(frame.pts * frame.time_base)
                        else:
                            seconds = last_seen + 1.0 / fps
                        last_seen = seconds
                        pts = int(round((offset + seconds) * fps))
                        if pts <= last_pts:
                            continue
                        out_frame = frame.reformat(width=width, height=height, format="yuv420p")
                        out_frame.pts = pts
                        out_frame.time_base = time_base
                        for packet in encoder.encode(out_frame):
                            target.mux(packet)
                        last_pts = pts
                    offset += clip_seconds if clip_seconds else last_seen + 1.0 / fps
            for packet in encoder.encode():
                target.mux(packet)
        return output_path.read_bytes()
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
