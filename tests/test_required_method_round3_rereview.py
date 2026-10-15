"""Method-explicit items, the round-3 re-review (stage method-explicit-3,
Codex job 20261014-210320-dJqoCB) on ``5392d7c3c..grading/method-explicit-items``.

* F1 (reopened): a contract or a key check recorded before the key named the
  required method (round 3, before review F1) used the legacy identity:
  statement, expected answer and rubric only. Clearing the method recreates
  exactly that hash, so the cleared question read as verified by a check of
  the method question, and a dispute of the cleared question reached an
  answer graded under the method. Checks now record the identity they were
  computed under, and the legacy records are read through explicit
  compatibility rules;
* F9: the resume budgeted the unjudged survivors chosen by character count,
  while a judgment's estimate grows with the UTF-8 bytes of its stem.

Fakes only; no network.
"""

from __future__ import annotations

import json
from contextlib import closing

import pytest

from learnloop.ai.spend import SpendCaps
from learnloop.db.connection import connect
from learnloop.db.stores.source_service import reference_content_hash as _METHOD_AWARE_HASH

from tests.test_required_method_round3_review import _needs_bwrap, _stretch_stem, _upsert, gated_successor  # noqa: F401

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
def pre_fix(gated_successor, monkeypatch):  # noqa: F811 - the imported fixture
    """A verified exercise answered under induction by the code before the
    fix: its import check, the check of its induction revision and its
    contract all carry the legacy hash, and neither a check nor the contract
    records an identity (contracts record it since the final verify)."""

    from learnloop.db.stores import source_service
    from learnloop.learner import assessment_contracts
    from tests.source_service_fakes import loaded
    from tests.test_reference_gate_imports import _attempt, _status, _verified_import
    from tests.test_required_method_rereview import _check

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


# -- F1 (reopened): legacy identities never meet the cleared question -------------------------------


def test_f1_a_cleared_method_is_never_verified_by_a_check_of_the_method_question(pre_fix):
    """The re-review's first reproduction: the cleared question's hash is the
    legacy hash the pre-fix checks of the induction question carry. They no
    longer verify it; a check of the cleared question does."""

    from learnloop.db.stores.source_service import (
        effective_key_status, reference_content_hash, reference_status_for_item,
    )
    from tests.test_required_method_rereview import _check

    paths, repository, item_id, _criterion, _attempt, legacy_hash = pre_fix
    cleared = _clear(paths, item_id)
    assert reference_content_hash(cleared) == legacy_hash
    with closing(connect(repository.sqlite_path)) as connection:
        assert effective_key_status(connection, cleared) == "changed_since_check"
        assert reference_status_for_item(connection, cleared) == "unverified"
    _check(repository, item_id, legacy_hash, "book_solution", "rkc_cleared_checked", "2099-01-01T00:00:00Z")
    with closing(connect(repository.sqlite_path)) as connection:
        assert reference_status_for_item(connection, cleared) == "verified"


def test_f1_a_dispute_of_the_cleared_question_never_reaches_the_answer_graded_under_the_method(pre_fix):
    """The re-review's second reproduction: the cleared revision is disputed
    (same hash as the legacy contract recorded); the regrade of the
    induction answer keeps the binding it had."""

    from tests.test_reference_gate_imports import _bindings, _regrade, _status
    from tests.test_required_method_rereview import _check

    paths, repository, item_id, _criterion, attempt, legacy_hash = pre_fix
    _clear(paths, item_id)
    _check(repository, item_id, legacy_hash, "disputed", "rkc_cleared_disputed", "2099-01-01T00:00:00Z")
    _regrade(paths, repository, attempt.attempt_id)
    assert _status(repository, attempt.attempt_id) == "verified"
    assert _bindings(repository, attempt.attempt_id) == []


def test_f1_the_legacy_contract_keeps_its_checks_and_meets_its_own_question_under_the_new_identity(pre_fix):
    """Explicit compatibility: the legacy contract still binds the pre-fix
    checks (verified), and a dispute of the induction question recorded
    under the method-aware identity reaches it."""

    from learnloop.db.stores.source_service import reference_content_hash
    from tests.source_service_fakes import loaded
    from tests.test_reference_gate_imports import _bindings, _regrade, _status
    from tests.test_required_method_rereview import _check

    paths, repository, item_id, _criterion, attempt, _legacy = pre_fix
    _regrade(paths, repository, attempt.attempt_id)
    assert _status(repository, attempt.attempt_id) == "verified"
    induction = reference_content_hash(loaded(paths).practice_items[item_id])
    _check(repository, item_id, induction, "disputed", "rkc_induction_disputed", "2099-01-01T00:00:00Z")
    _regrade(paths, repository, attempt.attempt_id)
    assert _status(repository, attempt.attempt_id) == "unverified"
    [binding] = _bindings(repository, attempt.attempt_id)
    assert binding["right_id"] == induction


def test_f1_a_historical_method_contract_keeps_its_legacy_checks(pre_fix):
    """A method contract frozen before contracts recorded the hash (round 2,
    F19) is rebuilt under the method-aware identity; the checks of its
    revision under the legacy identity still bind it."""

    from tests.test_reference_gate_imports import _bindings, _regrade, _status
    from tests.test_required_method_rereview import _make_historical

    paths, repository, _item_id, _criterion, attempt, _legacy = pre_fix
    _make_historical(repository, attempt.attempt_id)
    _regrade(paths, repository, attempt.attempt_id)
    assert _status(repository, attempt.attempt_id) == "verified"
    assert _bindings(repository, attempt.attempt_id) == []


def test_f1_checks_record_their_identity_and_an_item_without_a_method_keeps_its_checks(tmp_path):
    """A check written now records the identity it was computed under; an
    item that never had a method reads every check of its hash, with or
    without one (every check on main has none)."""

    from learnloop.db.stores.source_service import key_checks_for_item, reference_status_for_item
    from tests.source_service_fakes import build_textbook_vault, loaded
    from tests.test_reference_gate_imports import _verified_import

    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    item_id = _verified_import(paths, repository, spans)
    item = loaded(paths).practice_items[item_id]
    with closing(connect(repository.sqlite_path)) as connection:
        connection.row_factory = __import__("sqlite3").Row
        [check] = key_checks_for_item(connection, item_id)
        assert check["verification"].get("key_identity") == "method-aware"
        with connection:
            # The import's own check stays; a later dispute written before
            # identities were recorded (as on main) is still this item's.
            connection.execute(
                "INSERT INTO reference_key_checks (id,practice_item_id,import_id,content_hash,key_status,rung,"
                "verification_json,ledger_ids_json,trigger,started_at,created_at) VALUES "
                "('rkc_main',?,NULL,?,'disputed','test','{}','[]','verify',?,?)",
                (item_id, check["content_hash"], "2099-01-01T00:00:00Z", "2099-01-01T00:00:00Z"))
        assert reference_status_for_item(connection, item) == "unverified"


@pytest.mark.parametrize("persisted", ["before_the_fix", "since"])
def test_f1_a_ladder_result_committed_later_keeps_the_identity_it_was_computed_under(tmp_path, monkeypatch,
                                                                                    persisted):
    """A ladder result persisted before the import's commit names its hash's
    identity. Recovered later, the check records it only when the record
    did: a record written before the fix stays a legacy check."""

    from learnloop.content.authoring import source_exercise_import as SEI
    from tests.source_service_fakes import FakeServiceLLM, build_textbook_vault, service_clients
    from tests.test_source_exercise_import import _ProcessDeath, _checks, _import, _row

    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    real = SEI._commit_written

    def die(*_args, **_kwargs):
        raise _ProcessDeath()

    monkeypatch.setattr(SEI, "_commit_written", die)
    with pytest.raises(_ProcessDeath):
        _import(paths, repository, spans["exercises"][1], FakeServiceLLM(), import_id="sei_identity")
    monkeypatch.setattr(SEI, "_commit_written", real)
    row = _row(repository, "sei_identity")
    if persisted == "before_the_fix":
        verification = dict(row["verification"])
        verification["ladder_result"] = {key: value for key, value in verification["ladder_result"].items()
                                         if key != "key_identity"}
        with closing(connect(repository.sqlite_path)) as connection:
            with connection:
                connection.execute("UPDATE source_exercise_imports SET verification_json=? WHERE id=?",
                                   (json.dumps(verification, sort_keys=True), "sei_identity"))
    SEI.recover_import_checks(paths.root, repository, clients=service_clients(FakeServiceLLM()))
    [check] = _checks(repository, row["practice_item_id"])
    assert ("key_identity" in check["verification"]) is (persisted == "since")


# -- F9: the resume's judgment bound is the largest estimates -----------------------------------------


def test_f9_the_resume_budgets_the_largest_judgment_estimates_not_the_longest_stems(tmp_path):
    """One slot; the survivor with the most characters is ASCII, a shorter one
    is mostly multibyte and estimates higher. The bound is the larger
    estimate, and a cap between the two refuses the dry run."""

    from learnloop.ai.errors import AIProviderUnavailable
    from learnloop.content.proposals.method_statement_judge import planned_tokens
    from tests.pf_fakes import clients, enable_pf
    from tests.test_pf_generation import run
    from tests.test_required_method_authority import VARIANT_CONSISTENT, StatementDecider, _pf_method_vault
    from tests.test_required_method_reopened import FailingDecider
    from tests.test_required_method_round3 import _family_rows

    _needs_bwrap()
    repository, paths = _pf_method_vault(tmp_path)
    enable_pf(paths.root, max_published_per_day=5)
    run(paths, publish=True, select=1, fakes=clients(required_method_judge=FailingDecider(
        AIProviderUnavailable("timed out"))))
    survivors = [row for row in _family_rows(repository) if row["status"] in ("selected", "not_selected")]
    assert len(survivors) >= 2
    [first, *rest] = survivors
    with closing(connect(repository.sqlite_path)) as connection:
        with connection:
            selection = json.loads(first["selection_json"])
            for marker in ("selected_order", "selection_complete"):
                selection.pop(marker, None)
            connection.execute("UPDATE pf_candidates SET selection_json=? WHERE id=?",
                               (json.dumps(selection, sort_keys=True), first["id"]))
            for row in rest:
                connection.execute("UPDATE pf_candidates SET status='survivor', selection_json=NULL WHERE id=?",
                                   (row["id"],))
    ascii_stem = "Solve for x by substitution: " + "x + 1 = 2; " * 160
    heavy_stem = "Résolvez pour x par substitution : " + "∑∫≈≤≥∀∃⇒∞≠" * 80
    assert len(ascii_stem) > len(heavy_stem)
    by_ascii = planned_tokens("variant", ascii_stem, "substitution")
    by_heavy = planned_tokens("variant", heavy_stem, "substitution")
    assert by_heavy > by_ascii + 500
    _stretch_stem(repository, survivors[0]["id"], ascii_stem)
    _stretch_stem(repository, survivors[1]["id"], heavy_stem)
    for row in survivors[2:]:
        _stretch_stem(repository, row["id"], "Solve for x by substitution: x + 1 = 2.")
    fakes = clients(required_method_judge=StatementDecider(VARIANT_CONSISTENT))
    dry = run(paths, publish=True, select=1, dry_run=True, fakes=fakes)
    [plan] = dry["plan"]
    assert plan["resume"]["stage"] == "selection"
    judgment = plan["required_method_judgment"]
    assert (judgment["calls"], judgment["tokens"], judgment["per_call_tokens"]) == (1, by_heavy, by_heavy)
    selection = plan["roles"]["selection"]["tokens"]
    between = SpendCaps(max_candidates=100, max_pairs=2000, max_calls=10,
                        max_total_tokens=selection + (by_ascii + by_heavy) // 2, max_estimated_usd=10_000)
    capped = run(paths, publish=True, select=1, dry_run=True, caps=between, fakes=fakes)
    assert capped["status"] == "over_budget", capped.get("reason")
