"""Strokes to an image on the server (spec §10.10): deterministic, the spec's pen on the paper the ink was drawn on, at
the strokes' own device pixel ratio, cropped to the strokes with one pen width of margin; bounded by Pillow's own
canvas limit and the transport's image limit. Synthetic strokes only."""

from __future__ import annotations

import hashlib
import io

import pytest
from PIL import Image

from learnloop.ai.transport import MAX_IMAGE_BYTES
from learnloop.pads import ink_render
from learnloop.pads.ink import InkStroke
from tests.ink_helpers import STROKES, stroke


def _validated(strokes):
    return [{"stroke_id": s.stroke_id, "points": [list(p) for p in s.points]}
            for s in (InkStroke.model_validate(value) for value in strokes)]


def _image(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data)).convert("RGB")


def test_the_same_strokes_give_the_same_bytes():
    first = ink_render.render_png(_validated(STROKES), device_pixel_ratio=1.0)
    assert first == ink_render.render_png(_validated(STROKES), device_pixel_ratio=1.0)
    assert first[:8] == b"\x89PNG\r\n\x1a\n"
    # The bytes of this fixed input under the locked Pillow: a change here moves every reading's prompt (the image's
    # digest is in it), so it is seen, never silent.
    assert hashlib.sha256(first).hexdigest() == ink_render_digest()


def ink_render_digest() -> str:
    return "d4cd243e53788dc5efe807d93e8f767ecfe28413479f86a437540a8cd0c42afe"


def test_the_canvas_is_the_strokes_box_plus_one_pen_width_each_side():
    strokes = _validated(STROKES)  # x 10..80, y 8..40
    width, height, min_x, min_y, margin = ink_render.canvas(strokes, 1.0)
    assert (min_x, min_y, margin) == (10.0, 8.0, 2)  # 2.2 px rounds to 2 at one device pixel per CSS pixel
    assert (width, height) == (70 + 4 + 1, 32 + 4 + 1)
    image = _image(ink_render.render_png(strokes, device_pixel_ratio=1.0))
    assert image.size == (width, height)
    # At twice the resolution, twice the box and a pen of 4 px (2.2 x 2 rounds to 4).
    assert ink_render.canvas(strokes, 2.0)[0:2] == (140 + 8 + 1, 64 + 8 + 1)


def test_the_pen_is_the_specs_on_the_paper_it_was_drawn_on():
    strokes = _validated(STROKES)
    image = _image(ink_render.render_png(strokes, device_pixel_ratio=1.0))
    # The bar from (30, 8) to (70, 8): its middle is inked; a corner is paper.
    assert image.getpixel((50 - 10 + 2, 8 - 8 + 2)) == ink_render.PEN
    assert image.getpixel((0, image.size[1] - 1)) == ink_render.PAD_PAPER
    # The one-point stroke at (80, 40) is a dot.
    assert image.getpixel((80 - 10 + 2, 40 - 8 + 2)) == ink_render.PEN
    margin_note = _image(ink_render.render_png(strokes, device_pixel_ratio=1.0, paper=ink_render.SOURCE_PAPER))
    assert margin_note.getpixel((0, 0)) == ink_render.SOURCE_PAPER
    assert ink_render.PEN == (0x2B, 0x4F, 0xA8) and ink_render.PEN_WIDTH_CSS_PX == 2.2  # spec §4.2


def test_nothing_is_drawn_past_the_canvas_limit_or_sent_past_the_image_limit(monkeypatch):
    far = _validated([stroke("a", (0, 0)), stroke("b", (20_000, 20_000))])
    with pytest.raises(ink_render.InkTooLarge):
        ink_render.render_png(far, device_pixel_ratio=1.0)  # 400 million pixels, past Pillow's bomb limit
    monkeypatch.setattr(ink_render, "MAX_IMAGE_BYTES", 10)
    with pytest.raises(ink_render.InkTooLarge):
        ink_render.render_png(_validated(STROKES), device_pixel_ratio=1.0)
    assert MAX_IMAGE_BYTES > 10
    with pytest.raises(ValueError):
        ink_render.render_png([], device_pixel_ratio=1.0)
