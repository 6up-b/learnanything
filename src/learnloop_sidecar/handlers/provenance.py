from __future__ import annotations

from typing import Any

from learnloop.services.provenance import get_entity_provenance
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.registry import method


class EntityProvenanceInput(ParamsModel):
    entity_type: str
    entity_id: str


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
