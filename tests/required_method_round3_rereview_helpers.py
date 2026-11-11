"""What other test files use from ``tests/test_required_method_round3_rereview.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json
from contextlib import closing

import pytest

from learnloop.db.connection import connect
from learnloop.db.stores.source_service import reference_content_hash as _METHOD_AWARE_HASH

from tests.required_method_round3_review_helpers import _upsert


INDUCTION = "mathematical induction"


def _legacy_hash(item) -> str:
    """The key identity before review F1: the method was not part of it."""

    return _METHOD_AWARE_HASH(item.model_copy(update={"required_method": None}))


def _contract(repository, attempt_id: str) -> dict:
    version_id = next(row.assessment_contract_version_id for row in repository.fetch_grading_evidence(attempt_id)
                      if row.assessment_contract_version_id is not None)
    return dict(repository.fetch_assessment_contract_version(version_id)["contract"])


def _without_contract_identity(repository, attempt_id: str) -> None:
    """The attempt's contract as the code before the final verify froze it:
    without the key identity of its hash."""

    version_id = next(row.assessment_contract_version_id for row in repository.fetch_grading_evidence(attempt_id)
                      if row.assessment_contract_version_id is not None)
    contract = dict(repository.fetch_assessment_contract_version(version_id)["contract"])
    contract.pop("key_identity", None)
    with closing(connect(repository.sqlite_path)) as connection:
        with connection:
            connection.execute("UPDATE assessment_contract_versions SET contract_json=? WHERE id=?",
                               (json.dumps(contract, sort_keys=True), version_id))


def _checks(repository, item_id: str) -> list[dict]:
    from learnloop.db.stores.source_service import key_checks_for_item

    with closing(connect(repository.sqlite_path)) as connection:
        connection.row_factory = __import__("sqlite3").Row
        return key_checks_for_item(connection, item_id)


@pytest.fixture
def pre_fix(gated_successor, monkeypatch):
    """A verified exercise answered under induction by the code before the
    fix: its import check, the check of its induction revision and its
    contract all carry the legacy hash, and neither a check nor the contract
    records an identity (contracts record it since the final verify)."""

    from learnloop.db.stores import source_service
    from learnloop.learner import assessment_contracts
    from tests.source_service_fakes import loaded
    from tests.reference_gate_imports_helpers import _attempt, _status, _verified_import
    from tests.required_method_rereview_helpers import _check

    paths, repository, spans = gated_successor
    with monkeypatch.context() as legacy:
        legacy.setattr(source_service, "reference_content_hash", _legacy_hash)
        legacy.setattr(assessment_contracts, "_reference_content_hash", _legacy_hash)
        legacy.setattr(source_service, "_identity_fields", lambda legacy_identity=False: {}, raising=False)
        item_id = _verified_import(paths, repository, spans)
        criterion = loaded(paths).rubric_for_item(loaded(paths).practice_items[item_id]).criteria[0].id
        _upsert(paths, item_id, required_method={"name": INDUCTION, "criterion_ids": [criterion],
                                                 "statement": "source", "decided_by": "owner"})
        induction = loaded(paths).practice_items[item_id]
        legacy_hash = _legacy_hash(induction)
        _check(repository, item_id, legacy_hash, "book_solution", "rkc_prefix_induction", "2026-01-01T00:00:00Z")
        attempt = _attempt(paths, repository, item_id, criterion=criterion)
        assert _status(repository, attempt.attempt_id) == "verified"
    _without_contract_identity(repository, attempt.attempt_id)
    assert _contract(repository, attempt.attempt_id)["reference_content_hash"] == legacy_hash
    assert "key_identity" not in _contract(repository, attempt.attempt_id)
    assert all("key_identity" not in check["verification"] for check in _checks(repository, item_id))
    return paths, repository, item_id, criterion, attempt, legacy_hash


def _clear(paths, item_id: str):
    from tests.source_service_fakes import loaded

    _upsert(paths, item_id, required_method=None)
    return loaded(paths).practice_items[item_id]
