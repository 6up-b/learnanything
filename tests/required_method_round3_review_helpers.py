"""What other test files use from ``tests/test_required_method_round3_review.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json
from contextlib import closing

import pytest

from learnloop.db.connection import connect
from learnloop.vault.loader import load_vault


def _upsert(paths, item_id: str, **fields) -> None:
    from learnloop.vault.writer import upsert_practice_item

    data = load_vault(paths.root).practice_items[item_id].model_dump(mode="json")
    data.update(fields)
    upsert_practice_item(paths.root, data)


@pytest.fixture
def gated_successor(tmp_path, monkeypatch):
    from learnloop.content.authoring import pf_sandbox
    from tests.source_service_fakes import build_textbook_vault

    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    monkeypatch.setattr(pf_sandbox, "_sandbox_bwrap_path", lambda: None)
    return paths, repository, spans


def _method_import(paths, repository, spans, name: str) -> tuple[str, str]:
    """A verified textbook exercise whose (owner-decided) required method is
    ``name``, its key checked for exactly that question."""

    from learnloop.db.stores.source_service import reference_content_hash
    from tests.source_service_fakes import loaded
    from tests.reference_gate_imports_helpers import _verified_import
    from tests.required_method_rereview_helpers import _check

    item_id = _verified_import(paths, repository, spans)
    item = loaded(paths).practice_items[item_id]
    criterion = loaded(paths).rubric_for_item(item).criteria[0].id
    _upsert(paths, item_id, required_method={"name": name, "criterion_ids": [criterion], "statement": "source",
                                             "decided_by": "owner"})
    _check(repository, item_id, reference_content_hash(loaded(paths).practice_items[item_id]), "book_solution",
           "rkc_method_checked", "2026-01-01T00:00:00Z")
    return item_id, criterion


def _needs_bwrap():
    from learnloop.content.authoring.pf_sandbox import sandbox_available

    if not sandbox_available():
        pytest.skip("bubblewrap is not installed")


def _stretch_stem(repository, candidate_id: str, stem: str) -> None:
    with closing(connect(repository.sqlite_path)) as connection:
        with connection:
            payload = json.loads(connection.execute("SELECT payload_json FROM pf_candidates WHERE id=?",
                                                    (candidate_id,)).fetchone()[0])
            payload["stem"] = stem
            connection.execute("UPDATE pf_candidates SET payload_json=? WHERE id=?",
                               (json.dumps(payload, sort_keys=True), candidate_id))
