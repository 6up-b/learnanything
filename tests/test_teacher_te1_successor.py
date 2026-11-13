"""Teacher TE1's successor (spec_teacher_v1 §18.3): the tag, the upgrade, the kill switch's parity,
the shadow rebuild and the desktop RPCs. Every model is a fake; no network.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from tests.teacher_fakes import pin_default_tag
from learnloop.algorithm_versions import TEACHER_ALGORITHM_VERSION
from learnloop.algorithm_versions import (
    DELIVERABLE_PLAN_ALGORITHM_VERSION,
    LATEST_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
    TEACHER_ALGORITHM_VERSION,
    TEACHER_VERSIONS,
)
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from tests.teacher_fakes import (
    TeacherFake,
    build_teacher_vault,
    check_turn,
    clients,
    landed_and_close_turn,
    plan_turn,
)
from tests.teacher_te1_successor_helpers import _Ctx

T0 = datetime(2026, 11, 1, 9, 0, tzinfo=UTC)
TAG = TEACHER_ALGORITHM_VERSION


def _rows(repository, sql, params=()):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(sql, params).fetchall()]


def test_the_tag_is_the_chains_last_link_after_curriculum_c1():
    # Follow-ups Nov 2's mvp-0.42 and teacher TE1b's mvp-0.43 (the latest) follow it (and keep it).
    assert SUCCESSOR_CHAIN[-20:] == (DELIVERABLE_PLAN_ALGORITHM_VERSION, TAG, "mvp-0.42", "mvp-0.43", "mvp-0.44", "mvp-0.45", "mvp-0.46", "mvp-0.47", "mvp-0.48", "mvp-0.49", "mvp-0.50", "mvp-0.51", "mvp-0.52", "mvp-0.53", "mvp-0.54", "mvp-0.55", "mvp-0.56", "mvp-0.57", "mvp-0.58", LATEST_ALGORITHM_VERSION) == (
        "mvp-0.40", "mvp-0.41", "mvp-0.42", "mvp-0.43", "mvp-0.44", "mvp-0.45", "mvp-0.46", "mvp-0.47", "mvp-0.48", "mvp-0.49", "mvp-0.50", "mvp-0.51", "mvp-0.52", "mvp-0.53", "mvp-0.54", "mvp-0.55", "mvp-0.56", "mvp-0.57", "mvp-0.58", "mvp-0.59")
    assert TEACHER_VERSIONS == frozenset({TAG, "mvp-0.42", "mvp-0.43", "mvp-0.44", "mvp-0.45", "mvp-0.46", "mvp-0.47", "mvp-0.48", "mvp-0.49", "mvp-0.50", "mvp-0.51", "mvp-0.52", "mvp-0.53", "mvp-0.54", "mvp-0.55", "mvp-0.56", "mvp-0.57", "mvp-0.58", "mvp-0.59"})


def _practice(paths, repository, at):
    """A fixed run of ordinary practice: no lesson anywhere."""

    vault = load_vault(paths.root)
    for offset, (item_id, points, tap) in enumerate([("pi_eig_1", 4, 5), ("pi_det_1", 0, 4), ("pi_eig_2", 2, 3)]):
        complete_self_graded_attempt(
            vault, repository,
            AttemptDraft(practice_item_id=item_id, learner_answer_md="an answer", attempt_type="independent_attempt",
                         answer_confidence=tap),
            SelfGradeInput(criterion_points={"correctness": points}, confidence=tap),
            clock=FrozenClock(at + timedelta(hours=offset)))


def _state(repository):
    """Every learner-state table's rows, minus surrogate ids and the version label (which names the
    vault's tag, the one thing that differs below it)."""

    tables = ("learning_object_mastery", "facet_recall_state", "practice_item_state", "reveal_events",
              "lesson_weight_state", "confidence_calibration_state", "lessons")
    out = {}
    for table in tables:
        with repository.connection() as connection:
            cursor = connection.execute(f"SELECT * FROM {table} ORDER BY 1")
            names = [d[0] for d in cursor.description]
            rows = cursor.fetchall()
        keep = [i for i, name in enumerate(names) if name not in ("algorithm_version", "id")]
        out[table] = [tuple(row[i] for i in keep) for row in rows]
    return out


@pytest.mark.parametrize("setting", ["teacher_off", "below_tag"])
def test_with_the_switch_off_or_below_the_tag_practice_is_byte_identical(tmp_path, setting, monkeypatch):
    pin_default_tag(monkeypatch, TEACHER_ALGORITHM_VERSION)  # the first teacher tag's lesson is the subject
    from tests.ux_phase1_support import set_config

    on_paths, on_repository = build_teacher_vault(tmp_path / "on")
    if setting == "teacher_off":
        off_paths, off_repository = build_teacher_vault(tmp_path / "off")
        set_config(off_paths.root, {("teacher", "enabled"): False})
    else:
        off_paths, off_repository = build_teacher_vault(tmp_path / "off", version=DELIVERABLE_PLAN_ALGORITHM_VERSION)
    _practice(on_paths, on_repository, T0)
    _practice(off_paths, off_repository, T0)
    on, off = _state(on_repository), _state(off_repository)
    assert on["learning_object_mastery"] == off["learning_object_mastery"]
    assert on["facet_recall_state"] == off["facet_recall_state"]
    assert on["practice_item_state"] == off["practice_item_state"]
    assert on["lesson_weight_state"] == off["lesson_weight_state"] == []
    assert on["lessons"] == off["lessons"] == []


def _whole_lesson(paths, repository):
    fake = TeacherFake([plan_turn, check_turn()])
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object",
                         learning_object_ids=["lo_eigen"], clients=clients(fake), clock=FrozenClock(T0))
    S.take_turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="reply", payload={"text": "go"},
           clients=clients(fake), clock=FrozenClock(T0 + timedelta(minutes=1)))
    fake.turns = [landed_and_close_turn()]
    S.take_turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="answer_check",
           payload={"answer": "det(A - tI) = 0", "tap": 4}, clients=clients(fake),
           clock=FrozenClock(T0 + timedelta(minutes=2)))
    return view["lesson_id"]


def test_a_shadow_rebuild_after_a_lesson_has_zero_projection_deltas(tmp_path):
    from learnloop.substrate.shadow_rebuild import shadow_rebuild

    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

    paths, repository = build_teacher_vault(tmp_path / "vault")
    # The fixture's LOs were written as files: a live rebuild first gives them their cold rows, as
    # bootstrap would, so the shadow compares the lesson's effects only.
    rebuild_all_derived_state(load_vault(paths.root), repository)
    _whole_lesson(paths, repository)
    complete_self_graded_attempt(
        load_vault(paths.root), repository,
        AttemptDraft(practice_item_id="pi_eig_3", learner_answer_md="cold", attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=4), clock=FrozenClock(T0 + timedelta(days=3)))
    result = shadow_rebuild(load_vault(paths.root))
    assert result.live_database_unchanged
    assert result.learner_state_diff["summary"] == {"mastery": 0, "facet": 0, "schedule": 0}


def test_the_whole_rebuild_owns_the_lesson_weight_tables_and_reproduces_them(tmp_path):
    from learnloop.learner import lesson_weight as LW
    from learnloop.substrate.rebuild_orchestrator import derived_table_owners, rebuild_all_derived_state

    owners = derived_table_owners()
    for table in LW.DERIVED_TABLES:
        assert owners[table] == ("lesson_weight",)
    paths, repository = build_teacher_vault(tmp_path / "vault")
    _whole_lesson(paths, repository)
    snapshot = {table: _rows(repository, f"SELECT * FROM {table} ORDER BY 1") for table in LW.DERIVED_TABLES}
    rebuild_all_derived_state(load_vault(paths.root), repository)
    again = {table: _rows(repository, f"SELECT * FROM {table} ORDER BY 1") for table in LW.DERIVED_TABLES}
    assert again == snapshot
    receipts = _rows(repository, "SELECT COUNT(*) FROM lesson_receipts")
    assert receipts == [(1,)]  # RECEIPT rows are never cleared by replay


# --- the desktop RPCs ------------------------------------------------------------------------------


def test_lesson_turn_runs_a_lesson_and_lesson_view_resumes_it(tmp_path, monkeypatch):
    from learnloop_sidecar.handlers import lesson as H

    paths, repository = build_teacher_vault(tmp_path / "vault")
    fake = TeacherFake([plan_turn, check_turn()])
    monkeypatch.setattr(H, "_clients", lambda ctx, vault: clients(fake))
    ctx = _Ctx(paths, repository)
    opened = H.lesson_turn(ctx, H.LessonTurnInput(action="open", entry="learning_object",
                                                  learning_object_ids=["lo_eigen"]))
    lesson_id = opened["lessonId"]
    posed = H.lesson_turn(ctx, H.LessonTurnInput(action="reply", lesson_id=lesson_id, text="go"))
    assert posed["openCheck"] is not None and ctx.reloads == 1  # the minted item reloads the vault
    resumed = H.lesson_view(ctx, H.LessonViewInput(lesson_id=lesson_id))
    assert resumed["openCheck"]["checkRef"] == posed["openCheck"]["checkRef"]
    assert "committed" not in json.dumps(resumed).lower()


def test_lesson_turn_refuses_with_the_switch_off(tmp_path):
    from learnloop_sidecar.errors import SidecarError
    from learnloop_sidecar.handlers import lesson as H
    from tests.ux_phase1_support import set_config

    paths, repository = build_teacher_vault(tmp_path / "vault")
    set_config(paths.root, {("teacher", "enabled"): False})
    with pytest.raises(SidecarError) as raised:
        H.lesson_turn(_Ctx(paths, repository), H.LessonTurnInput(action="open", entry="learning_object",
                                                                 learning_object_ids=["lo_eigen"]))
    assert raised.value.code == "teacher_disabled"


def test_no_openrouter_offer_for_a_lesson_until_its_price_is_set():
    from learnloop.ai.plan_fallback import METERED_PRICE_SETTINGS, offer_blocker
    from learnloop.config.schema import LearnLoopConfig

    assert METERED_PRICE_SETTINGS["teacher"] == "teacher.metered_price_per_million"
    assert offer_blocker(LearnLoopConfig(), "teacher") is not None
    priced = LearnLoopConfig.model_validate({"teacher": {"metered_price_per_million": 1.0}})
    assert offer_blocker(priced, "teacher") is None


def test_a_metered_lesson_turn_needs_its_price_and_cap(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault")

    class Metered(TeacherFake):
        provider_type = "openrouter"

    with pytest.raises(S.LessonError) as raised:
        S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                      clients=clients(Metered([plan_turn])))
    assert raised.value.code == "plan_unavailable"
