"""S1 (G19): certification follows the answer key (C3, mvp-0.18)."""
from __future__ import annotations

from contextlib import closing

import pytest

from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION, PROOF_ROUTE_CHECK_ALGORITHM_VERSION, SOURCE_REFERENCE_GATE_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.content.authoring import pf_sandbox
from learnloop.content.authoring import source_exercise_import as SEI
from learnloop.db.connection import connect
from learnloop.db.stores.observation_ledger import load_canonical_observation_ledger
from learnloop.db.stores.source_service import insert_import, reference_status_for_item
from learnloop.diagnosis.causal_activity_policy import resolve_attempt_activity_policy
from learnloop.vault.writer import upsert_practice_item
from tests.helpers import set_algorithm_version
from tests.source_service_fakes import FakeServiceLLM, build_textbook_vault, loaded, service_clients


@pytest.mark.parametrize("status,certifies", [
    ("unverified", False), ("verified", True), ("not_applicable", True), (None, True)])
def test_the_policy_gate_changes_only_certification(status, certifies):
    base = resolve_attempt_activity_policy(attempt_type="independent_attempt")
    gated = resolve_attempt_activity_policy(attempt_type="independent_attempt", reference_status=status)
    assert gated.eligible_for_certification is certifies
    assert gated.eligible_for_fsrs == base.eligible_for_fsrs
    assert gated.counts_as_assisted == base.counts_as_assisted
    assert gated.contamination_class == base.contamination_class


def test_the_gate_is_a_successor_after_the_route_check():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(PROOF_ROUTE_CHECK_ALGORITHM_VERSION) + 1] == SOURCE_REFERENCE_GATE_ALGORITHM_VERSION
    assert LATEST_ALGORITHM_VERSION == SUCCESSOR_CHAIN[-1]


@pytest.fixture
def gated(tmp_path, monkeypatch):
    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    set_algorithm_version(paths, SOURCE_REFERENCE_GATE_ALGORITHM_VERSION)
    monkeypatch.setattr(pf_sandbox, "_sandbox_bwrap_path", lambda: None)
    return paths, repository, spans


def _attempt(paths, repository, item_id, *, points=2, criterion="answer"):
    vault = loaded(paths)
    return complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id=item_id, learner_answer_md="x = 5", attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={criterion: points}, fatal_errors=[], confidence=3),
    )


def _status(repository, attempt_id):
    with repository.connection() as connection:
        return connection.execute("SELECT reference_status FROM practice_attempts WHERE id=?",
                                  (attempt_id,)).fetchone()[0]


def test_attempts_record_the_key_status_and_unverified_ones_never_certify(gated):
    paths, repository, spans = gated
    unverified = SEI.import_source_exercise(
        paths.root, repository, extraction_id="ext_text", span_ids=[spans["exercises"][2]], caller="learner",
        clients=service_clients(FakeServiceLLM(drop_cited_quote=True)))
    verified = SEI.import_source_exercise(
        paths.root, repository, extraction_id="ext_text", span_ids=[spans["exercises"][1]], caller="learner",
        clients=service_clients(FakeServiceLLM()))
    assert (unverified["key_status"], verified["key_status"]) == ("panel_agrees_unconfirmed", "book_solution")
    first = _attempt(paths, repository, unverified["practice_item_id"])
    second = _attempt(paths, repository, verified["practice_item_id"])
    assert _status(repository, first.attempt_id) == "unverified"
    assert _status(repository, second.attempt_id) == "verified"
    # It schedules (FSRS) like any attempt.
    assert first.due_at and second.due_at
    # The replay ledger carries the recorded signal, so the projection gates it.
    with connect(repository.sqlite_path) as connection:
        rows = {row["attempt_id"]: row for row in load_canonical_observation_ledger(connection)}
    assert rows[first.attempt_id]["reference_status"] == "unverified"
    assert rows[second.attempt_id]["reference_status"] == "verified"
    policy = resolve_attempt_activity_policy(attempt_type="independent_attempt",
                                             reference_status=rows[first.attempt_id]["reference_status"])
    assert policy.eligible_for_certification is False and policy.eligible_for_fsrs is True


def test_a_later_verification_never_rewrites_earlier_attempts(gated):
    paths, repository, spans = gated
    result = SEI.import_source_exercise(
        paths.root, repository, extraction_id="ext_text", span_ids=[spans["exercises"][2]], caller="learner",
        clients=service_clients(FakeServiceLLM(drop_cited_quote=True)))
    before = _attempt(paths, repository, result["practice_item_id"])
    assert _status(repository, before.attempt_id) == "unverified"
    # The key verifies later (the book's solution is found and quoted this time).
    report = SEI.verify_item_key(paths.root, repository, result["practice_item_id"], trigger="verify",
                                 clients=service_clients(FakeServiceLLM()))
    assert report["key_status"] in ("book_solution", "panel_agrees_unconfirmed")
    after = _attempt(paths, repository, result["practice_item_id"])
    assert _status(repository, before.attempt_id) == "unverified"
    expected = "verified" if report["key_status"] == "book_solution" else "unverified"
    assert _status(repository, after.attempt_id) == expected


def test_items_that_are_not_imports_record_not_applicable(gated):
    paths, repository, _spans = gated
    result = _attempt(paths, repository, "pi_eigen_1", points=4, criterion="correct")
    assert _status(repository, result.attempt_id) == "not_applicable"


def test_below_the_tag_the_gate_never_runs(tmp_path, monkeypatch):
    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    set_algorithm_version(paths, PROOF_ROUTE_CHECK_ALGORITHM_VERSION)
    monkeypatch.setattr(pf_sandbox, "_sandbox_bwrap_path", lambda: None)
    result = SEI.import_source_exercise(
        paths.root, repository, extraction_id="ext_text", span_ids=[spans["exercises"][2]], caller="learner",
        clients=service_clients(FakeServiceLLM(drop_cited_quote=True)))
    attempt = _attempt(paths, repository, result["practice_item_id"])
    assert _status(repository, attempt.attempt_id) == "not_applicable"


def test_a_historical_reader_import_resolves_to_model_answer(gated):
    paths, repository, _spans = gated
    upsert_practice_item(paths.root, {
        "id": "pi_exercise_old", "learning_object_id": "lo_matrices", "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt"], "prompt": "Old reader import.", "expected_answer": "x",
        "evidence_facets": ["facet_eigen"], "evidence_weights": {"facet_eigen": 1.0},
        "provenance": {"origin": "canonical_extract", "source_refs": []},
        "created_at": "2026-10-01T00:00:00Z", "updated_at": "2026-10-01T00:00:00Z",
    })
    repository.append_interaction_event(
        kind="learner_item_authored", origin="learner", subject_type="practice_item", subject_id="pi_exercise_old",
        payload_json='{"mechanism": "reader_exercise_import"}')
    vault = loaded(paths)
    with closing(connect(repository.sqlite_path)) as connection:
        assert reference_status_for_item(connection, vault.practice_items["pi_exercise_old"]) == "unverified"
        # canonical_extract alone (an AI authoring proposal over a source) is not an import.
        assert reference_status_for_item(connection, vault.practice_items["pi_eigen_1"]) == "not_applicable"


def test_a_reader_import_row_counts_as_an_import(gated):
    paths, repository, _spans = gated
    with repository.connection() as connection:
        insert_import(connection, id="sei_r", created_at="2026-10-12T00:00:00Z", caller="reader",
                      extraction_id="ext_text", span_ids=["t7"], status="written", practice_item_id="pi_eigen_2",
                      key_status="model_answer")
    vault = loaded(paths)
    with closing(connect(repository.sqlite_path)) as connection:
        assert reference_status_for_item(connection, vault.practice_items["pi_eigen_2"]) == "unverified"


def test_a_shadow_rebuild_at_the_tag_shows_zero_deltas(gated):
    """Never retroactive: with every recorded status kept, mvp-0.18 projects what mvp-0.17 does."""
    from learnloop.substrate.shadow_rebuild import shadow_rebuild

    paths, repository, spans = gated
    result = SEI.import_source_exercise(
        paths.root, repository, extraction_id="ext_text", span_ids=[spans["exercises"][1]], caller="learner",
        clients=service_clients(FakeServiceLLM()))
    _attempt(paths, repository, result["practice_item_id"])
    _attempt(paths, repository, "pi_eigen_1", points=4, criterion="correct")
    # The live state here was built incrementally, so each rebuild is compared
    # with it; the two rebuilds must say exactly the same thing.
    at_tag = shadow_rebuild(loaded(paths), assignments=(
        f"algorithms.algorithm_version={SOURCE_REFERENCE_GATE_ALGORITHM_VERSION}",))
    before_tag = shadow_rebuild(loaded(paths), assignments=(
        f"algorithms.algorithm_version={PROOF_ROUTE_CHECK_ALGORITHM_VERSION}",))
    assert at_tag.live_database_unchanged and before_tag.live_database_unchanged
    assert _substantive(at_tag.learner_state_diff) == _substantive(before_tag.learner_state_diff)


def _strip_version(value):
    if isinstance(value, dict):
        return {key: _strip_version(inner) for key, inner in value.items() if key != "algorithm_version"}
    if isinstance(value, list):
        return [_strip_version(inner) for inner in value]
    return value


def _substantive(diff):
    """Each projection's changes, ignoring the version label every row is stamped with."""
    out = {}
    for name in ("mastery", "facet", "schedule"):
        changes = []
        for change in diff[name]["changes"]:
            before, after = _strip_version(change.get("before")), _strip_version(change.get("after"))
            if before != after:
                changes.append((repr(_strip_version(change.get("key"))), repr(before), repr(after)))
        out[name] = sorted(changes)
    return out


def test_the_projection_reads_the_recorded_status_on_replay(gated, monkeypatch):
    from learnloop.substrate import canonical_projection
    from learnloop.substrate.shadow_rebuild import shadow_rebuild

    paths, repository, spans = gated
    result = SEI.import_source_exercise(
        paths.root, repository, extraction_id="ext_text", span_ids=[spans["exercises"][2]], caller="learner",
        clients=service_clients(FakeServiceLLM(drop_cited_quote=True)))
    attempt = _attempt(paths, repository, result["practice_item_id"])
    seen = []
    real = canonical_projection.resolve_attempt_activity_policy

    def spy(**kwargs):
        policy = real(**kwargs)
        seen.append((kwargs.get("reference_status"), policy.eligible_for_certification))
        return policy

    monkeypatch.setattr(canonical_projection, "resolve_attempt_activity_policy", spy)
    shadow_rebuild(loaded(paths), assignments=(f"algorithms.algorithm_version={SOURCE_REFERENCE_GATE_ALGORITHM_VERSION}",))
    assert ("unverified", False) in seen
    assert _status(repository, attempt.attempt_id) == "unverified"


# -- A replacement grade is bound to the content it graded (spec-stage review F13) --------
#
# A regrade reads the item as it is now. After an edit, that is content no check
# has verified, so the new grade must not certify. The attempt's status may be
# lowered to ``unverified`` (never raised), in the transaction that publishes
# the grade and before its replay; a ``judgment_ledger`` row keeps the
# attempt-time status and the hash of the content the grade was read against.


def _regrade(paths, repository, attempt_id):
    from learnloop.attempts.regrade import regrade_attempt
    from tests.diagnosis_fakes import ReviewFakeClient
    from tests.split_live_helpers import ReadyRuntime

    regrade_attempt(loaded(paths), repository, repository.fetch_practice_attempt(attempt_id),
                    runtime=ReadyRuntime(), client=ReviewFakeClient(), grading_source="ai", clock=None)


def _bindings(repository, attempt_id):
    from learnloop.db.stores.source_service import REFERENCE_BINDING_TASK

    with closing(connect(repository.sqlite_path)) as connection:
        connection.row_factory = __import__("sqlite3").Row
        return [dict(row) for row in connection.execute(
            "SELECT * FROM judgment_ledger WHERE task=? AND left_id=? ORDER BY created_at, id",
            (REFERENCE_BINDING_TASK, attempt_id))]


def _verified_import(paths, repository, spans):
    result = SEI.import_source_exercise(
        paths.root, repository, extraction_id="ext_text", span_ids=[spans["exercises"][1]], caller="learner",
        clients=service_clients(FakeServiceLLM()))
    assert result["key_status"] == "book_solution"
    return result["practice_item_id"]


def _edit_key(paths, repository, item_id):
    from learnloop.content.authoring.item_authoring import edit_item

    edit_item(paths.root, repository, practice_item_id=item_id, expected_answer="x = 6", reason="test edit")
    with closing(connect(repository.sqlite_path)) as connection:
        assert reference_status_for_item(connection, loaded(paths).practice_items[item_id]) == "unverified"


def test_a_regrade_against_an_edited_unverified_key_never_certifies(gated):
    from learnloop.db.stores.source_service import reference_content_hash

    paths, repository, spans = gated
    item_id = _verified_import(paths, repository, spans)
    attempt = _attempt(paths, repository, item_id)
    assert _status(repository, attempt.attempt_id) == "verified"
    _edit_key(paths, repository, item_id)

    _regrade(paths, repository, attempt.attempt_id)

    assert _status(repository, attempt.attempt_id) == "unverified"
    with connect(repository.sqlite_path) as connection:
        rows = {row["attempt_id"]: row for row in load_canonical_observation_ledger(connection)}
    assert rows[attempt.attempt_id]["reference_status"] == "unverified"
    policy = resolve_attempt_activity_policy(attempt_type="independent_attempt",
                                             reference_status=rows[attempt.attempt_id]["reference_status"])
    assert policy.eligible_for_certification is False and policy.eligible_for_fsrs is True
    # The audit keeps what the attempt recorded and what the grade was read against.
    [binding] = _bindings(repository, attempt.attempt_id)
    content = reference_content_hash(loaded(paths).practice_items[item_id])
    assert (binding["verdict"], binding["judge"], binding["left_kind"]) == ("unverified", "verifier", "practice_attempt")
    assert (binding["right_kind"], binding["right_id"], binding["input_hash"]) == ("reference_content", content, content)
    assert "attempt_time_status=verified" in binding["rationale"]
    assert "key_status=changed_since_check" in binding["rationale"]


def test_the_regraded_grade_is_gated_live_and_on_rebuild(gated, monkeypatch):
    """The live replay inside the regrade and a rebuild both read ``unverified``."""
    from learnloop.substrate import canonical_projection
    from learnloop.substrate.shadow_rebuild import shadow_rebuild

    paths, repository, spans = gated
    item_id = _verified_import(paths, repository, spans)
    attempt = _attempt(paths, repository, item_id)
    _edit_key(paths, repository, item_id)
    seen = []
    real = canonical_projection.resolve_attempt_activity_policy

    def spy(**kwargs):
        policy = real(**kwargs)
        seen.append((kwargs.get("reference_status"), policy.eligible_for_certification))
        return policy

    monkeypatch.setattr(canonical_projection, "resolve_attempt_activity_policy", spy)
    _regrade(paths, repository, attempt.attempt_id)
    live = list(seen)
    assert ("unverified", False) in live and ("verified", True) not in live
    seen.clear()
    report = shadow_rebuild(loaded(paths), assignments=(
        f"algorithms.algorithm_version={SOURCE_REFERENCE_GATE_ALGORITHM_VERSION}",))
    assert report.live_database_unchanged
    assert ("unverified", False) in seen and ("verified", True) not in seen
    assert _status(repository, attempt.attempt_id) == "unverified"


def test_a_regrade_of_unchanged_verified_content_stays_verified(gated):
    paths, repository, spans = gated
    item_id = _verified_import(paths, repository, spans)
    attempt = _attempt(paths, repository, item_id)
    _regrade(paths, repository, attempt.attempt_id)
    assert _status(repository, attempt.attempt_id) == "verified"
    assert _bindings(repository, attempt.attempt_id) == []


def test_a_regrade_never_raises_an_attempts_status(gated):
    paths, repository, spans = gated
    result = SEI.import_source_exercise(
        paths.root, repository, extraction_id="ext_text", span_ids=[spans["exercises"][1]], caller="learner",
        clients=service_clients(FakeServiceLLM(drop_cited_quote=True)))
    item_id = result["practice_item_id"]
    attempt = _attempt(paths, repository, item_id)
    assert _status(repository, attempt.attempt_id) == "unverified"
    # The key of this exact content verifies later.
    from learnloop.db.stores.source_service import insert_key_check, reference_content_hash

    with repository.connection() as connection:
        insert_key_check(connection, id="rkc_later", practice_item_id=item_id,
                         content_hash=reference_content_hash(loaded(paths).practice_items[item_id]),
                         key_status="checked", rung="checked", trigger="verify",
                         started_at="2099-01-01T00:00:00Z", created_at="2099-01-01T00:00:01Z")
    with closing(connect(repository.sqlite_path)) as connection:
        assert reference_status_for_item(connection, loaded(paths).practice_items[item_id]) == "verified"
    _regrade(paths, repository, attempt.attempt_id)
    assert _status(repository, attempt.attempt_id) == "unverified"
    assert _bindings(repository, attempt.attempt_id) == []


def test_a_regrade_after_the_tag_binds_an_attempt_recorded_before_it(tmp_path, monkeypatch):
    """Recorded below the tag (``not_applicable``), regraded at it against an
    unverified key: the new grade is written under the gate, so it is gated."""
    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    set_algorithm_version(paths, PROOF_ROUTE_CHECK_ALGORITHM_VERSION)
    monkeypatch.setattr(pf_sandbox, "_sandbox_bwrap_path", lambda: None)
    item_id = _verified_import(paths, repository, spans)
    attempt = _attempt(paths, repository, item_id)
    assert _status(repository, attempt.attempt_id) == "not_applicable"
    set_algorithm_version(paths, SOURCE_REFERENCE_GATE_ALGORITHM_VERSION)
    _edit_key(paths, repository, item_id)
    _regrade(paths, repository, attempt.attempt_id)
    assert _status(repository, attempt.attempt_id) == "unverified"
    assert "attempt_time_status=not_applicable" in _bindings(repository, attempt.attempt_id)[0]["rationale"]


def test_below_the_tag_a_regrade_changes_nothing(tmp_path, monkeypatch):
    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    set_algorithm_version(paths, PROOF_ROUTE_CHECK_ALGORITHM_VERSION)
    monkeypatch.setattr(pf_sandbox, "_sandbox_bwrap_path", lambda: None)
    item_id = _verified_import(paths, repository, spans)
    attempt = _attempt(paths, repository, item_id)
    _edit_key(paths, repository, item_id)
    _regrade(paths, repository, attempt.attempt_id)
    assert _status(repository, attempt.attempt_id) == "not_applicable"
    assert _bindings(repository, attempt.attempt_id) == []


def test_a_regrade_of_an_item_that_is_not_an_import_changes_nothing(gated):
    paths, repository, _spans = gated
    attempt = _attempt(paths, repository, "pi_eigen_1", points=4, criterion="correct")
    _regrade(paths, repository, attempt.attempt_id)
    assert _status(repository, attempt.attempt_id) == "not_applicable"
    assert _bindings(repository, attempt.attempt_id) == []


@pytest.mark.parametrize("source,lowered", [("deterministic_key", True), ("human_owner", False)])
def test_a_key_based_adjudication_is_bound_like_a_regrade(gated, source, lowered):
    """``deterministic_key`` is a verdict against the stored key; a human
    adjudicator's verdict is not read from the key, so it is not bound."""
    from learnloop.attempts.grade_resolution import append_adjudication_evidence_revision

    paths, repository, spans = gated
    item_id = _verified_import(paths, repository, spans)
    attempt = _attempt(paths, repository, item_id, points=0)
    _edit_key(paths, repository, item_id)
    revision = append_adjudication_evidence_revision(
        repository, attempt_id=attempt.attempt_id, resolved_fraction=1.0, adjudication_id="adj_test",
        adjudicator_source=source, rationale="test", vault=loaded(paths))
    assert revision["status"] == "revised"
    assert _status(repository, attempt.attempt_id) == ("unverified" if lowered else "verified")
    assert len(_bindings(repository, attempt.attempt_id)) == (1 if lowered else 0)
