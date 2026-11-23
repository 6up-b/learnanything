"""Reader workbench v2 RPC: ``passage.union_range`` (spec §3.4, §7.6), everything tied to each
passage of one visible range. Batched per range, never per span on hover; goal-independent.

Desktop only (pinned in tests/test_mobile_allowlist.py). Read only; no model call.
"""
from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from learnloop.passage_union.union import UnionError, union_range
from learnloop.source_retrieval import note_links as NL
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

#: Every RPC this module registers (pinned desktop-only).
PASSAGE_UNION_RPCS: tuple[str, ...] = ("passage.union_range",)


class UnionRangeInput(ParamsModel):
    extraction_id: str = Field(min_length=1)
    from_span_id: str | None = None
    to_span_id: str | None = None
    t0: float | None = Field(default=None, ge=0)
    t1: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _one_range(self) -> UnionRangeInput:
        spans = self.from_span_id is not None and self.to_span_id is not None
        times = self.t0 is not None and self.t1 is not None
        partial = (self.from_span_id is None) != (self.to_span_id is None) or (self.t0 is None) != (self.t1 is None)
        if spans == times or partial:
            raise ValueError("a range is two passages (from_span_id, to_span_id) or two times (t0, t1)")
        return self


@method("passage.union_range", UnionRangeInput)
def passage_union_range_handler(ctx: SidecarContext, params: UnionRangeInput) -> dict[str, Any]:
    """``{extraction_id, spans: [{span_id, …everything tied to it}], sections}``."""

    vault, repository = ctx.require_vault()
    # The notes linked beside each passage (curriculum C2's marks, while notes.enabled): the sidecar reads
    # the notes' code, so the union read below it never does.
    notes_by_span = ({mark["span_id"]: mark["notes"] for mark in NL.marks(vault, repository, params.extraction_id)}
                     if NL.enabled(vault) and repository.get_extraction_run(params.extraction_id) is not None else {})
    try:
        return versioned(union_range(vault, repository, extraction_id=params.extraction_id,
                                     from_span_id=params.from_span_id, to_span_id=params.to_span_id, t0=params.t0,
                                     t1=params.t1, notes_by_span=notes_by_span))
    except UnionError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
