"""The contracts a job handler and the code it calls share with the ingest runner.

A handler raises :class:`IngestRunnerError` for a typed failure, :class:`JobCancelled` when cancelled and
:class:`WaitingForInput` to pause for the learner; it queues follow-up work as :class:`JobSpec` rows and reads a
fetch as :class:`FetchedBytes`. They live in this leaf, which imports nothing of LearnLoop, so a feature's job
module can use them without importing the runner, which loads those modules' defaults and handlers.
:mod:`learnloop.content.pipeline.runner` re-exports every name here: the classes are the same objects through
either path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


class IngestRunnerError(ValueError):
    """A typed, user-actionable job failure persisted for the Activity UI."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "invalid_job",
        details: Mapping[str, Any] | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.details = dict(details or {})
        self.retryable = retryable


class JobCancelled(Exception):
    """Raised from ``report()`` when a cancellation was requested mid-stage."""


class WaitingForInput(Exception):
    """A handler pauses the job pending user input (unit choice, consent, budget).

    Carries the actionable payload the Batch-progress UI renders as a card. The
    job releases its lease so the rest of the queue keeps draining (§6.2)."""

    def __init__(self, payload: Mapping[str, Any], *, message: str = "Waiting for input") -> None:
        self.payload = dict(payload)
        self.message = message
        super().__init__(message)


@dataclass(frozen=True)
class FetchedBytes:
    raw_bytes: bytes
    content_type: str | None
    original_uri: str
    retrieved_at: str
    # Human-readable metadata captured during the fetch phase, when the source
    # kind exposes it cheaply (e.g. a YouTube video's title + channel via oEmbed).
    # Absent (None/()) for sources with no knowable metadata — the import then
    # falls back to the URL title.
    title: str | None = None
    authors: tuple[str, ...] = ()


@dataclass(frozen=True)
class JobSpec:
    """One job in an enqueued batch. ``depends_on`` is a tuple of indices into
    the batch's job list (topologically before this job)."""

    job_type: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    depends_on: tuple[int, ...] = ()
