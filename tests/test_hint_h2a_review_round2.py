"""Adaptive hints H2a: the verify's reopened items V1-V4 (docs/reviews/hints-h2a-codex-review.md, fix round 2).

Each test reproduces one reopened item on the tree the verify read
(``2153658bc``) and pins its fix. Fakes only (no model is reached): the
writer and chooser are ``tests.hint_fakes``'s, the map model
``tests.approach_map_fakes``'s.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from contextlib import closing

import pytest

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.db.repositories import Repository
from learnloop.hints import service as S
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.handlers import practice as practice_handlers
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.approach_map_fakes import edge, good_map, node
from tests.hint_fakes import ITEM, WORK, ChooserFake, WriterFake, assists, good_answer, hint_vault, prefer, \
    reveals, store_map

ARGMAX = '[hints]\nchoice_policy = "argmax"\n'
SELF_GRADE = {"criterionPoints": {"cdf": 2, "value": 0}, "confidence": 3}


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _context(paths, *, inline: bool = False) -> SidecarContext:
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    ctx.hints_inline = inline
    ctx.hint_seed = "e"
    return ctx


def _attempt(paths, attempt_id: str) -> dict:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return dict(connection.execute("SELECT * FROM practice_attempts WHERE id = ?", (attempt_id,)).fetchone())


def _classes(paths, attempt_id: str) -> list[str]:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        return [row[0] for row in connection.execute(
            "SELECT contamination_class FROM causal_activity_classification_events WHERE attempt_id = ? "
            "ORDER BY seq", (attempt_id,))]


# ---------------------------------------------------------------------------
# V1: a delivery racing the submission's evidence snapshot (two sidecars)
# ---------------------------------------------------------------------------

def _two_sidecars(tmp_path, option: str):
    """Sidecar B prepares a hint of submission ``k1`` (written, not yet
    read); sidecar A will submit ``k1``. Both on one vault."""

    paths = hint_vault(tmp_path, config=ARGMAX)
    store_map(paths)
    a, b = _context(paths), _context(paths)
    session = _call(a, "start_session", {"energy": "medium"})["sessionId"]
    b.hint_writer_client = WriterFake()
    b.hint_chooser_client = ChooserFake(prefer(option, 0.9))
    params = {"sessionId": session, "practiceItemId": ITEM, "submissionId": "k1", "answerMd": WORK}
    if option.endswith(("L4", "L5")):
        params["takenLevel"] = int(option[-1])
    job = _call(b, "practice.request_hint", params)["jobId"]
    assert b.hint_jobs.get(job).done.wait(30)
    return paths, a, b, session, job


def _submit(ctx, session, submit: str):
    if submit == "attempt":
        return _call(ctx, "submit_attempt", {
            "sessionId": session, "practiceItemId": ITEM, "answerMd": WORK, "attemptType": "independent_attempt",
            "hintsUsed": 0, "selfGrade": SELF_GRADE, "submissionId": "k1"})
    return _call(ctx, "submit_dont_know", {"sessionId": session, "practiceItemId": ITEM, "submissionId": "k1"})


def _recorded(paths, attempt_id: str) -> dict:
    attempt = _attempt(paths, attempt_id)
    return {"hints_used": attempt["hints_used"], "primed": attempt["primed"],
            "attempt_type": attempt["attempt_type"], "classes": _classes(paths, attempt_id)}


CASES = [("attempt", "next_step@L3"), ("attempt", "walkthrough@L5"), ("dont_know", "next_step@L3"),
         ("dont_know", "worked_chunk@L4")]


@pytest.mark.parametrize("submit, option", CASES)
def test_v1_a_hint_delivered_after_the_fold_and_before_the_commit_is_counted(tmp_path, monkeypatch, submit,
                                                                             option):
    """Delivery wins: B shows the hint after A read the fold and before A's
    attempt commits. The attempt records exactly what a submit after the
    delivery records (the serial twin): the count, priming, the attempt type
    and the activity classification derived from them."""

    # The serial twin: delivered, then submitted.
    twin, a2, b2, session2, job2 = _two_sidecars(tmp_path / "serial", option)
    assert _call(b2, "practice.hint_job", {"jobId": job2})["result"]["shown"] is True
    expected = _recorded(twin, _submit(a2, session2, submit)["attemptId"])
    assert (expected["hints_used"], expected["primed"]) == ((1, expected["primed"]) if option.endswith("L3")
                                                            else (0, 1))

    paths, a, b, session, job = _two_sidecars(tmp_path / "raced", option)
    snapshot = practice_handlers._server_hint_fold
    polled: dict = {}

    def fold_then_deliver(*args, **kwargs):
        fold = snapshot(*args, **kwargs)
        # The fold is read; now the other sidecar delivers (its own connection).
        polled["result"] = _call(b, "practice.hint_job", {"jobId": job})["result"]
        return fold

    monkeypatch.setattr(practice_handlers, "_server_hint_fold", fold_then_deliver)
    result = _submit(a, session, submit)
    assert polled["result"]["shown"] is True and polled["result"]["hintMd"]
    assert _recorded(paths, result["attemptId"]) == expected
    [row] = assists(paths.sqlite_path)
    assert (row["shown"], row["attempt_id"]) == (1, result["attemptId"])


@pytest.mark.parametrize("submit", ["attempt", "dont_know"])
def test_v1_a_delivery_inside_the_commit_waits_and_is_refused(tmp_path, monkeypatch, submit):
    """The commit wins: B tries to deliver while A's attempt transaction
    holds the write lock (BEGIN IMMEDIATE). B waits, then finds the attempt
    committed and shows nothing; the attempt counted nothing."""

    paths, a, b, session, job = _two_sidecars(tmp_path, "next_step@L3")
    insert = Repository._insert_practice_attempt
    racer: dict = {}

    def insert_while_racing(self, connection, attempt):
        trying = threading.Event()

        def deliver():
            trying.set()
            racer["result"] = _call(b, "practice.hint_job", {"jobId": job})["result"]

        thread = threading.Thread(target=deliver)
        thread.start()
        assert trying.wait(10)
        time.sleep(0.3)  # B is now waiting on A's write lock
        racer["thread"] = thread
        assert "result" not in racer  # B could not deliver inside A's transaction
        return insert(self, connection, attempt)

    monkeypatch.setattr(Repository, "_insert_practice_attempt", insert_while_racing)
    result = _submit(a, session, submit)
    racer["thread"].join(30)
    assert (racer["result"]["status"], racer["result"]["reason"]) == ("unavailable", "submission_complete")
    assert racer["result"]["shown"] is False and racer["result"]["hintMd"] is None
    attempt = _attempt(paths, result["attemptId"])
    assert (attempt["hints_used"], attempt["primed"]) == (0, 0)
    [row] = assists(paths.sqlite_path)
    assert row["shown"] == 0 and reveals(paths.sqlite_path) == []


def test_v1_the_fold_rule_is_the_submits_own():
    from learnloop.attempts.hint_fold import ServerHintFold

    fold = ServerHintFold(practice_item_id=ITEM, session_id="s", submission_id="k", since=None, folded_hints=0,
                          folded_primed=False, base_hints=2, base_primed=False, max_useful_hints=2)
    assert (fold.hints_used(), fold.hints_used(1), fold.primed(), fold.primed(True)) == (2, 2, False, True)
    dont_know = ServerHintFold(practice_item_id=ITEM, session_id="s", submission_id="k", since=None,
                               folded_hints=0, folded_primed=False, base_hints=3, base_primed=False,
                               max_useful_hints=2, clamp_without_fold=False, stuck_types=())
    # "I don't know" clamps only when the fold adds (as before H2a); an empty
    # stuck answer's type follows the count.
    assert (dont_know.hints_used(), dont_know.hints_used(1)) == (3, 2)
    assert dont_know.attempt_type("independent_attempt", 0) == "hinted_attempt"
    zero = ServerHintFold(practice_item_id=ITEM, session_id="s", submission_id="k", since=None, folded_hints=0,
                          folded_primed=False, base_hints=0, base_primed=False, stuck_types=())
    assert (zero.attempt_type("x"), zero.attempt_type("x", 1)) == ("independent_attempt", "hinted_attempt")


# ---------------------------------------------------------------------------
# V2: the contract-failure fallback never raises a reply's level
# ---------------------------------------------------------------------------

def _setup(tmp_path, *, map_payload: dict | None = None):
    paths = hint_vault(tmp_path, config=ARGMAX)
    store_map(paths, map_payload)
    return paths, load_vault(paths.root), Repository.attach(paths.sqlite_path)


def _ask(vault, repository, option: str, answers=(), *, deliver: bool = True, **overrides):
    writer = WriterFake(list(answers))
    values = {"practice_item_id": ITEM, "session_id": "s1", "submission_id": "k1", "work_md": WORK}
    values.update(overrides)
    result = S.request_hint(vault, repository, S.HintRequestV1(**values), writer_client=writer,
                            chooser_client_factory=lambda: ChooserFake(prefer(option, 0.9)), seed="r")
    if deliver and result.status == S.READY:
        assert S.deliver(repository, str(result.assist_id)) is not None
    return result, writer


def _uncited(context):
    """A writer answer that fails rule 1 (no quote of the work)."""

    payload = good_answer(context)
    payload["placement"] = {**payload["placement"], "quotes": [], "stands_quote": "",
                            "first_questionable_quote": ""}
    return payload


@pytest.mark.parametrize("request_kind", ["feedback", "book_way"])
def test_v2_a_reply_or_pick_at_level_2_that_fails_twice_is_not_served_at_level_3(tmp_path, request_kind):
    paths, vault, repository = _setup(tmp_path)
    first, _w = _ask(vault, repository, "localize@L2")
    assert (first.status, first.level) == (S.READY, 2)
    second, writer = _ask(vault, repository, "localize@L2", [_uncited, _uncited], request=request_kind,
                          answered_assist_id=first.assist_id)
    assert second.status == S.UNAVAILABLE and second.hint_md is None and second.level is None
    assert second.message == S.NO_FITTING_HINT_MESSAGE and second.reason == "contract_failed"
    assert [(context["chosen"]["kind"], context["chosen"]["level"]) for context in writer.contexts] == [
        ("localize", 2), ("localize", 2)]
    row = assists(paths.sqlite_path)[1]
    assert (row["hint_kind"], row["level"], row["counted_by"], row["shown"]) == (None, None, None, 0)
    assert S.deliver(repository, str(second.assist_id)) is None


def test_v2_a_fixed_level_3_reply_keeps_the_level_3_downgrade(tmp_path):
    _paths, vault, repository = _setup(tmp_path)
    first, _w = _ask(vault, repository, "next_step@L3")
    second, writer = _ask(vault, repository, "next_step@L3", [_uncited, _uncited], request="feedback",
                          answered_assist_id=first.assist_id)
    assert (second.status, second.kind, second.level) == (S.READY, "next_step", 3)
    assert writer.calls == 3 and writer.contexts[-1]["chosen"].get("downgrade")


def test_v2_more_keeps_the_section_4_6_downgrade(tmp_path):
    _paths, vault, repository = _setup(tmp_path)
    result, writer = _ask(vault, repository, "localize@L2", [_uncited, _uncited])
    assert (result.status, result.kind, result.level, writer.calls) == (S.READY, "next_step", 3, 3)


# ---------------------------------------------------------------------------
# V3: unplaceable work gets no route-directed help, whatever the request
# ---------------------------------------------------------------------------

def _unplaced(context):
    payload = good_answer(context)
    payload["placement"] = {**payload["placement"], "work_matches_a_route": False, "work_valid_so_far": False}
    return payload


def _log(paths, index: int = -1) -> tuple[dict, dict]:
    row = assists(paths.sqlite_path)[index]
    return row, json.loads(row["contract_failures_json"])


@pytest.mark.parametrize("shortcut", [None, "learner_route"])
def test_v3_a_reply_on_unplaceable_work_gets_the_approach_question(tmp_path, shortcut):
    paths, vault, repository = _setup(tmp_path)
    first, _w = _ask(vault, repository, "next_step@L3")
    second, writer = _ask(vault, repository, "next_step@L3", [_unplaced], request="feedback",
                          answered_assist_id=first.assist_id, feedback_shortcut=shortcut)
    assert (second.status, second.kind, second.level, second.reason) == (S.READY, "approach_question", 1,
                                                                         "unplaced_work")
    assert [context["chosen"]["kind"] for context in writer.contexts] == ["next_step", "approach_question"]
    row, log = _log(paths)
    assert (log["drawn_kind"], log["served_kind"], log["reason"]) == ("next_step", "approach_question",
                                                                      "unplaced_work")
    assert json.loads(row["drawn_option_json"])["option"] == "next_step@L3"


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


def _from(start: str, target: str, *, unplaced: bool = False):
    def answer(context):
        payload = good_answer(context)
        payload["placement"] = {**payload["placement"], "reached_node_id": start, "route_id": "r_ref",
                                "work_matches_a_route": not unplaced, "work_valid_so_far": not unplaced}
        payload["target_node_id"] = target
        return payload
    return answer


def test_v3_a_smaller_step_on_unplaceable_work_gets_the_approach_question(tmp_path):
    _paths, vault, repository = _setup(tmp_path, map_payload=_longer())
    first, _w = _ask(vault, repository, "waypoint@L3", [_from("g", "b")])
    assert first.kind == "waypoint"
    # The approach question is placed on this map too (the fake's default node is not on it).
    second, writer = _ask(vault, repository, "next_step@L3",
                          [_from("g", "a", unplaced=True), _from("g", "", unplaced=True)],
                          request="smaller_step", answered_assist_id=first.assist_id)
    assert (second.kind, second.level, second.reason) == ("approach_question", 1, "unplaced_work")
    assert [context["chosen"]["kind"] for context in writer.contexts] == ["next_step", "approach_question"]


def test_v3_more_never_serves_a_check_this_part_on_unplaceable_work(tmp_path):
    _paths, vault, repository = _setup(tmp_path)
    result, _w = _ask(vault, repository, "error_specific@L3", [_unplaced])
    assert (result.kind, result.level, result.reason) == ("approach_question", 1, "unplaced_work")


def _from_givens(context):
    """The writer's answer when asked to start from the givens."""

    payload = good_answer({**context, "learner_work": ""})
    payload["placement"] = {**payload["placement"], "work_matches_a_route": False, "work_valid_so_far": False,
                            "reached_node_id": "g", "route_id": "r_ref"}
    return payload


def test_v3_the_books_way_on_unplaceable_work_starts_from_the_givens(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    first, _w = _ask(vault, repository, "next_step@L3")
    second, writer = _ask(vault, repository, "next_step@L3", [_unplaced, _from_givens], request="book_way",
                          answered_assist_id=first.assist_id)
    assert (second.status, second.kind, second.level, second.reason) == (S.READY, "next_step", 3,
                                                                         "unplaced_work")
    assert second.placement["reached_node_id"] == "g"
    assert [bool(context["chosen"].get("from_givens")) for context in writer.contexts] == [False, True]
    _row, log = _log(paths)
    assert log["rounds"][0]["switched_to"] == "from_givens"
    assert (log["drawn_kind"], log["served_kind"]) == ("next_step", "next_step")


def test_v3_worked_help_taken_on_unplaceable_work_starts_from_the_givens(tmp_path):
    payload = _longer()
    paths, vault, repository = _setup(tmp_path, map_payload=payload)

    def continuation_from(start: str, end: str, unplaced: bool):
        def answer(context):
            out = good_answer(context)
            out["placement"] = {**out["placement"], "reached_node_id": start, "route_id": "r_ref",
                                "stands_quote": "", "work_matches_a_route": not unplaced,
                                "work_valid_so_far": not unplaced}
            out["end_node_id"] = end
            return out
        return answer

    result, writer = _ask(vault, repository, "continuation@L4",
                          [continuation_from("a", "b", True), continuation_from("g", "a", True)], taken_level=4)
    assert (result.status, result.kind, result.level, result.reason) == (S.READY, "continuation", 4,
                                                                         "unplaced_work")
    assert result.placement["reached_node_id"] == "g" and writer.calls == 2
    assert writer.contexts[1]["chosen"].get("from_givens")
    # Placeable work keeps the learner's placement.
    _paths2, vault2, repository2 = _setup(tmp_path / "placed", map_payload=payload)
    kept, writer2 = _ask(vault2, repository2, "continuation@L4", [continuation_from("a", "b", False)],
                         taken_level=4)
    assert (kept.kind, kept.placement["reached_node_id"], writer2.calls) == ("continuation", "a", 1)


# ---------------------------------------------------------------------------
# V4: a hint is never delivered without its reveal
# ---------------------------------------------------------------------------

def test_v4_a_failed_reveal_write_shows_nothing_and_the_job_retries(tmp_path, monkeypatch):
    paths = hint_vault(tmp_path, config=ARGMAX)
    store_map(paths)
    ctx = _context(paths)
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    ctx.hint_writer_client = WriterFake()
    ctx.hint_chooser_client = ChooserFake(prefer("walkthrough@L5", 0.9))
    job = _call(ctx, "practice.request_hint", {"sessionId": session, "practiceItemId": ITEM, "submissionId": "k1",
                                               "answerMd": WORK, "takenLevel": 5})["jobId"]
    assert ctx.hint_jobs.get(job).done.wait(30)
    insert = Repository.insert_reveal_event

    def disk_full(self, event, *, clock=None):
        raise sqlite3.OperationalError("database or disk is full")

    monkeypatch.setattr(Repository, "insert_reveal_event", disk_full)
    failed = _call(ctx, "practice.hint_job", {"jobId": job})["result"]
    assert (failed["status"], failed["reason"], failed["shown"], failed["hintMd"]) == (
        "unavailable", "reveal_not_recorded", False, None)
    [row] = assists(paths.sqlite_path)
    assert (row["shown"], row["shown_at"]) == (0, None) and reveals(paths.sqlite_path) == []
    # The job stays deliverable: a later read, with the ledger writable, shows it with its reveal.
    monkeypatch.setattr(Repository, "insert_reveal_event", insert)
    delivered = _call(ctx, "practice.hint_job", {"jobId": job})["result"]
    assert delivered["status"] == "ready" and delivered["shown"] is True and delivered["hintMd"]
    [row] = assists(paths.sqlite_path)
    [reveal] = reveals(paths.sqlite_path)
    assert row["shown"] == 1 and (reveal["source_kind"], reveal["basis"]) == ("tutor_answer", "hint:walkthrough:L5")


def test_v4_record_reveal_keeps_swallowing_for_its_existing_callers(tmp_path, monkeypatch):
    from learnloop.attempts.reveal_ledger import record_reveal, record_reveal_strict

    paths = hint_vault(tmp_path)
    repository = Repository.attach(paths.sqlite_path)

    def disk_full(self, event, *, clock=None):
        raise sqlite3.OperationalError("database or disk is full")

    monkeypatch.setattr(Repository, "insert_reveal_event", disk_full)
    assert record_reveal(repository, practice_item_id=ITEM, source_kind="tutor_answer", amount=0.5) is None
    with pytest.raises(sqlite3.OperationalError):
        record_reveal_strict(repository, practice_item_id=ITEM, source_kind="tutor_answer", amount=0.5)
