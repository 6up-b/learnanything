"""Deterministic embedding doubles whose geometry follows shared words.

``BagOfWordsEmbedder`` signs-and-hashes each content word into a small vector,
so texts that share words land near each other and unrelated texts are nearly
orthogonal. Field labels of the recipe layouts ("Title:", "Claim:" ...) are
ignored, so the shared template does not make every pair similar.
"""

from __future__ import annotations

import hashlib
import math
import re

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.execution import model_call, report_call_usage

_TOKEN = re.compile(r"[a-z0-9]+")
_IGNORED = frozenset({
    "title", "claim", "description", "type", "aliases", "concept", "preconditions",
    "postconditions", "applicability", "positive", "negative", "examples", "non", "goals",
    "a", "an", "the", "of", "is", "are", "to", "and", "or", "for", "in", "on", "it",
})


class BagOfWordsEmbedder:
    model_id = model = "qwen/qwen3-embedding-8b"
    modalities = frozenset({"text"})
    max_input_tokens = 32_768
    provider_name = "fake_embedding"
    provider_type = "openai_embedding"

    def __init__(self, dims: int = 64, *, fail: bool = False):
        self.dims = dims
        self.fail = fail
        self.calls: list[tuple[list[str], str]] = []

    def vector(self, text: str) -> list[float]:
        values = [0.0] * self.dims
        for token in _TOKEN.findall(text.lower()):
            if token in _IGNORED:
                continue
            digest = int(hashlib.sha256(token.encode("utf-8")).hexdigest()[:12], 16)
            values[digest % self.dims] += 1.0 if (digest >> 20) & 1 else -1.0
        norm = math.sqrt(sum(value * value for value in values))
        if not norm:
            values[0] = 1.0
            norm = 1.0
        return [value / norm for value in values]

    def embed(self, inputs, task_prefix):
        with model_call(self, purpose="embedding", prompt=list(inputs)):
            self.calls.append((list(inputs), task_prefix))
            report_call_usage({
                "input_tokens": sum(len(str(text).encode("utf-8")) for text in inputs),
                "output_tokens": 0,
            })
            if self.fail:
                raise AIProviderUnavailable("embedding provider down")
            return [self.vector(str(text)) for text in inputs]


class ExplodingFactory:
    """A client factory that must never be called (zero-paid-call assertions)."""

    def __init__(self):
        self.calls = 0

    def __call__(self):
        self.calls += 1
        raise AssertionError("an embedding client was constructed where none may be")
