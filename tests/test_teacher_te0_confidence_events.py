"""Teacher TE0 (spec_teacher_v1 §15.2): confidence as events in model contexts and on the router card.

* the tap (``practice_attempts.answer_confidence``) and the grader's hedge read
  (``grading_evidence.learner_confidence``) are rendered as events in words
  with the outcome ("marked 5/5 sure; wrong"), never raw scalars or counts,
  and the limit is stated when the taps do not span the scale;
* they reach the router card (``learner_state_card_v2``), the history-aware
  diagnoser (history and current attempt), the hint writer and the tutor;
* never the blind grader;
* an attempt the shared protection withholds contributes no event to the hint
  writer or the tutor, and nothing shows when the protection is unreadable;
* parity: with no confidence data every context renders exactly as before,
  and the card's text and typed fields are a v1 card's (only the version
  label moves). Fakes only; no model is called.
"""

from __future__ import annotations

import ast
import hashlib
import json
from contextlib import closing
from pathlib import Path

import pytest

from learnloop import confidence_events as CE
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.router.card import CARD_VERSION, PREDECESSOR_CARD_VERSION, CardInputs, build_card, canonical_json
from learnloop.vault.loader import load_vault

from tests.approach_map_fakes import ITEM, LO, map_vault

SRC = Path(__file__).resolve().parents[1] / "src" / "learnloop"


def _attempt(sqlite_path, attempt_id: str, *, at: str, correctness: float | None, tap: int | None = None,
             hedge: str | None = None, attempt_type: str = "independent_attempt", item_id: str = ITEM,
             lo_id: str = LO, local_grader_id: str | None = None, answer: str = "my answer") -> None:
    with closing(connect(sqlite_path)) as connection:
        connection.execute(
            "INSERT INTO practice_attempts (id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "learner_answer_md, correctness, rubric_score, created_at, answer_confidence) "
            "VALUES (?, ?, ?, 'short_answer', ?, ?, ?, ?, ?, ?)",
            (attempt_id, item_id, lo_id, attempt_type, answer, correctness,
             None if correctness is None else correctness * 4, at, tap))
        if hedge is not None:
            connection.execute(
                "INSERT INTO grading_evidence (id, attempt_id, criterion_id, points_awarded, grader_tier, created_at, "
                "learner_confidence, local_grader_id) VALUES (?, ?, 'correctness', ?, 3, ?, ?, ?)",
                (f"ge_{attempt_id}", attempt_id, (correctness or 0) * 4, at, hedge, local_grader_id))
        connection.commit()


def _vault(tmp_path):
    paths = map_vault(tmp_path)
    return paths, load_vault(paths.root), Repository.attach(paths.sqlite_path)


# -- the rendering ------------------------------------------------------------------------


def test_events_are_words_with_the_outcome_never_scalars():
    assert CE.event_text(CE.Reading(tap=5), "incorrect") == "marked 5/5 sure; wrong"
    assert CE.event_text(CE.Reading(tap=2), "correct") == "marked 2/5 sure; right"
    assert CE.event_text(CE.Reading(hedge="hedged"), "correct") == \
        "no tap; the grader read the answer as hedged; right"
    assert CE.event_text(CE.Reading(tap=4, hedge="mixed"), "partial") == \
        "marked 4/5 sure; the grader read parts of the answer as hedged; partly right"
    assert CE.event_text(CE.Reading(tap=3), "held_for_review") == "marked 3/5 sure; held for review (no score yet)"
    assert CE.event_text(CE.Reading(), "correct") is None and CE.event_text(None, "correct") is None


def test_hedge_reads_combine_without_a_threshold():
    assert CE.combine_hedges(["hedged", "hedged"]) == "hedged"
    assert CE.combine_hedges(["confident", None, "absent"]) == "confident"
    assert CE.combine_hedges(["confident", "hedged"]) == "mixed"
    assert CE.combine_hedges(["absent", "unknown", None]) is None


def test_the_limit_is_stated_only_when_the_taps_do_not_span_the_scale():
    assert CE.taps_limit([4, 5, 5, 4]) == "your taps so far are all 4–5 (4 taps)"
    assert CE.taps_limit([5]) == "your taps so far are all 5 (1 tap)"
    assert CE.taps_limit([1, 3, 5]) is None
    assert CE.taps_limit([]) is None and CE.taps_limit([None, 9]) is None


# -- the card -----------------------------------------------------------------------------


def _card_inputs(**extra) -> CardInputs:
    entries = [{"attempt_id": f"a{i}", "at": f"2026-10-{i + 1:02d}T09:00:00Z", "learning_object_id": "lo",
                "topic": "Bases", "kind": "short_answer", "result": ["correct", "incorrect", "held_for_review"][i % 3],
                "hints_used": i % 2, "key_status": None, "stem": "What is a basis?",
                "answer": "a spanning independent set"} for i in range(4)]
    work = extra.pop("work", None)
    if work:
        for entry, event in zip(entries, work):
            if event:
                entry["confidence"] = event
    return CardInputs(
        decision={"surface": "daily_plan", "decided_at": "2026-10-12T09:00:00Z"},
        session={"plan_kind": "normal", "minutes_left": 10, "minutes_budget": 25},
        candidates=[{"ref": "maintain:1", "kind": "maintain", "est_minutes": 4, "topics": ["Bases"],
                     "reversible": True, "reason_code": "review"}],
        learning_objects={"lo": {"title": "Bases", "status": "demonstrated", "evidence": {"graded": 3}}},
        interaction_7d={"attempts": 3, "hints_used": 1}, unknowns=["never tested: Spans"], recent_work=entries,
        **extra,
    )


#: A ``learner_state_card_v1`` card built from :func:`_card_inputs` by the
#: pre-TE0 builder (base e9d4de1aa): its text, and its typed fields without the
#: version label. TE0's builder must reproduce both with no confidence data.
V1_TEXT_SHA256 = "e9b295544045371e70c1854ceda964f7a62efc0aab1ea2551325b78b30838dd2"
V1_BODY_SHA256 = "b242b95cded267e5b984ec497d190a5ba4b3065f88a044ce23c2c335381dc201"


def test_card_parity_with_no_confidence_data_only_the_version_moves():
    card = build_card(_card_inputs())
    assert card.card_version == CARD_VERSION == "learner_state_card_v2" and PREDECESSOR_CARD_VERSION.endswith("_v1")
    body = {key: value for key, value in card.json.items() if key != "card_version"}
    assert hashlib.sha256(card.text.encode()).hexdigest() == V1_TEXT_SHA256
    assert hashlib.sha256(canonical_json(body).encode()).hexdigest() == V1_BODY_SHA256
    assert "confidence_7d" not in card.json and "confidence_limit" not in card.json and "Confidence" not in card.text


def test_the_card_carries_the_events_on_work_lines_and_in_the_seven_day_window():
    card = build_card(_card_inputs(
        work=["marked 5/5 sure; right", "marked 5/5 sure; wrong"],
        confidence_7d={"lo": [{"attempt_id": "a1", "at": "2026-10-02T09:00:00Z", "event": "marked 5/5 sure; wrong"}]},
        confidence_limit="your taps so far are all 5 (2 taps)",
    ))
    assert "· incorrect · 1 hint · marked 5/5 sure; wrong\n" in card.text
    assert "# Confidence, last 7 days" in card.text
    assert "- Bases: 2026-10-02 marked 5/5 sure; wrong" in card.text
    assert "(your taps so far are all 5 (2 taps))" in card.text
    assert card.json["confidence_7d"]["lo"][0]["event"] == "marked 5/5 sure; wrong"


def _gathered_card(tmp_path, monkeypatch, attempts):
    from tests.test_router_card import _card, _card_world

    env = _card_world(tmp_path, monkeypatch)
    for row in attempts:
        _attempt(env.repository.sqlite_path, **row)
    return _card(env)


def test_the_gathered_card_renders_taps_and_hedge_reads_as_events(tmp_path, monkeypatch):
    # NOW is 2026-10-12T09:00Z: two attempts inside the 7-day window, one before it.
    card = _gathered_card(tmp_path, monkeypatch, [
        dict(attempt_id="att_sure_wrong", at="2026-10-10T09:00:00Z", correctness=0.0, tap=5, item_id="pi_a",
             lo_id="lo_m1"),
        dict(attempt_id="att_hedged_right", at="2026-10-11T09:00:00Z", correctness=1.0, hedge="hedged",
             item_id="pi_a", lo_id="lo_m1"),
        dict(attempt_id="att_self", at="2026-10-11T10:00:00Z", correctness=1.0, hedge="hedged",
             local_grader_id="self", item_id="pi_b", lo_id="lo_m2"),
        dict(attempt_id="att_old", at="2026-09-01T09:00:00Z", correctness=1.0, tap=4, item_id="pi_b", lo_id="lo_m2"),
    ])
    body, text = card["json"], card["text"]
    assert body["card_version"] == CARD_VERSION
    work = {entry["attempt_id"]: entry for entry in body["recent_work"]}
    assert work["att_sure_wrong"]["confidence"] == "marked 5/5 sure; wrong"
    assert work["att_hedged_right"]["confidence"] == "no tap; the grader read the answer as hedged; right"
    assert work["att_old"]["confidence"] == "marked 4/5 sure; right"
    # A self-grade's learner_confidence came from a stated number: no hedge read.
    assert "confidence" not in work["att_self"]
    window = body["confidence_7d"]
    assert [event["attempt_id"] for event in window["lo_m1"]] == ["att_hedged_right", "att_sure_wrong"]
    assert "lo_m2" not in window  # att_old is outside the window; att_self has no event
    assert body["confidence_limit"] == "your taps so far are all 4–5 (2 taps)"
    assert "marked 5/5 sure; wrong" in text and "your taps so far are all 4–5" in text
    # Events, never the raw scalars.
    assert "answer_confidence" not in json.dumps(body) and "learner_confidence" not in json.dumps(body)


def test_the_gathered_card_without_confidence_data_has_no_confidence_fields(tmp_path, monkeypatch):
    card = _gathered_card(tmp_path, monkeypatch, [
        dict(attempt_id="att_plain", at="2026-10-10T09:00:00Z", correctness=1.0, item_id="pi_a", lo_id="lo_m1"),
    ])
    body = card["json"]
    assert body["card_version"] == CARD_VERSION
    assert "confidence_7d" not in body and "confidence_limit" not in body
    assert all("confidence" not in entry for entry in body["recent_work"])
    assert "Confidence" not in card["text"]


def test_protected_past_work_keeps_its_result_and_its_event_but_no_text(tmp_path, monkeypatch):
    card = _gathered_card(tmp_path, monkeypatch, [
        dict(attempt_id="att_exam", at="2026-10-10T09:00:00Z", correctness=0.0, tap=5, item_id="pi_a",
             lo_id="lo_m1", attempt_type="exam_attempt", answer="EXAM_ANSWER_TE0"),
    ])
    work = {entry["attempt_id"]: entry for entry in card["json"]["recent_work"]}
    assert work["att_exam"]["answer"] is None and work["att_exam"]["withheld"]
    assert work["att_exam"]["confidence"] == "marked 5/5 sure; wrong"
    assert "EXAM_ANSWER_TE0" not in card["text"]


# -- the hint writer ----------------------------------------------------------------------


def _hint_world(tmp_path):
    """The hint service's vault with no authored hint, so the writer is asked."""

    from tests.test_hint_service import _setup

    return _setup(tmp_path, config="[hints]\nmax_daily_cost_usd = 0\n", hints=[])


def _ask_writer(vault, repository):
    from tests.hint_fakes import ChooserFake, WriterFake, prefer
    from tests.test_hint_service import _ask

    writer = WriterFake(provider_type="chatgpt_plan")
    _ask(vault, repository, writer=writer, chooser=ChooserFake(prefer("next_step@L3", 0.95)))
    assert writer.calls >= 1
    return writer


def test_the_hint_writer_reads_the_events_and_never_a_protected_attempts(tmp_path):
    paths, vault, repository = _hint_world(tmp_path)
    _attempt(paths.sqlite_path, "att_1", at="2026-10-10T09:00:00Z", correctness=0.0, tap=5)
    _attempt(paths.sqlite_path, "att_2", at="2026-10-11T09:00:00Z", correctness=1.0, hedge="hedged")
    _attempt(paths.sqlite_path, "att_exam", at="2026-10-11T10:00:00Z", correctness=0.0, tap=1,
             attempt_type="exam_attempt")
    writer = _ask_writer(vault, repository)
    block = writer.contexts[0]["learner_confidence"]
    assert block["version"] == CE.VERSION and block["note"] == CE.NOTE
    assert block["topics"][0]["events"] == [
        "2026-10-11: no tap; the grader read the answer as hedged; right",
        "2026-10-10: marked 5/5 sure; wrong",
    ]
    # The exam attempt contributes no event; its tap (a number, with no
    # question, answer or result) counts toward the stated limit, and 1 and 5
    # together span the scale, so no limit is stated.
    assert "1/5" not in json.dumps(block)
    assert "taps_so_far" not in block


def test_with_no_confidence_data_the_hint_writers_prompt_is_unchanged(tmp_path):
    paths, vault, repository = _hint_world(tmp_path)
    _attempt(paths.sqlite_path, "att_plain", at="2026-10-10T09:00:00Z", correctness=1.0)
    writer = _ask_writer(vault, repository)
    assert "learner_confidence" not in writer.contexts[0] and "learner_work" in writer.contexts[0]
    assert CE.VERSION not in writer.prompts[0]


def test_the_hint_writers_events_fail_closed_when_the_protection_cannot_be_read(tmp_path, monkeypatch):
    from learnloop import learner_protection

    paths, vault, repository = _vault(tmp_path)
    _attempt(paths.sqlite_path, "att_1", at="2026-10-10T09:00:00Z", correctness=0.0, tap=5)
    monkeypatch.setattr(learner_protection, "withheld_items",
                        lambda _vault, _repo: learner_protection.Withheld(available=False))
    assert CE.learner_events(vault, repository, learning_object_ids=[LO], before_iso="2027-01-01T00:00:00Z") is None


def test_a_held_grade_reads_held_for_review_in_the_events(tmp_path, monkeypatch):
    import learnloop.held_grades as held_grades

    paths, vault, repository = _vault(tmp_path)
    _attempt(paths.sqlite_path, "att_held", at="2026-10-10T09:00:00Z", correctness=0.4321, tap=4)
    real = held_grades.held_for_review_attempts
    monkeypatch.setattr(held_grades, "held_for_review_attempts",
                        lambda connection, ids=None: frozenset({"att_held"}) | real(connection, ids))
    block = CE.learner_events(vault, repository, learning_object_ids=[LO], before_iso="2027-01-01T00:00:00Z")
    assert block["topics"][0]["events"] == ["2026-10-10: marked 4/5 sure; held for review (no score yet)"]
    assert "0.43" not in json.dumps(block)
    assert block["taps_so_far"] == "your taps so far are all 4 (1 tap)"


# -- the tutor ----------------------------------------------------------------------------


def _tutor_context(vault, repository, context: str):
    from learnloop.tutor.tutor_qa import _build_context

    return _build_context(vault, repository, context=context, question_md="Why is F(1/2) the answer?",
                          candidates=[], thread=[], item=vault.practice_items[ITEM], attempt=None, note=None,
                          note_id=None, now_iso="2027-01-01T00:00:00Z")


def test_the_tutor_reads_the_events_in_practice_contexts(tmp_path):
    from learnloop.tutor.ai_contracts import tutor_qa_prompt

    paths, vault, repository = _vault(tmp_path)
    _attempt(paths.sqlite_path, "att_1", at="2026-10-10T09:00:00Z", correctness=0.0, tap=5)
    _attempt(paths.sqlite_path, "att_exam", at="2026-10-11T09:00:00Z", correctness=1.0, tap=2,
             attempt_type="exam_attempt")
    context = _tutor_context(vault, repository, "practice")
    assert context.learner_confidence["topics"][0]["events"] == ["2026-10-10: marked 5/5 sure; wrong"]
    assert "marked 5/5 sure; wrong" in tutor_qa_prompt(context)
    assert "2/5" not in tutor_qa_prompt(context)


def test_with_no_confidence_data_the_tutor_context_renders_and_hashes_as_before(tmp_path):
    from dataclasses import asdict

    from learnloop.tutor.ai_contracts import tutor_context_payload, tutor_qa_prompt
    from learnloop.tutor.tutor_qa import _tutor_context_hash

    paths, vault, repository = _vault(tmp_path)
    _attempt(paths.sqlite_path, "att_plain", at="2026-10-10T09:00:00Z", correctness=1.0)
    context = _tutor_context(vault, repository, "practice")
    assert context.learner_confidence is None
    before = asdict(context)
    before.pop("learner_confidence")
    assert tutor_context_payload(context) == before
    expected = hashlib.sha256(json.dumps(before, sort_keys=True, separators=(",", ":"), default=str)
                              .encode("utf-8")).hexdigest()
    assert _tutor_context_hash(context) == expected
    assert "learner_confidence" not in tutor_qa_prompt(context)


# -- the history-aware diagnoser ------------------------------------------------------------


def test_the_diagnosers_history_and_current_attempt_carry_the_events(tmp_path):
    from learnloop.diagnosis.split.context import _render_attempt
    from learnloop.diagnosis.split.history import VaultHistoryStore, learning_object_neighborhood
    from learnloop.diagnosis.split.live import current_attempt_for, current_confidence

    paths, vault, repository = _vault(tmp_path)
    _attempt(paths.sqlite_path, "att_1", at="2026-10-10T09:00:00Z", correctness=0.0, tap=5)
    _attempt(paths.sqlite_path, "att_2", at="2026-10-11T09:00:00Z", correctness=1.0, hedge="hedged")
    _attempt(paths.sqlite_path, "att_3", at="2026-10-12T09:00:00Z", correctness=1.0)
    store = VaultHistoryStore(vault, repository)
    by_id = {attempt.attempt_id: attempt for attempt in store.all_attempts()}
    assert by_id["att_1"].confidence_event == "marked 5/5 sure; wrong" and by_id["att_1"].answer_confidence == 5
    assert by_id["att_2"].confidence_event == "no tap; the grader read the answer as hedged; right"
    assert by_id["att_3"].confidence_event is None
    neighborhood = learning_object_neighborhood(vault, LO)
    assert _render_attempt(by_id["att_1"], neighborhood, with_answer=False)["confidence"] == "marked 5/5 sure; wrong"
    assert "confidence" not in _render_attempt(by_id["att_3"], neighborhood, with_answer=False)

    # The diagnosed attempt: a blind record whose criteria read the answer as hedged.
    _attempt(paths.sqlite_path, "att_now", at="2026-10-13T09:00:00Z", correctness=0.0, tap=4)
    record = {"rubric_score": 0, "max_points": 4.0,
              "criteria": [{"criterion_id": "correctness", "points_awarded": 0, "learner_confidence": "hedged"}]}
    attempt = {"id": "att_now", "practice_item_id": ITEM, "created_at": "2026-10-13T09:00:00Z",
               "learner_answer_md": "x", "answer_confidence": 4}
    block = current_confidence(repository, attempt, record)
    assert block["event"] == "marked 4/5 sure; the grader read the answer as hedged; wrong"
    assert block["taps_so_far"] == "your taps so far are all 4–5 (2 taps)"
    current = current_attempt_for(vault, attempt, record, repository)
    assert current.render()["confidence"]["event"] == block["event"]


def test_with_no_confidence_data_the_diagnosers_current_attempt_renders_as_before(tmp_path):
    from learnloop.diagnosis.split.live import current_attempt_for

    paths, vault, repository = _vault(tmp_path)
    _attempt(paths.sqlite_path, "att_now", at="2026-10-13T09:00:00Z", correctness=1.0)
    record = {"rubric_score": 4, "max_points": 4.0,
              "criteria": [{"criterion_id": "correctness", "points_awarded": 4, "learner_confidence": "absent"}]}
    attempt = {"id": "att_now", "practice_item_id": ITEM, "created_at": "2026-10-13T09:00:00Z",
               "learner_answer_md": "x"}
    with_repository = current_attempt_for(vault, attempt, record, repository)
    assert with_repository.confidence is None and "confidence" not in with_repository.render()
    assert with_repository.render() == current_attempt_for(vault, attempt, record).render()


# -- never the blind grader -----------------------------------------------------------------


def test_the_blind_grader_never_reads_a_tap_or_a_hedge_read(tmp_path):
    from dataclasses import fields

    from learnloop.attempts.blind_grading import BlindGradingContext, blind_grading_context, blind_grading_prompt

    paths, vault, repository = _vault(tmp_path)
    _attempt(paths.sqlite_path, "att_prior", at="2026-10-10T09:00:00Z", correctness=0.0, tap=5, hedge="hedged")
    _attempt(paths.sqlite_path, "att_new", at="2026-10-11T09:00:00Z", correctness=None, tap=5)
    prompt = blind_grading_prompt(blind_grading_context(vault, vault.practice_items[ITEM], attempt_id="att_new",
                                                        learner_answer_md="F(1/2) = 1/4"))
    for marker in ("marked 5/5", CE.VERSION, "taps so far", "hedge read", "answer_confidence"):
        assert marker not in prompt, marker
    assert not any("confidence" in field.name and field.name != "grader_confidence"
                   for field in fields(BlindGradingContext))


@pytest.mark.parametrize("relative", ["attempts/blind_grading.py", "attempts/grading.py"])
def test_no_grader_module_imports_the_confidence_events(relative):
    tree = ast.parse((SRC / relative).read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            names.add(node.module or "")
            names.update(f"{node.module}.{alias.name}" for alias in node.names)
        elif isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
    assert not any("confidence_events" in name for name in names)
