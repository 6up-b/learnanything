"""Teacher exam-question guard (spec_teacher_v1 §9.3 As built; docs/reviews/teacher-exam-question-guard.md).

Found at TE2's landing smoke: a teacher turn quoting an exam-reserved QUESTION (its stem) was accepted and shown,
because the output guards covered answer keys only. Every guarded field (the displayed ones, the logged ids, a posed
check's solution and rubric, a figure's words) is now also compared with the questions kept for an exam or held out,
by the matcher FG1's probes and TE2's typed goals use (``practice_leakage.reserved_findings``, its span kinds); the
inline grader's feedback likewise. Every model is a fake (``TeacherFake``); no network.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.teacher import guards as G
from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml
from tests.teacher_fakes import TeacherFake, _item, build_teacher_vault, check_turn, clients, close_turn, plan_turn

T0 = datetime(2026, 11, 6, 15, 0, tzinfo=UTC)
#: An exam-reserved question whose stem shares no words with its key (the smoke's shape: the key guard can't see it).
EXAM_ITEM = "pi_exam_stem"
EXAM_STEM = ("A lighthouse keeper turns the plane a quarter turn with the matrix whose rows are (0, -1) and (1, 0); "
             "which real vectors does it leave on their own line?")
EXAM_KEY = "jackal heron: none"
#: A held-out (not exam-pool) item: made from the held-out unit ``lay_held``.
HELD_ITEM = "pi_held_stem"
HELD_STEM = ("On the review sheet a matrix has trace 16.0 and determinant 63.0; name both of its "
             "eigenvalues and say which one is larger.")
HELD_KEY = "lynx osprey: seven and nine"
#: An exam-reserved question whose whole stem is shorter than the matcher's span: a short common phrase.
SHORT_ITEM = "pi_exam_short"
SHORT_STEM = "Define a basis."
#: Ordinary teaching sentences sharing a few words with each stem (fewer than the matcher's span), and the short
#: stem's words.
ORDINARY = ("A quarter turn of the plane leaves no real vector on its own line, so it has no real eigenvalue. "
            "A matrix's trace is the sum of its eigenvalues, and its determinant is their product. "
            "Later we define a basis carefully.")
DISTINCTIVE = ("lighthouse keeper", "review sheet")
#: Codex review F1: an exam-reserved question shorter than the matcher's span but carrying a distinctive number (the
#: matcher's own numeric rule), with an unrelated key. Shown whole, it is the question.
NUMBER_ITEM = "pi_exam_short_number"
NUMBER_STEM = "Factor 9871 into primes."
NUMBER_KEY = "badger wren: two factors"
#: Codex review F2: an exam-reserved question a turn can split between its message and its check, each half shorter
#: than the matcher's span.
SPLIT_ITEM = "pi_exam_split"
SPLIT_STEM = "For polynomial x³−7x+2, identify every real root."
SPLIT_SETUP, SPLIT_QUESTION = "For polynomial x³−7x+2,", "identify every real root."
#: Codex re-review F1: an exam-reserved question shorter than the matcher's span, words only (no distinctive number).
#: Posed (its own sentence or clause, or asked), it is the question; inside a teaching sentence it is a phrase.
CIPHER_ITEM = "pi_exam_cipher"
CIPHER_STEM = "Decrypt QEBNRFZH using Caesar cipher."


def _rows(repository, sql, params=()):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(sql, params).fetchall()]


def build_guard_vault(root, *, version=None):
    """``build_teacher_vault`` plus an exam-reserved item and a held-out item whose stems differ from their keys."""

    from learnloop.ingest.locators import BLOCK_SPAN_V1, format_block_span

    paths, repository = build_teacher_vault(root, version=version)
    write_yaml(paths.practice_item_path("linear-algebra", EXAM_ITEM), _item(EXAM_ITEM, "lo_eigen", EXAM_STEM, EXAM_KEY))
    write_yaml(paths.practice_item_path("linear-algebra", SHORT_ITEM),
               _item(SHORT_ITEM, "lo_eigen", SHORT_STEM, "otter newt: a spanning independent set"))
    write_yaml(paths.practice_item_path("linear-algebra", NUMBER_ITEM),
               _item(NUMBER_ITEM, "lo_eigen", NUMBER_STEM, NUMBER_KEY))
    write_yaml(paths.practice_item_path("linear-algebra", SPLIT_ITEM),
               _item(SPLIT_ITEM, "lo_eigen", SPLIT_STEM, "marten plover: three"))
    write_yaml(paths.practice_item_path("linear-algebra", CIPHER_ITEM),
               _item(CIPHER_ITEM, "lo_eigen", CIPHER_STEM, "stoat lark: a plain word"))
    (goal_id,) = _rows(repository, "SELECT goal_id FROM exam_pool_items LIMIT 1")[0]
    repository.insert_exam_pool_items([
        {"id": "epi_cipher", "goal_id": goal_id, "practice_item_id": CIPHER_ITEM,
         "reserved_at": "2026-10-30T00:00:00Z"},
        {"id": "epi_stem", "goal_id": goal_id, "practice_item_id": EXAM_ITEM, "reserved_at": "2026-10-30T00:00:00Z"},
        {"id": "epi_short", "goal_id": goal_id, "practice_item_id": SHORT_ITEM, "reserved_at": "2026-10-30T00:00:00Z"},
        {"id": "epi_number", "goal_id": goal_id, "practice_item_id": NUMBER_ITEM,
         "reserved_at": "2026-10-30T00:00:00Z"},
        {"id": "epi_split", "goal_id": goal_id, "practice_item_id": SPLIT_ITEM, "reserved_at": "2026-10-30T00:00:00Z"},
    ])
    (span,) = _rows(repository, "SELECT span_id FROM source_document_blocks WHERE extraction_id = 'ext_lay' "
                                "AND text LIKE '%HELDOUTSENTINEL%'")[0]
    held = _item(HELD_ITEM, "lo_det", HELD_STEM, HELD_KEY)
    held["provenance"] = {"origin": "human", "source_refs": [{
        "ref_type": "canonical_source", "ref_id": "ext_lay", "locator": format_block_span("ext_lay", span),
        "locator_scheme": BLOCK_SPAN_V1}]}
    write_yaml(paths.practice_item_path("linear-algebra", HELD_ITEM), held)
    return paths, repository


class _Lesson:
    def __init__(self, tmp_path, turns, *, fake=None, version=None, config=None):
        from tests.ux_phase1_support import set_config

        self.paths, self.repository = build_guard_vault(tmp_path / "vault", version=version)
        if config:
            set_config(self.paths.root, config)
        self.fake = fake if fake is not None else TeacherFake()
        self.fake.turns = list(turns)
        self.minute = 0
        self.views = []
        self.view = S.open_lesson(self.vault(), self.repository, entry="learning_object",
                                  learning_object_ids=["lo_eigen"], clients=clients(self.fake), clock=self.clock())
        self.views.append(self.view)
        self.lesson_id = self.view["lesson_id"]

    def vault(self):
        return load_vault(self.paths.root)

    def clock(self):
        self.minute += 1
        return FrozenClock(T0 + timedelta(minutes=self.minute))

    def act(self, action, payload=None, *, turns=None):
        if turns is not None:
            self.fake.turns = list(turns)
        self.view = S.take_turn(self.vault(), self.repository, lesson_id=self.lesson_id, action=action,
                                payload=payload or {}, clients=clients(self.fake), clock=self.clock())
        self.views.append(self.view)
        return self.view

    def teacher_turns(self):
        return [(validation, json.loads(payload)) for validation, payload in _rows(
            self.repository, "SELECT t.validation, p.payload_json FROM lesson_turns t "
                             "JOIN lesson_turn_payloads p ON p.turn_id = t.id "
                             "WHERE t.action = 'teacher_turn' ORDER BY t.seq")]

    def everything_shown(self):
        """Every displayed record, view, receipt and prompt the lesson produced (never the withheld raw payload)."""

        state = S.load_state(self.repository, self.lesson_id)
        shown = [json.dumps(view) for view in self.views]
        shown.append(json.dumps(S.view(self.vault(), self.repository, self.lesson_id)))
        shown.extend(S.displayed_texts(state))
        shown.extend(row[0] for row in _rows(self.repository, "SELECT receipt_json FROM lesson_receipts"))
        shown.append(self.fake.all_prompts())
        shown.append(json.dumps(S.transcript(state)))
        return "\n".join(shown)


def _never_shown(lesson, stem):
    shown = lesson.everything_shown()
    normalized = " ".join(re.sub(r"[^a-z0-9 ]+", " ", shown.lower()).split())
    assert stem not in shown
    for phrase in DISTINCTIVE:
        assert phrase not in shown.lower() and phrase not in normalized


def test_the_matcher_reads_both_items_as_withheld_questions(tmp_path):
    from learnloop.learner_protection import WITHHELD_EXAM, withheld_items

    paths, repository = build_guard_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    withheld = withheld_items(vault, repository)
    from learnloop.content.authoring.practice_leakage import reserved_findings

    assert {withheld.reason(item) for item in (EXAM_ITEM, HELD_ITEM, SHORT_ITEM)} == {WITHHELD_EXAM}
    reserved = G.reserved_book(vault, repository)
    assert not reserved.unreadable
    assert G.quotes_reserved(f"Try this: {EXAM_STEM}", reserved)
    assert G.quotes_reserved(f"Try this: {HELD_STEM}", reserved)
    # Part of a stem, at the matcher's span, is enough (the smoke's turn quoted the question, not always whole).
    assert G.quotes_reserved("so which real vectors does it leave on their own line?", reserved)
    # A short common phrase, a few shared words, a lone number: none trips it.
    assert not G.quotes_reserved(ORDINARY, reserved)
    assert not G.quotes_reserved("on their own line", reserved)
    assert reserved_findings("Here the trace is 16.0.", reserved.questions)  # the matcher's numeric finding
    assert not G.quotes_reserved("Here the trace is 16.0.", reserved)
    # The short stem: the matcher finds it whole, but inside a teaching sentence a phrase shorter than its span is not
    # a question shown (posed on its own, it is: re-review F1).
    assert reserved_findings("Later we define a basis carefully.", reserved.questions)
    assert not G.quotes_reserved("Later we define a basis carefully.", reserved)
    verdict = G.reserved_guard(EXAM_STEM, reserved)
    assert verdict.reason == "reserved_question" and "lighthouse" not in str(verdict.detail)


def _quoting(field, stem):
    """A first turn putting ``stem`` in one guarded field (otherwise ``plan_turn``)."""

    def turn(context):
        out = plan_turn(context)
        check = {k: v for k, v in check_turn().items() if k in ("check", "requests")}
        if field == "message":
            out["message"] = f"Here is a nice one to try: {stem}"
        elif field == "choice":
            out["choices"] = ["Go on", stem]
        elif field == "plan":
            out["requests"][0]["plan"][1]["statement"] = stem
        elif field == "prediction":
            out["prediction"] = {"node": "n1", "prompt": stem, "choices": []}
        elif field in ("check", "check.committed_solution", "check.rubric"):
            out.update(check)
            out["requests"] = [*plan_turn(context)["requests"], *check["requests"]]
            if field == "check":
                out["check"] = {**out["check"], "question": stem}
            elif field == "check.committed_solution":
                out["check"] = {**out["check"], "committed_solution": stem}
            else:
                out["check"] = {**out["check"], "rubric": [{"id": "char_poly", "fact": stem, "points": 2}]}
        elif field == "recap":
            out["requests"].append({"action": "close", "close_reason": "goal_reached", "recap": stem})
        elif field == "plan.id":
            out["requests"][0]["plan"][0]["id"] = stem[:80]
        return out

    return turn


@pytest.mark.parametrize("field", ["message", "choice", "plan", "prediction", "check", "check.committed_solution",
                                   "check.rubric", "recap"])
def test_a_turn_quoting_an_exam_reserved_stem_is_withheld_and_shown_nowhere(tmp_path, field):
    lesson = _Lesson(tmp_path, [_quoting(field, EXAM_STEM), plan_turn])
    turns = lesson.teacher_turns()
    assert [validation for validation, _ in turns] == ["withheld", "ok"]
    withheld = turns[0][1]
    assert withheld["reason"] == "reserved_question"
    location = withheld["detail"].split(":", 1)[0]
    assert location.split("[")[0].startswith(field.split(".")[0])
    assert "lighthouse" not in withheld["detail"]
    # The refused turn's raw payload is recorded as TE1 records any withheld turn (nothing reads it).
    assert EXAM_STEM in json.dumps(withheld["turn"])
    # The teacher was told, by location, and re-prompted.
    refusals = [e for e in lesson.fake.contexts[1]["transcript"] if e.get("refused")]
    assert refusals and refusals[0]["refused"] == "reserved_question"
    lesson.act("stop", turns=[close_turn()])
    assert lesson.view["closed"]
    _never_shown(lesson, EXAM_STEM)


def test_a_logged_field_quoting_a_reserved_stem_is_withheld_by_location(tmp_path):
    """The identifier guard's fields (never shown, copied into rows and receipts): a plan node's id, a probe's
    reading."""

    from learnloop.algorithm_versions import TEACHER_PROBES_ALGORITHM_VERSION
    from tests.test_teacher_te2_probes import probe_turn

    lesson = _Lesson(tmp_path / "plan", [_quoting("plan.id", EXAM_STEM), plan_turn])
    (withheld, ok) = lesson.teacher_turns()
    assert withheld[0] == "withheld" and ok[0] == "ok"
    assert withheld[1]["reason"] == "reserved_question" and withheld[1]["detail"].startswith("requests[0].plan[0].id: ")
    lesson.act("stop", turns=[close_turn()])
    _never_shown(lesson, EXAM_STEM)

    probe = _Lesson(tmp_path / "probe", [lambda c: probe_turn(c, readings=(f"thinks {EXAM_STEM}",)), plan_turn],
                    version=TEACHER_PROBES_ALGORITHM_VERSION)
    (withheld, ok) = probe.teacher_turns()
    assert withheld[0] == "withheld" and withheld[1]["reason"] == "reserved_question"
    assert withheld[1]["detail"].startswith("requests[1].readings[0]: ")
    assert _rows(probe.repository, "SELECT COUNT(*) FROM followup_generation_jobs") == [(0,)]


def test_a_held_out_items_stem_is_withheld_likewise(tmp_path):
    lesson = _Lesson(tmp_path, [_quoting("message", HELD_STEM), plan_turn])
    assert [v for v, _ in lesson.teacher_turns()] == ["withheld", "ok"]
    assert lesson.teacher_turns()[0][1]["reason"] == "reserved_question"
    lesson.act("stop", turns=[close_turn()])
    _never_shown(lesson, HELD_STEM)


def test_an_ordinary_sentence_sharing_a_few_words_with_a_reserved_stem_is_not_withheld(tmp_path):
    def ordinary(context):
        return {**plan_turn(context), "message": ORDINARY}

    lesson = _Lesson(tmp_path, [ordinary])
    assert [v for v, _ in lesson.teacher_turns()] == ["ok"]
    assert any(entry.get("text") == ORDINARY for entry in lesson.view["feed"])


def test_unreadable_protection_fails_closed(tmp_path, monkeypatch):
    from learnloop.content.authoring import practice_leakage

    def unreadable(*_args, **_kwargs):
        raise RuntimeError("protection store unreadable")

    monkeypatch.setattr(practice_leakage, "reserved_questions", unreadable)
    lesson = _Lesson(tmp_path, [plan_turn, plan_turn, plan_turn])
    turns = lesson.teacher_turns()
    assert turns and all(v == "withheld" and p["reason"] == "protection_unreadable" for v, p in turns)
    assert not any(entry.get("kind") == "message" for entry in lesson.view["feed"])
    assert lesson.view["closed"] and lesson.view["close_reason"] == "teacher_contract_failure"


def test_reserved_book_is_unreadable_when_withheld_items_is(tmp_path, monkeypatch):
    from learnloop import learner_protection as LP

    paths, repository = build_guard_vault(tmp_path / "vault")
    monkeypatch.setattr(LP, "withheld_items", lambda _v, _r: LP.Withheld(available=False))
    reserved = G.reserved_book(load_vault(paths.root), repository)
    assert reserved.unreadable
    assert G.reserved_guard("anything at all", reserved).reason == "protection_unreadable"
    assert G.shown_feedback("Right: det(A - tI) = 0.", reserved) is None


class FeedbackGrader(TeacherFake):
    """The blind grader with feedback (``TeacherFake`` gives none)."""

    def __init__(self, feedback, **kwargs):
        super().__init__(**kwargs)
        self.feedback = feedback

    def run_blind_grading_proposal(self, context):
        proposal = super().run_blind_grading_proposal(context)
        return proposal.model_copy(update={"feedback_md": self.feedback})


@pytest.mark.parametrize("quotes", [True, False])
def test_the_inline_graders_feedback_quoting_a_reserved_stem_is_not_shown(tmp_path, quotes):
    feedback = f"Right. Compare: {EXAM_STEM}" if quotes else "Right: the eigenvalues solve det(A - tI) = 0."
    lesson = _Lesson(tmp_path, [plan_turn], fake=FeedbackGrader(feedback))
    lesson.act("reply", {"text": "Go."}, turns=[check_turn()])
    lesson.act("answer_check", {"answer": "det(A - tI) = 0", "tap": 4}, turns=[close_turn()])
    (result,) = [json.loads(row[0]) for row in _rows(
        lesson.repository, "SELECT p.payload_json FROM lesson_turns t JOIN lesson_turn_payloads p "
                           "ON p.turn_id = t.id WHERE t.action = 'check_result'")]
    assert result["result"] == "right"  # the grade stands either way
    if quotes:
        assert result["grader_feedback"] is None
        _never_shown(lesson, EXAM_STEM)
    else:
        assert result["grader_feedback"] == feedback
        assert any(entry.get("grader_feedback") == feedback for entry in lesson.view["feed"])


def test_a_lesson_probes_grader_feedback_quoting_a_reserved_stem_is_not_shown(tmp_path):
    from tests.teacher_fakes import RESERVED_SENTINEL
    from tests.test_teacher_te2_probes import _Lesson as ProbeLesson
    from tests.test_teacher_te2_probes import probe_turn

    stem = f"{RESERVED_SENTINEL}: compute it."
    lesson = ProbeLesson(tmp_path, [probe_turn])
    lesson.generate()
    lesson.look()
    grader = FeedbackGrader(f"Partly. The exam asks: {stem}")
    lesson.fake = grader
    lesson.act("answer_probe", {"answer": "(1, 0), stretched by three", "tap": 4}, turns=[close_turn()])
    (result,) = [json.loads(row[0]) for row in lesson.rows(
        "SELECT p.payload_json FROM lesson_turns t JOIN lesson_turn_payloads p ON p.turn_id = t.id "
        "WHERE t.action = 'probe_result'")]
    assert result["grader_feedback"] is None
    assert "RESERVEDSENTINEL" not in json.dumps(lesson.view) and "RESERVEDSENTINEL" not in grader.all_prompts()


def test_a_figure_quoting_a_reserved_stem_is_not_shown(tmp_path, monkeypatch):
    import tests.test_reader_rw5d_p4b_teacher_visuals as RV
    from learnloop.teacher import visuals as V
    from tests.figure_fixtures import AuthorFake

    monkeypatch.setattr(RV, "build_teacher_vault", build_guard_vault)
    author = AuthorFake([RV._spec(demonstrates=EXAM_STEM)])
    paths, repository, fake, author, view, _ = RV._open(tmp_path, [lambda c: RV.visual_turn(c, prediction=False)],
                                                        author=author)
    entries = [e for e in view["feed"] if e["kind"] == "figure"]
    assert entries and entries[0]["status"] == V.WITHHELD and entries[0]["figure"] is None
    (payload,) = [json.loads(row[0]) for row in _rows(
        repository, "SELECT p.payload_json FROM lesson_turns t JOIN lesson_turn_payloads p ON p.turn_id = t.id "
                    "WHERE t.action = 'visual'")]
    assert payload["code"] == "reserved_question" and "shown_text" not in payload
    assert "lighthouse" not in json.dumps(view).lower()


def test_a_whole_short_reserved_question_with_a_distinctive_number_counts(tmp_path):
    """Codex review F1: a whole stem shorter than the matcher's span counts when it carries a distinctive number the
    matcher reports for it; a short common phrase, a lone number and a near miss still don't."""

    paths, repository = build_guard_vault(tmp_path / "vault")
    reserved = G.reserved_book(load_vault(paths.root), repository)
    assert G.quotes_reserved(NUMBER_STEM, reserved)
    assert G.quotes_reserved(f"Here is one to try: {NUMBER_STEM}", reserved)
    assert G.reserved_guard(NUMBER_STEM, reserved).reason == "reserved_question"
    assert G.shown_feedback(f"Right. Compare: {NUMBER_STEM}", reserved) is None
    for ordinary in ("Later we define a basis carefully.", "We factor whole numbers into primes.",
                     "Here 9871 is only a number.", "Factor 9872 into primes.", ORDINARY):
        assert not G.quotes_reserved(ordinary, reserved), ordinary
        assert G.shown_feedback(ordinary, reserved) == ordinary


@pytest.mark.parametrize("stem", [NUMBER_STEM, CIPHER_STEM])
def test_a_teacher_check_posing_a_short_reserved_question_is_withheld(tmp_path, stem):
    lesson = _Lesson(tmp_path, [_quoting("check", stem), plan_turn])
    turns = lesson.teacher_turns()
    assert [validation for validation, _ in turns] == ["withheld", "ok"]
    assert turns[0][1]["reason"] == "reserved_question" and turns[0][1]["detail"].startswith("check: ")
    lesson.act("stop", turns=[close_turn()])
    shown = lesson.everything_shown()
    assert stem not in shown and "factor 9871" not in shown.lower() and "qebnrfzh" not in shown.lower()


@pytest.mark.parametrize("stem", [NUMBER_STEM, CIPHER_STEM])
def test_the_graders_feedback_quoting_a_short_reserved_question_is_not_shown(tmp_path, stem):
    feedback = f"Right. Compare: {stem}"
    lesson = _Lesson(tmp_path, [plan_turn], fake=FeedbackGrader(feedback))
    lesson.act("reply", {"text": "Go."}, turns=[check_turn()])
    lesson.act("answer_check", {"answer": "det(A - tI) = 0", "tap": 4}, turns=[close_turn()])
    (result,) = [json.loads(row[0]) for row in _rows(
        lesson.repository, "SELECT p.payload_json FROM lesson_turns t JOIN lesson_turn_payloads p "
                           "ON p.turn_id = t.id WHERE t.action = 'check_result'")]
    assert result["result"] == "right" and result["grader_feedback"] is None
    assert stem not in lesson.everything_shown()


def test_a_whole_short_reserved_question_posed_on_its_own_counts_without_a_number(tmp_path):
    """Codex re-review F1: a whole stem shorter than the matcher's span, words only, counts when the text poses it (it
    stands as its own sentence or clause, or the text asks it). Inside a teaching sentence it is a phrase, not a
    question shown: the common-phrase negatives stay accepted."""

    paths, repository = build_guard_vault(tmp_path / "vault")
    reserved = G.reserved_book(load_vault(paths.root), repository)
    for posed in (CIPHER_STEM, f"Here is one to try: {CIPHER_STEM}", "Try “Decrypt QEBNRFZH using Caesar cipher”.",
                  "Can you decrypt QEBNRFZH using Caesar cipher?", "First, decrypt QEBNRFZH using Caesar cipher. Then "
                  "check it.", "Decrypt QEBNRFZH using Caesar cipher", SHORT_STEM, "Next: define a basis."):
        assert G.quotes_reserved(posed, reserved), posed
        assert G.reserved_guard(posed, reserved).reason == "reserved_question"
        assert G.shown_feedback(f"Right. {posed}", reserved) is None
    for ordinary in ("Later we define a basis carefully.", "Now we define a basis.", "To define a basis, list vectors.",
                     "We decrypt messages using a Caesar cipher.", ORDINARY):
        assert not G.quotes_reserved(ordinary, reserved), ordinary
        assert G.shown_feedback(ordinary, reserved) == ordinary


def test_a_short_reserved_question_counts_when_an_ordinary_item_shows_its_number(tmp_path):
    """Codex re-review F1: an ordinary item showing 9871 removes the matcher's numeric finding (what an ordinary item
    shows can't leak alone), but the whole reserved stem still carries that number: it counts, posed or inside a
    sentence."""

    from learnloop.content.authoring.practice_leakage import reserved_findings

    paths, repository = build_guard_vault(tmp_path / "vault")
    write_yaml(paths.practice_item_path("linear-algebra", "pi_ordinary_9871"),
               _item("pi_ordinary_9871", "lo_det", "Is 9871 divisible by seven?", "heron lemur: no"))
    reserved = G.reserved_book(load_vault(paths.root), repository)
    assert not [f for f in reserved_findings(NUMBER_STEM, reserved.questions) if f["kind"] == "numeric"]
    assert G.quotes_reserved(NUMBER_STEM, reserved)
    assert G.quotes_reserved("Then factor 9871 into primes by trial division.", reserved)
    assert G.shown_feedback(f"Right. Compare: {NUMBER_STEM}", reserved) is None
    for ordinary in ("Here 9871 is only a number.", "Factor 9872 into primes.", "We factor whole numbers into primes."):
        assert not G.quotes_reserved(ordinary, reserved), ordinary


def _split(message, question):
    def turn(context):
        check = check_turn()
        return {**plan_turn(context), "message": message,
                "check": {**check["check"], "question": question},
                "requests": [*plan_turn(context)["requests"], *check["requests"]]}

    return turn


def test_a_reserved_question_split_between_message_and_check_is_withheld(tmp_path):
    """Codex review F2: each half is shorter than the matcher's span and passes alone; the turn as the learner reads it
    shows the whole question, so the assembled turn is screened too."""

    paths, repository = build_guard_vault(tmp_path / "vault")
    reserved = G.reserved_book(load_vault(paths.root), repository)
    assert not G.quotes_reserved(SPLIT_SETUP, reserved) and not G.quotes_reserved(SPLIT_QUESTION, reserved)
    assert G.quotes_reserved(f"{SPLIT_SETUP}\n{SPLIT_QUESTION}", reserved)

    lesson = _Lesson(tmp_path / "lesson", [_split(SPLIT_SETUP, SPLIT_QUESTION), plan_turn])
    turns = lesson.teacher_turns()
    assert [validation for validation, _ in turns] == ["withheld", "ok"]
    assert turns[0][1]["reason"] == "reserved_question" and turns[0][1]["detail"].startswith("turn: ")
    lesson.act("stop", turns=[close_turn()])
    normalized = " ".join(re.sub(r"[^a-z0-9 ]+", " ", lesson.everything_shown().lower()).split())
    assert "identify every real root" not in normalized


def test_half_a_reserved_question_beside_an_ordinary_check_is_accepted(tmp_path):
    lesson = _Lesson(tmp_path, [_split(SPLIT_SETUP, "For a 2 by 2 matrix A, what equation gives its eigenvalues?")])
    assert [validation for validation, _ in lesson.teacher_turns()] == ["ok"]


def _script(lesson):
    lesson.act("reply", {"text": "Go."}, turns=[check_turn()])
    lesson.act("answer_check", {"answer": "det(A - tI) = 0", "tap": 4}, turns=[plan_turn])
    lesson.act("stop", turns=[close_turn()])
    return lesson


def test_a_lesson_with_no_reserved_text_is_byte_identical_with_the_guard_off(tmp_path, monkeypatch):
    """Nothing in the lesson quotes a reserved question: every row, payload, receipt, view and prompt is the same as
    with the reserved-question guard replaced by one that never fires (main's guards)."""

    def capture(lesson):
        def norm(text):
            text = text.replace(lesson.lesson_id, "LESSON")
            # Ids aside (the lesson's, its minted check item, ULIDs and turn ids): every byte else.
            return re.sub(r"pi_lesson_[0-9a-f]+|\b[0-9A-Z]{26}\b|\b[a-z]+_[0-9a-z]{26}\b", "ID", text)

        rows = _rows(lesson.repository, "SELECT t.seq, t.actor, t.action, t.validation, t.created_at, p.payload_json "
                                        "FROM lesson_turns t LEFT JOIN lesson_turn_payloads p ON p.turn_id = t.id "
                                        "WHERE t.lesson_id = ? ORDER BY t.seq", (lesson.lesson_id,))
        receipts = [norm(row[0]) for row in _rows(lesson.repository, "SELECT receipt_json FROM lesson_receipts")]
        return ([tuple(norm(str(v)) for v in row) for row in rows], receipts,
                [norm(json.dumps(view, sort_keys=True)) for view in lesson.views],
                [norm(prompt) for _purpose, prompt in lesson.fake.prompts])

    feedback = "Right: the eigenvalues solve det(A - tI) = 0."
    guarded = capture(_script(_Lesson(tmp_path / "guarded", [plan_turn], fake=FeedbackGrader(feedback))))
    with monkeypatch.context() as patch:
        patch.setattr(G, "reserved_book", lambda _vault, _repository: G.ReservedBook())
        off = capture(_script(_Lesson(tmp_path / "off", [plan_turn], fake=FeedbackGrader(feedback))))
    assert guarded == off
    assert feedback in str(guarded[0])
    assert len(guarded[0]) > 8 and guarded[1] and len(guarded[3]) >= 4
