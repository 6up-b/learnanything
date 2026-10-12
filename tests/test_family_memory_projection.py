"""Integrated PF-a projection tests; requires the foundation's migration 168.

Rows come from the learner-field canonical outcome view (``load_attempt_rows``
with ``retrieval=True``), the same rows the offline harness replays.
"""
from datetime import timedelta
import json

import pytest

from learnloop.db.repositories import Repository
from learnloop.field.outcomes import load_attempt_rows
from learnloop.substrate.family_memory import PROJECTION_LEGACY_FALLBACK, rebuild_family_memory
from learnloop.vault.loader import load_vault
from tests.helpers import NOW, create_basic_vault


def _attempt(repo, n, **overrides):
    """A legacy-path attempt plus its criterion grading evidence."""
    values = {
        "id": f"attempt-{n}", "practice_item_id": "pi_svd_define_001",
        "learning_object_id": "lo_svd_definition", "practice_mode": "define",
        "attempt_type": "independent_attempt", "rubric_score": 4,
        "created_at": (NOW+timedelta(days=n)).isoformat(),
        "learner_answer_md": "PRIVATE LEARNER RESPONSE",
    }
    values.update(overrides)
    points = values.pop("points", None)
    repo.insert_practice_attempt(values)
    if points is None:
        points = 0 if values["attempt_type"] == "dont_know" else values["rubric_score"]
    with repo.connection() as connection:
        connection.execute(
            """INSERT INTO grading_evidence
               (id, attempt_id, criterion_id, points_awarded, grader_tier, created_at, grading_revision)
               VALUES (?, ?, 'correctness', ?, 1, ?, 1)""",
            (f"evidence-{n}", values["id"], points, values["created_at"]))


def _vault(tmp_path):
    paths = create_basic_vault(tmp_path/"vault")
    return load_vault(paths.root), Repository(paths.sqlite_path)


def _family(vault):
    from learnloop.vault.models import ActivityFamily

    family = ActivityFamily(
        id="family-test", learning_object_id="lo_svd_definition",
        idea_statement="Definition of SVD", retrieval_target="Recall the decomposition",
        created_at=NOW.isoformat(), updated_at=NOW.isoformat())
    vault.activity_families[family.id] = family
    item = vault.practice_items["pi_svd_define_001"]
    vault.practice_items[item.id] = item.model_copy(update={
        "family_id": family.id, "variant_relation": "same_target"})
    return family


def _rows(vault, repo, legacy_fallback=PROJECTION_LEGACY_FALLBACK):
    with repo.connection() as connection:
        return load_attempt_rows(connection, vault, legacy_fallback=legacy_fallback, retrieval=True)


def _rebuild(vault, repo):
    return rebuild_family_memory(vault, repo, lambda: _rows(vault, repo))


def test_no_family_rebuild_does_not_touch_other_state(tmp_path):
    vault, repo = _vault(tmp_path)
    _attempt(repo, 0)
    before = repo.list_all_attempts()
    assert rebuild_family_memory(
        vault, repo, lambda: pytest.fail("no-family rebuild need not read outcomes"),
    )["families"] == 0
    assert repo.list_all_attempts() == before


def test_projection_deterministic_cold_only_no_models_and_undo(tmp_path, monkeypatch):
    import learnloop.ai.client as clients

    vault, repo = _vault(tmp_path)
    _family(vault)
    for n, overrides in enumerate([
        {}, {"hints_used": 1}, {"primed": True}, {"attempt_type": "hinted_attempt"},
        {"attempt_type": "diagnostic_probe"}, {"attempt_type": "teach_back"},
        {"attempt_type": "dont_know", "rubric_score": 0}, {},
    ]):
        _attempt(repo, n, **overrides)
    repo.insert_reveal_event({
        "practice_item_id": "sibling", "learning_object_id": "lo_svd_definition",
        "source_kind": "tutor_answer", "amount": 1,
        "created_at": (NOW+timedelta(days=6, hours=12)).isoformat()})

    def forbidden(*args, **kwargs):
        pytest.fail("rebuild must not call models, generators, or live scheduling caches")

    monkeypatch.setattr(clients, "make_ai_provider_client", forbidden)
    monkeypatch.setattr(clients, "make_ai_provider_client_from_profile", forbidden)
    monkeypatch.setattr(repo, "practice_item_state", forbidden)
    monkeypatch.setattr(repo, "activity_card_state", forbidden)
    original = repo.list_all_attempts()
    first = _rebuild(vault, repo)
    with repo.connection() as connection:
        state = [tuple(r) for r in connection.execute("SELECT * FROM family_memory_state")]
    assert first["reviews"] == 2
    assert first["skipped"] == {"not_cold": 3, "not_graded_retrieval": 3}
    assert first == _rebuild(vault, repo)
    with repo.connection() as connection:
        assert state == [tuple(r) for r in connection.execute("SELECT * FROM family_memory_state")]
    assert repo.list_all_attempts() == original
    item = vault.practice_items["pi_svd_define_001"]
    vault.practice_items[item.id] = item.model_copy(update={"family_id": None, "variant_relation": None})
    assert _rebuild(vault, repo)["families"] == 0
    with repo.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM family_memory_state").fetchone()[0] == 0


@pytest.mark.parametrize("relation,count", [("same_target", 1), ("isomorph", 1), ("near", 0), ("far", 0)])
def test_projection_relation_gate(tmp_path, relation, count):
    vault, repo = _vault(tmp_path)
    _family(vault)
    item = vault.practice_items["pi_svd_define_001"]
    vault.practice_items[item.id] = item.model_copy(update={"variant_relation": relation})
    _attempt(repo, 0)
    assert _rebuild(vault, repo)["reviews"] == count


@pytest.mark.durability
def test_family_projection_durable_repeat(tmp_path):
    vault, repo = _vault(tmp_path)
    _family(vault)
    _attempt(repo, 0)
    first = _rebuild(vault, repo)
    attached = Repository.attach(repo.sqlite_path)
    assert first == rebuild_family_memory(vault, attached, lambda: _rows(vault, attached))


def test_registry_has_exactly_one_owner_on_the_outcome_view():
    from learnloop.substrate.rebuild_orchestrator import (
        DERIVED_STATE_REPLAYERS, derived_table_owners, validate_replayer_registry,
    )

    validate_replayer_registry()
    assert derived_table_owners()["family_memory_state"] == ("family_memory",)
    spec = next(r for r in DERIVED_STATE_REPLAYERS if r.name == "family_memory")
    assert spec.depends_on == ("learning_state",)


def test_dont_know_is_an_observed_failure_review(tmp_path):
    vault, repo = _vault(tmp_path)
    _attempt(repo, 0, attempt_type="dont_know", rubric_score=0)
    row, = _rows(vault, repo)
    assert row.outcome == 0
    assert row.fsrs_rating == 1  # FSRS Again
    assert row.memory_eligible
    # Ability mass is the canonical view's configured dont_know mass.
    assert row.effective_mass == pytest.approx(
        vault.config.evidence.attempt_types["dont_know"].evidence_mass)


def test_legacy_revision_fallback_is_explicit_and_reveal_is_past_only(tmp_path):
    vault, repo = _vault(tmp_path)
    _attempt(repo, 0)
    _attempt(repo, 2)
    repo.insert_reveal_event({
        "practice_item_id": "sibling", "learning_object_id": "lo_svd_definition",
        "source_kind": "tutor_answer", "amount": 1,
        "created_at": (NOW+timedelta(days=1)).isoformat()})
    strict = _rows(vault, repo, legacy_fallback="exclude")
    assert [r.revision_status for r in strict] == ["excluded", "excluded"]
    assert not any(r.memory_scored for r in strict)
    reconstructed = _rows(vault, repo, legacy_fallback="current_content")
    assert [r.revision_status for r in reconstructed] == ["reconstructed_current"] * 2
    assert [r.retrieval_cold for r in reconstructed] == [True, False]


def test_legacy_calibration_is_not_invented_for_ability_arms(tmp_path):
    vault, repo = _vault(tmp_path)
    p0 = vault.config.algorithms.model_copy(update={"algorithm_version": "mvp-0.8"})
    vault.config = vault.config.model_copy(update={"algorithms": p0})
    _attempt(repo, 0)
    row, = _rows(vault, repo)
    # A P0 vault without an interpretation has no ability mass, but the graded
    # cold retrieval is still an FSRS review for the memory arms.
    assert row.effective_mass == 0
    assert row.memory_eligible


def test_old_reveal_does_not_permanently_veto_spaced_reviews(tmp_path):
    vault, repo = _vault(tmp_path)
    _family(vault)
    for day in (0, 2, 7):
        _attempt(repo, day)
    repo.insert_reveal_event({
        "practice_item_id": "sibling", "learning_object_id": "lo_svd_definition",
        "source_kind": "tutor_answer", "amount": .1,
        "created_at": (NOW+timedelta(days=1)).isoformat()})
    assert [row.retrieval_cold for row in _rows(vault, repo)] == [True, False, True]
    assert _rebuild(vault, repo)["reviews"] == 2


@pytest.mark.parametrize("status,expected", [("pass", True), ("fail", False), ("unknown", False)])
def test_receipt_owns_measurement_window_and_unassisted_claim(tmp_path, status, expected):
    vault, repo = _vault(tmp_path)
    _attempt(repo, 0)
    _attempt(repo, 7)
    # Before the explicitly recorded cold measurement window: not a permanent
    # veto. The receipt can still reject coldness for another recorded channel.
    repo.insert_reveal_event({
        "practice_item_id": "sibling", "learning_object_id": "lo_svd_definition",
        "source_kind": "tutor_answer", "amount": 1,
        "created_at": (NOW+timedelta(days=1)).isoformat()})
    with repo.connection() as connection:
        connection.execute(
            """INSERT INTO coldness_receipts
               (id, lane, stage, cold_attempt_id, dimensions_json, derived_json,
                telemetry_coverage_json, receipt_version, created_at)
               VALUES ('receipt', 'repair_cold_retry', 'final', 'attempt-7',
                       ?, '{}', ?, 'test', ?)""",
            (json.dumps({"unassisted": {"status": status},
                         "answer_leakage": {"status": "pass"}}),
             json.dumps({"interval": {"from": (NOW+timedelta(days=2)).isoformat(),
                                       "to": (NOW+timedelta(days=7)).isoformat()}}),
             (NOW+timedelta(days=7)).isoformat()))
    assert _rows(vault, repo)[-1].retrieval_cold is expected


def test_regrade_uses_the_latest_surviving_epoch_not_an_exclusion(tmp_path):
    vault, repo = _vault(tmp_path)
    _attempt(repo, 0)
    at = (NOW + timedelta(days=3)).isoformat()
    with repo.connection() as connection:
        connection.execute("UPDATE grading_evidence SET superseded_at=? WHERE id='evidence-0'", (at,))
        connection.execute(
            """INSERT INTO grading_evidence
               (id, attempt_id, criterion_id, points_awarded, grader_tier, created_at, grading_revision)
               VALUES ('evidence-0b', 'attempt-0', 'correctness', 1, 1, ?, 2)""", (at,))
    row, = _rows(vault, repo)
    assert row.outcome == .25 and row.memory_scored


def test_reveal_read_failure_is_not_reported_as_cold(tmp_path, monkeypatch):
    from learnloop.attempts.reveal_ledger import production_admissibility

    vault, repo = _vault(tmp_path)
    _attempt(repo, 0)

    def broken(self, **kwargs):
        raise RuntimeError("ledger unavailable")

    # Existing live callers retain best-effort behavior.
    monkeypatch.setattr(Repository, "reveal_events_for_target", broken)
    assert production_admissibility(
        repo, practice_item_id="pi_svd_define_001", produced_at=NOW.isoformat()).admissible
    with pytest.raises(RuntimeError, match="ledger unavailable"):
        _rows(vault, repo)


@pytest.mark.parametrize("score,points,rating", [(1, 2, 2), (3, 3.5, 3), (4, 4, 4)])
def test_fsrs_rating_uses_capped_rounded_grade_not_continuous_fraction(tmp_path, score, points, rating):
    vault, repo = _vault(tmp_path)
    _attempt(repo, 0, rubric_score=score, points=points)
    row, = _rows(vault, repo)
    assert row.outcome == points / 4
    assert row.fsrs_rating == rating


def test_family_grouping_is_current_authored_and_retrospective(tmp_path):
    vault, repo = _vault(tmp_path)
    _attempt(repo, 0)
    assert _rows(vault, repo)[0].features.family_id is None
    _family(vault)
    row, = _rows(vault, repo)
    assert (row.features.family_id, row.features.variant_relation) == ("family-test", "same_target")
    # An item pointing at a family file that does not exist stays unfamilied.
    item = vault.practice_items["pi_svd_define_001"]
    vault.practice_items[item.id] = item.model_copy(update={"family_id": "missing"})
    assert _rows(vault, repo)[0].features.family_id is None


def test_rebuild_and_evaluation_fold_the_same_leak_aware_rows(tmp_path):
    """Review F7: question-only leak telemetry voids coldness in both folds.

    A linked ``leak_suspected`` tutor question with no reveal-ledger row (a
    historical vault, or a failed best-effort reveal write) makes the attempt
    non-cold in evaluation; the stored projection must fold the same history.
    """
    from learnloop.cli.field import _replay_inputs
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

    vault, repo = _vault(tmp_path)
    _family(vault)
    for n in range(3):
        _attempt(repo, n)
    repo.insert_question_event({
        "id": "leaky-question", "context": "practice", "practice_item_id": "pi_svd_define_001",
        "attempt_id": "attempt-1", "question_md": "Is it U Sigma V transpose?",
        "question_type": "verification", "leak_suspected": True,
        "created_at": (NOW+timedelta(days=1)-timedelta(minutes=5)).isoformat(),
    })
    inputs = _replay_inputs(vault, legacy_fallback=PROJECTION_LEGACY_FALLBACK)
    evaluated = [r.attempt_id for r in inputs["attempts"] if r.memory_eligible]
    assert evaluated == ["attempt-0", "attempt-2"]
    rebuild_all_derived_state(vault, repo)
    with repo.connection() as connection:
        reviews = connection.execute(
            "SELECT review_count FROM family_memory_state WHERE family_id='family-test'"
        ).fetchone()[0]
    assert reviews == len(evaluated)
