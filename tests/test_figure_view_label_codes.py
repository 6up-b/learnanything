"""The view's label code and ``shown`` (K10.14): the desktop draws its badge from the code and reads ``shown``, so
the code set is closed, every presented row maps to one, and the desktop's type names exactly that set."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from learnloop.figures import view as FV

DTO = Path(__file__).resolve().parents[1] / "apps" / "learnloop-tauri" / "src" / "api" / "dto.ts"

ROWS = {
    "illustrative": {"verification": "illustrative", "tier": "grammar"},
    "not_from_books": {"verification": "illustrative", "tier": "grammar", "grounding": "none"},
    "sketch": {"verification": "illustrative", "tier": "sketch", "verification_report": {"checks": [{}]}},
    "sketch_unchecked": {"verification": "illustrative", "tier": "sketch"},
    "sketch_not_from_books": {"verification": "illustrative", "tier": "sketch", "grounding": "none"},
    "manim": {"verification": "illustrative", "tier": "manim", "verification_report": {"checks": [{}]}},
    "manim_unchecked": {"verification": "illustrative", "tier": "manim"},
    "manim_not_from_books": {"verification": "illustrative", "tier": "manim", "grounding": "none"},
    "rich_off": {"verification": "unsupported", "tier": "manim", "verification_report": {"rich_off": True}},
    "engine_changed": {"verification": "failed", "tier": "sketch", "verification_report": {"engine_changed": True}},
    "unsupported": {"verification": "unsupported", "tier": "grammar", "unsupported_kind": "a 3-D surface"},
    "failed": {"verification": "failed", "tier": "grammar", "verification_report": {"reason": "it failed"}},
}


@pytest.mark.parametrize("code", sorted(ROWS))
def test_each_presented_row_has_one_code_and_the_label_follows_it(code):
    row = ROWS[code]
    assert FV._label_code(row) == code
    label = FV._label(row)
    assert label and (code not in ("unsupported", "failed") or row.get("unsupported_kind", "it failed") in label)


def test_the_codes_are_closed_and_the_desktop_names_exactly_them():
    assert set(ROWS) == set(FV.LABEL_CODES)
    union = re.search(r"export type FigureLabelCode =([^;]+);", DTO.read_text(encoding="utf-8"))
    assert union is not None
    assert set(re.findall(r'"([a-z_]+)"', union.group(1))) == set(FV.LABEL_CODES)
