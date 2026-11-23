"""One model for "something to show" (spec §3.4): a window's content, an open spec, a
claim's target, a search result, a promoted row and a path row all carry a :data:`ContentRef`.

The models accept the desktop's camelCase as well as snake_case and refuse unknown fields, like every
RPC's params.
"""
from __future__ import annotations

from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _camel(name: str) -> str:
    head, *tail = name.split("_")
    return head + "".join(part[:1].upper() + part[1:] for part in tail)


class WireModel(BaseModel):
    """A strict wire model: camelCase or snake_case in, unknown fields refused."""

    model_config = ConfigDict(alias_generator=_camel, populate_by_name=True, extra="forbid", frozen=True)

    def wire(self) -> dict[str, Any]:
        """The snake_case form stored and hashed (absent optionals left out)."""

        return self.model_dump(mode="json", exclude_none=True)


class SpanRange(WireModel):
    from_span_id: str = Field(min_length=1)
    to_span_id: str = Field(min_length=1)


class SourceRef(WireModel):
    kind: Literal["source"]
    source_id: str = Field(min_length=1)
    extraction_id: str = Field(min_length=1)
    view: Literal["render", "pdf", "web"] = "render"
    range: SpanRange | None = None


class VideoRef(WireModel):
    kind: Literal["video"]
    source_id: str = Field(min_length=1)
    extraction_id: str = Field(min_length=1)
    t: float | None = Field(default=None, ge=0)


class PadRef(WireModel):
    kind: Literal["pad"]
    pad_id: str = Field(min_length=1)


class LessonRef(WireModel):
    kind: Literal["lesson"]
    lesson_id: str = Field(min_length=1)


class ThreadRef(WireModel):
    kind: Literal["thread"]
    root_exchange_id: str = Field(min_length=1)


class CompareRef(WireModel):
    kind: Literal["compare"]
    comparison_id: str | None = None
    query: str | None = None

    @model_validator(mode="after")
    def _one_of(self) -> CompareRef:
        if (self.comparison_id is None) == (self.query is None):
            raise ValueError("a compare reference names a comparison_id or a query, not both or neither")
        return self


class PanelRef(WireModel):
    kind: Literal["panel"]
    panel: Literal["guide", "path", "library", "notes"]
    extraction_id: str | None = None


class FigureNotebookRef(WireModel):
    kind: Literal["figure_notebook"]
    figure_id: str = Field(min_length=1)


ContentRef = Annotated[
    Union[SourceRef, VideoRef, PadRef, LessonRef, ThreadRef, CompareRef, PanelRef, FigureNotebookRef],
    Field(discriminator="kind"),
]

#: What a pad stack may hold (spec §5.2: pads, and Teacher lessons as tabs).
StackEntry = Annotated[Union[PadRef, LessonRef], Field(discriminator="kind")]


class Target(WireModel):
    """Where inside a content reference to land: a passage, a time or a block."""

    span_id: str | None = None
    t: float | None = Field(default=None, ge=0)
    block_id: str | None = None


class TargetedRef(WireModel):
    content: ContentRef
    target: Target | None = None


__all__ = [
    "CompareRef", "ContentRef", "FigureNotebookRef", "LessonRef", "PadRef", "PanelRef", "SourceRef", "SpanRange",
    "StackEntry", "Target", "TargetedRef", "ThreadRef", "VideoRef", "WireModel",
]
