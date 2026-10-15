"""Method-explicit items, the final verify of the round-3 re-review (Codex job
20261015-010744-fq1jgd) on ``c391dd8b8..grading/method-explicit-items`` at
``bcff06523``. It reopened F1 (High) in two historical cases:

* **An unrecoverable rubric.** A contract frozen under the induction method
  recorded its hash before review F1 (the legacy identity, no method). The
  method is cleared and that revision disputed; the live rubric changes and
  no snapshot kept the one graded. The binding fell back to the recorded
  hash, which is also the cleared question's, so the dispute lowered the
  answer graded under induction;
* **A contract without a recorded hash.** A method contract frozen before
  contracts recorded one was invisible to the collision rule, so a check
  made while the item required induction still verified the question with
  its method cleared, with no fresh check.

One fail-closed rule: a method contract binds its answer key only where that
binding is established exactly, by a hash recorded with its key identity
(contracts frozen from now on) or by rebuilding the graded revision from a
rubric the item is known to have had. Otherwise the binding is AMBIGUOUS:
no check of any revision verifies or disputes it, no question without a
method takes credit from a check it may own, and it needs a fresh check.

Fakes only; no network. Every case exists only in a vault that ran this
unmerged branch: main has no ``required_method``.
"""

from __future__ import annotations

import json
from contextlib import closing

import pytest

from learnloop.db.connection import connect

from tests.test_required_method_round3_review import _upsert, gated_successor  # noqa: F401
from tests.test_required_method_round3_rereview import _clear, _contract, pre_fix  # noqa: F401


def _lose_the_graded_rubric(paths, repository, item_id: str) -> None:
    """The live rubric is reworded (R2) and no snapshot kept the one graded (R1)."""

    from tests.source_service_fakes import loaded

    data = loaded(paths).practice_items[item_id].model_dump(mode="json")
    data["grading_rubric"]["criteria"][-1]["description"] += " (reworded)"
    _upsert(paths, item_id, grading_rubric=data["grading_rubric"])
    with closing(connect(repository.sqlite_path)) as connection:
        with connection:
            connection.execute("DELETE FROM practice_item_snapshots WHERE practice_item_id=?", (item_id,))


def _rewrite_contract(repository, attempt_id: str, **changes) -> None:
    """The attempt's stored contract with ``changes`` (None removes a key)."""

    version_id = next(row.assessment_contract_version_id for row in repository.fetch_grading_evidence(attempt_id)
                      if row.assessment_contract_version_id is not None)
    contract = dict(repository.fetch_assessment_contract_version(version_id)["contract"])
    for key, value in changes.items():
        if value is None:
            contract.pop(key, None)
        else:
            contract[key] = value
    with closing(connect(repository.sqlite_path)) as connection:
        with connection:
            connection.execute("UPDATE assessment_contract_versions SET contract_json=? WHERE id=?",
                               (json.dumps(contract, sort_keys=True), version_id))


# -- the verify's first case: the rubric graded cannot be rebuilt ------------------------------------


@pytest.mark.parametrize("cleared", ["disputed", "verified", "unchecked"])
@pytest.mark.parametrize("contract", ["recorded", "historical"])
def test_an_unrebuildable_method_binding_needs_a_fresh_check_whatever_another_revision_says(
        pre_fix, contract, cleared):  # noqa: F811 - the imported fixture
    """The verify's reproduction (``recorded``: the legacy hash) and its
    historical twin (no hash recorded). The method is cleared and the cleared
    question is disputed, verified or left alone by a check written now; the
    rubric graded is then lost. No check of another revision decides the
    regrade: in every case its binding reads ``changed_since_check`` (needs a
    fresh check), names its own revision and no other, and the grade
    certifies nothing."""

    from learnloop.db.stores.source_service import reference_content_hash
    from tests.test_reference_gate_imports import _bindings, _regrade, _status
    from tests.test_required_method_rereview import _check, _make_historical

    paths, repository, item_id, _criterion, attempt, legacy_hash = pre_fix
    if contract == "historical":
        _make_historical(repository, attempt.attempt_id)
    own = legacy_hash if contract == "recorded" else \
        f"unrebuilt:{_contract(repository, attempt.attempt_id)['item_content_hash']}"
    cleared_item = _clear(paths, item_id)
    assert reference_content_hash(cleared_item) == legacy_hash
    if cleared != "unchecked":
        status = "disputed" if cleared == "disputed" else "book_solution"
        _check(repository, item_id, legacy_hash, status, f"rkc_cleared_{cleared}", "2099-01-01T00:00:00Z")
    _lose_the_graded_rubric(paths, repository, item_id)
    _regrade(paths, repository, attempt.attempt_id)
    assert _status(repository, attempt.attempt_id) == "unverified"
    [binding] = _bindings(repository, attempt.attempt_id)
    assert binding["right_id"] == own
    assert "key_status=changed_since_check" in binding["rationale"]
    assert "graded_revision=ambiguous_method" in binding["rationale"]


# -- the verify's second case: a method contract without a recorded hash ----------------------------


def test_a_contract_without_a_recorded_hash_leaves_the_cleared_question_needing_a_fresh_check(
        pre_fix):  # noqa: F811 - the imported fixture
    """The verify's reproduction: a legacy check of the induction question and
    a method contract frozen before contracts recorded a hash. Clearing the
    method recreates the legacy hash; the cleared question needs a fresh
    check, and only a check written now verifies it. The contract itself is
    rebuilt exactly, so it keeps its own binding: a dispute of the cleared
    question never reaches it."""

    from learnloop.db.stores.source_service import effective_key_status, reference_status_for_item
    from tests.test_reference_gate_imports import _bindings, _regrade, _status
    from tests.test_required_method_rereview import _check, _make_historical

    paths, repository, item_id, _criterion, attempt, legacy_hash = pre_fix
    _make_historical(repository, attempt.attempt_id)
    cleared = _clear(paths, item_id)
    with closing(connect(repository.sqlite_path)) as connection:
        assert effective_key_status(connection, cleared) == "changed_since_check"
        assert reference_status_for_item(connection, cleared) == "unverified"
    _check(repository, item_id, legacy_hash, "disputed", "rkc_cleared_disputed", "2099-01-01T00:00:00Z")
    _regrade(paths, repository, attempt.attempt_id)
    assert _status(repository, attempt.attempt_id) == "verified"
    assert _bindings(repository, attempt.attempt_id) == []
    _check(repository, item_id, legacy_hash, "book_solution", "rkc_cleared_checked", "2099-02-01T00:00:00Z")
    with closing(connect(repository.sqlite_path)) as connection:
        assert reference_status_for_item(connection, cleared) == "verified"


# -- the rule's boundary: contracts frozen from now on, and this branch's since review F1 ------------


def test_a_contract_frozen_now_records_its_key_identity_and_binds_exactly_without_its_rubric(
        gated_successor):  # noqa: F811 - the imported fixture
    """A contract frozen now names its hash's identity, so it is never
    ambiguous: with the rubric graded lost, it still binds exactly its
    revision (verified by that revision's check, lowered by its dispute)."""

    from learnloop.db.stores.source_service import KEY_IDENTITY, KEY_IDENTITY_FIELD, reference_content_hash
    from tests.source_service_fakes import loaded
    from tests.test_reference_gate_imports import _attempt, _bindings, _regrade, _status
    from tests.test_required_method_rereview import _check
    from tests.test_required_method_round3_review import _method_import

    paths, repository, spans = gated_successor
    item_id, criterion = _method_import(paths, repository, spans, "mathematical induction")
    graded = reference_content_hash(loaded(paths).practice_items[item_id])
    attempt = _attempt(paths, repository, item_id, criterion=criterion)
    frozen = _contract(repository, attempt.attempt_id)
    assert (frozen["reference_content_hash"], frozen.get(KEY_IDENTITY_FIELD)) == (graded, KEY_IDENTITY)
    _lose_the_graded_rubric(paths, repository, item_id)
    _regrade(paths, repository, attempt.attempt_id)
    assert _status(repository, attempt.attempt_id) == "verified"
    assert _bindings(repository, attempt.attempt_id) == []
    _check(repository, item_id, graded, "disputed", "rkc_graded_disputed", "2099-01-01T00:00:00Z")
    _regrade(paths, repository, attempt.attempt_id)
    assert _status(repository, attempt.attempt_id) == "unverified"
    [binding] = _bindings(repository, attempt.attempt_id)
    assert binding["right_id"] == graded
    assert "graded_revision=frozen" in binding["rationale"]


@pytest.mark.parametrize("rubric", ["rebuilt", "lost"])
def test_a_branch_contract_recorded_since_review_f1_binds_exactly_only_when_it_is_rebuilt(
        gated_successor, rubric):  # noqa: F811 - the imported fixture
    """A contract this branch froze between review F1 and this fix recorded
    the method-aware hash but not its identity, so nothing tells it from a
    legacy hash except a rebuild. Rebuilt: it binds exactly and stays
    verified on its revision's check. Lost: it is ambiguous and needs a fresh
    check, although that check verified it (fail closed; this branch only)."""

    from learnloop.db.stores.source_service import KEY_IDENTITY_FIELD, reference_content_hash
    from tests.source_service_fakes import loaded
    from tests.test_reference_gate_imports import _attempt, _bindings, _regrade, _status
    from tests.test_required_method_round3_review import _method_import

    paths, repository, spans = gated_successor
    item_id, criterion = _method_import(paths, repository, spans, "mathematical induction")
    graded = reference_content_hash(loaded(paths).practice_items[item_id])
    attempt = _attempt(paths, repository, item_id, criterion=criterion)
    _rewrite_contract(repository, attempt.attempt_id, **{KEY_IDENTITY_FIELD: None})
    assert _contract(repository, attempt.attempt_id)["reference_content_hash"] == graded
    if rubric == "lost":
        _lose_the_graded_rubric(paths, repository, item_id)
    _regrade(paths, repository, attempt.attempt_id)
    if rubric == "rebuilt":
        assert _status(repository, attempt.attempt_id) == "verified"
        assert _bindings(repository, attempt.attempt_id) == []
        return
    assert _status(repository, attempt.attempt_id) == "unverified"
    [binding] = _bindings(repository, attempt.attempt_id)
    assert binding["right_id"] == graded
    assert "key_status=changed_since_check" in binding["rationale"]
    assert "graded_revision=ambiguous_method" in binding["rationale"]
