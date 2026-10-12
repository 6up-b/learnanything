"""Model-independent embedding contract. Vectors nominate; they are not evidence."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Protocol, TypeAlias, runtime_checkable

EmbedInput: TypeAlias = str | tuple[str, bytes]
Vector: TypeAlias = list[float]
TASK_PREFIXES = frozenset({"retrieval-document", "retrieval-query", "similarity"})
# Spec Slice 1 §9.1's published estimate (USD per million input tokens), not a
# promise of the provider's invoice. Unknown models fail closed in every caller.
EMBEDDING_PRICES_PER_MILLION = {"qwen/qwen3-embedding-8b": 0.01}

_request_timeout: ContextVar[float | None] = ContextVar("embedding_request_timeout", default=None)


@contextmanager
def embedding_request_timeout(seconds: float | None) -> Iterator[None]:
    """Bound the embedding requests made inside this scope to ``seconds``.

    A caller with a time box (Slice 2 T6's retrieval) sets the time it has
    left; a client that sends requests over the network passes it as that
    request's timeout. ``None`` keeps the client's own default. Context-local,
    restored on exit, and nestable, so no protocol change reaches the fakes.
    """

    token = _request_timeout.set(seconds)
    try:
        yield
    finally:
        _request_timeout.reset(token)


def current_embedding_timeout() -> float | None:
    """The request timeout set by :func:`embedding_request_timeout`, or None."""

    return _request_timeout.get()


@runtime_checkable
class EmbeddingClient(Protocol):
    model_id: str
    dims: int
    modalities: frozenset[str]
    max_input_tokens: int

    def embed(self, inputs: list[EmbedInput], task_prefix: str) -> list[Vector]:
        """Embed one batch in input order; callers own admission and retries.

        A client that makes network requests honours
        :func:`current_embedding_timeout` as the request timeout when it is set.
        """
        ...
