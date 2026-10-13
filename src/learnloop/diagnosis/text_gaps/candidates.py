"""Which vault entries a named gap is judged against (grounded, then shortlisted).

**Prerequisites.** Structural candidates first: the asking item's LO, the LOs
its declared prerequisites name (``LearningObject.prerequisites`` and
``prerequisite`` edges), and the prerequisites this pipeline created today
(so a second question about the same missing topic matches the first one's
creation instead of creating twice). Then a vault-wide shortlist over stored
``learning_object/statement`` vectors (top-k, plain cosine between the query
and document prompt spaces, T1's ``shortlist_pairs``; no cutoff unless one is
benchmark-set, and none is). A vault with no LO vectors yet gets a lexical
shortlist of the same size instead, so a missing-looking prerequisite is still
checked against similarly named LOs before anything is created; it only
nominates, the judge decides. Every candidate is restricted, BEFORE ranking,
to LOs in the asking text's subject: a target is never cross-subject (F11).

**Beliefs.** The registry and the holding pen as the diagnoser sees them:
durable misconceptions on the anchor LO (any status) and active ones on its
concept and ``confusable_with`` neighbours, holding-pen candidates on the
anchor LO, plus the ``misconception/statement`` kNN over the vault registry
in the same subject when vectors exist.
"""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import closing
from dataclasses import dataclass, field
import re
from typing import Any

import numpy as np

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.diagnosis.text_gaps.contract import LearnerText
from learnloop.diagnosis.text_gaps.kinds import (
    SAME_BELIEF,
    SAME_PREREQUISITE,
    learning_object_subject,
    registry_subject,
)
from learnloop.matching.kinds import Subject
from learnloop.matching.shortlist import CandidatePair, shortlist_pairs, stored_vectors
from learnloop.vault.models import LoadedVault

_WORD = re.compile(r"[a-z0-9]+")
_STOP = frozenset(
    "a an and are as at be by for from how in into is it of on or that the this to what when which why with".split()
)


@dataclass
class Candidates:
    subjects: list[Subject] = field(default_factory=list)
    #: How the shortlist part was ranked: knn | lexical | none.
    shortlist_basis: str = "none"
    shortlist_model: str | None = None
    excluded_cross_subject: int = 0

    def summary(self) -> dict[str, Any]:
        bases: dict[str, int] = {}
        for subject in self.subjects:
            basis = str(subject.scope.get("basis"))
            bases[basis] = bases.get(basis, 0) + 1
        return {"candidates": len(self.subjects), "by_basis": bases, "shortlist_basis": self.shortlist_basis,
                "shortlist_model": self.shortlist_model, "excluded_cross_subject": self.excluded_cross_subject}

    def pairs(self, query: Subject) -> list[CandidatePair]:
        return [
            CandidatePair(left=query, right=subject, score=0.0, rank=index + 1,
                          model_id=self.shortlist_model or "structural", basis=str(subject.scope.get("basis")))
            for index, subject in enumerate(self.subjects)
        ]


def _in_subject(vault: LoadedVault, learning_object_id: str, subject_id: str | None) -> bool:
    learning_object = vault.learning_objects.get(learning_object_id)
    if learning_object is None or learning_object.status != "active":
        return False
    return subject_id is None or subject_id in learning_object.subjects


def declared_prerequisites(vault: LoadedVault, anchors: Sequence[str]) -> list[str]:
    from learnloop.placement.state import prerequisite_learning_objects

    out: set[str] = set()
    for anchor in anchors:
        out |= prerequisite_learning_objects(vault, anchor)
    return sorted(out - set(anchors))


def created_today(repository: Repository, *, day_start: str) -> list[str]:
    """LOs this pipeline created since ``day_start`` and the learner kept."""

    from learnloop.db.stores.learner_gaps import gaps, reversals

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = [row for row in gaps(connection, since=day_start) if row.get("created_learning_object_id")]
        undone = {
            row["gap_id"] for row in reversals(connection, [row["id"] for row in rows])
            if row["reversal"] == "undo_creation"
        }
    return [str(row["created_learning_object_id"]) for row in rows if row["id"] not in undone]


def _tokens(text: str) -> set[str]:
    return {token for token in _WORD.findall(text.lower()) if token not in _STOP and len(token) > 2}


def lexical_rank(query_text: str, pool: Sequence[Subject], top_k: int) -> list[Subject]:
    """Token-overlap ranking (a fallback nominator only; the judge decides)."""

    query = _tokens(query_text)
    if not query:
        return []
    scored = []
    for subject in pool:
        overlap = len(query & _tokens(subject.text))
        if overlap:
            scored.append((-overlap, subject.id, subject))
    scored.sort()
    return [subject for _score, _id, subject in scored[:top_k]]


def prerequisite_candidates(
    vault: LoadedVault,
    repository: Repository,
    text: LearnerText,
    *,
    query: Subject,
    query_vector: np.ndarray | None,
    model_id: str | None,
    top_k: int,
    limit: int,
    day_start: str,
) -> Candidates:
    subject_id = text.subject_id
    result = Candidates()
    seen: set[str] = set()

    def add(learning_object_id: str, basis: str) -> None:
        if learning_object_id in seen:
            return
        if not _in_subject(vault, learning_object_id, subject_id):
            if learning_object_id in vault.learning_objects:
                result.excluded_cross_subject += 1
            return
        built = learning_object_subject(vault, learning_object_id, basis=basis)
        if built is not None:
            seen.add(learning_object_id)
            result.subjects.append(built)

    anchors = list(text.anchor_learning_object_ids)
    for learning_object_id in anchors:
        add(learning_object_id, "item")
    for learning_object_id in created_today(repository, day_start=day_start):
        add(learning_object_id, "created_today")
    first = list(result.subjects)
    result.subjects = []
    for learning_object_id in declared_prerequisites(vault, anchors):
        add(learning_object_id, "declared")
    declared = list(result.subjects)
    result.subjects = []
    pool = [
        built for learning_object_id in sorted(vault.learning_objects)
        if learning_object_id not in seen and _in_subject(vault, learning_object_id, subject_id)
        and (built := learning_object_subject(vault, learning_object_id, basis="shortlist")) is not None
    ]
    shortlisted: list[Subject] = []
    if (pool or declared) and query_vector is not None and model_id:
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            if stored_vectors(connection, SAME_PREREQUISITE, [*pool, *declared], model_id=model_id):
                if pool:
                    ranked = shortlist_pairs(
                        connection, SAME_PREREQUISITE, queries=[query], pool=pool, model_id=model_id, top_k=top_k,
                        cutoff=None, compatible=lambda _q, _c: True, query_vectors={query.id: query_vector},
                    )
                    shortlisted = [pair.right for pair in ranked.pairs]
                if len(declared) > 1:
                    # Declared prerequisites in the same order (nearest first),
                    # so a long declared list gives up its farthest ones.
                    ordered = shortlist_pairs(
                        connection, SAME_PREREQUISITE, queries=[query], pool=declared, model_id=model_id,
                        top_k=len(declared), cutoff=None, compatible=lambda _q, _c: True,
                        query_vectors={query.id: query_vector},
                    )
                    ranked_ids = [pair.right.id for pair in ordered.pairs]
                    declared.sort(key=lambda subject: ranked_ids.index(subject.id) if subject.id in ranked_ids else len(ranked_ids))
                result.shortlist_basis, result.shortlist_model = "knn", model_id
    if result.shortlist_basis == "none" and pool:
        shortlisted = lexical_rank(query.text, pool, top_k)
        result.shortlist_basis = "lexical"
    shortlisted = [subject for subject in shortlisted if subject.id not in seen]
    # The item's LO and today's creations first; then the declared
    # prerequisites and the vault-wide shortlist take turns, so neither crowds
    # the other out of the judge's budget.
    merged: list[Subject] = []
    for index in range(max(len(declared), len(shortlisted))):
        merged.extend(group[index] for group in (declared, shortlisted) if index < len(group))
    result.subjects = [*first, *merged][:limit]
    return result


def belief_candidates(
    vault: LoadedVault,
    repository: Repository,
    text: LearnerText,
    *,
    query: Subject,
    query_vector: np.ndarray | None,
    model_id: str | None,
    top_k: int,
    limit: int,
) -> Candidates:
    from learnloop.diagnosis.misconceptions import _candidate_misconceptions

    result = Candidates()
    anchor = text.anchor
    if anchor is None:
        return result
    seen: set[str] = set()

    def add(subject: Subject | None) -> None:
        if subject is not None and subject.id not in seen:
            seen.add(subject.id)
            result.subjects.append(subject)

    for row in _candidate_misconceptions(vault, repository, anchor):
        add(registry_subject("durable", row.id, row.statement, learning_object_id=row.learning_object_id,
                             basis="registry"))
    for row in repository.misconception_candidates_for_learning_object(anchor):
        add(registry_subject("candidate", str(row["id"]), str(row.get("statement") or ""),
                             learning_object_id=anchor, basis="holding_pen"))
    if query_vector is not None and model_id:
        pool = _registry_pool(vault, repository, subject_id=text.subject_id, exclude=seen)
        if pool:
            with closing(connect(repository.sqlite_path, read_only=True)) as connection:
                ranked = shortlist_pairs(
                    connection, SAME_BELIEF, queries=[query], pool=pool, model_id=model_id, top_k=top_k,
                    cutoff=None, compatible=lambda _q, _c: True, query_vectors={query.id: query_vector},
                )
            for pair in ranked.pairs:
                add(pair.right)
            result.shortlist_basis, result.shortlist_model = "knn", model_id
    result.subjects = result.subjects[:limit]
    return result


def _registry_pool(vault: LoadedVault, repository: Repository, *, subject_id: str | None, exclude: set[str]) -> list[Subject]:
    """Every registry entry in the subject (durable beliefs and legacy holding-pen rows)."""

    pool: list[Subject] = []
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        durable = connection.execute("SELECT id, statement, learning_object_id FROM misconceptions").fetchall()
        candidates = connection.execute(
            "SELECT id, statement, learning_object_id FROM misconception_candidates WHERE status = 'candidate'"
        ).fetchall()
    for kind, rows in (("durable", durable), ("candidate", candidates)):
        for record_id, statement, learning_object_id in rows:
            if learning_object_id and not _in_subject(vault, str(learning_object_id), subject_id):
                continue
            subject = registry_subject(kind, str(record_id), str(statement or ""),
                                       learning_object_id=str(learning_object_id or "") or None, basis="shortlist")
            if subject is not None and subject.id not in exclude:
                pool.append(subject)
    return pool


__all__ = [
    "Candidates",
    "belief_candidates",
    "created_today",
    "declared_prerequisites",
    "lexical_rank",
    "prerequisite_candidates",
]
