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
