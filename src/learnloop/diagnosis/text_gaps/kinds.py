"""The two match kinds learner-text gaps register on T1's shared matcher.

Both are ASYMMETRIC (``learnloop.matching.kinds``): the query is the gap as a
model named it, embedded once with the ``retrieval-query`` prompt (stored as
``learner_gap/<field>`` so a retry reuses it), matched against a pool of
stored ``retrieval-document`` vectors of another record kind:

* ``same_prerequisite``: a named missing prerequisite against learning
  objectives (``learning_object/statement``, a declared recipe);
* ``same_belief``: a stated wrong belief against the misconception registry
  and the holding pen (``misconception/statement``, keyed ``durable:<id>`` /
  ``candidate:<id>`` exactly as the diagnoser's registry shortlist keys them).

A judge decides every pair; the score only chooses which pairs a judge sees.
"""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from typing import Any

from learnloop.diagnosis.split.embeddings import MISCONCEPTION_FIELD, MISCONCEPTION_KIND, misconception_record
from learnloop.diagnosis.split.retrieval import DOCUMENT_PREFIX, QUERY_PREFIX
from learnloop.diagnosis.text_gaps.contract import (
    JUDGE_ROUTE,
    SAME_BELIEF_TASK,
    SAME_PREREQUISITE_TASK,
    LearnerText,
)
from learnloop.matching.kinds import MatchKind, Subject
from learnloop.vault.embedding_recipes import EMBEDDING_RECIPES, learning_object_statement_text
from learnloop.vault.models import LoadedVault

GAP_RECORD_KIND = "learner_gap"
PREREQUISITE_FIELD = "prerequisite"
BELIEF_FIELD = "belief"
LO_RECIPE = EMBEDDING_RECIPES["learning_object/statement"]
QUERY_RECIPE_VERSION = 1

_PREREQUISITE_QUESTION = (
    "One item is knowledge a learner was missing, named from the learner's own words; the "
    "other is a learning objective in the learner's course (both are labelled by `role`). "
    "Do they name the same piece of knowledge, so that learning the objective would supply "
    "exactly what the learner is missing?"
)
_PREREQUISITE_GUIDANCE = (
    "Say `same` when they are the same knowledge at about the same scope, allowing different "
    "wording and notation. Say `different` when one is only related, broader, narrower in a "
    "way that would not supply the missing piece, or a different topic: a shared word or "
    "subject is never enough. Say `unsure` when the text cannot settle it."
)
_BELIEF_QUESTION = (
    "Each item states a belief about the subject. Do the two state the same belief: the same "
    "thing taken to be true?"
)
_BELIEF_GUIDANCE = (
    "Say `same` when one belief would produce the other's statements, allowing different "
    "wording and examples. Say `different` when they are different beliefs, even about the "
    "same topic or leading to the same wrong answer. Say `unsure` when the text cannot settle "
    "it."
)


def _render(subject: Subject) -> Mapping[str, Any]:
    return dict(subject.view)


SAME_PREREQUISITE = MatchKind(
    name="same prerequisite",
    task=SAME_PREREQUISITE_TASK,
    subject_kind="learning_object",
    record_kind=LO_RECIPE.record_kind,
    field=LO_RECIPE.field,
    task_prefix=DOCUMENT_PREFIX,
    route=JUDGE_ROUTE,
    purpose="learner_gap_same_prerequisite",
    prompt_version="same-prerequisite-judge-v1",
    question=_PREREQUISITE_QUESTION,
    guidance=_PREREQUISITE_GUIDANCE,
    render=_render,
    recipe=f"{LO_RECIPE.name}@v{LO_RECIPE.version}",
    query_record_kind=GAP_RECORD_KIND,
    query_field=PREREQUISITE_FIELD,
    query_task_prefix=QUERY_PREFIX,
    query_recipe=f"{GAP_RECORD_KIND}/{PREREQUISITE_FIELD}@v{QUERY_RECIPE_VERSION}",
)

SAME_BELIEF = MatchKind(
    name="same belief",
    task=SAME_BELIEF_TASK,
    subject_kind="misconception",
    record_kind=MISCONCEPTION_KIND,
    field=MISCONCEPTION_FIELD,
    task_prefix=DOCUMENT_PREFIX,
    route=JUDGE_ROUTE,
    purpose="learner_gap_same_belief",
    prompt_version="same-belief-judge-v1",
    question=_BELIEF_QUESTION,
    guidance=_BELIEF_GUIDANCE,
    render=_render,
    recipe=f"{MISCONCEPTION_KIND}/{MISCONCEPTION_FIELD}@v1",
    query_record_kind=GAP_RECORD_KIND,
    query_field=BELIEF_FIELD,
    query_task_prefix=QUERY_PREFIX,
    query_recipe=f"{GAP_RECORD_KIND}/{BELIEF_FIELD}@v{QUERY_RECIPE_VERSION}",
)


def query_hash(field: str, text: str) -> str:
    payload = json.dumps([GAP_RECORD_KIND, field, QUERY_RECIPE_VERSION, text], ensure_ascii=False,
                         separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def prerequisite_query_text(name: str, line: str | None) -> str:
    return f"{name.strip()}\n{line.strip()}" if line and line.strip() else name.strip()


def prerequisite_query(text: LearnerText, name: str, line: str | None) -> Subject:
    """The named prerequisite as the query subject (``learner_gap`` in the ledger)."""

    body = prerequisite_query_text(name, line)
    return Subject(
        kind=GAP_RECORD_KIND,
        id=text.subject_key,
        text=body,
        content_hash=query_hash(PREREQUISITE_FIELD, body),
        created_at=text.created_at,
        view={"role": "missing knowledge named from the learner's text", "name": name, "line": line or ""},
    )


def belief_query(text: LearnerText, statement: str) -> Subject:
    return Subject(
        kind=GAP_RECORD_KIND,
        id=text.subject_key,
        text=statement,
        content_hash=query_hash(BELIEF_FIELD, statement),
        created_at=text.created_at,
        view={"role": "belief stated in the learner's text", "statement": statement},
    )


def learning_object_subject(vault: LoadedVault, learning_object_id: str, *, basis: str) -> Subject | None:
    learning_object = vault.learning_objects.get(learning_object_id)
    if learning_object is None:
        return None
    concept = vault.concepts.get(learning_object.concept)
    body = learning_object_statement_text(learning_object, concept)
    return Subject(
        kind="learning_object",
        id=learning_object_id,
        text=body,
        content_hash=LO_RECIPE.content_hash(body),
        created_at=str(learning_object.created_at or ""),
        scope={"basis": basis, "subjects": tuple(learning_object.subjects), "concept": learning_object.concept},
        view={
            "role": "learning objective in the learner's course",
            "title": learning_object.title,
            "concept": getattr(concept, "title", None) or learning_object.concept,
            "statement": learning_object.summary,
        },
    )


def registry_subject(kind: str, record_id: str, statement: str, *, learning_object_id: str | None, basis: str) -> Subject | None:
    """A durable misconception (``kind='durable'``) or holding-pen candidate.

    The subject id is the registry key the ``misconception/statement`` vectors
    use (``durable:<id>`` / ``candidate:<id>``), so a vector the diagnoser's
    registry shortlist or the backfill paid for is the one ranked here.
    """

    record = misconception_record(f"{kind}:{record_id}", statement)
    if record is None:
        return None
    return Subject(
        kind="misconception",
        id=record.record_id,
        text=record.text,
        content_hash=record.content_hash,
        scope={"basis": basis, "learning_object_id": learning_object_id, "registry_kind": kind,
               "registry_id": record_id},
        view={"role": "a belief in the learner's registry", "statement": record.text},
    )


__all__ = [
    "BELIEF_FIELD",
    "GAP_RECORD_KIND",
    "LO_RECIPE",
    "PREREQUISITE_FIELD",
    "SAME_BELIEF",
    "SAME_PREREQUISITE",
    "belief_query",
    "learning_object_subject",
    "prerequisite_query",
    "prerequisite_query_text",
    "query_hash",
    "registry_subject",
]
