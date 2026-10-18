"""Adaptive hints H2a: the Codex review's findings F1-F9 (docs/reviews/hints-h2a-codex-review.md).

Each test reproduces one finding on the tree the review read and pins its
fix. Fakes only (no model is reached): the writer and chooser are
``tests.hint_fakes``'s, the map model ``tests.approach_map_fakes``'s.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import closing

import pytest

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.db.repositories import Repository
from learnloop.hints import discriminating as D
from learnloop.hints import service as S
from learnloop.hints.contracts import Target, check_output
from learnloop.hints.state import assemble_state
from learnloop.hints.writer import HintWriterOutputV1, empty_output
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.approach_map_fakes import add_attempt, edge, good_map, node
from tests.hint_fakes import ITEM, WORK, ChooserFake, WriterFake, assists, good_answer, hint_vault, prefer, \
    reveals, store_map

ARGMAX = '[hints]\nchoice_policy = "argmax"\n'
SELF_GRADE = {"criterionPoints": {"cdf": 2, "value": 0}, "confidence": 3}


def _setup(tmp_path, *, config: str = "", map_payload: dict | None = None, with_map: bool = True):
    paths = hint_vault(tmp_path, config=ARGMAX + config)
    if with_map:
        store_map(paths, map_payload)
    return paths, load_vault(paths.root), Repository.attach(paths.sqlite_path)


def _ask(vault, repository, option: str, answers=(), *, writer=None, deliver: bool = True, **overrides):
    writer = writer or WriterFake(list(answers))
    values = {"practice_item_id": ITEM, "session_id": "s1", "submission_id": "k1", "work_md": WORK}
    values.update(overrides)
    chooser = ChooserFake(prefer(option, 0.9))
    result = S.request_hint(vault, repository, S.HintRequestV1(**values), writer_client=writer,
                            chooser_client_factory=lambda: chooser, seed="r")
    if deliver and result.status == S.READY:
        S.deliver(repository, str(result.assist_id))
    return result, writer, chooser


def _longer() -> dict:
    """The CDF item on a four-node route ``g -> a -> b -> goal``."""

    payload = good_map()
    payload["nodes"] = [node("g", "given", "Read the density", "f(x) = 2x on [0, 1]"),
                        node("a", "step", "Set up the integral", "int_0^x 2t dt", value="x^2"),
                        node("b", "step", "Find the CDF on the support", "$F(x) = x^2$ on [0, 1]"),
                        node("goal", "goal", "Evaluate the CDF at the point", "P(X ≤ 1/2) = 1/4",
                             conclusion="1/4")]
    payload["edges"] = [edge("g", "a"), edge("a", "b"), edge("b", "goal")]
    payload["routes"][0]["path"] = ["g", "a", "b", "goal"]
    return payload


def _three_routes() -> dict:
    """The reference route and two model routes to the goal."""

    payload = good_map()
    payload["nodes"] += [node("comp", "step", "Use the complement", "P(X > 1/2) = 3/4"),
                         node("sym", "step", "Use the area of a triangle", "area = x * 2x / 2")]
    payload["edges"] += [edge("g", "comp"), edge("comp", "goal"), edge("g", "sym"), edge("sym", "goal")]
    payload["routes"] += [
        {"id": "r_comp", "name": "Complement route", "path": ["g", "comp", "goal"], "origin": "model",
         "learner_attempt_ids": []},
        {"id": "r_area", "name": "Area route", "path": ["g", "sym", "goal"], "origin": "model",
         "learner_attempt_ids": []}]
    return payload


# ---------------------------------------------------------------------------
# F1: polling a completed submission never exposes an unrecorded hint
# ---------------------------------------------------------------------------

def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _sidecar(tmp_path):
    paths = hint_vault(tmp_path, config=ARGMAX)
    store_map(paths)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    ctx.hints_inline = False
    ctx.hint_seed = "e"
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    return paths, ctx, session


def _request(ctx, session, option: str, writer):
    ctx.hint_writer_client = writer
    ctx.hint_chooser_client = ChooserFake(prefer(option, 0.9))
    return _call(ctx, "practice.request_hint", {"sessionId": session, "practiceItemId": ITEM,
                                                "submissionId": "k1", "answerMd": WORK})


def _submit(ctx, session):
    return _call(ctx, "submit_attempt", {
        "sessionId": session, "practiceItemId": ITEM, "answerMd": WORK, "attemptType": "independent_attempt",
        "hintsUsed": 0, "selfGrade": SELF_GRADE, "submissionId": "k1"})


def _attempt(paths, attempt_id: str) -> dict:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return dict(connection.execute("SELECT * FROM practice_attempts WHERE id = ?", (attempt_id,)).fetchone())


def _assert_refused(polled: dict) -> None:
    result = polled["result"]
    assert polled["state"] == "done"
    assert result["shown"] is False and result["hintMd"] is None
    assert (result["status"], result["reason"]) == ("unavailable", "submission_complete")


@pytest.mark.parametrize("option", ["next_step@L3", "walkthrough@L5"])
def test_f1_a_hint_finished_before_the_submit_and_polled_after_it_is_never_shown(tmp_path, option):
    paths, ctx, session = _sidecar(tmp_path)
    writer = WriterFake()
    ctx.hint_writer_client = writer
    ctx.hint_chooser_client = ChooserFake(prefer(option, 0.9))
    params = {"sessionId": session, "practiceItemId": ITEM, "submissionId": "k1", "answerMd": WORK}
    if option.endswith("L5"):
        params["takenLevel"] = 5
    job = _call(ctx, "practice.request_hint", params)
    assert ctx.hint_jobs.get(job["jobId"]).done.wait(30)
    attempt = _attempt(paths, _submit(ctx, session)["attemptId"])
    [row] = assists(paths.sqlite_path)
    assert row["attempt_id"] == attempt["id"] and row["shown"] == 0  # H0 attached the prepared row
    polled = _call(ctx, "practice.hint_job", {"jobId": job["jobId"]})
    _assert_refused(polled)
    # Polling again keeps it refused; the row stays unshown and no reveal is written.
    _assert_refused(_call(ctx, "practice.hint_job", {"jobId": job["jobId"]}))
    [row] = assists(paths.sqlite_path)
    assert row["shown"] == 0 and row["shown_at"] is None
    assert reveals(paths.sqlite_path) == []
    assert (attempt["hints_used"], attempt["primed"]) == (0, 0)


def test_f1_a_hint_written_after_the_submit_is_never_shown_into_the_committed_attempt(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    gate = threading.Event()
    job = _request(ctx, session, "next_step@L3", WriterFake(gate=gate))
    assert job["state"] == "pending"
    attempt_id = _submit(ctx, session)["attemptId"]
    gate.set()
    assert ctx.hint_jobs.get(job["jobId"]).done.wait(30)
    [row] = assists(paths.sqlite_path)
    assert row["attempt_id"] is None  # inserted after the attach: nothing took it
    _assert_refused(_call(ctx, "practice.hint_job", {"jobId": job["jobId"]}))
    [row] = assists(paths.sqlite_path)
    assert row["shown"] == 0 and reveals(paths.sqlite_path) == []
    assert _attempt(paths, attempt_id)["hints_used"] == 0


def test_f1_an_open_submission_still_delivers_and_counts(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    job = _request(ctx, session, "next_step@L3", WriterFake())
    assert ctx.hint_jobs.get(job["jobId"]).done.wait(30)
    polled = _call(ctx, "practice.hint_job", {"jobId": job["jobId"]})
    assert polled["result"]["status"] == "ready" and polled["result"]["shown"] is True
    assert polled["result"]["hintMd"]
    assert _attempt(paths, _submit(ctx, session)["attemptId"])["hints_used"] == 1


# ---------------------------------------------------------------------------
# F2: a smaller step toward a waypoint two or more edges away
# ---------------------------------------------------------------------------

def _waypoint_at_b(context):
    payload = good_answer(context)
    payload["placement"] = {**payload["placement"], "reached_node_id": "g", "route_id": "r_ref"}
    payload["target_node_id"] = "b"
    return payload


def _step_to(target: str):
    def answer(context):
        payload = good_answer(context)
        payload["placement"] = {**payload["placement"], "reached_node_id": "g", "route_id": "r_ref"}
        payload["target_node_id"] = target
        return payload
    return answer


def test_f2_a_smaller_step_toward_a_far_waypoint_targets_the_adjacent_node_on_the_way(tmp_path):
    paths, vault, repository = _setup(tmp_path, map_payload=_longer())
    item = vault.practice_items[ITEM]
    state = assemble_state(vault, repository, item, session_id="s1", submission_id="k9", work_md=WORK)
    output = HintWriterOutputV1.model_validate(_step_to("a")({"chosen": {"kind": "next_step", "level": 3},
                                                             "learner_work": WORK, "approach_map": True}))
    target = Target("next_step", 3, target_node_id="b", request="smaller_step")
    assert check_output(output, target=target, state=state, item=item).failures == []
    # The waypoint itself is two edges away: not a next step.
    at_b = output.model_copy(update={"target_node_id": "b"})
    assert "rule6_next_step_not_adjacent" in check_output(at_b, target=target, state=state, item=item).failures
    # Past the waypoint (or off the way to it) is not toward it.
    past = output.model_copy(update={"target_node_id": "goal"})
    assert "rule6_not_the_waypoint_target" in check_output(past, target=target, state=state, item=item).failures


def test_f2_the_service_serves_the_smaller_step_on_an_unchanged_draft(tmp_path):
    paths, vault, repository = _setup(tmp_path, map_payload=_longer())
    first, _w, _c = _ask(vault, repository, "waypoint@L3", answers=[_waypoint_at_b])
    assert first.status == S.READY and first.kind == "waypoint"
    assert assists(paths.sqlite_path)[0]["target_node_id"] == "b"
    second, writer, _c = _ask(vault, repository, "next_step@L3", request="smaller_step",
                              answered_assist_id=first.assist_id, answers=[_step_to("a")])
    assert writer.calls == 1, writer.contexts[-1].get("previous_answer_problems")
    assert (second.status, second.kind, second.level) == (S.READY, "next_step", 3)
    row = assists(paths.sqlite_path)[1]
    assert row["target_node_id"] == "a"
    assert json.loads(row["contract_failures_json"])["outcome"] == "served"


# ---------------------------------------------------------------------------
# F3: what stands ends before the first questionable point
# ---------------------------------------------------------------------------

def _placed(state, item, *, stands: str, questionable: str, work: str):
    output = HintWriterOutputV1.model_validate(empty_output(
        placement={"route_id": "r_ref", "reached_node_id": "cdf", "stands_quote": stands,
                   "first_questionable_quote": questionable, "quotes": [stands or questionable]},
        route_id="r_ref", target_node_id="goal", hint_md="Look again at where your work goes next.",
        strategy="s"))
    return check_output(output, target=Target("next_step", 3), state=state, item=item).failures


def test_f3_a_checkpoint_after_the_first_questionable_point_is_refused(tmp_path):
    _paths, vault, repository = _setup(tmp_path)
    item = vault.practice_items[ITEM]
    first, second = WORK.splitlines()
    state = assemble_state(vault, repository, item, session_id="s1", submission_id="k9", work_md=WORK)
    # The early line questionable, the later dependent line cited as standing: disjoint quotes.
    assert "rule2_past_first_questionable" in _placed(state, item, stands=second, questionable=first, work=WORK)
    # The right order passes.
    assert "rule2_past_first_questionable" not in _placed(state, item, stands=first, questionable=second,
                                                          work=WORK)


def test_f3_repeated_text_is_placed_at_its_first_occurrence(tmp_path):
    _paths, vault, repository = _setup(tmp_path)
    item = vault.practice_items[ITEM]
    work = "F(1/2) + 1\nF(x) = x^2 on [0, 1]\nso P(X <= 1/2) = F(1/2) + 1"
    state = assemble_state(vault, repository, item, session_id="s1", submission_id="k9", work_md=work)
    # "F(1/2) + 1" is first questionable at line 1, so line 2 cannot stand after it.
    assert "rule2_past_first_questionable" in _placed(state, item, stands="F(x) = x^2 on [0, 1]",
                                                      questionable="F(1/2) + 1", work=work)
    # A standing quote that also occurs before the questionable point stands there.
    repeated = "F(x) = x^2 on [0, 1]\nso P(X <= 1/2) = F(1/2) + 1\nF(x) = x^2 on [0, 1]"
    state = assemble_state(vault, repository, item, session_id="s1", submission_id="k9", work_md=repeated)
    assert "rule2_past_first_questionable" not in _placed(state, item, stands="F(x) = x^2 on [0, 1]",
                                                          questionable="F(1/2) + 1", work=repeated)


# ---------------------------------------------------------------------------
# F4: a valid learner route is kept, whichever route it is
# ---------------------------------------------------------------------------

_NEXT = {"r_ref": "cdf", "r_comp": "comp", "r_area": "sym"}


def _routed(state, item, *, placed: str, served: str, target: Target, valid: bool = True):
    work = state.work_md
    output = HintWriterOutputV1.model_validate(empty_output(
        placement={"route_id": placed, "reached_node_id": "g", "stands_quote": work.splitlines()[0],
                   "quotes": [work.splitlines()[0]], "work_valid_so_far": valid},
        route_id=served, target_node_id=_NEXT[served], hint_md="Carry on from your first line.", strategy="s"))
    return check_output(output, target=target, state=state, item=item).failures


def test_f4_an_alternative_learner_route_is_not_swapped_for_another_alternative(tmp_path):
    _paths, vault, repository = _setup(tmp_path, map_payload=_three_routes())
    item = vault.practice_items[ITEM]
    state = assemble_state(vault, repository, item, session_id="s1", submission_id="k9", work_md=WORK)
    for target in (Target("next_step", 3), Target("next_step", 3, request="feedback", shortcut="learner_route")):
        assert "rule4_left_learner_route" in _routed(state, item, placed="r_comp", served="r_area", target=target)
        assert "rule4_left_learner_route" not in _routed(state, item, placed="r_comp", served="r_comp",
                                                         target=target)
    # Reference to an alternative leaves the learner's route too.
    assert "rule4_left_learner_route" in _routed(state, item, placed="r_ref", served="r_comp",
                                                 target=Target("next_step", 3))
    # An invalid route may change; the book's way may take the reference route.
    assert "rule4_left_learner_route" not in _routed(state, item, placed="r_comp", served="r_area",
                                                     target=Target("next_step", 3), valid=False)
    assert _routed(state, item, placed="r_comp", served="r_ref",
                   target=Target("next_step", 3, reference_route=True, request="book_way")) == []


# ---------------------------------------------------------------------------
# F5: the writer's fallback never raises a reply's level
# ---------------------------------------------------------------------------

def test_f5_a_reply_to_a_level_2_hint_with_the_writer_down_is_not_served_at_level_3(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    first, _w, _c = _ask(vault, repository, "localize@L2")
    assert (first.status, first.level) == (S.READY, 2)
    down = WriterFake(provider_type="codex_sdk")
    second, _w, _c = _ask(vault, repository, "localize@L2", writer=down, request="feedback",
                          answered_assist_id=first.assist_id, feedback_shortcut="not_where_stuck")
    assert second.status == S.UNAVAILABLE and second.level is None and second.hint_md is None
    assert second.reason == "codex_refused" and down.calls == 0
    row = assists(paths.sqlite_path)[1]
    assert (row["hint_kind"], row["level"], row["counted_by"]) == (None, None, None)


@pytest.mark.parametrize("shortcut, served", [(None, True), ("not_where_stuck", True), ("notation", False),
                                              ("learner_route", False)])
def test_f5_a_level_3_reply_falls_back_only_where_the_shortcut_allows_an_authored_hint(tmp_path, shortcut,
                                                                                       served):
    _paths, vault, repository = _setup(tmp_path)
    first, _w, _c = _ask(vault, repository, "next_step@L3")
    down = WriterFake(provider_type="codex_sdk")
    second, _w, _c = _ask(vault, repository, "next_step@L3", writer=down, request="feedback",
                          answered_assist_id=first.assist_id, feedback_shortcut=shortcut)
    if served:
        assert (second.status, second.kind, second.level, second.reason) == (S.READY, "authored", 3,
                                                                              "codex_refused")
    else:
        assert second.status == S.UNAVAILABLE and second.hint_md is None and second.reason == "codex_refused"


# ---------------------------------------------------------------------------
# F6: every candidate is ranked against the same rivals
# ---------------------------------------------------------------------------

def _rivals(count: int = 3) -> list[D.Rival]:
    statements = ["Adds one to a CDF value", "Reads the CDF as the density", "Forgets the support"][:count]
    return [D.Rival(D.rival_id(text), text, "hypothesis", f"h{index}", "candidate")
            for index, text in enumerate(statements)]


def test_f6_a_candidate_missing_a_rival_is_not_ranked_above_a_complete_one():
    a, b, c = _rivals()
    incomplete = {"question_md": "Q1", "predictions": [{"rival_id": a.id, "answer": "1"},
                                                      {"rival_id": b.id, "answer": "0"}]}
    complete = {"question_md": "Q2", "predictions": [{"rival_id": a.id, "answer": "1"},
                                                    {"rival_id": b.id, "answer": "0"},
                                                    {"rival_id": c.id, "answer": "0"}]}
    ranked = D.rank_candidates([incomplete, complete], [a, b, c])
    assert [entry.question_md for entry in ranked] == ["Q2"]
    # The two-versus-one split under uniform weights over all three rivals.
    assert ranked[0].eig_nats == pytest.approx(0.6365, abs=1e-3)
    assert D.best_candidate(ranked).question_md == "Q2"


def test_f6_a_duplicate_or_unknown_prediction_is_refused():
    a, b, c = _rivals()
    duplicate = {"question_md": "Q1", "predictions": [{"rival_id": a.id, "answer": "1"},
                                                     {"rival_id": a.id, "answer": "2"},
                                                     {"rival_id": b.id, "answer": "0"},
                                                     {"rival_id": c.id, "answer": "0"}]}
    unknown = {"question_md": "Q2", "predictions": [{"rival_id": a.id, "answer": "1"},
                                                   {"rival_id": b.id, "answer": "0"},
                                                   {"rival_id": c.id, "answer": "0"},
                                                   {"rival_id": "rv_nope", "answer": "3"}]}
    assert D.rank_candidates([duplicate, unknown], [a, b, c]) == []


# ---------------------------------------------------------------------------
# F7: work that matches no route and is not clearly valid gets an approach question
# ---------------------------------------------------------------------------

def _unplaced(context):
    payload = good_answer(context)
    payload["placement"] = {**payload["placement"], "work_matches_a_route": False, "work_valid_so_far": False}
    return payload


def test_f7_unplaceable_work_gets_a_checked_approach_question_not_a_next_step(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    result, writer, _c = _ask(vault, repository, "next_step@L3", answers=[_unplaced])
    assert (result.status, result.kind, result.level) == (S.READY, "approach_question", 1)
    assert [context["chosen"]["kind"] for context in writer.contexts] == ["next_step", "approach_question"]
    assert result.reason == "unplaced_work"
    row = assists(paths.sqlite_path)[0]
    log = json.loads(row["contract_failures_json"])
    assert (log["drawn_kind"], log["served_kind"], log["reason"]) == ("next_step", "approach_question",
                                                                      "unplaced_work")
    assert (row["hint_kind"], row["level"]) == ("approach_question", 1)
    assert json.loads(row["drawn_option_json"])["option"] == "next_step@L3"


def test_f7_placeable_or_valid_work_keeps_the_drawn_kind(tmp_path):
    _paths, vault, repository = _setup(tmp_path)

    def valid_new(context):
        payload = good_answer(context)
        payload["placement"] = {**payload["placement"], "work_matches_a_route": False, "work_valid_so_far": True}
        return payload

    result, writer, _c = _ask(vault, repository, "next_step@L3", answers=[valid_new])
    assert (result.kind, writer.calls) == ("next_step", 1)


# ---------------------------------------------------------------------------
# F8: "from the book" needs verified grounding, which H2a's passages lack
# ---------------------------------------------------------------------------

PASSAGE = "Example 3.2. Let Y have density 3y^2 on [0, 1]. Then F(y) = y^3 and P(Y <= c) = c^3."


def test_f8_a_book_origin_on_an_unverified_passage_is_refused(tmp_path):
    _paths, vault, repository = _setup(tmp_path)
    item = vault.practice_items[ITEM]
    state = assemble_state(vault, repository, item, session_id="s1", submission_id="k9", work_md=WORK)
    state.worked_example_texts = [PASSAGE]
    book = HintWriterOutputV1.model_validate(empty_output(
        placement={"route_id": "r_ref", "reached_node_id": "cdf", "stands_quote": WORK.splitlines()[0],
                   "quotes": [WORK.splitlines()[0]]},
        route_id="r_ref", target_node_id="goal", strategy="p", source_origin="book", source_quote="density",
        hint_md="For a uniform variable on [0, 4], F(u) = u/4."))
    failures = check_output(book, target=Target("worked_parallel", 3), state=state, item=item).failures
    assert "worked_parallel_book_unverified" in failures
    ai = book.model_copy(update={"source_origin": "ai", "source_quote": ""})
    assert check_output(ai, target=Target("worked_parallel", 3), state=state, item=item).failures == []


def test_f8_the_writer_is_told_its_passages_are_unverified(tmp_path):
    from learnloop.hints.writer import build_prompt

    _paths, vault, repository = _setup(tmp_path)
    item = vault.practice_items[ITEM]
    state = assemble_state(vault, repository, item, session_id="s1", submission_id="k9", work_md=WORK)
    state.worked_example_texts = [PASSAGE]
    prompt = build_prompt(vault, item, state, Target("worked_parallel", 3))
    assert "unverified" in prompt and '"worked_examples_verified": false' in prompt


# ---------------------------------------------------------------------------
# F9: a learner's new correct route reaches the map after a hint is shown
# ---------------------------------------------------------------------------

def _merge_sidecar(tmp_path, maps: str):
    from tests.approach_map_fakes import MapFake, map_vault

    paths = map_vault(tmp_path, config=ARGMAX + "[hints.maps]\nbuild_on_serve=true\nenabled=true\n")
    store_map(paths)
    config = paths.root / "learnloop.toml"
    config.write_text(config.read_text(encoding="utf-8").replace(
        "build_on_serve=true\nenabled=true", maps), encoding="utf-8")
    add_attempt(paths.sqlite_path, "a_one", created_at="2026-10-18T08:00:00+00:00")
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    ctx.hints_inline = True
    ctx.hint_seed = "e"
    fake = MapFake()
    ctx.approach_map_client = fake
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    return paths, ctx, session, fake


def test_f9_a_shown_hint_schedules_the_lazy_learner_route_merge(tmp_path):
    from learnloop.hints import map_builder as MB
    from tests.approach_map_fakes import rows

    paths, ctx, session, fake = _merge_sidecar(tmp_path, "build_on_serve=true\nenabled=true")
    assert MB.wait_for_background_builds(30)
    before = len(rows(paths.sqlite_path))
    job = _request(ctx, session, "next_step@L3", WriterFake())
    assert job["result"]["shown"] is True
    assert MB.wait_for_background_builds(30)
    stored = rows(paths.sqlite_path)
    assert len(stored) == before + 1 and stored[-1]["trigger"] == "merge"
    assert json.loads(stored[-1]["map_json"])["routes"][0]["learner_attempt_ids"] == ["a_one"]
    assert [purpose for purpose, _context in fake.requests] == ["approach_map_merge"]
    # Nothing new: a second shown hint merges nothing and asks nobody.
    ctx.hint_writer_client = WriterFake()
    _call(ctx, "practice.request_hint", {"sessionId": session, "practiceItemId": ITEM, "submissionId": "k1",
                                         "answerMd": WORK + "\nso F(1/2) = 1/4"})
    assert MB.wait_for_background_builds(30)
    assert len(rows(paths.sqlite_path)) == before + 1 and fake.calls == 1


@pytest.mark.parametrize("maps", ["build_on_serve=false\nenabled=true", "build_on_serve=true\nenabled=false"])
def test_f9_the_merge_after_a_hint_obeys_the_maps_switches(tmp_path, maps):
    from learnloop.hints import map_builder as MB

    _paths, ctx, session, fake = _merge_sidecar(tmp_path, maps)
    _request(ctx, session, "next_step@L3", WriterFake())
    assert MB.wait_for_background_builds(30)
    assert fake.requests == []


def test_f9_an_undelivered_hint_schedules_nothing(tmp_path):
    from learnloop.hints import map_builder as MB

    paths, ctx, session, fake = _merge_sidecar(tmp_path, "build_on_serve=true\nenabled=true")
    ctx.hints_inline = False
    gate = threading.Event()
    job = _request(ctx, session, "next_step@L3", WriterFake(gate=gate))
    _call(ctx, "practice.cancel_hint", {"jobId": job["jobId"]})
    gate.set()
    assert ctx.hint_jobs.get(job["jobId"]).done.wait(30)
    assert _call(ctx, "practice.hint_job", {"jobId": job["jobId"]})["state"] == "cancelled"
    assert MB.wait_for_background_builds(30)
    assert fake.requests == []
