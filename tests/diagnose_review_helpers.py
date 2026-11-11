"""What other test files use from ``tests/test_diagnose_review.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.ai.spend import SpendCaps
from learnloop.diagnosis.offline_review.runner import ReviewClients, ReviewOptions, run_review

from tests.diagnosis_fakes import FakeEmbeddingClient, ReviewFakeClient


CAPS = SpendCaps(max_calls=2000, max_candidates=500, max_total_tokens=10**8, max_estimated_usd=10.0)
OPTIONS = ReviewOptions(sample_size=10, planted_per_shape=1, repeat_subset=2, sweep_budgets=(2_000,), probe_items=2)


def _run(paths, vault, run_dir, *, client=None, options=OPTIONS, caps=CAPS, cancelled=None):
    client = client or ReviewFakeClient()
    clients = ReviewClients(grading=client, diagnosis=client, judge=client, generator=client, embedding=FakeEmbeddingClient())
    result = run_review(vault, source_sqlite=paths.sqlite_path, run_dir=run_dir, options=options, clients=clients, caps=caps, cancelled=cancelled)
    return client, result
