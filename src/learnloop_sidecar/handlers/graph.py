from __future__ import annotations

from typing import Any

from learnloop.services.mastery import display_mastery
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import versioned
from learnloop_sidecar.registry import method


@method("get_concept_graph")
def get_concept_graph(ctx: SidecarContext, _params) -> dict[str, Any]:
    """Concept graph for the Graph screen: concepts + edges + per-concept rollups.

    Pure serialization over the loaded vault and derived state — node positions are
    a frontend concern (the screen lays the graph out by prerequisite depth).
    """

    vault, repository = ctx.require_vault()

    lo_to_concept: dict[str, str] = {lo_id: lo.concept for lo_id, lo in vault.learning_objects.items()}
    concept_to_los: dict[str, list[tuple[str, Any]]] = {}
    for lo_id, learning_object in vault.learning_objects.items():
        concept_to_los.setdefault(learning_object.concept, []).append((lo_id, learning_object))

    practice_counts: dict[str, int] = {}
    for item in vault.practice_items.values():
        concept_id = lo_to_concept.get(item.learning_object_id)
        if concept_id is not None:
            practice_counts[concept_id] = practice_counts.get(concept_id, 0) + 1

    error_counts: dict[str, int] = {}
    for event in repository.active_error_events():
        concept_id = lo_to_concept.get(event.learning_object_id)
        if concept_id is not None:
            error_counts[concept_id] = error_counts.get(concept_id, 0) + 1

    def lo_mastery(lo_id: str) -> float | None:
        state = repository.mastery_state(lo_id)
        return display_mastery(state).mastery_mean if state is not None else None

    concepts: list[dict[str, Any]] = []
    misconception_count = 0
    for concept_id, concept in sorted(vault.concepts.items()):
        if concept.type == "misconception":
            misconception_count += 1
        learning_objects = [
            {"id": lo_id, "title": learning_object.title, "mastery": lo_mastery(lo_id)}
            for lo_id, learning_object in sorted(concept_to_los.get(concept_id, []), key=lambda pair: pair[0])
        ]
        concepts.append(
            {
                "id": concept_id,
                "title": concept.title,
                "type": concept.type,
                "aliases": concept.aliases,
                "description": concept.description,
                "learning_objects": learning_objects,
                "practice_item_count": practice_counts.get(concept_id, 0),
                "open_error_event_count": error_counts.get(concept_id, 0),
            }
        )

    edges = [
        {
            "id": edge.id,
            "source": edge.source,
            "target": edge.target,
            "relation_type": edge.relation_type,
            "strength": edge.strength,
        }
        for edge in vault.edges
    ]

    return versioned(
        {
            "subjects": sorted(vault.subjects),
            "concepts": concepts,
            "edges": edges,
            "counts": {
                "concepts": len(vault.concepts),
                "edges": len(edges),
                "misconceptions": misconception_count,
            },
        }
    )
