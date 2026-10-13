"""Tool requests as structured output (spec_source_practice_and_probes_v1 §10.2; S4).

No provider path here calls tools natively, so a model asks for a source tool
by writing a request into its structured output. These are plain wire models
with no behaviour: the tutor (and, later, the router) import them without
importing the service. The executing side is always code under the caller's
server-derived context; a model never sees another model's raw request and no
loop runs inside a provider, so each request is one bounded operation.

Every field is required, as strict schemas need; an empty string or list means
"none". The policy is never a field: it comes from the caller (SC2).
"""
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from learnloop.ai.schemas import WireModel

#: The tools a model may request in a tutor answer.
TUTOR_TOOLS = ("find_practice", "find_sources", "compare_sources")


class FindPracticeRequest(WireModel):
    tool: Literal["find_practice"]
    query: str = Field(max_length=2000, description="What to practise, in the learner's terms.")
    intent: Literal["practice", "discriminate", "retention", "remediate"]
    facet_ids: list[str] = Field(description="Facet ids from the context's candidate facets; [] for none.")
    learning_object_ids: list[str] = Field(description="Learning object ids; [] for none.")
    reason: str = Field(max_length=300, description="One line shown to the learner, never the answer.")


class FindSourcesRequest(WireModel):
    tool: Literal["find_sources"]
    query: str = Field(max_length=2000)
    intent: Literal["explain", "remediate", "alternative", "worked_example"]
    facet_ids: list[str]
    reason: str = Field(max_length=300)


class CompareSourcesRequest(WireModel):
    tool: Literal["compare_sources"]
    query: str = Field(max_length=2000)
    facet_ids: list[str]
    reason: str = Field(max_length=300)


ToolRequest = Annotated[FindPracticeRequest | FindSourcesRequest | CompareSourcesRequest,
                        Field(discriminator="tool")]


__all__ = ["CompareSourcesRequest", "FindPracticeRequest", "FindSourcesRequest", "TUTOR_TOOLS", "ToolRequest"]
