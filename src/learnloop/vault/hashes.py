from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel

from learnloop.vault.models import Concept, ConceptEdge, LearningObject, PracticeItem, Rubric


def _plain(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", exclude_none=True)
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_plain(item) for item in value]
    return value


def content_hash(fields: dict[str, Any]) -> str:
    payload = json.dumps(_plain(fields), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def learning_object_hash(learning_object: LearningObject) -> str:
    return content_hash(
        {
            "id": learning_object.id,
            "title": learning_object.title,
            "subjects": learning_object.subjects,
            "concept": learning_object.concept,
            "knowledge_type": learning_object.knowledge_type,
            "status": learning_object.status,
            "contradicts": learning_object.contradicts,
            "summary": learning_object.summary,
            "prerequisites": learning_object.prerequisites,
            "confusables": learning_object.confusables,
            "difficulty_prior": learning_object.difficulty_prior,
        }
    )


def practice_item_hash(practice_item: PracticeItem) -> str:
    return content_hash(
        {
            "learning_object_id": practice_item.learning_object_id,
            "practice_mode": practice_item.practice_mode,
            "attempt_types_allowed": practice_item.attempt_types_allowed,
            "evidence_facets": practice_item.evidence_facets,
            "evidence_weights": practice_item.evidence_weights,
            "prompt": practice_item.prompt,
            "expected_answer": practice_item.expected_answer,
            "difficulty": practice_item.difficulty,
            "hints": practice_item.hints,
            "hint_policy": practice_item.hint_policy,
            "grading_rubric": practice_item.grading_rubric,
        }
    )


def concept_hash(concept_id: str, concept: Concept) -> str:
    return content_hash(
        {
            "id": concept_id,
            "title": concept.title,
            "type": concept.type,
            "aliases": concept.aliases,
            "description": concept.description,
        }
    )


def concept_edge_hash(edge: ConceptEdge) -> str:
    source = edge.source
    target = edge.target
    if edge.relation_type == "confusable_with" and target < source:
        source, target = target, source
    return content_hash(
        {
            "id": edge.id,
            "relation_type": edge.relation_type,
            "source": source,
            "target": target,
            "strength": edge.strength,
            "rationale": edge.rationale,
        }
    )


def rubric_hash(rubric: Rubric) -> str:
    return content_hash(rubric.model_dump(mode="json", exclude_none=True))
