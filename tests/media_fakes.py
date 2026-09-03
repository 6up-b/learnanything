"""Tiny real media files for animation tests.

``tiny_mp4`` builds a genuine H.264 clip with PyAV so probe/remux/concat code
runs against real container structure instead of placeholder bytes. Tests
that call it skip when PyAV is not importable.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


def tiny_mp4(*, frames: int = 12, fps: int = 15, size: tuple[int, int] = (64, 48)) -> bytes:
    """A real mp4 (``frames`` at ``fps``; 12 @ 15 = 0.8 s like a manim fragment)."""

    av = pytest.importorskip("av")
    np = pytest.importorskip("numpy")
    width, height = size
    with tempfile.TemporaryDirectory(prefix="learnloop-tiny-mp4-") as tmp:
        path = Path(tmp) / "clip.mp4"
        with av.open(str(path), mode="w", format="mp4") as container:
            stream = container.add_stream("libx264", rate=fps)
            stream.width = width
            stream.height = height
            stream.pix_fmt = "yuv420p"
            for index in range(frames):
                pixels = np.full((height, width, 3), (index * 20) % 256, dtype=np.uint8)
                frame = av.VideoFrame.from_ndarray(pixels, format="rgb24")
                for packet in stream.encode(frame):
                    container.mux(packet)
            for packet in stream.encode():
                container.mux(packet)
        return path.read_bytes()
