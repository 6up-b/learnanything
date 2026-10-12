"""One paid, metered request per batch; no hidden retries or batch splitting."""

from __future__ import annotations

import math
import os

from learnloop.ai.embedding import EmbedInput, TASK_PREFIXES, Vector
from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.execution import model_call, report_call_usage
from learnloop.ai.transport import EMBEDDING
from learnloop.ai.usage import receipt_fields_from_chat_response
from learnloop.config import AIProviderConfig

DEFAULT_MODEL = "qwen/qwen3-embedding-8b"
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"


def prefixed_text(text: str, task_prefix: str, model_id: str) -> str:
    """Map the three stable tasks to model conventions, never arbitrary instructions."""
    if task_prefix not in TASK_PREFIXES:
        raise ValueError(f"Unsupported embedding task prefix: {task_prefix!r}")
    if model_id.startswith("qwen/qwen3-embedding"):
        if task_prefix == "retrieval-query":
            return f"Instruct: Given a search query, retrieve relevant passages that answer the query\nQuery: {text}"
    elif model_id.startswith("google/gemini-embedding"):
        instruction = {
            "retrieval-document": "Represent this document for retrieval",
            "retrieval-query": "Find relevant documents for this query",
            "similarity": "Represent this text for semantic similarity",
        }[task_prefix]
        return f"{instruction}:\n{text}"
    return text


class OpenAIEmbeddingProviderClient:
    provider_type = "openai_embedding"
    default_base_url = DEFAULT_BASE_URL
    modalities = frozenset({"text"})

    def __init__(self, provider_name: str, profile: AIProviderConfig):
        from openai import OpenAI

        self.provider_name = provider_name
        self.profile = profile
        self.model_id = profile.model or DEFAULT_MODEL
        self.model = self.model_id
        self.dims = getattr(profile, "dimensions", 4096)
        self.max_input_tokens = getattr(profile, "max_input_tokens", 32768)
        if self.dims <= 0 or self.max_input_tokens <= 0:
            raise ValueError("Embedding dimensions and input limit must be positive")
        key_env = profile.api_key_env or "OPENROUTER_API_KEY"
        key = os.environ.get(key_env)
        if not key:
            raise AIProviderUnavailable(f"Environment variable {key_env} is required.")
        self._client = OpenAI(
            api_key=key,
            base_url=profile.base_url or DEFAULT_BASE_URL,
            timeout=profile.timeout_seconds or 180,
            max_retries=0,
        )

    def supports(self, capability: str) -> bool:
        return capability == EMBEDDING

    def embed(self, inputs: list[EmbedInput], task_prefix: str) -> list[Vector]:
        if task_prefix not in TASK_PREFIXES:
            raise ValueError(f"Unsupported embedding task prefix: {task_prefix!r}")
        texts = []
        for value in inputs:
            if not isinstance(value, str):
                raise ValueError("This embedding client supports text only")
            text = prefixed_text(value, task_prefix, self.model_id)
            # UTF-8 bytes conservatively bound byte-level tokenizer tokens.
            # Do not silently truncate canonical text or split into extra paid calls.
            if not value.strip() or len(text.encode("utf-8")) > self.max_input_tokens:
                raise ValueError("Embedding input is empty or exceeds the conservative input limit")
            texts.append(text)
        if not texts:
            return []
        with model_call(self, purpose="embedding", prompt=texts):
            try:
                response = self._client.embeddings.create(
                    model=self.model_id,
                    input=texts,
                    encoding_format="float",
                    extra_body={"provider": {"data_collection": "deny"}},
                )
            except Exception as exc:
                # Normalize SDK errors for the bounded retry owner. Provider
                # exception messages can echo request text or credentials.
                raise AIProviderUnavailable(
                    f"Embedding request failed ({type(exc).__name__})"
                ) from None
            # OpenAI embedding responses share chat's usage/id/model envelope,
            # but have no choices and generate no output tokens.
            report_call_usage({**receipt_fields_from_chat_response(response), "output_tokens": 0})
            rows = sorted(response.data, key=lambda row: row.index)
            if [row.index for row in rows] != list(range(len(texts))):
                raise ValueError("Embedding response indices do not match the input batch")
            vectors = []
            widths = {len(row.embedding) for row in rows}
            if len(widths) != 1 or next(iter(widths)) < self.dims:
                raise ValueError("Embedding response dimensions do not match the configured dimensions")
            width = next(iter(widths))
            if width > self.dims and not self.model_id.startswith((
                "qwen/qwen3-embedding", "google/gemini-embedding", "openai/text-embedding-3-",
            )):
                raise ValueError("Dimension truncation requires a known MRL embedding model")
            for row in rows:
                vector = [float(value) for value in row.embedding]
                if not all(math.isfinite(value) for value in vector):
                    raise ValueError("Embedding response contains non-finite values")
                vector = vector[:self.dims]
                # MRL truncation preserves direction after normalization.
                norm = math.hypot(*vector)
                if not norm or not math.isfinite(norm):
                    raise ValueError("Embedding response has an invalid vector norm")
                vectors.append([value / norm for value in vector])
            return vectors
