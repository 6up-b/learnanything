"""The freeze before the lesson-weight refit, and grade-time capture on a replacement grade."""

import json
from datetime import UTC, datetime, timedelta

import pytest

from learnloop.algorithm_versions import LESSON_WEIGHT_CURVES_ALGORITHM_VERSION as TAG
from learnloop.clock import FrozenClock
from learnloop.db.stores.grade_curves import current_curve
from learnloop.learner import lesson_weight as LW
from learnloop.ops import upgrades
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item
from tests.regrade_contract_replay_helpers import ITEM, _regrade, _self_graded_apply
from tests.regrade_contract_successor_helpers import _vault
from tests.grade_curves_migration_helpers import forget_captures
from tests.teacher_fakes import build_teacher_vault
from tests.teacher_te1_review_fixes_helpers import _cold, _lesson_with_check, _rows

T = datetime(2026, 11, 1, 9, tzinfo=UTC)
CURVES = "SELECT * FROM attempt_grade_curves ORDER BY attempt_id, epoch_key"


def _projection(repository):
    return (
        _rows(repository, "SELECT * FROM lesson_weight_state ORDER BY family"),
        _rows(repository, "SELECT seq, kind, lesson_check_id, resolving_attempt_id, learning_object_id, at, detail_json "
                          "FROM lesson_weight_trace ORDER BY seq"),
    )


@pytest.mark.parametrize("missing", [True, False])
def test_upgrade_freezes_once_then_refits_and_rebuilds_twice(tmp_path, monkeypatch, missing):
    # The production row: the lesson-weight curves follow the probe router.
    production = next(link for link in upgrades.UPGRADES if link.tag == TAG)
    assert production.predecessor == "mvp-0.70"
    link = production
    paths, repository = build_teacher_vault(tmp_path / "vault", version=link.predecessor)
    _lesson_with_check(paths, repository, at=T, retained=0.8)
    middle = _cold(paths, repository, "pi_eig_1", T + timedelta(days=1), primed=True)
    outcome = _cold(paths, repository, "pi_eig_2", T + timedelta(days=2))
    _lesson_with_check(paths, repository, at=T + timedelta(days=3))
    vault = load_vault(paths.root)
    receipts = _rows(repository, "SELECT * FROM lesson_checks ORDER BY id")
    # The history an owner's vault holds: written by code that recorded no curve (every grade records one now).
    forget_captures(repository)
    assert not _rows(repository, CURVES)
    # The predecessor reads authored parameters despite this post-grade edit.
    old = LW._state_rows(LW.replay_state(vault, repository))
    data = vault.practice_items["pi_eig_2"].model_dump(mode="json")
    data["difficulty"] = 0.93
    upsert_practice_item(paths.root, data)
    assert LW._state_rows(LW.replay_state(load_vault(paths.root), repository)) != old
    if missing:
        with repository.connection() as connection:
            connection.execute("DELETE FROM attempt_surprise WHERE attempt_id = ?", (middle.attempt_id,))
            connection.execute("UPDATE attempt_surprise SET predicted_score_dist_json = ? WHERE attempt_id = ?",
                               ('{"a":true,"b":0}', outcome.attempt_id))
            connection.commit()
    predecessor = _projection(repository)
    def fail_after_clear(vault, repo, **kwargs):
        with repo.connection() as connection:
            connection.execute("DELETE FROM attempt_surprise")
        raise RuntimeError("interrupted after clear")

    with monkeypatch.context() as patch:
        patch.setattr(upgrades, "rebuild_all_derived_state", fail_after_clear)
        with pytest.raises(RuntimeError, match="interrupted after clear"):
            upgrades.upgrade(paths.root, to=TAG, links=[link])
    assert load_vault(paths.root).config.algorithms.algorithm_version == link.predecessor
    assert _projection(repository) == predecessor
    first = _rows(repository, CURVES)
    assert len(first) == len(receipts) + 2
    absent = {middle.attempt_id, outcome.attempt_id} if missing else set()
    assert {r[0] for r in first if r[-1] == "missing_at_upgrade"} == absent
    attempts = {r[0] for r in _rows(repository, "SELECT id FROM practice_attempts")}
    assert {r[0] for r in first if r[-1] == "reconstructed_at_upgrade"} == attempts - absent
    old_fit = LW.replay_state(load_vault(paths.root), repository)
    assert all("resolving_input" not in entry["detail"] for entry in old_fit.trace)
    rebuild_all_derived_state(load_vault(paths.root), repository)
    assert _rows(repository, CURVES) == first
    # Even a valid replacement in the predecessor projection cannot repair the first snapshot.
    with repository.connection() as connection:
        connection.execute("UPDATE attempt_surprise SET predicted_score_dist_json = ?", ('{"a":2,"b":1}',))
        connection.commit()

    assert upgrades.upgrade(paths.root, to=TAG, links=[link]).upgraded
    vault = load_vault(paths.root)
    expected = _projection(repository)
    assert {row[0].split(":")[0] for row in expected[0]} == {"weight", "pool"}
    details = {r[1]: json.loads(r[-1]) for r in expected[1] if r[3] == outcome.attempt_id}
    weight, pool = details["weight_update"], details["pool_update"]
    assert weight["trajectory_inputs"][-1]["attempt_id"] == middle.attempt_id
    assert pool["resolving_input"] == weight["resolving_input"]
    if missing:
        assert weight["likelihood"] == "first_order" and weight["resolving_fallback"] == "check_sensitivity"
        assert [c["provenance"] for c in weight["trajectory_inputs"]] == ["reconstructed_at_upgrade", "missing_at_upgrade"]
        assert pool["resolving_fallback"] == "forecast_p_a" and pool["p_a"] == pool["p_a_at_forecast"]
        assert pool["resolving_input"]["provenance"] == "missing_at_upgrade"
    else:
        assert weight["likelihood"] == "recorded_trajectory"
        assert all(c["provenance"] == "reconstructed_at_upgrade" for c in weight["trajectory_inputs"])
        endpoint = next(r for r in first if r[0] == outcome.attempt_id)
        assert (pool["resolving_input"]["item_a"], pool["resolving_input"]["item_b"]) == endpoint[3:5]
        assert expected[0] != predecessor[0]
    for _ in range(2):
        with repository.connection() as connection:
            connection.execute("DELETE FROM attempt_surprise")
            connection.commit()
        rebuild_all_derived_state(vault, repository, clock=FrozenClock(T + timedelta(days=5)))
        assert _projection(repository) == expected
        assert _rows(repository, CURVES) == first
        assert _rows(repository, "SELECT * FROM lesson_checks ORDER BY id") == receipts
    from learnloop.substrate.shadow_rebuild import shadow_rebuild

    shadow = shadow_rebuild(vault, observe=lambda _vault, repo: _projection(repo))
    assert shadow.live_database_unchanged
    assert shadow.observed_before == shadow.observed_after == expected
    assert _rows(repository, "PRAGMA foreign_key_check") == []
    assert _rows(repository, "PRAGMA integrity_check") == [("ok",)]


def test_regrade_adds_a_curve_for_only_the_new_epoch(tmp_path):
    paths, vault, repository = _vault(tmp_path, version=TAG)
    seeded = set(_rows(repository, CURVES))
    for i in range(2):
        _self_graded_apply(vault, repository, ITEM, {"setup": 1, "result": 1}, attempt_id=f"att_{i}",
                           when=T + timedelta(days=i))
    initial = _rows(repository, CURVES)
    added = sorted(set(initial) - seeded)
    assert [(row[0], row[1], row[2]) for row in added] == [("att_0", "revision:0", 0), ("att_1", "revision:0", 0)]
    data = vault.practice_items[ITEM].model_dump(mode="json")
    data["difficulty"] = 0.97
    upsert_practice_item(paths.root, data)
    vault = load_vault(paths.root)
    _regrade(vault, repository, "att_0", {"setup": 2, "result": 2}, when=T + timedelta(days=2))
    after = _rows(repository, CURVES)
    assert len(after) == len(initial) + 1 and set(initial) < set(after)
    with repository.connection() as connection:
        curve = current_curve(connection, "att_0")
    assert (curve.epoch_key, curve.grading_revision, curve.provenance, curve.algorithm_version) == (
        "revision:1", 1, "graded", TAG)
    dist = repository.latest_attempt_surprise("att_0")["predicted_score_dist"]
    assert (curve.item_a, curve.item_b) == (dist["a"], dist["b"])
    assert curve.item_b != added[0][4]
    rebuild_all_derived_state(vault, repository)
    assert _rows(repository, CURVES) == after


def test_upgrade_labels_superseded_epochs_and_keeps_a_legacy_stamp(tmp_path):
    from learnloop.db.stores.grade_curves import snapshot_grade_curves
    from tests.regrade_contract_successor_helpers import as_graded_before_contracts

    paths, vault, repository = _vault(tmp_path, version="mvp-0.68")
    production = next(link for link in upgrades.UPGRADES if link.tag == TAG)
    refused = upgrades.upgrade(paths.root, to=TAG, links=[production])
    assert not refused.upgraded and load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.68"
    _self_graded_apply(vault, repository, ITEM, {"setup": 1, "result": 1}, attempt_id="att_old", when=T)
    as_graded_before_contracts(repository, "att_old")
    _regrade(vault, repository, "att_old", {"setup": 2, "result": 2}, when=T + timedelta(days=1))
    _self_graded_apply(vault, repository, ITEM, {"setup": 2, "result": 2}, attempt_id="att_legacy", when=T)
    as_graded_before_contracts(repository, "att_legacy")
    forget_captures(repository)
    with repository.atomic(), repository.connection() as connection:
        assert snapshot_grade_curves(connection, vault.config.algorithms.algorithm_version)
        assert not snapshot_grade_curves(connection, vault.config.algorithms.algorithm_version)
        current = current_curve(connection, "att_old")
        legacy = current_curve(connection, "att_legacy")
    earlier, = _rows(repository, "SELECT epoch_key, grading_revision, item_a, item_b, provenance "
                      "FROM attempt_grade_curves WHERE attempt_id = 'att_old' AND grading_revision IS NULL")
    assert earlier == (legacy.epoch_key, None, None, None, "missing_at_upgrade")
    assert legacy.epoch_key.startswith("legacy:") and legacy.provenance == "reconstructed_at_upgrade"
    assert current.epoch_key == "revision:1" and current.provenance == "reconstructed_at_upgrade"


def test_pool_only_endpoint_uses_its_snapshot_and_reports_an_unapplied_replacement(tmp_path):
    from learnloop.attempts.grade_resolution import append_adjudication_evidence_revision
    from learnloop.teacher import service
    from tests.teacher_fakes import TeacherFake, clients, landed_and_close_turn, plan_turn

    production = next(link for link in upgrades.UPGRADES if link.tag == TAG)
    link = upgrades.Link(TAG, production.activate)
    paths, repository = build_teacher_vault(tmp_path / "vault", version=link.predecessor)
    vault = load_vault(paths.root)
    fake = TeacherFake([plan_turn, landed_and_close_turn()])
    lesson = service.open_lesson(vault, repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                                 clients=clients(fake), clock=FrozenClock(T))
    service.take_turn(vault, repository, lesson_id=lesson["lesson_id"], action="reply", payload={"text": "go"},
                      clients=clients(fake), clock=FrozenClock(T + timedelta(minutes=1)))
    outcome = _cold(paths, repository, "pi_eig_2", T + timedelta(days=1))
    assert not _rows(repository, "SELECT id FROM lesson_checks")
    receipts = _rows(repository, "SELECT * FROM lesson_receipts ORDER BY lesson_id")
    assert len(receipts) == 1
    forget_captures(repository)
    assert upgrades.upgrade(paths.root, to=TAG, links=[link]).upgraded
    vault = load_vault(paths.root)
    pool, = LW.replay_state(vault, repository).trace
    assert pool["kind"] == "pool_update" and pool["resolving_attempt_id"] == outcome.attempt_id
    assert pool["detail"]["resolving_input"]["provenance"] == "reconstructed_at_upgrade"
    assert _rows(repository, "SELECT * FROM lesson_receipts ORDER BY lesson_id") == receipts

    # This evidence-only writer has not applied the replacement to mastery. Neither the old
    # epoch nor the still-present surprise row may impersonate a grade-time capture for it.
    revision = append_adjudication_evidence_revision(
        repository, attempt_id=outcome.attempt_id, resolved_fraction=0, adjudication_id="adj_pending",
        adjudicator_source="human", rationale=None, vault=vault)
    assert revision["status"] == "revised"
    pool, = LW.replay_state(vault, repository).trace
    detail = pool["detail"]
    assert detail["resolving_input"]["epoch_key"] == "revision:1"
    assert detail["resolving_input"]["provenance"] == "missing_capture"
    assert detail["resolving_fallback"] == "forecast_p_a" and detail["p_a"] == detail["p_a_at_forecast"]
