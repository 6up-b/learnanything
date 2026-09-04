"""Tiny real media files for animation tests.

``tiny_mp4`` builds a genuine H.264 clip with PyAV so probe/remux/concat code
runs against real container structure instead of placeholder bytes. Tests
that call it skip when PyAV is not importable.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


def tiny_mp4(
    *,
    frames: int = 12,
    fps: int = 15,
    size: tuple[int, int] = (64, 48),
    start_seconds: float = 0.0,
    audio_seconds: float = 0.0,
) -> bytes:
    """A real mp4 (``frames`` at ``fps``; 12 @ 15 = 0.8 s like a manim fragment).

    ``start_seconds`` shifts every video timestamp (a clip whose first frame
    is not at t=0); ``audio_seconds`` adds a silent AAC track of that length
    (a container longer than its video track). Both shapes come out of video
    models and must not confuse the stitcher."""

    av = pytest.importorskip("av")
    np = pytest.importorskip("numpy")
    from fractions import Fraction

    width, height = size
    with tempfile.TemporaryDirectory(prefix="learnloop-tiny-mp4-") as tmp:
        path = Path(tmp) / "clip.mp4"
        with av.open(str(path), mode="w", format="mp4") as container:
            stream = container.add_stream("libx264", rate=fps)
            stream.width = width
            stream.height = height
            stream.pix_fmt = "yuv420p"
            if start_seconds:
                # Explicit timestamps (the default path lets the encoder number
                # frames itself, which is what manim's output looks like).
                stream.time_base = Fraction(1, fps * 1000)
            audio = None
            if audio_seconds > 0:
                audio = container.add_stream("aac", rate=48000)
                audio.layout = "mono"
            for index in range(frames):
                pixels = np.full((height, width, 3), (index * 20) % 256, dtype=np.uint8)
                frame = av.VideoFrame.from_ndarray(pixels, format="rgb24")
                if start_seconds:
                    frame.pts = int(round((start_seconds + index / fps) * fps * 1000))
                    frame.time_base = stream.time_base
                for packet in stream.encode(frame):
                    container.mux(packet)
            for packet in stream.encode():
                container.mux(packet)
            if audio is not None:
                samples_per_frame = 1024
                total = int(audio_seconds * 48000)
                pts = 0
                while pts < total:
                    chunk = np.zeros((1, samples_per_frame), dtype=np.float32)
                    aframe = av.AudioFrame.from_ndarray(chunk, format="fltp", layout="mono")
                    aframe.sample_rate = 48000
                    aframe.pts = pts
                    aframe.time_base = Fraction(1, 48000)
                    for packet in audio.encode(aframe):
                        container.mux(packet)
                    pts += samples_per_frame
                for packet in audio.encode():
                    container.mux(packet)
        return path.read_bytes()
