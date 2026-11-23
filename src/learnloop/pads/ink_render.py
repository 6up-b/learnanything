"""Strokes to an image, on the server, deterministically (spec §10.10: ``ink.transcribe`` renders the strokes and
sends the image).

The image is the ink as the learner saw it: the spec's pen (§4.2: stroke ``#2b4fa8``, 2.2 px) on the paper it was
drawn on (a pad's ``#fdfdfc``, a source's ``#f7f5f0``), at the device pixel ratio the strokes were drawn at, cropped
to the strokes with a margin of one pen width so a round end is never cut. Nothing is scaled, smoothed or thinned
beyond that: a size, a smoothing or a stroke model of our own would be a constant nobody chose. Each stroke is one
polyline with round joins and round ends; a one-point stroke is a dot. The same strokes give the same bytes (no
antialiasing, no timestamp in the file).

The canvas is bounded by Pillow's own decompression-bomb limit (``Image.MAX_IMAGE_PIXELS``) and the file by the
transport's image limit (``learnloop.ai.transport.MAX_IMAGE_BYTES``); past either, nothing is drawn or sent.
"""
from __future__ import annotations

import io
import math
from typing import Any

from PIL import Image, ImageDraw

from learnloop.ai.transport import MAX_IMAGE_BYTES

PEN = (0x2B, 0x4F, 0xA8)
PEN_WIDTH_CSS_PX = 2.2
PAD_PAPER = (0xFD, 0xFD, 0xFC)
SOURCE_PAPER = (0xF7, 0xF5, 0xF0)
MEDIA_TYPE = "image/png"


class InkTooLarge(ValueError):
    """The strokes span more than an image may hold."""


def pen_width_px(device_pixel_ratio: float) -> int:
    return max(1, round(PEN_WIDTH_CSS_PX * device_pixel_ratio))


def canvas(strokes: list[dict[str, Any]], device_pixel_ratio: float) -> tuple[int, int, float, float, int]:
    """``(width, height, min_x, min_y, margin)`` in device pixels for these strokes."""

    xs = [float(point[0]) for stroke in strokes for point in stroke["points"]]
    ys = [float(point[1]) for stroke in strokes for point in stroke["points"]]
    margin = pen_width_px(device_pixel_ratio)
    width = math.ceil((max(xs) - min(xs)) * device_pixel_ratio) + 2 * margin + 1
    height = math.ceil((max(ys) - min(ys)) * device_pixel_ratio) + 2 * margin + 1
    return width, height, min(xs), min(ys), margin


def render_png(strokes: list[dict[str, Any]], *, device_pixel_ratio: float, paper: tuple[int, int, int] = PAD_PAPER) -> bytes:
    """The strokes (each ``{points: [[x, y, ...], ...]}``, CSS pixels) as a PNG."""

    if not strokes:
        raise ValueError("there are no strokes to draw")
    width, height, min_x, min_y, margin = canvas(strokes, device_pixel_ratio)
    limit = Image.MAX_IMAGE_PIXELS
    if limit is not None and width * height > limit:
        raise InkTooLarge(f"the strokes span {width}x{height} pixels, more than an image may hold")
    pen = pen_width_px(device_pixel_ratio)
    image = Image.new("RGB", (width, height), paper)
    draw = ImageDraw.Draw(image)
    radius = pen / 2

    def at(point: Any) -> tuple[float, float]:
        return ((float(point[0]) - min_x) * device_pixel_ratio + margin,
                (float(point[1]) - min_y) * device_pixel_ratio + margin)

    for stroke in strokes:
        points = [at(point) for point in stroke["points"]]
        if len(points) > 1:
            draw.line(points, fill=PEN, width=pen, joint="curve")
        for x, y in (points[0], points[-1]):
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=PEN)
    out = io.BytesIO()
    image.save(out, format="PNG")
    data = out.getvalue()
    if len(data) > MAX_IMAGE_BYTES:
        raise InkTooLarge(f"the image is {len(data)} bytes, more than a request may carry")
    return data


__all__ = ["InkTooLarge", "MEDIA_TYPE", "PAD_PAPER", "PEN", "PEN_WIDTH_CSS_PX", "SOURCE_PAPER", "canvas",
           "pen_width_px", "render_png"]
