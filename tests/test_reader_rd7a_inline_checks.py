"""Inline cold checks in the Reader (spec §12.6; mvp-0.69): the administration protocol end to end through the
sidecar, the protection set, the lock shared with Today, exposure written at once, submission through the attempt
service (a grader fake), abandon, crash recovery at each transition, the owner's three rulings, and the projection a
whole-vault rebuild reproduces. No model is called but the grader fake."""
from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from learnloop.curriculum import commitments as C
from learnloop.db.repositories import Repository
from learnloop.intent import inline_administration as IA
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from tests.approach_map_fakes import EXPECTED, ITEM, LO
from tests.hint_fakes import hint_vault
from tests.workbench_help_fakes import call

ANSWER = "F(x) = x^2 on [0, 1], so P(X <= 1/2) = 1/4."


@pytest.fixture(autouse=True)
def grader(monkeypatch):
    """A blind grader fake behind the sidecar's grading provider (the attempt service grades as for any answer)."""

    import learnloop_sidecar.handlers.practice as practice
    from tests.split_live_helpers import ReadyRuntime
    from tests.stuck_prompt_helpers import StuckFake

    client = StuckFake()
    monkeypatch.setattr(practice, "ready_grading_provider", lambda vault, override=None: ("fake", ReadyRuntime(), client))
    return client


def _sidecar(tmp_path, name: str = "vault"):
    paths = hint_vault(tmp_path, name=name)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.post_attempt_worker.autostart = False
    session = call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    repository = Repository.attach(paths.sqlite_path)
    return paths, ctx, session, repository


def _due_check(repository: Repository, *, key: str = "rd7a") -> str:
    yesterday = (datetime.now(UTC) - timedelta(days=1)).date().isoformat()
    return C.create_commitment(
        repository, action="test_me_later", intent_text="check the CDF later",
        targets=[{"target_kind": "legacy_practice_item", "target_ref": ITEM, "role": "required"}],
        depth_preset="keep_in_touch", client_idempotency_key=key, due_hint=yesterday).id


def _rows(paths, sql: str, params: tuple = ()) -> list[tuple]:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        return [tuple(row) for row in connection.execute(sql, params)]


VISIBLE = {"windows": [
    {"windowId": "w_pad", "kind": "pad_stack", "padBlockIds": ["b1", "b2"]},
    {"windowId": "w_thread", "kind": "thread", "exchangeIds": ["qe_1"]},
], "companionOpen": True, "companionExchangeIds": ["qe_2"], "previewWindowIds": ["w_pad"]}


def _handle(ctx, commitment: str) -> str:
    """The handle ``checks.due_for`` answers for this check now (the desks know nothing else of it)."""

    from learnloop.db.stores import check_administrations as store
    from learnloop.intent.inline_checks import handle_of

    with ctx.require_vault()[1].connection() as connection:
        count = store.administration_counts(connection).get(commitment, 0)
    return handle_of(commitment, count)


def _begin(ctx, session, commitment, *, request_id="req_1", visible=None):
    return call(ctx, "check.begin_inline", {"requestId": request_id, "handle": _handle(ctx, commitment),
                                           "sessionId": session, "visible": VISIBLE if visible is None else visible})


def _submit(ctx, token, *, submission_id="sub_1", answer=ANSWER):
    # The client sends the last veil revision it applied (here, the server's own: every veil is applied).
    revision = IA.veils(ctx.require_vault()[1], token)["revision"]
    return call(ctx, "check.submit_inline", {"administrationToken": token, "submissionId": submission_id,
                                            "answerMd": answer, "veilsRevision": revision})


# -- the RPCs ---------------------------------------------------------------------------------------------------------

def test_the_rpcs_are_registered_desktop_only_and_refuse_extra_fields():
    from learnloop_mobile.allowlist import ALLOWLIST
    from learnloop_sidecar import handlers  # noqa: F401 - populates the registry
    from learnloop_sidecar.handlers import inline_checks as H
    from learnloop_sidecar.registry import METHOD_REGISTRY

    assert H.INLINE_CHECK_RPCS == ("checks.due_for", "check.begin_inline", "check.protect_more", "check.expose",
                                   "check.submit_inline", "check.abandon_inline", "check.open_inline")
    for name in H.INLINE_CHECK_RPCS:
        assert name in METHOD_REGISTRY and name not in ALLOWLIST
    with pytest.raises(ValueError):
        H.BeginInlineInput.model_validate({"requestId": "r", "commitmentId": "c", "sessionId": "s", "extra": 1})
    with pytest.raises(ValueError):
        H.ExposeInput.model_validate({"administrationToken": "t", "ref": {}, "kind": "peeked"})


def test_below_the_tag_every_check_rpc_refuses_and_today_ignores_the_lock(tmp_path):
    from learnloop.algorithm_versions import INLINE_CHECK_ALGORITHM_VERSION, SUCCESSOR_CHAIN
    from tests.helpers import set_algorithm_version

    paths, ctx, session, repository = _sidecar(tmp_path)
    # The tag just below the inline checks' (by name: later tags follow them in the chain).
    set_algorithm_version(paths, SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(INLINE_CHECK_ALGORITHM_VERSION) - 1])
    ctx.load(paths.root)
    commitment = _due_check(repository)
    with pytest.raises(SidecarError) as refused:
        _begin(ctx, session, commitment)
    assert refused.value.code == IA.BELOW_TAG
    with pytest.raises(SidecarError) as reopened:
        call(ctx, "check.open_inline", {})
    assert reopened.value.code == IA.BELOW_TAG


# -- opening: protection before the prompt ----------------------------------------------------------------------------

def test_begin_serves_todays_item_with_its_frozen_contract_and_records_the_veils_before_the_prompt(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    card = _begin(ctx, session, commitment)
    assert card["itemRef"] == ITEM and card["cold"] is True and card["contractHash"]
    # The prompt is the allowlisted cold presentation: the question and its blocks, never the key, hints or rubric.
    assert card["prompt"]["practiceItemId"] == ITEM and card["prompt"]["prompt"]
    assert not {"expectedAnswer", "hints", "rubric", "attempts", "sourceRefs"} & set(card["prompt"])
    # Every note-bearing surface is veiled by default: the pad and thread windows whole, the companion, the preview.
    kinds = sorted((ref["kind"], ref.get("window_id")) for ref in card["protection"]["veiled"])
    assert kinds == [("companion", None), ("preview", "w_pad"), ("window", "w_pad"), ("window", "w_thread")]
    # The hint vault's LO has no coverage judgment, so the sources that would teach it are veiled whole (fail closed).
    assert card["protection"]["method"] == IA.METHOD_WHOLE_SOURCES
    assert _rows(paths, "SELECT state, surface, cold, practice_item_id FROM check_administrations") == [
        ("open", IA.SURFACE, 1, ITEM)]
    assert _rows(paths, "SELECT seq, kind FROM check_veil_sets") == [(1, "begin")]
    # The same request again is the same administration (a retry after a lost reply).
    again = _begin(ctx, session, commitment)
    assert again["administrationToken"] == card["administrationToken"]
    assert _rows(paths, "SELECT COUNT(*) FROM check_administrations") == [(1,)]


def test_no_prompt_leaves_when_the_veils_cannot_be_recorded(tmp_path, monkeypatch):
    from learnloop.db.stores import check_administrations as store

    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)

    def fail(*_args, **_kwargs):
        raise sqlite3.OperationalError("disk full")

    monkeypatch.setattr(store, "insert_veil_set", fail)
    with pytest.raises(Exception):
        _begin(ctx, session, commitment)
    # One transaction: no administration without its veils, so nothing holds the lock and no card can reopen.
    assert _rows(paths, "SELECT COUNT(*) FROM check_administrations") == [(0,)]


def _sections(monkeypatch, by_span: dict[str, str]) -> None:
    """The reading's sections, by span id (no extraction holds them in the test vault)."""

    import learnloop.intent.inline_checks as inline_checks

    class Sections:
        def __init__(self, _repository):
            pass

        def section_of(self, extraction_id, span_id):
            return by_span.get(span_id)

    monkeypatch.setattr(inline_checks, "_Sections", Sections)


def test_the_protection_set_veils_covered_passages_and_every_note_bearing_surface(tmp_path, monkeypatch):
    paths, _ctx, _session, repository = _sidecar(tmp_path)
    from learnloop.vault.loader import load_vault


    _sections(monkeypatch, {"s1": "sec_cdf", "s2": "sec_other"})
    opened = IA.Opened(commitment_id="cm", practice_item_id=ITEM, cold=True, candidates=(ITEM,),
                       learning_object_ids=(LO,), provenance={})
    visible = {
        "windows": [
            {"window_id": "w_book", "kind": "source", "extraction_id": "ext_book", "span_ids": ["s1", "s2"],
             "note_ids": ["n1"], "figures": [{"figure_id": "f1", "span_id": "s1"}, {"figure_id": "f2", "span_id": "s2"}]},
            {"window_id": "w_lesson", "kind": "lesson"}, {"window_id": "w_ink", "kind": "ink", "pad_block_ids": ["i1"]},
        ],
        "preview_window_ids": ["w_book", "w_other"],
        "search_rows": [{"kind": "span", "extraction_id": "ext_book", "span_id": "s1"},
                        {"kind": "span", "extraction_id": "ext_book", "span_id": "s2"}, {"kind": "pad", "ref_id": "b9"}],
    }
    method, veiled = IA.protection(load_vault(paths.root), repository, opened, visible,
                                   lambda los: {LO: {("ext_book", "sec_cdf")}})
    assert method == IA.METHOD
    found = sorted((ref["group"], ref["kind"], ref.get("span_id") or ref.get("figure_id") or ref.get("note_id")
                    or ref.get("window_id") or ref.get("ref_id")) for ref in veiled)
    assert found == sorted([
        ("source passages", "span", "s1"), ("figures", "figure", "f1"), ("notes", "note", "n1"),
        ("lessons", "window", "w_lesson"), ("pads", "window", "w_ink"), ("previews", "preview", "w_book"),
        ("search results", "search_row", "s1"), ("search results", "search_row", "b9"),
    ])
    # Coverage unreadable: every visible source passage is veiled instead (fail closed).
    method, veiled = IA.protection(load_vault(paths.root), repository, opened, visible, lambda los: None)
    assert method == IA.METHOD_WHOLE_SOURCES
    assert {ref["span_id"] for ref in veiled if ref["kind"] == "span"} == {"s1", "s2"}


def test_protect_more_veils_only_what_is_new(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    token = _begin(ctx, session, _due_check(repository))["administrationToken"]
    more = call(ctx, "check.protect_more", {"administrationToken": token, "visible": {
        "windows": [*VISIBLE["windows"], {"windowId": "w_new", "kind": "pad_stack"}]}})
    assert [(ref["kind"], ref["window_id"]) for ref in more["veilAdditions"]] == [("window", "w_new")]
    assert _rows(paths, "SELECT seq, kind FROM check_veil_sets ORDER BY seq") == [(1, "begin"), (2, "more")]


# -- the lock shared with Today -------------------------------------------------------------------------------------

def test_one_administration_at_a_time_and_today_honours_it(tmp_path, monkeypatch):
    from learnloop.clock import SystemClock
    from learnloop.intent.checks import BEING_ANSWERED_BANNER, served_check
    from learnloop.intent.inline_checks import due_checks
    from learnloop.scheduling.intent.serving import intent_serving
    from learnloop.vault.loader import load_vault

    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    vault = load_vault(paths.root)
    view = served_check(vault, repository, ITEM, now=SystemClock().now())
    assert view is not None and view["cold"] is True and "being_answered_in" not in view
    token = _begin(ctx, session, commitment)["administrationToken"]
    # Two administrations never overlap: another begin of this check (a lost reply, a second click) adopts the open
    # one; another check's begin is refused, naming the open one.
    again = _begin(ctx, session, commitment, request_id="req_2")
    assert (again["administrationToken"], again["replayed"]) == (token, True)
    assert _rows(paths, "SELECT COUNT(*) FROM check_administrations") == [(1,)]
    import learnloop_sidecar.handlers.inline_checks as H

    # Another due check's handle (the fixture has one check: its handle resolves to a second commitment here).
    with monkeypatch.context() as patched, pytest.raises(SidecarError) as second:
        patched.setattr(H, "resolve_handle", lambda *args, **kwargs: "cm_another_check")
        _begin(ctx, session, "cm_another_check", request_id="req_3")
    assert second.value.code == "administration_open"
    assert second.value.details["administration_token"] == token
    # Today: the check is "being answered in the Reader", its item is not the check in a build, and the band knows.
    view = served_check(vault, repository, ITEM, now=SystemClock().now())
    assert view["being_answered_in"] == "reader" and view["banner"] == BEING_ANSWERED_BANNER and view["cold"] is False
    serving = intent_serving(vault, repository, now=SystemClock().now(), force=True)
    assert serving.locked == frozenset({commitment})

    class Entry:
        practice_item_id = ITEM

    kept, chosen = serving.pick_checks([Entry()])
    assert kept == [] and chosen == []
    assert [row["being_answered"] for row in due_checks(vault, repository)] == [True]
    call(ctx, "check.abandon_inline", {"administrationToken": token})
    assert served_check(vault, repository, ITEM, now=SystemClock().now())["cold"] is True
    assert intent_serving(vault, repository, now=SystemClock().now(), force=True).locked == frozenset()


def test_a_check_with_an_answer_being_written_in_today_is_not_opened_here(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    call(ctx, "update_session_checkpoint", {"sessionId": session, "currentPracticeItemId": ITEM,
                                          "currentAnswer": "F(x) = x^2"})
    with pytest.raises(SidecarError) as refused:
        _begin(ctx, session, commitment)
    assert refused.value.code == "being_answered_in_today"


# -- exposure (owner ruling Q1) ---------------------------------------------------------------------------------------

def _seed_block(ctx, text: str) -> dict:
    """A pad block of the learner's own words; the veil a window of it would get, as a ref."""

    call(ctx, "pad.apply", {"clientId": "c", "seq": 1, "padId": "pad_n", "ops": [
        {"op": "create_pad", "kind": "named", "title": "notes"},
        {"op": "insert_block", "blockId": "b1", "versionId": "v1", "kind": "text", "provenance": "learner",
         "positionKey": "a0", "bodyMd": text}]})
    return {"kind": "window", "window_id": "w_pad", "pad_block_ids": ["b1"]}


def test_opening_a_veil_that_states_the_answer_primes_the_item_and_the_answer_is_practice(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    ref = _seed_block(ctx, EXPECTED)
    token = _begin(ctx, session, commitment)["administrationToken"]
    status = call(ctx, "check.expose", {"administrationToken": token, "ref": ref, "kind": "opened_veil"})["protectionStatus"]
    # Persisted at once, before any answer: a source review sized by the overlap with the key.
    reveals = _rows(paths, "SELECT practice_item_id, source_kind, amount, basis FROM reveal_events")
    assert [(item, kind, basis) for item, kind, _amount, basis in reveals] == [(ITEM, "source_review", IA.OPENED_BASIS)]
    assert reveals[0][2] > 0
    assert status["coldNow"] is False
    reply = _submit(ctx, token)
    assert (reply["cold"], reply["reason"]) == (False, "primed")
    assert C.resolve_disposition(repository, commitment) == "one_check_pending"  # the duty stays


def test_opening_a_veil_that_says_nothing_of_the_answer_leaves_it_cold(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    ref = _seed_block(ctx, "Remember to buy milk on Tuesday.")
    token = _begin(ctx, session, commitment)["administrationToken"]
    status = call(ctx, "check.expose", {"administrationToken": token, "ref": ref, "kind": "opened_veil"})["protectionStatus"]
    assert _rows(paths, "SELECT COUNT(*) FROM reveal_events") == [(0,)]  # a zero overlap writes nothing
    assert status["coldNow"] is True
    call(ctx, "check.expose", {"administrationToken": token, "ref": {"kind": "window", "window_id": "w_x"},
                               "kind": "navigated"})
    assert _rows(paths, "SELECT COUNT(*) FROM reveal_events") == [(0,)]  # navigating is no exposure
    reply = _submit(ctx, token)
    assert (reply["cold"], reply["reason"]) == (True, "on_your_own")
    assert C.resolve_disposition(repository, commitment) == "satisfied"
    opened = _rows(paths, "SELECT opened_json FROM check_veil_sets WHERE kind = 'close'")
    assert "w_pad" in opened[0][0]


def test_opening_a_notes_veil_reads_no_note_and_says_so_in_the_receipt(tmp_path):
    # A note is never evidence (curriculum C2's fence): the administration names the notes the client showed (their
    # ids), never reads their words, and records an opened note as opened and unmeasured.
    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    token = _begin(ctx, session, commitment)["administrationToken"]
    ref = {"group": "notes", "kind": "note", "window_id": "w_book", "note_id": "note_1"}
    status = call(ctx, "check.expose", {"administrationToken": token, "ref": ref, "kind": "opened_veil"})["protectionStatus"]
    # Unmeasured: charged at the priming threshold on every candidate, so it outlives this administration.
    from learnloop.serve_eligibility import AUTO_PRIME_REVEAL_THRESHOLD

    assert _rows(paths, "SELECT practice_item_id, amount, basis FROM reveal_events") == [
        (ITEM, AUTO_PRIME_REVEAL_THRESHOLD, IA.UNMEASURED_BASIS)]
    assert status["coldNow"] is False and status["measured"] is False
    [event] = [event for event in status["exposure"] if event["kind"] == "opened_veil"]
    assert event["unmeasured_notes"] == ["note_1"] and event["amounts"] == {ITEM: AUTO_PRIME_REVEAL_THRESHOLD}


def test_an_answer_after_a_notes_veil_was_opened_is_practice_and_says_why(tmp_path):
    # Whether an unread note gave the answer away cannot be told, so the answer errs toward practice: it is submitted
    # declared primed (the attempt row's primed flag, which a rebuild reads), with no note read and no reveal row,
    # and the reply's sub-reason says a note was opened (an orchestrator interim the owner is still to confirm).
    from learnloop.substrate.replay import rebuild_derived_state
    from learnloop.vault.loader import load_vault

    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    token = _begin(ctx, session, commitment)["administrationToken"]
    call(ctx, "check.expose", {"administrationToken": token, "kind": "opened_veil",
                               "ref": {"group": "notes", "kind": "note", "window_id": "w_book", "note_id": "note_1"}})
    reply = _submit(ctx, token)
    assert (reply["cold"], reply["reason"], reply["primedBy"]) == (False, "primed", "unmeasured_note")
    assert _rows(paths, "SELECT primed FROM practice_attempts WHERE id = ?", (reply["attemptId"],)) == [(1,)]
    assert _rows(paths, "SELECT COUNT(*) FROM reveal_events") == [(1,)]
    assert C.resolve_disposition(repository, commitment) == "one_check_pending"

    def projection() -> dict[str, Any]:
        mastery = {lo: (round(state.logit_mean, 9), round(state.logit_variance, 9), state.evidence_count)
                   for lo, state in repository.mastery_states().items()}
        return {"mastery": mastery, "primed": _rows(paths, "SELECT id, primed FROM practice_attempts ORDER BY id")}

    live = projection()
    rebuild_derived_state(load_vault(paths.root), repository)
    assert projection() == live


# -- submitting, settling, competing surfaces (owner ruling Q3) -------------------------------------------------------

def test_submit_records_one_attempt_on_the_reader_surface_settles_and_is_idempotent(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    token = _begin(ctx, session, commitment)["administrationToken"]
    first = _submit(ctx, token)
    assert (first["cold"], first["reason"]) == (True, "on_your_own")
    attempt_id = first["attemptId"]
    assert _rows(paths, "SELECT entry_surface, submission_id FROM practice_attempts WHERE id = ?", (attempt_id,)) == [
        (IA.SURFACE, "inline:sub_1")]
    assert _rows(paths, "SELECT state, attempt_id, submission_id FROM check_administrations") == [
        ("submitted", attempt_id, "sub_1")]
    again = _submit(ctx, token)
    assert again["attemptId"] == attempt_id and (again["cold"], again["reason"]) == (True, "on_your_own")
    assert _rows(paths, "SELECT COUNT(*) FROM practice_attempts WHERE practice_item_id = ?", (ITEM,))[0][0] == 1
    with pytest.raises(SidecarError) as other:
        _submit(ctx, token, submission_id="sub_2")
    assert other.value.code == "already_submitted"


def test_an_answer_on_another_surface_while_the_reader_holds_the_check_answers_nothing(tmp_path):
    # Today serves the item as practice while the Reader holds the check ("being answered in the Reader"); an answer
    # there (a deep link) is ordinary evidence and settles nothing; the Reader's answer settles the check. After that,
    # a later answer on the other surface answers nothing either (the owner's Q3).
    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    token = _begin(ctx, session, commitment)["administrationToken"]
    today = call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": ITEM, "answerMd": ANSWER,
                                         "attemptType": "independent_attempt", "submissionId": "today_1"})
    from learnloop.intent.checks import settle_answered_checks
    from learnloop.vault.loader import load_vault

    assert settle_answered_checks(load_vault(paths.root), repository) == []
    assert C.resolve_disposition(repository, commitment) == "one_check_pending"
    reply = _submit(ctx, token)
    assert (reply["cold"], reply["reason"]) == (True, "on_your_own")
    assert reply["attemptId"] != today["attemptId"]
    later = call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": ITEM, "answerMd": ANSWER,
                                         "attemptType": "independent_attempt", "submissionId": "today_2"})
    assert settle_answered_checks(load_vault(paths.root), repository) == []
    assert _rows(paths, "SELECT json_extract(detail_json, '$.administration_id') FROM commitment_events "
                        "WHERE commitment_id = ? AND kind = 'disposition_changed'", (commitment,)) == [(reply["attemptId"],)]
    assert later["attemptId"] not in (today["attemptId"], reply["attemptId"])


def test_parity_with_check_once_in_today(tmp_path):
    """The same item, contract and answer give the same attempt, grade and settlement on either surface."""

    from learnloop.intent.checks import settle_answered_checks
    from learnloop.vault.loader import load_vault

    def record(paths, repository, attempt_id):
        row = _rows(paths, "SELECT practice_item_id, rubric_score, correctness, error_type, attempt_type, primed, "
                           "hints_used, learner_answer_md FROM practice_attempts WHERE id = ?", (attempt_id,))
        contracts = _rows(paths, "SELECT DISTINCT v.contract_hash FROM grading_evidence g JOIN assessment_contract_versions v "
                                 "ON v.id = g.assessment_contract_version_id WHERE g.attempt_id = ?", (attempt_id,))
        return row[0], contracts

    paths_a, ctx_a, session_a, repo_a = _sidecar(tmp_path, name="today")
    commitment_a = _due_check(repo_a)
    served = call(ctx_a, "get_practice_item", {"practiceItemId": ITEM, "sessionId": session_a})
    today = call(ctx_a, "submit_attempt", {"sessionId": session_a, "practiceItemId": ITEM, "answerMd": ANSWER,
                                           "attemptType": "independent_attempt", "submissionId": "s",
                                           "assessmentContractVersionId": served["assessmentContractVersionId"]})
    settle_answered_checks(load_vault(paths_a.root), repo_a)
    paths_b, ctx_b, session_b, repo_b = _sidecar(tmp_path, name="reader")
    commitment_b = _due_check(repo_b)
    token = _begin(ctx_b, session_b, commitment_b)["administrationToken"]
    inline = _submit(ctx_b, token)
    assert record(paths_a, repo_a, today["attemptId"]) == record(paths_b, repo_b, inline["attemptId"])
    assert record(paths_b, repo_b, inline["attemptId"])[1]  # graded under a frozen contract on both
    assert C.resolve_disposition(repo_a, commitment_a) == C.resolve_disposition(repo_b, commitment_b) == "satisfied"


# -- abandon and crash recovery ------------------------------------------------------------------------------------

def test_not_now_closes_with_no_attempt_and_the_duty_stays(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    token = _begin(ctx, session, commitment)["administrationToken"]
    call(ctx, "check.abandon_inline", {"administrationToken": token})
    assert _rows(paths, "SELECT state FROM check_administrations") == [("abandoned",)]
    assert _rows(paths, "SELECT kind FROM check_veil_sets ORDER BY seq") == [("begin",), ("close",)]
    assert _rows(paths, "SELECT COUNT(*) FROM practice_attempts WHERE practice_item_id = ?", (ITEM,))[0][0] == 0
    assert C.resolve_disposition(repository, commitment) == "one_check_pending"
    call(ctx, "check.abandon_inline", {"administrationToken": token})  # again: nothing more
    with pytest.raises(SidecarError) as closed:
        _submit(ctx, token)
    assert closed.value.code == "administration_closed"


def test_a_restart_reopens_the_open_card_with_its_veils(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    token = _begin(ctx, session, _due_check(repository))["administrationToken"]
    restarted = SidecarContext()
    restarted.load(paths.root)
    card = call(restarted, "check.open_inline", {})["administration"]
    assert card["administrationToken"] == token and card["itemRef"] == ITEM
    assert {ref["window_id"] for ref in card["protection"]["veiled"] if ref["kind"] == "window"} == {"w_pad", "w_thread"}


def test_a_crash_after_the_attempt_and_before_the_close_is_recovered_with_that_attempt(tmp_path, monkeypatch):
    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    token = _begin(ctx, session, commitment)["administrationToken"]

    def crash(*_args, **_kwargs):
        raise RuntimeError("the process stopped")

    monkeypatch.setattr(IA, "finish_submit", crash)
    with pytest.raises(Exception):
        _submit(ctx, token)
    monkeypatch.undo()
    assert _rows(paths, "SELECT state, submission_id FROM check_administrations") == [("open", "sub_1")]
    restarted = SidecarContext()
    restarted.load(paths.root)
    assert call(restarted, "check.open_inline", {})["administration"] is None
    attempt = _rows(paths, "SELECT id FROM practice_attempts WHERE submission_id = 'inline:sub_1'")[0][0]
    assert _rows(paths, "SELECT state, attempt_id FROM check_administrations") == [("submitted", attempt)]
    assert C.resolve_disposition(repository, commitment) == "satisfied"


def test_a_crash_after_the_submission_was_named_and_before_the_attempt_retries_to_one_attempt(tmp_path, monkeypatch):
    import learnloop_sidecar.handlers.practice as practice

    paths, ctx, session, repository = _sidecar(tmp_path)
    token = _begin(ctx, session, _due_check(repository))["administrationToken"]
    real = practice.submit_attempt_on

    def crash(*_args, **_kwargs):
        raise RuntimeError("the process stopped")

    monkeypatch.setattr(practice, "submit_attempt_on", crash)
    with pytest.raises(Exception):
        _submit(ctx, token)
    # No attempt: the restart read keeps the card open (nothing reached the attempt service).
    assert call(ctx, "check.open_inline", {})["administration"]["administrationToken"] == token
    monkeypatch.setattr(practice, "submit_attempt_on", real)
    reply = _submit(ctx, token)
    assert reply["cold"] is True
    assert _rows(paths, "SELECT COUNT(*) FROM practice_attempts WHERE practice_item_id = ?", (ITEM,))[0][0] == 1


def test_a_check_settled_elsewhere_while_open_is_closed_superseded_on_the_next_read(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    _begin(ctx, session, commitment)
    C.stop_commitment(repository, commitment_id=commitment) if hasattr(C, "stop_commitment") else C.satisfy_single_check(
        repository, commitment_id=commitment, administration_id="elsewhere")
    assert call(ctx, "check.open_inline", {})["administration"] is None
    assert _rows(paths, "SELECT state FROM check_administrations") == [("superseded",)]


# -- replay -----------------------------------------------------------------------------------------------------------

def _serving_checks(paths, repository):
    from learnloop.clock import SystemClock
    from learnloop.scheduling.intent.serving import intent_serving
    from learnloop.vault.loader import load_vault

    serving = intent_serving(load_vault(paths.root), repository, now=SystemClock().now(), force=True)
    return list(serving.checks.values()) if serving is not None else []


def test_the_projection_after_an_inline_answer_equals_a_whole_vault_rebuild(tmp_path):
    from learnloop.substrate.replay import rebuild_derived_state
    from learnloop.vault.loader import load_vault

    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    ref = _seed_block(ctx, EXPECTED)
    token = _begin(ctx, session, commitment)["administrationToken"]
    call(ctx, "check.expose", {"administrationToken": token, "ref": ref, "kind": "opened_veil"})
    _submit(ctx, token)

    def projection() -> dict[str, Any]:
        mastery = {lo: (round(state.logit_mean, 9), round(state.logit_variance, 9), state.evidence_count)
                   for lo, state in repository.mastery_states().items()}
        facets = sorted((cell.facet_id, cell.capability, round(cell.direct_positive_mass, 9),
                         round(cell.direct_negative_mass, 9), round(cell.certification_credit, 9))
                        for cell in repository.facet_capability_evidence_all())
        # The whole semantic projection the answer moves: the item's schedule state and due date, the check's
        # disposition and its date, and the reveal ledger, beside mastery and facets.
        return {"mastery": mastery, "facets": facets,
                "schedule": _rows(paths, "SELECT * FROM practice_item_state ORDER BY practice_item_id"),
                "dispositions": _rows(paths, "SELECT commitment_id, kind, detail_json FROM commitment_events ORDER BY rowid"),
                "check": [(check.commitment_id, check.date.isoformat(), check.due, check.answered_by)
                          for check in sorted(_serving_checks(paths, repository), key=lambda check: check.commitment_id)],
                "reveals": _rows(paths, "SELECT id, practice_item_id, amount, basis FROM reveal_events ORDER BY id"),
                "administrations": _rows(paths, "SELECT administration_token, state, outcome_json FROM check_administrations"),
                "veil_sets": _rows(paths, "SELECT veil_set_id FROM check_veil_sets ORDER BY seq")}

    live = projection()
    rebuild_derived_state(load_vault(paths.root), repository)
    assert projection() == live


# -- the fix round (the adversarial review of 2026-11-24) -------------------------------------------------------------

from learnloop.serve_eligibility import AUTO_PRIME_REVEAL_THRESHOLD  # noqa: E402

NOTE_REF = {"group": "notes", "kind": "note", "window_id": "w_book", "note_id": "note_1"}


def _today_attempt(ctx, session, submission_id="today_x", item=ITEM):
    return call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": item, "answerMd": ANSWER,
                                        "attemptType": "independent_attempt", "submissionId": submission_id})


def test_rd7_3_an_opened_note_outlives_not_now_the_next_attempt_anywhere_is_not_cold(tmp_path):
    from learnloop.intent.checks import settle_answered_checks
    from learnloop.vault.loader import load_vault

    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    token = _begin(ctx, session, commitment)["administrationToken"]
    call(ctx, "check.expose", {"administrationToken": token, "ref": NOTE_REF, "kind": "opened_veil"})
    call(ctx, "check.abandon_inline", {"administrationToken": token})
    # A new Reader administration opens not cold, and says why.
    card = _begin(ctx, session, commitment, request_id="req_after")
    assert card["cold"] is False and card["eligibility"] == "answer_shown"
    call(ctx, "check.abandon_inline", {"administrationToken": card["administrationToken"]})
    # Today: an answer now settles nothing (the reveal is the ledger's, not the closed administration's).
    _today_attempt(ctx, session)
    assert settle_answered_checks(load_vault(paths.root), repository) == []
    assert C.resolve_disposition(repository, commitment) == "one_check_pending"


def test_rd7_3_leaving_for_an_unveiled_surface_is_an_unmeasured_opening(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    token = _begin(ctx, session, _due_check(repository))["administrationToken"]
    status = call(ctx, "check.expose", {"administrationToken": token, "kind": "left",
                                        "ref": {"kind": "surface", "surface": "old_reader"}})["protectionStatus"]
    assert status["coldNow"] is False and status["measured"] is False
    assert _rows(paths, "SELECT practice_item_id, amount, basis FROM reveal_events") == [
        (ITEM, AUTO_PRIME_REVEAL_THRESHOLD, IA.UNMEASURED_BASIS)]


def test_rd7_4_every_candidate_of_an_lo_check_is_charged_from_the_set_begin_froze(tmp_path):
    from learnloop.vault.writer import upsert_practice_item
    from tests.helpers import NOW_ISO

    paths = hint_vault(tmp_path)
    other_key = "The median of X is one over the square root of two."
    upsert_practice_item(paths.root, {
        "id": "pi_cdf_b", "learning_object_id": LO, "subjects": None, "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt"], "evidence_facets": ["recall"], "evidence_weights": {"recall": 1.0},
        "prompt": "What is the median of X?", "expected_answer": other_key,
        "grading_rubric": {"max_points": 4, "criteria": [{"id": "c", "points": 4, "description": "Correct."}], "fatal_errors": []},
        "created_at": NOW_ISO, "updated_at": NOW_ISO})
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.post_attempt_worker.autostart = False
    session = call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    repository = Repository.attach(paths.sqlite_path)
    yesterday = (datetime.now(UTC) - timedelta(days=1)).date().isoformat()
    commitment = C.create_commitment(
        repository, action="test_me_later", intent_text="check the CDF later",
        targets=[{"target_kind": "learning_object", "target_ref": LO, "role": "required"}],
        depth_preset="keep_in_touch", client_idempotency_key="rd7_4", due_hint=yesterday).id
    ref = _seed_block(ctx, other_key)
    card = _begin(ctx, session, commitment)
    token = card["administrationToken"]
    frozen = {row["practice_item_id"] for row in IA.find(repository, token)["candidates"]}
    assert frozen >= {ITEM, "pi_cdf_b"}  # every item of the LO, as build_checks expands it
    call(ctx, "check.expose", {"administrationToken": token, "ref": ref, "kind": "opened_veil"})
    charged = dict(_rows(paths, "SELECT practice_item_id, amount FROM reveal_events"))
    # The pad states the other candidate's answer: that candidate is charged, whichever item was served.
    assert charged.get("pi_cdf_b", 0) > 0


def test_rd7_5_an_opening_and_its_reveals_commit_together_and_a_retry_charges_nothing_again(tmp_path, monkeypatch):
    paths, ctx, session, repository = _sidecar(tmp_path)
    ref = _seed_block(ctx, EXPECTED)
    token = _begin(ctx, session, _due_check(repository))["administrationToken"]
    real = Repository.insert_reveal_event

    def failing(self, event, *, clock=None):
        raise sqlite3.OperationalError("disk I/O error")

    monkeypatch.setattr(Repository, "insert_reveal_event", failing)
    with pytest.raises(Exception):
        call(ctx, "check.expose", {"administrationToken": token, "ref": ref, "kind": "opened_veil", "exposureId": "op_1"})
    # Nothing recorded: no reveal, no exposure, no opened veil (the veil must stay).
    assert _rows(paths, "SELECT COUNT(*) FROM reveal_events") == [(0,)]
    assert IA.find(repository, token)["exposure"] == []
    assert IA.veils(repository, token)["opened"] == []
    monkeypatch.setattr(Repository, "insert_reveal_event", real)
    first = call(ctx, "check.expose", {"administrationToken": token, "ref": ref, "kind": "opened_veil", "exposureId": "op_1"})
    again = call(ctx, "check.expose", {"administrationToken": token, "ref": ref, "kind": "opened_veil", "exposureId": "op_1"})
    assert _rows(paths, "SELECT COUNT(*) FROM reveal_events") == [(1,)]
    assert len(first["protectionStatus"]["exposure"]) == len(again["protectionStatus"]["exposure"]) == 1


def test_rd7_6_protect_more_returns_the_standing_set_so_a_lost_reply_loses_no_veil(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    token = _begin(ctx, session, _due_check(repository))["administrationToken"]
    visible = {"windows": [*VISIBLE["windows"], {"windowId": "w_new", "kind": "pad_stack"}]}
    first = call(ctx, "check.protect_more", {"administrationToken": token, "visible": visible})
    # The first reply was lost: the same request again adds nothing, but the standing set still holds the new veil.
    again = call(ctx, "check.protect_more", {"administrationToken": token, "visible": visible})
    assert again["veilAdditions"] == [] and again["revision"] == first["revision"] == 2
    assert ("window", "w_new") in {(ref["kind"], ref.get("window_id")) for ref in again["standing"]}


def test_rd7_7_an_opening_nothing_can_measure_is_charged_and_says_so_before(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    card = _begin(ctx, session, _due_check(repository), visible={"windows": [
        {"windowId": "w_lesson", "kind": "lesson"}, {"windowId": "w_thread", "kind": "thread"}]})
    measured = {ref["window_id"]: ref["measured"] for ref in card["protection"]["veiled"] if ref["kind"] == "window"}
    assert measured == {"w_lesson": False, "w_thread": False}
    figure = {"group": "figures", "kind": "figure", "window_id": "w_book", "figure_id": "f1"}
    status = call(ctx, "check.expose", {"administrationToken": card["administrationToken"], "ref": figure,
                                        "kind": "opened_veil"})["protectionStatus"]
    assert status["measured"] is False and status["coldNow"] is False
    assert _rows(paths, "SELECT amount, basis FROM reveal_events") == [(AUTO_PRIME_REVEAL_THRESHOLD, IA.UNMEASURED_BASIS)]


def test_rd7_8_the_host_passage_is_protected_and_missing_coverage_fails_closed_for_its_source(tmp_path, monkeypatch):
    from learnloop.vault.loader import load_vault

    paths, _ctx, _session, repository = _sidecar(tmp_path)

    _sections(monkeypatch, {"h1": "sec_host", "c1": "sec_cov", "o1": "sec_other"})
    monkeypatch.setattr(IA, "host_places", lambda _repository, los: ({("ext_book", "sec_host")}, {"ext_book"}))
    opened = IA.Opened(commitment_id="cm", practice_item_id=ITEM, cold=True, candidates=(ITEM,),
                       learning_object_ids=(LO,), provenance={})
    visible = {"windows": [{"window_id": "w_book", "kind": "source", "extraction_id": "ext_book", "span_ids": ["h1", "c1", "o1"]},
                           {"window_id": "w_far", "kind": "source", "extraction_id": "ext_far", "span_ids": ["f1"]}]}
    spans = lambda veiled: {(ref["window_id"], ref["span_id"]) for ref in veiled if ref["kind"] == "span"}  # noqa: E731
    # Judged coverage: the covered section and the host's (a host with no coverage judged about it is still the host).
    _method, veiled = IA.protection(load_vault(paths.root), repository, opened, visible, lambda los: {LO: {("ext_book", "sec_cov")}})
    assert spans(veiled) == {("w_book", "h1"), ("w_book", "c1")}
    # No current coverage judgment for the LO: its host's reading whole, another reading not.
    method, veiled = IA.protection(load_vault(paths.root), repository, opened, visible, lambda los: {})
    assert method == IA.METHOD_WHOLE_SOURCES and spans(veiled) == {("w_book", "h1"), ("w_book", "c1"), ("w_book", "o1")}


def test_rd7_9_recovery_shows_the_frozen_card_without_serving_again_and_names_the_reserved_submission(tmp_path, monkeypatch):
    import learnloop_sidecar.handlers.practice as practice

    paths, ctx, session, repository = _sidecar(tmp_path)
    card = _begin(ctx, session, _due_check(repository))
    token = card["administrationToken"]
    IA.prepare_submit(ctx.require_vault()[0], repository, token=token, submission_id="sub_crash")
    served = []
    real = practice.get_practice_item
    monkeypatch.setattr(practice, "get_practice_item", lambda *args, **kwargs: served.append(1) or real(*args, **kwargs))
    again = call(ctx, "check.open_inline", {})["administration"]
    assert served == []
    assert again["prompt"] == card["prompt"] and again["submissionId"] == "sub_crash"


def test_rd7_10_a_closed_request_is_refused_with_its_state_not_served_again(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    token = _begin(ctx, session, commitment)["administrationToken"]
    call(ctx, "check.abandon_inline", {"administrationToken": token})
    with pytest.raises(SidecarError) as closed:
        _begin(ctx, session, commitment)  # the same request id
    assert closed.value.code == "administration_closed" and closed.value.details["state"] == "abandoned"


def test_rd7_11_while_a_submission_is_reserved_not_now_and_openings_are_refused(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    token = _begin(ctx, session, _due_check(repository))["administrationToken"]
    IA.prepare_submit(ctx.require_vault()[0], repository, token=token, submission_id="sub_1")
    for name, extra in (("check.abandon_inline", {}),
                        ("check.expose", {"ref": NOTE_REF, "kind": "opened_veil"})):
        with pytest.raises(SidecarError) as refused:
            call(ctx, name, {"administrationToken": token, **extra})
        assert refused.value.code == "submission_in_flight"
    # A second submission cannot reserve it either.
    with pytest.raises(IA.InlineCheckError):
        IA.prepare_submit(ctx.require_vault()[0], repository, token=token, submission_id="sub_2")


def test_rd7_12_the_outcome_is_saved_with_the_close_and_every_retry_returns_it(tmp_path, monkeypatch):
    paths, ctx, session, repository = _sidecar(tmp_path)
    token = _begin(ctx, session, _due_check(repository))["administrationToken"]
    first = _submit(ctx, token)
    assert IA.find(repository, token)["outcome"] == {"cold": True, "reason": "on_your_own", "eligibility": None}
    monkeypatch.setattr(IA, "outcome", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("computed again")))
    again = _submit(ctx, token)
    assert (again["cold"], again["reason"], again["administrationToken"]) == (first["cold"], first["reason"], token)
    assert "administration_token" not in again and "eligibility" in again


def test_rd7_13_a_client_behind_the_veil_revision_cannot_submit(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    token = _begin(ctx, session, _due_check(repository))["administrationToken"]
    call(ctx, "check.protect_more", {"administrationToken": token, "visible": {
        "windows": [*VISIBLE["windows"], {"windowId": "w_new", "kind": "pad_stack"}]}})
    with pytest.raises(SidecarError) as stale:
        call(ctx, "check.submit_inline", {"administrationToken": token, "submissionId": "sub_1", "answerMd": ANSWER,
                                          "veilsRevision": 1})
    assert stale.value.code == "veils_stale"
    assert _rows(paths, "SELECT submission_id FROM check_administrations") == [(None,)]


def test_rd7_14_today_claims_its_current_presentation_not_an_old_session_nobody_ended(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    # The current session shows the item, nothing typed yet: the check is being answered in Today.
    call(ctx, "update_session_checkpoint", {"sessionId": session, "currentPracticeItemId": ITEM, "currentAnswer": ""})
    with pytest.raises(SidecarError) as today:
        _begin(ctx, session, commitment)
    assert today.value.code == "being_answered_in_today"
    # A newer session is the current one: the old one's checkpoint (an answer typed, the session never ended) does not
    # hold the check.
    call(ctx, "update_session_checkpoint", {"sessionId": session, "currentPracticeItemId": ITEM, "currentAnswer": "F(x)"})
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.execute("UPDATE sessions SET started_at = '2020-01-01T00:00:00Z' WHERE id = ?", (session,))
        connection.execute("INSERT INTO sessions (id, started_at) VALUES ('ps_newer', '2099-01-01T00:00:00Z')")
        connection.commit()
    card = _begin(ctx, "ps_newer", commitment, request_id="req_newer")
    assert card["administrationToken"]


def test_rd7_15_a_card_moved_by_an_answer_elsewhere_is_superseded_on_recovery(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    token = _begin(ctx, session, _due_check(repository))["administrationToken"]
    _today_attempt(ctx, session)
    assert call(ctx, "check.open_inline", {})["administration"] is None
    assert IA.find(repository, token)["state"] == "superseded"


def test_rd7_16_the_daily_plan_does_not_label_a_held_check(tmp_path):
    from learnloop.clock import SystemClock
    from learnloop.scheduling.intent.serving import intent_serving
    from learnloop.vault.loader import load_vault

    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    vault = load_vault(paths.root)
    assert list(intent_serving(vault, repository, now=SystemClock().now(), force=True).check_item_ids([ITEM])) == [ITEM]
    _begin(ctx, session, commitment)
    assert intent_serving(vault, repository, now=SystemClock().now(), force=True).check_item_ids([ITEM]) == {}


def test_rd7_17_work_that_would_reveal_the_check_waits_while_it_is_open(tmp_path, monkeypatch):
    from learnloop.pads import emission

    paths, ctx, session, repository = _sidecar(tmp_path)
    token = _begin(ctx, session, _due_check(repository))["administrationToken"]
    for name, params in (
            ("companion.ask", {"requestId": "q1", "deskId": "d1", "surface": "desk", "question": "why?", "extractionId": "e",
                               "spanId": "s"}),
            ("ink.transcribe", {"inkId": "ink_1"}),
            ("lesson.turn", {"action": "open", "entry": "learning_object", "learningObjectIds": [LO]})):
        with pytest.raises(SidecarError) as held:
            call(ctx, name, params)
        assert held.value.code == "check_open", name
    settled = []
    monkeypatch.setattr(emission, "settle_blocks", lambda *args, **kwargs: settled.append(1))
    _seed_block(ctx, "a pad line written during the check")
    assert settled == []
    reconciled = []
    monkeypatch.setattr(emission, "reconcile", lambda *args, **kwargs: reconciled.append(1) or emission.Settled())
    call(ctx, "check.abandon_inline", {"administrationToken": token})
    assert reconciled == [1]


def test_rd7_18_a_session_another_device_holds_is_refused_before_the_question_shows(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.execute("UPDATE sessions SET owner_device_id = 'phone_1' WHERE id = ?", (session,))
        connection.commit()
    with pytest.raises(SidecarError) as moved:
        _begin(ctx, session, _due_check(repository))
    assert moved.value.code == "session_moved"
    assert _rows(paths, "SELECT COUNT(*) FROM check_administrations") == [(0,)]


def test_rd7_19_the_self_grade_reaches_the_attempt_service():
    from learnloop_sidecar.handlers import inline_checks as H

    parsed = H.SubmitInlineInput.model_validate({"administrationToken": "t", "submissionId": "s", "answerMd": "a",
                                                 "veilsRevision": 1, "selfGrade": {"criterionPoints": {"c": 3}, "confidence": 3}})
    assert parsed.self_grade is not None


def test_rd7_20_a_subthreshold_opening_holds_the_check_and_the_reply_says_so(tmp_path):
    # A small overlap does not prime the item, but it holds the check for a while (the Check once rule): the answer is
    # not cold, and the reply's reason is that hold, not "primed" and not "on your own".
    from learnloop.clock import FrozenClock

    paths, ctx, session, repository = _sidecar(tmp_path)
    # The check was chosen an hour ago (a reveal holds it only when it came after the choice).
    yesterday = (datetime.now(UTC) - timedelta(days=1)).date().isoformat()
    commitment = C.create_commitment(
        repository, action="test_me_later", intent_text="check the CDF later",
        targets=[{"target_kind": "legacy_practice_item", "target_ref": ITEM, "role": "required"}],
        depth_preset="keep_in_touch", client_idempotency_key="rd7_20", due_hint=yesterday,
        clock=FrozenClock(datetime.now(UTC) - timedelta(hours=1))).id
    ref = _seed_block(ctx, "Integrate")
    token = _begin(ctx, session, commitment)["administrationToken"]
    status = call(ctx, "check.expose", {"administrationToken": token, "ref": ref, "kind": "opened_veil"})["protectionStatus"]
    [amount] = [row[0] for row in _rows(paths, "SELECT amount FROM reveal_events")]
    assert 0 < amount < AUTO_PRIME_REVEAL_THRESHOLD
    assert status["eligibility"] == "hold" and status["coldNow"] is False
    reply = _submit(ctx, token)
    assert (reply["cold"], reply["reason"], reply["eligibility"]) == (False, "hold", "hold")
    assert _rows(paths, "SELECT primed FROM practice_attempts WHERE id = ?", (reply["attemptId"],)) == [(0,)]
    assert C.resolve_disposition(repository, commitment) == "one_check_pending"
