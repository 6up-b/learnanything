"""What other test files use from ``tests/test_graph_nomination_ingest.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from pathlib import Path

from learnloop.ai.spend import SpendCaps
from learnloop.ops.embedding_backfill import backfill_embeddings
from learnloop.vault.loader import load_vault

from tests.embedding_fakes import BagOfWordsEmbedder


def _backfill(root: Path, embedder: BagOfWordsEmbedder, recipes: tuple[str, ...]) -> None:
    report = backfill_embeddings(
        load_vault(root), caps=SpendCaps(max_candidates=1000, max_total_tokens=10**7),
        recipes=recipes, client_factory=lambda: embedder,
    )
    assert report["status"] == "complete", report
