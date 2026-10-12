"""Model-independent embedding contract. Vectors nominate; they are not evidence."""

from typing import Protocol, TypeAlias, runtime_checkable

EmbedInput: TypeAlias = str | tuple[str, bytes]
Vector: TypeAlias = list[float]
TASK_PREFIXES = frozenset({"retrieval-document", "retrieval-query", "similarity"})
# Spec Slice 1 §9.1's published estimate (USD per million input tokens), not a
# promise of the provider's invoice. Unknown models fail closed in every caller.
EMBEDDING_PRICES_PER_MILLION = {"qwen/qwen3-embedding-8b": 0.01}


@runtime_checkable
class EmbeddingClient(Protocol):
    model_id: str
    dims: int
    modalities: frozenset[str]
    max_input_tokens: int

    def embed(self, inputs: list[EmbedInput], task_prefix: str) -> list[Vector]:
        """Embed one batch in input order; callers own admission and retries."""
        ...
