"""Front and back matter by heading: contents, preface, index, references...

One pattern for every place that skips them: the automatic build's reading-order
scope (UX Phase 1, §6.4) and the daily plan's reading step (usability round 1,
U4: a new book's first reading step was "Table of Contents").
"""

from __future__ import annotations

import re

FRONT_MATTER = re.compile(
    r"^\s*(?:(?:table of )?contents|preface|foreword|acknowledge?ments?|copyright|dedication|"
    r"about the authors?|index|bibliography|references|title page|half[- ]title|"
    r"list of (?:figures|tables|symbols)|notation|front matter|cover)\s*$",
    re.IGNORECASE,
)


def is_front_matter_label(label: str | None) -> bool:
    """Whether a section heading names front or back matter. A Markdown heading
    slug (``table-of-contents``) reads as its words."""

    text = str(label or "")
    if " " not in text and "-" in text and text == text.lower():
        text = text.replace("-", " ")
    return bool(FRONT_MATTER.match(text))


__all__ = ["FRONT_MATTER", "is_front_matter_label"]
