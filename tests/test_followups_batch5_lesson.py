"""Follow-ups batch 5 (C, D, E): the lesson's unavailable-route copy, resume without a call, and a teacher
visual's figures-budget refusal (spec_teacher_v1 §7, §17; spec_reader_show_me_figures_v1 §6.5). Every
model is a fake; no network.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from tests.teacher_fakes import TeacherFake, build_teacher_vault, clients


def _rows(repository, sql, params=()):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(sql, params).fetchall()]


class _Ctx:
    def __init__(self, paths, repository):
        self.paths, self.repository = paths, repository
        self.grading_provider_override = None
        self.reloads = 0

    def require_vault(self):
        return load_vault(self.paths.root), self.repository

    def reload(self, maintenance: bool = True):
        self.reloads += 1


# --- C: the unavailable route's copy is true to what was saved ------------------------------------------


def _route_down(monkeypatch):
    from learnloop.ai import routing

    monkeypatch.setattr(routing, "ready_client_for_task",
                        lambda root, config, task: ("chatgpt_plan", SimpleNamespace(ready=False), None))


def test_c_an_opening_whose_route_is_down_says_nothing_was_saved(tmp_path, monkeypatch):
    from learnloop_sidecar.errors import SidecarError
    from learnloop_sidecar.handlers import lesson as H

    paths, repository = build_teacher_vault(tmp_path / "vault")
    _route_down(monkeypatch)
    with pytest.raises(SidecarError) as raised:
        H.lesson_turn(_Ctx(paths, repository), H.LessonTurnInput(action="open", entry="learning_object",
                                                                 learning_object_ids=["lo_eigen"]))
    error = raised.value
    assert error.code == "plan_unavailable" and error.retryable
    assert "nothing was saved" in error.message and "is saved" not in error.message
    assert "lesson_id" not in error.details
    assert _rows(repository, "SELECT COUNT(*) FROM lessons") == [(0,)]


def test_c_a_step_of_a_saved_lesson_whose_route_is_down_says_it_is_saved(tmp_path, monkeypatch):
    from learnloop_sidecar.errors import SidecarError
    from learnloop_sidecar.handlers import lesson as H

    paths, repository = build_teacher_vault(tmp_path / "vault")
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(TeacherFake([{"message": "Hello."}])))
    _route_down(monkeypatch)
    with pytest.raises(SidecarError) as raised:
        H.lesson_turn(_Ctx(paths, repository), H.LessonTurnInput(action="reply", lesson_id=view["lesson_id"],
                                                                 text="go on"))
    assert "your lesson is saved" in raised.value.message and "nothing was saved" not in raised.value.message
    # The reply itself is saved, so resume runs it once the route is back.
    assert _rows(repository, "SELECT COUNT(*) FROM lesson_turns WHERE action = 'learner_reply'") == [(1,)]


def test_c_an_opening_whose_teacher_call_fails_after_the_save_says_it_is_saved_and_carries_its_id(tmp_path):
    from learnloop.ai.errors import AIProviderUnavailable
    from learnloop_sidecar.handlers.lesson import _error, route_unavailable_message

    paths, repository = build_teacher_vault(tmp_path / "vault")

    def down(_context):
        raise AIProviderUnavailable("the plan is down")

    with pytest.raises(S.LessonError) as raised:
        S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                      clients=clients(TeacherFake([down])))
    error = _error(raised.value)
    assert error.details["lesson_id"] == _rows(repository, "SELECT id FROM lessons")[0][0]
    assert "your lesson is saved" in error.message
    assert "is saved" in route_unavailable_message("The ChatGPT plan", saved=True)
    assert "nothing was saved" in route_unavailable_message("The ChatGPT plan", saved=False)


# --- D: resume after a completed help action makes no call (TE1 F16, ruled Low at R3) --------------------

SOLUTION = "the roots of det(A - tI) = 0"


def _teacher_calls(fake):
    return len([1 for purpose, _prompt in fake.prompts if purpose == "teacher_turn"])


def _help_lesson(tmp_path, help_turns):
    from tests.teacher_fakes import check_turn, plan_turn

    paths, repository = build_teacher_vault(tmp_path / "vault")
    fake = TeacherFake([plan_turn, check_turn(solution=SOLUTION)])
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(fake))
    S.take_turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="reply",
                payload={"text": "go"}, clients=clients(fake))
    fake.turns = list(help_turns)
    helped = S.take_turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="reply",
                         payload={"text": "I'm stuck, help?"}, clients=clients(fake))
    assert helped["open_check"] is None  # the help gave the solution away: the check was withdrawn
    return paths, repository, fake, view["lesson_id"]


def _resume(paths, repository, fake, lesson_id):
    fake.turns = [{"message": "never sent"}]
    return S.take_turn(load_vault(paths.root), repository, lesson_id=lesson_id, action="resume", payload={},
                       clients=clients(fake))


def test_d_resume_after_a_help_action_that_withdrew_the_check_makes_no_call(tmp_path):
    paths, repository, fake, lesson_id = _help_lesson(tmp_path, [{"message": f"Here it is: {SOLUTION}."}])
    calls = _teacher_calls(fake)
    view = _resume(paths, repository, fake, lesson_id)
    assert _teacher_calls(fake) == calls
    assert not view["closed"] and view["feed"][-1]["text"] != "never sent"


def test_d_resume_after_a_help_action_with_a_read_follow_up_makes_no_call(tmp_path):
    reads = {"message": f"Here it is: {SOLUTION}.",
             "requests": [{"action": "read_source", "refs": ["ext_book/ch_det"]}]}
    followup = {"message": "And once more.", "requests": [{"action": "read_source", "refs": ["ext_lay/lay_char"]}]}
    paths, repository, fake, lesson_id = _help_lesson(tmp_path, [reads, followup])
    calls = _teacher_calls(fake)
    _resume(paths, repository, fake, lesson_id)
    assert _teacher_calls(fake) == calls
    # The follow-up's own reads still ride with the next learner action (one call, results delivered).
    fake.turns = [{"message": "Next."}]
    S.take_turn(load_vault(paths.root), repository, lesson_id=lesson_id, action="reply", payload={"text": "ok"},
                clients=clients(fake))
    assert _teacher_calls(fake) == calls + 1
    assert "roots of the characteristic equation" in str(fake.contexts[-1]["results"])


# --- E: a figures daily-budget refusal marks only the visual unavailable (P4b) ----------------------------


class _MeteredRequest:
    """A physical metered request (an OpenRouter-like client with no owner price)."""

    provider_name = "openrouter_test"
    provider_type = "openrouter"


def lesson_envelope_refuses(_context):
    """The figure author's physical request goes through the active request gates: with a per-lesson cap
    and no price, the LESSON's envelope refuses it (``refusal`` recorded) before anything is sent."""

    from learnloop.ai.execution import model_call

    with model_call(_MeteredRequest(), purpose="figure_author", prompt="draw it"):
        raise AssertionError("the lesson's envelope admitted a request it should refuse")


def _visual_lesson(tmp_path, author_answers):
    from tests.figure_fixtures import AuthorFake
    from tests.test_reader_rw5d_p4b_teacher_visuals import _builder, _clients, _spec, visual_turn

    paths, repository = build_teacher_vault(tmp_path / "vault")
    author = AuthorFake(list(author_answers) or [_spec()])
    fake = TeacherFake([{"message": "Hello."}])
    build = _builder(paths, repository, author)
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=_clients(fake, build))
    fake.turns = [visual_turn]
    return paths, repository, fake, author, build, view["lesson_id"]


def _visual_payloads(repository, lesson_id):
    import json

    return [json.loads(row[0]) for row in _rows(
        repository, "SELECT p.payload_json FROM lesson_turns t JOIN lesson_turn_payloads p ON p.turn_id = t.id "
                    "WHERE t.lesson_id = ? AND t.action = 'visual' ORDER BY t.seq", (lesson_id,))]


def test_e_the_figures_daily_budget_refusing_a_visual_leaves_the_lesson_open(tmp_path):
    from learnloop.ai.spend import SpendLimitExceeded
    from tests.test_reader_rw5d_p4b_teacher_visuals import _clients

    # The figures' shared daily envelope refuses the author's request before it is sent (the figure
    # service reports it as ``capped``, raised from the SpendLimitExceeded).
    paths, repository, fake, author, build, lesson_id = _visual_lesson(
        tmp_path, [SpendLimitExceeded("today's figure budget would be passed")])
    view = S.take_turn(load_vault(paths.root), repository, lesson_id=lesson_id, action="reply",
                       payload={"text": "show me"}, clients=_clients(fake, build))
    assert not view["closed"]
    (visual,) = _visual_payloads(repository, lesson_id)
    assert visual["status"] == "unavailable" and visual["code"] == "capped"
    assert _rows(repository, "SELECT COUNT(*) FROM lesson_receipts") == [(0,)]
    # The lesson goes on: the next reply reaches the teacher.
    fake.turns = [{"message": "Without the figure, then."}]
    calls = len(fake.prompts)
    after = S.take_turn(load_vault(paths.root), repository, lesson_id=lesson_id, action="reply",
                        payload={"text": "ok"}, clients=_clients(fake, build))
    assert not after["closed"] and len(fake.prompts) == calls + 1


def test_e_the_lesson_envelope_refusing_a_visual_still_closes_the_lesson_with_budget(tmp_path):
    from tests.test_reader_rw5d_p4b_teacher_visuals import _clients
    from tests.ux_phase1_support import set_config

    paths, repository, fake, author, build, lesson_id = _visual_lesson(tmp_path, [lesson_envelope_refuses])
    set_config(paths.root, {("teacher", "max_lesson_cost_usd"): 1.0})
    view = S.take_turn(load_vault(paths.root), repository, lesson_id=lesson_id, action="reply",
                       payload={"text": "show me"}, clients=_clients(fake, build))
    assert view["closed"] and view["close_reason"] == "budget"
    assert _rows(repository, "SELECT close_reason FROM lesson_receipts") == [("budget",)]


def test_e_the_visual_builder_decides_by_the_lesson_gate_alone():
    from learnloop.ai.spend import SpendLimitExceeded
    from learnloop.figures.service import FigureRefused
    from learnloop.teacher import visuals as V

    try:
        try:
            raise SpendLimitExceeded("figures daily envelope")
        except SpendLimitExceeded as inner:
            raise FigureRefused("capped", "Today's figure budget is used.") from inner
    except FigureRefused as exc:
        refused = exc
    assert not V._budget_refused(SimpleNamespace(gate=SimpleNamespace(refusal=None)), refused)
    assert not V._budget_refused(SimpleNamespace(gate=None), refused)
    assert V._budget_refused(SimpleNamespace(gate=SimpleNamespace(refusal={"reason": "limit"})), refused)
