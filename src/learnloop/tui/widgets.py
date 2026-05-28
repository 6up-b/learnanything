from __future__ import annotations

from textual.content import Content
from textual.widgets import Static


class TextStatic(Static):
    """A `Static` that exposes the displayed text via `.renderable`.

    Textual 8.x renamed the legacy `Static.renderable` attribute. LearnLoop
    screens and tests read back the rendered text, so this thin subclass keeps
    a stable accessor. The stored value may be a plain `str` or a `Content`;
    `str(value)` yields the plain text in either case, so substring assertions
    in the tests hold regardless.
    """

    def __init__(self, text: str | Content = "", **kwargs) -> None:
        super().__init__(text, **kwargs)
        self._text: str | Content = text

    def update(self, content: str | Content = "", *, layout: bool = True) -> None:
        self._text = content
        super().update(content, layout=layout)

    @property
    def renderable(self) -> str | Content:
        return self._text


# ─────────────────────────────────────────────────────────────────────────
# Design language — Content-based helpers driven by theme tokens.
#
# Colors come from the active `learnloop` theme (see theme.py); no literal hex
# lives here. Pills follow toad's half-block style (`pill.py`): a rounded
# half-block end on each side with a true background color.
# ─────────────────────────────────────────────────────────────────────────

# variant -> (background token, foreground token)
_PILL_TOKENS = {
    "primary":   ("$primary-muted",   "$text-primary"),
    "success":   ("$success-muted",   "$text-success"),
    "accent":    ("$accent-muted",    "$text-accent"),
    "warning":   ("$warning-muted",   "$text-warning"),
    "error":     ("$error-muted",     "$text-error"),
    "secondary": ("$secondary-muted", "$text-secondary"),
    "slate":     ("$panel",           "$text-muted"),
    "probe":     ("$probe 25%",       "$probe"),
}

# practice_mode -> pill variant. Mirrors modePillColor() in the prototype.
_MODE_PILL_VARIANT = {
    "short_answer": "secondary",
    "explanation": "accent",
    "proof": "primary",
    "worked_problem": "success",
    "transfer": "probe",
    "free_recall": "slate",
}


def mode_pill_color(mode: str) -> str:
    """Map a practice mode to a pill variant name."""
    return _MODE_PILL_VARIANT.get(mode, "secondary")


def pill(text: str, variant: str = "secondary") -> Content:
    """A half-block pill (toad `pill.py` style) rendered via the Content API."""
    bg, fg = _PILL_TOKENS.get(variant, _PILL_TOKENS["secondary"])
    end_style = f"{bg} on transparent r"
    return Content.assemble(
        ("▌", end_style),
        Content(f" {text} ").stylize(f"{fg} on {bg}"),
        ("▐", end_style),
    )


def block_bar(value: float, width: int = 8, token: str = "$primary") -> Content:
    """Unicode block bar (▓ filled / ░ empty); fill color is a theme token."""
    value = max(0.0, min(1.0, value))
    filled = round(value * width)
    return Content.assemble(
        ("▓" * filled, token),
        ("░" * (width - filled), "$text-disabled"),
    )


def mastery_token(value: float) -> str:
    """Theme token for a mastery/quality value in [0, 1]."""
    return "$success" if value > 0.6 else "$warning" if value > 0.35 else "$error"


class KeyBar(Static):
    """Footer hot-key bar (prototype-faithful row), rendered via Content.

    Each `(key, label)` pair renders the key bold in `$footer-key-foreground`
    and the label in `$text-muted`. Layout/background live in `learnloop.tcss`.
    """

    def __init__(self, keys: list[tuple[str, str]], **kwargs) -> None:
        self._keys = keys
        super().__init__(self._render(), **kwargs)

    def set_keys(self, keys: list[tuple[str, str]]) -> None:
        self._keys = keys
        self.update(self._render())

    def _render(self) -> Content:
        items: list = []
        for i, (key, label) in enumerate(self._keys):
            if i:
                items.append("   ")
            items.append((key, "$footer-key-foreground bold"))
            items.append(" ")
            items.append((label, "$text-muted"))
        return Content.assemble(*items)
