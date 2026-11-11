"""Teacher TE1b landing ruling R2 (codex verify F8, docs/reviews/teacher-te1b-router-suggestions.md).

A Start whose lesson never opened is a reservation: the card keeps offering that lesson. Before it is
offered again it is checked against the current vault (its LO still there, the exam material readable,
as the lesson's opening needs). One that can no longer open is set aside (an ``expired`` row on its
decision, nothing deleted) and the day draws normally; the pending card's "Not now" lets it go
(``released``, the Start staying recorded). Every model is a fake; no network.
"""

from __future__ import annotations

import json

import pytest

from learnloop.daily_plan import lesson_suggestion as SG
from learnloop.db.stores import router_suggestions as store
from learnloop.router import lesson_suggestions as LS
from learnloop.router import outcomes as RO
from learnloop.teacher import service as S
from learnloop.teacher.brief import protection_state
from learnloop.vault.loader import load_vault
from tests.teacher_fakes import TeacherFake, clients, plan_turn
from tests.teacher_te1b_suggestions_helpers import _clock, _decisions, _rows, _vault, no_network, shown  # noqa: F401
from tests.teacher_te1b_landing_r2_helpers import _start, _today, _without


def _all_responses(repository, decision_id):
    return _rows(repository, "SELECT * FROM router_suggestion_responses WHERE decision_id = ? ORDER BY responded_at, id",
                 (decision_id,))


# --- an invalid reservation is validated before it is returned --------------------------------------------


def test_an_overnight_reservation_whose_lo_is_gone_is_set_aside_and_the_day_draws(tmp_path, shown, no_network):
    """F8's reproduction: Start on day 0, the app stops, the LO leaves the vault. Day 1 neither returns the
    reservation nor stays blocked: an ``expired`` row records it (the Start kept), and day 1 draws its own
    card; a month later the reservation is still gone."""

    paths, repository = _vault(tmp_path)
    card, lesson = _start(paths, repository)
    gone = lesson["learning_object_ids"]
    day1 = _today(_without(paths, gone), repository, _clock(days=1))
    assert day1 is not None and day1["decision_id"] != card["decision_id"] and day1["pending_lesson"] is None
    assert not set(day1["suggestion"]["learning_object_ids"]) & set(gone)
    assert [row["receipt_key"] for row in _decisions(repository)] == [
        "lesson_suggestion:2026-11-02", "lesson_suggestion:2026-11-03"]
    rows = _all_responses(repository, card["decision_id"])
    assert [row["response"] for row in rows] == ["accepted", "expired"]
    assert rows[0]["lesson_id"] == lesson["lesson_id"]  # nothing deleted, the Start still recorded
    detail = json.loads(rows[1]["detail_json"])
    assert detail["reason"] == "learning_object_missing" and detail["lesson_id"] == lesson["lesson_id"]
    assert json.loads(rows[1]["learning_object_ids_json"]) == gone and rows[1]["lesson_id"] is None
    # A month on, with the LO back, the expired reservation is never offered again.
    later = _today(load_vault(paths.root), repository, _clock(days=31))
    assert later is None or later["decision_id"] != card["decision_id"]
    assert len(_all_responses(repository, card["decision_id"])) == 2
    # The lesson can no longer open on it (refused before any teacher call).
    with pytest.raises(S.LessonError) as refused:
        S.open_lesson(load_vault(paths.root), repository, entry="learning_object",
                      clients=clients(TeacherFake([])), origin="router", origin_ref=card["decision_id"],
                      lesson_id=lesson["lesson_id"], clock=_clock(days=31, hours=1))
    assert refused.value.code == "not_found"


def test_a_same_day_reservation_whose_lo_is_gone_leaves_the_day_without_a_card(tmp_path, shown, no_network):
    """Today's own decision held the reservation: it is expired, and the day shows no card (one decision a
    day) rather than the unopenable lesson; the next day draws."""

    paths, repository = _vault(tmp_path)
    card, lesson = _start(paths, repository)
    assert _today(_without(paths, lesson["learning_object_ids"]), repository, _clock(hours=2)) is None
    assert [row["response"] for row in _all_responses(repository, card["decision_id"])] == ["accepted", "expired"]
    assert len(_decisions(repository)) == 1
    _today(load_vault(paths.root), repository, _clock(days=1))
    assert len(_decisions(repository)) == 2


def test_a_reservation_is_set_aside_when_the_exam_material_cannot_be_checked(tmp_path, shown, no_network, monkeypatch):
    paths, repository = _vault(tmp_path)
    card, _lesson = _start(paths, repository)
    monkeypatch.setattr(SG, "_protection_readable", lambda vault, repository: False)
    day1 = _today(load_vault(paths.root), repository, _clock(days=1))
    assert day1 is None or day1["decision_id"] != card["decision_id"]
    rows = _all_responses(repository, card["decision_id"])
    assert [row["response"] for row in rows] == ["accepted", "expired"]
    assert json.loads(rows[1]["detail_json"])["reason"] == "protection_unavailable"


def test_a_valid_reservation_is_still_offered(tmp_path, shown, no_network):
    paths, repository = _vault(tmp_path)
    card, lesson = _start(paths, repository)
    again = _today(load_vault(paths.root), repository, _clock(days=1))
    assert again["decision_id"] == card["decision_id"] and again["pending_lesson"]["lesson_id"] == lesson["lesson_id"]
    assert [row["response"] for row in _all_responses(repository, card["decision_id"])] == ["accepted"]


def test_the_protection_check_matches_the_lessons_opening(tmp_path):
    """``_protection_readable`` is the teacher's ``protection_state(...) is not None`` (read without importing
    the teacher)."""

    paths, repository = _vault(tmp_path)
    vault = load_vault(paths.root)
    assert SG._protection_readable(vault, repository) == (protection_state(vault, repository) is not None)
    view = {"pending_lesson": {"learning_object_ids": ["lo_det"]}}
    assert SG.reservation_problem(vault, repository, view) is None
    assert SG.reservation_problem(vault, repository, {"pending_lesson": {"learning_object_ids": ["lo_nope"]}}) == (
        "learning_object_missing")
    assert SG.reservation_problem(vault, repository, {"pending_lesson": {"learning_object_ids": []}}) == (
        "learning_object_missing")


# --- "Not now" on the pending card ------------------------------------------------------------------------


def test_not_now_on_a_pending_card_releases_the_reservation(tmp_path, shown, no_network):
    paths, repository = _vault(tmp_path)
    card, lesson = _start(paths, repository)
    pending = _today(load_vault(paths.root), repository, _clock(hours=2))
    assert pending["pending_lesson"]["lesson_id"] == lesson["lesson_id"]
    released = SG.respond(load_vault(paths.root), repository, decision_id=card["decision_id"], response="released",
                          clock=_clock(hours=3))
    assert released == {"decision_id": card["decision_id"], "response": "released",
                        "candidate_ref": card["suggestion"]["ref"], "lesson": None}
    # Idempotent: a second tap writes nothing.
    assert SG.respond(load_vault(paths.root), repository, decision_id=card["decision_id"], response="released",
                      clock=_clock(hours=3)) == released
    rows = _all_responses(repository, card["decision_id"])
    assert [row["response"] for row in rows] == ["accepted", "released"]
    assert json.loads(rows[1]["detail_json"])["reason"] == "not_now"
    assert json.loads(rows[1]["detail_json"])["lesson_id"] == lesson["lesson_id"]
    # Gone today, and the next day draws its own card (the released LO counts as declined).
    assert _today(load_vault(paths.root), repository, _clock(hours=4)) is None
    day1 = _today(load_vault(paths.root), repository, _clock(days=1))
    assert len(_decisions(repository)) == 2 and (day1 is None or day1["decision_id"] != card["decision_id"])
    with repository.connection() as connection:
        details = {d["id"]: d["detail"] for d in store.decisions(connection)}
        learner = store.responses(connection)
        responses = [*learner, *store.releases(connection)]
        assert store.response_for(connection, card["decision_id"])["response"] == "accepted"
        # The outcome ledger and the acceptance model still read the Start (a release is not a response).
        assert RO._suggestion_responses(connection)[card["decision_id"]]["response"] == "accepted"
    declines = LS.declines_by_learning_object(details, responses)
    assert set(lesson["learning_object_ids"]) <= set(declines)
    # A release is no acceptance observation: the model replays the Start alone.
    assert LS.observations(details, responses) == LS.observations(details, learner)
    assert [o.accepted for o in LS.observations(details, learner)] == [True]
    with pytest.raises(S.LessonError) as refused:
        S.open_lesson(load_vault(paths.root), repository, entry="learning_object",
                      clients=clients(TeacherFake([])), origin="router", origin_ref=card["decision_id"],
                      lesson_id=lesson["lesson_id"], clock=_clock(hours=5))
    assert refused.value.code == "not_found"


def test_release_needs_a_pending_lesson(tmp_path, shown, no_network):
    """An unanswered card, a declined one, or a Start whose lesson opened has nothing to release."""

    paths, repository = _vault(tmp_path)
    card = _today(load_vault(paths.root), repository, _clock())
    with pytest.raises(SG.SuggestionError) as unanswered:
        SG.respond(load_vault(paths.root), repository, decision_id=card["decision_id"], response="released",
                   clock=_clock(hours=1))
    assert unanswered.value.code == "not_found"
    started = SG.respond(load_vault(paths.root), repository, decision_id=card["decision_id"], response="accepted",
                         clock=_clock(hours=1))
    S.open_lesson(load_vault(paths.root), repository, entry="learning_object", clients=clients(TeacherFake([plan_turn])),
                  origin="router", origin_ref=card["decision_id"], lesson_id=started["lesson"]["lesson_id"],
                  clock=_clock(hours=2))
    with pytest.raises(SG.SuggestionError) as opened:
        SG.respond(load_vault(paths.root), repository, decision_id=card["decision_id"], response="released",
                   clock=_clock(hours=3))
    assert opened.value.code == "not_found"
    assert [row["response"] for row in _all_responses(repository, card["decision_id"])] == ["accepted"]


def test_an_expired_reservation_cannot_then_be_released(tmp_path, shown, no_network):
    paths, repository = _vault(tmp_path)
    card, lesson = _start(paths, repository)
    _today(_without(paths, lesson["learning_object_ids"]), repository, _clock(hours=2))
    with pytest.raises(SG.SuggestionError) as refused:
        SG.respond(load_vault(paths.root), repository, decision_id=card["decision_id"], response="released",
                   clock=_clock(hours=3))
    assert refused.value.code == "not_found"
    assert [row["response"] for row in _all_responses(repository, card["decision_id"])] == ["accepted", "expired"]


def test_the_store_keeps_one_response_and_one_release_per_decision(tmp_path, shown):
    paths, repository = _vault(tmp_path)
    card, _lesson = _start(paths, repository)
    with repository.atomic():
        connection = repository.connection()
        kwargs = dict(decision_id=card["decision_id"], candidate_ref="x", learning_object_ids=[],
                      responded_at="2026-11-02T12:00:00Z")
        assert store.insert_response(connection, response="declined", **kwargs) is False
        assert store.insert_response(connection, response="expired", **kwargs) is True
        assert store.insert_response(connection, response="released", **kwargs) is False
        with pytest.raises(ValueError):
            store.insert_response(connection, response="maybe", **kwargs)
        assert [r["response"] for r in store.responses(connection)] == ["accepted"]
        assert [r["response"] for r in store.releases(connection)] == ["expired"]
