"""What other test files use from ``tests/test_practice_index_find.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.ai.spend import SpendCaps
from learnloop.db.repositories import Repository
from learnloop.ops.embedding_backfill import backfill_embeddings
from learnloop.practice_index.dossiers import generate_dossiers
from learnloop.vault.loader import load_vault

from tests.practice_index_fakes import FakePracticeLLM, HashingEmbedder


CAPS = SpendCaps(max_candidates=1000, max_calls=100, max_total_tokens=10_000_000, max_estimated_usd=1.0)


def _index(paths, *, embeddings=True):
    vault = load_vault(paths.root)
    llm, embedder = FakePracticeLLM(), HashingEmbedder()
    assert generate_dossiers(vault, caps=CAPS, client=llm)["status"] == "complete"
    if embeddings:
        vault = load_vault(paths.root)
        report = backfill_embeddings(vault, caps=CAPS, client_factory=lambda: embedder)
        assert report["status"] == "complete", report
    return load_vault(paths.root), Repository(paths.sqlite_path), llm, embedder
