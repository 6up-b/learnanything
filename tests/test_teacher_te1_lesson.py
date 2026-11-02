"""Teacher TE1: the lesson lifecycle, the actions and the checks (spec_teacher_v1 §6-§13, §20).

Every model is ``TeacherFake`` (a scripted teacher and a blind grader); no network.
"""

from __future__ import annotations

import pytest

from learnloop.db.repositories import Repository
from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from tests.teacher_fakes import (
    TeacherFake,
    build_teacher_vault,
    check_turn,
    clients,
    close_turn,
    landed_and_close_turn,
    landed_turn,
    plan_turn,
)


def _rows(repository, sql, params=()):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(sql, params).fetchall()]


def _open(tmp_path, turns, **kwargs):
    paths, repository = build_teacher_vault(tmp_path / "vault", **kwargs)
    fake = TeacherFake(turns)
    vault = load_vault(paths.root)
    view = S.open_lesson(vault, repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(fake))
    return paths, repository, fake, view


def test_a_whole_lesson_opens_teaches_checks_and_closes_with_delayed_checks(tmp_path):
    paths, repository, fake, view = _open(tmp_path, [plan_turn, check_turn()])
    lesson_id = view["lesson_id"]
    assert [entry["kind"] for entry in view["feed"]][:1] == ["message"]
    assert view["plan"] and view["plan"][0]["id"] == "n1"
    # The learner says go; the teacher poses a check (minted, held, collapsed on screen).
    view = S.turn(load_vault(paths.root), repository, lesson_id=lesson_id, action="reply",
                  payload={"text": "Go ahead."}, clients=clients(fake))
    assert view["open_check"] is not None and "committed_solution" not in str(view["open_check"])
    fake.turns = [landed_and_close_turn()]
    view = S.turn(load_vault(paths.root), repository, lesson_id=lesson_id, action="answer_check",
                  payload={"answer": "det(A - tI) = 0", "tap": 4, "thinking": "THINKINGNOTE char poly"},
                  clients=clients(fake))
    assert view["closed"] and view["close_reason"] == "goal_reached"
    check = _rows(repository, "SELECT status, attempt_id, mass_applied, mass_learned, tap FROM lesson_checks")
    assert len(check) == 1 and check[0][0] == "answered" and check[0][4] == 4
    assert 0.0 < check[0][2] < 1.0 and abs(check[0][2] - check[0][3]) < 1e-12
    attempt = _rows(repository, "SELECT attempt_type, answer_confidence, primed FROM practice_attempts WHERE id = ?",
                    (check[0][1],))
    assert attempt == [("reconstruction_after_walkthrough", 4, 0)]
    # The blind grader saw the answer only: never the thinking note.
    assert fake.grading_contexts and all("THINKINGNOTE" not in str(c) for c in fake.grading_contexts)
    grading_prompts = [p for purpose, p in fake.prompts if purpose != "teacher_turn"]
    assert grading_prompts and all("THINKINGNOTE" not in p for p in grading_prompts)
    # Delayed checks: one retention on the landed node's LO and one transfer, dated, as Check once.
    commitments = _rows(repository, "SELECT created_action, idempotency_key FROM commitments")
    assert len(commitments) == 2 and all(row[0] == "test_me_later" and row[1].startswith("lesson:") for row in commitments)
    receipt = _rows(repository, "SELECT close_reason, receipt_json FROM lesson_receipts")
    assert receipt[0][0] == "goal_reached"
    import json

    data = json.loads(receipt[0][1])
    assert {c["purpose"] for c in data["delayed_checks"]} == {"retention", "transfer"}
    assert data["weight_inputs"][0]["tap"] == 4 and data["stability_inputs"]
    assert any(key.startswith("lesson_step_retained") for key in data["forecasts"])
    close = view["feed"][-1]
    assert close["kind"] == "close" and len(close["delayed_checks"]) == 2


def test_the_minted_check_item_is_held_to_its_lesson(tmp_path):
    from learnloop.vault.lifecycle import LESSON_HOLD, practice_item_serving_block

    paths, repository, fake, view = _open(tmp_path, [plan_turn, check_turn()])
    S.turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="reply",
           payload={"text": "ok"}, clients=clients(fake))
    vault = load_vault(paths.root)
    minted = [item for item in vault.practice_items.values() if item.id.startswith("pi_lesson_")]
    assert len(minted) == 1
    assert practice_item_serving_block(vault, minted[0]) == LESSON_HOLD
    extra = minted[0].provenance.model_extra
    assert extra["mechanism"] == "teacher_lesson_v1" and extra["lesson_id"] == view["lesson_id"]


# --- the actions -----------------------------------------------------------------------------


def _results(fake, index=-1):
    return fake.contexts[index]["results"]


def test_read_source_find_sources_find_practice_and_read_history_return_safe_results(tmp_path):
    from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
    from learnloop.clock import FrozenClock
    from datetime import UTC, datetime

    paths, repository = build_teacher_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    complete_self_graded_attempt(vault, repository, AttemptDraft(
        practice_item_id="pi_det_1", learner_answer_md="LEARNERWORDS it is minus two", attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=4),
        clock=FrozenClock(datetime(2026, 10, 20, tzinfo=UTC)))

    def reads(context):
        history = [entry["id"] for entry in context["brief"]["history"] if entry["id"].startswith("h:")]
        return {"message": "Let me look things up.", "requests": [
            {"action": "read_source", "refs": ["ext_book/ch_det"]},
            {"action": "find_sources", "query": "determinant cofactor expansion", "intent": "explain"},
            {"action": "find_practice", "query": "determinants", "intent": "practice",
             "learning_object_ids": ["lo_det"]},
            {"action": "read_history", "refs": history},
        ]}

    fake = TeacherFake([reads, {"message": "Thanks."}])
    S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                  clients=clients(fake))
    results = {entry["action"]: entry["result"] for entry in _results(fake)}
    sections = results["read_source"]["sections"]
    assert sections[0]["ref"] == "ext_book/ch_det" and sections[0]["passages"]
    assert all(p["alias"].startswith("S") for p in sections[0]["passages"])
    assert "book_additions" not in results["read_source"]
    assert "passages" in results["find_sources"]
    items = results["find_practice"]["items"]
    assert all("expected_answer" not in item for item in items)
    assert "capybara" not in str(items) and "tapir" not in str(items)
    history = results["read_history"]["entries"]
    assert history and history[0]["learner_answer"].startswith("LEARNERWORDS")
    calls = _rows(repository, "SELECT caller_kind, tool, row_kind FROM source_tool_calls ORDER BY created_at, id")
    assert ("teacher", "find_sources", "request") in calls and ("teacher", "find_practice", "run") in calls


def test_a_plan_whose_anchors_do_not_resolve_is_refused_back_to_the_teacher(tmp_path):
    bad = {"message": "Plan.", "requests": [{"action": "write_plan", "plan": [
        {"id": "n1", "statement": "x", "lo_id": "lo_eigen", "anchors": ["S999"], "premises": []}]}]}
    paths, repository, fake, view = _open(tmp_path, [bad, plan_turn])
    turns = _rows(repository, "SELECT action, validation FROM lesson_turns WHERE actor = 'teacher' ORDER BY seq")
    assert turns[0] == ("teacher_turn", "invalid") and ("teacher_turn", "ok") in turns
    assert "S999" in str(fake.contexts[1]["transcript"])
    assert _rows(repository, "SELECT COUNT(*) FROM lesson_plans") == [(1,)]


def test_forecasts_are_receipts_with_their_bindings(tmp_path):
    paths, repository, fake, view = _open(tmp_path, [plan_turn, check_turn()])
    S.turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="reply", payload={"text": "go"},
           clients=clients(fake))
    rows = _rows(repository, "SELECT kind, scope, binding_kind, decision_kind, p FROM forecast_receipts")
    assert ("lesson_check_correct", "lesson_check", "lesson_check_attempt", "lesson", 0.75) in rows


# --- the guards ------------------------------------------------------------------------------


def test_a_message_that_gives_an_items_answer_away_is_withheld_and_the_teacher_reprompted(tmp_path):
    leak = {"message": "The answer is quokka zebra marmot: two, five."}
    paths, repository, fake, view = _open(tmp_path, [leak, plan_turn])
    assert all("quokka" not in str(entry) for entry in view["feed"])
    turns = _rows(repository, "SELECT validation FROM lesson_turns WHERE actor = 'teacher' ORDER BY seq")
    assert turns[0] == ("withheld",) and ("ok",) in turns
    assert "answer_key" in str(fake.contexts[1]["transcript"])


def test_three_consecutive_refused_turns_close_the_lesson(tmp_path):
    leak = {"message": "quokka zebra marmot: two, five"}
    paths, repository, fake, view = _open(tmp_path, [leak, leak, leak])
    assert view["closed"] and view["close_reason"] == "teacher_contract_failure"


def test_citations_must_name_delivered_passages_and_quotes_must_match(tmp_path):
    unknown = {"message": "As the book says [S77]."}
    misquote = lambda context: {"message": '"Eigenvalues are purple bananas" [S1]'}  # noqa: E731
    paths, repository, fake, view = _open(tmp_path, [unknown, misquote, plan_turn])
    reasons = _rows(repository, "SELECT validation FROM lesson_turns WHERE actor = 'teacher' ORDER BY seq")
    assert reasons[:2] == [("withheld",), ("withheld",)]
    payloads = str(_rows(repository, "SELECT payload_json FROM lesson_turn_payloads"))
    assert "unknown_citation" in payloads and "quote_mismatch" in payloads


def test_while_a_check_is_open_its_solution_is_never_shown(tmp_path):
    leaking = check_turn(solution="the roots of det(A - tI) = 0", message="Hint: the roots of det(A - tI) = 0.")
    paths, repository, fake, view = _open(tmp_path, [plan_turn, leaking, check_turn(solution="the roots of det(A - tI) = 0")])
    view = S.turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="reply",
                  payload={"text": "go"}, clients=clients(fake))
    assert all("Hint: the roots" not in str(entry) for entry in view["feed"])
    assert view["open_check"] is not None
    assert "open_check_solution" in str(_rows(repository, "SELECT payload_json FROM lesson_turn_payloads"))


def test_help_that_gives_the_solution_away_withdraws_the_check_with_no_attempt(tmp_path):
    paths, repository, fake, view = _open(tmp_path, [plan_turn, check_turn(solution="the roots of det(A - tI) = 0")])
    S.turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="reply", payload={"text": "go"},
           clients=clients(fake))
    fake.turns = [{"message": "Here it is: the roots of det(A - tI) = 0."}]
    view = S.turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="reply",
                  payload={"text": "I'm stuck, help?"}, clients=clients(fake))
    assert view["open_check"] is None and view["notices"]
    assert _rows(repository, "SELECT status, attempt_id FROM lesson_checks") == [("withdrawn", None)]
    assert _rows(repository, "SELECT COUNT(*) FROM practice_attempts WHERE attempt_type = "
                             "'reconstruction_after_walkthrough'") == [(0,)]
    assert _rows(repository, "SELECT surface, shown FROM help_assists") == [("tutor", 1)]


def test_teaching_text_writes_lesson_reveal_rows_on_the_lessons_items(tmp_path):
    reveal = {"message": "Picture a capybara walking two steps."}
    paths, repository, fake, view = _open(tmp_path, [reveal])
    rows = _rows(repository, "SELECT practice_item_id, source_kind, basis FROM reveal_events WHERE amount > 0")
    assert ("pi_det_1", "tutor_answer", f"lesson:{view['lesson_id']}") in rows


# --- protection ---------------------------------------------------------------------------------


def test_exam_and_held_out_sentinels_never_reach_the_teacher_or_a_screen(tmp_path):
    from tests.teacher_fakes import SENTINELS

    def probe(context):
        return {"message": "Looking around.", "requests": [
            {"action": "read_source", "refs": ["ext_exam/exam_q", "ext_lay/lay_held", "ext_book/ch_eigen"]},
            {"action": "find_sources", "query": "eigenvalues of the midterm matrix", "intent": "explain"},
            {"action": "find_practice", "query": "eigenvalues", "intent": "practice"},
        ]}

    paths, repository, fake, view = _open(tmp_path, [probe, {"message": "ok"}])
    sel = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                        clients=clients(TeacherFake([{"message": "hi"}])))
    text = fake.all_prompts()
    for sentinel in SENTINELS:
        assert sentinel not in text
        assert sentinel not in str(view) and sentinel not in str(sel)
    refused = [s for s in _results(fake)[0]["result"]["sections"] if s.get("refused")]
    assert {s["ref"] for s in refused} == {"ext_exam/exam_q", "ext_lay/lay_held"}


def test_a_reader_selection_of_protected_material_is_refused_in_one_line(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    fake = TeacherFake([{"message": "hi"}])
    with pytest.raises(S.LessonError) as raised:
        S.open_lesson(load_vault(paths.root), repository, entry="reader_selection",
                      selection={"extraction_id": "ext_exam", "span_ids": ["s2"]}, clients=clients(fake))
    assert raised.value.code == "protected" and not fake.prompts
    assert _rows(repository, "SELECT COUNT(*) FROM lessons") == [(0,)]


def test_a_reader_selection_opens_on_its_sections_topics(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    fake = TeacherFake([{"message": "hi"}])
    view = S.open_lesson(load_vault(paths.root), repository, entry="reader_selection",
                         selection={"extraction_id": "ext_book", "span_ids": ["s2"]}, clients=clients(fake))
    assert "lo_eigen" in view["learning_object_ids"]
    brief = fake.contexts[0]["brief"]
    assert brief["sources"]["sections"][0]["ref"].startswith("ext_book/")


# --- the switches --------------------------------------------------------------------------------


def test_off_or_below_the_tag_no_lesson_opens(tmp_path):
    from tests.ux_phase1_support import set_config

    paths, repository = build_teacher_vault(tmp_path / "vault", version="mvp-0.40")
    with pytest.raises(S.LessonError) as raised:
        S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                      clients=clients(TeacherFake()))
    assert raised.value.code == "teacher_unavailable"
    paths2, repository2 = build_teacher_vault(tmp_path / "vault2")
    set_config(paths2.root, {("teacher", "enabled"): False})
    with pytest.raises(S.LessonError) as raised:
        S.open_lesson(load_vault(paths2.root), repository2, entry="learning_object", learning_object_ids=["lo_eigen"],
                      clients=clients(TeacherFake()))
    assert raised.value.code == "teacher_disabled"
    for repo in (repository, repository2):
        assert _rows(repo, "SELECT COUNT(*) FROM lessons") == [(0,)]


def test_with_the_learned_weight_off_a_check_enters_at_the_types_configured_mass(tmp_path):
    from tests.ux_phase1_support import set_config

    paths, repository = build_teacher_vault(tmp_path / "vault")
    set_config(paths.root, {("teacher", "weight", "learned"): False})
    fake = TeacherFake([plan_turn, check_turn()])
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(fake))
    S.turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="reply", payload={"text": "go"},
           clients=clients(fake))
    S.turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="answer_check",
           payload={"answer": "det(A - tI) = 0"}, clients=clients(fake))
    assert _rows(repository, "SELECT mass_applied, json_extract(weight_inputs_json, '$.rule') FROM lesson_checks") \
        == [(0.5, "fixed")]
