from __future__ import annotations

from typing import Any

from learnloop.content.sources.provenance import get_entity_provenance
from learnloop.reader.span_view import SpanViewError, build_span_view
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method


class EntityProvenanceInput(ParamsModel):
    entity_type: str
    entity_id: str


class SpanViewInput(ParamsModel):
    extraction_id: str
    span_id: str
    context: str = "provenance"
    entity_type: str | None = None
    entity_id: str | None = None


@method("get_span_view", SpanViewInput)
def get_span_view_handler(ctx: SidecarContext, params: SpanViewInput) -> dict[str, Any]:
    """Open-in-source viewer data (§9.2): span text + page/bbox/polygon geometry,
    section path, neighboring spans, and same-page spans. Records a
    ``source_exposure`` event on EVERY view (§14). PDF pages have no persisted
    raster, so the viewer renders the honest text fallback (viewer_mode
    ``pdf_text``); HTML/text uses scroll-to-anchor (``text_anchor``)."""

    _vault, repository = ctx.require_vault()
    try:
        view = build_span_view(
            repository,
            params.extraction_id,
            params.span_id,
            context=params.context,
            entity_type=params.entity_type,
            entity_id=params.entity_id,
            record=True,
        )
    except SpanViewError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    return versioned({"spanView": view})


@method("get_entity_provenance", EntityProvenanceInput)
def get_entity_provenance_handler(
    ctx: SidecarContext, params: EntityProvenanceInput
) -> dict[str, Any]:
    """Entity provenance view (§9.2): supporting sources with spans, semantic vs
    assessment-alignment authority (separated), staleness, conflicts, notation, and
    the synthesis run that introduced the entity."""

    _vault, repository = ctx.require_vault()
    payload = get_entity_provenance(repository, params.entity_type, params.entity_id)
    return versioned(payload)
