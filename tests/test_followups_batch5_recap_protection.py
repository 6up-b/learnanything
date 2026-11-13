"""Follow-ups batch 5 (A): an earlier lesson's recap enters a brief, or ``read_history``, only while what that
lesson relied on is still teachable (TE1 post-land Codex verify, job 20261102-050349-DQNXMf, High).

The repro: lesson 1 reads passage P (``ext_lay/lay_char``) and closes with a recap quoting it; P is then
held out; "Start a fresh lesson" imported the recap through ``last_lessons``, and the fresh lesson records
today's protection as its baseline, so ``protection_changed`` never fires and the first teacher prompt
carried P. Real brief, protection, gate and prompt builders; synthetic vault; every model a fake.
"""

from __future__ import annotations

import json

from tests.teacher_fakes import pin_default_tag
from learnloop.algorithm_versions import TEACHER_ALGORITHM_VERSION
from learnloop.teacher import brief as B
from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from tests.section_coverage_fixtures import hold_out
from tests.teacher_fakes import TeacherFake, build_teacher_vault, clients, close_turn

PASSAGE = "The eigenvalues of A are the roots of the characteristic equation det(A - tI) = 0."
PASSAGE_WORDS = "roots of the characteristic equation"
READ_LAY = {"message": "Let me read.", "requests": [{"action": "read_source", "refs": ["ext_lay/lay_char"]}]}


def _first_lesson(tmp_path, *, read_lay: bool = True):
    """Lesson 1 on ``lo_eigen``: reads P (``read_lay``), then the learner stops and the recap quotes P."""

    paths, repository = build_teacher_vault(tmp_path / "vault")
    opening = [READ_LAY, {"message": "Read it."}] if read_lay else [{"message": "Hello."}]
    fake = TeacherFake(opening)
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(fake))
    fake.turns = [close_turn(recap=f"Remember: {PASSAGE}")]
    closed = S.take_turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="stop", payload={},
                         clients=clients(fake))
    assert closed["closed"]
    return paths, repository, view["lesson_id"]


def _fresh(paths, repository, turns):
    fake = TeacherFake(turns)
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(fake))
    return fake, view


def _prior(fake, lesson_id):
    return next(entry for entry in fake.contexts[0]["brief"]["last_lessons"] if entry["id"] == f"l:{lesson_id}")


def test_a_recap_quoting_a_passage_held_out_since_is_not_in_the_fresh_lesson_s_prompt(tmp_path):
    paths, repository, first = _first_lesson(tmp_path)
    hold_out(repository, "lay_char")
    fake, view = _fresh(paths, repository, [{"message": "Fresh start."}])
    # The lesson still opens; the earlier lesson stays listed, without its recap.
    assert not view["closed"]
    prior = _prior(fake, first)
    assert prior["recap"] is None and prior["recap_omitted"] == B.RECAP_OMITTED
    assert all(PASSAGE_WORDS not in prompt for _purpose, prompt in fake.prompts)


def test_read_history_cannot_fetch_that_recap_either(tmp_path):
    paths, repository, first = _first_lesson(tmp_path)
    hold_out(repository, "lay_char")
    reads = {"message": "Let me look back.", "requests": [{"action": "read_history", "refs": [f"l:{first}"]}]}
    fake, _view = _fresh(paths, repository, [reads, {"message": "Thanks."}])
    entries = fake.contexts[-1]["results"][0]["result"]["entries"]
    assert entries[0]["id"] == f"l:{first}" and entries[0]["recap"] is None
    assert entries[0]["recap_omitted"] == B.RECAP_OMITTED
    assert all(PASSAGE_WORDS not in prompt for _purpose, prompt in fake.prompts)


def test_the_recap_stays_while_protection_is_unchanged(tmp_path):
    paths, repository, first = _first_lesson(tmp_path)
    fake, _view = _fresh(paths, repository, [{"message": "Fresh start."}])
    prior = _prior(fake, first)
    assert prior["recap"] == f"Remember: {PASSAGE}" and "recap_omitted" not in prior
    assert PASSAGE_WORDS in json.dumps(fake.contexts[0]["brief"]["last_lessons"])


def test_the_recap_stays_when_protection_changed_elsewhere(tmp_path):
    paths, repository, first = _first_lesson(tmp_path)
    # A different unit held out: the protection epoch moved, but every passage lesson 1 delivered is still
    # teachable, so its recap re-checks clean.
    hold_out(repository, "lay_ortho")
    fake, _view = _fresh(paths, repository, [{"message": "Fresh start."}])
    assert _prior(fake, first)["recap"] == f"Remember: {PASSAGE}"


def test_an_item_the_earlier_lesson_was_shown_now_reserved_for_an_exam_drops_its_recap(tmp_path, monkeypatch):
    pin_default_tag(monkeypatch, TEACHER_ALGORITHM_VERSION)  # the first teacher tag's lesson is the subject
    from tests.teacher_te1_review_fixes_helpers import _rows

    paths, repository, first = _first_lesson(tmp_path, read_lay=False)
    opened = S.load_state(repository, first)
    probes = [probe["id"] for node in opened.brief["nodes"] for probe in node.get("probes") or []]
    assert "pi_det_1" in probes
    goal_id = _rows(repository, "SELECT goal_id FROM exam_pool_items LIMIT 1")[0][0]
    repository.insert_exam_pool_items([{"id": "epi_b5", "goal_id": goal_id, "practice_item_id": "pi_det_1",
                                        "reserved_at": "2026-11-01T08:00:00Z"}])
    fake, view = _fresh(paths, repository, [{"message": "Fresh start."}])
    assert not view["closed"]
    assert _prior(fake, first)["recap"] is None


def test_unreadable_protection_drops_the_recap_only(tmp_path, monkeypatch):
    paths, repository, first = _first_lesson(tmp_path)
    vault = load_vault(paths.root)
    monkeypatch.setattr(B, "protection_state", lambda *_a, **_k: None)
    brief, _book = B.build_brief(vault, repository, learning_object_ids=["lo_eigen"], how={"lo_eigen": "t"},
                                 goal_text="Eigenvalues", selection=None, driver="desktop", lesson_id=None,
                                 constraints={})
    prior = next(entry for entry in brief["last_lessons"] if entry["id"] == f"l:{first}")
    assert prior["recap"] is None and prior["recap_omitted"] == B.RECAP_OMITTED
    # The rest of the brief is built as usual.
    assert brief["nodes"] and brief["sources"]


def test_a_lesson_with_no_recorded_protection_rechecks_its_passages(tmp_path):
    paths, repository, first = _first_lesson(tmp_path)
    with repository.atomic():
        connection = repository.connection()
        row = connection.execute(
            "SELECT p.turn_id, p.payload_json FROM lesson_turn_payloads p JOIN lesson_turns t ON t.id = p.turn_id "
            "WHERE t.lesson_id = ? AND t.action = 'open'", (first,)).fetchone()
        payload = json.loads(row[1])
        payload.pop("protection")
        connection.execute("UPDATE lesson_turn_payloads SET payload_json = ? WHERE turn_id = ?",
                           (json.dumps(payload), row[0]))
    vault = load_vault(paths.root)
    assert B.recap_admissible(vault, repository, first)
    hold_out(repository, "lay_char")
    assert not B.recap_admissible(load_vault(paths.root), repository, first)
