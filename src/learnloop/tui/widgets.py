from __future__ import annotations

from textual.widgets import Static


class TextStatic(Static):
    """A `Static` that exposes the displayed text via `.renderable`.

    Textual 8.x renamed the legacy `Static.renderable` attribute. LearnLoop
    screens and tests read back the rendered text, so this thin subclass keeps
    a stable accessor regardless of the installed Textual version.
    """

    def __init__(self, text: str = "", **kwargs) -> None:
        super().__init__(text, **kwargs)
        self._text = text

    def update(self, content: str = "", *, layout: bool = True) -> None:
        self._text = content
        super().update(content, layout=layout)

    @property
    def renderable(self) -> str:
        return self._text
