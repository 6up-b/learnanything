"""What other test files use from ``tests/test_compare_sources_keep.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from contextlib import closing

from learnloop.db.connection import connect
from learnloop.db.stores.source_block_fts import blocks_by_key

from tests.source_service_fakes import FakeServiceLLM


QUESTION = "why does the determinant change sign when two rows are swapped"
PINS = ["ext_book:s6", "ext_text:t3"]


def _fake_service(monkeypatch, llm=None):
    import learnloop.instructional.sources as service

    real = service.propose_comparison
    llm = llm or FakeServiceLLM()
    monkeypatch.setattr(service, "propose_comparison", lambda *a, **k: real(*a, client=llm, verify_client=llm, **k))
    return llm


def _block_text(repository, key: str) -> str:
    extraction, span = key.split(":", 1)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return blocks_by_key(connection, [(extraction, span)])[(extraction, span)].text
