from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel

from learnloop.db.stores.source_service import reference_content_hash as _reference_hash
from learnloop.vault.models import ActivityFamily, Concept, ConceptEdge, LearningObject, PracticeItem, Rubric


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
    fields: dict[str, Any] = {
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
    # A required method changes what the item measures (its method criteria
    # are graded on use of the method), so it is item content. Hashed only
    # when present: every item without one keeps its hash.
    if practice_item.required_method is not None:
        fields["required_method"] = practice_item.required_method
    return content_hash(fields)


def reference_content_hash(practice_item: PracticeItem) -> str:
    """What an answer-key check verified (canonical sources S1, §7.3a): the
    prompt, the expected answer and the grading rubric. One definition, in the
    store that binds checks to it; separate from :func:`practice_item_hash`,
    which is unchanged."""
    return _reference_hash(practice_item)


def skeleton_content_hash(prompt: str, expected_answer: str | dict[str, Any]) -> str:
    """The item text a PF solution skeleton describes (``item_skeletons.content_hash``).

    A generated candidate and the item published from it share it, so a skeleton
    written at mint time serves the published item.
    """
    payload = json.dumps({"prompt": prompt, "expected_answer": expected_answer},
                         sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


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


def activity_family_hash(family: ActivityFamily) -> str:
    """Authored family content has its own revision hash, never the item hash."""
    return content_hash(family.model_dump(mode="json"))


def rubric_hash(rubric: Rubric) -> str:
    return content_hash(rubric.model_dump(mode="json", exclude_none=True))
