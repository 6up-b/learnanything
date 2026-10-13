"""S1 (G19): certification follows the answer key (C3, mvp-0.15)."""
from __future__ import annotations

from contextlib import closing

import pytest

from learnloop.algorithm_versions import (
    DAILY_PLAN_ALGORITHM_VERSION, LATEST_ALGORITHM_VERSION, SOURCE_REFERENCE_GATE_ALGORITHM_VERSION,
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


def test_the_gate_is_a_successor_after_the_plan():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(DAILY_PLAN_ALGORITHM_VERSION) + 1] == SOURCE_REFERENCE_GATE_ALGORITHM_VERSION
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
    set_algorithm_version(paths, DAILY_PLAN_ALGORITHM_VERSION)
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
    """Never retroactive: with every recorded status kept, mvp-0.15 projects what mvp-0.14 does."""
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
        f"algorithms.algorithm_version={DAILY_PLAN_ALGORITHM_VERSION}",))
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
