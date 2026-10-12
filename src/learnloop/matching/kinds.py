"""What a "same or different?" question is about (Slice 2 R4, §4).

A :class:`MatchKind` parameterizes the one shortlist + judge + ledger step.
Slice 2 T1 registers the first kind (hypothesis recurrence, task
``same_cause``); later stages add kinds (missing prerequisites, tutor-question
misconception sightings) without a new mechanism. Nothing here knows what a
misconception is: a kind supplies the task name, the embedding identity of its
subjects, the AI route and prompt version, the question and how a subject is
shown to the judge.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

VERDICTS = ("same", "different", "unsure")


@dataclass(frozen=True)
class Subject:
    """One thing that may be "the same" as another.

    ``kind`` and ``id`` are its ``judgment_ledger`` subject (``left_kind`` /
    ``left_id``); ``content_hash`` is its ``embedding_vectors`` identity for
    the kind's ``record_kind``/``field``; ``text`` is the LLM-written or
    canonical text that was embedded. ``scope`` holds the structured
    attributes a kind's blocking filter reads (never sent to the judge unless
    the kind's renderer shows them); ``view`` is what the judge reads.
    """

    kind: str
    id: str
    text: str
    content_hash: str
    created_at: str = ""
    scope: Mapping[str, Any] = field(default_factory=dict)
    view: Mapping[str, Any] = field(default_factory=dict)


def _default_render(subject: Subject) -> Mapping[str, Any]:
    return dict(subject.view) if subject.view else {"text": subject.text}


@dataclass(frozen=True)
class MatchKind:
    #: Short name, e.g. ``hypothesis_recurrence``.
    name: str
    #: ``judgment_ledger.task`` its verdicts are written under.
    task: str
    #: ``judgment_ledger`` subject kind (``left_kind``/``right_kind``).
    subject_kind: str
    #: Embedding identity of its subjects' vectors.
    record_kind: str
    field: str
    task_prefix: str
    #: ``ai.routing`` task and the model-call purpose of one judgment.
    route: str
    purpose: str
    prompt_version: str
    #: What the judge decides, and the rules for the three verdicts.
    question: str
    guidance: str
    #: How a subject is shown to the judge (defaults to its ``view``).
    render: Callable[[Subject], Mapping[str, Any]] = _default_render
    #: The declared text recipe its subjects' vectors embed (e.g.
    #: ``hypothesis/statement@v1``). A benchmark-set blocking cutoff names the
    #: recipe, width and task prefix it was measured on and applies only to
    #: vectors of exactly that identity.
    recipe: str = ""


__all__ = ["MatchKind", "Subject", "VERDICTS"]
