"""Reader RW5d P4b: the teacher's manipulatives (spec_reader_show_me_figures_v1 §6.5, §7.1, §10.4;
spec_teacher_v1 §8.2; docs/reviews/reader-rw5d-p4b-teacher-visuals.md).

A teacher turn's ``visual`` becomes a ``FigureRequestV1`` with origin ``teacher`` built by the figure
service (grammar and sketch tiers), shown in the lesson with the figure's own predictions suppressed;
plan nodes carry planned visuals hit by the same input hash; ``teacher.visuals`` off keeps TE1's prompt
and turn schema byte for byte; held-out inputs are refused before any call; a figure never reaches the
grader. Every model is a fake (``TeacherFake``, ``AuthorFake``); no network.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from learnloop.figures import service as FS
from learnloop.teacher import service as S
from learnloop.teacher import visuals as V
from learnloop.vault.loader import load_vault
from tests.figure_fixtures import AuthorFake, flagship
from tests.teacher_fakes import TeacherFake, build_teacher_vault, check_turn, context_of, plan_turn

#: TE1's turn schema and doctrine as they stood at main 1a33bb5db3 (before RW5d P4b), pinned: with
#: teacher.visuals off the teacher is sent exactly these.
TE1_SCHEMA_SHA256 = "9668bbc1796bd73e2169c6a402a8b5c656906cff03c75ce20f587eb3ba042dc0"
TE1_DOCTRINE_SHA256 = "ecec5db5b07d2ceb878fbfc578a547c70011a7dc8cf2b25f6418475062d296ea"
GOAL = "Let the learner move lambda while p stays at 0.3; watch the mass left of zero."
FIGURE_WORDS = "WOMBATFIGURE how the mass splits around zero"


def _rows(repository, sql, params=()):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(sql, params).fetchall()]


def _spec(**changes):
    """The flagship figure (with its own predictions), claims dropped (this vault has no §5.4)."""

    base = {"source_claims": [], "assumptions": [{"text": "lambda > 0", "span_id": None, "quote": None}],
            "demonstrates": FIGURE_WORDS}
    return flagship(**{**base, **changes})


def _aliases(context):
    return [p["alias"] for s in context["brief"]["sources"].get("sections", []) for p in s.get("passages", [])]


def visual_turn(context, *, goal=GOAL, prediction=True):
    turn = {"message": "Here only lambda is yours to move.",
            "visual": {"goal": goal, "anchors": _aliases(context)[:1], "planned_node": None}}
    if prediction:
        turn["prediction"] = {"node": "n1", "prompt": "What happens to the left mass as lambda grows?",
                              "choices": []}
    return turn


def _clients(fake, builder):
    return S.Clients(teacher=lambda: fake, grading=lambda: fake, grading_source="ai", figures=builder)


def _builder(paths, repository, author, *, calls=None, spawn=None):
    def build(request):
        if calls is not None:
            calls.append(request)
        return FS.build_figure(load_vault(paths.root), repository, request, author_client=author, spawn_rich=spawn)

    return build


def _open(tmp_path, turns, *, author=None, config=None, builder=True, calls=None):
    from tests.ux_phase1_support import set_config

    paths, repository = build_teacher_vault(tmp_path / "vault")
    if config:
        set_config(paths.root, config)
    author = author if author is not None else AuthorFake([_spec()])
    fake = TeacherFake(turns)
    build = _builder(paths, repository, author, calls=calls) if builder else None
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=_clients(fake, build))
    return paths, repository, fake, author, view, build


def _schema_sha(model):
    from learnloop.ai.strict_schema import strict_output_schema

    return hashlib.sha256(json.dumps(strict_output_schema(model), sort_keys=True).encode()).hexdigest()


# --- a visual turn builds a figure ------------------------------------------------------------------


def test_a_visual_turn_builds_a_teacher_figure_shown_inline_with_its_predictions_suppressed(tmp_path):
    paths, repository, fake, author, view, _build = _open(tmp_path, [visual_turn])
    lesson_id = view["lesson_id"]
    # The teacher was offered the visual: its paragraph, its prompt version and the schema with ``visual``.
    assert fake.result_models == [V.turn_model(True)]
    prompt = fake.prompts[0][1]
    assert f"prompt_version: {V.VISUALS_PROMPT_VERSION}" in prompt and "Instruments over description" in prompt
    # One author call: the teacher's goal, written by the teacher, grounded in the delivered passage.
    assert author.calls == 1
    sent = author.contexts[0]
    assert sent["learner_request"] == {"text": GOAL, "written_by": "teacher"}
    assert sent["grounding"] == "retrieved"
    alias = _aliases(fake.contexts[0])[0]
    passage = fake.contexts[0]["brief"]["sources"]["sections"][0]["passages"][0]
    assert passage["alias"] == alias
    # The request as the figure service recorded it: origin and author teacher, the lesson as host, the
    # lesson's policy under caller kind teacher, grammar and sketch only, no home in the Reader.
    (request,) = _rows(repository, "SELECT origin, goal_author, caller_kind, policy, host_ref_json, tiers_allowed_json, "
                                   "reading_at_json, figure_id FROM figure_requests")
    assert request[:4] == ("teacher", "teacher", "teacher", "reading")
    assert json.loads(request[4]) == {"lesson_id": lesson_id, "node_id": "n1"}
    assert set(json.loads(request[5])) <= set(FS.LESSON_TIERS)
    assert request[6] is None
    (figure,) = _rows(repository, "SELECT id, origin, extraction_id, spec_json FROM interactive_figures")
    assert figure[0] == request[7] and figure[1] == "teacher" and figure[2] is None
    assert json.loads(figure[3])["predictions"], "the stored figure has its own predictions"
    # Shown inline in the turn, with no predictions (the teacher posed one instead).
    entries = [entry for entry in view["feed"] if entry["kind"] == "figure"]
    assert len(entries) == 1 and entries[0]["status"] == V.SHOWN and entries[0]["node"] == "n1"
    shown = entries[0]["figure"]
    assert shown["figure_id"] == figure[0] and shown["predictions"] == [] and shown["host"] == "lesson"
    assert shown["goal_author"] == "teacher" and shown["demonstrates"] == FIGURE_WORDS
    assert [entry["kind"] for entry in view["feed"]] == ["message", "prediction", "figure"]
    assert view["open_prediction"]["prompt"].startswith("What happens")
    assert any(entry["kind"] == "figure" for entry in view["shown_now"])
    # The lesson view reads the same (no model call).
    again = S.view_lesson(load_vault(paths.root), repository, lesson_id)
    assert [e["figure"]["figure_id"] for e in again["feed"] if e["kind"] == "figure"] == [figure[0]]
    assert author.calls == 1
    # The next teacher call is told what was shown and what the learner can move.
    S.take_turn(load_vault(paths.root), repository, lesson_id=lesson_id, action="answer_prediction",
                payload={"answer": "it shrinks"}, clients=_clients(fake, _build))
    told = [entry["visual"] for entry in fake.contexts[-1]["transcript"] if "visual" in entry]
    assert told and told[0]["status"] == V.SHOWN and told[0]["figure"]["demonstrates"] == FIGURE_WORDS
    assert told[0]["figure"]["controls"] and {"name", "label", "min", "max", "default"} <= set(told[0]["figure"]["controls"][0])
    # Formative nothing: no figure prediction from a lesson; the receipt-to-be lists the figure.
    assert _rows(repository, "SELECT COUNT(*) FROM figure_predictions") == [(0,)]


def test_the_figure_never_reaches_the_grader_and_is_never_a_help_row(tmp_path):
    def visual_and_check(context):
        turn = visual_turn(context, prediction=False)
        turn.update({k: v for k, v in check_turn().items() if k in ("check", "requests")})
        return turn

    def landed_and_close(context):
        return {"message": "Done.", "requests": [{"action": "close", "close_reason": "goal_reached",
                                                  "recap": "Retrieve later: eigenvalues solve det(A - tI) = 0."}]}

    paths, repository, fake, author, view, build = _open(tmp_path, [plan_turn, visual_and_check, landed_and_close])
    lesson_id = view["lesson_id"]
    view = S.take_turn(load_vault(paths.root), repository, lesson_id=lesson_id, action="reply",
                       payload={"text": "go"}, clients=_clients(fake, build))
    assert view["open_check"] is not None
    assert [e["status"] for e in view["feed"] if e["kind"] == "figure"] == [V.SHOWN]
    # Built while the check was open: the lesson's policy bound to the minted item.
    assert _rows(repository, "SELECT policy FROM figure_requests") == [("assisted_practice",)]
    view = S.take_turn(load_vault(paths.root), repository, lesson_id=lesson_id, action="answer_check",
                       payload={"answer": "det(A - tI) = 0", "tap": 3}, clients=_clients(fake, build))
    assert view["closed"]
    grading = [prompt for purpose, prompt in fake.prompts if purpose != "teacher_turn"]
    assert fake.grading_contexts or grading
    assert all("WOMBATFIGURE" not in str(c) for c in fake.grading_contexts)
    assert all("WOMBATFIGURE" not in p for p in grading)
    # Never a help row (the figure is teaching material, not help on the check) and never evidence.
    assert _rows(repository, "SELECT COUNT(*) FROM help_assists WHERE assist_kind = 'figure'") == [(0,)]
    receipt = json.loads(_rows(repository, "SELECT receipt_json FROM lesson_receipts")[0][0])
    assert [entry["status"] for entry in receipt["visuals"]] == [V.SHOWN]
    assert receipt["doctrine"]["sha256"] == TE1_DOCTRINE_SHA256


def test_figure_words_that_give_the_open_checks_solution_away_are_not_shown(tmp_path):
    solution = "The eigenvalues are the roots of the characteristic polynomial det(A - tI) = 0."

    def visual_and_check(context):
        turn = visual_turn(context, prediction=False)
        turn.update({k: v for k, v in check_turn(solution=solution).items() if k in ("check", "requests")})
        return turn

    author = AuthorFake([_spec(demonstrates=solution)])
    paths, repository, fake, author, view, _ = _open(tmp_path, [visual_and_check], author=author)
    entries = [e for e in view["feed"] if e["kind"] == "figure"]
    assert entries and entries[0]["status"] == V.WITHHELD and entries[0]["figure"] is None
    (payload,) = [json.loads(row[0]) for row in _rows(
        repository, "SELECT p.payload_json FROM lesson_turns t JOIN lesson_turn_payloads p ON p.turn_id = t.id "
                    "WHERE t.action = 'visual'")]
    assert payload["status"] == V.WITHHELD and payload["code"] == "open_check_solution"


def test_a_shown_figures_words_count_as_the_lessons_displayed_text(tmp_path):
    """A vault question the figure reproduces is exposure: the receipt lists it and no delayed check
    picks it (the delayed checks read the lesson's displayed text)."""

    from tests.teacher_fakes import ITEMS

    question = ITEMS["pi_eig_1"][1]

    def close(context):
        return {"message": "Done.", "requests": [{"action": "close", "close_reason": "goal_reached",
                                                  "recap": "Retrieve later: eigenvalues solve det(A - tI) = 0."}]}

    author = AuthorFake([_spec(demonstrates=question)])
    paths, repository, fake, author, view, build = _open(tmp_path, [visual_turn, close], author=author)
    assert [e["status"] for e in view["feed"] if e["kind"] == "figure"] == [V.SHOWN]
    S.take_turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="answer_prediction",
                payload={"answer": "it shrinks"}, clients=_clients(fake, build))
    receipt = json.loads(_rows(repository, "SELECT receipt_json FROM lesson_receipts")[0][0])
    assert "pi_eig_1" in receipt["exposure"]["shown_items"]
    assert all(check.get("item_id") != "pi_eig_1" for check in receipt["delayed_checks"])


# --- planned visuals ------------------------------------------------------------------------------


def test_a_planned_visual_is_the_identical_request_and_hits_the_same_figure(tmp_path):
    def plan_with_visual(context):
        turn = plan_turn(context)
        turn["requests"][0]["plan"][0]["visual"] = {"goal": GOAL, "anchors": _aliases(context)[:1]}
        return turn

    def step(context):
        return {"message": "Step one.", "visual": {"goal": "", "anchors": [], "planned_node": "n1"}}

    paths, repository, fake, author, view, build = _open(tmp_path, [plan_with_visual, step])
    plan = _rows(repository, "SELECT outline_json FROM lesson_plans")
    assert json.loads(plan[0][0])[0]["visual"]["goal"] == GOAL
    view = S.take_turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="reply",
                       payload={"text": "go"}, clients=_clients(fake, build))
    assert author.calls == 1
    # A second request with the same goal and passages (another lesson step asking for it): reused.
    fake.turns = [step]
    S.take_turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="reply",
                payload={"text": "again"}, clients=_clients(fake, build))
    assert author.calls == 1
    requests = _rows(repository, "SELECT figure_id, host_ref_json FROM figure_requests ORDER BY created_at, id")
    assert len(requests) == 2 and requests[0][0] == requests[1][0]
    assert all(json.loads(row[1])["node_id"] == "n1" for row in requests)


def test_a_visual_the_lesson_cannot_build_is_refused_back_to_the_teacher(tmp_path):
    def unknown_anchor(context):
        return {"message": "Look.", "visual": {"goal": GOAL, "anchors": ["S99"], "planned_node": None}}

    def no_plan(context):
        return {"message": "Look.", "visual": {"goal": "", "anchors": [], "planned_node": "n9"}}

    def both(context):
        return {"message": "Look.", "visual": {"goal": GOAL, "anchors": _aliases(context)[:1], "planned_node": "n1"}}

    paths, repository, fake, author, view, _ = _open(tmp_path, [unknown_anchor, no_plan, both])
    assert view["closed"] and view["close_reason"] == "teacher_contract_failure"
    details = [json.loads(row[0]).get("detail") for row in _rows(
        repository, "SELECT p.payload_json FROM lesson_turns t JOIN lesson_turn_payloads p ON p.turn_id = t.id "
                    "WHERE t.action = 'teacher_turn' ORDER BY t.seq")]
    assert "S99" in details[0] and "no planned visual" in details[1] and "not both" in details[2]
    assert author.calls == 0 and _rows(repository, "SELECT COUNT(*) FROM figure_requests") == [(0,)]


# --- the switch -----------------------------------------------------------------------------------


def test_switch_off_keeps_te1s_prompt_and_turn_schema_byte_identical(tmp_path):
    from learnloop.ai.transport import render_structured_prompt
    from learnloop.teacher.contracts import PROMPT_VERSION, TeacherTurnV1
    from learnloop.teacher.doctrines import doctrine_hash, doctrine_text

    assert _schema_sha(TeacherTurnV1) == TE1_SCHEMA_SHA256 and doctrine_hash() == TE1_DOCTRINE_SHA256
    assert _schema_sha(V.turn_model(True)) != TE1_SCHEMA_SHA256
    cases = (({("teacher", "visuals"): False}, True), ({("figures", "show_me_enabled"): False}, True),
             ({("figures", "enabled"): False}, True), (None, False))
    for index, (config, builder) in enumerate(cases):
        paths, repository, fake, author, view, _ = _open(tmp_path / f"case{index}", [plan_turn],
                                                         config=config, builder=builder)
        assert fake.result_models == [TeacherTurnV1], config
        purpose, prompt = fake.prompts[0]
        rebuilt = render_structured_prompt("LearnLoop lesson: you are the teacher", PROMPT_VERSION,
                                           {"instructions": doctrine_text(), "context": context_of(prompt)},
                                           context_tail_fields=("transcript",))
        assert prompt == rebuilt, config
        assert "Instruments over description" not in prompt and "visual" not in prompt.split('"context"')[0]
        stored = [json.loads(row[0]) for row in _rows(
            repository, "SELECT p.payload_json FROM lesson_turns t JOIN lesson_turn_payloads p ON p.turn_id = t.id "
                        "WHERE t.action = 'teacher_turn'")]
        assert stored and all("visual" not in entry["turn"] and "visuals" not in entry for entry in stored)
        assert all("visual" not in node for node in json.loads(
            _rows(repository, "SELECT outline_json FROM lesson_plans")[0][0]))
        assert author.calls == 0


def test_switching_visuals_off_hides_a_lessons_figures_and_stops_a_pending_one(tmp_path):
    from tests.ux_phase1_support import set_config

    paths, repository, fake, author, view, build = _open(tmp_path, [visual_turn])
    assert [e["status"] for e in view["feed"] if e["kind"] == "figure"] == [V.SHOWN]
    set_config(paths.root, {("teacher", "visuals"): False})
    view = S.view_lesson(load_vault(paths.root), repository, view["lesson_id"])
    assert not [e for e in view["feed"] if e["kind"] == "figure"]
    # The figure service refuses a lesson's figure with the switch off, before any call.
    request = V.figure_request(S.load_state(repository, view["lesson_id"]),
                               {"goal": GOAL, "anchors": ["S1"], "node": None})
    with pytest.raises(FS.FigureRefused) as refused:
        FS.build_figure(load_vault(paths.root), repository, request, author_client=author)
    assert refused.value.code == "teacher_visuals_disabled" and author.calls == 1


# --- exam protection ------------------------------------------------------------------------------


def test_held_out_inputs_are_refused_before_any_call(tmp_path, monkeypatch):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    author = AuthorFake([_spec()])
    fake = TeacherFake([visual_turn])
    held = []
    original = FS.keys_withheld

    def withheld(vault, repo, keys):
        # The anchor's passage became held-out material between the brief and the build.
        if any(tuple(key) in held for key in keys):
            return "That passage is kept for your exam."
        return original(vault, repo, keys)

    monkeypatch.setattr(FS, "keys_withheld", withheld)
    vault = load_vault(paths.root)
    calls = []
    build = _builder(paths, repository, author, calls=calls)

    def wrapped(request):
        held.extend(tuple(key) for key in request.grounding_keys)
        return build(request)

    view = S.open_lesson(vault, repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=_clients(fake, wrapped))
    entries = [e for e in view["feed"] if e["kind"] == "figure"]
    assert entries == [{"kind": "figure", "node": "n1", "goal": GOAL, "status": V.WITHHELD, "figure": None}]
    assert author.calls == 0 and _rows(repository, "SELECT COUNT(*) FROM interactive_figures") == [(0,)]
    assert not view["closed"]  # the lesson goes on without the figure


def test_a_shown_figure_held_out_since_is_no_longer_shown(tmp_path, monkeypatch):
    paths, repository, fake, author, view, _ = _open(tmp_path, [visual_turn])
    assert [e["status"] for e in view["feed"] if e["kind"] == "figure"] == [V.SHOWN]
    monkeypatch.setattr(FS, "figure_withheld", lambda vault, repo, figure_id: True)
    again = S.view_lesson(load_vault(paths.root), repository, view["lesson_id"])
    assert [(e["status"], e["figure"]) for e in again["feed"] if e["kind"] == "figure"] == [(V.WITHHELD, None)]


def test_the_teacher_origin_is_the_lesson_services_only(tmp_path):
    from learnloop.source_retrieval.policy import CallerContext

    paths, repository = build_teacher_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    base = dict(extraction_id=None, span_ids=[], origin="teacher", goal_text=GOAL, goal_author="teacher",
                host_ref={"lesson_id": "les_x"}, grounding_keys=[("ext_book", "s1")])
    for changes in ({"caller": None}, {"caller": CallerContext(kind="reader")},
                    {"caller": CallerContext(kind="teacher", ref="les_x"), "host_ref": {}},
                    {"caller": CallerContext(kind="teacher", ref="les_x"), "grounding_keys": None},
                    {"caller": CallerContext(kind="teacher", ref="les_x"), "goal_author": "learner"},
                    {"caller": CallerContext(kind="teacher", ref="les_x"), "span_ids": ["s1"],
                     "extraction_id": "ext_book"}):
        request = FS.FigureRequest(**{**base, **changes})
        with pytest.raises(FS.FigureRefused) as refused:
            FS.check_request(vault, repository, request)
        assert refused.value.code == "validation_error", changes
    # A "not right?" of a lesson's figure is never made from an RPC (its revision has no teacher caller).
    revision = FS.FigureRequest(**{**base, "caller": None, "supersedes_id": "fig_x"})
    with pytest.raises(FS.FigureRefused):
        FS.check_request(vault, repository, revision)
    assert "teacher" in FS.SERVICE_ORIGINS and "teacher" not in FS.RESERVED_ORIGINS


def test_a_lesson_figure_never_spawns_a_rich_job(tmp_path, monkeypatch):
    from tests.ux_phase1_support import set_config

    # Every rich tier ready on this machine: a Reader press with a spawner would put them on the menu.
    monkeypatch.setattr(FS.RICH, "tiers_allowed", lambda vault, sketch=False: ("grammar", "sketch", "js_animation",
                                                                               "manim"))
    spawned = []
    paths, repository = build_teacher_vault(tmp_path / "vault")
    set_config(paths.root, {("figures", "rich_tiers_enabled"): True})
    author = AuthorFake([_spec()])
    fake = TeacherFake([visual_turn])
    build = _builder(paths, repository, author, spawn=lambda payload: spawned.append(payload) or "job_x")
    S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                  clients=_clients(fake, build))
    assert author.calls == 1 and spawned == []
    (tiers,) = _rows(repository, "SELECT tiers_allowed_json FROM figure_requests")
    assert "manim" not in json.loads(tiers[0]) and "js_animation" not in json.loads(tiers[0])
    from learnloop.figures import routes as R

    version_line = author.prompts[0].splitlines()[1]
    assert version_line.startswith("prompt_version:") and R.RICH_SUFFIX not in version_line


def test_lesson_view_never_builds_a_pending_figure(tmp_path, monkeypatch):
    """An action interrupted after its accepted turn: ``lesson.view`` recovers without any model call
    (the visual waits); the next action builds it."""

    paths, repository = build_teacher_vault(tmp_path / "vault")
    author = AuthorFake([_spec()])
    fake = TeacherFake([visual_turn])
    build = _builder(paths, repository, author)
    original = S._visual

    def interrupted(*args, **kwargs):
        raise KeyboardInterrupt  # the process stops between the accepted turn and its figure

    monkeypatch.setattr(S, "_visual", interrupted)
    with pytest.raises(KeyboardInterrupt):
        S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                      clients=_clients(fake, build))
    monkeypatch.setattr(S, "_visual", original)
    (lesson_id,) = _rows(repository, "SELECT id FROM lessons")[0]
    viewed = S.view_lesson(load_vault(paths.root), repository, lesson_id)
    assert author.calls == 0 and not [e for e in viewed["feed"] if e["kind"] == "figure"]
    fake.turns = [{"message": "Go on."}]
    resumed = S.take_turn(load_vault(paths.root), repository, lesson_id=lesson_id, action="answer_prediction",
                          payload={"answer": "it shrinks"}, clients=_clients(fake, build))
    assert author.calls == 1
    assert [e["status"] for e in resumed["feed"] if e["kind"] == "figure"] == [V.SHOWN]


def test_lesson_turn_builds_the_visual_through_the_figure_service(tmp_path, monkeypatch):
    """The desktop RPC: ``lesson.turn`` attaches the sidecar's figure builder (the figure route the
    Reader's builds use, with the injected author in tests)."""

    from learnloop_sidecar.handlers import lesson as H

    paths, repository = build_teacher_vault(tmp_path / "vault")
    fake = TeacherFake([visual_turn])
    author = AuthorFake([_spec()])
    monkeypatch.setattr(H, "_clients", lambda ctx, vault: S.Clients(teacher=lambda: fake, grading=lambda: fake))

    class Ctx:
        grading_provider_override = None
        figure_author_client = author

        def require_vault(self):
            return load_vault(paths.root), repository

        def reload(self, maintenance=True):
            pass

    opened = H.lesson_turn(Ctx(), H.LessonTurnInput(action="open", entry="learning_object",
                                                    learning_object_ids=["lo_eigen"]))
    figures = [entry for entry in opened["feed"] if entry["kind"] == "figure"]
    assert len(figures) == 1 and figures[0]["status"] == V.SHOWN
    assert figures[0]["figure"]["predictions"] == [] and figures[0]["figure"]["goalAuthor"] == "teacher"
    assert author.calls == 1


def test_teacher_checks_and_the_grader_never_import_figure_code():
    """Structural: the lesson-check minting and grading (and the delayed checks) import no figure code,
    so a figure can never reach certification (pinned in pyproject's import-linter contract too)."""

    import ast
    from pathlib import Path

    import learnloop.teacher as T

    root = Path(T.__file__).parent
    for name in ("checks.py", "delayed.py", "guards.py"):
        tree = ast.parse((root / name).read_text(encoding="utf-8"))
        imported = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        imported |= {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        assert not any(module.startswith(("learnloop.figures", "learnloop.teacher.visuals")) for module in imported)
