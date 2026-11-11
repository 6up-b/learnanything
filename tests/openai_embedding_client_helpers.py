"""What other test files use from ``tests/test_openai_embedding_client.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from types import SimpleNamespace


def response(*vectors, indices=None):
    return SimpleNamespace(
        data=[SimpleNamespace(index=index, embedding=vector) for index, vector in
              zip(indices if indices is not None else range(len(vectors)), vectors, strict=True)],
        usage=SimpleNamespace(prompt_tokens=12, total_tokens=12),
    )
