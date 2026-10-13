"""The first match kind: hypothesis recurrence (task ``same_cause``, Slice 2 §3).

Subjects are concrete causal-hypothesis episodes (the current head of each
episode, keyed by ``episode_key`` like their ``hypothesis/statement``
vectors). The judge reads the statement, its mechanism slug, where it was
seen (learning object, facet) and the first-divergence quote the grader
anchored, and decides whether two of them name the same underlying cause.

Scope (Slice 1 §9.5): a candidate must come from an EARLIER attempt and share
the query's target facet, or, when either has no facet, its learning object.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from learnloop.db.repositories import Repository
from learnloop.diagnosis.split.embeddings import (
    HYPOTHESIS_FIELD,
    HYPOTHESIS_KIND,
    HYPOTHESIS_VERSION,
    TASK_PREFIX,
    hypothesis_records,
)
from learnloop.matching.kinds import MatchKind, Subject
from learnloop.vault.models import LoadedVault

SAME_CAUSE_TASK = "same_cause"
SAME_CAUSE_PROMPT_VERSION = "same-cause-judge-v1"
SAME_CAUSE_ROUTE = "same_cause_judge"
SAME_CAUSE_PURPOSE = "same_cause_judgment"
#: The declared text recipe of hypothesis vectors (statement + mechanism slug).
HYPOTHESIS_RECIPE = f"{HYPOTHESIS_KIND}/{HYPOTHESIS_FIELD}@v{HYPOTHESIS_VERSION}"

_QUESTION = (
    "Each item is a hypothesis a diagnoser wrote about why the SAME learner got an "
    "answer wrong, possibly on different problems and days. Do the two name the same "
    "underlying cause: the same wrong belief, the same missing or misapplied step, or "
    "the same mechanism?"
)
_GUIDANCE = (
    "Say `same` when one cause would produce both errors, allowing different wording, "
    "notation and problems. Say `different` when they name different beliefs or "
    "mechanisms, even if both errors reached the same wrong answer, concern the same "
    "topic or were made on the same item: a shared answer, topic or item is never "
    "enough for `same`. Say `unsure` when the statements cannot settle it."
)


def _render(subject: Subject) -> Mapping[str, Any]:
    view = dict(subject.view)
    return {key: view[key] for key in ("statement", "mechanism", "learning_object", "facet", "first_divergence_quote") if view.get(key)}


SAME_CAUSE = MatchKind(
    name="same cause",
    task=SAME_CAUSE_TASK,
    subject_kind="hypothesis",
    record_kind=HYPOTHESIS_KIND,
    field=HYPOTHESIS_FIELD,
    task_prefix=TASK_PREFIX,
    route=SAME_CAUSE_ROUTE,
    purpose=SAME_CAUSE_PURPOSE,
    prompt_version=SAME_CAUSE_PROMPT_VERSION,
    question=_QUESTION,
    guidance=_GUIDANCE,
    render=_render,
    recipe=HYPOTHESIS_RECIPE,
)


@dataclass(frozen=True)
class HypothesisScope:
    attempt_id: str
    attempt_order: tuple[str, str]
    learning_object_id: str
    facet: str | None
    statement_normalized: str
    cause_scope: str


def scope_of(subject: Subject) -> HypothesisScope:
    return subject.scope["hypothesis"]  # type: ignore[return-value]


def _facet(target_ref: Any) -> str | None:
    if isinstance(target_ref, Mapping) and target_ref.get("kind") == "facet_capability" and target_ref.get("facet_id"):
        return str(target_ref["facet_id"])
    return None


def hypothesis_subjects(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_ids: Iterable[str] | None = None,
) -> list[Subject]:
    """Every concrete hypothesis head as a subject (text and hash = its vector's)."""

    wanted = set(attempt_ids) if attempt_ids is not None else None
    records = {record.record_id: record for record in hypothesis_records(repository, attempt_ids=wanted)}
    if not records:
        return []
    # Two bulk reads (episode heads, attempt times), not one per hypothesis:
    # the live step builds the whole population on every diagnose job.
    heads = {
        str(row["episode_key"]): row
        for row in repository.all_causal_hypotheses(latest_only=True)
        if str(row["episode_key"]) in records and row.get("status") != "open_set"
    }
    with repository.connection() as connection:
        attempt_times = {
            str(row[0]): str(row[1] or "")
            for row in connection.execute("SELECT id, created_at FROM practice_attempts")
        }
    subjects: list[Subject] = []
    for episode_key, record in sorted(records.items()):
        head = heads.get(episode_key)
        if head is None:
            continue
        attempt_id = str(head.get("attempt_id") or "")
        created = attempt_times.get(attempt_id) or str(head.get("created_at") or "")
        learning_object_id = str(head.get("learning_object_id") or "")
        learning_object = vault.learning_objects.get(learning_object_id)
        facet = _facet(head.get("target_ref"))
        facet_record = vault.evidence_facets.get(vault.canonical_facet_id(facet)) if facet else None
        evidence = head.get("evidence") if isinstance(head.get("evidence"), Mapping) else {}
        divergence = evidence.get("first_divergence") if isinstance(evidence, Mapping) else None
        projection = evidence.get("mechanism_projection") if isinstance(evidence, Mapping) else None
        subjects.append(
            Subject(
                kind="hypothesis",
                id=episode_key,
                text=record.text,
                content_hash=record.content_hash,
                created_at=created,
                scope={
                    "hypothesis": HypothesisScope(
                        attempt_id=attempt_id,
                        attempt_order=(created, attempt_id),
                        learning_object_id=learning_object_id,
                        facet=facet,
                        statement_normalized=str(head.get("statement_normalized") or ""),
                        cause_scope=str(head.get("cause_scope") or "unknown"),
                    )
                },
                view={
                    "statement": str(head.get("statement") or ""),
                    "mechanism": head.get("operation")
                    or (projection.get("mechanism") if isinstance(projection, Mapping) else None),
                    "learning_object": getattr(learning_object, "title", None) or learning_object_id,
                    "facet": getattr(facet_record, "title", None) or getattr(facet_record, "claim", None) or facet,
                    "first_divergence_quote": divergence.get("quote") if isinstance(divergence, Mapping) else None,
                },
            )
        )
    return subjects


def compatible(query: Subject, candidate: Subject) -> bool:
    """§9.5 blocking filter: earlier attempt, same facet (else same LO)."""

    left, right = scope_of(query), scope_of(candidate)
    if left.attempt_id == right.attempt_id or right.attempt_order >= left.attempt_order:
        return False
    if left.facet and right.facet:
        return left.facet == right.facet
    return left.learning_object_id == right.learning_object_id


__all__ = [
    "HYPOTHESIS_RECIPE",
    "HypothesisScope",
    "SAME_CAUSE",
    "SAME_CAUSE_PROMPT_VERSION",
    "SAME_CAUSE_PURPOSE",
    "SAME_CAUSE_ROUTE",
    "SAME_CAUSE_TASK",
    "compatible",
    "hypothesis_subjects",
    "scope_of",
]
